frappe.pages['qms-call-screen'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'QMS Call Screen',
        single_column: true
    });

    window._qmsCallPage = page;
    window._csInterval = null;
    var _csCounterLocations = {};
    var _csLiveBound = false;

    // SVG icons
    var IC = {
        hospital: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><path d="M9 9h1"/><path d="M9 13h1"/><path d="M9 17h1"/></svg>',
        medCross: '<svg viewBox="0 0 24 24" fill="currentColor" class="cs-ico"><path d="M9 2h6v6h6v6h-6v6H9v-6H3V8h6V2z" opacity=".9"/></svg>',
        heartPulse: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M3 12h4l3-9 4 18 3-9h4"/></svg>',
        callNext: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
        complete: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><polyline points="20 6 9 17 4 12"/></svg>',
        hold: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>',
        noshow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        recall: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M18.36 19.36A9 9 0 1 0 5 5"/><polyline points="1 1 5 5 9 1"/></svg>',
        transfer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><polyline points="15 3 21 3 21 9"/><line x1="21" y1="3" x2="14" y2="10"/><polyline points="9 21 3 21 3 15"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
        counter: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
        queue: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
        service: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
        ticket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="cs-ico"><path d="M15 5v2"/><path d="M15 11v2"/><path d="M15 17v2"/><path d="M5 5h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7a2 2 0 0 1 2-2z"/></svg>',
        noTicket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:56px;height:56px;color:var(--text-muted);opacity:.25"><path d="M15 5v2"/><path d="M15 11v2"/><path d="M15 17v2"/><path d="M5 5h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7a2 2 0 0 1 2-2z"/></svg>',
        emptyQ: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:28px;height:28px;opacity:.3"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
    };

    // Dark mode: load saved preference (default to dark)
    var _csTheme = localStorage.getItem('qms_cs_theme') || 'dark';

    page.main.html(
        '<div class="cs-wrap" data-theme="' + _csTheme + '">' +
        '<div class="cs-hospital-header">' +
        '<div class="cs-hospital-brand">' +
        '<div class="cs-hospital-logo">' + IC.medCross + '</div>' +
        '<div class="cs-hospital-text">' +
        '<div class="cs-hospital-name" id="cs-hospital-name">Queue Management</div>' +
        '<div class="cs-hospital-sub">' + IC.heartPulse + ' Patient Queue Management</div>' +
        '</div>' +
        '</div>' +
        '<div class="cs-hospital-right">' +
        '<div class="cs-hospital-time" id="cs-hospital-time"></div>' +
        '<button class="cs-theme-toggle" id="cs-theme-toggle" title="Toggle dark/light mode">' +
        (_csTheme === 'dark' ? '&#9728;' : '&#9790;') +
        '</button>' +
        '</div>' +
        '</div>' +
        '<div class="cs-counter-bar">' +
        '<label>' + IC.counter + ' Your Counter:</label>' +
        '<select id="cs-counter-select"><option value="">-- Select your counter --</option></select>' +
        '<div class="cs-counter-info" id="cs-counter-info"></div>' +
        '<div class="cs-shift-bar" id="cs-shift-bar"></div>' +
        '</div>' +
        '<div id="cs-content"></div>' +
        '</div>'
    );

    // Load hospital name from settings
    frappe.xcall('queue_management.qms_api.get_hospital_name').then(function(name) {
        page.main.find('#cs-hospital-name').text(name);
    });

    // Live clock in hospital header
    function _csUpdateClock() {
        var el = document.getElementById('cs-hospital-time');
        if (!el) return;
        var now = new Date();
        var opts = {weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'};
        el.textContent = now.toLocaleDateString('en-US', opts);
    }
    _csUpdateClock();
    var _csClockInterval = null;

    // Theme toggle handler
    page.main.on('click', '#cs-theme-toggle', function() {
        var wrap = page.main.find('.cs-wrap');
        var current = wrap.attr('data-theme');
        var next = current === 'dark' ? 'light' : 'dark';
        wrap.attr('data-theme', next);
        $(this).html(next === 'dark' ? '&#9728;' : '&#9790;');
        localStorage.setItem('qms_cs_theme', next);
    });

    // Keep icon references on window for render function
    window._csIcons = IC;

    frappe.xcall('frappe.client.get_list', {
        doctype: 'QMS Counter',
        filters: {is_active: 1},
        fields: ['name', 'counter_name', 'counter_number', 'status', 'location'],
        limit_page_length: 50
    }).then(function(counters) {
        var sel = page.main.find('#cs-counter-select');
        counters.forEach(function(c) {
            _csCounterLocations[c.name] = c.location || '';
            sel.append('<option value="' + c.name + '">' + c.counter_name + ' (#' + c.counter_number + ')</option>');
        });
        sel.on('change', function() {
            if (window._csInterval) clearInterval(window._csInterval);
            _qmsRenderCS();
            window._csInterval = setInterval(_qmsRenderCS, 15000);
        });

        // Auto-select counter assigned to current user
        frappe.xcall('queue_management.qms_display_api.get_my_counter').then(function(myCounter) {
            if (myCounter && myCounter.name) {
                sel.val(myCounter.name).trigger('change');
            }
        });
    });

    // Event delegation for all action buttons
    page.main.on('click', '[data-cs-action]', function() {
        var $el = $(this);
        var action = $el.attr('data-cs-action');
        var counter = $el.attr('data-cs-counter');
        var ticket = $el.attr('data-cs-ticket') || '';
        window.csAction(action, counter, ticket);
    });

    // Shift button event delegation
    page.main.on('click', '[data-cs-shift]', function() {
        var action = $(this).attr('data-cs-shift');
        var counter = $(this).attr('data-cs-counter');
        var apiMap = {
            'start': {fn: 'queue_management.qms_api.start_shift', msg: 'Shift started'},
            'end':   {fn: 'queue_management.qms_api.end_shift', msg: 'Shift ended'},
            'break': {fn: 'queue_management.qms_api.take_break', msg: 'On break'}
        };
        var cfg = apiMap[action];
        if (!cfg) return;
        function _doShift() {
            fetch('/api/method/' + cfg.fn, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                body: JSON.stringify({counter: counter})
            }).then(function(res) { return res.json(); }).then(function() {
                frappe.show_alert({message: cfg.msg, indicator: action === 'end' ? 'blue' : 'green'});
                _qmsRenderCS();
            }).catch(function(e) {
                frappe.show_alert({message: (e && e.message) || 'Action failed', indicator: 'red'});
            });
        }
        if (action === 'end') {
            _csConfirm('End your shift at this counter?', _doShift);
        } else {
            _doShift();
        }
    });

    var _csDebounce = null;
    function _csMatchesEvent(data) {
        var selectedCounter = page.main.find('#cs-counter-select').val();
        if (!selectedCounter || !data) return true;
        if (data.counter === selectedCounter || data.from_counter === selectedCounter || data.to_counter === selectedCounter) {
            return true;
        }
        var selectedLocation = _csCounterLocations[selectedCounter] || '';
        if (!selectedLocation) return true;
        var eventLocation = data.location || data.to_location || data.from_location || '';
        return !eventLocation || eventLocation === selectedLocation;
    }

    function debouncedRenderCS(data) {
        if (!_csMatchesEvent(data)) return;
        // If we just rendered from a combined action response, skip this realtime-triggered
        // re-render — it would be redundant (same data, extra HTTP call for nothing).
        // Keep suppressing for the full window (actions can fire multiple events).
        if (window._csActionRenderedAt && (Date.now() - window._csActionRenderedAt) < 2000) {
            console.log('[CS] skipping redundant realtime render (action rendered',
                (Date.now() - window._csActionRenderedAt) + 'ms ago)');
            return;
        }
        if (_csDebounce) clearTimeout(_csDebounce);
        _csDebounce = setTimeout(_qmsRenderCS, 80);
    }
    window.debouncedRenderCS = debouncedRenderCS;

    var _csRealtimeEvents = ['qms_ticket_called', 'qms_ticket_completed', 'qms_new_ticket', 'qms_ticket_held', 'qms_ticket_no_show', 'qms_counter_updated', 'qms_ticket_transferred', 'qms_ticket_cancelled', 'qms_ticket_requeued', 'qms_ticket_serving'];

    function _csBindLive() {
        if (_csLiveBound) return;
        _csRealtimeEvents.forEach(function(evt) {
            frappe.realtime.on(evt, debouncedRenderCS);
        });
        if (_csClockInterval) clearInterval(_csClockInterval);
        _csClockInterval = setInterval(_csUpdateClock, 30000);
        _csUpdateClock();
        $(document).on('keydown.qms_cs', _csKeyHandler);
        _csLiveBound = true;
        // Re-trigger render for current counter selection
        var sel = page.main.find('#cs-counter-select').val();
        if (sel) {
            if (window._csInterval) clearInterval(window._csInterval);
            _qmsRenderCS();
            window._csInterval = setInterval(_qmsRenderCS, 15000);
        }
    }

    function _csUnbindLive() {
        $(document).off('keydown.qms_cs');
        if (window._csInterval) { clearInterval(window._csInterval); window._csInterval = null; }
        if (_csClockInterval) { clearInterval(_csClockInterval); _csClockInterval = null; }
        if (_csDebounce) { clearTimeout(_csDebounce); _csDebounce = null; }
        _csRealtimeEvents.forEach(function(evt) {
            frappe.realtime.off(evt, debouncedRenderCS);
        });
        _csLiveBound = false;
    }

    _csBindLive();

    // ── Keyboard Shortcuts ──
    function _csKeyHandler(e) {
        // Don't trigger if user is typing in an input/textarea/select or dialog is open
        if ($(e.target).is('input, textarea, select') || $('.modal.show').length || $('.cs-dialog-overlay').length) return;
        if (!e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;

        var counter = page.main.find('#cs-counter-select').val();
        if (!counter) return;

        var currentTicket = (window._csServingTickets && window._csServingTickets.length === 1)
            ? window._csServingTickets[0].name : null;

        switch(e.key.toLowerCase()) {
            case 'n':
            case ' ':
                e.preventDefault();
                window.csAction('next', counter, '');
                break;
            case 'c':
                if (currentTicket) {
                    e.preventDefault();
                    window.csAction('complete', counter, currentTicket);
                }
                break;
            case 'h':
                if (currentTicket) {
                    e.preventDefault();
                    window.csAction('hold', counter, currentTicket);
                }
                break;
            case 't':
                if (currentTicket) {
                    e.preventDefault();
                    window.csAction('transfer', counter, currentTicket);
                }
                break;
        }
    }

    // Store for on_page_show re-bind
    wrapper._qmsCSBind = _csBindLive;

    // Cleanup on page change
    page.wrapper.on('page-change', _csUnbindLive);
};

