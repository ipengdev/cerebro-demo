frappe.pages['qms-display'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Queue Display Board',
		single_column: true
	});

	var _dispTheme = localStorage.getItem('qms_display_theme') || 'light';
	var _displayLanguage = localStorage.getItem('qms_display_language') || 'English';

	// Make display fullscreen — hide Frappe chrome
	$('header.navbar, .page-head').hide();
	$('body').css({'padding-top': 0, 'overflow': 'hidden', 'height': '100vh'});
	$(page.wrapper).css({'margin': 0, 'padding': 0, 'height': '100vh'});
	$(page.wrapper).find('.page-content, .layout-main-section-wrapper, .layout-main-section, .container-fluid').css({'margin': 0, 'padding': 0, 'max-width': '100%', 'height': '100%'});
	page.main.css({'margin': 0, 'padding': 0, 'height': '100%'});

	page.main.html('<div class="disp-wrap" data-theme="' + _dispTheme + '" id="display-board"></div>');

	function esc(v) { return String(v||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;'); }

	var _displayLocation = frappe.utils.get_url_arg('location') || '';
	var _displayCounter = frappe.utils.get_url_arg('counter') || '';
	var _displayInterval = null;
	var _displayIntervalMs = 0;
	var _mediaTimer = null;
	var _mediaState = null;
	var _lastCalledTicket = null;
	var _activeCallPopup = null;
	var _callPopupTimer = null;
	var _dispLiveBound = false;
	var _qmsHospitalName = 'Queue Management';
	var _defaultYoutubeVideo = {
		media_type: 'Embed',
		media_file: 'https://www.youtube-nocookie.com/embed/gC3X0c8nZfQ?autoplay=1&mute=1&controls=0&rel=0&loop=1&playlist=gC3X0c8nZfQ&modestbranding=1&playsinline=1&fs=1&iv_load_policy=3',
		display_duration: 45,
		sort_order: 9999,
		title: 'Queue Display Video'
	};

	// Load hospital name from settings
	frappe.xcall('queue_management.qms_api.get_hospital_name').then(function(name) {
		_qmsHospitalName = name;
	});
	var _templateConfig = {};

	function isArabicUI() {
		return _displayLanguage === 'Arabic';
	}

	function t(english, arabic) {
		return isArabicUI() ? (arabic || english) : english;
	}

	function getLanguageToggleLabel() {
		return isArabicUI() ? 'English' : '\u0639\u0631\u0628\u064A';
	}

	function rerenderCurrentView() {
		if (!_displayLocation) {
			showLocationPicker();
		} else if (_displayCounter || page.main.find('.disp-main-grid').length) {
			loadDisplay();
		} else {
			showCounterPicker();
		}
	}

	function clearDisplayTimers() {
		if (_displayInterval) { clearInterval(_displayInterval); _displayInterval = null; }
		if (_mediaTimer) { clearTimeout(_mediaTimer); _mediaTimer = null; }
		if (_callPopupTimer) { clearTimeout(_callPopupTimer); _callPopupTimer = null; }
		_displayIntervalMs = 0;
	}

	function _dispMatchesBoard(data) {
		if (!_dispMatchesLocation(data)) return false;
		if (!_displayCounter) return true;
		return !data || !data.counter || data.counter === _displayCounter;
	}

	function showCallPopup(data) {
		if (!_dispMatchesBoard(data)) return;
		_activeCallPopup = {
			ticket_number: data && data.ticket_number,
			counter_name: data && data.counter_name,
			counter_number: data && data.counter_number,
			service: data && data.service
		};
		if (_callPopupTimer) clearTimeout(_callPopupTimer);
		_callPopupTimer = setTimeout(function() {
			_activeCallPopup = null;
			_callPopupTimer = null;
			if (_displayLocation) loadDisplay();
		}, 5000);
	}

	function setDisplayRefreshInterval(seconds) {
		var s = parseInt(seconds, 10) || 15;
		if (s > 15) s = 15; // cap safety-net polling — realtime handles instant updates
		var ms = s * 1000;
		if (_displayInterval && _displayIntervalMs === ms) return;
		if (_displayInterval) clearInterval(_displayInterval);
		_displayInterval = setInterval(loadDisplay, ms);
		_displayIntervalMs = ms;
	}

	function isEnabled(value) {
		return !(value === 0 || value === '0' || value === false || value === null);
	}

	function applyTemplateStyling(tpl) {
		var $board = page.main.find('#display-board');
		var boardStyle = {};
		if (tpl.background_color) boardStyle.backgroundColor = tpl.background_color;
		if (tpl.background_image) {
			boardStyle.backgroundImage = 'url(' + tpl.background_image + ')';
			boardStyle.backgroundSize = 'cover';
			boardStyle.backgroundPosition = 'center';
		}
		if (tpl.text_color) boardStyle.color = tpl.text_color;
		$board.css(boardStyle);
		page.main.find('#disp-template-style').remove();
		var css = '';
		if (tpl.accent_color) {
			css += '#display-board .disp-announce, #display-board .disp-list-kicker, #display-board .disp-list-meta, #display-board .disp-waiting-strip-label, #display-board .disp-visual-subtitle { color: ' + tpl.accent_color + '; }';
			css += '#display-board .disp-board-row.just-called { box-shadow: inset -4px 0 0 ' + tpl.accent_color + '; }';
		}
		if (tpl.custom_css) css += tpl.custom_css;
		if (css) page.main.append('<style id="disp-template-style">' + css + '</style>');
	}

	function buildMediaPlaylist(items) {
		var playlist = (items || []).slice();
		playlist.push(_defaultYoutubeVideo);
		return playlist;
	}

	function getMediaItemKey(item) {
		return [
			item && item.media_type || '',
			item && item.media_file || '',
			parseInt(item && item.display_duration, 10) || 0,
			parseInt(item && item.sort_order, 10) || 0
		].join('::');
	}

	function getMediaSignature(items) {
		return (items || []).map(getMediaItemKey).join('|');
	}

	function rememberMediaState(signature, index, item, startedAt, currentTime) {
		_mediaState = {
			signature: signature,
			index: index,
			media_type: item && item.media_type || '',
			media_file: item && item.media_file || '',
			startedAt: startedAt || Date.now(),
			currentTime: currentTime || 0
		};
	}

	function getResumeMediaState(signature, items) {
		if (!_mediaState || _mediaState.signature !== signature) return null;
		if (_mediaState.index >= items.length) return null;
		var item = items[_mediaState.index];
		if (!item) return null;
		if ((item.media_type || '') !== (_mediaState.media_type || '')) return null;
		if ((item.media_file || '') !== (_mediaState.media_file || '')) return null;
		return _mediaState;
	}

	function captureMediaProgress() {
		var videoEl = page.main.find('#disp-media-stage video').get(0);
		if (!videoEl || !_mediaState) return;
		_mediaState.currentTime = videoEl.currentTime || 0;
	}

	function renderMediaStage(items) {
		if (_mediaTimer) { clearTimeout(_mediaTimer); _mediaTimer = null; }
		var $stage = page.main.find('#disp-media-stage');
		if (!$stage.length || !items || !items.length) {
			_mediaState = null;
			return;
		}

		function markStageMedia(signature, index, item) {
			$stage.attr('data-media-signature', signature || '');
			$stage.attr('data-media-index', String(index));
			$stage.attr('data-media-type', item && item.media_type || '');
			$stage.attr('data-media-file', item && item.media_file || '');
		}

		function stageMatchesMedia(signature, index, item) {
			return ($stage.attr('data-media-signature') || '') === (signature || '')
				&& ($stage.attr('data-media-index') || '') === String(index)
				&& ($stage.attr('data-media-type') || '') === (item && item.media_type || '')
				&& ($stage.attr('data-media-file') || '') === (item && item.media_file || '');
		}

		var orderedItems = items.slice().sort(function(left, right) {
			var leftIsVideo = left.media_type === 'Video';
			var rightIsVideo = right.media_type === 'Video';
			var leftOrder = parseInt(left.sort_order, 10) || 0;
			var rightOrder = parseInt(right.sort_order, 10) || 0;
			if (leftIsVideo !== rightIsVideo) return leftIsVideo ? 1 : -1;
			return leftOrder - rightOrder;
		});
		var signature = getMediaSignature(orderedItems);
		var resumeState = getResumeMediaState(signature, orderedItems);
		var index = resumeState ? resumeState.index : 0;

		function advance() {
			index = (index + 1) % orderedItems.length;
			resumeState = null;
			renderCurrent();
		}

		function scheduleTimedAdvance(item, defaultSeconds) {
			var durationMs = (parseInt(item.display_duration, 10) || defaultSeconds) * 1000;
			var remainingMs = durationMs;
			if (resumeState && resumeState.index === index) {
				var elapsedMs = Date.now() - (resumeState.startedAt || Date.now());
				if (elapsedMs >= durationMs && orderedItems.length > 1) {
					index = (index + Math.floor(elapsedMs / durationMs)) % orderedItems.length;
					resumeState = null;
					renderCurrent();
					return;
				}
				remainingMs = Math.max(250, durationMs - Math.max(0, elapsedMs));
				rememberMediaState(signature, index, item, Date.now() - (durationMs - remainingMs), 0);
			} else {
				rememberMediaState(signature, index, item, Date.now(), 0);
			}
			if (orderedItems.length > 1) {
				_mediaTimer = setTimeout(advance, remainingMs);
			}
		}

		function renderCurrent() {
			if (_mediaTimer) { clearTimeout(_mediaTimer); _mediaTimer = null; }
			var item = orderedItems[index];
			if (!item) return;
			var mediaHtml = '';
			if (item.media_type === 'Embed') {
				if (stageMatchesMedia(signature, index, item) && $stage.find('iframe').length) {
					scheduleTimedAdvance(item, 45);
					return;
				}
				mediaHtml = '<iframe class="disp-media-asset disp-media-embed" src="' + esc(item.media_file) + '" title="' + esc(item.title || 'Hospital laboratory video') + '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>';
			} else if (item.media_type === 'Video') {
				if (stageMatchesMedia(signature, index, item)) {
					var existingVideo = $stage.find('video').get(0);
					if (existingVideo) {
						rememberMediaState(signature, index, item, _mediaState && _mediaState.startedAt || Date.now(), existingVideo.currentTime || 0);
						existingVideo.play().catch(function() {});
						return;
					}
				}
				mediaHtml = '<video class="disp-media-asset" src="' + esc(item.media_file) + '" autoplay muted playsinline preload="auto"></video>';
			} else {
				if (stageMatchesMedia(signature, index, item) && $stage.find('img').length) {
					scheduleTimedAdvance(item, 10);
					return;
				}
				mediaHtml = '<img class="disp-media-asset" src="' + esc(item.media_file) + '" alt="Display media">';
			}
			$stage.html(mediaHtml);
			markStageMedia(signature, index, item);
			if (item.media_type === 'Embed') {
				scheduleTimedAdvance(item, 45);
			} else if (item.media_type === 'Video') {
				var videoEl = $stage.find('video').get(0);
				if (!videoEl) return;
				var resumeTime = resumeState && resumeState.index === index ? (resumeState.currentTime || 0) : 0;
				rememberMediaState(signature, index, item, Date.now(), resumeTime);
				if (resumeTime > 0) {
					videoEl.addEventListener('loadedmetadata', function() {
						var nextTime = resumeTime;
						if (isFinite(videoEl.duration)) {
							nextTime = Math.min(resumeTime, Math.max(0, videoEl.duration - 0.25));
						}
						try {
							videoEl.currentTime = Math.max(0, nextTime);
						} catch (error) {}
					}, { once: true });
				}
				videoEl.addEventListener('timeupdate', function() {
					if (!_mediaState || _mediaState.signature !== signature || _mediaState.index !== index) return;
					_mediaState.currentTime = videoEl.currentTime || 0;
				});
				videoEl.onended = function() {
					if (orderedItems.length > 1) {
						advance();
					} else {
						videoEl.currentTime = 0;
						if (_mediaState) _mediaState.currentTime = 0;
						videoEl.play().catch(function() {});
					}
				};
				videoEl.play().catch(function() {});
			} else if (orderedItems.length > 1) {
				scheduleTimedAdvance(item, 10);
			} else {
				rememberMediaState(signature, index, item, Date.now(), 0);
			}
		}
		renderCurrent();
	}

	function showLocationPicker() {
		clearDisplayTimers();
		_displayLocation = '';

		frappe.xcall('frappe.client.get_list', {
			doctype: 'QMS Location',
			filters: {is_active: 1},
			fields: ['name', 'location_name', 'location_type'],
			limit_page_length: 50
		}).then(function(locs) {
			if (locs.length === 1) {
				_displayLocation = locs[0].name;
				startDisplay();
				return;
			}
			var h = '<div class="disp-loc-picker" dir="' + (isArabicUI() ? 'rtl' : 'ltr') + '"><h2>' + esc(_qmsHospitalName || 'Queue Management') + ' &mdash; ' + esc(t('Display Board', '\u0644\u0648\u062D\u0629 \u0627\u0644\u0639\u0631\u0636')) + '</h2>';
			h += '<div class="disp-picker-actions"><button class="disp-control-btn" id="disp-lang-toggle" title="Switch language">' + esc(getLanguageToggleLabel()) + '</button><button class="disp-theme-toggle" id="disp-theme-toggle" title="Toggle night/light mode" style="width:48px;height:48px;font-size:22px;border-radius:12px">';
			h += (page.main.find('.disp-wrap').attr('data-theme') === 'dark' ? '&#9728;' : '&#9790;');
			h += '</button></div>';
			locs.forEach(function(l) {
			h += '<div class="disp-loc-card" data-loc="' + esc(l.name) + '">'
				+ '<div class="disp-loc-name">' + esc(l.location_name) + '</div>'
				+ '<div class="disp-loc-type">' + esc(l.location_type || '') + '</div>'
					+ '</div>';
			});
			if (!locs.length) {
				h += '<div class="disp-empty">' + esc(t('No locations are configured yet. Create one in QMS Location.', '\u0645\u0627 \u0641\u064A \u0645\u0648\u0627\u0642\u0639 \u0645\u0636\u0627\u0641\u0629. \u0631\u0648\u062D \u0639 QMS Location \u0644\u062A\u0636\u064A\u0641 \u0648\u062D\u062F\u0629.')) + '</div>';
			}
			h += '</div>';
			page.main.find('#display-board').html(h);

			page.main.find('.disp-loc-card').on('click', function() {
				_displayLocation = $(this).data('loc');
				showCounterPicker();
			});
		});
	}

	// Theme toggle handler
	page.main.on('click', '#disp-theme-toggle', function() {
		var wrap = page.main.find('.disp-wrap');
		var cur = wrap.attr('data-theme');
		var nxt = cur === 'dark' ? 'light' : 'dark';
		wrap.attr('data-theme', nxt);
		$(this).html(nxt === 'dark' ? '&#9728;' : '&#9790;');
		localStorage.setItem('qms_display_theme', nxt);
	});

	page.main.on('click', '#disp-lang-toggle', function() {
		_displayLanguage = isArabicUI() ? 'English' : 'Arabic';
		localStorage.setItem('qms_display_language', _displayLanguage);
		rerenderCurrentView();
	});

	function showCounterPicker() {
		clearDisplayTimers();
		frappe.xcall('frappe.client.get_list', {
			doctype: 'QMS Counter',
			filters: {is_active: 1, location: _displayLocation},
			fields: ['name', 'counter_name', 'counter_number'],
			order_by: 'counter_number asc',
			limit_page_length: 50
		}).then(function(counters) {
			if (!counters.length) {
				_displayCounter = '';
				startDisplay();
				return;
			}
			var h = '<div class="disp-loc-picker" dir="' + (isArabicUI() ? 'rtl' : 'ltr') + '"><h2>' + esc(t('Select Counter', '\u0627\u062E\u062A\u0627\u0631 \u0627\u0644\u0643\u0627\u0648\u0646\u062A\u0631')) + '</h2>';
			h += '<div class="disp-picker-actions"><button class="disp-control-btn" id="disp-lang-toggle" title="Switch language">' + esc(getLanguageToggleLabel()) + '</button><button class="disp-theme-toggle" id="disp-theme-toggle" title="Toggle night/light mode" style="width:48px;height:48px;font-size:22px;border-radius:12px">';
			h += (page.main.find('.disp-wrap').attr('data-theme') === 'dark' ? '&#9728;' : '&#9790;');
			h += '</button></div>';
			h += '<div class="disp-loc-card" data-counter="" style="border:2px dashed var(--gray-400)">' +
				'<div class="disp-loc-name">' + esc(t('All Counters', '\u0643\u0644 \u0627\u0644\u0643\u0627\u0648\u0646\u062A\u0631\u0627\u062A')) + '</div>' +
				'<div class="disp-loc-type">' + esc(t('Show the full location queue', '\u0639\u0631\u0636 \u0643\u0644 \u0637\u0627\u0628\u0648\u0631 \u0627\u0644\u0645\u0648\u0642\u0639')) + '</div></div>';
			counters.forEach(function(c) {
				h += '<div class="disp-loc-card" data-counter="' + esc(c.name) + '">' +
					'<div class="disp-loc-name">' + esc(c.counter_name) + '</div>' +
					'<div class="disp-loc-type">' + esc(t('Counter #', '\u0643\u0627\u0648\u0646\u062A\u0631 #')) + esc(c.counter_number) + '</div></div>';
			});
			h += '</div>';
			page.main.find('#display-board').html(h);
			page.main.find('.disp-loc-card').on('click', function() {
				_displayCounter = $(this).data('counter') || '';
				startDisplay();
			});
		});
	}

	function startDisplay() {
		loadDisplay();
	}

	function loadDisplay() {
		var params = {location: _displayLocation};
		if (_displayCounter) params.counter = _displayCounter;
		frappe.xcall('queue_management.qms_display_api.get_display_data', params).then(function(data) {
			captureMediaProgress();
			var now = frappe.datetime.now_time();
			var tpl = data.template || {};
			_templateConfig = tpl;
			setDisplayRefreshInterval(tpl.auto_refresh_interval || 60);
			applyTemplateStyling(tpl);
			var showAr = isArabicUI();
			var showEn = !showAr;
			var showNowServing = isEnabled(tpl.show_now_serving);
			var showWaiting = isEnabled(tpl.show_waiting_list);
			var nowServing = data.now_serving || [];
			var waiting = data.waiting || [];
			var mediaItems = buildMediaPlaylist(data.media_items || []);

			// Resolve bilingual text
			var headerEn = tpl.header_text || 'Queue Display Board';
			var headerAr = tpl.header_text_ar || '';
			var footerEn = tpl.footer_text || '';
			var footerAr = tpl.footer_text_ar || '';
			var announceEn = tpl.announcement_text || '';
			var announceAr = tpl.announcement_text_ar || '';
			var tokenLabel = showAr && !showEn ? '\u0627\u0644\u0631\u0642\u0645' : 'Token';
			var counterLabel = showAr && !showEn ? '\u0627\u0644\u0643\u0627\u0648\u0646\u062A\u0631' : 'Counter';
			var nowServingLabel = showAr && !showEn ? '\u0639\u0645 \u064A\u0646\u062E\u062F\u0645\u0648 \u0647\u0644\u0623' : 'Now Serving';
			var waitingLabel = showAr && !showEn ? '\u0628\u0627\u0644\u0627\u0646\u062A\u0638\u0627\u0631' : 'Waiting';
			var noServingLabel = showAr && !showEn ? '\u0645\u0627 \u0641\u064A \u062A\u0630\u0627\u0643\u0631 \u0639\u0645 \u062A\u0646\u062E\u062F\u0645 \u0647\u0644\u0623' : 'No active token right now';
			var noWaitingLabel = showAr && !showEn ? '\u0645\u0627 \u0641\u064A \u062A\u0630\u0627\u0643\u0631 \u0628\u0627\u0644\u0627\u0646\u062A\u0638\u0627\u0631' : 'No waiting tickets';
			var visualFallbackImage = tpl.logo || tpl.background_image || '';
			var boardRows = nowServing.slice(0, 8);
			var placeholderRows = Math.max(6, boardRows.length);

			var headerText = showAr ? esc(headerAr || headerEn) : esc(headerEn);

			var h = '<div class="disp-header">';
			h += '<div style="display:flex;align-items:center;gap:14px">';
			h += '<h2>' + headerText + '</h2>';
			h += '<button class="disp-back-btn" id="disp-back-btn">' + esc(t('Change Location', '\u063A\u064A\u0651\u0631 \u0627\u0644\u0645\u0648\u0642\u0639')) + '</button>';
			h += '<button class="disp-back-btn" id="disp-counter-btn" style="margin-right:6px">' + esc(t('Change Counter', '\u063A\u064A\u0651\u0631 \u0627\u0644\u0643\u0627\u0648\u0646\u062A\u0631')) + '</button>';
			h += '</div>';
			h += '<div style="display:flex;align-items:center;gap:12px">';
			h += '<div class="disp-clock">' + now + '</div>';
			h += '<button class="disp-control-btn" id="disp-lang-toggle" title="Switch language">' + esc(getLanguageToggleLabel()) + '</button>';
			h += '<button class="disp-theme-toggle" id="disp-theme-toggle" title="Toggle night/light mode">';
			h += (page.main.find('.disp-wrap').attr('data-theme') === 'dark' ? '&#9728;' : '&#9790;');
			h += '</button></div></div>';

			// Announcement banner
			var announceHtml = showAr ? (announceAr || announceEn) : announceEn;
			if (announceHtml) h += '<div class="disp-announce">' + esc(announceHtml) + '</div>';

			h += '<div class="disp-body">';
			h += '<div class="disp-main-grid">';
			h += '<section class="disp-visual-panel">';
			if (mediaItems.length) {
				h += '<div class="disp-visual-media"><div class="disp-media-stage" id="disp-media-stage"></div></div>';
			} else {
				h += '<div class="disp-visual-fallback">';
				h += '<div class="disp-visual-copy">';
				h += '<div class="disp-visual-kicker">' + esc(_qmsHospitalName || 'Hospital') + '</div>';
				h += '<div class="disp-visual-title">' + esc(showAr ? (headerAr || headerEn) : headerEn) + '</div>';
				if (showAr && headerEn) {
					h += '<div class="disp-visual-subtitle">' + esc(headerEn) + '</div>';
				} else if (!showAr && headerAr) {
					h += '<div class="disp-visual-subtitle disp-ar" dir="rtl">' + esc(headerAr) + '</div>';
				}
				h += '</div>';
				h += '<div class="disp-visual-art">';
				if (visualFallbackImage) {
					h += '<img class="disp-visual-image" src="' + esc(visualFallbackImage) + '" alt="Hospital display">';
				} else {
					h += '<div class="disp-visual-mark">' + esc((_qmsHospitalName || 'H').charAt(0).toUpperCase()) + '</div>';
				}
				h += '</div>';
				h += '</div>';
			}
			h += '</section>';

			h += '<aside class="disp-list-panel">';
			h += '<div class="disp-list-header">';
			h += '<div><div class="disp-list-kicker">' + esc(nowServingLabel) + '</div><div class="disp-list-count">' + nowServing.length + '</div></div>';
			if (showWaiting) {
				h += '<div class="disp-list-meta">' + esc(waitingLabel) + ': ' + waiting.length + '</div>';
			}
			h += '</div>';
			if (showNowServing) {
				h += '<div class="disp-board-head">';
				h += '<span class="disp-list-col token">' + esc(tokenLabel) + '</span>';
				h += '<span class="disp-list-col counter">' + esc(counterLabel) + '</span>';
				h += '</div>';
				h += '<div class="disp-board-list">';
				if (boardRows.length) {
					boardRows.forEach(function(ticket) {
						var justCalled = _lastCalledTicket && _lastCalledTicket === ticket.ticket_number ? ' just-called' : '';
						h += '<div class="disp-board-row' + justCalled + '">';
						h += '<span class="disp-board-ticket">' + esc(ticket.ticket_number) + '</span>';
						h += '<span class="disp-board-counter">' + esc(ticket.counter || '-') + '</span>';
						h += '</div>';
					});
				} else {
					h += '<div class="disp-board-row is-empty"><span class="disp-board-empty">' + esc(noServingLabel) + '</span></div>';
				}
				for (var rowIndex = boardRows.length; rowIndex < placeholderRows; rowIndex++) {
					h += '<div class="disp-board-row is-placeholder"><span class="disp-board-placeholder"></span><span class="disp-board-placeholder"></span></div>';
				}
				h += '</div>';
			}
			if (showWaiting) {
				h += '<div class="disp-waiting-strip">';
				h += '<div class="disp-waiting-strip-label">' + esc(waitingLabel) + '</div>';
				if (waiting.length) {
					waiting.slice(0, 4).forEach(function(ticket, idx) {
						h += '<div class="disp-waiting-chip">';
						h += '<span class="disp-waiting-chip-order">' + (idx + 1) + '</span>';
						h += '<span class="disp-waiting-chip-ticket">' + esc(ticket.ticket_number) + '</span>';
						h += '</div>';
					});
				} else {
					h += '<div class="disp-waiting-empty">' + esc(noWaitingLabel) + '</div>';
				}
				h += '</div>';
			}
			h += '</aside>';
			h += '</div>';
			h += '</div>';

			// Footer
			var footerHtml = showAr ? (footerAr || footerEn) : footerEn;
			if (!footerHtml) footerHtml = t('Live updates enabled', '\u0627\u0644\u062A\u062D\u062F\u064A\u062B\u0627\u062A \u0627\u0644\u0645\u0628\u0627\u0634\u0631\u0629 \u0634\u063A\u0627\u0644\u0629');
			h += '<div class="disp-footer">' + esc(footerHtml) + '</div>';
			if (_activeCallPopup && _activeCallPopup.ticket_number) {
				h += '<div class="disp-call-popup">';
				h += '<div class="disp-call-popup-card">';
				h += '<div class="disp-call-popup-kicker">' + esc(t('Now Calling', '\u064A\u062C\u0631\u064A \u0645\u0646\u0627\u062F\u0627\u0629')) + '</div>';
				h += '<div class="disp-call-popup-ticket">' + esc(_activeCallPopup.ticket_number) + '</div>';
				if (_activeCallPopup.service) {
					h += '<div class="disp-call-popup-service">' + esc(_activeCallPopup.service) + '</div>';
				}
				h += '</div></div>';
			}

			page.main.find('#display-board').html(h);
			renderMediaStage(mediaItems);

			page.main.find('#disp-back-btn').on('click', function() {
				showLocationPicker();
			});
			page.main.find('#disp-counter-btn').on('click', function() {
				showCounterPicker();
			});
		});
	}

	if (!_displayLocation) {
		showLocationPicker();
	} else if (!_displayCounter) {
		showCounterPicker();
	} else {
		startDisplay();
	}

	// Realtime updates with debounce
	var _dispDebounce = null;
	function debouncedLoadDisplay(delay) {
		if (!_displayLocation) return;
		if (_dispDebounce) clearTimeout(_dispDebounce);
		_dispDebounce = setTimeout(loadDisplay, delay || 120);
	}

	// ── Audio announcement ──
	var _audioCtx = null;
	function _getAudioCtx() {
		if (!_audioCtx) {
			_audioCtx = new (window.AudioContext || window.webkitAudioContext)();
		}
		return _audioCtx;
	}

	function playChime() {
		try {
			var soundFile = _templateConfig.call_sound;
			var repeatCount = parseInt(_templateConfig.call_sound_repeat) || 1;

			if (soundFile) {
				var played = 0;
				function playOnce() {
					var audio = new Audio(soundFile);
					audio.volume = 0.8;
					audio.onended = function() {
						played++;
						if (played < repeatCount) playOnce();
					};
					audio.play().catch(function() {});
				}
				playOnce();
			} else {
				// Fallback: synthesized arpeggio chime (reuse AudioContext)
				var ctx = _getAudioCtx();
				var notes = [880, 1108.73, 1318.5]; // A5, C#6, E6
				notes.forEach(function(freq, i) {
					var osc = ctx.createOscillator();
					var gain = ctx.createGain();
					osc.type = 'sine';
					osc.frequency.value = freq;
					gain.gain.setValueAtTime(0.25, ctx.currentTime + i * 0.15);
					gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.15 + 0.4);
					osc.connect(gain);
					gain.connect(ctx.destination);
					osc.start(ctx.currentTime + i * 0.15);
					osc.stop(ctx.currentTime + i * 0.15 + 0.5);
				});
			}
		} catch(e) { /* audio not available */ }
	}

	function announceTicket(data) {
		if (!data || !data.ticket_number) return;
		playChime();
		if ('speechSynthesis' in window) {
			setTimeout(function() {
				var ticketNum = data.ticket_number.replace(/[^0-9A-Za-z]/g, ' ').trim().split('').join(' ');
				var counterText = data.counter_name || ('Counter ' + (data.counter_number || ''));
				var textEn = 'Ticket ' + ticketNum + '. Please proceed to ' + counterText + '.';
				var utter = new SpeechSynthesisUtterance(textEn);
				utter.lang = 'en-US';
				utter.rate = 0.75;
				utter.pitch = 1;
				utter.volume = 1;
				window.speechSynthesis.cancel();
				window.speechSynthesis.speak(utter);
			}, 800);
		}
	}

	function _dispMatchesLocation(data) {
		if (!_displayLocation) return true; // no filter = show all
		if (!data) return true; // no payload = refresh to be safe
		var loc = data.location || data.to_location || data.from_location || '';
		return !loc || loc === _displayLocation;
	}

	function _dispTicketCalled(data) {
		if (!_dispMatchesBoard(data)) return;
		_lastCalledTicket = data && data.ticket_number;
		showCallPopup(data);
		announceTicket(data);
		debouncedLoadDisplay(50);
	}

	function _dispFilteredRefresh(data) {
		if (!_dispMatchesLocation(data)) return;
		debouncedLoadDisplay(120);
	}

	var _dispRealtimeEvents = ['qms_ticket_completed', 'qms_new_ticket', 'qms_ticket_held', 'qms_ticket_no_show', 'qms_counter_updated', 'qms_ticket_transferred', 'qms_ticket_requeued', 'qms_ticket_serving', 'qms_ticket_cancelled'];

	function _dispBindLive() {
		if (_dispLiveBound) return;
		frappe.realtime.on('qms_ticket_called', _dispTicketCalled);
		_dispRealtimeEvents.forEach(function(evt) {
			frappe.realtime.on(evt, _dispFilteredRefresh);
		});
		_dispLiveBound = true;
		if (_displayLocation) loadDisplay();
	}

	function _dispUnbindLive() {
		clearDisplayTimers();
		if (_dispDebounce) { clearTimeout(_dispDebounce); _dispDebounce = null; }
		if (_audioCtx) { _audioCtx.close().catch(function(){}); _audioCtx = null; }
		frappe.realtime.off('qms_ticket_called', _dispTicketCalled);
		_dispRealtimeEvents.forEach(function(evt) {
			frappe.realtime.off(evt, _dispFilteredRefresh);
		});
		_dispLiveBound = false;
	}

	_dispBindLive();

	// Store for on_page_show re-bind
	wrapper._qmsDispBind = _dispBindLive;

	page.wrapper.on('page-change', function() {
		_dispUnbindLive();
		// Restore Frappe chrome when leaving display
		$('header.navbar, .page-head').show();
		$('body').css({'padding-top': '', 'overflow': ''});
	});
};

// Re-bind live updates when navigating back to the display board
frappe.pages['qms-display'].on_page_show = function(wrapper) {
	// Re-enter fullscreen mode
	$('header.navbar, .page-head').hide();
	$('body').css({'padding-top': 0, 'overflow': 'hidden', 'height': '100vh'});
	$(page.wrapper).css({'margin': 0, 'padding': 0, 'height': '100vh'});
	$(page.wrapper).find('.page-content, .layout-main-section-wrapper, .layout-main-section, .container-fluid').css({'margin': 0, 'padding': 0, 'max-width': '100%', 'height': '100%'});
	page.main.css({'margin': 0, 'padding': 0, 'height': '100%'});
	if (wrapper._qmsDispBind) wrapper._qmsDispBind();
};
