import frappe
from frappe.realtime import get_website_room
from frappe.utils import now_datetime, today, time_diff_in_seconds, getdate, add_days
from queue_management.qms_utils import normalize_rating_to_five_scale, resolve_service_names


# Valid status transitions matrix
VALID_TRANSITIONS = {
	"Waiting": {"Called", "Cancelled", "On Hold"},
	"Called": {"Serving", "Waiting", "On Hold", "No Show", "Completed"},
	"Serving": {"Completed", "On Hold"},
	"On Hold": {"Waiting", "Called", "Cancelled"},
	"No Show": {"Called", "Waiting"},
	"Completed": set(),
	"Cancelled": set(),
	"Transferred": {"Waiting"},
}


def _publish_qms_realtime(event, message=None, after_commit=False):
	"""Publish QMS events to Desk listeners and website/guest listeners."""
	message = message or {}
	frappe.publish_realtime(event, message, after_commit=after_commit)
	frappe.publish_realtime(
		f"{event}_website",
		message,
		room=get_website_room(),
		after_commit=after_commit,
	)


def _log_qms_action(action, ticket=None, counter=None, extra=None):
	"""Write an audit trail for queue mutations to qms.log."""
	request = getattr(frappe.local, "request", None)
	headers = getattr(request, "headers", {}) or {}
	payload = {
		"action": action,
		"ticket": ticket,
		"counter": counter,
		"user": getattr(getattr(frappe, "session", None), "user", None),
		"path": getattr(request, "path", None),
		"method": getattr(request, "method", None),
		"remote_addr": getattr(request, "remote_addr", None),
		"referrer": headers.get("Referer"),
		"user_agent": headers.get("User-Agent"),
	}
	if extra:
		payload.update(extra)
	frappe.logger("qms", allow_site=True, file_count=20).info(payload)


def _validate_status_transition(current_status, new_status):
	"""Validate that a status transition is allowed."""
	allowed = VALID_TRANSITIONS.get(current_status, set())
	if new_status not in allowed:
		frappe.throw(
			f"Cannot change status from '{current_status}' to '{new_status}'. "
			f"Allowed: {', '.join(sorted(allowed)) or 'none'}"
		)


def _check_qms_role():
	"""Check if current user has a QMS role. Throws if not."""
	if getattr(frappe.flags, "qms_staff_session_authenticated", False):
		return
	roles = frappe.get_roles()
	if not any(r in roles for r in ("System Manager", "Healthcare Administrator", "QMS Operator")):
		frappe.throw("You do not have permission to perform this action", frappe.PermissionError)


def _check_counter_access(counter):
	"""Verify current user is assigned to or manages the given counter."""
	if getattr(frappe.flags, "qms_staff_session_authenticated", False):
		allowed = set(getattr(frappe.flags, "qms_staff_allowed_counters", set()) or set())
		if counter in allowed:
			return
		frappe.throw("You are not assigned to this counter", frappe.PermissionError)
	roles = frappe.get_roles()
	if "System Manager" in roles or "Healthcare Administrator" in roles:
		return
	operator = frappe.db.get_value("QMS Counter", counter, "operator")
	if operator != frappe.session.user:
		frappe.throw("You are not assigned to this counter", frappe.PermissionError)


def _check_ticket_access(ticket_doc):
	"""Verify the current actor can mutate the ticket at its current counter."""
	counter_name = ticket_doc.counter or ticket_doc.transferred_from_counter
	if counter_name:
		_check_counter_access(counter_name)


def _require_qms_live_mutation(action_name):
	"""Block accidental bench/console mutations of live queue state."""
	if getattr(frappe.flags, "qms_allow_non_http_mutation", False):
		return
	if getattr(frappe.flags, "in_test", False):
		return
	if getattr(frappe.local, "request", None):
		return
	frappe.throw(
		f"{action_name} can only be run from an interactive QMS request. "
		"Direct bench/console execution is blocked. "
		"For intentional maintenance scripts, set frappe.flags.qms_allow_non_http_mutation = True first."
	)


