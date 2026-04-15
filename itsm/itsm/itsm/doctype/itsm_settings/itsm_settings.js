// Copyright (c) 2026, iPeng Holdings and contributors
// For license information, please see license.txt

frappe.ui.form.on("ITSM Settings", {
	refresh(frm) {
		frm.disable_save();
		_render_demo_data_section(frm);
		_render_auto_discovery_section(frm);
		_load_demo_stats(frm);
	},
});

function _render_demo_data_section(frm) {
	const wrapper = frm.fields_dict.demo_data_html.$wrapper;
	wrapper.empty();
	wrapper.html(`
		<div class="itsm-settings-panel" style="padding: 15px 0;">
			<p class="text-muted" style="margin-bottom: 12px;">
				Generate realistic demo data (assets, tickets, contracts, CMDB, discovery results) to explore ITSM features.
				All demo records are prefixed with <strong>[DEMO]</strong> and can be removed with one click.
			</p>
			<div id="demo-stats" style="margin-bottom: 15px;"></div>
			<div style="display: flex; gap: 10px; flex-wrap: wrap;">
				<button class="btn btn-primary btn-sm" id="btn-create-demo">
					<i class="fa fa-magic"></i>&nbsp; Create Demo Data
				</button>
				<button class="btn btn-danger btn-sm" id="btn-clean-demo">
					<i class="fa fa-trash"></i>&nbsp; Clean Demo Data
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

	wrapper.find("#btn-create-demo").on("click", function () {
		frappe.confirm(
			"This will create demo data across all ITSM modules. Continue?",
			function () {
				_run_demo_action("itsm.demo_data.create_demo_data", "itsm_demo_progress", wrapper, frm);
			}
		);
	});

	wrapper.find("#btn-clean-demo").on("click", function () {
		frappe.confirm(
			"<b>This will permanently delete all [DEMO] records.</b> Continue?",
			function () {
				_run_demo_action("itsm.demo_data.clean_demo_data", "itsm_demo_cleanup", wrapper, frm);
			}
		);
	});
}

function _render_auto_discovery_section(frm) {
	const wrapper = frm.fields_dict.auto_discovery_html.$wrapper;
	wrapper.empty();
	wrapper.html(`
		<div class="itsm-settings-panel" style="padding: 15px 0;">
			<p class="text-muted" style="margin-bottom: 12px;">
				Run a zero-config network scan to discover devices on all local subnets.
				No probes or schedules needed — just click the button.
			</p>
			<div style="display: flex; gap: 10px; flex-wrap: wrap;">
				<button class="btn btn-primary btn-sm" id="btn-auto-discover">
					<i class="fa fa-search"></i>&nbsp; Run Auto Discovery
				</button>
			</div>
			<div id="discovery-progress" style="margin-top: 12px; display: none;">
				<div class="progress">
					<div class="progress-bar progress-bar-info progress-bar-striped active" role="progressbar"
						style="width: 0%; min-width: 2em;">0%</div>
				</div>
				<p class="discovery-progress-text text-muted small" style="margin-top: 4px;"></p>
			</div>
		</div>
	`);

	wrapper.find("#btn-auto-discover").on("click", function () {
		frappe.confirm(
			"This will scan the local network to discover devices. Continue?",
			function () {
				const btn = wrapper.find("#btn-auto-discover");
				btn.prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i>&nbsp; Scanning...');

				const progress = wrapper.find("#discovery-progress");
				progress.show();

				frappe.realtime.on("itsm_auto_discovery", function (data) {
					progress.find(".progress-bar").css("width", data.percent + "%").text(data.percent + "%");
					progress.find(".discovery-progress-text").text(data.stage || "");
					if (data.done) {
						frappe.realtime.off("itsm_auto_discovery");
						btn.prop("disabled", false).html('<i class="fa fa-search"></i>&nbsp; Run Auto Discovery');
						frappe.show_alert({message: data.stage, indicator: "green"}, 7);
						setTimeout(function () { progress.fadeOut(); }, 5000);
					}
				});

				frappe.call({
					method: "itsm.asset_discovery.discovery_engine.auto_discover",
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({
								message: `Discovered ${r.message.hosts_found || 0} hosts, created ${r.message.assets_created || 0} assets`,
								indicator: "green"
							}, 7);
						}
					},
					error: function () {
						btn.prop("disabled", false).html('<i class="fa fa-search"></i>&nbsp; Run Auto Discovery');
						progress.hide();
					}
				});
			}
		);
	});
}

function _load_demo_stats(frm) {
	frappe.call({
		method: "itsm.demo_data.get_demo_data_stats",
		callback: function (r) {
			if (!r.message) return;
			const stats = r.message;
			const wrapper = frm.fields_dict.demo_data_html.$wrapper;
			const el = wrapper.find("#demo-stats");

			if (stats.total === 0) {
				el.html('<span class="badge" style="background: var(--gray-300); color: var(--gray-700); padding: 4px 10px;">No demo data present</span>');
			} else {
				let badges = "";
				for (const [dt, count] of Object.entries(stats)) {
					if (dt === "total" || count === 0) continue;
					badges += `<span class="badge" style="background: var(--blue-100); color: var(--blue-700); padding: 3px 8px; margin: 2px;">${dt}: ${count}</span> `;
				}
				el.html(`
					<div style="margin-bottom: 8px;">
						<span class="badge" style="background: var(--orange-100); color: var(--orange-700); padding: 4px 10px;">
							<strong>${stats.total}</strong> demo records present
						</span>
					</div>
					<div>${badges}</div>
				`);
			}
		}
	});
}

function _run_demo_action(method, event_name, wrapper, frm) {
	const progress = wrapper.find("#demo-progress");
	progress.show();
	wrapper.find("#btn-create-demo, #btn-clean-demo").prop("disabled", true);

	frappe.realtime.on(event_name, function (data) {
		progress.find(".progress-bar").css("width", data.percent + "%").text(data.percent + "%");
		progress.find(".demo-progress-text").text(data.stage || "");
		if (data.done) {
			frappe.realtime.off(event_name);
			wrapper.find("#btn-create-demo, #btn-clean-demo").prop("disabled", false);
			frappe.show_alert({message: data.stage, indicator: "green"}, 7);
			_load_demo_stats(frm);
			setTimeout(function () { progress.fadeOut(); }, 5000);
		}
	});

	frappe.call({
		method: method,
		callback: function (r) {
			if (r.message) {
				_load_demo_stats(frm);
			}
		},
		error: function () {
			wrapper.find("#btn-create-demo, #btn-clean-demo").prop("disabled", false);
			progress.hide();
		}
	});
}
