"""Shared utilities for Lebanese Ministry of Finance (MoF) reports.

Lebanese income tax slabs (as per 2022 Budget Law, Article 57 Income Tax Law):
- 0 to 18,000,000 LBP: 2%
- 18,000,001 to 45,000,000 LBP: 4%
- 45,000,001 to 90,000,000 LBP: 7%
- 90,000,001 to 180,000,000 LBP: 11%
- 180,000,001 to 360,000,000 LBP: 15%
- 360,000,001 to 675,000,000 LBP: 20%
- Over 675,000,000 LBP: 25%

Personal deductions (2024 Budget Law, Article 49):
- Personal: 450,000,000 LBP/year
- Spouse: 225,000,000 LBP/year
- Per child: 45,000,000 LBP/year (max 5)
"""

from frappe.utils import flt

# Default Lebanese Income Tax Slabs (2022 Budget Law)
LEBANESE_TAX_SLABS = [
	(18_000_000, 0.02),
	(45_000_000, 0.04),
	(90_000_000, 0.07),
	(180_000_000, 0.11),
	(360_000_000, 0.15),
	(675_000_000, 0.20),
	(float("inf"), 0.25),
]


def get_tax_slabs_from_settings():
	"""Load tax slabs from Lebanese Payroll Settings if available."""
	import frappe

	try:
		settings = frappe.get_single("Lebanese Payroll Settings")
		if settings and settings.tax_slabs:
			slabs = []
			for row in settings.tax_slabs:
				limit = flt(row.to_amount) if flt(row.to_amount) > 0 else float("inf")
				slabs.append((limit, flt(row.rate) / 100))
			if slabs:
				return slabs
	except Exception:
		pass
	return LEBANESE_TAX_SLABS


def compute_annual_tax(taxable_income, tax_slabs=None):
	"""Compute Lebanese progressive income tax on annual taxable income."""
	if not tax_slabs:
		tax_slabs = get_tax_slabs_from_settings()

	tax = 0
	prev_limit = 0
	remaining = flt(taxable_income)

	if remaining <= 0:
		return 0

	for limit, rate in tax_slabs:
		bracket = min(remaining, limit - prev_limit)
		if bracket <= 0:
			break
		tax += bracket * rate
		remaining -= bracket
		prev_limit = limit

	return flt(tax, 0)


def get_employee_tax_deductions(employee, constants):
	"""Calculate total annual tax deductions for an employee based on family status."""
	import frappe

	marital_status = frappe.db.get_value("Employee", employee, "marital_status") or ""
	# Try to get number of children from custom field or default to 0
	number_of_children = 0
	try:
		number_of_children = int(frappe.db.get_value("Employee", employee, "number_of_dependent_children") or 0)
	except Exception:
		pass

	personal = flt(constants.tax_personal_allowance) if constants else 450_000_000
	spouse = flt(constants.tax_spouse_allowance) if constants else 225_000_000
	per_child = flt(constants.tax_child_allowance) if constants else 45_000_000
	edu_per_child = flt(constants.tax_education_allowance) if constants else 0
	max_children = int(constants.max_children_deduction) if constants else 5

	total_deduction = personal

	if marital_status in ("Married", "متزوج"):
		total_deduction += spouse

	children = min(number_of_children, max_children)
	total_deduction += children * per_child
	total_deduction += children * edu_per_child

	return total_deduction


def get_mof_filters_js():
	"""Standard JS filters for MoF reports."""
	return """
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "year",
			label: __("Fiscal Year"),
			fieldtype: "Select",
			options: (() => {
				let years = [];
				let current = new Date().getFullYear();
				for (let y = current; y >= current - 5; y--) years.push(y);
				return years;
			})(),
			reqd: 1,
			default: new Date().getFullYear(),
		},
	]"""
