import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "service", "label": "Service", "fieldtype": "Data", "width": 200},
		{"fieldname": "total_tickets", "label": "Total Tickets", "fieldtype": "Int", "width": 120},
		{"fieldname": "completed", "label": "Completed", "fieldtype": "Int", "width": 100},
		{"fieldname": "no_show", "label": "No Show", "fieldtype": "Int", "width": 100},
		{"fieldname": "avg_wait", "label": "Avg Wait (min)", "fieldtype": "Float", "width": 120},
		{"fieldname": "avg_service", "label": "Avg Service (min)", "fieldtype": "Float", "width": 130},
	]
	conditions = "WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s"
	if filters.get("location"):
		conditions += " AND qt.location = %(location)s"
	data = frappe.db.sql(f"""
		SELECT IFNULL(s.service_name, qt.service) as service,
		       COUNT(*) as total_tickets,
		       SUM(CASE WHEN qt.status='Completed' THEN 1 ELSE 0 END) as completed,
		       SUM(CASE WHEN qt.status='No Show' THEN 1 ELSE 0 END) as no_show,
		       ROUND(AVG(qt.wait_time_mins), 1) as avg_wait,
		       ROUND(AVG(qt.service_duration_mins), 1) as avg_service
		FROM `tabQMS Queue Ticket` qt
		LEFT JOIN `tabQMS Service` s ON s.name = qt.service
		{conditions}
		GROUP BY qt.service
		ORDER BY total_tickets DESC
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [d.service for d in data],
			"datasets": [
				{"name": "Completed", "values": [d.completed for d in data]},
				{"name": "No Show", "values": [d.no_show for d in data]},
			],
		},
		"type": "bar",
		"colors": ["#16a34a", "#dc2626"],
	} if data else None

	return columns, data, None, chart
