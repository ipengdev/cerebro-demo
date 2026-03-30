frappe.ui.form.on('QMS Counter', {
	refresh(frm) {
		if (frm.doc.status === 'Available') {
			frm.add_custom_button(__('Call Next'), () => {
				frappe.xcall('queue_management.qms_api.call_next_ticket', {counter: frm.doc.name})
					.then(r => {
						if (r) frappe.show_alert({message: __('Called ticket: {0}', [r.ticket_number]), indicator: 'green'});
						else frappe.show_alert({message: __('No tickets waiting'), indicator: 'orange'});
						frm.reload_doc();
					});
			});
		}
	}
});
