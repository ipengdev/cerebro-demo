frappe.ui.form.on('QMS Staff Assignment', {
	refresh(frm) {
		// Auto-fill employee name
	},
	employee(frm) {
		if (frm.doc.employee) {
			frappe.db.get_value('Employee', frm.doc.employee, 'employee_name').then(r => {
				if (r.message) frm.set_value('employee_name', r.message.employee_name);
			});
		}
	}
});
