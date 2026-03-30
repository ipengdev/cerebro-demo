import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "hour", "label": "Hour", "fieldtype": "Data", "width": 100},
		{"fieldname": "total_tickets", "label": "Total Tickets", "fieldtype": "Int", "width": 120},
		{"fieldname": "avg_wait", "label": "Avg Wait (min)", "fieldtype": "Float", "width": 120},
	]
	conditions = "WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s"
	if filters.get("location"):
		conditions += " AND qt.location = %(location)s"
	data = frappe.db.sql(f"""
		SELECT CONCAT(HOUR(qt.check_in_time), ':00') as hour,
		       COUNT(*) as total_tickets,
		       ROUND(AVG(qt.wait_time_mins), 1) as avg_wait
		FROM `tabQMS Queue Ticket` qt
		{conditions}
		  AND qt.check_in_time IS NOT NULL
		GROUP BY HOUR(qt.check_in_time)
		ORDER BY HOUR(qt.check_in_time)
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [d.hour for d in data],
			"datasets": [{"name": "Total Tickets", "values": [d.total_tickets for d in data]}],
		},
		"type": "bar",
		"colors": ["#2563eb"],
	} if data else None

	return columns, data, None, chart
