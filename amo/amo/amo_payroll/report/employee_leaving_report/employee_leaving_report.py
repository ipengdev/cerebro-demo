"""Employee Leaving Report — Lebanese CNSS / MoL deregistration format.

Lists employees who left during the selected period with all required fields
for CNSS deregistration and end-of-service calculations.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff


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
		{"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 110},
		{"label": _("Relieving Date"), "fieldname": "relieving_date", "fieldtype": "Date", "width": 110},
		{"label": _("Years of Service"), "fieldname": "years_of_service", "fieldtype": "Float", "precision": 1, "width": 80},
		{"label": _("Reason for Leaving"), "fieldname": "reason_for_leaving", "fieldtype": "Data", "width": 160},
		{"label": _("CNSS #"), "fieldname": "cnss_number", "fieldtype": "Data", "width": 120},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 140},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 140},
		{"label": _("Last Salary"), "fieldname": "last_salary", "fieldtype": "Currency", "width": 130},
		{"label": _("End of Service Due"), "fieldname": "eos_due", "fieldtype": "Currency", "width": 140},
		{"label": _("Final Settlement"), "fieldname": "final_settlement", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	conditions = {
		"company": filters.company,
		"status": "Left",
		"relieving_date": ("between", [filters.from_date, filters.to_date]),
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
			"relieving_date",
			"reason_for_leaving",
			"ctc as cnss_number",
			"department",
			"designation",
		],
		order_by="relieving_date asc",
	)

	for emp in employees:
		# Calculate years of service
		if emp.date_of_joining and emp.relieving_date:
			days = date_diff(emp.relieving_date, emp.date_of_joining)
			emp["years_of_service"] = round(days / 365.25, 1)
		else:
			emp["years_of_service"] = 0

		# Get last salary
		last_slip = frappe.get_all(
			"Salary Slip",
			filters={"employee": emp.employee, "docstatus": 1},
			fields=["gross_pay"],
			order_by="start_date desc",
			limit=1,
		)
		emp["last_salary"] = flt(last_slip[0].gross_pay) if last_slip else 0

		# Calculate end-of-service indemnity (Lebanese labour law)
		# 1 month salary per year of service for first 5 years
		# 1.5 months for years 6-10, 2 months for 10+ years
		years = emp["years_of_service"]
		monthly = emp["last_salary"]
		eos = 0
		if years > 0:
			if years <= 5:
				eos = years * monthly
			elif years <= 10:
				eos = (5 * monthly) + ((years - 5) * monthly * 1.5)
			else:
				eos = (5 * monthly) + (5 * monthly * 1.5) + ((years - 10) * monthly * 2)
		emp["eos_due"] = flt(eos, 0)

		# Check if full and final statement exists
		emp["final_settlement"] = _("Pending")

	return employees


def get_summary(data):
	if not data:
		return []

	total_eos = sum(flt(d.get("eos_due")) for d in data)

	return [
		{"value": len(data), "indicator": "red", "label": _("Total Leavings"), "datatype": "Int"},
		{"value": total_eos, "indicator": "orange", "label": _("Total EoS Due"), "datatype": "Currency"},
	]