def _lock_ticket(ticket_name):
	"""Acquire a row-level FOR UPDATE lock on a ticket and return its current DB state.

	The lock prevents any other transaction from modifying this ticket until
	the current transaction commits.  The returned dict reflects the *true*
	committed state, unaffected by REPEATABLE-READ snapshots.
	"""
	rows = frappe.db.sql(
		"""SELECT name, status, counter, modified
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket_name,),
		as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket_name}")
	return rows[0]


def _save_ticket(doc):
	"""Save a QMS Queue Ticket.  Caller must hold a FOR UPDATE lock."""
	doc.flags.ignore_version = True
	doc.save(ignore_permissions=True)


def _refresh_counter_state(counter_name):
	"""Check remaining Called/Serving tickets at this counter and update state accordingly."""
	if not counter_name:
		return
	remaining = frappe.db.count(
		"QMS Queue Ticket",
		{"counter": counter_name, "status": ("in", ["Called", "Serving"]), "token_date": today()},
	)
	if remaining:
		primary = frappe.db.get_value(
			"QMS Queue Ticket",
			{"counter": counter_name, "status": ("in", ["Called", "Serving"]), "token_date": today()},
			"name",
			order_by="called_time asc",
		)
		frappe.db.set_value("QMS Counter", counter_name, {"status": "Busy", "current_ticket": primary})
		new_status = "Busy"
	else:
		frappe.db.set_value("QMS Counter", counter_name, {"status": "Available", "current_ticket": None})
		new_status = "Available"
	location = frappe.db.get_value("QMS Counter", counter_name, "location") or ""
	_publish_qms_realtime("qms_counter_updated", {
		"counter": counter_name, "status": new_status, "location": location,
	}, after_commit=True)


# ──────────────────────────────────────────────
# Global settings helpers
# ──────────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def get_hospital_name():
	"""Return the hospital name from QMS Settings (safe for guest pages)."""
	return frappe.db.get_single_value("QMS Settings", "hospital_name") or "Queue Management"


# ──────────────────────────────────────────────
# Permission check (used in hooks add_to_apps_screen)
# ──────────────────────────────────────────────
def has_qms_permission():
	roles = frappe.get_roles()
	return any(r in roles for r in ("System Manager", "Healthcare Administrator", "QMS Operator"))


# ──────────────────────────────────────────────
# Ticket operations
# ──────────────────────────────────────────────
@frappe.whitelist()
def create_ticket(service, location, patient_name=None, patient_phone=None,
                  patient_email=None, source="Walk-in", priority="Normal",
                  patient_form_data=None):
	"""Create a new queue ticket."""
	_check_qms_role()

	# Validate inputs
	if not service or not frappe.db.exists("QMS Service", service):
		frappe.throw("Invalid service")
	if not location or not frappe.db.exists("QMS Location", location):
		frappe.throw("Invalid location")
	if priority not in ("Normal", "High", "VIP"):
		priority = "Normal"

	ticket = frappe.new_doc("QMS Queue Ticket")
	ticket.service = service
	ticket.location = location
	ticket.token_date = today()
	ticket.status = "Waiting"
	ticket.source = source
	ticket.priority = priority
	ticket.patient_name = patient_name
	ticket.patient_phone = patient_phone
	ticket.patient_email = patient_email
	if patient_form_data:
		ticket.patient_form_data = patient_form_data
	ticket.insert(ignore_permissions=True)
	return ticket


@frappe.whitelist()
def call_next_ticket(counter):
	"""Call the next waiting ticket for the services assigned to this counter."""
	_require_qms_live_mutation("Call Next")
	_check_qms_role()
	_check_counter_access(counter)

	counter_doc = frappe.get_doc("QMS Counter", counter)
	services = [row.service for row in counter_doc.services]
	if not services:
		return None

	# Retry a small number of times if another worker wins the race for the same row.
	# This preserves the current optimistic claim behaviour without risking recursion.
	max_attempts = 5
	for _attempt in range(max_attempts):
		# FIFO by check_in_time: earliest time first.
		# Returning tickets get check_in_time="2000-01-01" so they go to front.
		# Includes:
		#   - tickets matching counter's services that are not assigned to another counter
		#   - tickets explicitly assigned/transferred to this counter (regardless of service)
		# Preserve strict FIFO across the live queue; do not partition by peer counter,
		# or a later ticket can be called ahead of an earlier one.
		service_list = ", ".join(["%s"] * len(services))
		params = list(services) + [counter, counter, today()]
		location_clause = ""
		if counter_doc.location:
			# Location filter: match counter's location OR ticket explicitly assigned to this counter
			location_clause = "AND (location = %s OR counter = %s)"
			params.append(counter_doc.location)
			params.append(counter)
		tickets = frappe.db.sql(
			f"""SELECT name, counter FROM `tabQMS Queue Ticket`
				WHERE status='Waiting'
				AND (
					(service IN ({service_list}) AND (counter IS NULL OR counter='' OR counter=%s))
					OR (counter=%s AND transferred_from_counter IS NOT NULL)
				)
				AND token_date=%s {location_clause}
				ORDER BY check_in_time ASC
				FOR UPDATE""",
			tuple(params),
			as_dict=True,
		)
		if not tickets:
			return None

		assigned_to_me = [t for t in tickets if t.counter == counter]
		unassigned = [t for t in tickets if not t.counter or t.counter == ""]
		candidates = assigned_to_me + unassigned

		if not candidates:
			return None

		# Claim the ticket within the same FOR UPDATE transaction to prevent race condition
		candidate_name = candidates[0].name
		_now = now_datetime()
		frappe.db.sql(
			"""UPDATE `tabQMS Queue Ticket` SET status='Called', called_time=%s, counter=%s,
			   modified=%s, modified_by=%s
			   WHERE name=%s AND status='Waiting'""",
			(_now, counter, _now, frappe.session.user, candidate_name),
		)
		if frappe.db.sql("SELECT ROW_COUNT()")[0][0]:
			break
	else:
		frappe.throw("Queue changed while claiming the next ticket. Please try again.")

	# Now load the doc and do remaining bookkeeping outside the lock
	doc = frappe.get_doc("QMS Queue Ticket", candidate_name)
	employee = frappe.db.get_value(
		"QMS Staff Assignment",
		{"counter": counter, "is_active": 1},
		"employee"
	)
	if employee:
		doc.db_set("served_by", employee, update_modified=False)
	counter_name = ""
	counter_number = ""
	cinfo = frappe.db.get_value(
		"QMS Counter", counter, ["counter_name", "counter_number"], as_dict=True
	)
	if cinfo:
		counter_name = cinfo.counter_name or ""
		counter_number = cinfo.counter_number or ""
	# Update counter state to Busy (raw SQL UPDATE above skips ORM hooks)
	_refresh_counter_state(counter)
	_publish_qms_realtime("qms_ticket_called", {
		"ticket": doc.name, "ticket_number": doc.ticket_number,
		"counter": counter, "service": doc.service,
		"counter_name": counter_name, "counter_number": counter_number,
		"location": doc.location or "",
	}, after_commit=True)
	_log_qms_action("call_next_ticket", ticket=doc.name, counter=counter, extra={
		"ticket_number": doc.ticket_number,
		"service": doc.service,
	})
	return {"ticket": doc.name, "ticket_number": doc.ticket_number}


@frappe.whitelist()
def call_ticket(ticket, counter=None):
	"""Call a specific ticket.  Uses direct SQL to avoid ~300ms ORM overhead."""
	_require_qms_live_mutation("Call Ticket")
	_check_qms_role()
	if counter:
		_check_counter_access(counter)

	rows = frappe.db.sql(
		"""SELECT name, status, counter, recall_count, ticket_number,
		          service, location, transferred_from_counter
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]

	# Prevent a different counter from stealing an already-called ticket
	if row.status == "Called" and row.counter and counter and row.counter != counter:
		other = frappe.db.get_value("QMS Counter", row.counter, "counter_name") or row.counter
		frappe.throw(f"Ticket is already being served at {other}")

	recall_count = row.recall_count or 0
	if row.status in ("Called", "On Hold", "No Show"):
		recall_count += 1
		max_recalls = frappe.db.get_single_value("QMS Settings", "max_recall_count") or 0
		if max_recalls and recall_count > max_recalls:
			frappe.throw(f"Ticket has exceeded the maximum recall limit ({max_recalls})")
	else:
		_validate_status_transition(row.status, "Called")

	called_time = now_datetime()
	served_by = None
	if counter:
		served_by = frappe.db.get_value(
			"QMS Staff Assignment", {"counter": counter, "is_active": 1}, "employee"
		)

	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET status='Called', called_time=%s, recall_count=%s,
		    counter=COALESCE(%s, counter), served_by=COALESCE(%s, served_by),
		    modified=NOW(), modified_by=%s
		WHERE name=%s
	""", (called_time, recall_count, counter, served_by, frappe.session.user, ticket))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	# on_ticket_updated logic: set counter to Busy (status="Called" triggers this)
	effective_counter = counter or row.counter
	if effective_counter:
		frappe.db.set_value("QMS Counter", effective_counter,
		                    {"status": "Busy", "current_ticket": ticket}, update_modified=False)
		_publish_qms_realtime("qms_counter_updated", {
			"counter": effective_counter, "status": "Busy", "ticket": ticket,
			"location": row.location or "",
		}, after_commit=True)

	counter_name = ""
	counter_number = ""
	if effective_counter:
		cinfo = frappe.db.get_value(
			"QMS Counter", effective_counter, ["counter_name", "counter_number"], as_dict=True
		)
		if cinfo:
			counter_name = cinfo.counter_name or ""
			counter_number = cinfo.counter_number or ""

	_publish_qms_realtime("qms_ticket_called", {
		"ticket": row.name, "ticket_number": row.ticket_number,
		"counter": effective_counter, "service": row.service,
		"counter_name": counter_name, "counter_number": counter_number,
		"location": row.location or "",
	}, after_commit=True)
	_log_qms_action("call_ticket", ticket=row.name, counter=effective_counter, extra={
		"ticket_number": row.ticket_number, "service": row.service,
	})
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def complete_ticket(ticket):
	"""Mark ticket as completed.

	Uses direct SQL instead of doc.save() to avoid the ~300ms Frappe ORM
	overhead (validate pipeline, before_save, cache clear, on_update hooks).
	The on_ticket_updated hook is a no-op for Completed status anyway.
	"""
	_require_qms_live_mutation("Complete Ticket")
	_check_qms_role()

	# Lock + load all needed fields in one query
	rows = frappe.db.sql(
		"""SELECT name, status, counter, modified, service_start_time,
		          called_time, check_in_time, ticket_number, service, location,
		          transferred_from_counter
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]

	_validate_status_transition(row.status, "Completed")

	# Access check (same as _check_ticket_access but without loading the doc)
	access_counter = row.counter or row.transferred_from_counter
	if access_counter:
		_check_counter_access(access_counter)

	# Compute fields
	service_end = now_datetime()
	service_start = row.service_start_time or row.called_time

	wait_time_mins = 0
	if row.called_time and row.check_in_time:
		if not str(row.check_in_time).startswith("2000-01-01"):
			diff = time_diff_in_seconds(row.called_time, row.check_in_time)
			if diff and diff > 0:
				wait_time_mins = round(diff / 60, 1)

	service_duration_mins = 0
	if service_end and service_start:
		diff = time_diff_in_seconds(service_end, service_start)
		if diff and diff > 0:
			service_duration_mins = round(diff / 60, 1)

	# Direct SQL update — bypass full ORM save (~300ms → ~2ms)
	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET status='Completed',
		    service_end_time=%s,
		    service_start_time=COALESCE(service_start_time, called_time),
		    wait_time_mins=%s,
		    service_duration_mins=%s,
		    modified=NOW(),
		    modified_by=%s
		WHERE name=%s
	""", (service_end, wait_time_mins, service_duration_mins, frappe.session.user, ticket))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	if row.counter:
		_refresh_counter_state(row.counter)

	_publish_qms_realtime("qms_ticket_completed", {
		"ticket": row.name, "counter": row.counter, "location": row.location or "",
	}, after_commit=True)
	_log_qms_action("complete_ticket", ticket=row.name, counter=row.counter, extra={
		"ticket_number": row.ticket_number, "service": row.service,
	})
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def return_ticket(ticket):
	"""Return a transferred ticket to its origin counter at front of queue.
	Uses direct SQL to avoid ~300ms ORM overhead."""
	_require_qms_live_mutation("Return Ticket")
	_check_qms_role()

	rows = frappe.db.sql(
		"""SELECT name, status, counter, ticket_number, location,
		          transferred_from_counter
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]

	access_counter = row.counter or row.transferred_from_counter
	if access_counter:
		_check_counter_access(access_counter)
	if not row.transferred_from_counter:
		frappe.throw("This ticket has no origin counter to return to")

	return_to = row.transferred_from_counter
	current_counter = row.counter

	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET status='Waiting', counter=%s, transferred_from_counter=NULL,
		    check_in_time='2000-01-01 00:00:00', called_time=NULL,
		    modified=NOW(), modified_by=%s
		WHERE name=%s
	""", (return_to, frappe.session.user, ticket))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	if current_counter:
		_refresh_counter_state(current_counter)

	return_counter_name = frappe.db.get_value("QMS Counter", return_to, "counter_name") or return_to
	from_counter_name = frappe.db.get_value("QMS Counter", current_counter, "counter_name") if current_counter else ""
	_publish_qms_realtime("qms_ticket_transferred", {
		"ticket": row.name, "ticket_number": row.ticket_number,
		"from_counter": current_counter, "to_counter": return_to,
		"from_counter_name": from_counter_name or "",
		"to_counter_name": return_counter_name or "",
		"location": row.location or "",
	}, after_commit=True)
	frappe.msgprint(f"Ticket {row.ticket_number} sent back to {return_counter_name} at front of queue", alert=True)
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def hold_ticket(ticket, reason=None):
	"""Put ticket on hold.  Uses direct SQL to avoid ~300ms ORM overhead."""
	_require_qms_live_mutation("Hold Ticket")
	_check_qms_role()

	rows = frappe.db.sql(
		"""SELECT name, status, counter, ticket_number, location,
		          transferred_from_counter
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]

	_validate_status_transition(row.status, "On Hold")
	access_counter = row.counter or row.transferred_from_counter
	if access_counter:
		_check_counter_access(access_counter)

	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET status='On Hold', modified=NOW(), modified_by=%s
		WHERE name=%s
	""", (frappe.session.user, ticket))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	if reason:
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "QMS Queue Ticket",
			"reference_name": ticket,
			"content": reason,
		}).insert(ignore_permissions=True)

	if row.counter:
		_refresh_counter_state(row.counter)
	_publish_qms_realtime("qms_ticket_held", {
		"ticket": row.name, "ticket_number": row.ticket_number,
		"counter": row.counter, "location": row.location or "",
	}, after_commit=True)
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def transfer_ticket(ticket, to_counter=None, to_location=None, reason=None):
	"""Transfer a ticket to another counter or location.

	The ticket goes to the END of the destination queue.
	The origin counter is remembered so the ticket can be sent back later.
	"""
	_require_qms_live_mutation("Transfer Ticket")
	_check_qms_role()
	if not to_counter and not to_location:
		frappe.throw("Please specify a destination counter or location")

	rows = frappe.db.sql(
		"""SELECT name, counter, location, ticket_number, transfer_count,
		          transferred_from_counter, transferred_from_location
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]

	access_counter = row.counter or row.transferred_from_counter
	if access_counter:
		_check_counter_access(access_counter)

	if to_counter:
		if not frappe.db.exists("QMS Counter", to_counter):
			frappe.throw("Destination counter does not exist")
		if not frappe.db.get_value("QMS Counter", to_counter, "is_active"):
			frappe.throw("Destination counter is not active")
	if to_location:
		if not frappe.db.exists("QMS Location", to_location):
			frappe.throw("Destination location does not exist")
		if not frappe.db.get_value("QMS Location", to_location, "is_active"):
			frappe.throw("Destination location is not active")

	old_counter = row.counter
	old_location = row.location
	new_transfer_count = (row.transfer_count or 0) + 1
	new_location = to_location if to_location and to_location != old_location else old_location
	new_counter = to_counter if to_counter else None
	transferred_from_location = row.transferred_from_location or old_location

	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET transferred_from_counter=%s,
		    transfer_reason=%s,
		    transfer_count=%s,
		    transferred_from_location=%s,
		    location=%s,
		    counter=%s,
		    status='Waiting',
		    check_in_time=%s,
		    modified=NOW(),
		    modified_by=%s
		WHERE name=%s
	""", (
		old_counter,
		reason,
		new_transfer_count,
		transferred_from_location,
		new_location,
		new_counter,
		now_datetime(),
		frappe.session.user,
		ticket,
	))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	if old_counter:
		_refresh_counter_state(old_counter)

	to_counter_name = frappe.db.get_value("QMS Counter", to_counter, "counter_name") if to_counter else ""
	from_counter_name = frappe.db.get_value("QMS Counter", old_counter, "counter_name") if old_counter else ""
	to_location_name = frappe.db.get_value("QMS Location", to_location, "location_name") if to_location else ""
	_publish_qms_realtime("qms_ticket_transferred", {
		"ticket": row.name, "ticket_number": row.ticket_number,
		"from_counter": old_counter, "to_counter": to_counter,
		"from_counter_name": from_counter_name or "",
		"to_counter_name": to_counter_name or "",
		"from_location": old_location, "to_location": to_location or old_location,
		"to_location_name": to_location_name or "",
		"transfer_count": new_transfer_count,
		"location": new_location or "",
	}, after_commit=True)
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def mark_no_show(ticket):
	"""Mark ticket as no-show: requeue it at the end so the holder can come back.
	Uses direct SQL to avoid ~300ms ORM overhead."""
	_require_qms_live_mutation("No Show")
	_check_qms_role()

	rows = frappe.db.sql(
		"""SELECT name, status, counter, ticket_number, location,
		          transferred_from_counter, no_show_count
		   FROM `tabQMS Queue Ticket` WHERE name=%s FOR UPDATE""",
		(ticket,), as_dict=True,
	)
	if not rows:
		frappe.throw(f"Ticket not found: {ticket}")
	row = rows[0]
	_validate_status_transition(row.status, "Waiting")

	access_counter = row.counter or row.transferred_from_counter
	if access_counter:
		_check_counter_access(access_counter)

	old_counter = row.counter
	new_no_show = (row.no_show_count or 0) + 1

	frappe.db.sql("""
		UPDATE `tabQMS Queue Ticket`
		SET status='Waiting', counter=NULL, called_time=NULL,
		    check_in_time=%s, no_show_count=%s,
		    modified=NOW(), modified_by=%s
		WHERE name=%s
	""", (now_datetime(), new_no_show, frappe.session.user, ticket))
	frappe.clear_document_cache("QMS Queue Ticket", ticket)

	if old_counter:
		_refresh_counter_state(old_counter)

	_publish_qms_realtime("qms_ticket_no_show", {
		"ticket": row.name, "ticket_number": row.ticket_number,
		"requeued": True, "counter": old_counter,
		"location": row.location or "",
	}, after_commit=True)
	return {"ticket": row.name, "ticket_number": row.ticket_number}


@frappe.whitelist()
def get_queue_status(location=None, service=None, from_date=None, to_date=None):
	"""Get current queue status for display screens."""
	target_date = from_date or today()
	end_date = to_date or target_date
	filters = {"status": ("in", ["Waiting", "Called", "Serving"])}
	if target_date == end_date:
		filters["token_date"] = target_date
	else:
		filters["token_date"] = ("between", [target_date, end_date])
	if location:
		filters["location"] = location
	if service:
		filters["service"] = service

	tickets = frappe.get_all(
		"QMS Queue Ticket",
		filters=filters,
		fields=["name", "ticket_number", "status", "service", "counter",
		        "priority", "check_in_time", "called_time", "patient_name",
		        "transfer_count"],
		order_by="check_in_time asc",
		limit_page_length=500,
	)
	# Sort: transferred tickets first, then by priority weight, then FIFO
	priority_weight = {"VIP": 0, "High": 1, "Normal": 2}
	tickets.sort(key=lambda t: (
		0 if (t.transfer_count or 0) > 0 else 1,
		priority_weight.get(t.priority, 2),
		t.check_in_time or "",
	))

	# Resolve service IDs to human-readable names
	svc_map = resolve_service_names(tickets)
	for t in tickets:
		t["service_display"] = svc_map.get(t.service, t.service)

	# Completed / avg wait for dashboard
	completed_filters = {"status": "Completed"}
	if target_date == end_date:
		completed_filters["token_date"] = target_date
	else:
		completed_filters["token_date"] = ("between", [target_date, end_date])
	completed_today = frappe.db.count("QMS Queue Ticket", completed_filters)
	avg_wait = frappe.db.sql(
		"""SELECT ROUND(AVG(wait_time_mins),1) FROM `tabQMS Queue Ticket`
		   WHERE token_date BETWEEN %s AND %s AND status='Completed' AND wait_time_mins > 0""",
		(target_date, end_date)
	)
	avg_wait = avg_wait[0][0] if avg_wait and avg_wait[0][0] else 0

	# Counter statuses
	counter_filters = {"is_active": 1}
	if location:
		counter_filters["location"] = location
	counters = frappe.get_all("QMS Counter", filters=counter_filters,
		fields=["name", "counter_name", "counter_number", "status", "current_ticket", "location"])
	current_ticket_ids = [counter.current_ticket for counter in counters if counter.get("current_ticket")]
	if current_ticket_ids:
		ticket_number_map = {
			row.name: row.ticket_number
			for row in frappe.get_all(
				"QMS Queue Ticket",
				filters={"name": ("in", current_ticket_ids)},
				fields=["name", "ticket_number"],
			)
		}
		for counter in counters:
			if counter.get("current_ticket"):
				counter["current_ticket_number"] = ticket_number_map.get(
					counter["current_ticket"], counter["current_ticket"]
				)

	return {
		"tickets": tickets,
		"waiting": len([t for t in tickets if t.status == "Waiting"]),
		"serving": len([t for t in tickets if t.status in ("Called", "Serving")]),
		"completed": completed_today,
		"avg_wait": avg_wait,
		"counters": counters,
	}


@frappe.whitelist()
def start_shift(counter):
	"""Start shift — set counter status to Available and assign current user."""
	_check_qms_role()
	_check_counter_access(counter)
	updates = {"status": "Available"}
	if not getattr(frappe.flags, "qms_staff_session_authenticated", False):
		updates["operator"] = frappe.session.user
	frappe.db.set_value("QMS Counter", counter, updates)
	counter_location = frappe.db.get_value("QMS Counter", counter, "location") or ""
	_publish_qms_realtime("qms_counter_updated", {"counter": counter, "status": "Available", "location": counter_location}, after_commit=True)
	return {"status": "Available"}


@frappe.whitelist()
def end_shift(counter):
	"""End shift — set counter status to Closed and clear operator."""
	_check_qms_role()
	_check_counter_access(counter)
	counter_location = frappe.db.get_value("QMS Counter", counter, "location") or ""
	# Put ALL active tickets back to Waiting so they're not orphaned (batch update)
	frappe.db.sql(
		"""UPDATE `tabQMS Queue Ticket`
		   SET status='Waiting', counter=NULL, served_by=NULL,
		       modified=%s, modified_by=%s
		   WHERE counter=%s AND status IN ('Called', 'Serving') AND token_date=%s""",
		(now_datetime(), frappe.session.user, counter, today()),
	)
	_publish_qms_realtime("qms_ticket_requeued", {"counter": counter, "location": counter_location}, after_commit=True)
	updates = {
		"status": "Closed",
		"current_ticket": None,
	}
	if not getattr(frappe.flags, "qms_staff_session_authenticated", False):
		updates["operator"] = None
	frappe.db.set_value("QMS Counter", counter, updates)
	_publish_qms_realtime("qms_counter_updated", {"counter": counter, "status": "Closed", "location": counter_location}, after_commit=True)
	return {"status": "Closed"}


@frappe.whitelist()
def take_break(counter):
	"""Put counter on break."""
	_check_qms_role()
	_check_counter_access(counter)
	frappe.db.set_value("QMS Counter", counter, "status", "On Break")
	counter_location = frappe.db.get_value("QMS Counter", counter, "location") or ""
	_publish_qms_realtime("qms_counter_updated", {"counter": counter, "status": "On Break", "location": counter_location}, after_commit=True)
	return {"status": "On Break"}


@frappe.whitelist()
def start_serving(ticket):
	"""Mark ticket as actively being served (transition from Called to Serving)."""
	_require_qms_live_mutation("Start Serving")
	_check_qms_role()
	locked = _lock_ticket(ticket)
	_validate_status_transition(locked.status, "Serving")
	doc = frappe.get_doc("QMS Queue Ticket", ticket)
	doc.modified = locked.modified
	_check_ticket_access(doc)
	doc.status = "Serving"
	doc.service_start_time = now_datetime()
	_save_ticket(doc)
	if doc.counter:
		_refresh_counter_state(doc.counter)
	_publish_qms_realtime("qms_ticket_serving", {"ticket": doc.name, "counter": doc.counter, "location": doc.location or ""}, after_commit=True)
	return doc


@frappe.whitelist()
def checkin_appointment(appointment):
	"""Check in an appointment and create a queue ticket."""
	_check_qms_role()
	appt = frappe.get_doc("QMS Appointment", appointment)
	if appt.status not in ("Confirmed", "Scheduled"):
		frappe.throw(f"Appointment is '{appt.status}', cannot check in")
	# Prevent duplicate check-in
	if appt.linked_ticket:
		existing = frappe.db.get_value("QMS Queue Ticket", appt.linked_ticket, "status")
		if existing and existing not in ("Completed", "Cancelled", "No Show"):
			frappe.throw(f"This appointment already has an active ticket ({appt.linked_ticket})")
	ticket = create_ticket(
		service=appt.service,
		location=appt.location,
		patient_name=appt.patient_name,
		patient_phone=appt.patient_phone,
		patient_email=appt.patient_email,
		source="Online Booking",
		priority="Normal",
	)
	appt.status = "Checked-In"
	appt.linked_ticket = ticket.name
	appt.save(ignore_permissions=True)
	return ticket


# ──────────────────────────────────────────────
# Document event handlers (referenced in hooks.py)
# ──────────────────────────────────────────────
def on_ticket_created(doc, method):
	"""After insert handler for QMS Queue Ticket."""
	_publish_qms_realtime("qms_new_ticket", {
		"ticket": doc.name, "ticket_number": doc.ticket_number,
		"service": doc.service, "location": doc.location,
	}, after_commit=True)


def on_ticket_updated(doc, method):
	"""On update handler for QMS Queue Ticket."""
	if doc.status in ("Called", "Serving") and doc.counter:
		frappe.db.set_value("QMS Counter", doc.counter, {"status": "Busy", "current_ticket": doc.name})
		_publish_qms_realtime("qms_counter_updated", {
			"counter": doc.counter, "status": "Busy", "ticket": doc.name,
			"location": doc.location or "",
		}, after_commit=True)
	if doc.status == "Serving" and not doc.service_start_time:
		doc.db_set("service_start_time", now_datetime(), update_modified=False)


def on_feedback_submitted(doc, method):
	"""After insert handler for QMS Feedback Response."""
	if not doc.feedback_form:
		return
	template = frappe.get_doc("QMS Feedback Form Template", doc.feedback_form)
	for action in template.actions:
		if action.trigger_condition == "Any Submission":
			_execute_feedback_action(action, doc)
		elif action.trigger_condition == "Rating Below Threshold":
			rating = normalize_rating_to_five_scale(doc.overall_rating)
			if rating and rating < (action.threshold_value or 3):
				_execute_feedback_action(action, doc)


def _execute_feedback_action(action, feedback):
	"""Execute feedback action (email, todo, etc.)."""
	if action.action_type == "Create ToDo":
		frappe.get_doc({
			"doctype": "ToDo",
			"description": action.action_message or f"Follow up on feedback {feedback.name}",
			"allocated_to": action.action_target,
			"reference_type": "QMS Feedback Response",
			"reference_name": feedback.name,
		}).insert(ignore_permissions=True)
	elif action.action_type == "Send Email" and action.action_target:
		rating = normalize_rating_to_five_scale(feedback.overall_rating)
		frappe.sendmail(
			recipients=[action.action_target],
			subject=f"QMS Feedback Alert - {feedback.name}",
			message=action.action_message or f"New feedback received: Rating {rating}/5",
		)


def on_staff_assignment_updated(doc, method):
	"""Sync assignment to Employee custom fields and notify screens."""
	if doc.employee and frappe.db.exists("DocType", "Employee"):
		if doc.is_active:
			frappe.db.set_value("Employee", doc.employee, {"qms_counter": doc.counter, "qms_role": doc.qms_role})
		else:
			frappe.db.set_value("Employee", doc.employee, {"qms_counter": None, "qms_role": None})
	# Notify screens so counter assignment changes are reflected immediately
	if doc.counter:
		counter_location = frappe.db.get_value("QMS Counter", doc.counter, "location") or ""
		_publish_qms_realtime("qms_counter_updated", {
			"counter": doc.counter, "location": counter_location,
		}, after_commit=True)


# ──────────────────────────────────────────────
# Scheduler tasks (referenced in hooks.py)
# ──────────────────────────────────────────────
def cleanup_stale_tickets():
	"""Midnight: cancel tickets still in Waiting/Called from previous days."""
	try:
		frappe.db.sql(
			"""UPDATE `tabQMS Queue Ticket`
			   SET status='Cancelled', modified=%s, modified_by='Administrator'
			   WHERE status IN ('Waiting', 'Called', 'On Hold') AND token_date < %s""",
			(now_datetime(), today()),
		)
		frappe.db.commit()
		_publish_qms_realtime("qms_ticket_cancelled", {"source": "cleanup_stale_tickets"})
	except Exception:
		frappe.log_error(title="QMS: cleanup_stale_tickets failed")


def auto_expire_called_tickets():
	"""DISABLED – automatic timeout triggers removed to prevent ghost actions on tickets."""
	return
	try:
		timeout = frappe.db.get_single_value("QMS Settings", "no_show_timeout_minutes") or 0
		if not timeout:
			return
		from frappe.utils import add_to_date
		cutoff = add_to_date(now_datetime(), minutes=-timeout)
		expired = frappe.get_all(
			"QMS Queue Ticket",
			filters={
				"status": "Called",
				"token_date": today(),
				"called_time": ("<", cutoff),
			},
			fields=["name", "ticket_number", "counter", "location"],
		)
		if not expired:
			return
		expired_names = [t.name for t in expired]
		_now = now_datetime()
		frappe.db.sql(
			"""UPDATE `tabQMS Queue Ticket`
			   SET status='No Show', counter=NULL, called_time=NULL,
			       no_show_count=IFNULL(no_show_count,0)+1,
			       modified=%s, modified_by='Administrator'
			   WHERE name IN ({placeholders})""".format(
				placeholders=", ".join(["%s"] * len(expired_names))
			),
			tuple([_now] + list(expired_names)),
		)
		# Free up counters — batch refresh instead of N+1
		counter_names = list({t.counter for t in expired if t.counter})
		if counter_names:
			placeholders = ", ".join(["%s"] * len(counter_names))
			busy_counters = frappe.db.sql(
				f"""SELECT counter, MIN(name) as primary_ticket
				    FROM `tabQMS Queue Ticket`
				    WHERE counter IN ({placeholders}) AND status='Called' AND token_date=%s
				    GROUP BY counter""",
				tuple(counter_names) + (today(),),
				as_dict=True,
			)
			busy_map = {r.counter: r.primary_ticket for r in busy_counters}
			# Look up counter locations for realtime events
			counter_locs = {r["name"]: r.get("location", "") for r in frappe.get_all(
				"QMS Counter", filters={"name": ("in", counter_names)}, fields=["name", "location"]
			)}
			for cn in counter_names:
				if cn in busy_map:
					frappe.db.set_value("QMS Counter", cn, {"status": "Busy", "current_ticket": busy_map[cn]})
					new_status = "Busy"
				else:
					frappe.db.set_value("QMS Counter", cn, {"status": "Available", "current_ticket": None})
					new_status = "Available"
				_publish_qms_realtime("qms_counter_updated", {
					"counter": cn, "status": new_status, "location": counter_locs.get(cn, ""),
				}, after_commit=True)
		for t in expired:
			_publish_qms_realtime("qms_ticket_no_show", {
				"ticket": t.name,
				"ticket_number": t.ticket_number,
				"requeued": False,
				"location": t.location or "",
			}, after_commit=True)
			_log_qms_action("auto_expire_called_ticket", ticket=t.name, counter=t.counter, extra={
				"ticket_number": t.ticket_number,
				"timeout_minutes": timeout,
			})
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="QMS: auto_expire_called_tickets failed")


def purge_old_records():
	"""Midnight: delete completed/cancelled tickets older than data_retention_days."""
	try:
		retention_days = frappe.db.get_single_value("QMS Settings", "data_retention_days")
		if not retention_days:
			return
		from frappe.utils import add_days
		cutoff = add_days(today(), -int(retention_days))

		# Delete related feedback responses and old tickets in batch
		frappe.db.sql(
			"""DELETE fr FROM `tabQMS Feedback Response` fr
			   INNER JOIN `tabQMS Queue Ticket` qt ON fr.ticket = qt.name
			   WHERE qt.status IN ('Completed', 'Cancelled', 'No Show')
			     AND qt.token_date < %s""",
			(cutoff,),
		)
		frappe.db.sql(
			"""DELETE FROM `tabQMS Queue Ticket`
			   WHERE status IN ('Completed', 'Cancelled', 'No Show')
			     AND token_date < %s""",
			(cutoff,),
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="QMS: purge_old_records failed")


def send_appointment_reminders():
	"""7 AM: send reminder emails for today's appointments."""
	try:
		appointments = frappe.get_all(
			"QMS Appointment",
			filters={"appointment_date": today(), "status": "Confirmed", "reminder_sent": 0},
			fields=["name", "patient_name", "patient_email", "appointment_time", "service"],
		)
		# Batch enqueue emails instead of sending synchronously
		names_to_mark = []
		for appt in appointments:
			try:
				if appt.patient_email:
					frappe.sendmail(
						recipients=[appt.patient_email],
						subject="Appointment Reminder",
						message=f"Dear {frappe.utils.escape_html(appt.patient_name)}, your appointment for {frappe.utils.escape_html(appt.service)} is today at {appt.appointment_time}.",
						now=False,
					)
					names_to_mark.append(appt.name)
			except Exception:
				frappe.log_error(title=f"QMS: Failed to send reminder for {appt.name}")
		if names_to_mark:
			placeholders = ", ".join(["%s"] * len(names_to_mark))
			frappe.db.sql(
				f"""UPDATE `tabQMS Appointment` SET reminder_sent=1, modified=%s
				   WHERE name IN ({placeholders})""",
				tuple([now_datetime()] + list(names_to_mark)),
			)
			frappe.db.commit()
	except Exception:
		frappe.log_error(title="QMS: send_appointment_reminders failed")


