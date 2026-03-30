frappe.ui.form.on('QMS Appointment', {
	refresh(frm) {
		if (frm.doc.status === 'Scheduled' || frm.doc.status === 'Confirmed') {
			frm.add_custom_button(__('Check In'), () => {
				frappe.xcall('queue_management.qms_api.checkin_appointment', {appointment: frm.doc.name})
					.then(() => frm.reload_doc());
			});
		}
	}
});
