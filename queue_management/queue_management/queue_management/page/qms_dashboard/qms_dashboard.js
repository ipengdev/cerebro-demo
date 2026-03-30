frappe.pages['qms-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'QMS Dashboard',
        single_column: true
    });

    // SVG icon helpers - crisp at any size
    var ICONS = {
        waiting: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        serving: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        completed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        avgwait: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        counter: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon-sm"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
        ticket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon-sm"><path d="M15 5v2"/><path d="M15 11v2"/><path d="M15 17v2"/><path d="M5 5h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7a2 2 0 0 1 2-2z"/></svg>',
        service: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon-sm"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>',
        location: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="q-icon-sm"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        notickets: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:48px;height:48px;opacity:.3;margin-bottom:12px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
        nocounters: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:36px;height:36px;opacity:.3;margin-bottom:8px"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
    };

    var _dashLocation = '';
    var _dashIcons = ICONS;
    var _qdTheme = localStorage.getItem('qms_dashboard_theme') || 'light';

    page.main.html(
        '<div class="qd" data-theme="' + _qdTheme + '">' +
        '<div class="qd-topbar">' +
        '<div class="qd-topbar-title">' + ICONS.ticket + ' <span id="qd-hospital-name">Queue Management</span></div>' +
        '<span class="qd-live-dot" id="qd-live-dot"></span><span class="qd-live-lbl" id="qd-live-lbl" style="font-size:12px">Live</span>' +
        '<button class="qd-theme-toggle" id="qd-theme-toggle" title="Toggle night/light mode">' +
        (_qdTheme === 'dark' ? '&#9728;' : '&#9790;') + '</button>' +
        '<div class="qd-date-filter">' +
        '<label>From:</label><input type="date" id="qd-from-date" value="' + frappe.datetime.get_today() + '">' +
        '<label>To:</label><input type="date" id="qd-to-date" value="' + frappe.datetime.get_today() + '">' +
        '<div class="qd-date-presets">' +
        '<button class="qd-date-preset active" data-preset="today">Today</button>' +
        '<button class="qd-date-preset" data-preset="yesterday">Yesterday</button>' +
        '<button class="qd-date-preset" data-preset="week">This Week</button>' +
        '<button class="qd-date-preset" data-preset="month">This Month</button>' +
        '</div>' +
        '</div>' +
        '<div class="qd-loc-filter">' + ICONS.location +
        '<label>Location:</label><select id="qd-loc-select"><option value="">All Locations</option></select></div>' +
        '</div>' +
        '<div class="qd-stats" id="qd-stats"></div>' +
        '<div id="qd-svc-section"></div>' +
        '<div class="row"><div class="col-lg-8 col-md-7"><div id="qd-queue-section"></div></div>' +
        '<div class="col-lg-4 col-md-5"><div id="qd-counter-section"></div></div></div>' +
        '</div>'
    );

    // Load hospital name from settings
    frappe.xcall('queue_management.qms_api.get_hospital_name').then(function(name) {
        page.set_title(name + ' \u2014 Dashboard');
        page.main.find('#qd-hospital-name').text(name);
    });

    // Theme toggle handler
    page.main.on('click', '#qd-theme-toggle', function() {
        var wrap = page.main.find('.qd');
        var cur = wrap.attr('data-theme');
        var nxt = cur === 'dark' ? 'light' : 'dark';
        wrap.attr('data-theme', nxt);
        $(this).html(nxt === 'dark' ? '&#9728;' : '&#9790;');
        localStorage.setItem('qms_dashboard_theme', nxt);
    });

    // Load locations
    frappe.xcall('queue_management.qms_kiosk_api.get_locations').then(function(locs) {
        var sel = page.main.find('#qd-loc-select');
        locs.forEach(function(l) {
            sel.append('<option value="' + l.name + '">' + l.location_name + '</option>');
        });
        sel.on('change', function() { _dashLocation = $(this).val(); updateDashLiveState(); loadDash(); });
    });

    // Date range filter
    page.main.find('#qd-from-date, #qd-to-date').on('change', function() {
        page.main.find('.qd-date-preset').removeClass('active');
        updateDashLiveState();
        loadDash();
    });

    // Date preset buttons
    page.main.on('click', '.qd-date-preset', function() {
        var preset = $(this).data('preset');
        var today = frappe.datetime.get_today();
        var from = today, to = today;
        if (preset === 'yesterday') {
            from = to = frappe.datetime.add_days(today, -1);
        } else if (preset === 'week') {
            var dayOfWeek = new Date(today).getDay();
            from = frappe.datetime.add_days(today, -dayOfWeek);
        } else if (preset === 'month') {
            from = today.substring(0, 8) + '01';
        }
        page.main.find('#qd-from-date').val(from);
        page.main.find('#qd-to-date').val(to);
        page.main.find('.qd-date-preset').removeClass('active');
        $(this).addClass('active');
        updateDashLiveState();
        loadDash();
    });

    // Avatar colors based on name
    var avatarColors = ['#f97316','#2563eb','#16a34a','#7c3aed','#ec4899','#06b6d4','#ea580c','#8b5cf6'];
    function getAvatarColor(name) {
        var hash = 0;
        for (var i = 0; i < (name||'').length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
        return avatarColors[Math.abs(hash) % avatarColors.length];
    }
    function getInitials(name) {
        if (!name || name === 'Walk-in') return '?';
        var parts = name.trim().split(/\s+/);
        return parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].substring(0,2).toUpperCase();
    }

    function esc(v) { return String(v||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;'); }

    function dashStatusToken(status) {
        return String(status || 'Closed').replace(/[^A-Za-z0-9]+/g, '-');
    }

    function dashBuildXferChip(isTransferred) {
        return '<span class="qd-xfer-chip' + (isTransferred ? '' : ' is-hidden') + '" data-row-transfer-chip>XFER</span>';
    }

    function dashBuildQueueRow(t, rowNumber) {
        var pName = t.patient_name || 'Walk-in';
        var ac = getAvatarColor(pName);
        var initials = getInitials(pName);
        var pr = t.priority || 'Normal';
        var prToken = dashStatusToken(pr);
        var statusText = t.status || '-';
        var statusToken = dashStatusToken(statusText);
        var waitMin = '';
        if (t.check_in_time) {
            try {
                var diff = Math.round((new Date() - new Date(t.check_in_time)) / 60000);
                if (diff >= 0) waitMin = diff + 'm';
            } catch(e) {}
        }
        var isTransferred = (t.transfer_count || 0) > 0;
        var ticketLabel = t.ticket_number || t.name;
        var row = '<tr data-ticket="' + esc(t.name || '') + '" data-ticket-number="' + esc(ticketLabel || '') + '">';
        row += '<td style="font-weight:800;color:var(--text-muted)">' + rowNumber + '</td>';
        row += '<td><div class="qd-tnum">' + ICONS.ticket + '<span data-row-ticket-label>' + esc(ticketLabel) + '</span>' + dashBuildXferChip(isTransferred) + '</div></td>';
        row += '<td><div class="qd-patient"><div class="qd-avatar" style="background:' + ac + '">' + initials + '</div><span>' + esc(pName) + '</span></div></td>';
        row += '<td>' + esc(t.service_display || t.service || '-') + '</td>';
        row += '<td><span class="qd-badge qd-badge-' + prToken + '">' + pr + '</span></td>';
        row += '<td data-row-counter>' + esc(t.counter || '-') + '</td>';
        row += '<td><div class="qd-wait-chip">' + ICONS.waiting + ' <span data-row-wait>' + (waitMin || '-') + '</span></div></td>';
        row += '<td><span class="qd-badge qd-badge-' + statusToken + '" data-row-status>' + esc(statusText) + '</span></td>';
        row += '</tr>';
        return row;
    }

    function dashEventMatchesLocation(data) {
        if (!_dashLocation || !data) return true;
        var loc = data.location || data.to_location || data.from_location || '';
        return !loc || loc === _dashLocation || data.to_location === _dashLocation || data.from_location === _dashLocation;
    }

    function dashFindCounterCard(counterName) {
        if (!counterName) return $();
        return page.main.find('.qd-ctr').filter(function() {
            return $(this).attr('data-counter') === counterName;
        }).first();
    }

    function dashFlashCounter($card) {
        if (!$card.length) return;
        $card.stop(true, true);
        $card.css({ transform: 'translateY(-2px)', boxShadow: '0 10px 24px rgba(37,99,235,.18)' });
        setTimeout(function() {
            $card.css({ transform: '', boxShadow: '' });
        }, 650);
    }

    function dashFindTicketRow(data) {
        var ticketId = data && data.ticket ? String(data.ticket) : '';
        var ticketNumber = data && data.ticket_number ? String(data.ticket_number) : '';
        return page.main.find('.qd-table tbody tr').filter(function() {
            var $row = $(this);
            return (ticketId && $row.attr('data-ticket') === ticketId) ||
                (ticketNumber && $row.attr('data-ticket-number') === ticketNumber);
        }).first();
    }

    function dashFlashRow($row) {
        if (!$row.length) return;
        $row.addClass('qd-row-live-flash');
        setTimeout(function() {
            $row.removeClass('qd-row-live-flash');
        }, 700);
    }

    function dashPatchTicketRow(data, patch) {
        var $row = dashFindTicketRow(data);
        if (!$row.length) return;
        if (patch.status) {
            var statusToken = dashStatusToken(patch.status);
            $row.find('[data-row-status]').attr('class', 'qd-badge qd-badge-' + statusToken).text(patch.status);
        }
        if (Object.prototype.hasOwnProperty.call(patch, 'counterText')) {
            $row.find('[data-row-counter]').text(patch.counterText);
        }
        if (Object.prototype.hasOwnProperty.call(patch, 'isTransferred')) {
            $row.find('[data-row-transfer-chip]').toggleClass('is-hidden', !patch.isTransferred);
        }
        if (patch.fade) {
            $row.addClass('qd-row-pending-exit');
        } else {
            $row.removeClass('qd-row-pending-exit');
        }
        dashFlashRow($row);
    }

    function dashApplyCounterVisual(counterName, status, ticketText) {
        var $card = dashFindCounterCard(counterName);
        if (!$card.length) return;
        var normalizedStatus = status || $card.attr('data-status') || 'Closed';
        var statusToken = dashStatusToken(normalizedStatus);
        var $icon = $card.find('[data-counter-icon]');
        var $status = $card.find('[data-counter-status]');
        var $ticket = $card.find('[data-counter-ticket]');
        $card.attr('data-status', normalizedStatus);
        $icon.removeClass('Available Busy Closed On-Break').addClass(statusToken);
        $status.removeClass('Available Busy Closed On-Break').addClass(statusToken).text(normalizedStatus);
        if (typeof ticketText === 'string') {
            $ticket.text(ticketText);
        }
        dashFlashCounter($card);
    }

    function dashApplyRealtimePatch(eventName, data) {
        if (!data) return;
        if (eventName === 'qms_counter_updated' && data.counter) {
            dashApplyCounterVisual(data.counter, data.status, data.status === 'Busy' ? 'Serving: Updating...' : 'No ticket');
            return;
        }
        if ((eventName === 'qms_ticket_called' || eventName === 'qms_ticket_serving') && data.counter) {
            dashApplyCounterVisual(data.counter, 'Busy', 'Serving: ' + (data.ticket_number || data.ticket || 'Updating...'));
            dashPatchTicketRow(data, {
                status: eventName === 'qms_ticket_serving' ? 'Serving' : 'Called',
                counterText: data.counter,
                fade: false,
            });
            return;
        }
        if ((eventName === 'qms_ticket_completed' || eventName === 'qms_ticket_held' || eventName === 'qms_ticket_no_show' || eventName === 'qms_ticket_cancelled') && data.counter) {
            dashApplyCounterVisual(data.counter, 'Available', 'Updating...');
            if (eventName === 'qms_ticket_completed') {
                dashPatchTicketRow(data, { status: 'Completed', counterText: data.counter || '-', fade: true });
            } else if (eventName === 'qms_ticket_held') {
                dashPatchTicketRow(data, { status: 'On Hold', counterText: data.counter || '-', fade: true });
            } else if (eventName === 'qms_ticket_cancelled') {
                dashPatchTicketRow(data, { status: 'Cancelled', counterText: '-', fade: true });
            } else if (eventName === 'qms_ticket_no_show') {
                dashPatchTicketRow(data, { status: data.requeued ? 'Waiting' : 'No Show', counterText: '-', fade: !data.requeued });
            }
            return;
        }
        if ((eventName === 'qms_ticket_completed' || eventName === 'qms_ticket_held' || eventName === 'qms_ticket_no_show' || eventName === 'qms_ticket_cancelled') && data.ticket) {
            if (eventName === 'qms_ticket_completed') {
                dashPatchTicketRow(data, { status: 'Completed', counterText: data.counter || '-', fade: true });
            } else if (eventName === 'qms_ticket_held') {
                dashPatchTicketRow(data, { status: 'On Hold', counterText: data.counter || '-', fade: true });
            } else if (eventName === 'qms_ticket_cancelled') {
                dashPatchTicketRow(data, { status: 'Cancelled', counterText: '-', fade: true });
            } else if (eventName === 'qms_ticket_no_show') {
                dashPatchTicketRow(data, { status: data.requeued ? 'Waiting' : 'No Show', counterText: '-', fade: !data.requeued });
            }
            return;
        }
        if (eventName === 'qms_ticket_transferred') {
            if (data.from_counter) dashApplyCounterVisual(data.from_counter, 'Available', 'Updating...');
            if (data.to_counter) dashApplyCounterVisual(data.to_counter, 'Busy', 'Incoming ticket');
            dashPatchTicketRow(data, {
                status: 'Waiting',
                counterText: data.to_counter || '-',
                isTransferred: true,
                fade: false,
            });
            return;
        }
        if (eventName === 'qms_ticket_requeued' && data.counter) {
            dashApplyCounterVisual(data.counter, 'Available', 'No ticket');
            dashPatchTicketRow(data, { status: 'Waiting', counterText: '-', fade: false });
        }
    }

    function dashRangeIncludesToday() {
        var today = frappe.datetime.get_today();
        var fromDate = page.main.find('#qd-from-date').val() || today;
        var toDate = page.main.find('#qd-to-date').val() || fromDate;
        return fromDate <= today && toDate >= today;
    }

    function updateDashLiveState() {
        var isLive = dashRangeIncludesToday();
        var dot = page.main.find('#qd-live-dot');
        var lbl = page.main.find('#qd-live-lbl');
        lbl.text(isLive ? 'Live' : 'History');
        dot.css('opacity', isLive ? '1' : '.35');
        lbl.css('opacity', isLive ? '1' : '.65');
    }

    function loadDash() {
        var args = {};
        if (_dashLocation) args.location = _dashLocation;
        var fromDate = page.main.find('#qd-from-date').val();
        var toDate = page.main.find('#qd-to-date').val();
        if (fromDate) args.from_date = fromDate;
        if (toDate) args.to_date = toDate;

        frappe.xcall('queue_management.qms_api.get_queue_status', args).then(function(d) {
            var tickets = d.tickets || [];
            var counters = d.counters || [];

            // Stats
            var sh = '';
            sh += '<div class="qd-stat waiting"><div class="qd-stat-icon">' + ICONS.waiting + '</div><div class="qd-stat-text"><div class="qd-stat-val">' + (d.waiting || 0) + '</div><div class="qd-stat-lbl">Waiting</div></div></div>';
            sh += '<div class="qd-stat serving"><div class="qd-stat-icon">' + ICONS.serving + '</div><div class="qd-stat-text"><div class="qd-stat-val">' + (d.serving || 0) + '</div><div class="qd-stat-lbl">Being Served</div></div></div>';
            sh += '<div class="qd-stat completed"><div class="qd-stat-icon">' + ICONS.completed + '</div><div class="qd-stat-text"><div class="qd-stat-val">' + (d.completed || 0) + '</div><div class="qd-stat-lbl">Completed</div></div></div>';
            sh += '<div class="qd-stat avgwait"><div class="qd-stat-icon">' + ICONS.avgwait + '</div><div class="qd-stat-text"><div class="qd-stat-val">' + (d.avg_wait || '0') + '</div><div class="qd-stat-lbl">Avg Wait (min)</div></div></div>';
            page.main.find('#qd-stats').html(sh);

            // Service breakdown
            var svcMap = {};
            tickets.forEach(function(t) {
                var s = t.service_display || t.service || 'Unknown';
                if (!svcMap[s]) svcMap[s] = {waiting: 0, serving: 0};
                if (t.status === 'Waiting') svcMap[s].waiting++;
                else svcMap[s].serving++;
            });
            var svcKeys = Object.keys(svcMap);
            if (svcKeys.length) {
                var svh = '<div class="qd-section"><div class="qd-section-head">' + ICONS.service + '<span class="qd-section-title">Services</span></div>';
                svh += '<div class="qd-svc-grid">';
                var svcColors = ['#3b82f6','#16a34a','#f97316','#7c3aed','#ec4899','#06b6d4','#ea580c'];
                svcKeys.sort().forEach(function(s, i) {
                    var c = svcColors[i % svcColors.length];
                    svh += '<div class="qd-svc-card" style="border-left-color:' + c + '">';
                    svh += '<div class="qd-svc-name">' + ICONS.service + ' ' + esc(s) + '</div>';
                    svh += '<div class="qd-svc-stats">';
                    svh += '<div class="qd-svc-stat"><div class="qd-svc-stat-val" style="color:#ea580c">' + svcMap[s].waiting + '</div><div class="qd-svc-stat-lbl">Waiting</div></div>';
                    svh += '<div class="qd-svc-stat"><div class="qd-svc-stat-val" style="color:#2563eb">' + svcMap[s].serving + '</div><div class="qd-svc-stat-lbl">Serving</div></div>';
                    svh += '</div></div>';
                });
                svh += '</div></div>';
                page.main.find('#qd-svc-section').html(svh);
            } else {
                page.main.find('#qd-svc-section').html('');
            }

            // Queue table with search + pagination
            var _dashPageSize = 50;
            var qh = '<div class="qd-section"><div class="qd-section-head">' + ICONS.ticket + '<span class="qd-section-title">Live Queue</span><span class="qd-section-count">' + tickets.length + '</span></div>';
            if (tickets.length) {
                qh += '<div class="qd-search-wrap"><input type="text" class="qd-search" id="qd-queue-search" placeholder="Search by ticket # or patient name..."></div>';
            }
            if (!tickets.length) {
                qh += '<div class="qd-empty">' + ICONS.notickets + '<div style="font-size:15px;font-weight:600;margin-bottom:4px">All Clear!</div><div style="font-size:13px">No active tickets right now</div></div>';
            } else {
                qh += '<table class="qd-table"><thead><tr><th>#</th><th>Ticket</th><th>Patient</th><th>Service</th><th>Priority</th><th>Counter</th><th>Wait</th><th>Status</th></tr></thead><tbody>';
                var posCounter = 0;
                var visibleCount = Math.min(tickets.length, _dashPageSize);
                for (var ti = 0; ti < visibleCount; ti++) {
                    var t = tickets[ti];
                    posCounter++;
                    qh += dashBuildQueueRow(t, posCounter);
                }
                qh += '</tbody></table>';
                if (tickets.length > _dashPageSize) {
                    qh += '<div style="text-align:center;padding:12px"><button class="qd-date-preset" id="qd-show-all">Show All (' + tickets.length + ' tickets)</button></div>';
                }
            }
            qh += '</div>';
            page.main.find('#qd-queue-section').html(qh);

            // "Show All" handler
            if (tickets.length > _dashPageSize) {
                page.main.find('#qd-show-all').on('click', function() {
                    var tbody = page.main.find('.qd-table tbody');
                    for (var ti = _dashPageSize; ti < tickets.length; ti++) {
                        var t = tickets[ti];
                        tbody.append(dashBuildQueueRow(t, ti + 1));
                    }
                    $(this).parent().remove();
                });
            }

            // Search filter on queue table
            page.main.find('#qd-queue-search').on('input', function() {
                var q = $(this).val().toLowerCase();
                page.main.find('.qd-table tbody tr').each(function() {
                    var text = $(this).text().toLowerCase();
                    $(this).toggle(text.includes(q));
                });
            });

            // Counters
            var ch = '<div class="qd-section"><div class="qd-section-head">' + ICONS.counter + '<span class="qd-section-title">Counters</span><span class="qd-section-count">' + counters.length + '</span></div>';
            if (!counters.length) {
                ch += '<div class="qd-empty">' + ICONS.nocounters + '<div style="font-size:14px;font-weight:600">No Counters</div><div style="font-size:13px;margin-top:4px">Configure counters to get started</div></div>';
            } else {
                ch += '<div class="qd-counter-grid">';
                counters.forEach(function(c) {
                    var st = c.status || 'Closed';
                    var statusToken = dashStatusToken(st);
                    ch += '<div class="qd-ctr" data-counter="' + esc(c.name) + '" data-status="' + esc(st) + '">';
                    ch += '<div class="qd-ctr-icon ' + statusToken + '" data-counter-icon="' + esc(c.name) + '">' + ICONS.counter + '</div>';
                    ch += '<div class="qd-ctr-info"><div class="qd-ctr-name">' + esc(c.counter_name) + '</div>';
                    ch += '<div class="qd-ctr-ticket" data-counter-ticket="' + esc(c.name) + '">' + (c.current_ticket ? 'Serving: ' + esc(c.current_ticket_number || c.current_ticket) : 'No ticket') + '</div></div>';
                    ch += '<span class="qd-ctr-status ' + statusToken + '" data-counter-status="' + esc(c.name) + '">' + st + '</span>';
                    ch += '</div>';
                });
                ch += '</div>';
            }
            ch += '</div>';
            page.main.find('#qd-counter-section').html(ch);
        }).catch(function(err) {
            page.main.find('#qd-stats').html(
                '<div class="qd-stat" style="grid-column:1/-1;text-align:center;padding:24px">' +
                '<div style="font-size:15px;font-weight:600;color:var(--text-muted)">Failed to load dashboard</div>' +
                '<div style="font-size:13px;color:var(--text-light);margin-top:4px">' + esc(err.message || 'Unknown error') + '</div>' +
                '<button class="qd-date-preset" id="qd-retry-btn" style="margin-top:12px">Retry</button></div>'
            );
            page.main.find('#qd-retry-btn').on('click', loadDash);
        });
    }

    var _dashDebounce = null;
    function debouncedLoadDash() {
        if (_dashDebounce) clearTimeout(_dashDebounce);
		_dashDebounce = setTimeout(loadDash, 120);
    }

    function _dashFilteredRefresh(eventName, data) {
        if (!dashRangeIncludesToday()) return;
        if (!dashEventMatchesLocation(data)) return;
        dashApplyRealtimePatch(eventName, data);
        debouncedLoadDash();
    }

    var _dashRealtimeEvents = ['qms_ticket_called', 'qms_ticket_completed', 'qms_new_ticket', 'qms_ticket_held', 'qms_ticket_no_show', 'qms_counter_updated', 'qms_ticket_transferred', 'qms_ticket_requeued', 'qms_ticket_serving', 'qms_ticket_cancelled'];
    var _dashInterval = null;
    var _dashRealtimeHandlers = {};

    function _dashBindLive() {
        if (_dashInterval) return; // already bound
        loadDash();
        _dashInterval = setInterval(loadDash, 15000);
        _dashRealtimeEvents.forEach(function(evt) {
            if (!_dashRealtimeHandlers[evt]) {
                _dashRealtimeHandlers[evt] = function(data) {
                    _dashFilteredRefresh(evt, data);
                };
            }
            frappe.realtime.on(evt, _dashRealtimeHandlers[evt]);
        });
    }

    function _dashUnbindLive() {
        if (_dashInterval) { clearInterval(_dashInterval); _dashInterval = null; }
        if (_dashDebounce) { clearTimeout(_dashDebounce); _dashDebounce = null; }
        _dashRealtimeEvents.forEach(function(evt) {
            if (_dashRealtimeHandlers[evt]) frappe.realtime.off(evt, _dashRealtimeHandlers[evt]);
        });
    }

    updateDashLiveState();
    _dashBindLive();

    // Store for on_page_show re-bind
    wrapper._qmsDashBind = _dashBindLive;

    // Cleanup on page hide to prevent memory leaks
    page.wrapper.on('page-change', _dashUnbindLive);
};

// Re-bind live updates when navigating back to the dashboard
frappe.pages['qms-dashboard'].on_page_show = function(wrapper) {
    if (wrapper._qmsDashBind) wrapper._qmsDashBind();
};
