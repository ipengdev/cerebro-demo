// Service Ticket - Enhanced List View
frappe.listview_settings["Service Ticket"] = {
	add_fields: [
		"status", "priority", "assigned_to", "ticket_category",
		"response_sla_status", "resolution_sla_status",
		"response_by", "resolution_by", "raised_by",
		"escalation_level", "resolved_on",
	],

	has_indicator_for_draft: false,

	get_indicator(doc) {
		const map = {
			"Open":        [__("Open"),        "red"],
			"In Progress": [__("In Progress"), "blue"],
			"Pending":     [__("Pending"),     "orange"],
			"On Hold":     [__("On Hold"),     "yellow"],
			"Resolved":    [__("Resolved"),    "green"],
			"Closed":      [__("Closed"),      "gray"],
			"Cancelled":   [__("Cancelled"),   "gray"],
		};
		return map[doc.status] || [doc.status, "gray"];
	},

	formatters: {
		priority(value) {
			if (!value) return value;
			const cls = value.toLowerCase();
			return `<span class="itsm-list-priority-pill ${cls}">${value}</span>`;
		},

		assigned_to(value) {
			if (!value) return `<span style="color:#d1d5db;font-size:11px">Unassigned</span>`;
			return frappe.avatar(value, "avatar-small") + " " + frappe.user.full_name(value);
		},

		subject(value, df, doc) {
			let prefix = "";
			// SLA indicator
			if (doc.resolution_sla_status === "Breached" || doc.response_sla_status === "Breached") {
				prefix += `<span class="itsm-list-sla-dot breach" title="SLA Breached"></span>`;
			} else if (doc.resolution_sla_status === "Within SLA" || doc.response_sla_status === "Within SLA") {
				prefix += `<span class="itsm-list-sla-dot within" title="Within SLA"></span>`;
			} else {
				prefix += `<span class="itsm-list-sla-dot none"></span>`;
			}
			// Escalation badge
			if (doc.escalation_level && doc.escalation_level > 0) {
				prefix += `<span style="font-size:10px;font-weight:700;color:#ea580c;margin-right:4px">L${doc.escalation_level}</span>`;
			}
			return prefix + frappe.utils.escape_html(value);
		},

		ticket_category(value) {
			if (!value) return "";
			return `<span style="font-size:11px;color:#6b7280;background:#f1f5f9;padding:1px 8px;border-radius:10px">${frappe.utils.escape_html(value)}</span>`;
		},
	},

	onload(listview) {
		listview.page.add_inner_button(__("My Tickets"), () => {
			listview.filter_area.add([
				["Service Ticket", "assigned_to", "=", frappe.session.user],
			]);
		});
		listview.page.add_inner_button(__("SLA Breached"), () => {
			listview.filter_area.add([
				["Service Ticket", "resolution_sla_status", "=", "Breached"],
			]);
		});
		listview.page.add_inner_button(__("Urgent / High"), () => {
			listview.filter_area.add([
				["Service Ticket", "priority", "in", ["Urgent", "High"]],
			]);
		});
		listview.page.add_inner_button(__("Open Tickets"), () => {
			listview.filter_area.add([
				["Service Ticket", "status", "in", ["Open", "In Progress", "Pending"]],
			]);
		});
	},
};
