import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "total_tickets", "label": "Total Tickets", "fieldtype": "Int", "width": 120},
		{"fieldname": "avg_wait", "label": "Avg Wait (min)", "fieldtype": "Float", "width": 120},
		{"fieldname": "max_wait", "label": "Max Wait (min)", "fieldtype": "Float", "width": 120},
		{"fieldname": "min_wait", "label": "Min Wait (min)", "fieldtype": "Float", "width": 120},
	]
	conditions = "WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s"
	if filters.get("location"):
		conditions += " AND qt.location = %(location)s"
	data = frappe.db.sql(f"""
		SELECT qt.token_date as date,
		       COUNT(*) as total_tickets,
		       ROUND(AVG(qt.wait_time_mins), 1) as avg_wait,
		       ROUND(MAX(qt.wait_time_mins), 1) as max_wait,
		       ROUND(MIN(qt.wait_time_mins), 1) as min_wait
		FROM `tabQMS Queue Ticket` qt
		{conditions}
		GROUP BY qt.token_date
		ORDER BY qt.token_date DESC
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [str(d.date) for d in data],
			"datasets": [
				{"name": "Avg Wait", "values": [d.avg_wait for d in data]},
				{"name": "Max Wait", "values": [d.max_wait for d in data]},
			],
		},
		"type": "line",
		"colors": ["#2563eb", "#dc2626"],
	} if data else None

	return columns, data, None, chart
