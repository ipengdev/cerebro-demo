import frappe

no_cache = True
allow_guest = True


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.title = "Queue Access"
	branding = frappe.db.get_value(
		"QMS Settings",
		"QMS Settings",
		["hospital_name", "hospital_logo", "background_image"],
		as_dict=True,
	) or {}
	context.hospital_name = branding.get("hospital_name") or "Queue Management"
	context.hospital_logo = branding.get("hospital_logo") or ""
	context.background_image = branding.get("background_image") or ""