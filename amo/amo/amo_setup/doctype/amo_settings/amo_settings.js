// Copyright (c) 2026, iPeng Holdings and contributors
// For license information, please see license.txt

frappe.ui.form.on("AMO Settings", {
	refresh(frm) {
		frm.disable_save();
		_render_demo_data_section(frm);
		_load_demo_stats(frm);
	},
});

/* ── Demo Data Section ── */
function _render_demo_data_section(frm) {
	const wrapper = frm.fields_dict.demo_data_html.$wrapper;
	wrapper.empty();
	wrapper.html(`
		<div class="amo-settings-panel" style="padding: 15px 0;">
			<p class="text-muted" style="margin-bottom: 12px;">
				Generate realistic demo employees with full details (names, family info, bank,
				education, personal details). All demo records are prefixed with
				<strong>[DEMO]</strong> and can be removed with one click.
			</p>
			<div id="demo-stats" style="margin-bottom: 15px;"></div>
			<div style="display: flex; gap: 10px; flex-wrap: wrap;">
				<button class="btn btn-primary btn-sm" id="btn-create-demo">
					<i class="fa fa-magic"></i>&nbsp; Create Demo Data
				</button>
				<button class="btn btn-success btn-sm" id="btn-attendance-demo">
					<i class="fa fa-calendar-check-o"></i>&nbsp; Generate Attendance &amp; Leaves
				</button>
				<button class="btn btn-default btn-sm" id="btn-lifecycle-demo" style="border-color: var(--purple-300); color: var(--purple-600);">
					<i class="fa fa-sitemap"></i>&nbsp; Generate HR Lifecycle
				</button>
				<button class="btn btn-default btn-sm" id="btn-assets-demo" style="border-color: var(--teal-300); color: var(--teal-600);">
					<i class="fa fa-building"></i>&nbsp; Generate Assets &amp; Inventory
				</button>
				<button class="btn btn-warning btn-sm" id="btn-link-demo">
					<i class="fa fa-link"></i>&nbsp; Link to Existing Employees
				</button>
				<button class="btn btn-info btn-sm" id="btn-backfill-demo">
					<i class="fa fa-pencil-square-o"></i>&nbsp; Backfill Missing Data
				</button>
				<button class="btn btn-danger btn-sm" id="btn-clean-demo">
					<i class="fa fa-trash"></i>&nbsp; Clear Demo Data
				</button>
			</div>
			<div id="demo-progress" style="margin-top: 12px; display: none;">
				<div class="progress">
					<div class="progress-bar progress-bar-striped active" role="progressbar"
						style="width: 0%; min-width: 2em;">0%</div>
				</div>
				<p class="demo-progress-text text-muted small" style="margin-top: 4px;"></p>
			</div>
		</div>
	`);

	/* Create Demo Data */
	wrapper.find("#btn-create-demo").on("click", function () {
		const count = frm.doc.number_of_employees || 20;
		frappe.confirm(
			`This will create <b>${count}</b> demo employees with all fields filled. Continue?`,
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.create_demo_data",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Link to Existing Employees */
	wrapper.find("#btn-link-demo").on("click", function () {
		frappe.confirm(
			"This will tag existing employees in the selected company as <b>[DEMO]</b> records" +
			" (adds '[DEMO]' prefix to Employee Number). Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.link_existing_demo_data",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Backfill Missing Data */
	wrapper.find("#btn-backfill-demo").on("click", function () {
		frappe.confirm(
			"This will add missing fields (department, employment type, passport, national ID, religion, personal details) to existing demo employees. Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.backfill_demo_data",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Generate Attendance & Leaves */
	wrapper.find("#btn-attendance-demo").on("click", function () {
		frappe.confirm(
			"This will create <b>Lebanese leave types</b>, leave policy, allocations, " +
			"and generate <b>daily attendance &amp; leave applications</b> for all demo employees " +
			"(current year). This may take a few minutes. Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.generate_demo_attendance",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Generate HR Lifecycle */
	wrapper.find("#btn-lifecycle-demo").on("click", function () {
		frappe.confirm(
			"This will create the full <b>recruitment pipeline</b> (Job Opening → Applicant → Interview → Offer) " +
			"and <b>performance appraisals</b> for demo employees. Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.generate_demo_lifecycle",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Generate Assets & Inventory */
	wrapper.find("#btn-assets-demo").on("click", function () {
		frappe.confirm(
			"This will create <b>fixed assets</b> (with movements, maintenance & repairs) " +
			"and <b>inventory transactions</b> (material requests, stock receipts, transfers & issues) " +
			"for all AMO companies. Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.generate_demo_assets_inventory",
					"amo_demo_progress",
					wrapper,
					frm,
				);
			},
		);
	});

	/* Clear Demo Data */
	wrapper.find("#btn-clean-demo").on("click", function () {
		frappe.confirm(
			"<b>This will permanently delete all [DEMO] employee records and their linked data.</b> Continue?",
			function () {
				_run_demo_action(
					"amo.amo_setup.demo_data.clear_demo_data",
					"amo_demo_cleanup",
					wrapper,
					frm,
				);
			},
		);
	});
}

/* ── Demo Stats ── */
function _load_demo_stats(frm) {
	frappe.call({
		method: "amo.amo_setup.demo_data.get_demo_data_stats",
		callback: function (r) {
			if (!r.message) return;
			const stats = r.message;
			const wrapper = frm.fields_dict.demo_data_html.$wrapper;
			const el = wrapper.find("#demo-stats");

			if (stats.total === 0) {
				el.html(
					'<span class="badge" style="background: var(--gray-300); color: var(--gray-700); padding: 4px 10px;">' +
					"No demo data present</span>",
				);
			} else {
				let badges = "";
				for (const [dt, count] of Object.entries(stats)) {
					if (dt === "total" || count === 0) continue;
					badges +=
						`<span class="badge" style="background: var(--blue-100); color: var(--blue-700); ` +
						`padding: 3px 8px; margin: 2px;">${dt}: ${count}</span> `;
				}
				el.html(`
					<div style="margin-bottom: 8px;">
						<span class="badge" style="background: var(--orange-100); color: var(--orange-700); padding: 4px 10px;">
							<strong>${stats.total}</strong> demo records
						</span>
					</div>
					<div>${badges}</div>
				`);
			}
		},
	});
}

/* ── Progress helper ── */
function _run_demo_action(method, event_name, wrapper, frm) {
	const progress = wrapper.find("#demo-progress");
	progress.show();
	wrapper.find("#btn-create-demo, #btn-attendance-demo, #btn-lifecycle-demo, #btn-assets-demo, #btn-link-demo, #btn-backfill-demo, #btn-clean-demo").prop("disabled", true);

	frappe.realtime.on(event_name, function (data) {
		progress.find(".progress-bar").css("width", data.percent + "%").text(data.percent + "%");
		progress.find(".demo-progress-text").text(data.stage || "");
		if (data.done) {
			frappe.realtime.off(event_name);
			wrapper.find("#btn-create-demo, #btn-attendance-demo, #btn-lifecycle-demo, #btn-assets-demo, #btn-link-demo, #btn-backfill-demo, #btn-clean-demo").prop("disabled", false);
			frappe.show_alert({ message: data.stage, indicator: "green" }, 7);
			_load_demo_stats(frm);
			setTimeout(function () {
				progress.fadeOut();
			}, 5000);
		}
	});

	frappe.call({
		method: method,
		callback: function () {
			/* stats reload handled by realtime done event */
		},
		error: function () {
			wrapper.find("#btn-create-demo, #btn-attendance-demo, #btn-lifecycle-demo, #btn-assets-demo, #btn-link-demo, #btn-backfill-demo, #btn-clean-demo").prop("disabled", false);
			progress.hide();
		},
	});
}
