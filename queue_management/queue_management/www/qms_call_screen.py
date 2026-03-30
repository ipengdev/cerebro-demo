import frappe

no_cache = True
allow_guest = True


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.title = "QMS Call Screen"
	branding = frappe.db.get_value(
		"QMS Settings", "QMS Settings",
		["hospital_name"],
		as_dict=True,
	) or {}
	context.hospital_name = branding.get("hospital_name") or "Queue Management"