// Re-bind live updates when navigating back to the call screen
frappe.pages['qms-call-screen'].on_page_show = function(wrapper) {
    if (wrapper._qmsCSBind) wrapper._qmsCSBind();
};

function _esc(v) {
    return String(v || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/'/g, '&#39;');
}

function _csStatusToken(status) {
    return String(status || 'Closed').replace(/[^A-Za-z0-9]+/g, '-');
}

function _qmsRenderCS() {
    var page = window._qmsCallPage;
    if (!page) return;
    if (window._csRendering) {
        // A render is in progress — schedule a re-render once it finishes
        window._csRenderQueued = true;
        return;
    }
    var counter = page.main.find('#cs-counter-select').val();
    var content = page.main.find('#cs-content');
    if (!counter) { content.html(''); page.main.find('#cs-counter-info').html(''); return; }

    window._csRendering = true;
    window._csRenderQueued = false;
    var _pollT0 = performance.now();

    // Raw fetch instead of frappe.xcall to bypass Frappe request pipeline overhead
    fetch('/api/method/queue_management.qms_display_api.get_call_screen_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        body: JSON.stringify({counter: counter})
    }).then(function(res) { return res.json(); }).then(function(resp) {
        var data = resp.message || resp;
        console.log('[CS] poll/realtime refresh:', (performance.now()-_pollT0).toFixed(0) + 'ms');
        _csRenderData(data);
    }).catch(function(e) {
        console.log('[CS] poll/realtime refresh error:', e);
    }).finally(function() {
        window._csRendering = false;
        // If events arrived while we were rendering, re-render now
        if (window._csRenderQueued) {
            window._csRenderQueued = false;
            setTimeout(_qmsRenderCS, 100);
        }
    });
}

