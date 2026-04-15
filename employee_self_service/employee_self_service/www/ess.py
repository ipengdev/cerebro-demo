import frappe
from frappe import _
from frappe.utils import get_system_timezone
from frappe.utils.telemetry import capture

no_cache = 1


def get_context():
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/ess"
		raise frappe.Redirect

	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	desk_theme = frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"site_name": frappe.local.site,
			"default_route": "/ess/dashboard",
			"csrf_token": frappe.sessions.get_csrf_token(),
			"default_currency": frappe.db.get_default("currency") or "USD",
			"desk_theme": desk_theme.lower(),
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
		}
	)
