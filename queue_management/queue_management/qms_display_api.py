import secrets

import frappe
from frappe.utils import today, now_datetime
from markupsafe import escape as escape_html
from frappe.utils.password import get_decrypted_password
from queue_management.qms_utils import resolve_service_names_inplace


_DISPLAY_SESSION_PREFIX = "qms_display_portal_session:"
# Session TTL: 30 days — display boards run on dedicated devices and should not expire
_DISPLAY_SESSION_TTL = 60 * 60 * 24 * 30
_DISPLAY_SESSION_SCOPE = "display"


def _display_portal_auth_enabled():
	"""Return whether the public display board requires portal login."""
	return bool(frappe.db.get_single_value("QMS Settings", "enable_display_portal_auth"))


def _get_display_portal_credentials():
	"""Load external portal credentials for the public display board."""
	username = (frappe.db.get_single_value("QMS Settings", "display_portal_username") or "").strip().lower()
	password = get_decrypted_password("QMS Settings", "QMS Settings", "display_portal_password", raise_exception=False) or ""
	return {"username": username, "password": password}


def _validate_display_portal_token(token):
	"""Validate a display portal session token or raise an auth error."""
	if not _display_portal_auth_enabled():
		return {"username": "public"}
	if not token or not isinstance(token, str) or len(token) > 128:
		frappe.throw("Invalid or expired display portal session", frappe.AuthenticationError)
	cache_key = f"{_DISPLAY_SESSION_PREFIX}{token}"
	username = frappe.cache.get_value(cache_key)
	if not username:
		# Redis miss — try DB fallback (survives Redis restarts)
		from queue_management.qms_session_store import load_session
		username = load_session(token, _DISPLAY_SESSION_SCOPE)
		if username:
			frappe.cache.set_value(cache_key, username, expires_in_sec=_DISPLAY_SESSION_TTL)
	if not username:
		frappe.throw("Display portal session expired. Please sign in again.", frappe.AuthenticationError)
	# Sliding window: extend TTL on each successful validation
	frappe.cache.set_value(cache_key, username, expires_in_sec=_DISPLAY_SESSION_TTL)
	return {"username": username}


@frappe.whitelist(allow_guest=True)
def display_portal_login(username=None, password=None):
	"""Authenticate a public display board session without creating a Frappe user."""
	if not _display_portal_auth_enabled():
		token = secrets.token_urlsafe(32)
		frappe.cache.set_value(f"{_DISPLAY_SESSION_PREFIX}{token}", "public", expires_in_sec=_DISPLAY_SESSION_TTL)
		from queue_management.qms_session_store import save_session
		save_session(token, _DISPLAY_SESSION_SCOPE, "public")
		return {"token": token, "username": "public", "auth_required": False}
	username = (username or "").strip().lower()
	password = (password or "").strip()
	creds = _get_display_portal_credentials()
	if not username or not password or not creds["username"] or not creds["password"]:
		frappe.throw("Display portal credentials are not configured")
	if username != creds["username"] or password != creds["password"]:
		frappe.throw("Invalid username or password", frappe.AuthenticationError)
	token = secrets.token_urlsafe(48)
	frappe.cache.set_value(f"{_DISPLAY_SESSION_PREFIX}{token}", username, expires_in_sec=_DISPLAY_SESSION_TTL)
	from queue_management.qms_session_store import save_session
	save_session(token, _DISPLAY_SESSION_SCOPE, username)
	return {"token": token, "username": username, "auth_required": True}


@frappe.whitelist(allow_guest=True)
def display_portal_logout(token):
	"""Invalidate a display portal session token."""
	if token and isinstance(token, str) and len(token) <= 128:
		frappe.cache.delete_value(f"{_DISPLAY_SESSION_PREFIX}{token}")
		from queue_management.qms_session_store import delete_session
		delete_session(token, _DISPLAY_SESSION_SCOPE)
	return {"success": True}


@frappe.whitelist(allow_guest=True)
def get_display_portal_boot(token=None):
	"""Return login requirement and branding info for the public display board."""
	hospital_name = frappe.db.get_single_value("QMS Settings", "hospital_name") or "Queue Management"
	auth_required = _display_portal_auth_enabled()
	authenticated = False
	if auth_required and token:
		try:
			_validate_display_portal_token(token)
			authenticated = True
		except frappe.AuthenticationError:
			authenticated = False
	return {
		"hospital_name": hospital_name,
		"auth_required": auth_required,
		"authenticated": authenticated,
	}


