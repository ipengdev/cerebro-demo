import io
import json

import frappe
from frappe.realtime import get_website_room
from frappe.utils import get_datetime, now_datetime, today
from frappe.rate_limiter import rate_limit
from queue_management.qms_utils import estimated_wait_minutes, normalize_rating_to_five_scale, validate_guest_input, validate_phone, validate_email


AVG_WAIT_RESET_DEFAULT_KEY = "qms_kiosk_avg_wait_resets"


def _get_qms_sender_email():
	"""Get the configured sender email from QMS Settings, or return None to use system default."""
	try:
		settings = frappe.get_cached_doc("QMS Settings")
		if settings.sender_email:
			return settings.sender_email
		if settings.smtp_email_account:
			return frappe.db.get_value("Email Account", settings.smtp_email_account, "email_id")
	except Exception:
		pass
	return None


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


def _get_avg_wait_reset_map():
	"""Return service-level avg-wait reset timestamps stored in defaults."""
	raw_value = frappe.db.get_default(AVG_WAIT_RESET_DEFAULT_KEY)
	if not raw_value:
		return {}
	if isinstance(raw_value, dict):
		return raw_value
	try:
		data = json.loads(raw_value)
	except (TypeError, ValueError):
		return {}
	return data if isinstance(data, dict) else {}


def _set_avg_wait_reset_map(reset_map):
	"""Persist service-level avg-wait reset timestamps."""
	frappe.db.set_default(AVG_WAIT_RESET_DEFAULT_KEY, json.dumps(reset_map, separators=(",", ":")))


def reset_avg_wait_for_services(service_names, reset_at=None):
	"""Reset kiosk average wait calculations for the given services."""
	reset_time = reset_at or now_datetime()
	reset_map = _get_avg_wait_reset_map()
	reset_str = str(reset_time)
	for service_name in service_names or []:
		if service_name:
			reset_map[service_name] = reset_str
	_set_avg_wait_reset_map(reset_map)
	return reset_str


def _get_serving_counters(service, location):
	"""Get active counters that serve a given service at a location."""
	counters = frappe.db.sql(
		"""SELECT c.counter_name, c.counter_number
		   FROM `tabQMS Counter` c
		   INNER JOIN `tabQMS Counter Service` cs ON cs.parent = c.name
		   WHERE cs.service = %s AND c.location = %s AND c.is_active = 1
		   ORDER BY c.counter_number ASC""",
		(service, location),
		as_dict=True,
	)
	return [{
		"counter_name": c.counter_name,
		"counter_number": c.counter_number,
	} for c in counters]


def _generate_qr_svg(data):
	"""Generate a QR code as SVG string using pyqrcode."""
	from pyqrcode import create as qrcreate
	qr = qrcreate(data, error="M")
	buf = io.BytesIO()
	qr.svg(buf, scale=6, quiet_zone=2)
	return buf.getvalue().decode("utf-8")


def _send_ticket_email(patient_email, ticket_number, service_name, queue_position, estimated_wait, location):
	"""Send ticket confirmation email to patient if email is provided."""
	if not patient_email:
		return
	try:
		location_name = frappe.db.get_value("QMS Location", location, "location_name") or location
		subject = f"Your Queue Ticket #{ticket_number} — {service_name}"
		message = f"""
		<div style="font-family: 'Segoe UI', system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 32px 24px;">
			<div style="text-align: center; margin-bottom: 32px;">
				<div style="display: inline-block; background: linear-gradient(135deg, #004d40, #00838f); color: #fff;
							border-radius: 50%; width: 80px; height: 80px; line-height: 80px; font-size: 32px; font-weight: 800;">
					{ticket_number}
				</div>
			</div>
			<h2 style="text-align: center; color: #004d40; margin: 0 0 8px;">Your Ticket is Confirmed</h2>
			<p style="text-align: center; color: #555; font-size: 16px; margin: 0 0 32px;">You have been added to the queue.</p>
			<table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
				<tr>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; color: #777; width: 40%;">Ticket Number</td>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; font-weight: 700; color: #004d40;">{ticket_number}</td>
				</tr>
				<tr>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; color: #777;">Service</td>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; font-weight: 600;">{service_name}</td>
				</tr>
				<tr>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; color: #777;">Location</td>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; font-weight: 600;">{location_name}</td>
				</tr>
				<tr>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; color: #777;">Queue Position</td>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; font-weight: 600;">{queue_position}</td>
				</tr>
				<tr>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; color: #777;">Estimated Wait</td>
					<td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0; font-weight: 600;">{estimated_wait} minutes</td>
				</tr>
			</table>
			<p style="text-align: center; color: #777; font-size: 14px;">
				Please stay nearby. You will be called when it is your turn.
			</p>
		</div>
		"""
		sender = _get_qms_sender_email()
		send_kwargs = {
			"recipients": [patient_email],
			"subject": subject,
			"message": message,
			"now": True,
		}
		if sender:
			send_kwargs["sender"] = sender
		frappe.sendmail(**send_kwargs)
	except Exception:
		frappe.log_error("QMS Ticket Email Failed", frappe.get_traceback())


