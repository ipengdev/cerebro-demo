frappe.pages['itsm-dashboard'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ITSM',
		single_column: true,
	});

	page.set_primary_action(__('New Ticket'), () => frappe.new_doc('Service Ticket'), 'es-line-add');
	page.add_inner_button(__('Service Tickets'), () => frappe.set_route('List', 'Service Ticket'));
	page.add_inner_button(__('IT Assets'), () => frappe.set_route('List', 'IT Asset'));
	page.add_inner_button(__('CMDB'), () => frappe.set_route('List', 'Configuration Item'));

	const $main = $(wrapper).find('.layout-main-section');
	$main.html(itBuildShell());
	itSetupThemeToggle($main);
	itSetupDateFilter($main);
	itLoadDashboard($main);

	wrapper._itsm = { $main, page };
};

frappe.pages['itsm-dashboard'].on_page_show = function(wrapper) {
	if (wrapper._itsm) itLoadDashboard(wrapper._itsm.$main);
};

/* ================================================================
   SVG ICONS
   ================================================================ */
const IT_ICONS = {
	'alert-circle': '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
	'activity': '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
	'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
	'alert-triangle': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
	'monitor': '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
	'check-circle': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
	'plus': '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
	'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
	'sun': '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
	'moon': '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
	'settings': '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
	'list': '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
	'database': '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
};

function itIcon(name, size) {
	size = size || 20;
	return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + (IT_ICONS[name] || IT_ICONS['monitor']) + '</svg>';
}

function itEsc(s) { return frappe.utils.escape_html(s || ''); }

/* ================================================================
   SHELL
   ================================================================ */
function itBuildShell() {
	return '<div class="it-wrapper">'
		+ '<div class="it-topbar">'
		+   '<div class="it-topbar-left">'
		+     '<h1 class="it-title">ITSM Dashboard</h1>'
		+     '<span class="it-live-dot"></span>'
		+   '</div>'
		+   '<div class="it-topbar-right">'
		+     '<div class="it-date-filter">'
		+       '<button class="it-date-btn active" data-range="all">All Time</button>'
		+       '<button class="it-date-btn" data-range="today">Today</button>'
		+       '<button class="it-date-btn" data-range="week">This Week</button>'
		+       '<button class="it-date-btn" data-range="month">This Month</button>'
		+     '</div>'
		+     '<button class="it-theme-toggle" title="Toggle dark mode">' + itIcon('moon', 18) + '</button>'
		+   '</div>'
		+ '</div>'
		+ '<div class="it-quick-actions">'
		+   '<button class="it-quick-btn" data-action="new-ticket">' + itIcon('plus', 14) + ' New Ticket</button>'
		+   '<button class="it-quick-btn" data-action="all-tickets">' + itIcon('list', 14) + ' All Tickets</button>'
		+   '<button class="it-quick-btn" data-action="assets">' + itIcon('monitor', 14) + ' Assets</button>'
		+   '<button class="it-quick-btn" data-action="cmdb">' + itIcon('database', 14) + ' CMDB</button>'
		+   '<button class="it-quick-btn" data-action="settings">' + itIcon('settings', 14) + ' Settings</button>'
		+ '</div>'
		+ '<div id="it-stats-area"></div>'
		+ '<div id="it-kpis-area"></div>'
		+ '<div id="it-charts-area"></div>'
		+ '<div id="it-breakdowns-area"></div>'
		+ '<div id="it-details-area"></div>'
		+ '<div id="it-overdue-area"></div>'
		+ '</div>';
}

/* ================================================================
   SETUP
   ================================================================ */
function itSetupThemeToggle($main) {
	$main.on('click', '.it-theme-toggle', function() {
		var $w = $main.find('.it-wrapper');
		var isDark = $w.attr('data-theme') === 'dark';
		$w.attr('data-theme', isDark ? '' : 'dark');
		$(this).html(itIcon(isDark ? 'moon' : 'sun', 18));
	});
}

