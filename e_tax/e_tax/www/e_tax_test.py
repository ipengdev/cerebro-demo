import frappe

no_cache = 1


def get_context():
	frappe.db.commit()
	context = frappe._dict()
	context.boot = frappe._dict(
		{
			"csrf_token": frappe.sessions.get_csrf_token(),
		}
	)
	return context