// Render the call screen from pre-fetched data (no API call)
function _csRenderData(data) {
    var page = window._qmsCallPage;
    if (!page) return;
    var counter = page.main.find('#cs-counter-select').val();
    var content = page.main.find('#cs-content');
    if (!counter) return;

    var IC = window._csIcons;
        var ct = data.current_ticket;
        var stList = data.serving_tickets || [];
        window._csCurrentTicket = ct;
        window._csServingTickets = stList;
        var ctr = data.counter || {};
        var wl = data.waiting || [];
        var hl = data.on_hold || [];
        var tl = data.transferred_out || [];
        var ql = data.queue_length || 0;
        var ec = _esc(counter);

        var cStatus = ctr.status || 'Available';
        page.main.find('#cs-counter-info').html(
            '<span class="cs-status-dot ' + _csStatusToken(cStatus) + '"></span><span>' + cStatus + '</span>'
        );

        // Render shift buttons based on status
        var shiftHtml = '';
        if (cStatus === 'Closed' || cStatus === 'On Break') {
            shiftHtml += '<button class="cs-shift-btn start" data-cs-shift="start" data-cs-counter="' + ec + '">&#9654; Start Shift</button>';
        }
        if (cStatus === 'Available' || cStatus === 'Busy') {
            shiftHtml += '<button class="cs-shift-btn break" data-cs-shift="break" data-cs-counter="' + ec + '">&#9749; Take Break</button>';
            shiftHtml += '<button class="cs-shift-btn end" data-cs-shift="end" data-cs-counter="' + ec + '">&#9632; End Shift</button>';
        }
        page.main.find('#cs-shift-bar').html(shiftHtml);

        var h = '';

        // Stats bar
        h += '<div class="cs-stats">';
        h += '<div class="cs-stat waiting"><div class="cs-stat-icon">' + IC.queue + '</div><div><div class="cs-stat-val">' + ql + '</div><div class="cs-stat-lbl">In Queue</div></div></div>';
        h += '<div class="cs-stat serving"><div class="cs-stat-icon">' + IC.user + '</div><div><div class="cs-stat-val">' + stList.length + '</div><div class="cs-stat-lbl">Now Serving</div></div></div>';
        h += '<div class="cs-stat held"><div class="cs-stat-icon">' + IC.hold + '</div><div><div class="cs-stat-val">' + hl.length + '</div><div class="cs-stat-lbl">On Hold</div></div></div>';
        h += '<div class="cs-stat transferred"><div class="cs-stat-icon">' + IC.transfer + '</div><div><div class="cs-stat-val">' + tl.length + '</div><div class="cs-stat-lbl">Transferred</div></div></div>';
        h += '<div class="cs-stat done"><div class="cs-stat-icon">' + IC.complete + '</div><div><div class="cs-stat-val">' + (data.completed_today || 0) + '</div><div class="cs-stat-lbl">Completed</div></div></div>';
        h += '</div>';

        // ── Call Next button (always visible, separate from ticket cards) ──
        h += '<div class="cs-call-next-bar">';
        h += '<button class="cs-btn cs-btn-next" data-cs-action="next" data-cs-counter="' + ec + '">' + IC.callNext + ' Call Next Ticket<span class="cs-btn-shortcut">N</span></button>';
        h += '</div>';

        // ── Serving tickets area ──
        h += '<div class="cs-serving-area">';
        h += '<div class="cs-serving-header">' + IC.bell + ' Currently Serving (' + stList.length + ')</div>';
        if (stList.length) {
            // Determine the most recently called ticket for visual emphasis
            var latestIdx = 0;
            if (stList.length > 1) {
                var latestTime = 0;
                stList.forEach(function(st, idx) {
                    var t = st.called_time ? new Date(st.called_time).getTime() : 0;
                    if (t > latestTime) { latestTime = t; latestIdx = idx; }
                });
            }
            h += '<div class="cs-serving-grid">';
            stList.forEach(function(st, idx) {
                var stEsc = _esc(st.name);
                var waitInfo = '';
                if (st.called_time) {
                    try {
                        var calledAt = new Date(st.called_time.replace(' ', 'T'));
                        var serverNow = data.server_time ? new Date(data.server_time.replace(' ', 'T')) : new Date();
                        var elapsed = Math.round((serverNow - calledAt) / 60000);
                        if (elapsed >= 0) waitInfo = elapsed + ' min ago';
                    } catch(e) {}
                }
                h += '<div class="cs-serve-card' + (stList.length > 1 && idx === latestIdx ? ' cs-serve-card-latest' : '') + '" data-ticket="' + stEsc + '">';
                h += '<div class="cs-serve-card-top">';
                h += '<div class="cs-serve-ticket-num">' + (st.ticket_number || st.name) + '</div>';
                h += '<span class="cs-q-badge cs-q-badge-' + _esc(st.status || 'Called') + '">' + _esc(st.status || 'Called') + '</span>';
                if (st.transferred_from_counter) {
                    h += '<span class="cs-serve-transferred">' + IC.transfer + ' from ' + _esc(st.transferred_from_counter_name || st.transferred_from_counter) + '</span>';
                }
                h += '</div>';
                h += '<div class="cs-serve-card-details">';
                h += '<div class="cs-serve-detail">' + IC.user + ' ' + _esc(st.patient_name || 'Walk-in') + '</div>';
                h += '<div class="cs-serve-detail">' + IC.service + ' ' + _esc(st.service || '-') + '</div>';
                if (waitInfo) {
                    h += '<div class="cs-serve-timer">' + IC.queue + ' Called ' + waitInfo + '</div>';
                }
                h += '</div>';
                h += '<div class="cs-serve-card-actions">';
                if (st.status === 'Called') {
                    h += '<button class="cs-mini-btn cs-mini-call" data-cs-action="serve" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="Start Serving">' + IC.user + '</button>';
                }
                h += '<button class="cs-mini-btn cs-mini-done" data-cs-action="complete" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="Complete">' + IC.complete + '</button>';
                h += '<button class="cs-mini-btn cs-mini-hold" data-cs-action="hold" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="Hold">' + IC.hold + '</button>';
                h += '<button class="cs-mini-btn cs-mini-noshow" data-cs-action="noshow" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="No Show">' + IC.noshow + '</button>';
                h += '<button class="cs-mini-btn cs-mini-recall" data-cs-action="recall" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="Recall">' + IC.recall + '</button>';
                h += '<button class="cs-mini-btn cs-mini-transfer" data-cs-action="transfer" data-cs-counter="' + ec + '" data-cs-ticket="' + stEsc + '" title="Transfer">' + IC.transfer + '</button>';
                h += '</div>';
                h += '</div>';
            });
            h += '</div>';
        } else {
            h += '<div class="cs-no-ticket">' + IC.noTicket;
            h += '<div class="cs-no-ticket-text">No ticket being served</div>';
            h += '<div style="font-size:13px;color:var(--text-light)">Click &quot;Call Next Ticket&quot; to start</div></div>';
        }
        h += '</div>';

        // Bottom: waiting + on hold
        h += '<div class="cs-bottom">';

        // Waiting queue — with position numbers and transfer indicators
        h += '<div class="cs-panel"><div class="cs-panel-header">' + IC.queue + '<span class="cs-panel-title">Waiting Queue</span><span class="cs-panel-count">' + wl.length + '</span></div>';
        h += '<div class="cs-panel-body">';
        if (wl.length) {
            wl.forEach(function(t, idx) {
                var tpr = t.priority || 'Normal';
                var wt = '';
                if (t.check_in_time) {
                    try {
                        var checkInYear = new Date(t.check_in_time).getFullYear();
                        if (checkInYear > 2000) {
                            var diff = Math.round((new Date() - new Date(t.check_in_time)) / 60000);
                            if (diff >= 0) wt = diff + ' min';
                        } else {
                            wt = 'returning';
                        }
                    } catch(e) {}
                }
                var waitClass = '';
                if (wt) {
                    var mins = parseInt(wt);
                    if (mins > 15) waitClass = ' long';
                    else if (mins > 5) waitClass = ' medium';
                    else waitClass = ' short';
                }
                var isTransferred = (t.transfer_count || 0) > 0;
                h += '<div class="cs-queue-row" data-cs-action="call" data-cs-counter="' + ec + '" data-cs-ticket="' + _esc(t.name) + '" title="Click to call this ticket">';
                h += '<span class="cs-q-pos">#' + (idx + 1) + '</span>';
                h += '<span class="cs-q-num">' + IC.ticket + ' ' + (t.ticket_number || t.name) + '</span>';
                if (isTransferred && t.transferred_from_counter) {
                    h += '<span class="cs-q-transferred" title="Transferred from ' + _esc(t.transferred_from_counter_name || t.transferred_from_counter) + '">&#x21C4; ' + _esc(t.transferred_from_counter_name || '') + '</span>';
                }
                h += '<span class="cs-q-patient">' + IC.user + ' ' + _esc(t.patient_name || 'Walk-in') + '</span>';
                h += '<span class="cs-q-service">' + _esc(t.service || '') + '</span>';
                h += '<span class="cs-q-badge cs-q-badge-' + tpr + '">' + tpr + '</span>';
                h += '<span class="cs-q-wait' + waitClass + '">' + wt + '</span>';
                h += '</div>';
            });
        } else {
            h += '<div class="cs-empty">' + IC.emptyQ + '<div style="margin-top:8px">Queue is empty</div></div>';
        }
        h += '</div></div>';

        // On hold
        h += '<div class="cs-panel"><div class="cs-panel-header">' + IC.hold + '<span class="cs-panel-title">On Hold</span><span class="cs-panel-count">' + hl.length + '</span></div>';
        h += '<div class="cs-panel-body">';
        if (hl.length) {
            hl.forEach(function(t) {
                var tpr = t.priority || 'Normal';
                h += '<div class="cs-queue-row" data-cs-action="call" data-cs-counter="' + ec + '" data-cs-ticket="' + _esc(t.name) + '" title="Click to recall this ticket">';
                h += '<span class="cs-q-num">' + IC.ticket + ' ' + (t.ticket_number || t.name) + '</span>';
                h += '<span class="cs-q-patient">' + IC.user + ' ' + _esc(t.patient_name || 'Walk-in') + '</span>';
                h += '<span class="cs-q-service">' + _esc(t.service || '') + '</span>';
                h += '<span class="cs-q-badge cs-q-badge-' + tpr + '">' + tpr + '</span>';
                h += '</div>';
            });
        } else {
            h += '<div class="cs-empty">' + IC.hold + '<div style="margin-top:8px">No tickets on hold</div></div>';
        }
        h += '</div></div>';

        // Transferred out
        h += '<div class="cs-panel cs-panel-transferred"><div class="cs-panel-header">' + IC.transfer + '<span class="cs-panel-title">Transferred</span><span class="cs-panel-count">' + tl.length + '</span></div>';
        h += '<div class="cs-panel-body">';
        if (tl.length) {
            tl.forEach(function(t) {
                var tpr = t.priority || 'Normal';
                var destName = t.dest_counter_name || t.counter || '';
                h += '<div class="cs-queue-row cs-transferred-row">';
                h += '<span class="cs-q-num">' + IC.ticket + ' ' + (t.ticket_number || t.name) + '</span>';
                h += '<span class="cs-q-patient">' + IC.user + ' ' + _esc(t.patient_name || 'Walk-in') + '</span>';
                h += '<span class="cs-q-service">' + _esc(t.service || '') + '</span>';
                h += '<span class="cs-q-dest">' + IC.transfer + ' ' + _esc(destName) + '</span>';
                h += '<span class="cs-q-badge cs-q-badge-' + _esc(t.status) + '">' + _esc(t.status) + '</span>';
                h += '</div>';
            });
        } else {
            h += '<div class="cs-empty">' + IC.transfer + '<div style="margin-top:8px">No transferred tickets</div></div>';
        }
        h += '</div></div></div>';

        h += '<div class="cs-refresh-note">' + IC.heartPulse + ' Live updates &bull; Click a waiting ticket to call &bull; Keyboard: Alt+N=Call Next, Alt+C=Complete, Alt+H=Hold, Alt+T=Transfer</div>';
        content.html(h);

        // Use completed count from call screen data
        content.find('.cs-stat.done .cs-stat-val').text(data.completed_today || 0);
}

