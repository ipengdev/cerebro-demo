// Service Ticket - Professional Workflow UI
frappe.ui.form.on("Service Ticket", {
	refresh(frm) {
		itsm_ticket.render_workflow_header(frm);
		itsm_ticket.add_workflow_actions(frm);
		itsm_ticket.render_ticket_sidebar(frm);
	},

	status(frm) {
		itsm_ticket.render_workflow_header(frm);
		itsm_ticket.add_workflow_actions(frm);
	},

	priority(frm) {
		itsm_ticket.render_workflow_header(frm);
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.raised_by) {
			frm.set_value("raised_by", frappe.session.user);
		}
	},
});

const itsm_ticket = {
	stages: [
		{ status: "Open",        icon: "es-icon-open-folder",   label: "Open",        color: "#dc2626" },
		{ status: "In Progress", icon: "es-icon-wrench",        label: "In Progress", color: "#2563eb" },
		{ status: "Pending",     icon: "es-icon-clock",         label: "Pending",     color: "#d97706" },
		{ status: "Resolved",    icon: "es-icon-check-circle",  label: "Resolved",    color: "#16a34a" },
		{ status: "Closed",      icon: "es-icon-lock",          label: "Closed",      color: "#6b7280" },
	],

	status_to_stage: {
		"Open": 0, "In Progress": 1, "Pending": 2, "On Hold": 2,
		"Resolved": 3, "Closed": 4, "Cancelled": 4,
	},

	render_workflow_header(frm) {
		$(".itsm-workflow-header").remove();

		const current = frm.doc.status || "Open";
		const current_idx = this.status_to_stage[current] ?? 0;
		const is_cancelled = current === "Cancelled";
		const is_on_hold = current === "On Hold";
		const elapsed = this._get_elapsed_time(frm);
		const priority = frm.doc.priority || "Medium";

		// ─── Priority banner ───
		let priority_banner = "";
		if (priority === "Urgent") {
			priority_banner = `<div class="itsm-priority-banner priority-urgent">
				<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 2.5a1 1 0 011 1V8a1 1 0 01-2 0V4.5a1 1 0 011-1zm0 7.5a1 1 0 100-2 1 1 0 000 2z"/></svg>
				<span>URGENT — Immediate attention required</span>
			</div>`;
		} else if (priority === "High") {
			priority_banner = `<div class="itsm-priority-banner priority-high">
				<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8.982 1.566a1.13 1.13 0 00-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 01-1.1 0L7.1 5.995A.905.905 0 018 5zm.002 6a1 1 0 110 2 1 1 0 010-2z"/></svg>
				<span>HIGH PRIORITY — Expedited handling</span>
			</div>`;
		}

		// ─── Stage pipeline ───
		let pipeline = `<div class="stage-pipeline">`;
		this.stages.forEach((stage, idx) => {
			let cls = "stage-step";
			if (is_cancelled) {
				cls += idx === 4 ? " stage-cancelled" : " stage-inactive";
			} else if (idx < current_idx) {
				cls += " stage-completed";
			} else if (idx === current_idx) {
				cls += " stage-active";
				if (is_on_hold) cls += " stage-on-hold";
			} else {
				cls += " stage-inactive";
			}

			const show_label = is_on_hold && idx === current_idx ? "On Hold" : stage.label;
			const check_icon = `<svg width="18" height="18" viewBox="0 0 20 20" fill="white"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg>`;

			// Timestamp for completed stages
			let ts = "";
			if (idx === 0 && frm.doc.creation) {
				ts = `<div class="stage-ts">${this._format_dt(frm.doc.creation)}</div>`;
			} else if (idx === 1 && frm.doc.first_responded_on) {
				ts = `<div class="stage-ts">${this._format_dt(frm.doc.first_responded_on)}</div>`;
			} else if (idx === 3 && frm.doc.resolved_on) {
				ts = `<div class="stage-ts">${this._format_dt(frm.doc.resolved_on)}</div>`;
			} else if (idx === 4 && frm.doc.closed_on) {
				ts = `<div class="stage-ts">${this._format_dt(frm.doc.closed_on)}</div>`;
			}

			pipeline += `
			<div class="${cls}" data-status="${stage.status}">
				<div class="stage-node">
					<div class="stage-icon">${idx < current_idx ? check_icon : (idx + 1)}</div>
				</div>
				<div class="stage-label">${show_label}</div>
				${ts}
				${idx < this.stages.length - 1 ? '<div class="stage-connector"></div>' : ""}
			</div>`;
		});
		pipeline += `</div>`;

		// ─── Info cards row ───
		let info_cards = `<div class="ticket-info-cards">`;

		// Card 1: Ticket ID + Category
		info_cards += `<div class="info-card">
			<div class="info-card-icon" style="background:#eff6ff;color:#2563eb">
				<svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>
			</div>
			<div class="info-card-body">
				<div class="info-card-title">${frm.doc.name || "New Ticket"}</div>
				<div class="info-card-sub">${frm.doc.ticket_category || "—"} ${frm.doc.ticket_type ? "· " + frm.doc.ticket_type : ""}</div>
			</div>
		</div>`;

		// Card 2: Priority
		const p_colors = { Urgent: "#dc2626", High: "#ea580c", Medium: "#d97706", Low: "#2563eb" };
		const p_bgs = { Urgent: "#fef2f2", High: "#fff7ed", Medium: "#fffbeb", Low: "#eff6ff" };
		info_cards += `<div class="info-card">
			<div class="info-card-icon" style="background:${p_bgs[priority] || "#f1f5f9"};color:${p_colors[priority] || "#64748b"}">
				<svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 6a3 3 0 013-3h10l-4 4 4 4H6a3 3 0 01-3-3V6z" clip-rule="evenodd"/><path d="M5 16V6"/></svg>
			</div>
			<div class="info-card-body">
				<div class="info-card-title" style="color:${p_colors[priority] || "#64748b"}">${priority}</div>
				<div class="info-card-sub">Priority</div>
			</div>
		</div>`;

		// Card 3: Age / Duration
		info_cards += `<div class="info-card">
			<div class="info-card-icon" style="background:#f0fdf4;color:#16a34a">
				<svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/></svg>
			</div>
			<div class="info-card-body">
				<div class="info-card-title">${elapsed || "Just now"}</div>
				<div class="info-card-sub">Ticket Age</div>
			</div>
		</div>`;

		// Card 4: Assigned
		const assignee = frm.doc.assigned_to ? frappe.user.full_name(frm.doc.assigned_to) : "Unassigned";
		const esc = frm.doc.escalation_level ? ` · L${frm.doc.escalation_level}` : "";
		info_cards += `<div class="info-card">
			<div class="info-card-icon" style="background:#faf5ff;color:#7c3aed">
				<svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>
			</div>
			<div class="info-card-body">
				<div class="info-card-title">${assignee}</div>
				<div class="info-card-sub">Assigned${esc}</div>
			</div>
		</div>`;

		info_cards += `</div>`;

		// ─── SLA Section ───
		let sla_html = "";
		if ((frm.doc.response_by || frm.doc.resolution_by) && !["Closed", "Cancelled"].includes(current)) {
			sla_html = this._build_sla_section(frm);
		}

		// ─── Assemble full header ───
		const html = `<div class="itsm-workflow-header">
			${priority_banner}
			<div class="itsm-stage-tracker">${pipeline}</div>
			${info_cards}
			${sla_html}
		</div>`;

		$(frm.fields_dict.section_basic.$wrapper)
			.closest(".form-layout")
			.before(html);
	},

	_build_sla_section(frm) {
		const now = frappe.datetime.now_datetime();
		let items = [];

		if (frm.doc.response_by) {
			const responded = frm.doc.first_responded_on;
			if (responded) {
				const ok = frm.doc.response_sla_status !== "Breached";
				items.push({
					label: "First Response",
					status: ok ? "met" : "breached",
					primary: ok ? "Within SLA" : "Breached",
					secondary: this._format_dt(responded),
					pct: 100,
				});
			} else {
				const rem = this._time_remaining(now, frm.doc.response_by);
				items.push({
					label: "Response Due",
					status: rem.overdue ? "breached" : rem.urgent ? "warning" : "ok",
					primary: rem.text,
					secondary: "Due " + this._format_dt(frm.doc.response_by),
					pct: rem.pct,
				});
			}
		}

		if (frm.doc.resolution_by) {
			const resolved = frm.doc.resolved_on;
			if (resolved) {
				const ok = frm.doc.resolution_sla_status !== "Breached";
				items.push({
					label: "Resolution",
					status: ok ? "met" : "breached",
					primary: ok ? "Within SLA" : "Breached",
					secondary: this._format_dt(resolved),
					pct: 100,
				});
			} else {
				const rem = this._time_remaining(now, frm.doc.resolution_by);
				items.push({
					label: "Resolution Due",
					status: rem.overdue ? "breached" : rem.urgent ? "warning" : "ok",
					primary: rem.text,
					secondary: "Due " + this._format_dt(frm.doc.resolution_by),
					pct: rem.pct,
				});
			}
		}

		if (!items.length) return "";

		let html = `<div class="itsm-sla-section">
			<div class="sla-section-title">
				<svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/></svg>
				SLA Tracking
			</div>
			<div class="sla-cards">`;

		items.forEach(item => {
			const bar_color = item.status === "breached" ? "#dc2626" : item.status === "warning" ? "#d97706" : item.status === "met" ? "#16a34a" : "#16a34a";
			html += `
			<div class="sla-card sla-${item.status}">
				<div class="sla-card-header">
					<span class="sla-card-label">${item.label}</span>
					<span class="sla-card-status">${item.primary}</span>
				</div>
				<div class="sla-progress-bar">
					<div class="sla-progress-fill" style="width:${Math.min(item.pct, 100)}%;background:${bar_color}"></div>
				</div>
				<div class="sla-card-footer">${item.secondary}</div>
			</div>`;
		});

		html += `</div></div>`;
		return html;
	},

	render_sla_badges() { /* replaced by _build_sla_section */ },
	render_priority_banner() { /* integrated into render_workflow_header */ },

	add_workflow_actions(frm) {
		if (frm.is_new()) return;

		const status = frm.doc.status;
		const transitions = {
			"Open":        [{ to: "In Progress", label: "Start Working", btn: "primary" }],
			"In Progress": [
				{ to: "Pending",   label: "Set Pending",   btn: "warning" },
				{ to: "On Hold",   label: "Put On Hold",   btn: "default" },
				{ to: "Resolved",  label: "Mark Resolved", btn: "success" },
			],
			"Pending": [
				{ to: "In Progress", label: "Resume Work", btn: "primary" },
				{ to: "Resolved",    label: "Mark Resolved", btn: "success" },
			],
			"On Hold": [
				{ to: "In Progress", label: "Resume Work", btn: "primary" },
			],
			"Resolved": [
				{ to: "Closed",      label: "Close Ticket",    btn: "success" },
				{ to: "In Progress", label: "Reopen",          btn: "warning" },
			],
			"Closed": [
				{ to: "Open", label: "Reopen Ticket", btn: "warning" },
			],
		};

		const available = transitions[status] || [];
		available.forEach(t => {
			frm.add_custom_button(
				__(t.label),
				() => {
					if (t.to === "Resolved" && !frm.doc.resolution_details) {
						frappe.prompt(
							[{
								fieldtype: "Text Editor",
								fieldname: "resolution_details",
								label: "Resolution Details",
								reqd: 1,
							}],
							(values) => {
								frm.set_value("resolution_details", values.resolution_details);
								frm.set_value("status", t.to);
								frm.save();
							},
							__("Provide Resolution Details"),
							__("Resolve")
						);
					} else {
						frm.set_value("status", t.to);
						frm.save();
					}
				},
				__("Actions")
			);
		});

		// Escalate button
		if (["Open", "In Progress", "Pending"].includes(status)) {
			frm.add_custom_button(
				__("Escalate"),
				() => {
					frappe.prompt(
						[{
							fieldtype: "Link",
							fieldname: "escalate_to",
							label: "Escalate To",
							options: "User",
							reqd: 1,
						}, {
							fieldtype: "Small Text",
							fieldname: "reason",
							label: "Escalation Reason",
						}],
						(values) => {
							const level = (frm.doc.escalation_level || 0) + 1;
							frm.set_value("escalated_to", values.escalate_to);
							frm.set_value("escalation_level", level);
							frappe.xcall("frappe.client.add_comment", {
								reference_doctype: "Service Ticket",
								reference_name: frm.doc.name,
								content: `Escalated to Level ${level} (${values.escalate_to}). Reason: ${values.reason || "Not specified"}`,
								comment_type: "Info",
							}).then(() => frm.save());
						},
						__("Escalate Ticket"),
						__("Escalate")
					);
				},
				__("Actions")
			);
		}
	},

	render_ticket_sidebar(frm) {
		if (frm.is_new()) return;

		// Fetch activity log for this ticket
		frappe.xcall("itsm.api.get_ticket_activity", {
			ticket_name: frm.doc.name,
		}).then(activity => {
			if (!activity || !activity.length) return;

			$(".itsm-activity-panel").remove();

			let html = `<div class="itsm-activity-panel">
				<div class="activity-panel-title">
					<svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/></svg>
					Activity Timeline
				</div>
				<div class="activity-list">`;

			activity.forEach((a, idx) => {
				const icon_cls = this._activity_icon(a.type);
				html += `
				<div class="activity-item ${idx === 0 ? "latest" : ""}">
					<div class="activity-dot ${icon_cls}"></div>
					<div class="activity-content">
						<div class="activity-text">${a.text}</div>
						<div class="activity-meta">${a.by_name} · ${a.ago}</div>
					</div>
				</div>`;
			});

			html += `</div></div>`;

			// Insert after the SLA section or after the workflow header
			const $target = $(".itsm-sla-section");
			if ($target.length) {
				$target.after(html);
			} else {
				$(".itsm-workflow-header").append(html);
			}
		}).catch(() => {});
	},

	_activity_icon(type) {
		const map = {
			"status_change": "act-status",
			"assignment": "act-assign",
			"escalation": "act-escalate",
			"comment": "act-comment",
			"creation": "act-create",
			"sla_breach": "act-breach",
		};
		return map[type] || "act-default";
	},

	_time_remaining(now_str, target_str) {
		const now = moment(now_str);
		const target = moment(target_str);
		const diff = target.diff(now, "minutes");
		// Calculate progress percentage based on creation to target
		const total_window = target.diff(moment(target).subtract(Math.abs(diff) + 60, "minutes"), "minutes");
		const pct = diff <= 0 ? 100 : Math.max(0, Math.min(100, 100 - (diff / (Math.abs(diff) + 60)) * 100));

		if (diff < 0) {
			const abs = Math.abs(diff);
			return {
				overdue: true, urgent: false, pct: 100,
				text: abs >= 60 ? `${Math.floor(abs / 60)}h ${abs % 60}m overdue` : `${abs}m overdue`,
			};
		}
		if (diff <= 60) {
			return {
				overdue: false, urgent: true, pct: Math.min(95, pct),
				text: `${diff}m remaining`,
			};
		}
		return {
			overdue: false, urgent: false,
			pct: Math.min(80, pct),
			text: diff >= 1440
				? `${Math.floor(diff / 1440)}d ${Math.floor((diff % 1440) / 60)}h`
				: `${Math.floor(diff / 60)}h ${diff % 60}m`,
		};
	},

	_get_elapsed_time(frm) {
		if (!frm.doc.creation) return "";
		const created = moment(frm.doc.creation);
		const end = frm.doc.closed_on ? moment(frm.doc.closed_on) : moment();
		const mins = end.diff(created, "minutes");

		if (mins < 60) return `${mins}m`;
		if (mins < 1440) return `${Math.floor(mins / 60)}h ${mins % 60}m`;
		const days = Math.floor(mins / 1440);
		const hrs = Math.floor((mins % 1440) / 60);
		return `${days}d ${hrs}h`;
	},

	_format_dt(dt) {
		if (!dt) return "";
		return moment(dt).format("MMM D, h:mm A");
	},
};
