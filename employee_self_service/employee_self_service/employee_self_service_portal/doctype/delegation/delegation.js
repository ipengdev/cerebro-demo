frappe.ui.form.on("Delegation", {
	refresh(frm) {
		frm.set_query("user", function () {
			return {
				filters: { enabled: 1, user_type: "System User" },
			};
		});

		frm.set_query("delegate", function () {
			return {
				filters: { enabled: 1, user_type: "System User" },
			};
		});

		// Show activate/deactivate buttons for HR Manager and System Manager
		if (frm.doc.docstatus === 1) {
			if (frm.doc.status === "Pending") {
				frm.add_custom_button(__("Activate Now"), function () {
					frappe.confirm(
						__("Are you sure you want to activate this delegation immediately?"),
						function () {
							frappe.call({
								method: "employee_self_service.employee_self_service_portal.doctype.delegation.delegation.activate_delegation_manually",
								args: { delegation_name: frm.doc.name },
								callback: function () {
									frm.reload_doc();
								},
							});
						}
					);
				}, __("Actions"));
			}

			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Deactivate Now"), function () {
					frappe.confirm(
						__("Are you sure you want to deactivate this delegation immediately?"),
						function () {
							frappe.call({
								method: "employee_self_service.employee_self_service_portal.doctype.delegation.delegation.deactivate_delegation_manually",
								args: { delegation_name: frm.doc.name },
								callback: function () {
									frm.reload_doc();
								},
							});
						}
					);
				}, __("Actions"));
			}
		}

		// Color-coded status indicator
		if (frm.doc.status) {
			const colors = {
				Pending: "orange",
				Active: "blue",
				Completed: "green",
				Cancelled: "red",
			};
			frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "gray");
		}
	},

	delegation_type(frm) {
		if (frm.doc.delegation_type === "All Roles") {
			frm.set_value("roles_to_delegate", []);
		}
	},

	user(frm) {
		if (frm.doc.user && frm.doc.delegate && frm.doc.user === frm.doc.delegate) {
			frappe.msgprint(__("User and Delegate cannot be the same person."));
			frm.set_value("delegate", "");
		}
	},

	delegate(frm) {
		if (frm.doc.user && frm.doc.delegate && frm.doc.user === frm.doc.delegate) {
			frappe.msgprint(__("User and Delegate cannot be the same person."));
			frm.set_value("delegate", "");
		}
	},
});