function itSetupDateFilter($main) {
	$main.on('click', '.it-date-btn', function() {
		$main.find('.it-date-btn').removeClass('active');
		$(this).addClass('active');
		itLoadDashboard($main);
	});

	$main.on('click', '.it-quick-btn', function() {
		var action = $(this).data('action');
		if (action === 'new-ticket') frappe.new_doc('Service Ticket');
		else if (action === 'all-tickets') frappe.set_route('List', 'Service Ticket');
		else if (action === 'assets') frappe.set_route('List', 'IT Asset');
		else if (action === 'cmdb') frappe.set_route('List', 'Configuration Item');
		else if (action === 'settings') frappe.set_route('Form', 'ITSM Settings');
	});
}

/* ================================================================
   DATA LOADING
   ================================================================ */
function itLoadDashboard($main) {
	$main.find('#it-stats-area').html('<div class="it-loading"><div class="it-spinner"></div><span>Loading dashboard...</span></div>');
	['kpis', 'charts', 'breakdowns', 'details', 'overdue'].forEach(function(a) {
		$main.find('#it-' + a + '-area').html('');
	});

	frappe.xcall('itsm.api.get_dashboard_stats').then(function(stats) {
		if (!stats) {
			$main.find('#it-stats-area').html('<div class="it-empty">No data available</div>');
			return;
		}
		itRenderStats($main, stats);
		itRenderKPIs($main, stats);
		itRenderCharts($main, stats);
		itRenderBreakdowns($main, stats);
		itRenderDetails($main, stats);
		itRenderOverdue($main, stats);
	}).catch(function(e) {
		console.error('ITSM dashboard error:', e);
		$main.find('#it-stats-area').html('<div class="it-error">Failed to load dashboard data</div>');
	});
}

/* ================================================================
   RENDER: STAT CARDS
   ================================================================ */
function itRenderStats($main, s) {
	var cards = [
		{ cls: 'open', icon: 'alert-circle', val: s.open_tickets, label: 'Open Tickets', dt: 'Service Ticket', f: {status: 'Open'} },
		{ cls: 'progress', icon: 'activity', val: s.in_progress, label: 'In Progress', dt: 'Service Ticket', f: {status: 'In Progress'} },
		{ cls: 'breached', icon: 'alert-triangle', val: s.sla_breached, label: 'SLA Breached', dt: 'Service Ticket', f: {resolution_sla_status: 'Breached'} },
		{ cls: 'assets', icon: 'monitor', val: s.active_assets, label: 'Active Assets', dt: 'IT Asset', f: {status: 'Active'} },
	];

	var html = '<div class="it-stats">';
	cards.forEach(function(c) {
		html += '<div class="it-stat ' + c.cls + '" data-dt="' + c.dt + "\" data-filters='" + JSON.stringify(c.f) + "'>"
			+ '<div class="it-stat-icon">' + itIcon(c.icon) + '</div>'
			+ '<div class="it-stat-val">' + (c.val || 0) + '</div>'
			+ '<div class="it-stat-label">' + c.label + '</div>'
			+ '</div>';
	});
	html += '</div>';

	$main.find('#it-stats-area').html(html);
	$main.find('.it-stat').on('click', function() {
		var dt = $(this).data('dt');
		var f = $(this).data('filters');
		if (dt) frappe.set_route('List', dt, f);
	});
}

/* ================================================================
   RENDER: KPIs
   ================================================================ */
function itRenderKPIs($main, s) {
	var compliance = s.sla_compliance || 100;
	var cc = compliance >= 90 ? '#22c55e' : compliance >= 70 ? '#f59e0b' : '#ef4444';

	$main.find('#it-kpis-area').html(
		'<div class="it-kpis">'
		+ '<div class="it-kpi"><div class="it-kpi-val">' + (s.total_tickets || 0) + '</div><div class="it-kpi-label">Total Tickets</div></div>'
		+ '<div class="it-kpi highlight" style="--it-compliance-color:' + cc + '"><div class="it-kpi-val">' + compliance + '%</div><div class="it-kpi-label">SLA Compliance</div>'
		+   '<div class="it-kpi-bar"><div class="it-kpi-bar-fill" style="width:' + compliance + '%;background:' + cc + '"></div></div></div>'
		+ '<div class="it-kpi"><div class="it-kpi-val">' + (s.avg_resolution_hours || 0) + '<small>h</small></div><div class="it-kpi-label">Avg Resolution</div></div>'
		+ '<div class="it-kpi"><div class="it-kpi-val">' + (s.resolved_today || 0) + '</div><div class="it-kpi-label">Resolved Today</div></div>'
		+ '</div>'
	);
}