# ──────────────────────────────────────────────
# Combined action + data (single round-trip for call screen)
# ──────────────────────────────────────────────
@frappe.whitelist()
def call_screen_action(action, counter, ticket=None, reason=None,
                       to_counter=None, to_location=None):
	"""Execute an action and return updated call screen data in one round-trip.

	Eliminates the second HTTP fetch that the call screen normally does
	after every action, cutting perceived latency roughly in half.
	"""
	import time as _time
	from queue_management.qms_display_api import get_call_screen_data

	request_headers = getattr(getattr(frappe, "request", None), "headers", {}) or {}
	confirm_live_action = request_headers.get("X-QMS-Confirm-Live-Action")
	if confirm_live_action != "1":
		frappe.throw(
			"Live call-screen actions require X-QMS-Confirm-Live-Action: 1. "
			"This blocks accidental bench/curl requests from changing queue state."
		)

	_t0 = _time.perf_counter()
	result = None
	error = None
	try:
		if action == "next":
			result = call_next_ticket(counter)
		elif action == "call":
			result = call_ticket(ticket, counter)
		elif action == "serve":
			result = start_serving(ticket)
		elif action == "complete":
			result = complete_ticket(ticket)
		elif action == "hold":
			result = hold_ticket(ticket, reason=reason)
		elif action == "noshow":
			result = mark_no_show(ticket)
		elif action == "transfer":
			result = transfer_ticket(ticket, to_counter=to_counter,
			                         to_location=to_location, reason=reason)
		elif action == "return":
			result = return_ticket(ticket)
		else:
			frappe.throw(f"Unknown action: {action}")
	except Exception as exc:
		error = str(exc)
		frappe.clear_messages()
		frappe.local.message_log = []

	_t1 = _time.perf_counter()
	screen_data = get_call_screen_data(counter)
	_t2 = _time.perf_counter()

	resp = {"screen_data": screen_data}
	if error:
		resp["error"] = error
	else:
		# Normalise: if result is a Document, convert to dict
		if hasattr(result, "as_dict"):
			result = {"ticket": result.name, "ticket_number": result.ticket_number}
		resp["action_result"] = result

	# Timing for debug — visible in browser console via _timing key
	resp["_timing"] = {
		"action_ms": round((_t1 - _t0) * 1000, 1),
		"data_ms": round((_t2 - _t1) * 1000, 1),
		"total_ms": round((_t2 - _t0) * 1000, 1),
	}
	return resp
