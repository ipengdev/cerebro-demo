frappe.pages["cnss-reports"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("CNSS Reports — تقارير الضمان الاجتماعي"),
		single_column: true,
	});

	page.main.html(`
		<div class="cnss-reports-container" style="max-width:1200px; margin:0 auto; padding:20px;">
			<div class="frappe-card" style="padding:20px; margin-bottom:20px;">
				<h4>${__("Select Report / إختر التقرير")}</h4>
				<div class="form-group">
					<label>${__("Report Type")}</label>
					<select class="form-control" id="cnss-report-type">
						<option value="">-- ${__("Select")} --</option>
						<option value="CNSS Monthly Declaration">${__("CNSS Monthly Declaration")} — التصريح الشهري للضمان</option>
						<option value="CNSS Yearly Declaration">${__("CNSS Yearly Declaration")} — التصريح السنوي للضمان</option>
						<option value="Employee Joining Report">${__("Employee Joining Report")} — تقرير التحاق الموظفين</option>
						<option value="Employee Leaving Report">${__("Employee Leaving Report")} — تقرير ترك الموظفين</option>
					</select>
				</div>
			</div>
			<div class="frappe-card" style="padding:20px; margin-bottom:20px; display:none;" id="cnss-filters">
				<h4>${__("Parameters / المعايير")}</h4>
				<div id="cnss-filter-fields"></div>
				<div style="margin-top:15px;">
					<button class="btn btn-primary btn-sm" id="cnss-run">${__("Run Report / تشغيل التقرير")}</button>
					<button class="btn btn-success btn-sm" id="cnss-pdf" style="margin-left:10px; display:none;">${__("Generate PDF / إنشاء PDF")}</button>
					<button class="btn btn-default btn-sm" id="cnss-preview" style="margin-left:10px; display:none;">${__("Preview / معاينة")}</button>
					<button class="btn btn-default btn-sm" id="cnss-export" style="margin-left:10px; display:none;">${__("Export to Excel")}</button>
				</div>
			</div>
			<div id="cnss-preview-area" style="display:none;">
				<div class="frappe-card" style="padding:20px;">
					<h4>${__("Preview / معاينة")}</h4>
					<iframe id="cnss-preview-frame" style="width:100%; height:800px; border:1px solid #ddd;"></iframe>
				</div>
			</div>
			<div id="cnss-summary-area" style="display:none;">
				<div class="frappe-card" style="padding:15px; margin-bottom:20px;">
					<div id="cnss-summary" style="display:flex; flex-wrap:wrap; gap:20px;"></div>
				</div>
			</div>
			<div id="cnss-result-area" style="display:none;">
				<div class="frappe-card" style="padding:20px;">
					<div id="cnss-datatable-wrapper"></div>
				</div>
			</div>
		</div>
	`);

	let current_year = new Date().getFullYear();
	let year_options = "";
	for (let y = current_year; y >= current_year - 5; y--) {
		year_options += `<option value="${y}" ${y === current_year ? "selected" : ""}>${y}</option>`;
	}

	let month_options = [
		{ value: 1, label: __("January") },
		{ value: 2, label: __("February") },
		{ value: 3, label: __("March") },
		{ value: 4, label: __("April") },
		{ value: 5, label: __("May") },
		{ value: 6, label: __("June") },
		{ value: 7, label: __("July") },
		{ value: 8, label: __("August") },
		{ value: 9, label: __("September") },
		{ value: 10, label: __("October") },
		{ value: 11, label: __("November") },
		{ value: 12, label: __("December") },
	];
	let current_month = new Date().getMonth() + 1;
	let month_opts_html = month_options
		.map((m) => `<option value="${m.value}" ${m.value === current_month ? "selected" : ""}>${m.label}</option>`)
		.join("");

	let filters = {};
	let last_columns = [];
	let last_data = [];
	let datatable = null;

	function render_filters(report_type) {
		let html = "";
		filters = {};

		// Company — all reports need it
		html += `
			<div class="form-group" style="margin-bottom:10px;">
				<label>${__("Company")}</label>
				<div id="cnss-company-field"></div>
			</div>`;

		if (report_type === "CNSS Monthly Declaration") {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Month")}</label>
					<select class="form-control" id="cnss-month">${month_opts_html}</select>
				</div>
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Year")}</label>
					<select class="form-control" id="cnss-year">${year_options}</select>
				</div>`;
		} else if (report_type === "CNSS Yearly Declaration") {
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Year")}</label>
					<select class="form-control" id="cnss-year">${year_options}</select>
				</div>`;
		} else {
			// Employee Joining / Leaving
			html += `
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("From Date")}</label>
					<div id="cnss-from-date-field"></div>
				</div>
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("To Date")}</label>
					<div id="cnss-to-date-field"></div>
				</div>
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Department")}</label>
					<div id="cnss-department-field"></div>
				</div>
				<div class="form-group" style="margin-bottom:10px;">
					<label>${__("Employee")}</label>
					<div id="cnss-employee-field"></div>
				</div>`;
		}

		$("#cnss-filter-fields").html(html);
		$("#cnss-filters").show();

		// Initialize company link field
		filters.company = frappe.ui.form.make_control({
			df: { fieldtype: "Link", options: "Company", fieldname: "company", label: "Company" },
			parent: $("#cnss-company-field"),
			render_input: true,
		});
		filters.company.set_value(frappe.defaults.get_user_default("Company") || "");

		// Date and department fields for joining/leaving reports
		if (["Employee Joining Report", "Employee Leaving Report"].includes(report_type)) {
			filters.from_date = frappe.ui.form.make_control({
				df: { fieldtype: "Date", fieldname: "from_date", label: "From Date" },
				parent: $("#cnss-from-date-field"),
				render_input: true,
			});
			filters.from_date.set_value(frappe.datetime.add_months(frappe.datetime.get_today(), -1));

			filters.to_date = frappe.ui.form.make_control({
				df: { fieldtype: "Date", fieldname: "to_date", label: "To Date" },
				parent: $("#cnss-to-date-field"),
				render_input: true,
			});
			filters.to_date.set_value(frappe.datetime.get_today());

			filters.department = frappe.ui.form.make_control({
				df: { fieldtype: "Link", options: "Department", fieldname: "department", label: "Department" },
				parent: $("#cnss-department-field"),
				render_input: true,
			});

			filters.employee = frappe.ui.form.make_control({
				df: { fieldtype: "Link", options: "Employee", fieldname: "employee", label: "Employee" },
				parent: $("#cnss-employee-field"),
				render_input: true,
			});
		}
	}

	function get_filters(report_type) {
		let f = {};
		if (filters.company) f.company = filters.company.get_value();

		if (report_type === "CNSS Monthly Declaration") {
			f.month = $("#cnss-month").val();
			f.year = $("#cnss-year").val();
		} else if (report_type === "CNSS Yearly Declaration") {
			f.year = $("#cnss-year").val();
		} else {
			if (filters.from_date) f.from_date = filters.from_date.get_value();
			if (filters.to_date) f.to_date = filters.to_date.get_value();
			if (filters.department) {
				let dept = filters.department.get_value();
				if (dept) f.department = dept;
			}
			if (filters.employee) {
				let emp = filters.employee.get_value();
				if (emp) f.employee = emp;
			}
		}
		return f;
	}

	function validate_filters(report_type, f) {
		if (!f.company) {
			frappe.msgprint(__("Please select a Company"));
			return false;
		}
		if (report_type === "CNSS Monthly Declaration" && (!f.month || !f.year)) {
			frappe.msgprint(__("Please select Month and Year"));
			return false;
		}
		if (report_type === "CNSS Yearly Declaration" && !f.year) {
			frappe.msgprint(__("Please select a Year"));
			return false;
		}
		if (["Employee Joining Report", "Employee Leaving Report"].includes(report_type)) {
			if (!f.from_date || !f.to_date) {
				frappe.msgprint(__("Please select From Date and To Date"));
				return false;
			}
		}
		return true;
	}

	function render_summary(summary) {
		if (!summary || !summary.length) {
			$("#cnss-summary-area").hide();
			return;
		}
		let html = summary
			.map((s) => {
				let formatted_value = s.value;
				if (s.datatype === "Currency") {
					formatted_value = format_currency(s.value);
				} else if (s.datatype === "Int") {
					formatted_value = cint(s.value).toLocaleString();
				}
				let color = {
					blue: "#5e64ff",
					green: "#29cd42",
					orange: "#ffa00a",
					red: "#fc4f51",
					pink: "#ed5a99",
				}[s.indicator] || "#333";
				return `<div style="text-align:center; min-width:120px;">
					<div style="font-size:1.4em; font-weight:600; color:${color};">${formatted_value}</div>
					<div style="font-size:0.85em; color:#888; margin-top:2px;">${__(s.label)}</div>
				</div>`;
			})
			.join("");
		$("#cnss-summary").html(html);
		$("#cnss-summary-area").show();
	}

	function render_datatable(columns, data) {
		last_columns = columns;
		last_data = data;

		if (datatable) {
			datatable.destroy();
			datatable = null;
		}
		$("#cnss-datatable-wrapper").empty();

		if (!data || !data.length) {
			$("#cnss-datatable-wrapper").html(
				`<div style="text-align:center; padding:40px; color:#888;">${__("No data found")}</div>`
			);
			$("#cnss-result-area").show();
			$("#cnss-export").hide();
			return;
		}

		let dt_columns = columns.map((col) => ({
			name: col.label,
			id: col.fieldname,
			width: col.width || 150,
			format: (value) => {
				if (col.fieldtype === "Currency" && value != null) {
					return format_currency(value);
				}
				if (col.fieldtype === "Date" && value) {
					return frappe.datetime.str_to_user(value);
				}
				if (col.fieldtype === "Link" && value) {
					return value;
				}
				return value != null ? value : "";
			},
		}));

		let dt_data = data.map((row) => columns.map((col) => row[col.fieldname]));

		datatable = new frappe.DataTable("#cnss-datatable-wrapper", {
			columns: dt_columns,
			data: dt_data,
			dynamicRowHeight: true,
			inlineFilters: true,
			layout: "fluid",
			noDataMessage: __("No data found"),
		});

		$("#cnss-result-area").show();
		$("#cnss-export").show();
	}

	function run_report() {
		let report_type = $("#cnss-report-type").val();
		if (!report_type) return;

		let f = get_filters(report_type);
		if (!validate_filters(report_type, f)) return;

		frappe.call({
			method: "frappe.desk.query_report.run",
			args: {
				report_name: report_type,
				filters: f,
			},
			freeze: true,
			freeze_message: __("Loading report..."),
			callback: function (r) {
				if (r && r.message) {
					let result = r.message;
					render_summary(result.report_summary || []);
					render_datatable(result.columns || [], result.result || []);
				}
			},
		});
	}

	function export_report() {
		if (!last_data || !last_data.length) return;
		let report_type = $("#cnss-report-type").val();
		let f = get_filters(report_type);

		// Use Frappe's built-in report export
		let args = {
			cmd: "frappe.desk.query_report.export_query",
			report_name: report_type,
			filters: JSON.stringify(f),
			file_format_type: "Excel",
		};
		open_url_post(frappe.request.url, args);
	}

	function get_pdf_method(report_type) {
		let map = {
			"CNSS Monthly Declaration": "amo.amo_payroll.cnss_forms.cnss_forms.generate_cnss_monthly_pdf",
			"CNSS Yearly Declaration": "amo.amo_payroll.cnss_forms.cnss_forms.generate_cnss_yearly_pdf",
			"Employee Joining Report": "amo.amo_payroll.cnss_forms.cnss_forms.generate_employee_joining_pdf",
			"Employee Leaving Report": "amo.amo_payroll.cnss_forms.cnss_forms.generate_employee_leaving_pdf",
		};
		return map[report_type];
	}

	function get_pdf_args(report_type, f) {
		let args = { company: f.company };
		if (report_type === "CNSS Monthly Declaration") {
			args.month = f.month;
			args.year = f.year;
		} else if (report_type === "CNSS Yearly Declaration") {
			args.year = f.year;
		} else {
			args.from_date = f.from_date;
			args.to_date = f.to_date;
			if (f.department) args.department = f.department;
			if (f.employee) args.employee = f.employee;
		}
		return args;
	}

	function generate_pdf() {
		let report_type = $("#cnss-report-type").val();
		if (!report_type) return;

		let f = get_filters(report_type);
		if (!validate_filters(report_type, f)) return;

		let method = get_pdf_method(report_type);
		if (!method) return;

		let args = get_pdf_args(report_type, f);
		args._t = Date.now();
		let query = new URLSearchParams(args).toString();
		window.open(`/api/method/${method}?${query}`, "_blank");
	}

	function preview_pdf() {
		let report_type = $("#cnss-report-type").val();
		if (!report_type) return;

		let f = get_filters(report_type);
		if (!validate_filters(report_type, f)) return;

		let method = get_pdf_method(report_type);
		if (!method) return;

		let args = get_pdf_args(report_type, f);
		args._t = Date.now();
		let query = new URLSearchParams(args).toString();
		$("#cnss-preview-frame").attr("src", `/api/method/${method}?${query}`);
		$("#cnss-preview-area").show();
	}

	// Event handlers
	$("#cnss-report-type").on("change", function () {
		let report_type = $(this).val();
		if (report_type) {
			render_filters(report_type);
			// Show PDF and Preview buttons once a report type is selected
			$("#cnss-pdf").show();
			$("#cnss-preview").show();
		} else {
			$("#cnss-filters").hide();
			$("#cnss-pdf").hide();
			$("#cnss-preview").hide();
		}
		$("#cnss-result-area").hide();
		$("#cnss-summary-area").hide();
		$("#cnss-preview-area").hide();
		$("#cnss-export").hide();
	});

	$(wrapper).on("click", "#cnss-run", function () {
		run_report();
	});

	$(wrapper).on("click", "#cnss-export", function () {
		export_report();
	});

	$(wrapper).on("click", "#cnss-pdf", function () {
		generate_pdf();
	});

	$(wrapper).on("click", "#cnss-preview", function () {
		preview_pdf();
	});
};
