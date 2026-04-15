"""CNSS Official Forms — PDF Generation.

Generates printable PDF versions of the official CNSS forms:
- CNSS 190A: جدول الاشتراكات المستحقة (Monthly Contributions Table)
- CNSS 351:  جدول الاشتراكات المتوجبة — التصريح الاسمي السنوي (Annual Contributions)
- CNSS 2M:   إفادة عمل (Work Certificate — Sickness & Maternity)
- إشعار ترك العمل (Employee Leaving Notice)

Uses overlay on official blank CNSS PDF forms (190A, 351, 2M).
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months

MONTH_NAMES_AR = {
	1: "كانون الثاني",
	2: "شباط",
	3: "آذار",
	4: "نيسان",
	5: "أيار",
	6: "حزيران",
	7: "تموز",
	8: "آب",
	9: "أيلول",
	10: "تشرين الأول",
	11: "تشرين الثاني",
	12: "كانون الأول",
}


def _get_company_info(company):
	"""Load company name, tax_id, address, phone for PDF header."""
	comp = frappe.get_doc("Company", company)

	addr = frappe.db.sql("""
		SELECT a.address_line1, a.address_line2, a.city, a.state, a.phone
		FROM tabAddress a
		JOIN `tabDynamic Link` dl ON dl.parent = a.name AND dl.parenttype = 'Address'
		WHERE dl.link_doctype = 'Company' AND dl.link_name = %s
		LIMIT 1
	""", company, as_dict=True)

	if addr:
		a = addr[0]
		address_str = ", ".join(filter(None, [a.address_line1, a.address_line2, a.city, a.state]))
		phone = a.phone or ""
	else:
		address_str = ""
		phone = ""

	return {
		"company_name": comp.company_name,
		"tax_id": comp.tax_id or "",
		"address": address_str,
		"phone": phone,
	}


# ════════════════════════════════════════════════════════════════
#  CNSS 190A — Monthly Contributions Table
# ════════════════════════════════════════════════════════════════

@frappe.whitelist()
def generate_cnss_monthly_pdf(company, month, year):
	"""Generate CNSS 190A monthly contributions PDF."""
	from amo.amo_payroll.report.cnss_monthly_declaration.cnss_monthly_declaration import (
		get_data, validate_filters,
	)

	month = int(month)
	year = int(year)

	filters = frappe._dict({"company": company, "month": month, "year": year})
	validate_filters(filters)
	data = get_data(filters)

	if not data:
		frappe.throw(_("No data found for the selected period"))

	# Compute totals matching CNSS 190A form structure
	totals = {
		"gross": sum(flt(d["gross_salary"]) for d in data),
		"medical_capped": sum(flt(d["capped_salary"]) for d in data),
		"family_capped": sum(flt(d["family_capped"]) for d in data),
		"ee_sickness": sum(flt(d["ee_sickness"]) for d in data),
		"ee_maternity": sum(flt(d["ee_maternity"]) for d in data),
		"er_sickness": sum(flt(d["er_sickness"]) for d in data),
		"er_maternity": sum(flt(d["er_maternity"]) for d in data),
		"employer_family": sum(flt(d["employer_family"]) for d in data),
		"employer_eos": sum(flt(d["employer_eos"]) for d in data),
		"total_cnss": sum(flt(d["total_cnss"]) for d in data),
	}
	totals["total_ee"] = totals["ee_sickness"] + totals["ee_maternity"]
	totals["total_er"] = (
		totals["er_sickness"] + totals["er_maternity"]
		+ totals["employer_family"] + totals["employer_eos"]
	)
	# Branch 3 (المرض والأمومة): 9% = EE sickness + EE maternity + ER sickness + ER maternity
	totals["branch3_due"] = (
		totals["ee_sickness"] + totals["ee_maternity"]
		+ totals["er_sickness"] + totals["er_maternity"]
	)

	company_info = _get_company_info(company)
	month_name = MONTH_NAMES_AR.get(month, str(month))

	from .pdf_cnss_190a import build_cnss_190a
	pdf = build_cnss_190a({
		**company_info,
		"month_name": month_name,
		"year": year,
		"employees": data,
		"totals": totals,
		"employee_count": len(data),
	})

	frappe.local.response.filename = f"CNSS_190A_{year}_{month:02d}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  CNSS 351 — Annual Contributions Table
# ════════════════════════════════════════════════════════════════

@frappe.whitelist()
def generate_cnss_yearly_pdf(company, year):
	"""Generate CNSS 351 annual contributions PDF."""
	from amo.amo_payroll.report.cnss_yearly_declaration.cnss_yearly_declaration import (
		get_data, validate_filters,
	)

	year = int(year)

	filters = frappe._dict({"company": company, "year": year})
	validate_filters(filters)
	data = get_data(filters)

	if not data:
		frappe.throw(_("No data found for the selected year"))

	totals = {
		"gross": sum(flt(d["annual_gross"]) for d in data),
		"medical_capped": sum(flt(d["annual_medical_capped"]) for d in data),
		"family_capped": sum(flt(d["annual_family_capped"]) for d in data),
		"ee_sickness": sum(flt(d["ee_sickness"]) for d in data),
		"ee_maternity": sum(flt(d["ee_maternity"]) for d in data),
		"er_sickness": sum(flt(d["er_sickness"]) for d in data),
		"er_maternity": sum(flt(d["er_maternity"]) for d in data),
		"employer_family": sum(flt(d["employer_family"]) for d in data),
		"employer_eos": sum(flt(d["employer_eos"]) for d in data),
		"total_er": sum(flt(d["total_employer"]) for d in data),
		"total_cnss": sum(flt(d["total_cnss"]) for d in data),
	}
	totals["total_ee"] = totals["ee_sickness"] + totals["ee_maternity"]
	# Branch 3 (المرض والأمومة): 9%
	totals["branch3_due"] = (
		totals["ee_sickness"] + totals["ee_maternity"]
		+ totals["er_sickness"] + totals["er_maternity"]
	)

	company_info = _get_company_info(company)

	from .pdf_cnss_351 import build_cnss_351
	pdf = build_cnss_351({
		**company_info,
		"year": year,
		"employees": data,
		"totals": totals,
		"employee_count": len(data),
	})

	frappe.local.response.filename = f"CNSS_351_{year}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  CNSS 2M — إفادة عمل (Work Certificate)
# ════════════════════════════════════════════════════════════════

@frappe.whitelist()
def generate_employee_joining_pdf(company, from_date, to_date, department=None, employee=None):
	"""Generate CNSS 2M work certificate forms PDF."""
	from amo.amo_payroll.report.employee_joining_report.employee_joining_report import (
		get_data, validate_filters,
	)

	filters = frappe._dict({
		"company": company,
		"from_date": from_date,
		"to_date": to_date,
	})
	if department:
		filters["department"] = department
	if employee:
		filters["employee"] = employee

	validate_filters(filters)
	data = get_data(filters)

	if not data:
		frappe.throw(_("لا يوجد أجراء للفترة المحددة"))

	company_info = _get_company_info(company)

	# Enrich each employee with CNSS 2M data:
	# - monthly_data: last 6 months work breakdown
	# - last_3m_salaries: last 3 months salary detail
	# - last_3m_total: sum of last 3 months
	for emp in data:
		emp_id = emp.get("employee")
		joining = emp.get("date_of_joining")

		# Get last 6 months salary slips for this employee
		six_months_ago = add_months(to_date, -6)
		slips = frappe.get_all(
			"Salary Slip",
			filters={
				"employee": emp_id,
				"docstatus": 1,
				"start_date": (">=", six_months_ago),
				"end_date": ("<=", to_date),
			},
			fields=["start_date", "end_date", "gross_pay", "total_working_days"],
			order_by="start_date asc",
		)

		monthly_data = []
		for ss in slips:
			m = getdate(ss.start_date).month
			monthly_data.append({
				"month_name": MONTH_NAMES_AR.get(m, str(m)),
				"days_worked": ss.total_working_days or 26,
				"from_date": ss.start_date,
				"to_date": ss.end_date,
			})
		emp["monthly_data"] = monthly_data
		emp["months_worked"] = len(monthly_data)

		# Last 3 months salaries
		last_3 = slips[-3:] if len(slips) >= 3 else slips
		last_3m_salaries = []
		total_3m = 0
		for ss in last_3:
			m = getdate(ss.start_date).month
			last_3m_salaries.append({
				"month_name": MONTH_NAMES_AR.get(m, str(m)),
				"amount": flt(ss.gross_pay),
			})
			total_3m += flt(ss.gross_pay)
		emp["last_3m_salaries"] = last_3m_salaries
		emp["last_3m_total"] = total_3m
		emp["salary_continued"] = True  # Default assumption

	from .pdf_cnss_2m import build_cnss_2m
	pdf = build_cnss_2m({
		**company_info,
		"employees": data,
	})

	frappe.local.response.filename = f"CNSS_2M_{from_date}_to_{to_date}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  إشعار ترك العمل — Employee Leaving Notice
# ════════════════════════════════════════════════════════════════

@frappe.whitelist()
def generate_employee_leaving_pdf(company, from_date, to_date, department=None, employee=None):
	"""Generate CNSS employee leaving notice forms PDF."""
	from amo.amo_payroll.report.employee_leaving_report.employee_leaving_report import (
		get_data, validate_filters,
	)

	filters = frappe._dict({
		"company": company,
		"from_date": from_date,
		"to_date": to_date,
	})
	if department:
		filters["department"] = department
	if employee:
		filters["employee"] = employee

	validate_filters(filters)
	data = get_data(filters)

	if not data:
		frappe.throw(_("لا يوجد أجراء للفترة المحددة"))

	company_info = _get_company_info(company)

	from .pdf_cnss_leaving import build_cnss_leaving
	pdf = build_cnss_leaving({
		**company_info,
		"employees": data,
	})

	frappe.local.response.filename = f"CNSS_Leaving_{from_date}_to_{to_date}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"
	frappe.local.response.type = "pdf"
