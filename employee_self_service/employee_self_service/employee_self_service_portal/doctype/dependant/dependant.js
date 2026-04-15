frappe.ui.form.on("Dependant", {
	employee: function (frm) {
		if (frm.doc.employee) {
			frm.set_value(
				"employee_name",
				frm.doc.employee_name || ""
			);
		}
	},
	first_name: function (frm) {
		set_full_name(frm);
	},
	middle_name: function (frm) {
		set_full_name(frm);
	},
	last_name: function (frm) {
		set_full_name(frm);
	},
});

function set_full_name(frm) {
	var parts = [frm.doc.first_name, frm.doc.middle_name, frm.doc.last_name];
	frm.set_value(
		"full_name",
		parts.filter(Boolean).join(" ")
	);
}
