import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = [
		{"fieldname": "service", "label": "Service", "fieldtype": "Data", "width": 200},
		{"fieldname": "total_responses", "label": "Responses", "fieldtype": "Int", "width": 100},
		{"fieldname": "avg_rating", "label": "Avg Rating", "fieldtype": "Float", "width": 100},
		{"fieldname": "five_star", "label": "5 Stars", "fieldtype": "Int", "width": 80},
		{"fieldname": "one_star", "label": "1 Star", "fieldtype": "Int", "width": 80},
	]
	data = frappe.db.sql("""
		SELECT IFNULL(s.service_name, fr.service) as service,
		       COUNT(*) as total_responses,
		       ROUND(AVG(CASE WHEN fr.overall_rating <= 1 THEN fr.overall_rating * 5 ELSE fr.overall_rating END), 1) as avg_rating,
		       SUM(CASE WHEN (CASE WHEN fr.overall_rating <= 1 THEN fr.overall_rating * 5 ELSE fr.overall_rating END) >= 4.5 THEN 1 ELSE 0 END) as five_star,
		       SUM(CASE WHEN (CASE WHEN fr.overall_rating <= 1 THEN fr.overall_rating * 5 ELSE fr.overall_rating END) <= 1.5 THEN 1 ELSE 0 END) as one_star
		FROM `tabQMS Feedback Response` fr
		LEFT JOIN `tabQMS Service` s ON s.name = fr.service
		WHERE fr.submission_time BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY fr.service
		ORDER BY avg_rating DESC
	""", filters, as_dict=1)

	chart = {
		"data": {
			"labels": [d.service for d in data],
			"datasets": [{"name": "Avg Rating", "values": [d.avg_rating for d in data]}],
		},
		"type": "bar",
		"colors": ["#ffc107"],
	} if data else None

	return columns, data, None, chart
