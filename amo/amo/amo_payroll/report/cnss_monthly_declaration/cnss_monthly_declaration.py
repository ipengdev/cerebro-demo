"""CNSS Monthly Declaration Report — Lebanese Social Security (NSSF).

Generates the monthly CNSS declaration showing each employee's:
- Gross salary, capped salary (ceiling), employee & employer contributions
- Broken down by branch: Sickness & Maternity, Family, End of Service
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_first_day, get_last_day

from amo.amo_payroll.doctype.payroll_constants.payroll_constants import PayrollConstants


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data, filters)
	return columns, data, None, chart, summary


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Please select a Company"))
	if not filters.get("month"):
		frappe.throw(_("Please select a Month"))
	if not filters.get("year"):
		frappe.throw(_("Please select a Year"))


def get_columns():
	return [
		{"label": _("CNSS #"), "fieldname": "cnss_number", "fieldtype": "Data", "width": 120},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 100},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 140},
		{"label": _("Gross Salary"), "fieldname": "gross_salary", "fieldtype": "Currency", "width": 130},
		{"label": _("Medical Capped"), "fieldname": "capped_salary", "fieldtype": "Currency", "width": 130},
		{"label": _("Family Capped"), "fieldname": "family_capped", "fieldtype": "Currency", "width": 130},
		{"label": _("EE Sickness (2%)"), "fieldname": "ee_sickness", "fieldtype": "Currency", "width": 130},
		{"label": _("EE Maternity (1%)"), "fieldname": "ee_maternity", "fieldtype": "Currency", "width": 130},
		{"label": _("ER Sickness (7%)"), "fieldname": "er_sickness", "fieldtype": "Currency", "width": 130},
		{"label": _("ER Maternity (1%)"), "fieldname": "er_maternity", "fieldtype": "Currency", "width": 130},
		{"label": _("ER Family (6%)"), "fieldname": "employer_family", "fieldtype": "Currency", "width": 130},
		{"label": _("ER EoS (8.5%)"), "fieldname": "employer_eos", "fieldtype": "Currency", "width": 130},
		{"label": _("Total Employer"), "fieldname": "total_employer_cnss", "fieldtype": "Currency", "width": 140},
		{"label": _("Total CNSS"), "fieldname": "total_cnss", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	month = int(filters.month)
	year = int(filters.year)
	company = filters.company

	start_date = get_first_day(f"{year}-{month:02d}-01")
	end_date = get_last_day(f"{year}-{month:02d}-01")

	# Get active constants for this period
	constants = PayrollConstants.get_active_constants(company, start_date)
	if not constants:
		frappe.msgprint(_("No active Payroll Constants found for {0} on {1}").format(
			company, start_date
		))
		# Use defaults
		medical_ceiling = 120000000
		family_ceiling = 18000000
		ee_sickness_rate = 2.0
		ee_maternity_rate = 1.0
		er_sickness_rate = 7.0
		er_maternity_rate = 1.0
		er_family_rate = 6.0
		er_eos_rate = 8.5
	else:
		medical_ceiling = flt(constants.medical_maternity_contributions_ceiling) or 120000000
		family_ceiling = flt(constants.family_allowance_contributions_ceiling) or 18000000
		ee_sickness_rate = flt(constants.employee_nssf_sickness_percentage) or 2.0
		ee_maternity_rate = flt(constants.employee_nssf_maternity_percentage) or 1.0
		er_sickness_rate = flt(constants.employer_nssf_sickness_percentage) or 7.0
		er_maternity_rate = flt(constants.employer_nssf_maternity_percentage) or 1.0
		er_family_rate = flt(constants.employer_nssf_family_percentage) or 6.0
		er_eos_rate = flt(constants.employer_nssf_eos_percentage) or 8.5

	# Get salary slips for the period
	salary_slips = frappe.get_all(
		"Salary Slip",
		filters={
			"company": company,
			"start_date": (">=", start_date),
			"end_date": ("<=", end_date),
			"docstatus": 1,
		},
		fields=["employee", "employee_name", "department", "gross_pay", "start_date"],
		order_by="employee_name asc",
	)

	# Get CNSS numbers from Employee
	employees = {
		e.name: e for e in frappe.get_all(
			"Employee",
			filters={"company": company, "status": "Active"},
			fields=["name", "ctc as cnss_number", "department"],
		)
	}

	data = []
	for ss in salary_slips:
		gross = flt(ss.gross_pay)
		medical_capped = min(gross, medical_ceiling) if medical_ceiling else gross
		family_capped_val = min(gross, family_ceiling) if family_ceiling else gross

		# Employee pays on medical-capped salary
		ee_sick = flt(medical_capped * ee_sickness_rate / 100, 0)
		ee_mat = flt(medical_capped * ee_maternity_rate / 100, 0)

		# Employer sickness & maternity on medical-capped salary
		er_sick = flt(medical_capped * er_sickness_rate / 100, 0)
		er_mat = flt(medical_capped * er_maternity_rate / 100, 0)
		# Employer family on family-capped salary
		er_family = flt(family_capped_val * er_family_rate / 100, 0)
		# Employer EoS on uncapped gross (no ceiling)
		er_eos = flt(gross * er_eos_rate / 100, 0)

		total_ee = ee_sick + ee_mat
		total_er = er_sick + er_mat + er_family + er_eos
		total_cnss = total_ee + total_er

		emp_data = employees.get(ss.employee, frappe._dict())

		data.append({
			"cnss_number": emp_data.get("cnss_number", ""),
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"department": ss.department or emp_data.get("department", ""),
			"gross_salary": gross,
			"capped_salary": medical_capped,
			"family_capped": family_capped_val,
			"ee_sickness": ee_sick,
			"ee_maternity": ee_mat,
			"er_sickness": er_sick,
			"er_maternity": er_mat,
			"employer_family": er_family,
			"employer_eos": er_eos,
			"total_employer_cnss": total_er,
			"total_cnss": total_cnss,
		})

	return data


def get_chart(data):
	if not data:
		return None

	total_ee_sick = sum(flt(d.get("ee_sickness")) for d in data)
	total_ee_mat = sum(flt(d.get("ee_maternity")) for d in data)
	total_er_sick = sum(flt(d.get("er_sickness")) for d in data)
	total_er_mat = sum(flt(d.get("er_maternity")) for d in data)
	total_family = sum(flt(d.get("employer_family")) for d in data)
	total_eos = sum(flt(d.get("employer_eos")) for d in data)

	return {
		"data": {
			"labels": [
				_("EE Sickness"), _("EE Maternity"),
				_("ER Sickness"), _("ER Maternity"),
				_("ER Family"), _("ER EoS"),
			],
			"datasets": [{"values": [
				total_ee_sick, total_ee_mat,
				total_er_sick, total_er_mat,
				total_family, total_eos,
			]}],
		},
		"type": "bar",
		"colors": ["#5e64ff", "#8b8fff", "#ffa00a", "#ffc85e", "#29cd42", "#fc4f51"],
	}


def get_summary(data, filters):
	if not data:
		return []

	total_gross = sum(flt(d.get("gross_salary")) for d in data)
	total_ee = sum(flt(d.get("ee_sickness")) + flt(d.get("ee_maternity")) for d in data)
	total_er = sum(flt(d.get("total_employer_cnss")) for d in data)
	total_all = sum(flt(d.get("total_cnss")) for d in data)

	return [
		{"value": len(data), "indicator": "blue", "label": _("Employees"), "datatype": "Int"},
		{"value": total_gross, "indicator": "blue", "label": _("Total Gross"), "datatype": "Currency"},
		{"value": total_ee, "indicator": "orange", "label": _("Total Employee CNSS"), "datatype": "Currency"},
		{"value": total_er, "indicator": "red", "label": _("Total Employer CNSS"), "datatype": "Currency"},
		{"value": total_all, "indicator": "red", "label": _("Grand Total CNSS"), "datatype": "Currency"},
	]