@frappe.whitelist(allow_guest=True)
def get_locations():
	"""Get active locations for kiosk location picker (guest-accessible)."""
	return frappe.get_all(
		"QMS Location",
		filters={"is_active": 1},
		fields=["name", "location_name", "location_type"],
		order_by="location_name asc",
	)


@frappe.whitelist(allow_guest=True)
def get_services(location):
	"""Get active services with live queue stats for kiosk display."""
	services = frappe.get_all(
		"QMS Service",
		filters={"location": location, "is_active": 1},
		fields=["name", "service_name", "service_code", "parent_service",
		        "icon", "color", "estimated_service_time", "description"],
		order_by="priority asc, service_name asc",
	)
	# Batch query: get waiting counts for all services in one query
	svc_names = [s.name for s in services]
	waiting_counts = {}
	if svc_names:
		rows = frappe.db.sql(
			"""SELECT service, COUNT(*) as cnt FROM `tabQMS Queue Ticket`
			   WHERE service IN ({}) AND status='Waiting' AND token_date=%s
			   GROUP BY service""".format(", ".join(["%s"] * len(svc_names))),
			(*svc_names, today()),
			as_dict=True,
		)
		for r in rows:
			waiting_counts[r.service] = r.cnt
	# Batch query: get active counter counts per service at this location
	counter_counts = {}
	if svc_names:
		counter_rows = frappe.db.sql(
			"""SELECT cs.service, COUNT(DISTINCT c.name) as cnt
			   FROM `tabQMS Counter` c
			   INNER JOIN `tabQMS Counter Service` cs ON cs.parent = c.name
			   WHERE cs.service IN ({}) AND c.location = %s AND c.is_active = 1
			   GROUP BY cs.service""".format(", ".join(["%s"] * len(svc_names))),
			(*svc_names, location),
			as_dict=True,
		)
		for r in counter_rows:
			counter_counts[r.service] = r.cnt

	# Batch query: get average wait time per service (from today's completed tickets)
	avg_waits = {}
	reset_map = _get_avg_wait_reset_map()
	reset_cutoffs = {}
	for service_name in svc_names:
		reset_at = reset_map.get(service_name)
		if not reset_at:
			continue
		try:
			reset_cutoffs[service_name] = get_datetime(reset_at)
		except Exception:
			continue
	if svc_names:
		avg_rows = frappe.db.sql(
			"""SELECT service, wait_time_mins, service_end_time, called_time
			   FROM `tabQMS Queue Ticket`
			   WHERE service IN ({}) AND status='Completed' AND token_date=%s
			     AND wait_time_mins > 0 AND wait_time_mins < 1440
			     AND check_in_time > '2001-01-01'""".format(", ".join(["%s"] * len(svc_names))),
			(*svc_names, today()),
			as_dict=True,
		)
		avg_totals = {}
		avg_counts = {}
		for r in avg_rows:
			completed_at = r.service_end_time or r.called_time
			cutoff = reset_cutoffs.get(r.service)
			if cutoff and completed_at and completed_at < cutoff:
				continue
			if cutoff and not completed_at:
				continue
			avg_totals[r.service] = avg_totals.get(r.service, 0.0) + float(r.wait_time_mins or 0)
			avg_counts[r.service] = avg_counts.get(r.service, 0) + 1
		for service_name, total_wait in avg_totals.items():
			count = avg_counts.get(service_name) or 0
			if count:
				avg_waits[service_name] = int(round(total_wait / count))
	for svc in services:
		waiting = waiting_counts.get(svc.name, 0)
		svc["waiting_count"] = waiting
		est = svc.get("estimated_service_time") or 10
		num_counters = counter_counts.get(svc.name, 1)
		svc["estimated_wait"] = estimated_wait_minutes(waiting, est, num_counters)
		svc["avg_wait_mins"] = avg_waits.get(svc.name, 0)
	return services