/* ================================================================
   RENDER: CHARTS
   ================================================================ */
function itRenderCharts($main, s) {
	$main.find('#it-charts-area').html(
		'<div class="it-grid-2-1">'
		+ '<div class="it-card"><div class="it-card-head"><h3>Ticket Trend</h3><span class="it-card-sub">Last 14 days</span></div>'
		+   '<div class="it-card-body"><div id="it-chart-trend"></div></div></div>'
		+ '<div class="it-card"><div class="it-card-head"><h3>By Priority</h3></div>'
		+   '<div class="it-card-body"><div id="it-chart-priority"></div></div></div>'
		+ '</div>'
	);

	setTimeout(function() {
		var labels = [], created = [], resolved = [];
		for (var i = 13; i >= 0; i--) {
			var d = moment().subtract(i, 'days');
			var key = d.format('YYYY-MM-DD');
			labels.push(d.format('D MMM'));
			created.push((s.trend_created || {})[key] || 0);
			resolved.push((s.trend_resolved || {})[key] || 0);
		}
		var trendEl = document.getElementById('it-chart-trend');
		if (trendEl) {
			new frappe.Chart(trendEl, {
				data: { labels: labels, datasets: [{ name: 'Created', values: created }, { name: 'Resolved', values: resolved }] },
				type: 'line', height: 220,
				colors: ['#ef4444', '#22c55e'],
				lineOptions: { regionFill: 1, spline: 1, hideDots: 0 },
				axisOptions: { xIsSeries: true },
				tooltipOptions: { formatTooltipY: function(d) { return d + ' tickets'; } },
			});
		}

		var priorities = ['Urgent', 'High', 'Medium', 'Low'];
		var pVals = priorities.map(function(p) { return (s.by_priority || {})[p] || 0; });
		var priEl = document.getElementById('it-chart-priority');
		if (priEl && pVals.some(function(v) { return v > 0; })) {
			new frappe.Chart(priEl, {
				data: { labels: priorities, datasets: [{ values: pVals }] },
				type: 'percentage', height: 160,
				colors: ['#ef4444', '#f97316', '#f59e0b', '#3b82f6'],
				barOptions: { spaceRatio: 0.4 },
			});
		} else if (priEl) {
			priEl.innerHTML = '<div class="it-empty">No priority data</div>';
		}
	}, 200);
}

/* ================================================================
   RENDER: BREAKDOWNS
   ================================================================ */
function itRenderBreakdowns($main, s) {
	var sc = { Open: '#ef4444', 'In Progress': '#3b82f6', Pending: '#f59e0b', 'On Hold': '#f97316', Resolved: '#22c55e', Closed: '#6b7280' };
	$main.find('#it-breakdowns-area').html(
		'<div class="it-grid-1-1">'
		+ '<div class="it-card"><div class="it-card-head"><h3>By Status</h3></div><div class="it-card-body">' + itBuildBars(s.by_status, sc) + '</div></div>'
		+ '<div class="it-card"><div class="it-card-head"><h3>By Category</h3></div><div class="it-card-body">' + itBuildBars(s.by_category, null, '#6366f1') + '</div></div>'
		+ '</div>'
	);
}

function itBuildBars(data, colorMap, defaultColor) {
	var entries = Object.entries(data || {});
	if (!entries.length) return '<div class="it-empty">No data</div>';
	var total = entries.reduce(function(a, e) { return a + e[1]; }, 0) || 1;
	var html = '<div class="it-bars">';
	entries.forEach(function(e) {
		var label = e[0], cnt = e[1];
		var pct = Math.round(cnt / total * 100);
		var c = (colorMap && colorMap[label]) || defaultColor || '#4f46e5';
		html += '<div class="it-bar-row">'
			+ '<span class="it-bar-label">' + itEsc(label) + '</span>'
			+ '<div class="it-bar-track"><div class="it-bar-fill" style="width:' + pct + '%;background:' + c + '"></div></div>'
			+ '<span class="it-bar-val">' + cnt + '</span>'
			+ '</div>';
	});
	html += '</div>';
	return html;
}

/* ================================================================
   RENDER: RECENT TICKETS + ASSIGNEES
   ================================================================ */