// Execute action + fetch screen data in a single round-trip
function _csExecAction(args, successMsg, onDone) {
    var t0 = performance.now();
    console.log('[CS] action start:', args.action, args);
    // Use raw fetch instead of frappe.xcall to bypass Frappe's request pipeline overhead
    fetch('/api/method/queue_management.qms_api.call_screen_action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Frappe-CSRF-Token': frappe.csrf_token,
            'X-QMS-Confirm-Live-Action': '1'
        },
        body: JSON.stringify(args)
    }).then(function(res) { return res.json(); }).then(function(data) {
        var r = data.message || data;
        var t1 = performance.now();
        _csActionInFlight = false;
        if (r.error) {
            frappe.show_alert({message: r.error, indicator: 'red'});
        } else if (successMsg) {
            frappe.show_alert({message: successMsg, indicator: 'green'});
        }
        // Render directly from response — no second API call
        if (r.screen_data) {
            _csRenderData(r.screen_data);
            // Suppress the next realtime-triggered re-render (it's redundant)
            window._csActionRenderedAt = Date.now();
        }
        var t2 = performance.now();
        console.log('[CS] action done:', args.action,
            '| http=' + (t1-t0).toFixed(0) + 'ms',
            '| render=' + (t2-t1).toFixed(0) + 'ms',
            '| total=' + (t2-t0).toFixed(0) + 'ms',
            r._timing ? ('| server: action=' + r._timing.action_ms + 'ms data=' + r._timing.data_ms + 'ms total=' + r._timing.total_ms + 'ms') : '');
        if (onDone) onDone(r);
    }).catch(function(e) {
        _csActionInFlight = false;
        console.log('[CS] action error:', args.action, (performance.now()-t0).toFixed(0) + 'ms', e);
        frappe.show_alert({message: e.message || 'Error', indicator: 'red'});
    });
}

