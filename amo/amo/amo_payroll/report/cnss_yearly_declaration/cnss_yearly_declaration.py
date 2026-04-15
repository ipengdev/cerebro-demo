"""CNSS Yearly Declaration Report — Lebanese Social Security Annual Summary.

Aggregates the full year CNSS contributions per employee for the annual NSSF filing.
Shows monthly breakdown and annual totals per employee.
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
	summary = get_summary(data)
	return columns, data, None, chart, summary


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Please select a Company"))
	if not filters.get("year"):
		frappe.throw(_("Please select a Year"))


def get_columns():
	return [
		{"label": _("CNSS #"), "fieldname": "cnss_number", "fieldtype": "Data", "width": 120},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 100},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Months Worked"), "fieldname": "months_worked", "fieldtype": "Int", "width": 80},
		{"label": _("Annual Gross"), "fieldname": "annual_gross", "fieldtype": "Currency", "width": 140},
		{"label": _("Medical Capped"), "fieldname": "annual_medical_capped", "fieldtype": "Currency", "width": 140},
		{"label": _("EE Sickness"), "fieldname": "ee_sickness", "fieldtype": "Currency", "width": 120},
		{"label": _("EE Maternity"), "fieldname": "ee_maternity", "fieldtype": "Currency", "width": 120},
		{"label": _("ER Sickness"), "fieldname": "er_sickness", "fieldtype": "Currency", "width": 120},
		{"label": _("ER Maternity"), "fieldname": "er_maternity", "fieldtype": "Currency", "width": 120},
		{"label": _("ER Family"), "fieldname": "employer_family", "fieldtype": "Currency", "width": 120},
		{"label": _("ER EoS"), "fieldname": "employer_eos", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Employer"), "fieldname": "total_employer", "fieldtype": "Currency", "width": 130},
		{"label": _("Total CNSS"), "fieldname": "total_cnss", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	year = int(filters.year)
	company = filters.company

	start_date = f"{year}-01-01"
	end_date = f"{year}-12-31"

	constants = PayrollConstants.get_active_constants(company, start_date)
	if not constants:
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

	salary_slips = frappe.get_all(
		"Salary Slip",
		filters={
			"company": company,
			"start_date": (">=", start_date),
			"end_date": ("<=", end_date),
			"docstatus": 1,
		},
		fields=["employee", "employee_name", "gross_pay", "start_date"],
		order_by="employee_name asc, start_date asc",
	)

	employees = {
		e.name: e for e in frappe.get_all(
			"Employee",
			filters={"company": company},
			fields=["name", "ctc as cnss_number"],
		)
	}

	# Aggregate by employee
	employee_data = {}
	for ss in salary_slips:
		key = ss.employee
		if key not in employee_data:
			emp_info = employees.get(key, frappe._dict())
			employee_data[key] = {
				"cnss_number": emp_info.get("cnss_number", ""),
				"employee": ss.employee,
				"employee_name": ss.employee_name,
				"months_worked": 0,
				"annual_gross": 0,
				"annual_medical_capped": 0,
				"annual_family_capped": 0,
				"ee_sickness": 0,
				"ee_maternity": 0,
				"er_sickness": 0,
				"er_maternity": 0,
				"employer_family": 0,
				"employer_eos": 0,
				"total_employer": 0,
				"total_cnss": 0,
			}

		gross = flt(ss.gross_pay)
		med_capped = min(gross, medical_ceiling) if medical_ceiling else gross
		fam_capped = min(gross, family_ceiling) if family_ceiling else gross

		ee_sick = flt(med_capped * ee_sickness_rate / 100, 0)
		ee_mat = flt(med_capped * ee_maternity_rate / 100, 0)
		er_sick = flt(med_capped * er_sickness_rate / 100, 0)
		er_mat = flt(med_capped * er_maternity_rate / 100, 0)
		er_fam = flt(fam_capped * er_family_rate / 100, 0)
		er_eos = flt(gross * er_eos_rate / 100, 0)
		total_ee = ee_sick + ee_mat
		total_er = er_sick + er_mat + er_fam + er_eos

		employee_data[key]["months_worked"] += 1
		employee_data[key]["annual_gross"] += gross
		employee_data[key]["annual_medical_capped"] += med_capped
		employee_data[key]["annual_family_capped"] += fam_capped
		employee_data[key]["ee_sickness"] += ee_sick
		employee_data[key]["ee_maternity"] += ee_mat
		employee_data[key]["er_sickness"] += er_sick
		employee_data[key]["er_maternity"] += er_mat
		employee_data[key]["employer_family"] += er_fam
		employee_data[key]["employer_eos"] += er_eos
		employee_data[key]["total_employer"] += total_er
		employee_data[key]["total_cnss"] += total_ee + total_er

	return sorted(employee_data.values(), key=lambda d: d["employee_name"])


def get_chart(data):
	if not data:
		return None

	labels = [d["employee_name"][:20] for d in data[:15]]
	ee_vals = [flt(d["ee_sickness"]) + flt(d["ee_maternity"]) for d in data[:15]]
	er_vals = [flt(d["total_employer"]) for d in data[:15]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Employee CNSS"), "values": ee_vals},
				{"name": _("Employer CNSS"), "values": er_vals},
			],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
	}


def get_summary(data):
	if not data:
		return []

	total_gross = sum(flt(d.get("annual_gross")) for d in data)
	total_ee = sum(flt(d.get("ee_sickness")) + flt(d.get("ee_maternity")) for d in data)
	total_er = sum(flt(d.get("total_employer")) for d in data)
	total_all = sum(flt(d.get("total_cnss")) for d in data)

	return [
		{"value": len(data), "indicator": "blue", "label": _("Employees"), "datatype": "Int"},
		{"value": total_gross, "indicator": "blue", "label": _("Total Annual Gross"), "datatype": "Currency"},
		{"value": total_ee, "indicator": "orange", "label": _("Total Employee CNSS"), "datatype": "Currency"},
		{"value": total_er, "indicator": "red", "label": _("Total Employer CNSS"), "datatype": "Currency"},
		{"value": total_all, "indicator": "red", "label": _("Grand Total CNSS"), "datatype": "Currency"},
	]