@frappe.whitelist(allow_guest=True)
def get_display_locations_portal(token=None):
	"""Guest-safe list of active display locations for the portal page."""
	_validate_display_portal_token(token)
	return frappe.get_all(
		"QMS Location",
		filters={"is_active": 1},
		fields=["name", "location_name", "location_type"],
		order_by="location_name asc",
	)


@frappe.whitelist(allow_guest=True)
def get_display_counters_portal(token=None, location=None):
	"""Guest-safe list of active counters for a location on the portal page."""
	_validate_display_portal_token(token)
	filters = {"is_active": 1}
	if location:
		filters["location"] = location
	return frappe.get_all(
		"QMS Counter",
		filters=filters,
		fields=["name", "counter_name", "counter_number"],
		order_by="counter_number asc",
	)


@frappe.whitelist(allow_guest=True)
def get_display_data_portal(token=None, location=None, counter=None):
	"""Portal wrapper around display data for external display sessions."""
	_validate_display_portal_token(token)
	return get_display_data(location=location, counter=counter)


def _get_peer_counters(counter, location, services):
	"""Return sorted list of active counter names serving the same services at the same location."""
	if not services or not location:
		return [counter]
	# Find counters at the same location that share at least one service
	rows = frappe.db.sql(
		"""SELECT DISTINCT parent
		   FROM `tabQMS Counter Service`
		   WHERE service IN ({placeholders})
		     AND parent IN (
		         SELECT name FROM `tabQMS Counter`
		         WHERE is_active=1 AND location=%s AND status != 'Closed'
		     )""".format(placeholders=", ".join(["%s"] * len(services))),
		tuple(list(services) + [location]),
	)
	peers = sorted(set(r[0] for r in rows))
	if counter not in peers:
		peers.append(counter)
		peers.sort()
	return peers


@frappe.whitelist(allow_guest=True)
def get_display_data(location, screen_type=None, counter=None):
	"""Get data for TV/display screens.

	Args:
		location: QMS Location name (required)
		screen_type: optional screen type filter for template
		counter: optional QMS Counter name to filter tickets for a specific counter
	"""
	# Get template
	filters = {"location": location}
	if screen_type:
		filters["screen_type"] = screen_type
	template = frappe.db.get_value(
		"QMS Display Screen Template", filters,
		["name", "template_name", "screen_type", "logo", "language",
		 "background_color", "background_image", "text_color", "accent_color",
		 "header_text", "header_text_ar", "footer_text", "footer_text_ar",
		 "show_now_serving", "show_waiting_list", "max_tickets_displayed",
		 "auto_refresh_interval", "announcement_text", "announcement_text_ar",
		 "call_sound", "call_sound_repeat",
		 "custom_css"],
		as_dict=True,
	)

	# Resolve counter services when filtering by counter
	counter_services = []
	if counter:
		counter_services = [r.service for r in frappe.get_all(
			"QMS Counter Service", filters={"parent": counter}, fields=["service"]
		)]

	# Get currently serving tickets
	serving_filters = {"location": location, "token_date": today(),
		               "status": ("in", ["Called", "Serving"])}
	if counter:
		serving_filters["counter"] = counter
	now_serving = frappe.get_all(
		"QMS Queue Ticket",
		filters=serving_filters,
		fields=["ticket_number", "service", "counter", "patient_name", "called_time"],
		order_by="called_time desc",
	)

	# Get waiting tickets
	max_display = (template or {}).get("max_tickets_displayed") or 20
	waiting_filters = {"location": location, "token_date": today(), "status": "Waiting"}
	if counter and counter_services:
		waiting_filters["service"] = ("in", counter_services)
	elif counter:
		# Counter has no services configured — show only tickets assigned to it
		waiting_filters["counter"] = counter
	waiting = frappe.get_all(
		"QMS Queue Ticket",
		filters=waiting_filters,
		fields=["ticket_number", "service", "priority", "check_in_time", "transfer_count"],
		order_by="check_in_time asc",
		limit=max_display,
	)
	# FIFO by check_in_time – returning tickets have earliest timestamp (front of queue)
	waiting.sort(key=lambda t: t.check_in_time or "")

	# Get media items for the template
	media_items = []
	if template and template.name:
		media_items = frappe.get_all(
			"QMS Display Media Item",
			filters={"parent": template.name},
			fields=["media_type", "media_file", "display_duration", "sort_order"],
			order_by="sort_order asc",
		)

	# On-hold tickets for the display
	on_hold_filters = {"location": location, "token_date": today(), "status": "On Hold"}
	if counter:
		on_hold_filters["counter"] = counter
	on_hold = frappe.get_all(
		"QMS Queue Ticket",
		filters=on_hold_filters,
		fields=["ticket_number", "service", "priority", "patient_name"],
	)

	# Resolve service IDs to human-readable names
	resolve_service_names_inplace(list(now_serving) + list(waiting) + list(on_hold))

	# Escape patient names to prevent XSS on display screens
	for t in list(now_serving) + list(on_hold):
		if t.get("patient_name"):
			t.patient_name = str(escape_html(t.patient_name))

	# Resolve counter IDs to human-readable counter names
	counter_ids = list({t.counter for t in now_serving if t.get("counter")})
	if counter_ids:
		counter_map = {
			r.name: (
				f"Counter {r.counter_number}"
				if r.counter_number is not None and str(r.counter_number).strip()
				else (r.counter_name or r.name)
			)
			for r in frappe.get_all(
				"QMS Counter",
				filters={"name": ("in", counter_ids)},
				fields=["name", "counter_name", "counter_number"],
			)
		}
		for t in now_serving:
			if t.get("counter") and t.counter in counter_map:
				t.counter = counter_map[t.counter]

	return {
		"template": template,
		"now_serving": now_serving,
		"waiting": waiting,
		"on_hold": on_hold,
		"media_items": media_items,
	}