// ── Themed in-page dialogs ──
function _csShowDialog(html) {
    $('.cs-dialog-overlay').remove();
    // Read current theme from .cs-wrap so overlay gets the right data-theme
    var theme = $('.cs-wrap').attr('data-theme') || 'dark';
    var $overlay = $('<div class="cs-dialog-overlay" data-theme="' + theme + '"></div>');
    $overlay.html('<div class="cs-dialog">' + html + '</div>');
    // Append to body for proper fixed positioning; theme vars are on .cs-dialog-overlay itself
    $('body').append($overlay);
    $overlay.on('click', function(e) {
        if ($(e.target).hasClass('cs-dialog-overlay')) $overlay.remove();
    });
    var escHandler = function(e) {
        if (e.key === 'Escape') { $overlay.remove(); $(document).off('keydown', escHandler); }
    };
    $(document).on('keydown', escHandler);
    setTimeout(function() {
        $overlay.find('button, input, select, textarea').first().focus();
    }, 50);
    return $overlay;
}

function _csConfirm(msg, onYes, yesLabel, noLabel, onNo) {
    var h = '<h3>Confirm</h3>';
    h += '<div class="cs-confirm-msg">' + msg + '</div>';
    h += '<div class="cs-dialog-actions">';
    h += '<button class="cs-dialog-btn cancel" id="cs-dlg-no">' + (noLabel || 'Cancel') + '</button>';
    h += '<button class="cs-dialog-btn primary" id="cs-dlg-yes">' + (yesLabel || 'Yes') + '</button>';
    h += '</div>';
    var $d = _csShowDialog(h);
    $d.find('#cs-dlg-no').on('click', function() { $d.remove(); if (onNo) onNo(); });
    $d.find('#cs-dlg-yes').on('click', function() { $d.remove(); if (onYes) onYes(); });
    return $d;
}

