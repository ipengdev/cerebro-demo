import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint


# Prefix used to identify auto-created records
_PREFIX = "LB -"


class LebanesePayrollSettings(Document):
	def validate(self):
		self.transport_allowance_monthly = flt(self.transport_allowance_daily) * cint(
			self.working_days_per_month or 22
		)


# ---------------------------------------------------------------------------
# Salary Components definitions
# ---------------------------------------------------------------------------
SALARY_COMPONENTS = [
	{
		"salary_component": "Basic Salary",
		"salary_component_abbr": "BS",
		"type": "Earning",
		"is_tax_applicable": 1,
		"depends_on_payment_days": 1,
	},
	{
		"salary_component": "Transport Allowance",
		"salary_component_abbr": "TA",
		"type": "Earning",
		"exempted_from_income_tax": 1,
		"is_tax_applicable": 0,
		"depends_on_payment_days": 1,
	},
	{
		"salary_component": "Schooling Allowance",
		"salary_component_abbr": "SA",
		"type": "Earning",
		"exempted_from_income_tax": 1,
		"is_tax_applicable": 0,
		"depends_on_payment_days": 0,
	},
	{
		"salary_component": "CNSS Employee - Sickness (2%)",
		"salary_component_abbr": "CNSS-ES",
		"type": "Deduction",
		"is_tax_applicable": 0,
		"exempted_from_income_tax": 1,
		"depends_on_payment_days": 0,
		"description": "Employee CNSS sickness contribution (2% of capped salary)",
	},
	{
		"salary_component": "CNSS Employee - Maternity (1%)",
		"salary_component_abbr": "CNSS-EM",
		"type": "Deduction",
		"is_tax_applicable": 0,
		"exempted_from_income_tax": 1,
		"depends_on_payment_days": 0,
		"description": "Employee CNSS maternity contribution (1% of capped salary)",
	},
	{
		"salary_component": "Income Tax",
		"salary_component_abbr": "IT",
		"type": "Deduction",
		"is_income_tax_component": 1,
		"variable_based_on_taxable_salary": 1,
		"depends_on_payment_days": 0,
		"is_tax_applicable": 0,
		"description": "Lebanese progressive income tax deduction",
	},
	{
		"salary_component": "CNSS Employer - Sickness (7%)",
		"salary_component_abbr": "CNSS-SM",
		"type": "Deduction",
		"statistical_component": 1,
		"do_not_include_in_total": 1,
		"depends_on_payment_days": 0,
		"is_tax_applicable": 0,
		"description": "Employer sickness contribution (7% of capped salary)",
	},
	{
		"salary_component": "CNSS Employer - Maternity (1%)",
		"salary_component_abbr": "CNSS-MT",
		"type": "Deduction",
		"statistical_component": 1,
		"do_not_include_in_total": 1,
		"depends_on_payment_days": 0,
		"is_tax_applicable": 0,
		"description": "Employer maternity contribution (1% of capped salary)",
	},
	{
		"salary_component": "CNSS Employer - Family (6%)",
		"salary_component_abbr": "CNSS-FA",
		"type": "Deduction",
		"statistical_component": 1,
		"do_not_include_in_total": 1,
		"depends_on_payment_days": 0,
		"is_tax_applicable": 0,
		"description": "Employer family allowance contribution (6% of capped salary)",
	},
	{
		"salary_component": "CNSS Employer - EoS (8.5%)",
		"salary_component_abbr": "CNSS-EOS",
		"type": "Deduction",
		"statistical_component": 1,
		"do_not_include_in_total": 1,
		"depends_on_payment_days": 0,
		"is_tax_applicable": 0,
		"description": "Employer end-of-service contribution (8.5%, no ceiling)",
	},
]


def _get_settings():
	return frappe.get_single("Lebanese Payroll Settings")