@frappe.whitelist(allow_guest=True)
def get_kiosk_info(location):
	"""Get location info and summary for kiosk welcome screen."""
	loc = frappe.db.get_value("QMS Location", location,
		["name", "location_name", "location_type"], as_dict=True)
	if not loc:
		frappe.throw("Location not found")
	total_waiting = frappe.db.count("QMS Queue Ticket", {
		"location": location, "status": "Waiting", "token_date": today()
	})
	total_served = frappe.db.count("QMS Queue Ticket", {
		"location": location, "status": "Completed", "token_date": today()
	})
	return {
		"location": loc,
		"total_waiting": total_waiting,
		"total_served": total_served,
	}


@frappe.whitelist(allow_guest=True)
def get_patient_form(location, service=None):
	"""Get the patient form template for a service/location."""
	filters = {"location": location, "is_active": 1}
	if service:
		filters["service"] = service
	else:
		filters["is_default"] = 1

	template = frappe.db.get_value(
		"QMS Patient Form Template", filters,
		["name", "form_name"], as_dict=True
	)
	if not template:
		return None

	fields = frappe.get_all(
		"QMS Patient Form Field",
		filters={"parent": template.name},
		fields=["field_label", "field_name", "field_type", "options", "is_required", "sort_order"],
		order_by="sort_order asc",
	)
	return {"form_name": template.form_name, "fields": fields}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60)
def submit_ticket(service, location, patient_name=None, patient_phone=None,
                  patient_email=None, patient_form_data=None):
	"""Submit a ticket from kiosk (guest-accessible)."""
	# Validate inputs
	patient_name = validate_guest_input(patient_name, "Patient name", max_length=140)
	patient_phone = validate_phone(patient_phone)
	patient_email = validate_email(patient_email)
	if patient_form_data:
		patient_form_data = validate_guest_input(patient_form_data, "Form data", max_length=5000)

	# Validate that service and location exist and are active
	if not frappe.db.exists("QMS Service", {"name": service, "is_active": 1}):
		frappe.throw("Invalid or inactive service")
	if not frappe.db.exists("QMS Location", {"name": location, "is_active": 1}):
		frappe.throw("Invalid or inactive location")

	# Create ticket directly (bypass staff role check for guest kiosk)
	ticket = frappe.new_doc("QMS Queue Ticket")
	ticket.service = service
	ticket.location = location
	ticket.token_date = today()
	ticket.status = "Waiting"
	ticket.source = "Kiosk"
	ticket.priority = "Normal"
	ticket.patient_name = patient_name
	ticket.patient_phone = patient_phone
	ticket.patient_email = patient_email
	if patient_form_data:
		ticket.patient_form_data = patient_form_data
	ticket.insert(ignore_permissions=True)
	# Calculate queue position & estimated wait
	position = frappe.db.count("QMS Queue Ticket", {
		"service": service, "location": location, "status": "Waiting", "token_date": today(),
		"check_in_time": ("<=", ticket.check_in_time)
	})
	svc_info = frappe.db.get_value("QMS Service", service, ["estimated_service_time", "service_name"], as_dict=True) or {}
	est_time = svc_info.get("estimated_service_time") or 10
	svc_name = svc_info.get("service_name") or service
	qr_url = frappe.utils.get_url(
		"/api/method/queue_management.qms_kiosk_api.check_ticket_status?ticket="
		+ ticket.name
	)
	serving_counters = _get_serving_counters(service, location)
	num_counters = len(serving_counters) or 1
	wait_mins = estimated_wait_minutes(position, est_time, num_counters)

	# Send confirmation email if patient provided an email address
	_send_ticket_email(patient_email, ticket.ticket_number, svc_name, position, wait_mins, location)

	return {
		"ticket": ticket.name,
		"ticket_number": ticket.ticket_number,
		"service": svc_name,
		"service_id": service,
		"token_date": str(ticket.token_date),
		"queue_position": position,
		"estimated_wait": wait_mins,
		"qr_code_svg": _generate_qr_svg(qr_url),
		"serving_counters": serving_counters,
	}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60)
