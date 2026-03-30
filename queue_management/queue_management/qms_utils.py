import frappe


def resolve_service_names(items):
	"""Build a map of service IDs to human-readable names. Returns the map."""
	svc_ids = list({item.get("service") for item in items if item and item.get("service")})
	if not svc_ids:
		return {}
	svc_map = {}
	cache = frappe.cache()
	uncached_ids = []
	for sid in svc_ids:
		cached = cache.get_value(f"qms_service_name:{sid}")
		if cached:
			svc_map[sid] = cached
		else:
			uncached_ids.append(sid)
	if uncached_ids:
		for s in frappe.get_all("QMS Service", filters={"name": ("in", uncached_ids)}, fields=["name", "service_name"]):
			svc_map[s.name] = s.service_name
			cache.set_value(f"qms_service_name:{s.name}", s.service_name, expires_in_sec=300)
	return svc_map


def resolve_service_names_inplace(items):
	"""Replace service link IDs with human-readable names in-place."""
	svc_map = resolve_service_names(items)
	for item in items:
		if item and item.get("service") and item["service"] in svc_map:
			item["service"] = svc_map[item["service"]]


def normalize_rating_to_five_scale(value):
	"""Normalize legacy 0..1 ratings and current 1..5 ratings to a 1..5 scale."""
	if value in (None, ""):
		return 0
	try:
		rating = float(value)
	except (TypeError, ValueError):
		frappe.throw("Invalid rating value")
	if rating <= 1:
		rating *= 5
	rating = max(1, min(5, rating))
	return int(round(rating))


def estimated_wait_minutes(queue_position, estimated_service_time, num_counters=1):
	"""Estimate wait time from a 1-based queue position, service-time estimate,
	and the number of parallel counters serving this queue."""
	position = max(int(queue_position or 0), 0)
	service_time = max(int(estimated_service_time or 0), 0)
	counters = max(int(num_counters or 1), 1)
	if position <= 1:
		return 0
	return round((position - 1) * service_time / counters)


def validate_guest_input(value, field_name, max_length=200):
	"""Basic input validation for guest-accessible endpoints."""
	if value is None:
		return None
	value = str(value).strip()
	if len(value) > max_length:
		frappe.throw(f"{field_name} is too long (max {max_length} characters)")
	return value


def validate_phone(phone):
	"""Validate phone number format."""
	if not phone:
		return None
	import re
	phone = str(phone).strip()
	# Allow digits, spaces, dashes, parens, plus sign
	if not re.match(r'^[\d\s\-\(\)\+\.]{3,20}$', phone):
		frappe.throw("Invalid phone number format")
	return phone


def validate_email(email):
	"""Basic email validation."""
	if not email:
		return None
	email = str(email).strip()
	if len(email) > 200:
		frappe.throw("Email address is too long")
	from frappe.utils import validate_email_address
	if not validate_email_address(email):
		frappe.throw("Invalid email address")
	return email
