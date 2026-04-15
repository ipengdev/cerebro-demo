// ITSM Global JS — redirect workspace to dashboard page
$(document).on("page-change", function () {
	const route = frappe.get_route();
	if (
		route &&
		route[0] === "Workspaces" &&
		(route[1] === "ITSM" || route[2] === "ITSM")
	) {
		// Auto-redirect to the real dashboard page
		frappe.set_route("itsm-dashboard");
	}
});