function itRenderDetails($main, s) {
	$main.find('#it-details-area').html(
		'<div class="it-grid-2-1">'
		+ '<div class="it-card"><div class="it-card-head"><h3>Recent Tickets</h3>'
		+   '<a class="it-card-link" onclick="frappe.set_route(\'List\',\'Service Ticket\')">View all &rarr;</a></div>'
		+   '<div class="it-card-body flush">' + itBuildTicketTable(s.recent_tickets) + '</div></div>'
		+ '<div class="it-card"><div class="it-card-head"><h3>Top Assignees</h3></div>'
		+   '<div class="it-card-body">' + itBuildAssignees(s.top_assignees) + '</div></div>'
		+ '</div>'
	);
}

function itBuildTicketTable(tickets) {
	if (!tickets || !tickets.length) return '<div class="it-empty">No recent tickets</div>';
	var html = '<table class="it-table"><thead><tr><th>ID</th><th>Subject</th><th>Priority</th><th>Status</th><th>Created</th></tr></thead><tbody>';
	tickets.forEach(function(t) {
		var p = (t.priority || 'Medium').toLowerCase();
		var st = (t.status || 'Open').toLowerCase().replace(/ /g, '-');
		html += '<tr onclick="frappe.set_route(\'Form\',\'Service Ticket\',\'' + itEsc(t.name) + '\')">'
			+ '<td><span class="it-tid">' + itEsc(t.name) + '</span></td>'
			+ '<td class="it-td-subject">' + itEsc(t.subject || '\u2014') + '</td>'
			+ '<td><span class="it-pill it-p-' + p + '">' + (t.priority || '\u2014') + '</span></td>'
			+ '<td><span class="it-pill it-s-' + st + '">' + (t.status || '\u2014') + '</span></td>'
			+ '<td class="it-td-ago">' + moment(t.creation).fromNow() + '</td>'
			+ '</tr>';
	});
	html += '</tbody></table>';
	return html;
}

function itBuildAssignees(assignees) {
	if (!assignees || !assignees.length) return '<div class="it-empty">No assignments</div>';
	var html = '<div class="it-assignees">';
	assignees.forEach(function(a, i) {
		var name = a.assigned_to ? frappe.user.full_name(a.assigned_to) : '\u2014';
		var pct = a.cnt ? Math.round((a.resolved_cnt || 0) / a.cnt * 100) : 0;
		var avatar = frappe.avatar(a.assigned_to, 'avatar-small');
		html += '<div class="it-assignee">'
			+ '<span class="it-assignee-rank">' + (i + 1) + '</span>'
			+ '<div class="it-assignee-avatar">' + avatar + '</div>'
			+ '<div class="it-assignee-info"><span class="it-assignee-name">' + itEsc(name) + '</span>'
			+ '<span class="it-assignee-sub">' + (a.resolved_cnt || 0) + '/' + a.cnt + ' resolved</span></div>'
			+ '<div class="it-assignee-pct"><div class="it-mini-bar"><div class="it-mini-fill" style="width:' + pct + '%"></div></div>'
			+ '<span>' + pct + '%</span></div>'
			+ '</div>';
	});
	html += '</div>';
	return html;
}

/* ================================================================
   RENDER: OVERDUE
   ================================================================ */
function itRenderOverdue($main, s) {
	var tickets = s.overdue_tickets;
	if (!tickets || !tickets.length) { $main.find('#it-overdue-area').html(''); return; }

	var html = '<div class="it-overdue"><div class="it-overdue-head">'
		+ itIcon('alert-triangle', 18)
		+ '<h3>Overdue Tickets <span class="it-overdue-badge">' + tickets.length + '</span></h3></div>';
	tickets.forEach(function(t) {
		html += '<div class="it-overdue-item" onclick="frappe.set_route(\'Form\',\'Service Ticket\',\'' + itEsc(t.name) + '\')">'
			+ '<span class="it-tid">' + itEsc(t.name) + '</span>'
			+ '<span class="it-overdue-subj">' + itEsc(t.subject || '') + '</span>'
			+ '<span class="it-overdue-by">Due ' + moment(t.resolution_by).fromNow() + '</span>'
			+ '</div>';
	});
	html += '</div>';
	$main.find('#it-overdue-area').html(html);
}
