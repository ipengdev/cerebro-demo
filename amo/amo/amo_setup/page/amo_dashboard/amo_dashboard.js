frappe.pages['amo-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'AMO Dashboard',
		single_column: true
	});

	let views = [
		{ key: 'Faculty & Programs', icon: 'fa-university', label: 'Faculty & Programs' },
		{ key: 'Cost Allocation', icon: 'fa-pie-chart', label: 'Cost Allocation' },
		{ key: 'Tuition & Scholarships', icon: 'fa-graduation-cap', label: 'Tuition & Aid' },
		{ key: 'Grants & Research', icon: 'fa-flask', label: 'Grants & Research' },
		{ key: 'Multi-Year Planning', icon: 'fa-line-chart', label: 'Multi-Year' },
		{ key: 'Rector Executive', icon: 'fa-shield', label: 'Executive' },
	];

	let tabs_html = views.map((v, i) =>
		`<div class="amo-nav-tab${i === 0 ? ' active' : ''}" data-view="${v.key}"><i class="fa ${v.icon}"></i>${v.label}</div>`
	).join('');

	page.main.html(`
		<div class="amo-dashboard">
			<div class="amo-header">
				<div class="amo-header-inner">
					<div class="amo-header-top">
						<div class="amo-header-brand">
							<img src="/assets/amo/images/amo-icon.png" alt="AMO" onerror="this.style.display='none'">
							<h3>AMO Dashboard<span>Financial Analytics</span></h3>
						</div>
						<div class="amo-header-meta">
							<div class="amo-refresh-time"><i class="fa fa-clock-o"></i> <span id="amo-last-refresh">--</span></div>
							<button class="amo-refresh-btn" id="amo-refresh-btn"><i class="fa fa-refresh"></i> Refresh</button>
						</div>
					</div>
					<div class="amo-nav-tabs">${tabs_html}</div>
				</div>
			</div>
			<div class="amo-filter-bar">
				<div class="amo-filter-bar-inner">
					<div id="amo-company-filter"></div>
				</div>
			</div>
			<div id="amo-dash-content" class="amo-content"></div>
		</div>
	`);

	let company_filter = frappe.ui.form.make_control({
		df: {
			fieldtype: 'Link',
			options: 'Company',
			fieldname: 'company',
			label: 'Filter by Campus / Entity',
			placeholder: 'All Campuses & Entities',
			get_query: () => ({
				filters: { 'parent_company': ['like', 'AMO%'] }
			})
		},
		parent: page.main.find('#amo-company-filter'),
		render_input: true
	});

	let current_view = views[0].key;

	function $c() { return page.main.find('#amo-dash-content'); }

	// ── Tab click handler ────────────────────────────────────────
	page.main.find('.amo-nav-tab').on('click', function() {
		page.main.find('.amo-nav-tab').removeClass('active');
		$(this).addClass('active');
		current_view = $(this).data('view');
		load_view();
	});

	// ── Refresh button ───────────────────────────────────────────
	page.main.find('#amo-refresh-btn').on('click', function() {
		$(this).addClass('spinning');
		load_view();
		setTimeout(() => $(this).removeClass('spinning'), 800);
	});

	// ── View router ──────────────────────────────────────────────
	function load_view() {
		let co = company_filter.get_value();
		$c().html('<div class="amo-loading"><div class="spinner"></div><div class="loading-text">Loading data...</div></div>');
		switch(current_view) {
			case 'Faculty & Programs': load_faculty(co); break;
			case 'Cost Allocation': load_cost(co); break;
			case 'Tuition & Scholarships': load_tuition(co); break;
			case 'Grants & Research': load_grants(co); break;
			case 'Multi-Year Planning': load_multiyear(co); break;
			case 'Rector Executive': load_rector(); break;
		}
		page.main.find('#amo-last-refresh').text(frappe.datetime.now_time().substring(0, 5));
	}

	company_filter.$input.on('change', load_view);

	// ════════════════════════════════════════════════════════════
	// 1. Faculty & Program Financial Visibility
	// ════════════════════════════════════════════════════════════
	function load_faculty(company) {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_faculty_program_data',
			args: { company: company || '' },
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;
				let t = d.totals || {};

				let rows = (d.faculty_data || []).map(f => {
					let margin_color = f.margin_pct >= 30 ? 'green' : f.margin_pct >= 15 ? 'amber' : 'red';
					return `
					<tr>
						<td class="fw-600">${f.faculty}</td>
						<td class="text-right text-mono text-success">${fmt_currency(f.revenue)}</td>
						<td class="text-right text-mono text-danger">${fmt_currency(f.expenses)}</td>
						<td class="text-right text-mono fw-700 ${f.surplus >= 0 ? 'text-success' : 'text-danger'}">${fmt_currency(f.surplus)}</td>
						<td class="text-right" style="width:180px">
							<div class="amo-progress-label">
								<span></span><span class="${margin_color === 'green' ? 'text-success' : margin_color === 'red' ? 'text-danger' : 'text-warning'}">${f.margin_pct}%</span>
							</div>
							<div class="amo-progress">
								<div class="amo-progress-fill progress-${margin_color}" style="width:${Math.min(Math.abs(f.margin_pct), 100)}%"></div>
							</div>
						</td>
					</tr>`;
				}).join('');

				let periods = [...new Set((d.monthly_trend || []).map(m => m.period))].sort();
				let faculties = [...new Set((d.monthly_trend || []).map(m => m.faculty))];
				let chart_data = {
					labels: periods,
					datasets: faculties.map(fac => ({
						name: fac,
						values: periods.map(p => {
							let row = (d.monthly_trend || []).find(m => m.faculty === fac && m.period === p);
							return row ? (row.revenue - row.expenses) : 0;
						})
					}))
				};

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-blue"><i class="fa fa-university"></i></span> Faculty & Program Financial Visibility</h4>
							<p>Revenue, expenses, and surplus per faculty with margin analysis</p>
						</div>
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Total Revenue', fmt_currency(t.revenue), 'fa-arrow-up', 'green')}
						${kpi_card('Total Expenses', fmt_currency(t.expenses), 'fa-arrow-down', 'red')}
						${kpi_card('Net Surplus', fmt_currency(t.surplus), 'fa-balance-scale', t.surplus >= 0 ? 'green' : 'red')}
						${kpi_card('Overall Margin', t.margin_pct + '%', 'fa-percent', t.margin_pct >= 20 ? 'green' : 'amber')}
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Faculty Breakdown
							<span class="card-subtitle">${(d.faculty_data || []).length} faculties tracked</span>
						</div>
						<div class="amo-table-scroll">
						<table class="amo-table striped">
							<thead>
								<tr>
									<th>Faculty</th>
									<th class="text-right">Revenue</th>
									<th class="text-right">Expenses</th>
									<th class="text-right">Surplus</th>
									<th class="text-right">Margin</th>
								</tr>
							</thead>
							<tbody>${rows || empty_row(5)}</tbody>
						</table>
						</div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Monthly Surplus Trend by Faculty
							<span class="card-subtitle">Last 12 months</span>
						</div>
						<div id="faculty-trend-chart"></div>
					</div>
					</div>
				`);

				if (periods.length) {
					new frappe.Chart('#faculty-trend-chart', {
						data: chart_data,
						type: 'line',
						height: 300,
						colors: ['#3b82f6', '#f59e0b', '#10b981', '#ec4899', '#06b6d4', '#8b5cf6'],
						lineOptions: { regionFill: 1, hideDots: 0, dotSize: 4 },
						axisOptions: { xIsSeries: true }
					});
				}
			}
		});
	}

	// ════════════════════════════════════════════════════════════
	// 2. Cost Allocation & Academic Transparency
	// ════════════════════════════════════════════════════════════
	function load_cost(company) {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_cost_allocation_data',
			args: { company: company || '' },
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;
				let k = d.kpis || {};

				let fac_rows = (d.faculty_cost || []).map(f => {
					let share = k.total_expenses ? (f.total_cost / k.total_expenses * 100).toFixed(1) : 0;
					return `
					<tr>
						<td class="fw-600">${f.faculty}</td>
						<td class="text-right text-mono">${fmt_currency(f.total_cost)}</td>
						<td style="width:160px">
							<div class="amo-progress-label"><span></span><span>${share}%</span></div>
							<div class="amo-progress">
								<div class="amo-progress-fill progress-blue" style="width:${Math.min(share, 100)}%"></div>
							</div>
						</td>
					</tr>`;
				}).join('');

				let cc_rows = (d.cost_center_breakdown || []).map((c, i) => `
					<tr>
						<td><span class="text-muted" style="margin-right:6px">${i+1}.</span>${c.cost_center}</td>
						<td class="text-right text-mono">${fmt_currency(c.amount)}</td>
					</tr>
				`).join('');

				let pie_data = {
					labels: (d.cost_split || []).map(s => s.category),
					datasets: [{ values: (d.cost_split || []).map(s => s.amount) }]
				};

				// Admin ratio visual indicator
				let admin_pct = k.admin_ratio_pct || 0;
				let admin_color = admin_pct <= 25 ? 'green' : admin_pct <= 35 ? 'amber' : 'red';

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-amber"><i class="fa fa-pie-chart"></i></span> Cost Allocation & Academic Transparency</h4>
							<p>Administrative vs. academic cost ratio and allocation accuracy</p>
						</div>
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Total Expenses', fmt_currency(k.total_expenses), 'fa-money', 'blue')}
						${kpi_card('Admin Ratio', k.admin_ratio_pct + '%', 'fa-building', admin_color)}
						${kpi_card('Academic Ratio', k.academic_ratio_pct + '%', 'fa-graduation-cap', 'green')}
					</div>

					<div class="amo-grid amo-grid-5-7">
						<div class="amo-card">
							<div class="amo-card-header">Admin vs Academic Split</div>
							<div id="cost-pie-chart"></div>
							<div class="amo-card-body" style="padding-top:0">
								<div class="amo-progress-label"><span>Administrative</span><span>${admin_pct}%</span></div>
								<div class="amo-progress" style="height:10px">
									<div class="amo-progress-fill progress-${admin_color}" style="width:${admin_pct}%"></div>
								</div>
								<div class="amo-progress-label" style="margin-top:10px"><span>Academic</span><span>${k.academic_ratio_pct}%</span></div>
								<div class="amo-progress" style="height:10px">
									<div class="amo-progress-fill progress-green" style="width:${k.academic_ratio_pct}%"></div>
								</div>
							</div>
						</div>
						<div class="amo-card">
							<div class="amo-card-header">
								Cost per Faculty
								<span class="card-subtitle">${(d.faculty_cost || []).length} faculties</span>
							</div>
							<table class="amo-table striped">
								<thead><tr><th>Faculty</th><th class="text-right">Cost</th><th>Share</th></tr></thead>
								<tbody>${fac_rows || empty_row(3)}</tbody>
							</table>
						</div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Cost Center Breakdown
							<span class="card-subtitle">Top 15 by amount</span>
						</div>
						<div class="amo-table-scroll">
						<table class="amo-table striped">
							<thead><tr><th>Cost Center</th><th class="text-right">Amount</th></tr></thead>
							<tbody>${cc_rows || empty_row(2)}</tbody>
						</table>
						</div>
					</div>
					</div>
				`);

				if ((d.cost_split || []).length) {
					new frappe.Chart('#cost-pie-chart', {
						data: pie_data,
						type: 'pie',
						height: 230,
						colors: ['#f87171', '#34d399']
					});
				}
			}
		});
	}

	// ════════════════════════════════════════════════════════════
	// 3. Tuition & Scholarship Governance
	// ════════════════════════════════════════════════════════════
	function load_tuition(company) {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_tuition_scholarship_data',
			args: { company: company || '' },
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;
				let k = d.kpis || {};

				let tui_rows = (d.tuition_by_month || []).map(t => `
					<tr><td>${t.campus}</td><td class="text-mono">${t.period}</td><td class="text-right text-mono text-success">${fmt_currency(t.revenue)}</td></tr>
				`).join('');

				let sch_rows = (d.scholarships_by_month || []).map(s => `
					<tr><td>${s.campus}</td><td class="text-mono">${s.period}</td><td class="text-right text-mono text-warning">${fmt_currency(s.disbursed)}</td></tr>
				`).join('');

				let fac_rows = (d.faculty_tuition || []).map(f => `
					<tr><td class="fw-600">${f.faculty}</td><td class="text-right text-mono">${fmt_currency(f.revenue)}</td></tr>
				`).join('');

				// Receivables aging
				let recv = d.receivables || [];
				let aging_rows = '';
				if (recv.length) {
					let buckets = {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0};
					recv.forEach(r => {
						let days = r.age_days || 0;
						let bucket = days <= 30 ? '0-30' : days <= 60 ? '31-60' : days <= 90 ? '61-90' : '90+';
						buckets[bucket] += flt(r.amount);
					});
					let total_recv = Object.values(buckets).reduce((a, b) => a + b, 0);
					aging_rows = Object.entries(buckets).map(([bucket, amt]) => {
						let pct = total_recv ? (amt / total_recv * 100).toFixed(0) : 0;
						let color = bucket === '0-30' ? 'green' : bucket === '31-60' ? 'blue' : bucket === '61-90' ? 'amber' : 'red';
						return `
						<div style="margin-bottom:12px">
							<div class="amo-progress-label"><span>${bucket} days</span><span>${fmt_currency(amt)} (${pct}%)</span></div>
							<div class="amo-progress"><div class="amo-progress-fill progress-${color}" style="width:${pct}%"></div></div>
						</div>`;
					}).join('');
				}

				// Chart data
				let tui_periods = [...new Set((d.tuition_by_month || []).map(t => t.period))].sort();
				let tui_vals = tui_periods.map(p => (d.tuition_by_month || []).filter(t => t.period === p).reduce((s, t) => s + flt(t.revenue), 0));
				let sch_vals = tui_periods.map(p => (d.scholarships_by_month || []).filter(s => s.period === p).reduce((s, t) => s + flt(t.disbursed), 0));

				// Scholarship burden visual
				let burden = k.scholarship_burden_pct || 0;
				let burden_color = burden <= 15 ? 'green' : burden <= 25 ? 'amber' : 'red';
				let collection = k.collection_rate_pct || 100;
				let coll_color = collection >= 90 ? 'green' : collection >= 75 ? 'amber' : 'red';

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-green"><i class="fa fa-graduation-cap"></i></span> Tuition & Scholarship Governance</h4>
							<p>Collection rates, scholarship burden, and receivables aging</p>
						</div>
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Total Tuition', fmt_currency(k.total_tuition), 'fa-money', 'green')}
						${kpi_card('Scholarships', fmt_currency(k.total_scholarship), 'fa-gift', 'amber')}
						${kpi_card('Net Tuition', fmt_currency((k.total_tuition || 0) - (k.total_scholarship || 0)), 'fa-calculator', 'blue')}
						${kpi_card('Scholarship Burden', burden + '%', 'fa-percent', burden_color)}
						${kpi_card('Collection Rate', collection + '%', 'fa-check-circle', coll_color)}
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Tuition vs Scholarship Trend
							<span class="card-subtitle">Current fiscal year</span>
						</div>
						<div id="tuition-trend-chart"></div>
					</div>

					<div class="amo-grid amo-grid-3">
						<div class="amo-card">
							<div class="amo-card-header">Revenue by Faculty</div>
							<table class="amo-table compact striped">
								<thead><tr><th>Faculty</th><th class="text-right">Revenue</th></tr></thead>
								<tbody>${fac_rows || empty_row(2)}</tbody>
							</table>
						</div>
						<div class="amo-card">
							<div class="amo-card-header">Tuition by Period</div>
							<div class="amo-table-scroll" style="max-height:280px;overflow-y:auto">
							<table class="amo-table compact striped">
								<thead><tr><th>Campus</th><th>Period</th><th class="text-right">Revenue</th></tr></thead>
								<tbody>${tui_rows || empty_row(3)}</tbody>
							</table>
							</div>
						</div>
						<div class="amo-card">
							<div class="amo-card-header">Receivables Aging</div>
							<div class="amo-card-body">
								${aging_rows || '<div class="amo-empty-state"><i class="fa fa-check-circle"></i><p>No outstanding receivables</p></div>'}
							</div>
						</div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Scholarship Disbursements
							<span class="card-subtitle">${(d.scholarships_by_month || []).length} records</span>
						</div>
						<div class="amo-table-scroll" style="max-height:300px;overflow-y:auto">
						<table class="amo-table compact striped">
							<thead><tr><th>Campus</th><th>Period</th><th class="text-right">Amount</th></tr></thead>
							<tbody>${sch_rows || empty_row(3)}</tbody>
						</table>
						</div>
					</div>
					</div>
				`);

				if (tui_periods.length) {
					new frappe.Chart('#tuition-trend-chart', {
						data: {
							labels: tui_periods,
							datasets: [
								{ name: 'Tuition', values: tui_vals },
								{ name: 'Scholarships', values: sch_vals }
							]
						},
						type: 'bar',
						height: 280,
						colors: ['#10b981', '#f59e0b'],
						barOptions: { spaceRatio: 0.3 }
					});
				}
			}
		});
	}

	// ════════════════════════════════════════════════════════════
	// 4. Grant & Research Project Control
	// ════════════════════════════════════════════════════════════
	function load_grants(company) {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_grant_research_data',
			args: { company: company || '' },
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;
				let k = d.kpis || {};

				let status_icon = { 'Open': 'fa-clock-o', 'Completed': 'fa-check', 'Cancelled': 'fa-times' };
				let status_badge = { 'Open': 'badge-blue', 'Completed': 'badge-green', 'Cancelled': 'badge-grey', 'Overdue': 'badge-red' };

				let proj_rows = (d.projects || []).map(p => {
					let pct = p.percent_complete || 0;
					let bar_color = pct >= 80 ? 'green' : pct >= 40 ? 'blue' : 'amber';
					let budget_status = flt(p.actual_cost) > flt(p.budget) ? 'text-danger' : 'text-success';
					return `
					<tr>
						<td class="fw-600">${p.project_name}</td>
						<td class="text-muted">${p.company}</td>
						<td><span class="amo-badge ${status_badge[p.status] || 'badge-grey'}"><i class="fa ${status_icon[p.status] || 'fa-question'}"></i> ${p.status}</span></td>
						<td class="text-right text-mono">${fmt_currency(p.budget)}</td>
						<td class="text-right text-mono ${budget_status}">${fmt_currency(p.actual_cost)}</td>
						<td style="min-width:130px">
							<div class="amo-progress-label"><span></span><span>${pct}%</span></div>
							<div class="amo-progress"><div class="amo-progress-fill progress-${bar_color}" style="width:${pct}%"></div></div>
						</td>
					</tr>`;
				}).join('');

				let budget_rows = (d.budgets || []).map(b => `
					<tr>
						<td class="fw-600">${b.budget_name}</td>
						<td class="text-muted">${b.company}</td>
						<td class="text-right text-mono">${fmt_currency(b.budget_amount)}</td>
						<td><span class="amo-badge badge-blue">${b.from_fiscal_year}</span></td>
						<td class="text-muted">${b.cost_center || '—'}</td>
					</tr>
				`).join('');

				// budget vs actual donut-style indicator
				let bva = k.budget_vs_actual_pct || 0;
				let bva_color = bva <= 90 ? 'green' : bva <= 100 ? 'amber' : 'red';

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-purple"><i class="fa fa-flask"></i></span> Grant & Research Project Control</h4>
							<p>Project budgets, grant utilization, and completion tracking</p>
						</div>
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Total Projects', k.total_projects, 'fa-folder-open', 'blue')}
						${kpi_card('Open', k.open_projects, 'fa-clock-o', 'amber')}
						${kpi_card('Completed', k.completed_projects, 'fa-check', 'green')}
						${kpi_card('Budget Usage', bva + '%', 'fa-bar-chart', bva_color)}
						${kpi_card('On-Budget Rate', k.on_budget_pct + '%', 'fa-thumbs-up', k.on_budget_pct >= 80 ? 'green' : 'amber')}
						${kpi_card('Total Grants', fmt_currency(k.total_grant_amount), 'fa-bank', 'purple')}
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Projects
							<span class="card-subtitle">${(d.projects || []).length} projects tracked</span>
						</div>
						<div class="amo-table-scroll">
							<table class="amo-table striped">
								<thead>
									<tr><th>Project</th><th>Company</th><th>Status</th><th class="text-right">Budget</th><th class="text-right">Actual</th><th>Progress</th></tr>
								</thead>
								<tbody>${proj_rows || empty_row(6)}</tbody>
							</table>
						</div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Budget Allocations
							<span class="card-subtitle">${(d.budgets || []).length} budgets</span>
						</div>
						<table class="amo-table striped">
							<thead>
								<tr><th>Budget</th><th>Company</th><th class="text-right">Amount</th><th>Fiscal Year</th><th>Cost Center</th></tr>
							</thead>
							<tbody>${budget_rows || empty_row(5)}</tbody>
						</table>
					</div>
					</div>
				`);
			}
		});
	}

	// ════════════════════════════════════════════════════════════
	// 5. Multi-Year Academic Financial Planning
	// ════════════════════════════════════════════════════════════
	function load_multiyear(company) {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_multiyear_planning_data',
			args: { company: company || '' },
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;

				let yr_rows = (d.yearly_financials || []).map(y => {
					let surplus = (y.total_revenue || 0) - (y.total_expenses || 0);
					return `
					<tr>
						<td class="fw-700">${y.year}</td>
						<td class="text-right text-mono text-success">${fmt_currency(y.total_revenue)}</td>
						<td class="text-right text-mono">${fmt_currency(y.tuition_revenue)}</td>
						<td class="text-right text-mono text-danger">${fmt_currency(y.total_expenses)}</td>
						<td class="text-right text-mono">${fmt_currency(y.faculty_expenses)}</td>
						<td class="text-right text-mono">${fmt_currency(y.scholarship_cost)}</td>
						<td class="text-right fw-700 ${surplus >= 0 ? 'text-success' : 'text-danger'}">${fmt_currency(surplus)}</td>
					</tr>`;
				}).join('');

				let proj_rows = (d.projection || []).map(p => `
					<tr class="amo-projection-row">
						<td class="fw-600">${p.year} <span class="amo-badge badge-purple small">Projected</span></td>
						<td class="text-right text-mono">${fmt_currency(p.projected_revenue)}</td>
						<td class="text-right text-mono">${fmt_currency(p.projected_expenses)}</td>
						<td class="text-right fw-700 ${p.projected_surplus >= 0 ? 'text-success' : 'text-danger'}">${fmt_currency(p.projected_surplus)}</td>
					</tr>
				`).join('');

				// Chart data
				let all_years = (d.yearly_financials || []).map(y => String(y.year));
				let rev_vals = (d.yearly_financials || []).map(y => y.total_revenue || 0);
				let exp_vals = (d.yearly_financials || []).map(y => y.total_expenses || 0);
				let surplus_vals = (d.yearly_financials || []).map(y => (y.total_revenue || 0) - (y.total_expenses || 0));
				(d.projection || []).forEach(p => {
					all_years.push(p.year + ' (P)');
					rev_vals.push(p.projected_revenue);
					exp_vals.push(p.projected_expenses);
					surplus_vals.push(p.projected_surplus);
				});

				let asset_rows = (d.assets_by_year || []).map(a => `
					<tr><td class="fw-600">${a.year}</td><td class="text-right text-mono">${a.count}</td><td class="text-right text-mono">${fmt_currency(a.value)}</td></tr>
				`).join('');

				// YoY growth rates
				let yf = d.yearly_financials || [];
				let growth_html = '';
				if (yf.length >= 2) {
					let last = yf[yf.length - 1];
					let prev = yf[yf.length - 2];
					let rev_g = prev.total_revenue ? ((last.total_revenue - prev.total_revenue) / prev.total_revenue * 100).toFixed(1) : 0;
					let exp_g = prev.total_expenses ? ((last.total_expenses - prev.total_expenses) / prev.total_expenses * 100).toFixed(1) : 0;
					growth_html = `
						<div class="amo-card">
							<div class="amo-card-header">Year-over-Year Growth (${prev.year} → ${last.year})</div>
							<div class="amo-card-body">
								<div style="margin-bottom:14px">
									<div class="amo-progress-label"><span>Revenue Growth</span><span class="${rev_g >= 0 ? 'text-success' : 'text-danger'}">${rev_g >= 0 ? '+' : ''}${rev_g}%</span></div>
									<div class="amo-progress" style="height:10px"><div class="amo-progress-fill progress-${rev_g >= 0 ? 'green' : 'red'}" style="width:${Math.min(Math.abs(rev_g), 100)}%"></div></div>
								</div>
								<div>
									<div class="amo-progress-label"><span>Expense Growth</span><span class="${exp_g <= 5 ? 'text-success' : 'text-warning'}">${exp_g >= 0 ? '+' : ''}${exp_g}%</span></div>
									<div class="amo-progress" style="height:10px"><div class="amo-progress-fill progress-${exp_g <= 5 ? 'green' : 'amber'}" style="width:${Math.min(Math.abs(exp_g), 100)}%"></div></div>
								</div>
							</div>
						</div>`;
				}

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-blue"><i class="fa fa-line-chart"></i></span> Multi-Year Academic Financial Planning</h4>
							<p>Historical trends, 3-year projections, and sustainability analysis</p>
						</div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Revenue vs Expenses Trend (with Projections)
							<span class="card-subtitle">${all_years.length} periods</span>
						</div>
						<div id="multiyear-chart"></div>
					</div>

					<div class="amo-card">
						<div class="amo-card-header">
							Yearly Financial Summary
							<span class="card-subtitle">${(d.yearly_financials || []).length} years of data</span>
						</div>
						<div class="amo-table-scroll">
						<table class="amo-table striped">
							<thead>
								<tr><th>Year</th><th class="text-right">Total Revenue</th><th class="text-right">Tuition</th><th class="text-right">Total Expenses</th><th class="text-right">Faculty</th><th class="text-right">Scholarships</th><th class="text-right">Net Surplus</th></tr>
							</thead>
							<tbody>${yr_rows || empty_row(7)}</tbody>
						</table>
						</div>
					</div>

					<div class="amo-grid amo-grid-7-5">
						<div class="amo-card">
							<div class="amo-card-header">
								3-Year Surplus Projection
								<span class="card-subtitle">Based on historical growth rates</span>
							</div>
							<table class="amo-table striped">
								<thead><tr><th>Year</th><th class="text-right">Revenue</th><th class="text-right">Expenses</th><th class="text-right">Surplus</th></tr></thead>
								<tbody>${proj_rows || empty_row(4)}</tbody>
							</table>
						</div>
						<div>
							${growth_html}
							<div class="amo-card">
								<div class="amo-card-header">Asset Base by Year</div>
								<table class="amo-table compact striped">
									<thead><tr><th>Year</th><th class="text-right">Count</th><th class="text-right">Value</th></tr></thead>
									<tbody>${asset_rows || empty_row(3)}</tbody>
								</table>
							</div>
						</div>
					</div>
					</div>
				`);

				if (all_years.length) {
					new frappe.Chart('#multiyear-chart', {
						data: {
							labels: all_years,
							datasets: [
								{ name: 'Revenue', values: rev_vals, chartType: 'line' },
								{ name: 'Expenses', values: exp_vals, chartType: 'line' },
								{ name: 'Surplus', values: surplus_vals, chartType: 'bar' }
							]
						},
						type: 'axis-mixed',
						height: 320,
						colors: ['#10b981', '#ef4444', '#3b82f6'],
						lineOptions: { regionFill: 1, dotSize: 5 },
						barOptions: { spaceRatio: 0.5 },
						axisOptions: { xIsSeries: true }
					});
				}
			}
		});
	}

	// ════════════════════════════════════════════════════════════
	// 6. Rector Executive Dashboard
	// ════════════════════════════════════════════════════════════
	function load_rector() {
		frappe.call({
			method: 'amo.amo_setup.dashboard_api.get_rector_dashboard_data',
			callback: function(r) {
				if (!r.message) return;
				let d = r.message;
				let cy = d.current_year || {};
				let py = d.previous_year || {};
				let g = d.growth || {};
				let org = d.org_summary || {};

				let fac_rows = (d.faculty_margins || []).map(f => {
					let bar_w = Math.min(Math.abs(f.margin_pct), 100);
					return `
					<tr>
						<td class="fw-600">${f.faculty}</td>
						<td class="text-right text-mono">${fmt_currency(f.revenue)}</td>
						<td class="text-right text-mono">${fmt_currency(f.expenses)}</td>
						<td class="text-right fw-700 ${f.margin >= 0 ? 'text-success' : 'text-danger'}">${fmt_currency(f.margin)}</td>
						<td style="min-width:160px">
							<div class="amo-bar-cell">
								<div class="amo-bar ${f.margin_pct >= 0 ? 'bar-green' : 'bar-red'}" style="width:${bar_w}%"></div>
								<span class="${f.margin_pct >= 0 ? 'text-success' : 'text-danger'}">${f.margin_pct}%</span>
							</div>
						</td>
					</tr>`;
				}).join('');

				let grp_rows = (d.groups || []).map(g => `
					<tr>
						<td class="fw-600">${(g.grp || '').replace('AMO - ', '')}</td>
						<td class="text-right">
							<span class="amo-badge badge-blue">${g.count}</span>
						</td>
					</tr>
				`).join('');

				// Revenue vs Expense delta indicators
				let rev_delta = g.revenue_pct || 0;
				let exp_delta = g.expense_pct || 0;

				$c().html(`
					<div class="amo-stagger">
					<div class="amo-section-header">
						<div class="amo-section-header-left">
							<h4><span class="amo-section-icon icon-purple"><i class="fa fa-shield"></i></span> Rector Executive Dashboard</h4>
							<p>Top-level financial health and year-over-year performance across the AMO network</p>
						</div>
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Revenue (YTD)', fmt_currency(cy.revenue), 'fa-arrow-up', 'green', rev_delta)}
						${kpi_card('Expenses (YTD)', fmt_currency(cy.expenses), 'fa-arrow-down', 'red', exp_delta)}
						${kpi_card('Net Surplus', fmt_currency(cy.surplus), 'fa-balance-scale', cy.surplus >= 0 ? 'green' : 'red')}
						${kpi_card('Operating Margin', d.operating_margin_pct + '%', 'fa-percent', d.operating_margin_pct >= 15 ? 'green' : 'amber')}
					</div>

					<div class="amo-kpi-row">
						${kpi_card('Revenue Growth', (rev_delta >= 0 ? '+' : '') + rev_delta + '%', 'fa-trending-up', rev_delta >= 0 ? 'green' : 'red')}
						${kpi_card('Expense Growth', (exp_delta >= 0 ? '+' : '') + exp_delta + '%', 'fa-trending-up', exp_delta <= 5 ? 'green' : 'amber')}
						${kpi_card('Total Entities', org.total_companies, 'fa-building', 'blue')}
						${kpi_card('Total Assets', fmt_currency(org.total_assets), 'fa-bank', 'purple')}
						${kpi_card('Projects', org.total_projects, 'fa-folder-open', 'blue')}
						${kpi_card('Active Projects', org.open_projects, 'fa-clock-o', 'amber')}
					</div>

					<div class="amo-grid amo-grid-8-4">
						<div class="amo-card">
							<div class="amo-card-header">
								Operating Margin per Faculty
								<span class="card-subtitle">${(d.faculty_margins || []).length} faculties analyzed</span>
							</div>
							<div class="amo-table-scroll">
							<table class="amo-table striped">
								<thead>
									<tr><th>Faculty</th><th class="text-right">Revenue</th><th class="text-right">Expenses</th><th class="text-right">Margin</th><th>Margin %</th></tr>
								</thead>
								<tbody>${fac_rows || empty_row(5)}</tbody>
							</table>
							</div>
						</div>
						<div>
							<div class="amo-card">
								<div class="amo-card-header">Year-over-Year Comparison</div>
								<div id="yoy-chart"></div>
							</div>
							<div class="amo-card">
								<div class="amo-card-header">Organization Groups</div>
								<table class="amo-table compact striped">
									<thead><tr><th>Group</th><th class="text-right">Entities</th></tr></thead>
									<tbody>${grp_rows || empty_row(2)}</tbody>
								</table>
							</div>
						</div>
					</div>
					</div>
				`);

				new frappe.Chart('#yoy-chart', {
					data: {
						labels: ['Revenue', 'Expenses', 'Surplus'],
						datasets: [
							{ name: 'Previous Year', values: [py.revenue || 0, py.expenses || 0, py.surplus || 0] },
							{ name: 'Current Year', values: [cy.revenue || 0, cy.expenses || 0, cy.surplus || 0] }
						]
					},
					type: 'bar',
					height: 240,
					colors: ['#94a3b8', '#3b82f6'],
					barOptions: { spaceRatio: 0.4 }
				});
			}
		});
	}

	// ── Helpers ───────────────────────────────────────────────
	function fmt(val) {
		if (val === null || val === undefined) return '0';
		return Number(val).toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0});
	}

	function fmt_currency(val) {
		if (val === null || val === undefined || val === 0) return '$0';
		let n = Number(val);
		if (Math.abs(n) >= 1000000) {
			return '$' + (n / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
		}
		if (Math.abs(n) >= 1000) {
			return '$' + (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
		}
		return '$' + n.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0});
	}

	function flt(val) {
		return parseFloat(val) || 0;
	}

	function kpi_card(label, value, icon, color, delta) {
		let delta_html = '';
		if (delta !== undefined && delta !== null) {
			let dir = delta >= 0 ? 'up' : 'down';
			let arrow = delta >= 0 ? '&#9650;' : '&#9660;';
			delta_html = `<div class="amo-kpi-delta ${dir}">${arrow} ${Math.abs(delta)}% vs last year</div>`;
		}
		return `
		<div class="amo-kpi">
			<div class="amo-kpi-inner kpi-${color}">
				<div class="amo-kpi-icon"><i class="fa ${icon}"></i></div>
				<div class="amo-kpi-body">
					<div class="amo-kpi-value">${value}</div>
					<div class="amo-kpi-label">${label}</div>
					${delta_html}
				</div>
			</div>
		</div>`;
	}

	function empty_row(cols) {
		return `<tr><td colspan="${cols}" class="text-center py-4">
			<div class="amo-empty-state">
				<i class="fa fa-inbox"></i>
				<p>No data available for this selection</p>
			</div>
		</td></tr>`;
	}

	// Initial load
	load_view();
};