@frappe.whitelist()
def get_call_screen_data(counter):
	"""Get data for the staff call screen."""
	counter_doc = frappe.get_doc("QMS Counter", counter)
	services = [row.service for row in counter_doc.services]

	settings = frappe.db.get_value(
		"QMS Call Screen Settings",
		{"counter": counter},
		["name", "language", "show_patient_info", "show_queue_length",
		 "show_wait_time", "enable_hold", "enable_transfer",
		 "enable_recall", "enable_no_show", "auto_call_next"],
		as_dict=True,
	)

	# Currently serving tickets (tickets that have been called or actively started)
	serving_tickets = frappe.get_all(
		"QMS Queue Ticket",
		filters={"counter": counter, "status": ("in", ["Called", "Serving"]), "token_date": today()},
		fields=["name", "ticket_number", "service", "patient_name", "patient_phone",
		        "priority", "status", "called_time", "service_start_time", "source", "transferred_from_counter",
		        "transfer_count"],
		order_by="called_time asc",
	)

	# Backward compat: also expose single current_ticket
	current_ticket = None
	if counter_doc.current_ticket:
		ct_status = frappe.db.get_value("QMS Queue Ticket", counter_doc.current_ticket, "status")
		if ct_status in ("Called", "Serving"):
			current_ticket = frappe.get_doc("QMS Queue Ticket", counter_doc.current_ticket).as_dict()
	if not current_ticket and serving_tickets:
		current_ticket = frappe.get_doc("QMS Queue Ticket", serving_tickets[0].name).as_dict()

	# Waiting queue: ALL waiting tickets at this location so staff can see
	# the full picture, plus any tickets explicitly assigned to this counter
	# (covers transfers regardless of service/location).
	# Round-robin is only applied in call_next_ticket for fair distribution.
	waiting_fields = ["name", "ticket_number", "service", "patient_name",
	                  "priority", "check_in_time", "wait_time_mins", "transfer_count",
	                  "counter", "transfer_back", "return_to_counter",
	                  "transferred_from_counter", "location"]
	location = counter_doc.location
	if location:
		# Show ALL waiting tickets at this location + any ticket assigned to this counter
		waiting = frappe.db.sql(
			"""SELECT name, ticket_number, service, patient_name,
			        priority, check_in_time, wait_time_mins,
			        IFNULL(transfer_count, 0) as transfer_count, counter,
			        transfer_back, return_to_counter, transferred_from_counter,
			        location
			    FROM `tabQMS Queue Ticket`
			    WHERE status='Waiting' AND token_date=%s
			    AND (location=%s OR counter=%s)
			    ORDER BY check_in_time ASC""",
			(today(), location, counter),
			as_dict=True,
		)
	elif services:
		# No location — fall back to service-based filtering + assigned tickets
		service_list = ", ".join(["%s"] * len(services))
		params = [today()] + list(services) + [counter]
		waiting = frappe.db.sql(
			f"""SELECT name, ticket_number, service, patient_name,
			        priority, check_in_time, wait_time_mins,
			        IFNULL(transfer_count, 0) as transfer_count, counter,
			        transfer_back, return_to_counter, transferred_from_counter,
			        location
			    FROM `tabQMS Queue Ticket`
			    WHERE status='Waiting' AND token_date=%s
			    AND (
			        service IN ({service_list})
			        OR counter=%s
			    )
			    ORDER BY check_in_time ASC""",
			tuple(params),
			as_dict=True,
		)
	else:
		# No services configured — show tickets assigned to this counter
		waiting = frappe.get_all(
			"QMS Queue Ticket",
			filters={
				"counter": counter, "status": "Waiting", "token_date": today(),
			},
			fields=waiting_fields,
		)
	# FIFO by check_in_time – returning tickets have earliest timestamp (front of queue)
	waiting.sort(key=lambda t: t.check_in_time or "")

	# On-hold tickets
	on_hold = frappe.get_all(
		"QMS Queue Ticket",
		filters={"counter": counter, "status": "On Hold", "token_date": today()},
		fields=["name", "ticket_number", "service", "patient_name", "priority"],
	)

	# Resolve service IDs to human-readable names
	resolve_service_names_inplace(list(waiting) + list(on_hold) + list(serving_tickets) + ([current_ticket] if current_ticket else []))

	# Resolve transferred_from_counter to human-readable counter names
	all_items = list(waiting) + list(serving_tickets) + ([current_ticket] if current_ticket else [])
	counter_ids = set()
	for item in all_items:
		fc = item.get("transferred_from_counter") if isinstance(item, dict) else getattr(item, "transferred_from_counter", None)
		if fc:
			counter_ids.add(fc)
	if counter_ids:
		counter_names = {r[0]: r[1] for r in frappe.get_all(
			"QMS Counter", filters={"name": ("in", list(counter_ids))},
			fields=["name", "counter_name"], as_list=True
		)}
		for item in all_items:
			fc = item.get("transferred_from_counter") if isinstance(item, dict) else getattr(item, "transferred_from_counter", None)
			if fc and fc in counter_names:
				if isinstance(item, dict):
					item["transferred_from_counter_name"] = counter_names[fc]
				else:
					item.transferred_from_counter_name = counter_names[fc]

	# Tickets transferred OUT from this counter (still waiting/called at another counter)
	transferred_out = frappe.get_all(
		"QMS Queue Ticket",
		filters={
			"transferred_from_counter": counter,
			"counter": ("!=", counter),
			"status": ("in", ["Waiting", "Called"]),
			"token_date": today(),
		},
		fields=["name", "ticket_number", "service", "patient_name",
		        "priority", "status", "counter", "transfer_reason",
		        "check_in_time"],
		order_by="check_in_time asc",
	)
	resolve_service_names_inplace(transferred_out)
	# Resolve destination counter names for transferred_out tickets
	dest_counter_ids = set(t.get("counter") for t in transferred_out if t.get("counter"))
	if dest_counter_ids:
		dest_counter_names = {r[0]: r[1] for r in frappe.get_all(
			"QMS Counter", filters={"name": ("in", list(dest_counter_ids))},
			fields=["name", "counter_name"], as_list=True
		)}
		for t in transferred_out:
			if t.get("counter") and t["counter"] in dest_counter_names:
				t["dest_counter_name"] = dest_counter_names[t["counter"]]

	# Completed today count (avoids extra API call from frontend)
	completed_today = frappe.db.count("QMS Queue Ticket", {"token_date": today(), "status": "Completed"})

	return {
		"counter": counter_doc.as_dict(),
		"settings": settings,
		"current_ticket": current_ticket,
		"serving_tickets": serving_tickets,
		"waiting": waiting,
		"on_hold": on_hold,
		"transferred_out": transferred_out,
		"queue_length": len(waiting),
		"completed_today": completed_today,
		"server_time": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
	}


@frappe.whitelist()
def get_my_counter():
	"""Get the counter assigned to the current logged-in user."""
	user = frappe.session.user
	counter = frappe.db.get_value(
		"QMS Counter",
		{"operator": user, "is_active": 1},
		["name", "counter_name", "counter_number", "status", "location"],
		as_dict=True,
	)
	return counter
