frappe.listview_settings["Delegation"] = {
	add_fields: ["status", "user", "delegate", "start_date", "end_date"],
	get_indicator(doc) {
		const status_map = {
			Pending: [__("Pending"), "orange", "status,=,Pending"],
			Active: [__("Active"), "blue", "status,=,Active"],
			Completed: [__("Completed"), "green", "status,=,Completed"],
			Cancelled: [__("Cancelled"), "red", "status,=,Cancelled"],
		};
		return status_map[doc.status] || [__("Unknown"), "gray", ""];
	},
};
