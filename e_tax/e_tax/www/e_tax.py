import frappe
from frappe.utils import cint, get_system_timezone

no_cache = 1


def get_context():
	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	return context


def get_boot():
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"site_name": frappe.local.site,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"sysdefaults": frappe.defaults.get_defaults(),
			"is_fc_site": 0,
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
		}
	)