function _csPrompt(title, label, onSubmit, onCancel) {
    var h = '<h3>' + _esc(title) + '</h3>';
    h += '<div class="cs-dialog-field"><label>' + _esc(label) + '</label>';
    h += '<input type="text" class="cs-prompt-input" id="cs-prompt-val"></div>';
    h += '<div class="cs-dialog-actions">';
    h += '<button class="cs-dialog-btn cancel" id="cs-dlg-no">Cancel</button>';
    h += '<button class="cs-dialog-btn primary" id="cs-dlg-yes">OK</button>';
    h += '</div>';
    var $d = _csShowDialog(h);
    $d.find('#cs-dlg-no').on('click', function() { $d.remove(); if (onCancel) onCancel(); });
    $d.find('#cs-dlg-yes').on('click', function() {
        var val = $d.find('#cs-prompt-val').val();
        $d.remove();
        onSubmit(val);
    });
    $d.find('#cs-prompt-val').on('keydown', function(e) {
        if (e.key === 'Enter') { $d.find('#cs-dlg-yes').click(); }
    });
}

var _csActionInFlight = false;

window.csAction = function(action, counter, ticket) {
    // Prevent concurrent actions (double-click, key repeat, etc.)
    if (_csActionInFlight) return;
    _csActionInFlight = true;

    function _cancelLock() { _csActionInFlight = false; }

    // Confirmation when calling a ticket from the waiting list while already serving
    if (action === 'call') {
        var servingCount = (window._csServingTickets || []).length;
        if (servingCount > 0) {
            _csConfirm(
                'You are already serving <b>' + servingCount + '</b> ticket(s).<br><br>' +
                'Call ticket <b>' + _esc(ticket) + '</b> as an additional ticket at your counter?',
                function() {
                    _doAction(action, counter, ticket);
                }, 'Call Ticket', 'Cancel', _cancelLock
            );
            return;
        }
    }

    // Confirmation when calling next while already serving
    if (action === 'next') {
        var servingNow = (window._csServingTickets || []).length;
        if (servingNow > 0) {
            _csConfirm(
                'You are already serving <b>' + servingNow + '</b> ticket(s).<br><br>' +
                'Call the next ticket as an additional ticket at your counter?',
                function() {
                    _doAction(action, counter, ticket);
                }, 'Call Next', 'Cancel', _cancelLock
            );
            return;
        }
    }

    _doAction(action, counter, ticket);
};

