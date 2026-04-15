frappe.ui.form.on("Lebanese Payroll Settings", {
	refresh(frm) {
		// Auto-calculate monthly transport
		frm.trigger("calculate_monthly_transport");

		// Populate default tax slabs if empty
		if (!frm.doc.tax_slabs || frm.doc.tax_slabs.length === 0) {
			frm.trigger("populate_default_slabs");
		}

		// Add action buttons
		frm.add_custom_button(
			__("Create Payroll Data"),
			() => frm.trigger("create_payroll_data"),
			__("Actions")
		);
		frm.add_custom_button(
			__("Clear Payroll Data"),
			() => frm.trigger("clear_payroll_data"),
			__("Actions")
		);

		// Style the clear button red
		frm.$wrapper
			.find('.btn-group .dropdown-menu a:contains("Clear Payroll Data")')
			.css("color", "var(--red-500)");

		if (frm.doc.data_created) {
			frm.dashboard.set_headline(
				__("Payroll data has been created for {0}", [frm.doc.company]),
				"green"
			);
		}
	},

	transport_allowance_daily(frm) {
		frm.trigger("calculate_monthly_transport");
	},

	working_days_per_month(frm) {
		frm.trigger("calculate_monthly_transport");
	},

	calculate_monthly_transport(frm) {
		let daily = flt(frm.doc.transport_allowance_daily);
		let days = cint(frm.doc.working_days_per_month) || 22;
		frm.set_value("transport_allowance_monthly", daily * days);
	},

	populate_default_slabs(frm) {
		const slabs = [
			{ from_amount: 0, to_amount: 18000000, rate: 2 },
			{ from_amount: 18000001, to_amount: 45000000, rate: 4 },
			{ from_amount: 45000001, to_amount: 90000000, rate: 7 },
			{ from_amount: 90000001, to_amount: 180000000, rate: 11 },
			{ from_amount: 180000001, to_amount: 360000000, rate: 15 },
			{ from_amount: 360000001, to_amount: 675000000, rate: 20 },
			{ from_amount: 675000001, to_amount: 0, rate: 25 },
		];

		slabs.forEach((slab) => {
			let row = frm.add_child("tax_slabs");
			row.from_amount = slab.from_amount;
			row.to_amount = slab.to_amount;
			row.rate = slab.rate;
		});
		frm.refresh_field("tax_slabs");
		frm.dirty();
	},

	create_payroll_data(frm) {
		if (!frm.doc.company) {
			frappe.msgprint(__("Please select a Company first."));
			return;
		}

		if (frm.is_dirty()) {
			frappe.msgprint(__("Please save the settings before creating data."));
			return;
		}

		frappe.confirm(
			__(
				"This will create Salary Components, Income Tax Slab, Payroll Constants, and Salary Structure for <b>{0}</b>. Continue?",
				[frm.doc.company]
			),
			() => {
				frappe.call({
					method:
						"amo.amo_payroll.doctype.lebanese_payroll_settings.lebanese_payroll_settings.create_payroll_data",
					args: { company: frm.doc.company },
					freeze: true,
					freeze_message: __("Creating Lebanese payroll data..."),
					callback(r) {
						if (r.message) {
							frappe.msgprint({
								title: __("Payroll Data Created"),
								message: r.message,
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			}
		);
	},

	clear_payroll_data(frm) {
		if (!frm.doc.company) {
			frappe.msgprint(__("Please select a Company first."));
			return;
		}

		frappe.confirm(
			__(
				"<b style='color:var(--red-500)'>Warning:</b> This will permanently delete the Lebanese payroll data created for <b>{0}</b> including Salary Components, Income Tax Slab, Payroll Constants, and Salary Structure. This cannot be undone. Continue?",
				[frm.doc.company]
			),
			() => {
				frappe.call({
					method:
						"amo.amo_payroll.doctype.lebanese_payroll_settings.lebanese_payroll_settings.clear_payroll_data",
					args: { company: frm.doc.company },
					freeze: true,
					freeze_message: __("Clearing Lebanese payroll data..."),
					callback(r) {
						if (r.message) {
							frappe.msgprint({
								title: __("Payroll Data Cleared"),
								message: r.message,
								indicator: "orange",
							});
							frm.reload_doc();
						}
					},
				});
			}
		);
	},
});
