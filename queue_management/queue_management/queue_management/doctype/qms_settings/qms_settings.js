frappe.ui.form.on('QMS Settings', {
	refresh(frm) {
		frm.add_custom_button(__('Load Demo Data'), () => {
			frappe.confirm(
				__('This will create sample locations, services, counters and tickets. Continue?'),
				() => {
					frappe.xcall('queue_management.demo_data.create_demo_data')
						.then(() => frappe.show_alert({message: __('Demo data created!'), indicator: 'green'}));
				}
			);
		});
	}
});
