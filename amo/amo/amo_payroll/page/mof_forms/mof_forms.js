frappe.pages["mof-forms"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("MoF Tax Forms — نماذج وزارة المالية"),
		single_column: true,
	});

	page.main.html(`
		<div class="mof-forms-container" style="max-width:900px; margin:0 auto; padding:20px;">
			<div class="frappe-card" style="padding:20px; margin-bottom:20px;">
				<h4>${__("Select Form / إختر النموذج")}</h4>
				<div class="form-group">
					<label>${__("Form Type")}</label>
					<select class="form-control" id="mof-form-type">
						<option value="">-- ${__("Select")} --</option>
						<option value="R3">ر٣ — ${__("New Employee Registration")} — طلب تسجيل مستخدم/أجير جديد</option>
						<option value="R4">ر٤ — ${__("Employee Info Statement")} — بيان معلومات من المستخدم/الأجير</option>
						<option value="R5">ر٥ — ${__("Annual Tax Declaration")} — تصريح سنوي عن ضريبة الدخل</option>
						<option value="R6">ر٦ — ${__("Annual Individual Income")} — كشف سنوي إفرادي بإجمالي إيرادات</option>
						<option value="R7">ر٧ — ${__("Employees Who Left")} — كشف إجمالي بالمستخدمين الذين تركوا العمل</option>
						<option value="R10">ر١٠ — ${__("Periodic Tax Statement")} — بيان دوري بتأدية ضريبة الرواتب</option>
					</select>
				</div>
			</div>
			<div class="frappe-card" style="padding:20px; margin-bottom:20px; display:none;" id="mof-filters">
				<h4>${__("Parameters / المعايير")}</h4>
				<div id="mof-filter-fields"></div>
				<div style="margin-top:15px;">
					<button class="btn btn-primary btn-sm" id="mof-generate">${__("Generate PDF / إنشاء PDF")}</button>
					<button class="btn btn-default btn-sm" id="mof-preview" style="margin-right:10px;">${__("Preview / معاينة")}</button>
				</div>
			</div>
			<div id="mof-preview-area" style="display:none;">
				<div class="frappe-card" style="padding:20px;">
					<h4>${__("Preview / معاينة")}</h4>
					<iframe id="mof-preview-frame" style="width:100%; height:800px; border:1px solid #ddd;"></iframe>
				</div>
			</div>
		</div>
	`);

	let current_year = new Date().getFullYear();
	let year_options = "";
	for (let y = current_year; y >= current_year - 5; y--) {
		year_options += `<option value="${y}" ${y === current_year ? "selected" : ""}>${y}</option>`;
	}

	let filters = {};

	function render_filters(form_type) {
		let html = "";
		let needs = { company: false, year: false, employee: false, quarter: false };

		if (["R3", "R4"].includes(form_type)) {
			needs.employee = true;
		}
		if (["R5", "R7", "R10"].includes(form_type)) {
			needs.company = true;
			needs.year = true;
		}
		if (form_type === "R6") {
			needs.company = true;
			needs.year = true;
			needs.employee = true;
		}
		if (form_type === "R10") {
			needs.quarter = true;
		}

		if (needs.company) {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Company")}</label>
					<div id="mof-company-field"></div>
				</div>`;
		}
		if (needs.year) {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Fiscal Year")}</label>
					<select class="form-control" id="mof-year">${year_options}</select>
				</div>`;
		}
		if (needs.employee) {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Employee")}</label>
					<div id="mof-employee-field"></div>
				</div>`;
		}
		if (needs.quarter) {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Period Type")}</label>
					<select class="form-control" id="mof-period-type">
						<option value="Annual">${__("Annual")}</option>
						<option value="Quarterly">${__("Quarterly")}</option>
					</select>
				</div>
				<div class="form-group" style="margin-bottom:10px; display:none;" id="mof-quarter-group">
					<label>${__("Quarter")}</label>
					<select class="form-control" id="mof-quarter">
						<option value="Q1">Q1 (Jan-Mar)</option>
						<option value="Q2">Q2 (Apr-Jun)</option>
						<option value="Q3">Q3 (Jul-Sep)</option>
						<option value="Q4">Q4 (Oct-Dec)</option>
					</select>
				</div>`;
		}

		$("#mof-filter-fields").html(html);
		$("#mof-filters").show();

		// Initialize Frappe link fields
		if (needs.company) {
			filters.company = frappe.ui.form.make_control({
				df: { fieldtype: "Link", options: "Company", fieldname: "company", label: "Company" },
				parent: $("#mof-company-field"),
				render_input: true,
			});
			filters.company.set_value(frappe.defaults.get_user_default("Company") || "");
		}
		if (needs.employee) {
			filters.employee = frappe.ui.form.make_control({
				df: { fieldtype: "Link", options: "Employee", fieldname: "employee", label: "Employee" },
				parent: $("#mof-employee-field"),
				render_input: true,
			});
		}
		if (needs.quarter) {
			$("#mof-period-type").on("change", function () {
				if ($(this).val() === "Quarterly") {
					$("#mof-quarter-group").show();
				} else {
					$("#mof-quarter-group").hide();
				}
			});
		}
	}

	function get_params(form_type) {
		let params = {};
		if (filters.company) params.company = filters.company.get_value();
		if (filters.employee) params.employee = filters.employee.get_value();
		if ($("#mof-year").length) params.year = $("#mof-year").val();
		if ($("#mof-period-type").length) params.period_type = $("#mof-period-type").val();
		if (params.period_type === "Quarterly") params.quarter = $("#mof-quarter").val();
		return params;
	}

	function get_api_method(form_type) {
		let map = {
			R3: "amo.amo_payroll.mof_forms.mof_forms.generate_r3_pdf",
			R4: "amo.amo_payroll.mof_forms.mof_forms.generate_r4_pdf",
			R5: "amo.amo_payroll.mof_forms.mof_forms.generate_r5_pdf",
			R6: "amo.amo_payroll.mof_forms.mof_forms.generate_r6_pdf",
			R7: "amo.amo_payroll.mof_forms.mof_forms.generate_r7_pdf",
			R10: "amo.amo_payroll.mof_forms.mof_forms.generate_r10_pdf",
		};
		return map[form_type];
	}

	function validate_params(form_type, params) {
		if (["R3", "R4"].includes(form_type) && !params.employee) {
			frappe.msgprint(__("Please select an Employee"));
			return false;
		}
		if (["R5", "R7", "R10"].includes(form_type) && !params.company) {
			frappe.msgprint(__("Please select a Company"));
			return false;
		}
		if (form_type === "R6" && (!params.company || !params.employee)) {
			frappe.msgprint(__("Please select Company and Employee"));
			return false;
		}
		return true;
	}

	// Event handlers
	$("#mof-form-type").on("change", function () {
		let form_type = $(this).val();
		filters = {};
		if (form_type) {
			render_filters(form_type);
		} else {
			$("#mof-filters").hide();
		}
		$("#mof-preview-area").hide();
	});

	$(wrapper).on("click", "#mof-generate", function () {
		let form_type = $("#mof-form-type").val();
		let params = get_params(form_type);
		if (!validate_params(form_type, params)) return;

		let method = get_api_method(form_type);
		params._t = Date.now();
		let query = new URLSearchParams(params).toString();
		window.open(`/api/method/${method}?${query}`, "_blank");
	});

	$(wrapper).on("click", "#mof-preview", function () {
		let form_type = $("#mof-form-type").val();
		let params = get_params(form_type);
		if (!validate_params(form_type, params)) return;

		let method = get_api_method(form_type);
		params._t = Date.now();
		let query = new URLSearchParams(params).toString();
		$("#mof-preview-frame").attr("src", `/api/method/${method}?${query}`);
		$("#mof-preview-area").show();
	});
};
