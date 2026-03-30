import frappe
from frappe.utils import today, add_months

def execute(filters=None):
	if not filters:
		filters = {}
	filters.setdefault("from_date", add_months(today(), -1))
	filters.setdefault("to_date", today())

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"fieldname": "ticket_number", "label": "Ticket", "fieldtype": "Data", "width": 100},
		{"fieldname": "patient_name", "label": "Patient", "fieldtype": "Data", "width": 150},
		{"fieldname": "service", "label": "Service", "fieldtype": "Data", "width": 150},
		{"fieldname": "location", "label": "Location", "fieldtype": "Data", "width": 150},
		{"fieldname": "counter", "label": "Counter", "fieldtype": "Data", "width": 120},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "check_in_time", "label": "Check In", "fieldtype": "Datetime", "width": 150},
		{"fieldname": "wait_time_mins", "label": "Wait (min)", "fieldtype": "Float", "width": 100},
		{"fieldname": "service_duration_mins", "label": "Service (min)", "fieldtype": "Float", "width": 100},
	]

def get_data(filters):
	conditions = "WHERE qt.token_date BETWEEN %(from_date)s AND %(to_date)s"
	if filters.get("location"):
		conditions += " AND qt.location = %(location)s"
	if filters.get("service"):
		conditions += " AND qt.service = %(service)s"

	return frappe.db.sql(f"""
		SELECT qt.ticket_number, qt.patient_name,
		       IFNULL(s.service_name, qt.service) as service,
		       IFNULL(l.location_name, qt.location) as location,
		       IFNULL(c.counter_name, qt.counter) as counter,
		       qt.status, qt.check_in_time,
		       qt.wait_time_mins, qt.service_duration_mins
		FROM `tabQMS Queue Ticket` qt
		LEFT JOIN `tabQMS Service` s ON s.name = qt.service
		LEFT JOIN `tabQMS Location` l ON l.name = qt.location
		LEFT JOIN `tabQMS Counter` c ON c.name = qt.counter
		{conditions}
		ORDER BY qt.check_in_time DESC
	""", filters, as_dict=1)
