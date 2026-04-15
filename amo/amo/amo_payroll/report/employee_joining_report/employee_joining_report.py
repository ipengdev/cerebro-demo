"""Employee Joining Report — Lebanese CNSS / MoL notification format.

Lists employees who joined during the selected period with all required fields
for CNSS registration and Ministry of Labour notifications.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	return columns, data, None, None, summary


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Please select a Company"))
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("Please select From Date and To Date"))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 100},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 120},
		{"label": _("Date of Birth"), "fieldname": "date_of_birth", "fieldtype": "Date", "width": 110},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 80},
		{"label": _("Nationality"), "fieldname": "nationality", "fieldtype": "Data", "width": 100},
		{"label": _("Marital Status"), "fieldname": "marital_status", "fieldtype": "Data", "width": 100},
		{"label": _("CNSS #"), "fieldname": "cnss_number", "fieldtype": "Data", "width": 120},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 140},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 140},
		{"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Data", "width": 120},
		{"label": _("Basic Salary"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 130},
		{"label": _("Phone"), "fieldname": "emergency_phone_number", "fieldtype": "Data", "width": 120},
		{"label": _("Personal Email"), "fieldname": "personal_email", "fieldtype": "Data", "width": 180},
	]


def get_data(filters):
	conditions = {
		"company": filters.company,
		"date_of_joining": ("between", [filters.from_date, filters.to_date]),
	}
	if filters.get("department"):
		conditions["department"] = filters.department
	if filters.get("employee"):
		conditions["name"] = filters.employee

	employees = frappe.get_all(
		"Employee",
		filters=conditions,
		fields=[
			"name as employee",
			"employee_name",
			"date_of_joining",
			"date_of_birth",
			"gender",
			"ctc as cnss_number",
			"department",
			"designation",
			"employment_type",
			"emergency_phone_number",
			"personal_email",
			"marital_status",
		],
		order_by="date_of_joining asc",
	)

	# Get nationality from Employee doctype
	for emp in employees:
		nationality = frappe.db.get_value("Employee", emp.employee, "nationality")
		emp["nationality"] = nationality or ""

		# Get basic salary from latest salary structure assignment
		ssa = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": emp.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		emp["basic_salary"] = flt(ssa[0].base) if ssa else 0

	return employees


def get_summary(data):
	if not data:
		return []

	return [
		{"value": len(data), "indicator": "green", "label": _("Total New Joinings"), "datatype": "Int"},
		{"value": len([d for d in data if d.get("gender") == "Male"]), "indicator": "blue", "label": _("Male"), "datatype": "Int"},
		{"value": len([d for d in data if d.get("gender") == "Female"]), "indicator": "pink", "label": _("Female"), "datatype": "Int"},
	]
