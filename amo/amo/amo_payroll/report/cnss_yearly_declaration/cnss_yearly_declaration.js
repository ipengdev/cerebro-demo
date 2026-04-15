// CNSS Yearly Declaration - Lebanese Social Security Annual Summary
frappe.query_reports["CNSS Yearly Declaration"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			options: (() => {
				let years = [];
				let current = new Date().getFullYear();
				for (let y = current; y >= current - 5; y--) {
					years.push(y);
				}
				return years;
			})(),
			reqd: 1,
			default: new Date().getFullYear(),
		},
	],
};