function _doAction(action, counter, ticket) {

    function _unlockAction() { _csActionInFlight = false; }

    if (action === 'transfer') {
        // Fetch counters and locations in parallel
        var pCounters = frappe.xcall('frappe.client.get_list', {
            doctype: 'QMS Counter', filters: {is_active: 1},
            fields: ['name', 'counter_name', 'counter_number', 'status', 'location'],
            limit_page_length: 50
        });
        var pLocations = frappe.xcall('frappe.client.get_list', {
            doctype: 'QMS Location', filters: {is_active: 1},
            fields: ['name', 'location_name', 'location_type'],
            limit_page_length: 50
        });

        Promise.all([pCounters, pLocations]).then(function(results) {
            var counters = results[0] || [];
            var locations = results[1] || [];

            var counterMap = {};
            var counterOptionsHtml = '<option value="">-- Select --</option>';
            counters.forEach(function(c) {
                if (c.name === counter) return;
                var label = _esc(c.counter_name + ' (#' + c.counter_number + ') - ' + (c.status || 'Unknown'));
                counterOptionsHtml += '<option value="' + _esc(c.name) + '">' + label + '</option>';
                counterMap[c.name] = label;
            });

            var locationMap = {};
            var locationOptionsHtml = '<option value="">-- Select --</option>';
            locations.forEach(function(l) {
                locationOptionsHtml += '<option value="' + _esc(l.name) + '">' + _esc(l.location_name) + '</option>';
                locationMap[l.name] = l.location_name;
            });

            var h = '<h3>Transfer Ticket</h3>';
            h += '<div class="cs-dialog-field"><label>Transfer to Counter</label>';
            h += '<select id="cs-xfer-counter">' + counterOptionsHtml + '</select></div>';
            h += '<div class="cs-dialog-field cs-xfer-divider"><span>Or transfer to Location</span></div>';
            h += '<div class="cs-dialog-field"><label>-- Select --</label>';
            h += '<select id="cs-xfer-location">' + locationOptionsHtml + '</select></div>';
            h += '<div class="cs-dialog-field"><label>Reason for transfer</label>';
            h += '<textarea id="cs-xfer-reason" rows="2" placeholder="Reason (optional)"></textarea></div>';
            h += '<div class="cs-dialog-actions">';
            h += '<button class="cs-dialog-btn cancel" id="cs-dlg-no">Cancel</button>';
            h += '<button class="cs-dialog-btn primary" id="cs-dlg-yes">Transfer</button>';
            h += '</div>';

            var $d = _csShowDialog(h);

            $d.find('#cs-xfer-counter').on('change', function() {
                if ($(this).val()) $d.find('#cs-xfer-location').val('');
            });
            $d.find('#cs-xfer-location').on('change', function() {
                if ($(this).val()) $d.find('#cs-xfer-counter').val('');
            });

            $d.find('#cs-dlg-no').on('click', function() { $d.remove(); _unlockAction(); });
            $d.find('#cs-dlg-yes').on('click', function() {
                var toCounter = $d.find('#cs-xfer-counter').val();
                var toLocation = $d.find('#cs-xfer-location').val();
                var reason = $d.find('#cs-xfer-reason').val() || '';

                if (!toCounter && !toLocation) {
                    frappe.msgprint('Please select a counter or location');
                    return;
                }

                var destLabel = '';
                if (toCounter) {
                    destLabel = counterMap[toCounter] || toCounter;
                } else {
                    destLabel = (locationMap[toLocation] || toLocation) + ' (Location)';
                }

                $d.remove();
                var tktNum = ticket;
                (window._csServingTickets || []).forEach(function(st) {
                    if (st.name === ticket) tktNum = st.ticket_number || ticket;
                });
                _csExecAction({
                    action: 'transfer', counter: counter, ticket: ticket,
                    reason: reason, to_counter: toCounter || '', to_location: toLocation || ''
                }, null, function() {
                    frappe.msgprint({
                        title: 'Ticket Transferred',
                        message: '<b>' + _esc(tktNum) + '</b> has been transferred to <b>' + _esc(destLabel) + '</b>.',
                        indicator: 'purple'
                    });
                });
            });

        }).catch(function(err) {
            _unlockAction();
            frappe.msgprint('Error loading transfer options: ' + (err.message || err));
        });
        return;
    }

    if (action === 'complete') {
        var servingTicket = null;
        (window._csServingTickets || []).forEach(function(st) {
            if (st.name === ticket) servingTicket = st;
        });
        var fromCounter = servingTicket && servingTicket.transferred_from_counter;
        if (fromCounter) {
            var counterName = (servingTicket && servingTicket.transferred_from_counter_name) || fromCounter;
            _csConfirm(
                'This ticket was transferred from <b>' + counterName + '</b>.<br><br>Send it back to the front of their queue?',
                function() {
                    _csExecAction({action: 'return', counter: counter, ticket: ticket},
                        'Ticket sent back to ' + counterName);
                },
                'Send Back', 'Just Complete',
                function() {
                    _csExecAction({action: 'complete', counter: counter, ticket: ticket},
                        'Ticket completed');
                }
            );
        } else {
            _csExecAction({action: 'complete', counter: counter, ticket: ticket},
                'Ticket completed');
        }
        return;
    }

    if (action === 'hold') {
        _csPrompt('Hold Ticket', 'Hold Reason (optional)', function(reason) {
            _csExecAction({action: 'hold', counter: counter, ticket: ticket, reason: reason || ''},
                'Ticket put on hold');
        }, _unlockAction);
        return;
    }

    if (action === 'noshow') {
        _csConfirm('Mark this ticket as No Show?<br><br><span style="font-size:13px;color:var(--cs-text-muted)">The ticket will be moved to the end of the queue so the patient can come back.</span>', function() {
            _csExecAction({action: 'noshow', counter: counter, ticket: ticket},
                'Marked as No Show \u2014 ticket requeued');
        }, 'Mark No Show', 'Cancel', _unlockAction);
        return;
    }

    // Generic actions: next, call, recall, serve
    var actionForApi = (action === 'recall') ? 'call' : action;
    var msgs = {next: 'Next ticket called', call: 'Ticket called', recall: 'Ticket recalled', serve: 'Service started'};
    _csExecAction({action: actionForApi, counter: counter, ticket: ticket || ''},
        null, function(r) {
            if (action === 'next' && r.action_result === null) {
                frappe.show_alert({message: 'No tickets waiting', indicator: 'orange'});
            } else if (!r.error) {
                frappe.show_alert({message: msgs[action] || 'Done', indicator: 'green'});
            }
        });
}