def leave_waitlist(ticket):
	"""Cancel a waiting ticket from kiosk (guest-accessible)."""
	ticket = validate_guest_input(ticket, "Ticket ID", max_length=50)
	status = frappe.db.get_value("QMS Queue Ticket", ticket, "status")
	if not status:
		frappe.throw("Ticket not found")
	if status != "Waiting":
		frappe.throw("Only waiting tickets can be cancelled from the kiosk")
	doc = frappe.get_doc("QMS Queue Ticket", ticket)
	doc.status = "Cancelled"
	doc.save(ignore_permissions=True)
	_publish_qms_realtime("qms_ticket_cancelled", {"ticket": ticket, "location": doc.location or ""}, after_commit=True)
	return {"ok": True}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=60)
def get_queue_list(service, location):
	"""Get today's queue list for a service/location (guest-accessible, privacy-safe)."""
	service = validate_guest_input(service, "Service", max_length=140)
	location = validate_guest_input(location, "Location", max_length=140)

	tickets = frappe.db.sql(
		"""SELECT ticket_number, status, check_in_time, called_time
		   FROM `tabQMS Queue Ticket`
		   WHERE service=%s AND location=%s AND token_date=%s
		     AND status IN ('Waiting', 'Called', 'Serving', 'On Hold', 'Completed')
		   ORDER BY check_in_time ASC""",
		(service, location, today()),
		as_dict=True,
	)
	return tickets


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=60)
def check_ticket_status(ticket):
	"""Check current status of a ticket (for QR code lookup)."""
	# Validate ticket input to prevent injection
	ticket = validate_guest_input(ticket, "Ticket ID", max_length=50)
	doc = frappe.db.get_value(
		"QMS Queue Ticket", ticket,
		["name", "ticket_number", "status", "service", "counter",
		 "location", "wait_time_mins", "check_in_time", "called_time"],
		as_dict=True
	)
	if not doc:
		frappe.throw("Ticket not found", frappe.DoesNotExistError)

	# Calculate position in queue
	position = frappe.db.count(
		"QMS Queue Ticket",
		{"status": "Waiting", "token_date": today(),
		 "service": doc.service, "location": doc.location,
		 "check_in_time": ("<", doc.check_in_time)}
	) + 1 if doc.status == "Waiting" else 0

	doc["queue_position"] = position

	# Estimated wait based on position, service time, and active counters
	est_time = frappe.db.get_value("QMS Service", doc.service, "estimated_service_time") or 10
	num_counters = len(_get_serving_counters(doc.service, doc.location)) or 1
	doc["estimated_wait"] = estimated_wait_minutes(position, est_time, num_counters) if position else 0

	# Counter display info when ticket is called/serving
	doc["counter_name"] = ""
	doc["counter_number"] = ""
	if doc.get("counter"):
		cinfo = frappe.db.get_value(
			"QMS Counter", doc["counter"],
			["counter_name", "counter_number"], as_dict=True
		)
		if cinfo:
			doc["counter_name"] = cinfo.counter_name or ""
			doc["counter_number"] = cinfo.counter_number or ""

	# Serving counters for this service
	service_id = doc.get("service") or ""
	location = frappe.db.get_value("QMS Queue Ticket", ticket, "location") or ""
	doc["serving_counters"] = _get_serving_counters(service_id, location) if service_id else []
	doc["service_id"] = service_id

	# Resolve service ID to human-readable name
	if doc.get("service"):
		svc_name = frappe.db.get_value("QMS Service", doc["service"], "service_name")
		if svc_name:
			doc["service"] = svc_name
	return doc