# ---------------------------------------------------------------------------
# Create payroll data
# ---------------------------------------------------------------------------
@frappe.whitelist()
def create_payroll_data(company):
	frappe.only_for(["System Manager", "HR Manager"])

	settings = _get_settings()
	if not company:
		frappe.throw(_("Please select a Company."))

	currency = frappe.db.get_value("Company", company, "default_currency") or "LBP"

	created = []

	# 1. Salary Components
	for comp_def in SALARY_COMPONENTS:
		name = comp_def["salary_component"]
		if not frappe.db.exists("Salary Component", name):
			doc = frappe.new_doc("Salary Component")
			doc.update(comp_def)
			doc.insert(ignore_permissions=True)
			created.append(f"Salary Component: {name}")

	# 2. Income Tax Slab
	slab_name = f"{_PREFIX} Income Tax Slab - {company}"
	if not frappe.db.exists("Income Tax Slab", slab_name):
		slab = frappe.new_doc("Income Tax Slab")
		slab.name1 = slab_name  # prompt naming
		slab.__newname = slab_name
		slab.effective_from = "2022-01-01"
		slab.company = company
		slab.currency = currency
		slab.allow_tax_exemption = 1
		slab.standard_tax_exemption_amount = flt(settings.personal_allowance)

		for row in settings.tax_slabs or []:
			slab.append(
				"slabs",
				{
					"from_amount": flt(row.from_amount),
					"to_amount": flt(row.to_amount) if flt(row.to_amount) > 0 else 0,
					"percent_deduction": flt(row.rate),
				},
			)

		slab.insert(ignore_permissions=True)
		slab.submit()
		created.append(f"Income Tax Slab: {slab_name}")

	# 3. Payroll Constants
	pc_title = f"{_PREFIX} Payroll Constants - {company}"
	if not frappe.db.exists("Payroll Constants", pc_title):
		pc = frappe.new_doc("Payroll Constants")
		pc.title = pc_title
		pc.company = company
		pc.effective_from = "2022-01-01"
		pc.is_active = 1

		# CNSS rates from settings (split sickness/maternity)
		pc.employer_nssf_sickness_percentage = flt(settings.cnss_employer_sickness_rate)
		pc.employer_nssf_maternity_percentage = flt(settings.cnss_employer_maternity_rate)
		pc.employer_nssf_medical_percentage = (
			flt(settings.cnss_employer_sickness_rate)
			+ flt(settings.cnss_employer_maternity_rate)
		)
		pc.employer_nssf_family_percentage = flt(settings.cnss_employer_family_rate)
		pc.employer_nssf_eos_percentage = flt(settings.cnss_employer_eos_rate)

		pc.employee_nssf_sickness_percentage = flt(settings.cnss_employee_sickness_rate)
		pc.employee_nssf_maternity_percentage = flt(settings.cnss_employee_maternity_rate)
		pc.employee_nssf_medical_percentage = (
			flt(settings.cnss_employee_sickness_rate)
			+ flt(settings.cnss_employee_maternity_rate)
		)

		pc.medical_maternity_contributions_ceiling = flt(settings.cnss_medical_ceiling)
		pc.family_allowance_contributions_ceiling = flt(settings.cnss_family_ceiling)

		# Tax allowances from settings
		pc.tax_personal_allowance = flt(settings.personal_allowance)
		pc.tax_spouse_allowance = flt(settings.spouse_allowance)
		pc.tax_child_allowance = flt(settings.child_allowance)
		pc.tax_education_allowance = 0  # covered by schooling allowance
		pc.max_children_deduction = cint(settings.max_children_deduction)

		# Allowances
		pc.transport_allowance = flt(settings.transport_allowance_monthly)
		pc.meal_allowance = 0

		pc.insert(ignore_permissions=True)
		created.append(f"Payroll Constants: {pc_title}")

	# 4. Salary Structure
	ss_name = f"{_PREFIX} Salary Structure - {company}"
	if not frappe.db.exists("Salary Structure", ss_name):
		ss = frappe.new_doc("Salary Structure")
		ss.__newname = ss_name
		ss.company = company
		ss.is_active = "Yes"
		ss.is_default = "No"
		ss.payroll_frequency = "Monthly"
		ss.currency = currency

		# Earnings
		ss.append(
			"earnings",
			{
				"salary_component": "Basic Salary",
				"abbr": "BS",
				"amount_based_on_formula": 1,
				"formula": "base",
				"amount": 0,
			},
		)
		ss.append(
			"earnings",
			{
				"salary_component": "Transport Allowance",
				"abbr": "TA",
				"amount_based_on_formula": 1,
				"formula": f"{flt(settings.transport_allowance_monthly)}",
				"exempted_from_income_tax": 1,
			},
		)

		# Deductions — split employee CNSS into sickness + maternity
		medical_ceiling = flt(settings.cnss_medical_ceiling)
		employee_sickness_rate = flt(settings.cnss_employee_sickness_rate)
		employee_maternity_rate = flt(settings.cnss_employee_maternity_rate)
		ss.append(
			"deductions",
			{
				"salary_component": "CNSS Employee - Sickness (2%)",
				"abbr": "CNSS-ES",
				"amount_based_on_formula": 1,
				"formula": f"(base if base < {medical_ceiling} else {medical_ceiling}) * {employee_sickness_rate} / 100",
			},
		)
		ss.append(
			"deductions",
			{
				"salary_component": "CNSS Employee - Maternity (1%)",
				"abbr": "CNSS-EM",
				"amount_based_on_formula": 1,
				"formula": f"(base if base < {medical_ceiling} else {medical_ceiling}) * {employee_maternity_rate} / 100",
			},
		)
		ss.append(
			"deductions",
			{
				"salary_component": "Income Tax",
				"abbr": "IT",
				"variable_based_on_taxable_salary": 1,
				"amount_based_on_formula": 0,
				"amount": 0,
			},
		)

		ss.insert(ignore_permissions=True)
		ss.submit()
		created.append(f"Salary Structure: {ss_name}")

	# Mark data as created
	frappe.db.set_single_value("Lebanese Payroll Settings", "data_created", 1)
	frappe.db.commit()

	if created:
		msg = _("Successfully created:") + "<br><ul>"
		for item in created:
			msg += f"<li>{item}</li>"
		msg += "</ul>"
	else:
		msg = _("All payroll data already exists. No new records created.")

	return msg


