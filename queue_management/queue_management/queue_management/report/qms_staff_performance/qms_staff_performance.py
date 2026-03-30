import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "served_by", "label": "Employee", "fieldtype": "Data", "width": 200},
		{"fieldname": "total_served", "label": "Total Served", "fieldtype": "Int", "width": 120},
		{"fieldname": "avg_service", "label": "Avg Service (min)", "fieldtype": "Float", "width": 130},
		{"fieldname": "avg_wait", "label": "Avg Wait (min)", "fieldtype": "Float", "width": 120},
	]
	data = frappe.db.sql("""
		SELECT IFNULL(e.employee_name, qt.served_by) as served_by,
		       COUNT(*) as total_served,
		       ROUND(AVG(qt.service_duration_mins), 1) as avg_service,
		       ROUND(AVG(qt.wait_time_mins), 1) as avg_wait
		FROM `tabQMS Queue Ticket` qt
		LEFT JOIN `tabEmployee` e ON e.name = qt.served_by
		WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s
		  AND qt.status = 'Completed' AND qt.served_by IS NOT NULL
		GROUP BY qt.served_by
		ORDER BY total_served DESC
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [d.served_by or "Unknown" for d in data],
			"datasets": [{"name": "Total Served", "values": [d.total_served for d in data]}],
		},
		"type": "bar",
	} if data else None

	return columns, data, None, chart
