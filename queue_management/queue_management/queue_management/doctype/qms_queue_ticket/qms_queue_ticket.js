frappe.ui.form.on('QMS Queue Ticket', {
	refresh(frm) {
		if (frm.doc.status === 'Waiting') {
			frm.add_custom_button(__('Call'), () => {
				frappe.xcall('queue_management.qms_api.call_ticket', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
		}
		if (frm.doc.status === 'Called') {
			frm.add_custom_button(__('Start Serving'), () => {
				frappe.xcall('queue_management.qms_api.start_serving', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
		}
		if (frm.doc.status === 'Called' || frm.doc.status === 'Serving') {
			frm.add_custom_button(__('Complete'), () => {
				frappe.xcall('queue_management.qms_api.complete_ticket', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
			frm.add_custom_button(__('Hold'), () => {
				frappe.xcall('queue_management.qms_api.hold_ticket', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
			frm.add_custom_button(__('No Show'), () => {
				frappe.xcall('queue_management.qms_api.mark_no_show', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
			frm.add_custom_button(__('Transfer'), () => {
				let d = new frappe.ui.Dialog({
					title: __('Transfer Ticket'),
					fields: [
						{fieldname: 'counter', fieldtype: 'Link', options: 'QMS Counter', label: __('To Counter'), reqd: 1},
						{fieldname: 'reason', fieldtype: 'Small Text', label: __('Reason')},
					],
					primary_action_label: __('Transfer'),
					primary_action(values) {
						frappe.xcall('queue_management.qms_api.transfer_ticket', {
							ticket: frm.doc.name,
							to_counter: values.counter,
							reason: values.reason
						}).then(() => { d.hide(); frm.reload_doc(); });
					}
				});
				d.show();
			}, __('Actions'));
		}
		if (frm.doc.status === 'On Hold') {
			frm.add_custom_button(__('Resume'), () => {
				frappe.xcall('queue_management.qms_api.call_ticket', {ticket: frm.doc.name})
					.then(() => frm.reload_doc());
			}, __('Actions'));
		}
	}
});