# ---------------------------------------------------------------------------
# Clear payroll data
# ---------------------------------------------------------------------------
@frappe.whitelist()
def clear_payroll_data(company):
	frappe.only_for("System Manager")

	if not company:
		frappe.throw(_("Please select a Company."))

	deleted = []

	# 1. Salary Structure (cancel first, then delete)
	ss_name = f"{_PREFIX} Salary Structure - {company}"
	if frappe.db.exists("Salary Structure", ss_name):
		# Check for Salary Structure Assignments
		assignments = frappe.get_all(
			"Salary Structure Assignment",
			filters={"salary_structure": ss_name, "docstatus": 1},
			pluck="name",
		)
		for ssa in assignments:
			frappe.get_doc("Salary Structure Assignment", ssa).cancel()
			frappe.delete_doc("Salary Structure Assignment", ssa, force=True)

		doc = frappe.get_doc("Salary Structure", ss_name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Salary Structure", ss_name, force=True)
		deleted.append(f"Salary Structure: {ss_name}")

	# 2. Income Tax Slab (cancel first, then delete)
	slab_name = f"{_PREFIX} Income Tax Slab - {company}"
	if frappe.db.exists("Income Tax Slab", slab_name):
		doc = frappe.get_doc("Income Tax Slab", slab_name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Income Tax Slab", slab_name, force=True)
		deleted.append(f"Income Tax Slab: {slab_name}")

	# 3. Payroll Constants
	pc_title = f"{_PREFIX} Payroll Constants - {company}"
	if frappe.db.exists("Payroll Constants", pc_title):
		frappe.delete_doc("Payroll Constants", pc_title, force=True)
		deleted.append(f"Payroll Constants: {pc_title}")

	# 4. Salary Components (only delete if no salary slips reference them)
	for comp_def in SALARY_COMPONENTS:
		name = comp_def["salary_component"]
		if frappe.db.exists("Salary Component", name):
			has_slips = frappe.db.exists(
				"Salary Detail", {"salary_component": name, "parenttype": "Salary Slip"}
			)
			if not has_slips:
				frappe.delete_doc("Salary Component", name, force=True)
				deleted.append(f"Salary Component: {name}")
			else:
				deleted.append(
					f"Salary Component: {name} (kept - referenced by Salary Slips)"
				)

	# Unmark
	frappe.db.set_single_value("Lebanese Payroll Settings", "data_created", 0)
	frappe.db.commit()

	if deleted:
		msg = _("Successfully cleared:") + "<br><ul>"
		for item in deleted:
			msg += f"<li>{item}</li>"
		msg += "</ul>"
	else:
		msg = _("No payroll data found to clear.")

	return msg
