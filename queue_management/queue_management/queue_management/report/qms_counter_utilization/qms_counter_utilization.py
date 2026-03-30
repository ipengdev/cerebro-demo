import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "counter", "label": "Counter", "fieldtype": "Data", "width": 200},
		{"fieldname": "total_served", "label": "Total Served", "fieldtype": "Int", "width": 120},
		{"fieldname": "avg_service", "label": "Avg Service (min)", "fieldtype": "Float", "width": 130},
		{"fieldname": "total_service_mins", "label": "Total Service (min)", "fieldtype": "Float", "width": 150},
	]
	data = frappe.db.sql("""
		SELECT IFNULL(c.counter_name, qt.counter) as counter,
		       COUNT(*) as total_served,
		       ROUND(AVG(qt.service_duration_mins), 1) as avg_service,
		       ROUND(SUM(qt.service_duration_mins), 1) as total_service_mins
		FROM `tabQMS Queue Ticket` qt
		LEFT JOIN `tabQMS Counter` c ON c.name = qt.counter
		WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s
		  AND qt.status = 'Completed' AND qt.counter IS NOT NULL
		GROUP BY qt.counter
		ORDER BY total_served DESC
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [d.counter or "Unknown" for d in data],
			"datasets": [{"name": "Total Served", "values": [d.total_served for d in data]}],
		},
		"type": "bar",
	} if data else None

	return columns, data, None, chart