@frappe.whitelist(allow_guest=True)
def get_ticket_screen_settings(location):
	"""Get ticket screen settings for a location."""
	settings = frappe.db.get_value(
		"QMS Ticket Screen Settings",
		{"location": location},
		["name", "logo", "language", "header_text", "header_text_ar",
		 "footer_text", "footer_text_ar", "background_color",
		 "text_color", "accent_color", "show_qr_code",
		 "show_wait_time", "show_queue_position"],
		as_dict=True
	)
	return settings


@frappe.whitelist(allow_guest=True)
def get_feedback_form(ticket):
	"""Get the feedback form template for a completed ticket."""
	ticket = validate_guest_input(ticket, "Ticket ID", max_length=50)
	ticket_doc = frappe.db.get_value(
		"QMS Queue Ticket", ticket,
		["name", "status", "service", "location"], as_dict=True,
	)
	if not ticket_doc:
		frappe.throw("Ticket not found", frappe.DoesNotExistError)
	if ticket_doc.status != "Completed":
		frappe.throw("Feedback is only available for completed tickets")

	# Check if feedback was already submitted
	if frappe.db.exists("QMS Feedback Response", {"ticket": ticket}):
		return {"already_submitted": True}

	# Find matching feedback form template
	template = frappe.db.get_value(
		"QMS Feedback Form Template",
		{"is_active": 1, "service": ticket_doc.service, "location": ticket_doc.location},
		"name",
	)
	if not template:
		template = frappe.db.get_value(
			"QMS Feedback Form Template",
			{"is_active": 1, "location": ticket_doc.location, "service": ("is", "not set")},
			"name",
		)
	if not template:
		template = frappe.db.get_value(
			"QMS Feedback Form Template",
			{"is_active": 1, "location": ("is", "not set"), "service": ("is", "not set")},
			"name",
		)
	if not template:
		return {"no_form": True}

	form_name = frappe.db.get_value("QMS Feedback Form Template", template, "form_name")
	fields = frappe.get_all(
		"QMS Feedback Form Field",
		filters={"parent": template},
		fields=["field_label", "field_type", "options", "is_required", "sort_order"],
		order_by="sort_order asc",
	)
	return {"form_name": form_name, "template": template, "fields": fields}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def submit_feedback(ticket, overall_rating, comments=None, response_data=None):
	"""Submit feedback for a completed ticket (guest-accessible)."""
	ticket = validate_guest_input(ticket, "Ticket ID", max_length=50)
	comments = validate_guest_input(comments, "Comments", max_length=2000)
	if response_data:
		response_data = validate_guest_input(response_data, "Response data", max_length=5000)

	ticket_doc = frappe.db.get_value(
		"QMS Queue Ticket", ticket,
		["name", "status", "service", "location", "counter",
		 "patient_name", "patient_email"],
		as_dict=True,
	)
	if not ticket_doc:
		frappe.throw("Ticket not found", frappe.DoesNotExistError)
	if ticket_doc.status != "Completed":
		frappe.throw("Feedback is only available for completed tickets")
	if frappe.db.exists("QMS Feedback Response", {"ticket": ticket}):
		frappe.throw("Feedback has already been submitted for this ticket")

	overall_rating = normalize_rating_to_five_scale(overall_rating)

	fb = frappe.get_doc({
		"doctype": "QMS Feedback Response",
		"ticket": ticket_doc.name,
		"service": ticket_doc.service,
		"location": ticket_doc.location,
		"counter": ticket_doc.counter,
		"patient_name": ticket_doc.patient_name,
		"patient_email": ticket_doc.patient_email,
		"overall_rating": overall_rating,
		"comments": comments,
		"response_data": response_data,
		"submission_time": frappe.utils.now_datetime(),
	})
	fb.flags.ignore_permissions = True
	fb.insert()
	frappe.db.commit()
	return {"success": True}
