// CNSS Monthly Declaration - Lebanese Social Security
frappe.query_reports["CNSS Monthly Declaration"] = {
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
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				{ value: 1, label: __("January") },
				{ value: 2, label: __("February") },
				{ value: 3, label: __("March") },
				{ value: 4, label: __("April") },
				{ value: 5, label: __("May") },
				{ value: 6, label: __("June") },
				{ value: 7, label: __("July") },
				{ value: 8, label: __("August") },
				{ value: 9, label: __("September") },
				{ value: 10, label: __("October") },
				{ value: 11, label: __("November") },
				{ value: 12, label: __("December") },
			],
			reqd: 1,
			default: new Date().getMonth() + 1,
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
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "total_cnss" && data) {
			value = "<b>" + value + "</b>";
		}
		return value;
	},
};
