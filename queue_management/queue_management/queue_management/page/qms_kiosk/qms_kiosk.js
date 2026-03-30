frappe.pages['qms-kiosk'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'QMS Kiosk',
        single_column: true
    });

    // Hide navbar in kiosk mode
    var isKioskMode = frappe.utils.get_url_arg('kiosk') === '1';
    if (isKioskMode) {
        $('header.navbar, .page-head').hide();
        $('body').css('padding-top', 0);
    }

    var _kioskLocation = frappe.utils.get_url_arg('location') || '';
    var _resetTimer = null;
    var _locationFromUrl = !!_kioskLocation;
    var _isProcessing = false; // double-tap prevention
    var _qmsHospitalName = 'Queue Management';
    var _multipleLocations = false; // track if more than one location exists

    // Load hospital name from settings
    frappe.xcall('queue_management.qms_api.get_hospital_name').then(function(name) {
        _qmsHospitalName = name;
    });

    // SVG icons (no emojis — cleaner for hospital setting)
    var ICONS = {
        hospital: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><path d="M9 9h1"/><path d="M9 13h1"/><path d="M9 17h1"/></svg>',
        ticket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5v2"/><path d="M15 11v2"/><path d="M15 17v2"/><path d="M5 5h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7a2 2 0 0 1 2-2z"/></svg>',
        search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
        check: '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    };

    // Default service icons
    var SVC_ICONS = {
        'Laboratory': '&#129514;',
        'Blood Test': '&#129656;',
        'Urine Test': '&#129514;',
        'Reception': '&#128203;',
        'Insurance': '&#128179;',
        'Pharmacy': '&#128138;',
        'Radiology': '&#128248;',
        'Consultation': '&#129658;',
    };

    // ── Ticket state persistence (survives page refresh) ──
    var TICKET_STORAGE_KEY = 'qms_active_ticket_desk';
    function saveTicketState(data) {
        try { sessionStorage.setItem(TICKET_STORAGE_KEY, JSON.stringify(data)); } catch(e) {}
    }
    function loadTicketState() {
        try { var raw = sessionStorage.getItem(TICKET_STORAGE_KEY); return raw ? JSON.parse(raw) : null; } catch(e) { return null; }
    }
    function clearTicketState() {
        try { sessionStorage.removeItem(TICKET_STORAGE_KEY); } catch(e) {}
    }

    var _kioskTheme = localStorage.getItem('qms_kiosk_theme') || 'light';
    page.main.html('<div class="k-wrap" data-theme="' + _kioskTheme + '">' +
        '<div class="k-offline-bar" id="k-offline-bar" style="display:none">&#9888; You are offline. Please check your connection.</div>' +
        '<button class="k-theme-toggle" id="k-theme-toggle" title="Toggle night/light mode">' +
        (_kioskTheme === 'dark' ? '&#9728;' : '&#9790;') + '</button>' +
        '<div class="k-inner" id="kiosk-root"></div></div>');

    // Offline detection
    function _updateOnlineStatus() {
        $('#k-offline-bar').toggle(!navigator.onLine);
    }
    window.addEventListener('online', _updateOnlineStatus);
    window.addEventListener('offline', _updateOnlineStatus);
    _updateOnlineStatus();

    page.main.on('click', '#k-theme-toggle', function() {
        var wrap = page.main.find('.k-wrap');
        var cur = wrap.attr('data-theme');
        var nxt = cur === 'dark' ? 'light' : 'dark';
        wrap.attr('data-theme', nxt);
        $(this).html(nxt === 'dark' ? '&#9728;' : '&#9790;');
        localStorage.setItem('qms_kiosk_theme', nxt);
    });

    function esc(v) { return String(v||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;'); }

    // Audio announcement of ticket number
    function announceTicketNumber(ticketNumber) {
        try {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                var num = ticketNumber.replace(/[^0-9]/g, ' ').trim().split('').join(' ');
                var text = 'Your ticket number is ' + num + '. Please have a seat and wait.';
                var utter = new SpeechSynthesisUtterance(text);
                utter.lang = 'en-US';
                utter.rate = 0.75;
                utter.pitch = 1;
                utter.volume = 1;
                window.speechSynthesis.speak(utter);
            }
        } catch(e) { /* audio not available */ }
    }

    function normalizeFieldKey(value) {
        return String(value || '')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '');
    }

    function inferBuiltinField(field) {
        var key = normalizeFieldKey(field.field_name || field.field_label);
        var type = String(field.field_type || '').toLowerCase();
        if (type === 'email' || key.indexOf('email') !== -1) return 'email';
        if (type === 'phone' || /(phone|mobile|contact|telephone)/.test(key)) return 'phone';
        if (/(^name$|full_name|patient_name)/.test(key)) return 'name';
        return '';
    }

    function renderPatientField(field, builtinKind) {
        var label = esc(field.field_label || 'Field');
        var key = normalizeFieldKey(field.field_name || field.field_label);
        var required = !!field.is_required;
        var requiredMark = required ? ' <span style="color:#c62828">*</span>' : '';
        var attrs = builtinKind
            ? ' data-builtin="' + builtinKind + '"'
            : ' data-field-name="' + esc(key) + '"';
        attrs += required ? ' data-required="1"' : '';
        var html = '<div class="k-info-field"><label>' + label + requiredMark + '</label>';
        if ((field.field_type || 'Text') === 'Textarea') {
            html += '<textarea class="k-dynamic-field"' + attrs + ' placeholder="Enter ' + label + '"></textarea>';
        } else if (field.field_type === 'Select') {
            html += '<select class="k-dynamic-field"' + attrs + '>';
            html += '<option value="">Select ' + label + '</option>';
            String(field.options || '').split(/\n+/).forEach(function(option) {
                option = option.trim();
                if (!option) return;
                html += '<option value="' + esc(option) + '">' + esc(option) + '</option>';
            });
            html += '</select>';
        } else {
            var inputType = 'text';
            if (field.field_type === 'Date') inputType = 'date';
            else if (field.field_type === 'Number') inputType = 'number';
            else if (field.field_type === 'Email') inputType = 'email';
            else if (field.field_type === 'Phone') inputType = 'tel';
            html += '<input class="k-dynamic-field" type="' + inputType + '"' + attrs + ' placeholder="Enter ' + label + '">';
        }
        html += '</div>';
        return html;
    }

    function renderPatientFields(form) {
        var fields = (form && form.fields) || [];
        var html = '';
        var seenBuiltins = { name: false, phone: false, email: false };
        fields.forEach(function(field) {
            var builtinKind = inferBuiltinField(field);
            if (builtinKind) seenBuiltins[builtinKind] = true;
            html += renderPatientField(field, builtinKind);
        });
        if (!fields.length) {
            html += renderPatientField({ field_label: 'Full Name', field_name: 'patient_name', field_type: 'Text' }, 'name');
            html += renderPatientField({ field_label: 'Phone Number', field_name: 'patient_phone', field_type: 'Phone' }, 'phone');
            html += renderPatientField({ field_label: 'Email', field_name: 'patient_email', field_type: 'Email' }, 'email');
            return html;
        }
        if (!seenBuiltins.name) html += renderPatientField({ field_label: 'Full Name', field_name: 'patient_name', field_type: 'Text' }, 'name');
        if (!seenBuiltins.phone) html += renderPatientField({ field_label: 'Phone Number', field_name: 'patient_phone', field_type: 'Phone' }, 'phone');
        if (!seenBuiltins.email) html += renderPatientField({ field_label: 'Email', field_name: 'patient_email', field_type: 'Email' }, 'email');
        return html;
    }

    function collectPatientFormValues() {
        var patientName = '';
        var patientPhone = '';
        var patientEmail = '';
        var patientFormData = {};
        var hasError = false;
        $('#kiosk-root').find('.k-dynamic-field').each(function() {
            var $field = $(this);
            var value = String($field.val() || '').trim();
            var isRequired = $field.attr('data-required') === '1';
            var label = $field.closest('.k-info-field').find('label').text().replace('*', '').trim();
            if (isRequired && !value && !hasError) {
                hasError = true;
                frappe.show_alert({message: label + ' is required', indicator: 'orange'});
                $field.focus();
                return false;
            }
            var builtinKind = $field.attr('data-builtin');
            if (builtinKind === 'name') patientName = value;
            else if (builtinKind === 'phone') patientPhone = value;
            else if (builtinKind === 'email') patientEmail = value;
            else if (value) patientFormData[$field.attr('data-field-name')] = value;
        });
        if (hasError) return null;
        return {
            patientName: patientName,
            patientPhone: patientPhone,
            patientEmail: patientEmail,
            patientFormData: Object.keys(patientFormData).length ? JSON.stringify(patientFormData) : '',
        };
    }

    // ── LOCATION PICKER ──
    function showLocationPicker() {
        clearAutoReset();
        _isProcessing = false;
        frappe.xcall('queue_management.qms_kiosk_api.get_locations').then(function(locs) {
            _multipleLocations = locs.length > 1;
            if (locs.length === 1) {
                _kioskLocation = locs[0].name;
                showWelcome();
                return;
            }
            var h = '<div style="text-align:center">';
            h += '<div class="k-logo">' + ICONS.hospital + '</div>';
            h += '<h2 class="k-title">' + (_qmsHospitalName || 'Queue Management') + '</h2>';
            h += '<p class="k-subtitle">Select your location</p>';
            h += '<div class="k-loc-grid">';
            locs.forEach(function(l) {
                h += '<div class="k-loc-card" data-loc="' + esc(l.name) + '">';
                h += '<div class="k-loc-card-name">' + esc(l.location_name) + '</div>';
                h += '<div class="k-loc-card-type">' + esc(l.location_type || '') + '</div>';
                h += '</div>';
            });
            if (!locs.length) {
                h += '<div class="k-no-services">No locations available</div>';
            }
            h += '</div></div>';
            $('#kiosk-root').html(h);

            $('#kiosk-root').find('.k-loc-card').on('click', function() {
                _kioskLocation = $(this).attr('data-loc');
                showWelcome();
            });
        }).catch(function() {
            $('#kiosk-root').html('<div style="text-align:center;padding:40px"><p>Unable to load locations. Please try again.</p><button class="k-btn k-btn-primary" onclick="location.reload()">Retry</button></div>');
        });
    }

    // ── WELCOME SCREEN ──
    function showWelcome() {
        clearAutoReset();
        _isProcessing = false;
        frappe.xcall('queue_management.qms_kiosk_api.get_kiosk_info', {location: _kioskLocation}).then(function(info) {
            var loc = info.location;
            var h = '<div class="k-welcome">';
            h += '<div class="k-logo">' + ICONS.hospital + '</div>';
            h += '<h1 class="k-title">' + esc(loc.location_name) + '</h1>';
            h += '<p class="k-subtitle">' + esc(loc.location_type || 'Welcome') + '</p>';

            // One big primary action
            h += '<div class="k-main-actions">';
            h += '<div class="k-main-btn primary" id="k-take-ticket">';
            h += '<span class="k-main-btn-text">Get Your Number</span>';
            h += '<span class="k-main-btn-sub">Tap here to join the queue</span>';
            h += '</div>';
            h += '</div>';

            if (!_locationFromUrl && _multipleLocations) {
                h += '<div class="k-change-loc">';
                h += '<a href="#" id="k-change-loc">' + ICONS.back + ' Change Location</a>';
                h += '</div>';
            }
            h += '</div>';

            $('#kiosk-root').html(h);

            $('#k-take-ticket').on('click', function() { showServices(); });
            if (!_locationFromUrl && _multipleLocations) {
                $('#k-change-loc').on('click', function(e) { e.preventDefault(); _kioskLocation = ''; showLocationPicker(); });
            }
        }).catch(function() {
            $('#kiosk-root').html('<div style="text-align:center;padding:40px"><p>Unable to load kiosk. Please try again.</p><button class="k-btn k-btn-primary" onclick="location.reload()">Retry</button></div>');
        });
    }

    // ── SERVICE SELECTION ──
    function showServices() {
        _isProcessing = false;
        startAutoReset();
        frappe.xcall('queue_management.qms_kiosk_api.get_services', {location: _kioskLocation}).then(function(services) {
            var h = '<div class="k-header">';
            h += '<div class="k-back" id="k-back-welcome">' + ICONS.back + ' Back</div>';
            h += '<div class="k-header-text"><h2>Select Your Service</h2><p>Tap the service you need</p></div>';
            h += '<div style="width:140px"></div>';
            h += '</div>';

            h += '<div class="k-services">';
            if (!services.length) {
                h += '<div class="k-no-services">No services available at this time</div>';
            }
            services.forEach(function(s) {
                var icon = SVC_ICONS[s.service_name] || '&#127915;';
                var color = s.color || '#1976D2';
                h += '<div class="k-svc-card" data-svc="' + esc(s.name) + '">';
                h += '<div class="k-svc-accent" style="background:' + color + '"></div>';
                h += '<div class="k-svc-icon">' + icon + '</div>';
                h += '<div class="k-svc-name">' + esc(s.service_name) + '</div>';
                h += '<div class="k-svc-info">';
                h += '<div class="k-svc-info-item"><span class="num">' + s.waiting_count + '</span> waiting</div>';
                var waitDisplay = s.avg_wait_mins ? ('~' + s.avg_wait_mins + ' min') : (s.estimated_wait ? '~' + s.estimated_wait + ' min' : '--');
                h += '<div class="k-svc-info-item"><span class="num">' + waitDisplay + '</span> avg wait</div>';
                h += '</div>';
                h += '</div>';
            });
            h += '</div>';

            $('#kiosk-root').html(h);

            $('#k-back-welcome').on('click', function() { showWelcome(); });
            $('#kiosk-root').find('.k-svc-card').on('click', function() {
                // Double-tap prevention
                if (_isProcessing) return;
                _isProcessing = true;
                var $card = $(this);
                $card.addClass('loading');
                var svc = $card.attr('data-svc');
                // Show optional patient info step
                showPatientInfo(svc);
            });
        }).catch(function() {
            frappe.show_alert({message: 'Unable to load services', indicator: 'red'});
            showWelcome();
        });
    }

    // ── OPTIONAL PATIENT INFO ──
    // Collects name, phone, email — all optional, user can skip
    function showPatientInfo(service) {
        _isProcessing = false;
        startAutoReset();
        $('#kiosk-root').html('<div class="k-loading"><div class="k-spinner"></div><div class="k-loading-text">Loading form...</div></div>');
        frappe.xcall('queue_management.qms_kiosk_api.get_patient_form', {location: _kioskLocation, service: service}).then(function(form) {
            var h = '<div class="k-header">';
            h += '<div class="k-back" id="k-back-services">' + ICONS.back + ' Back</div>';
            h += '<div class="k-header-text"><h2>' + esc((form && form.form_name) || 'Your Details') + '</h2><p>Optional — you can skip this step</p></div>';
            h += '<div style="width:140px"></div>';
            h += '</div>';

            h += '<div class="k-info-step">';
            h += '<div class="k-info-fields">' + renderPatientFields(form) + '</div>';
            h += '<div class="k-info-btns">';
            h += '<button class="k-btn k-btn-ghost" id="k-skip-info">Skip</button>';
            h += '<button class="k-btn k-btn-primary" id="k-submit-info">Get My Ticket</button>';
            h += '</div>';
            h += '</div>';

            $('#kiosk-root').html(h);

            $('#k-back-services').on('click', function() { showServices(); });
            $('#k-skip-info').on('click', function() {
                if (_isProcessing) return;
                _isProcessing = true;
                issueTicket(service, '', '', '', '');
            });
            $('#k-submit-info').on('click', function() {
                if (_isProcessing) return;
                var formValues = collectPatientFormValues();
                if (!formValues) return;
                _isProcessing = true;
                issueTicket(service, formValues.patientName, formValues.patientPhone, formValues.patientEmail, formValues.patientFormData);
            });
        }).catch(function() {
            showServices();
        });
    }

    // ── ISSUE TICKET ──
    function issueTicket(service, patientName, patientPhone, patientEmail, patientFormData) {
        $('#kiosk-root').html(
            '<div class="k-loading"><div class="k-spinner"></div><div class="k-loading-text">Getting your ticket...</div></div>'
        );
        var args = {service: service, location: _kioskLocation};
        if (patientName) args.patient_name = patientName;
        if (patientPhone) args.patient_phone = patientPhone;
        if (patientEmail) args.patient_email = patientEmail;
        if (patientFormData) args.patient_form_data = patientFormData;

        frappe.xcall('queue_management.qms_kiosk_api.submit_ticket', args).then(function(r) {
            _isProcessing = false;
            showResult(r);
        }).catch(function(e) {
            _isProcessing = false;
            frappe.show_alert({message: e.message || 'Error issuing ticket', indicator: 'red'});
            showServices();
        });
    }

    // ── TICKET RESULT (live-updating) ──
    var _pollTimer = null;
    var _realtimeBound = false;
    var _onQmsEvent = function() {};
    var _onNoShowEvent = function() {};
    var _onTransferEvent = function() {};
    var _countdownTimer = null;

    var STATUS_CFG = {
        'Waiting':   { icon: '\u23F3', label: 'Waiting',  badge: 'fs-waiting', row: '' },
        'Called':    { icon: '\uD83D\uDCE2', label: 'Called',   badge: 'fs-called',  row: 'row-active' },
        'Serving':   { icon: '\u2705', label: 'Serving',  badge: 'fs-serving', row: 'row-active' },
        'Completed': { icon: '\u2705', label: 'Done',     badge: 'fs-done',    row: 'row-served' },
        'No Show':   { icon: '\u274C', label: 'No Show',  badge: 'fs-noshow',  row: 'row-served' },
        'Cancelled': { icon: '\u274C', label: 'Cancelled',badge: 'fs-noshow',  row: 'row-served' },
        'On Hold':   { icon: '\u23F8', label: 'On Hold',  badge: 'fs-hold',    row: '' },
    };

    function clearPoll() {
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
        if (_realtimeBound && window.frappe && frappe.realtime) {
            frappe.realtime.off('qms_ticket_called', _onQmsEvent);
            frappe.realtime.off('qms_ticket_completed', _onQmsEvent);
            frappe.realtime.off('qms_ticket_cancelled', _onQmsEvent);
            frappe.realtime.off('qms_ticket_no_show', _onNoShowEvent);
            frappe.realtime.off('qms_new_ticket', _onQmsEvent);
            frappe.realtime.off('qms_ticket_held', _onQmsEvent);
            frappe.realtime.off('qms_ticket_requeued', _onQmsEvent);
            frappe.realtime.off('qms_ticket_transferred', _onTransferEvent);
            frappe.realtime.off('qms_ticket_serving', _onQmsEvent);
            _realtimeBound = false;
        }
    }

    function showResult(r) {
        clearAutoReset();
        clearPoll();
        var ticketId = r.ticket;
        var ticketNum = r.ticket_number;
        var serviceName = r.service;
        var _serviceId = r.service_id || '';
        var _servingCounters = r.serving_counters || [];
        var _lastStatus = r.status || 'Waiting';
        var _refreshing = false;
        var _countdownSecs = (r.estimated_wait || 0) * 60;
        var _lastServerWait = (r.estimated_wait || 0);
        var _isRestoredState = !!r.restored;

        saveTicketState({
            ticket: ticketId, ticket_number: ticketNum, service: serviceName,
            service_id: _serviceId, serving_counters: _servingCounters,
            queue_position: r.queue_position, estimated_wait: r.estimated_wait,
            location: _kioskLocation, status: _lastStatus,
            counter_name: r.counter_name || '', counter_number: r.counter_number || ''
        });

        function fmtCountdown(secs) {
            if (secs <= 0) return 'Any moment now!';
            var m = Math.floor(secs / 60);
            var s = secs % 60;
            return m + ':' + (s < 10 ? '0' : '') + s;
        }

        function startCountdown() {
            if (_countdownTimer) clearInterval(_countdownTimer);
            _countdownTimer = setInterval(function() {
                if (_countdownSecs > 0) _countdownSecs--;
                var el = $('#k-countdown-val');
                if (el.length) {
                    el.text(fmtCountdown(_countdownSecs));
                    if (_countdownSecs <= 120) el.addClass('k-pulse');
                    else el.removeClass('k-pulse');
                }
            }, 1000);
        }

        function refreshStatus() {
            if (_refreshing) return;
            _refreshing = true;
            frappe.xcall('queue_management.qms_kiosk_api.check_ticket_status', {ticket: ticketId}).then(function(s) {
                _refreshing = false;
                if (s.status === 'Waiting') {
                    var newWait = (s.estimated_wait || 0);
                    var newPos = s.queue_position || 1;
                    if (newWait !== _lastServerWait) {
                        _countdownSecs = newWait * 60;
                        _lastServerWait = newWait;
                    }
                    var posEl = $('#k-live-pos');
                    if (posEl.length) {
                        posEl.text('#' + newPos);
                    } else {
                        renderWaiting(newPos, newWait);
                    }
                } else if (s.status === 'Called' || s.status === 'Serving') {
                    if (_lastStatus === 'Waiting') {
                        renderCalled(s.counter_name, s.counter_number);
                    }
                } else if (s.status === 'Completed') {
                    clearTicketState();
                    renderCompleted();
                } else if (s.status === 'Cancelled' || s.status === 'No Show') {
                    clearTicketState();
                    clearPoll();
                    if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
                    showWelcome();
                }
                _lastStatus = s.status;
            }).catch(function() { _refreshing = false; });
        }

        function renderWaiting(pos, estWait) {
            var ahead = Math.max(0, (pos || 1) - 1);
            _countdownSecs = (estWait || 0) * 60;

            var h = '<div class="k-waiting-compact">';

            // Top row: ticket + service
            h += '<div class="k-waiting-header">';
            h += '<div class="k-waiting-label">Your Number</div>';
            h += '<div class="k-waiting-ticket">' + esc(ticketNum) + '</div>';
            h += '<div class="k-waiting-service">' + esc(serviceName) + '</div>';
            h += '</div>';

            // Counters row
            if (_servingCounters.length) {
                h += '<div class="k-waiting-counters">';
                h += '<span class="k-waiting-counters-label">\uD83C\uDFE5 Serving at</span>';
                _servingCounters.forEach(function(c) {
                    h += '<span class="k-counter-chip">' + esc(c.counter_name || ('Counter ' + c.counter_number)) + '</span>';
                });
                h += '</div>';
            }

            // Info strip: estimated wait + position
            h += '<div class="k-waiting-info-strip">';
            h += '<div class="k-info-cell">';
            h += '<div class="k-info-val" id="k-countdown-val">' + fmtCountdown(_countdownSecs) + '</div>';
            h += '<div class="k-info-label">\u23F1\uFE0F Est. Wait</div>';
            h += '</div>';
            h += '<div class="k-info-divider"></div>';
            h += '<div class="k-info-cell">';
            h += '<div class="k-info-val" id="k-live-pos">#' + (pos || 1) + '</div>';
            h += '<div class="k-info-label">\uD83D\uDC65 <span id="k-ahead-count">' + ahead + '</span> ' + (ahead === 1 ? 'person' : 'people') + ' ahead</div>';
            h += '</div>';
            h += '</div>';

            // Live feed (compact)
            h += '<div class="k-feed-title">\uD83D\uDCCB Live Queue</div>';
            h += '<div class="k-feed" id="k-queue-feed"><div style="text-align:center;padding:12px;color:#6b7280">Loading...</div></div>';

            // Leave button
            h += '<div class="k-waiting-actions">';
            h += '<button class="k-btn k-btn-ghost" id="k-leave-waitlist" style="color:#c62828;border-color:#ef9a9a">\u274C Leave Waitlist</button>';
            h += '</div>';

            h += '</div>';

            $('#kiosk-root').html(h);
            $('#k-leave-waitlist').on('click', function() {
                if (_isProcessing) return;
                _isProcessing = true;
                clearPoll();
                if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
                clearTicketState();
                frappe.xcall('queue_management.qms_kiosk_api.leave_waitlist', {ticket: ticketId}).then(function() {
                    _isProcessing = false;
                    frappe.show_alert({message: 'Your ticket has been cancelled.', indicator: 'green'});
                    showWelcome();
                }).catch(function(e) {
                    _isProcessing = false;
                    frappe.show_alert({message: e.message || 'Could not cancel ticket', indicator: 'red'});
                });
            });
            refreshQueueList();
            startCountdown();
        }

        function renderCalled(counterName, counterNumber) {
            clearPoll();
            if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
            var cDisplay = counterName || ('Counter ' + (counterNumber || ''));
            var h = '<div class="k-result" style="animation: k-pop .5s ease">';
            h += '<div class="k-result-check" style="background:linear-gradient(135deg,#1565C0,#0D47A1);box-shadow:0 8px 32px rgba(21,101,192,.45)">';
            h += '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:56px;height:56px"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.362 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';
            h += '</div>';
            h += '<div class="k-result-label" style="font-size:36px;color:#1565C0;font-weight:900;margin-bottom:12px">You Have Been Called!</div>';
            h += '<div class="k-result-ticket">' + esc(ticketNum) + '</div>';
            h += '<div style="font-size:36px;font-weight:900;color:#004d40;margin:20px 0 8px">Please proceed to</div>';
            h += '<div style="font-size:64px;font-weight:900;color:#1565C0;letter-spacing:2px;margin-bottom:24px">' + esc(cDisplay) + '</div>';
            h += '<div class="k-result-msg" style="background:#e3f2fd;border-color:#90caf9;color:#0d47a1">';
            h += 'Please go to <strong>' + esc(cDisplay) + '</strong> now.';
            h += '</div>';
            h += '</div>';
            $('#kiosk-root').html(h);
            // Voice announcement
            try {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    var num = ticketNum.replace(/[^0-9]/g, ' ').trim().split('').join(' ');
                    var text = 'Ticket ' + num + '. Please proceed to ' + cDisplay + '.';
                    var utter = new SpeechSynthesisUtterance(text);
                    utter.lang = 'en-US';
                    utter.rate = 0.75; utter.volume = 1;
                    window.speechSynthesis.speak(utter);
                }
            } catch(e) {}
        }

        function renderCompleted() {
            clearPoll();
            clearTicketState();
            if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
            var h = '<div class="k-result">';
            h += '<div class="k-result-check">' + ICONS.check + '</div>';
            h += '<div class="k-result-label">Service Complete</div>';
            h += '<div class="k-result-ticket">' + esc(ticketNum) + '</div>';
            h += '<div class="k-result-msg">Thank you! Your service has been completed.</div>';
            h += '<div class="k-result-actions">';
            h += '<button class="k-btn k-btn-primary" id="k-open-feedback">Leave Feedback</button>';
            h += '<button class="k-btn k-btn-ghost" id="k-complete-home">Back to Home</button>';
            h += '</div>';
            h += '</div>';
            $('#kiosk-root').html(h);
            $('#k-open-feedback').on('click', function() { showFeedback(ticketId); });
            $('#k-complete-home').on('click', function() { showWelcome(); });
        }

        function refreshQueueList() {
            if (!_serviceId) return;
            frappe.xcall('queue_management.qms_kiosk_api.get_queue_list', {
                service: _serviceId, location: _kioskLocation
            }).then(function(tickets) {
                var feed = $('#k-queue-feed');
                if (!feed.length) return;
                if (!tickets || !tickets.length) {
                    feed.html('<div style="text-align:center;padding:20px;color:#6b7280">Queue is empty</div>');
                    return;
                }

                var served = 0;
                var myIndex = -1;
                tickets.forEach(function(t, i) {
                    if (t.status === 'Completed' || t.status === 'No Show' || t.status === 'Cancelled') served++;
                    if (t.ticket_number === ticketNum) myIndex = i;
                });

                // Update ahead count
                var aheadLabelEl = $('#k-ahead-count').closest('.k-info-label');
                if (aheadLabelEl.length && myIndex >= 0) {
                    var aheadOfMe = 0;
                    tickets.forEach(function(t, i) {
                        if (i < myIndex && t.status === 'Waiting') aheadOfMe++;
                    });
                    var word = aheadOfMe === 1 ? 'person' : 'people';
                    aheadLabelEl.html('\uD83D\uDC65 <span id="k-ahead-count">' + aheadOfMe + '</span> ' + word + ' ahead');
                }

                var rows = '';
                var activeTickets = tickets.filter(function(t) { return t.status !== 'Completed' && t.status !== 'No Show' && t.status !== 'Cancelled'; });
                var waitNum = 0;
                activeTickets.forEach(function(t) {
                    var cfg = STATUS_CFG[t.status] || STATUS_CFG['Waiting'];
                    var isYou = t.ticket_number === ticketNum;
                    var rowClass = isYou ? 'row-you' : cfg.row;
                    var posLabel;
                    if (t.status === 'Called' || t.status === 'Serving') {
                        posLabel = cfg.icon;
                    } else {
                        waitNum++;
                        posLabel = '#' + waitNum;
                    }
                    rows += '<div class="k-feed-row ' + rowClass + '">';
                    rows += '<div class="k-feed-pos">' + posLabel + '</div>';
                    rows += '<div class="k-feed-mid"><span class="k-feed-num">' + esc(t.ticket_number) + '</span>';
                    if (isYou) rows += '<span class="k-feed-you-tag">\u261D\uFE0F YOU</span>';
                    rows += '</div>';
                    rows += '<span class="k-feed-status ' + cfg.badge + '">' + cfg.icon + ' ' + cfg.label + '</span>';
                    rows += '</div>';
                });
                feed.html(rows);
                if (!feed.data('scrolled')) {
                    var youRow = feed.find('.row-you');
                    if (youRow.length) {
                        var scrollPos = youRow[0].offsetTop - feed[0].offsetTop - 80;
                        feed.animate({scrollTop: Math.max(0, scrollPos)}, 300);
                        feed.data('scrolled', true);
                    }
                }
            }).catch(function() {});
        }

        // Initial render - respect restored state
        if (_lastStatus === 'Called' || _lastStatus === 'Serving') {
            renderCalled(r.counter_name, r.counter_number);
        } else {
            renderWaiting(r.queue_position, r.estimated_wait);
        }
        if (!_isRestoredState && _lastStatus === 'Waiting') announceTicketNumber(ticketNum);

        function showNoShowNotice(data) {
            if (!data || data.ticket !== ticketId || !data.requeued || document.getElementById('k-noshow-notice')) return;
            var overlay = document.createElement('div');
            overlay.id = 'k-noshow-notice';
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(8,15,28,0.72);display:flex;align-items:center;justify-content:center;z-index:9999;padding:24px;';
            overlay.innerHTML = '<div style="background:#fff8e1;border:3px solid #fb8c00;border-radius:20px;padding:32px;max-width:540px;width:100%;text-align:center;box-shadow:0 16px 48px rgba(0,0,0,.24)">' +
                '<div style="font-size:48px;line-height:1;margin-bottom:16px">&#9888;&#65039;</div>' +
                '<div style="font-size:28px;font-weight:800;color:#e65100;margin-bottom:12px">Your ticket was requeued</div>' +
                '<div style="font-size:18px;line-height:1.55;color:#5d4037;margin-bottom:24px">Ticket <strong>' + esc(data.ticket_number || ticketNum) + '</strong> was marked as no-show and moved back into the queue. Please stay close to the counter so you do not miss the next call.</div>' +
                '<button id="k-noshow-ok" class="k-btn k-btn-primary" style="margin:0 auto">OK</button>' +
                '</div>';
            document.body.appendChild(overlay);
            $('#k-noshow-ok').on('click', function() {
                $('#k-noshow-notice').remove();
            });
        }

        function showTransferNotice(data) {
            if (!data || data.ticket !== ticketId || document.getElementById('k-transfer-notice')) return;
            var dest = data.to_counter_name || data.to_location_name || '';
            var msg = 'Your ticket <strong>' + esc(data.ticket_number || ticketNum) + '</strong> has been transferred';
            if (dest) msg += ' to <strong>' + esc(dest) + '</strong>';
            msg += '. You have been placed in the new queue. Please wait for your number to be called.';

            var overlay = document.createElement('div');
            overlay.id = 'k-transfer-notice';
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(8,15,28,0.72);display:flex;align-items:center;justify-content:center;z-index:9999;padding:24px;';
            overlay.innerHTML = '<div style="background:#e3f2fd;border:3px solid #1565C0;border-radius:20px;padding:32px;max-width:540px;width:100%;text-align:center;box-shadow:0 16px 48px rgba(0,0,0,.24)">' +
                '<div style="font-size:48px;line-height:1;margin-bottom:16px">&#128260;</div>' +
                '<div style="font-size:28px;font-weight:800;color:#1565C0;margin-bottom:12px">You Have Been Transferred</div>' +
                '<div style="font-size:18px;line-height:1.55;color:#37474f;margin-bottom:24px">' + msg + '</div>' +
                '<button id="k-transfer-ok" class="k-btn k-btn-primary" style="margin:0 auto">OK</button>' +
                '</div>';
            document.body.appendChild(overlay);
            $('#k-transfer-ok').on('click', function() {
                $('#k-transfer-notice').remove();
            });
            // Voice announcement
            try {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    var text = 'Your ticket has been transferred' + (dest ? ' to ' + dest : '') + '. Please wait to be called.';
                    var utter = new SpeechSynthesisUtterance(text);
                    utter.lang = 'en-US';
                    utter.rate = 0.8; utter.volume = 1;
                    window.speechSynthesis.speak(utter);
                }
            } catch(e) {}
        }

        // Listen for realtime events — debounced and location-filtered
        var _evtDebounce = null;
        _onQmsEvent = function(data) {
            // Skip events from different locations
            if (_kioskLocation && data && data.location && data.location !== _kioskLocation) return;
            if (_evtDebounce) clearTimeout(_evtDebounce);
            // Immediate refresh if the event is about THIS ticket
            var isMyTicket = data && (data.ticket === ticketId || data.ticket_number === ticketNum);
            _evtDebounce = setTimeout(function() {
                refreshStatus(); refreshQueueList();
            }, isMyTicket ? 50 : 300);
        };
        _onNoShowEvent = function(data) {
            showNoShowNotice(data);
            _onQmsEvent(data);
        };
        _onTransferEvent = function(data) {
            showTransferNotice(data);
            _onQmsEvent(data);
        };
        if (window.frappe && frappe.realtime) {
            frappe.realtime.on('qms_ticket_called', _onQmsEvent);
            frappe.realtime.on('qms_ticket_completed', _onQmsEvent);
            frappe.realtime.on('qms_ticket_cancelled', _onQmsEvent);
            frappe.realtime.on('qms_ticket_no_show', _onNoShowEvent);
            frappe.realtime.on('qms_new_ticket', _onQmsEvent);
            frappe.realtime.on('qms_ticket_held', _onQmsEvent);
            frappe.realtime.on('qms_ticket_requeued', _onQmsEvent);
            frappe.realtime.on('qms_ticket_transferred', _onTransferEvent);
            frappe.realtime.on('qms_ticket_serving', _onQmsEvent);
            _realtimeBound = true;
        }

        // Safety-net poll (realtime handles immediate updates)
        _pollTimer = setInterval(function() { refreshStatus(); refreshQueueList(); }, 15000);

        // Auto-reset to welcome if kiosk is abandoned on the result screen
        startAutoReset(300);
    }

    // ── FEEDBACK — Smiley Face Design ──
    function showFeedback(ticketId) {
        $('#kiosk-root').html(
            '<div class="k-loading"><div class="k-spinner"></div><div class="k-loading-text">Loading...</div></div>'
        );
        frappe.xcall('queue_management.qms_kiosk_api.get_feedback_form', {ticket: ticketId}).then(function(form) {
            if (form.already_submitted) {
                showFeedbackMsg('Thank you! You have already submitted feedback.');
                return;
            }
            if (form.no_form) {
                showFeedbackMsg('Feedback is not available for this service.');
                return;
            }
            renderFeedbackForm(ticketId, form);
        }).catch(function(e) {
            showFeedbackMsg(e.message || 'Unable to load feedback form.');
        });
    }

    function showFeedbackMsg(msg) {
        var h = '<div class="k-header">';
        h += '<div class="k-back" id="k-fb-back">' + ICONS.back + ' Back</div>';
        h += '<div class="k-header-text"><h2>Feedback</h2></div>';
        h += '<div style="width:140px"></div></div>';
        h += '<div class="k-info-step"><p style="font-size:26px;font-weight:600">' + esc(msg) + '</p>';
        h += '<button class="k-btn k-btn-primary" id="k-fb-home" style="margin-top:32px">Back to Home</button></div>';
        $('#kiosk-root').html(h);
        $('#k-fb-back, #k-fb-home').on('click', function() { showWelcome(); });
    }

    function renderFeedbackForm(ticketId, form) {
        var h = '<div class="k-header">';
        h += '<div class="k-back" id="k-fb-back">' + ICONS.back + ' Back</div>';
        h += '<div class="k-header-text"><h2>Your Feedback</h2></div>';
        h += '<div style="width:140px"></div></div>';

        h += '<div class="k-fb-wrap">';
        h += '<div class="k-fb-question">How was your experience?</div>';

        // 3 smiley faces
        h += '<div class="k-fb-faces">';
        h += '<div class="k-fb-face face-sad" data-rating="1">';
        h += '<span class="k-fb-face-emoji">&#128577;</span>';
        h += '<span class="k-fb-face-label">Poor</span>';
        h += '</div>';
        h += '<div class="k-fb-face face-ok" data-rating="3">';
        h += '<span class="k-fb-face-emoji">&#128528;</span>';
        h += '<span class="k-fb-face-label">Okay</span>';
        h += '</div>';
        h += '<div class="k-fb-face face-happy" data-rating="5">';
        h += '<span class="k-fb-face-emoji">&#128522;</span>';
        h += '<span class="k-fb-face-label">Great</span>';
        h += '</div>';
        h += '</div>';

        // Optional comment
        h += '<div class="k-fb-comment">';
        h += '<label>Any comments? (optional)</label>';
        h += '<textarea id="k-fb-comments" placeholder="Tell us more..."></textarea>';
        h += '</div>';

        h += '<div class="k-fb-actions">';
        h += '<button class="k-btn k-btn-ghost" id="k-fb-skip">Skip</button>';
        h += '<button class="k-btn k-btn-primary" id="k-fb-submit">Submit</button>';
        h += '</div>';

        h += '</div>';

        $('#kiosk-root').html(h);

        var selectedRating = 0;
        $('.k-fb-face').on('click', function() {
            selectedRating = parseInt($(this).data('rating'));
            $('.k-fb-face').removeClass('selected');
            $(this).addClass('selected');
        });

        $('#k-fb-back, #k-fb-skip').on('click', function() { showWelcome(); });
        $('#k-fb-submit').on('click', function() {
            if (!selectedRating) {
                frappe.show_alert({message: 'Please tap a face to rate your experience', indicator: 'orange'});
                return;
            }
            frappe.xcall('queue_management.qms_kiosk_api.submit_feedback', {
                ticket: ticketId,
                overall_rating: selectedRating,
                comments: $('#k-fb-comments').val() || '',
                response_data: JSON.stringify({}),
            }).then(function() {
                showFeedbackMsg('Thank you for your feedback!');
            }).catch(function(e) {
                frappe.show_alert({message: e.message || 'Error submitting feedback', indicator: 'red'});
            });
        });
    }

    function clearAutoReset() {
        if (_resetTimer) { clearInterval(_resetTimer); _resetTimer = null; }
    }

    function startAutoReset(seconds) {
        clearAutoReset();
        var sec = seconds || 120;
        _resetTimer = setTimeout(function() { showWelcome(); }, sec * 1000);
    }

    // ── START ──
    function startFresh() {
        clearTicketState();
        if (_kioskLocation) {
            showWelcome();
        } else {
            showLocationPicker();
        }
    }

    // If the user had an active ticket before refreshing, restore it
    var _savedTicket = loadTicketState();
    if (_savedTicket && _savedTicket.ticket) {
        if (!_kioskLocation && _savedTicket.location) _kioskLocation = _savedTicket.location;

        var _restoreDone = false;
        var _restoreTimer = setTimeout(function() {
            if (_restoreDone) return;
            _restoreDone = true;
            startFresh();
        }, 5000);

        frappe.xcall('queue_management.qms_kiosk_api.check_ticket_status', {ticket: _savedTicket.ticket}).then(function(s) {
            if (_restoreDone) return;
            _restoreDone = true;
            clearTimeout(_restoreTimer);
            var active = s && s.status && s.status !== 'Cancelled' && s.status !== 'No Show' && s.status !== 'Completed';
            if (active) {
                var serverWait = (s.estimated_wait != null) ? s.estimated_wait : (_savedTicket.estimated_wait || 0);
                showResult({
                    ticket: _savedTicket.ticket,
                    ticket_number: _savedTicket.ticket_number,
                    service: s.service || _savedTicket.service,
                    service_id: s.service_id || _savedTicket.service_id,
                    queue_position: s.queue_position || _savedTicket.queue_position || 1,
                    estimated_wait: serverWait,
                    serving_counters: s.serving_counters || _savedTicket.serving_counters || [],
                    restored: true,
                    status: s.status,
                    counter_name: s.counter_name || _savedTicket.counter_name || '',
                    counter_number: s.counter_number || _savedTicket.counter_number || ''
                });
            } else {
                startFresh();
            }
        }).catch(function() {
            if (_restoreDone) return;
            _restoreDone = true;
            clearTimeout(_restoreTimer);
            startFresh();
        });
    } else if (_kioskLocation) {
        showWelcome();
    } else {
        showLocationPicker();
    }

    // Cleanup on page change to prevent memory leaks
    page.wrapper.on('page-change', function() {
        clearAutoReset();
        clearPoll();
        if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
        window.removeEventListener('online', _updateOnlineStatus);
        window.removeEventListener('offline', _updateOnlineStatus);
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    });
};
