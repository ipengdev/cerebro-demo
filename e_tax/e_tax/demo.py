# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

"""
Demo data loader for e-Tax application.
Creates users, taxpayers, and sample declarations across all modules.

Usage:
    bench --site <site> execute e_tax.demo.load_demo_data
"""

import frappe
from frappe.utils import nowdate, add_days, add_months, getdate

DEMO_USERS = ["company@etax.demo", "person@etax.demo", "agent@etax.demo"]
DEMO_TINS = ["TIN-ENT-001", "TIN-ENT-002", "TIN-ENT-003", "TIN-IND-001", "TIN-IND-002"]


def load_demo_data():
	"""Main entry point: create everything."""
	frappe.flags.ignore_permissions = True
	try:
		create_users()
		create_taxpayers()
		configure_tax_settings()
		create_tax_rates()
		create_enterprise_declarations()
		create_vat_returns()
		create_personal_income_tax()
		create_customs_declarations()
		create_excise_duty_returns()
		frappe.db.commit()
		print("✓ Demo data loaded successfully!")
	finally:
		frappe.flags.ignore_permissions = False


def clear_demo_data():
	"""Remove all demo data created by load_demo_data."""
	frappe.flags.ignore_permissions = True
	try:
		# Get demo taxpayer names
		taxpayer_names = []
		for tin in DEMO_TINS:
			tp = frappe.db.get_value("Taxpayer", {"tax_identification_number": tin}, "name")
			if tp:
				taxpayer_names.append(tp)

		# Delete submittable documents linked to demo taxpayers (cancel first if submitted)
		for doctype in [
			"Enterprise Declaration",
			"VAT Return",
			"Personal Income Tax",
			"Customs Declaration",
			"Excise Duty Return",
		]:
			for tp in taxpayer_names:
				for doc_name in frappe.get_all(doctype, {"taxpayer": tp}, pluck="name"):
					doc = frappe.get_doc(doctype, doc_name)
					if doc.docstatus == 1:
						doc.flags.ignore_permissions = True
						doc.cancel()
					if doc.docstatus != 0:
						# reload after cancel
						doc = frappe.get_doc(doctype, doc_name)
					frappe.delete_doc(doctype, doc_name, force=True, ignore_permissions=True)
			print(f"  ✓ Cleared {doctype}")

		# Delete demo taxpayers
		for tp in taxpayer_names:
			frappe.delete_doc("Taxpayer", tp, force=True, ignore_permissions=True)
		print(f"  ✓ Cleared {len(taxpayer_names)} taxpayers")

		# Delete demo users
		for email in DEMO_USERS:
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		print(f"  ✓ Cleared demo users")

		# Delete demo tax rates
		for rate_name in frappe.get_all("Tax Rate", {"fiscal_year": "2026"}, pluck="name"):
			frappe.delete_doc("Tax Rate", rate_name, force=True, ignore_permissions=True)
		print("  ✓ Cleared tax rates")

		frappe.db.commit()
		print("✓ Demo data cleared successfully!")
	finally:
		frappe.flags.ignore_permissions = False


# ─── Users ────────────────────────────────────────────────────────────────────

def create_users():
	"""Create 3 demo users with different roles."""
	users = [
		{
			"email": "company@etax.demo",
			"first_name": "Entreprise",
			"last_name": "Dumoulin",
			"roles": ["Tax Filer"],
			"password": "Demo@1234",
		},
		{
			"email": "person@etax.demo",
			"first_name": "Jean-Claude",
			"last_name": "Mbeki",
			"roles": ["Tax Filer"],
			"password": "Demo@1234",
		},
		{
			"email": "agent@etax.demo",
			"first_name": "Marie",
			"last_name": "Ndongo",
			"roles": ["Tax Officer", "Customs Officer", "Tax Auditor"],
			"password": "Demo@1234",
		},
	]

	for u in users:
		if frappe.db.exists("User", u["email"]):
			print(f"  User {u['email']} already exists, skipping")
			continue

		user = frappe.new_doc("User")
		user.email = u["email"]
		user.first_name = u["first_name"]
		user.last_name = u["last_name"]
		user.enabled = 1
		user.new_password = u["password"]
		user.send_welcome_email = 0

		for role_name in u["roles"]:
			user.append("roles", {"role": role_name})

		user.insert()
		print(f"  ✓ Created user: {u['email']} ({', '.join(u['roles'])})")

	frappe.db.commit()


# ─── Taxpayers ────────────────────────────────────────────────────────────────

TAXPAYERS = [
	{
		"taxpayer_name": "Société Industrielle du Cameroun (SIC)",
		"taxpayer_type": "Enterprise",
		"tax_identification_number": "TIN-ENT-001",
		"email": "sic@example.com",
		"phone": "+237 233 42 10 00",
		"address": "12 Rue de l'Industrie",
		"city": "Douala",
		"region": "Littoral",
		"enterprise_name": "Société Industrielle du Cameroun",
		"industry": "Manufacturing",
		"annual_turnover": 4200000,
		"employee_count": 450,
	},
	{
		"taxpayer_name": "Brasseries d'Afrique Centrale (BAC)",
		"taxpayer_type": "Enterprise",
		"tax_identification_number": "TIN-ENT-002",
		"email": "bac@example.com",
		"phone": "+237 233 50 20 00",
		"address": "Avenue Charles de Gaulle",
		"city": "Douala",
		"region": "Littoral",
		"enterprise_name": "Brasseries d'Afrique Centrale",
		"industry": "Beverages",
		"annual_turnover": 9700000,
		"employee_count": 1200,
	},
	{
		"taxpayer_name": "Transport Express Sahel (TES)",
		"taxpayer_type": "Enterprise",
		"tax_identification_number": "TIN-ENT-003",
		"email": "tes@example.com",
		"phone": "+237 222 30 40 00",
		"address": "BP 1234, Zone Industrielle",
		"city": "Yaoundé",
		"region": "Centre",
		"enterprise_name": "Transport Express Sahel",
		"industry": "Logistics & Transport",
		"annual_turnover": 1350000,
		"employee_count": 180,
	},
	{
		"taxpayer_name": "Jean-Claude Mbeki",
		"taxpayer_type": "Individual",
		"tax_identification_number": "TIN-IND-001",
		"email": "jc.mbeki@example.com",
		"phone": "+237 699 00 11 22",
		"address": "Quartier Bastos",
		"city": "Yaoundé",
		"region": "Centre",
	},
	{
		"taxpayer_name": "Aïssatou Diallo",
		"taxpayer_type": "Individual",
		"tax_identification_number": "TIN-IND-002",
		"email": "a.diallo@example.com",
		"phone": "+237 677 88 99 00",
		"address": "Rue de la Joie, Akwa",
		"city": "Douala",
		"region": "Littoral",
	},
]


def create_taxpayers():
	"""Create 5 sample taxpayers."""
	for tp in TAXPAYERS:
		if frappe.db.exists("Taxpayer", {"tax_identification_number": tp["tax_identification_number"]}):
			print(f"  Taxpayer {tp['taxpayer_name']} already exists, skipping")
			continue

		doc = frappe.new_doc("Taxpayer")
		for field, value in tp.items():
			doc.set(field, value)
		doc.status = "Active"
		doc.currency = "USD"
		doc.insert()
		print(f"  ✓ Created taxpayer: {tp['taxpayer_name']}")

	frappe.db.commit()


def _get_taxpayer(tin):
	return frappe.db.get_value("Taxpayer", {"tax_identification_number": tin}, "name")


def _ensure_fiscal_year():
	year = "2026"
	if not frappe.db.exists("Tax Fiscal Year", year):
		doc = frappe.new_doc("Tax Fiscal Year")
		doc.year_name = year
		doc.start_date = "2026-01-01"
		doc.end_date = "2026-12-31"
		doc.is_active = 1
		doc.insert()
		frappe.db.commit()
	return year


# ─── Tax Settings & Rates ────────────────────────────────────────────────────

def configure_tax_settings():
	"""Configure the Tax Settings singleton."""
	try:
		doc = frappe.get_doc("Tax Settings")
		doc.country = "Cameroon"
		doc.currency = "USD"
		doc.tax_authority_name = "Direction Générale des Impôts (DGI)"
		doc.default_fiscal_year = _ensure_fiscal_year()
		doc.enable_email_notifications = 0
		doc.save()
		print("  ✓ Configured Tax Settings")
	except Exception:
		print("  ⚠ Could not configure Tax Settings (may not be installed)")
	frappe.db.commit()


def create_tax_rates():
	"""Create tax rates for all tax types for FY 2026."""
	fy = _ensure_fiscal_year()
	rates = [
		{"tax_type": "Corporate Income Tax", "rate": 30, "description": "Standard corporate income tax rate"},
		{"tax_type": "Value Added Tax", "rate": 19.25, "description": "Standard VAT rate (19.25%)"},
		{"tax_type": "Personal Income Tax", "rate": 20, "description": "Standard personal income tax rate"},
		{"tax_type": "Social Tax", "rate": 33, "description": "Employer social tax contribution rate"},
		{"tax_type": "Unemployment Insurance", "rate": 1.6, "description": "Unemployment insurance rate"},
		{"tax_type": "Mandatory Pension Fund", "rate": 2, "description": "Pension fund contribution rate"},
		{"tax_type": "Customs Import Duty", "rate": 10, "description": "Standard import duty rate"},
		{"tax_type": "Alcohol Excise Duty", "rate": 25, "description": "Excise duty on alcoholic beverages"},
		{"tax_type": "Tobacco Excise Duty", "rate": 30, "description": "Excise duty on tobacco products"},
		{"tax_type": "Fuel Excise Duty", "rate": 15, "description": "Excise duty on petroleum products"},
		{"tax_type": "Packaging Excise Duty", "rate": 5, "description": "Excise duty on non-recyclable packaging"},
	]

	for r in rates:
		if not frappe.db.exists("Tax Type", r["tax_type"]):
			continue
		existing = frappe.db.exists("Tax Rate", {"tax_type": r["tax_type"], "fiscal_year": fy})
		if existing:
			print(f"  Tax Rate for {r['tax_type']} already exists, skipping")
			continue

		doc = frappe.new_doc("Tax Rate")
		doc.tax_type = r["tax_type"]
		doc.fiscal_year = fy
		doc.rate = r["rate"]
		doc.effective_from = "2026-01-01"
		doc.effective_to = "2026-12-31"
		doc.description = r["description"]
		doc.insert()
		print(f"  ✓ Created Tax Rate: {r['tax_type']} @ {r['rate']}%")

	frappe.db.commit()


# ─── Enterprise Declarations ─────────────────────────────────────────────────

def create_enterprise_declarations():
	"""Create enterprise declarations with varied statuses across months."""
	fy = _ensure_fiscal_year()

	declarations = [
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_period": "Monthly",
			"filing_date": "2026-01-15",
			"due_date": "2026-01-31",
			"gross_revenue": 350000,
			"allowable_deductions": 25000,
			"total_payroll": 67000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"declaration_period": "Monthly",
			"filing_date": "2026-01-20",
			"due_date": "2026-01-31",
			"gross_revenue": 800000,
			"allowable_deductions": 60000,
			"total_payroll": 193000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_period": "Monthly",
			"filing_date": "2026-02-12",
			"due_date": "2026-02-28",
			"gross_revenue": 375000,
			"allowable_deductions": 27000,
			"total_payroll": 68000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"declaration_period": "Monthly",
			"filing_date": "2026-02-18",
			"due_date": "2026-02-28",
			"gross_revenue": 850000,
			"allowable_deductions": 63000,
			"total_payroll": 200000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"declaration_period": "Monthly",
			"filing_date": "2026-02-25",
			"due_date": "2026-02-28",
			"gross_revenue": 113000,
			"allowable_deductions": 8700,
			"total_payroll": 42500,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_period": "Quarterly",
			"filing_date": "2026-04-05",
			"due_date": "2026-04-30",
			"gross_revenue": 1042000,
			"allowable_deductions": 75000,
			"total_payroll": 200000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"declaration_period": "Quarterly",
			"filing_date": "2026-03-28",
			"due_date": "2026-03-31",
			"gross_revenue": 2417000,
			"allowable_deductions": 183000,
			"total_payroll": 583000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"declaration_period": "Monthly",
			"filing_date": "2026-04-07",
			"due_date": "2026-04-15",
			"gross_revenue": 110000,
			"allowable_deductions": 8300,
			"total_payroll": 41700,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Draft",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_period": "Monthly",
			"filing_date": "2026-05-10",
			"due_date": "2026-05-31",
			"gross_revenue": 400000,
			"allowable_deductions": 28000,
			"total_payroll": 70000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"declaration_period": "Monthly",
			"filing_date": "2026-05-15",
			"due_date": "2026-05-31",
			"gross_revenue": 883000,
			"allowable_deductions": 67000,
			"total_payroll": 208000,
			"income_tax_rate": 30,
			"social_tax_rate": 33,
			"unemployment_insurance_rate": 1.6,
			"pension_fund_rate": 2,
			"status_target": "Submitted",
		},
	]

	for d in declarations:
		tp = _get_taxpayer(d["taxpayer_tin"])
		if not tp:
			continue

		existing = frappe.db.exists("Enterprise Declaration", {"taxpayer": tp, "filing_date": d["filing_date"]})
		if existing:
			print(f"  Enterprise Declaration for {d['taxpayer_tin']} on {d['filing_date']} exists, skipping")
			continue

		doc = frappe.new_doc("Enterprise Declaration")
		doc.taxpayer = tp
		doc.fiscal_year = fy
		doc.declaration_period = d["declaration_period"]
		doc.filing_date = d["filing_date"]
		doc.due_date = d["due_date"]
		doc.gross_revenue = d["gross_revenue"]
		doc.allowable_deductions = d["allowable_deductions"]
		doc.total_payroll = d["total_payroll"]
		doc.income_tax_rate = d["income_tax_rate"]
		doc.social_tax_rate = d["social_tax_rate"]
		doc.unemployment_insurance_rate = d["unemployment_insurance_rate"]
		doc.pension_fund_rate = d["pension_fund_rate"]
		doc.currency = "USD"
		doc.insert()

		if d["status_target"] in ("Submitted", "Approved"):
			doc.submit()

		if d["status_target"] == "Approved":
			doc.db_set("status", "Approved")
			doc.db_set("approved_by", "agent@etax.demo")

		print(f"  ✓ Created Enterprise Declaration: {doc.name} [{d['status_target']}]")

	frappe.db.commit()


# ─── VAT Returns ─────────────────────────────────────────────────────────────

def create_vat_returns():
	"""Create VAT returns across multiple months."""
	fy = _ensure_fiscal_year()

	returns = [
		{
			"taxpayer_tin": "TIN-ENT-001",
			"return_period": "Monthly",
			"period_start": "2026-01-01",
			"period_end": "2026-01-31",
			"filing_date": "2026-02-05",
			"total_sales": 325000,
			"exempt_sales": 13000,
			"zero_rated_sales": 6700,
			"total_purchases": 200000,
			"exempt_purchases": 10000,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"return_period": "Monthly",
			"period_start": "2026-01-01",
			"period_end": "2026-01-31",
			"filing_date": "2026-02-08",
			"total_sales": 767000,
			"exempt_sales": 30000,
			"zero_rated_sales": 20000,
			"total_purchases": 458000,
			"exempt_purchases": 16700,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"return_period": "Monthly",
			"period_start": "2026-02-01",
			"period_end": "2026-02-28",
			"filing_date": "2026-03-05",
			"total_sales": 342000,
			"exempt_sales": 15000,
			"zero_rated_sales": 7500,
			"total_purchases": 208000,
			"exempt_purchases": 11700,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"return_period": "Monthly",
			"period_start": "2026-02-01",
			"period_end": "2026-02-28",
			"filing_date": "2026-03-06",
			"total_sales": 817000,
			"exempt_sales": 31700,
			"zero_rated_sales": 23300,
			"total_purchases": 475000,
			"exempt_purchases": 18300,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"return_period": "Monthly",
			"period_start": "2026-03-01",
			"period_end": "2026-03-31",
			"filing_date": "2026-04-05",
			"total_sales": 350000,
			"exempt_sales": 16700,
			"zero_rated_sales": 8300,
			"total_purchases": 217000,
			"exempt_purchases": 13300,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"return_period": "Monthly",
			"period_start": "2026-03-01",
			"period_end": "2026-03-31",
			"filing_date": "2026-03-30",
			"total_sales": 800000,
			"exempt_sales": 33300,
			"zero_rated_sales": 25000,
			"total_purchases": 483000,
			"exempt_purchases": 20000,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"return_period": "Quarterly",
			"period_start": "2026-01-01",
			"period_end": "2026-03-31",
			"filing_date": "2026-04-07",
			"total_sales": 91700,
			"exempt_sales": 3300,
			"zero_rated_sales": 0,
			"total_purchases": 66700,
			"exempt_purchases": 5000,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Draft",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"return_period": "Monthly",
			"period_start": "2026-04-01",
			"period_end": "2026-04-30",
			"filing_date": "2026-05-06",
			"total_sales": 367000,
			"exempt_sales": 18300,
			"zero_rated_sales": 9200,
			"total_purchases": 225000,
			"exempt_purchases": 14200,
			"output_vat_rate": 19.25,
			"input_vat_rate": 19.25,
			"status_target": "Submitted",
		},
	]

	for r in returns:
		tp = _get_taxpayer(r["taxpayer_tin"])
		if not tp:
			continue

		existing = frappe.db.exists("VAT Return", {"taxpayer": tp, "period_start": r["period_start"]})
		if existing:
			print(f"  VAT Return for {r['taxpayer_tin']} {r['period_start']} exists, skipping")
			continue

		doc = frappe.new_doc("VAT Return")
		doc.taxpayer = tp
		doc.fiscal_year = fy
		doc.return_period = r["return_period"]
		doc.period_start = r["period_start"]
		doc.period_end = r["period_end"]
		doc.filing_date = r["filing_date"]
		doc.total_sales = r["total_sales"]
		doc.exempt_sales = r["exempt_sales"]
		doc.zero_rated_sales = r["zero_rated_sales"]
		doc.total_purchases = r["total_purchases"]
		doc.exempt_purchases = r["exempt_purchases"]
		doc.output_vat_rate = r["output_vat_rate"]
		doc.input_vat_rate = r["input_vat_rate"]
		doc.currency = "USD"
		doc.insert()

		if r["status_target"] in ("Submitted", "Approved"):
			doc.submit()

		if r["status_target"] == "Approved":
			doc.db_set("status", "Approved")
			doc.db_set("approved_by", "agent@etax.demo")

		print(f"  ✓ Created VAT Return: {doc.name} [{r['status_target']}]")

	frappe.db.commit()


# ─── Personal Income Tax ─────────────────────────────────────────────────────

def create_personal_income_tax():
	"""Create personal income tax filings across months."""
	fy = _ensure_fiscal_year()

	filings = [
		{
			"taxpayer_tin": "TIN-IND-001",
			"tax_year": "2025",
			"filing_date": "2026-01-20",
			"employment_income": 30000,
			"other_employment_benefits": 4000,
			"employer_name": "Banque Centrale",
			"employer_tin": "TIN-ENT-999",
			"business_income": 0,
			"rental_income": 6000,
			"investment_income": 1300,
			"other_income": 0,
			"social_security_contributions": 2000,
			"pension_contributions": 1500,
			"insurance_premiums": 1000,
			"charitable_donations": 330,
			"other_deductions": 0,
			"tax_rate": 20,
			"tax_withheld": 5300,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-IND-002",
			"tax_year": "2025",
			"filing_date": "2026-02-28",
			"employment_income": 16000,
			"other_employment_benefits": 1300,
			"employer_name": "Hôpital Général",
			"employer_tin": "TIN-ENT-888",
			"business_income": 7000,
			"rental_income": 0,
			"investment_income": 500,
			"other_income": 0,
			"social_security_contributions": 1300,
			"pension_contributions": 800,
			"insurance_premiums": 600,
			"charitable_donations": 170,
			"other_deductions": 0,
			"tax_rate": 20,
			"tax_withheld": 2700,
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-IND-001",
			"tax_year": "2026",
			"filing_date": "2026-03-15",
			"employment_income": 32000,
			"other_employment_benefits": 4000,
			"employer_name": "Banque Centrale",
			"employer_tin": "TIN-ENT-999",
			"business_income": 0,
			"rental_income": 6000,
			"investment_income": 2000,
			"other_income": 830,
			"social_security_contributions": 2200,
			"pension_contributions": 1600,
			"insurance_premiums": 1000,
			"charitable_donations": 420,
			"other_deductions": 0,
			"tax_rate": 20,
			"tax_withheld": 5800,
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-IND-002",
			"tax_year": "2026",
			"filing_date": "2026-04-08",
			"employment_income": 17000,
			"other_employment_benefits": 1500,
			"employer_name": "Hôpital Général",
			"employer_tin": "TIN-ENT-888",
			"business_income": 8000,
			"rental_income": 2000,
			"investment_income": 750,
			"other_income": 330,
			"social_security_contributions": 1400,
			"pension_contributions": 850,
			"insurance_premiums": 630,
			"charitable_donations": 250,
			"other_deductions": 0,
			"tax_rate": 20,
			"tax_withheld": 3000,
			"status_target": "Draft",
		},
	]

	for f in filings:
		tp = _get_taxpayer(f["taxpayer_tin"])
		if not tp:
			continue

		existing = frappe.db.exists("Personal Income Tax", {
			"taxpayer": tp, "tax_year": f["tax_year"], "filing_date": f["filing_date"]
		})
		if existing:
			print(f"  PIT for {f['taxpayer_tin']} {f['tax_year']} exists, skipping")
			continue

		doc = frappe.new_doc("Personal Income Tax")
		doc.taxpayer = tp
		doc.fiscal_year = fy
		doc.tax_year = f["tax_year"]
		doc.filing_date = f["filing_date"]
		doc.employment_income = f["employment_income"]
		doc.other_employment_benefits = f["other_employment_benefits"]
		doc.employer_name = f["employer_name"]
		doc.employer_tin = f["employer_tin"]
		doc.business_income = f["business_income"]
		doc.rental_income = f["rental_income"]
		doc.investment_income = f["investment_income"]
		doc.other_income = f["other_income"]
		doc.social_security_contributions = f["social_security_contributions"]
		doc.pension_contributions = f["pension_contributions"]
		doc.insurance_premiums = f["insurance_premiums"]
		doc.charitable_donations = f["charitable_donations"]
		doc.other_deductions = f["other_deductions"]
		doc.tax_rate = f["tax_rate"]
		doc.tax_withheld = f["tax_withheld"]
		doc.currency = "USD"
		doc.insert()

		if f["status_target"] in ("Submitted", "Approved"):
			doc.submit()

		if f["status_target"] == "Approved":
			doc.db_set("status", "Approved")
			doc.db_set("approved_by", "agent@etax.demo")

		print(f"  ✓ Created Personal Income Tax: {doc.name} [{f['status_target']}]")

	frappe.db.commit()


# ─── Customs Declarations ────────────────────────────────────────────────────

def create_customs_declarations():
	"""Create customs declarations across months."""
	fy = _ensure_fiscal_year()

	declarations = [
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_type": "Import",
			"filing_date": "2026-01-18",
			"customs_office": "Port de Douala",
			"transport_mode": "Sea",
			"country_of_origin": "Germany",
			"vessel_name": "MV Hamburg Express",
			"bill_of_lading": "BL-2026-01-00045",
			"arrival_date": "2026-01-16",
			"items": [
				{
					"item_description": "CNC Milling Machines",
					"hs_code": "8459.21",
					"quantity": 3,
					"unit": "Pcs",
					"fob_value": 142000,
					"freight": 10000,
					"insurance": 2800,
					"duty_rate": 5,
					"vat_rate": 19.25,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"declaration_type": "Import",
			"filing_date": "2026-02-14",
			"customs_office": "Port de Douala",
			"transport_mode": "Sea",
			"country_of_origin": "Belgium",
			"vessel_name": "MV Antwerp Star",
			"bill_of_lading": "BL-2026-02-00089",
			"arrival_date": "2026-02-12",
			"items": [
				{
					"item_description": "Barley Malt for Brewing",
					"hs_code": "1107.10",
					"quantity": 50000,
					"unit": "KG",
					"fob_value": 58000,
					"freight": 7000,
					"insurance": 1200,
					"duty_rate": 10,
					"vat_rate": 19.25,
				},
				{
					"item_description": "Glass Bottles (500ml)",
					"hs_code": "7010.90",
					"quantity": 200000,
					"unit": "Pcs",
					"fob_value": 30000,
					"freight": 4200,
					"insurance": 600,
					"duty_rate": 20,
					"vat_rate": 19.25,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-001",
			"declaration_type": "Import",
			"filing_date": "2026-04-02",
			"customs_office": "Port de Douala",
			"transport_mode": "Sea",
			"country_of_origin": "China",
			"vessel_name": "MV Africa Star",
			"bill_of_lading": "BL-2026-04-00123",
			"arrival_date": "2026-04-01",
			"items": [
				{
					"item_description": "Industrial Machinery Parts",
					"hs_code": "8431.39",
					"quantity": 500,
					"unit": "KG",
					"fob_value": 75000,
					"freight": 5800,
					"insurance": 1500,
					"duty_rate": 10,
					"vat_rate": 19.25,
				},
				{
					"item_description": "Electronic Control Units",
					"hs_code": "8537.10",
					"quantity": 200,
					"unit": "Pcs",
					"fob_value": 47000,
					"freight": 3300,
					"insurance": 930,
					"duty_rate": 15,
					"vat_rate": 19.25,
				},
			],
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"declaration_type": "Import",
			"filing_date": "2026-03-20",
			"customs_office": "Aéroport de Yaoundé-Nsimalen",
			"transport_mode": "Air",
			"country_of_origin": "France",
			"vessel_name": "AF 892",
			"bill_of_lading": "AWB-2026-03-00456",
			"arrival_date": "2026-03-19",
			"items": [
				{
					"item_description": "Truck Spare Parts",
					"hs_code": "8708.99",
					"quantity": 150,
					"unit": "KG",
					"fob_value": 20000,
					"freight": 3000,
					"insurance": 400,
					"duty_rate": 10,
					"vat_rate": 19.25,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"declaration_type": "Export",
			"filing_date": "2026-05-08",
			"customs_office": "Port de Douala",
			"transport_mode": "Sea",
			"country_of_origin": "Cameroon",
			"vessel_name": "MV Lagos Trader",
			"bill_of_lading": "BL-2026-05-00210",
			"arrival_date": "2026-05-07",
			"items": [
				{
					"item_description": "Cocoa Beans (Grade 1)",
					"hs_code": "1801.00",
					"quantity": 25000,
					"unit": "KG",
					"fob_value": 104000,
					"freight": 0,
					"insurance": 2100,
					"duty_rate": 0,
					"vat_rate": 0,
				},
			],
			"status_target": "Submitted",
		},
	]

	for d in declarations:
		tp = _get_taxpayer(d["taxpayer_tin"])
		if not tp:
			continue

		existing = frappe.db.exists("Customs Declaration", {
			"taxpayer": tp, "filing_date": d["filing_date"]
		})
		if existing:
			print(f"  Customs Declaration for {d['taxpayer_tin']} {d['filing_date']} exists, skipping")
			continue

		doc = frappe.new_doc("Customs Declaration")
		doc.taxpayer = tp
		doc.declaration_type = d["declaration_type"]
		doc.filing_date = d["filing_date"]
		doc.customs_office = d["customs_office"]
		doc.transport_mode = d["transport_mode"]
		doc.country_of_origin = d["country_of_origin"]
		doc.vessel_name = d["vessel_name"]
		doc.bill_of_lading = d["bill_of_lading"]
		doc.arrival_date = d["arrival_date"]

		for item in d["items"]:
			doc.append("items", item)

		doc.currency = "USD"
		doc.insert()

		if d["status_target"] in ("Submitted", "Approved"):
			doc.submit()

		if d["status_target"] == "Approved":
			doc.db_set("status", "Approved")
			doc.db_set("approved_by", "agent@etax.demo")

		print(f"  ✓ Created Customs Declaration: {doc.name} [{d['status_target']}]")

	frappe.db.commit()


# ─── Excise Duty Returns ─────────────────────────────────────────────────────

def create_excise_duty_returns():
	"""Create excise duty returns across months."""
	fy = _ensure_fiscal_year()

	returns = [
		{
			"taxpayer_tin": "TIN-ENT-002",
			"excise_type": "Alcohol Excise",
			"return_period": "Monthly",
			"period_start": "2026-01-01",
			"period_end": "2026-01-31",
			"filing_date": "2026-02-06",
			"items": [
				{
					"item_description": "Beer – Standard Lager (5%)",
					"product_category": "Beer",
					"quantity": 780000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.20,
				},
				{
					"item_description": "Beer – Premium (7%)",
					"product_category": "Beer",
					"quantity": 290000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.30,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"excise_type": "Alcohol Excise",
			"return_period": "Monthly",
			"period_start": "2026-02-01",
			"period_end": "2026-02-28",
			"filing_date": "2026-03-06",
			"items": [
				{
					"item_description": "Beer – Standard Lager (5%)",
					"product_category": "Beer",
					"quantity": 820000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.20,
				},
				{
					"item_description": "Beer – Premium (7%)",
					"product_category": "Beer",
					"quantity": 310000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.30,
				},
				{
					"item_description": "Local Palm Wine",
					"product_category": "Wine",
					"quantity": 42000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.15,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-002",
			"excise_type": "Alcohol Excise",
			"return_period": "Monthly",
			"period_start": "2026-03-01",
			"period_end": "2026-03-31",
			"filing_date": "2026-04-05",
			"items": [
				{
					"item_description": "Beer – Standard Lager (5%)",
					"product_category": "Beer",
					"quantity": 850000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.20,
				},
				{
					"item_description": "Beer – Premium (7%)",
					"product_category": "Beer",
					"quantity": 320000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.30,
				},
				{
					"item_description": "Local Palm Wine",
					"product_category": "Wine",
					"quantity": 45000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.15,
				},
			],
			"status_target": "Submitted",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"excise_type": "Fuel Excise",
			"return_period": "Monthly",
			"period_start": "2026-01-01",
			"period_end": "2026-01-31",
			"filing_date": "2026-02-05",
			"items": [
				{
					"item_description": "Diesel – Transport Fleet",
					"product_category": "Diesel",
					"quantity": 115000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.13,
				},
				{
					"item_description": "Petrol – Service Vehicles",
					"product_category": "Petrol",
					"quantity": 32000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.16,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"excise_type": "Fuel Excise",
			"return_period": "Monthly",
			"period_start": "2026-02-01",
			"period_end": "2026-02-28",
			"filing_date": "2026-03-04",
			"items": [
				{
					"item_description": "Diesel – Transport Fleet",
					"product_category": "Diesel",
					"quantity": 118000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.13,
				},
				{
					"item_description": "Petrol – Service Vehicles",
					"product_category": "Petrol",
					"quantity": 34000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.16,
				},
			],
			"status_target": "Approved",
		},
		{
			"taxpayer_tin": "TIN-ENT-003",
			"excise_type": "Fuel Excise",
			"return_period": "Monthly",
			"period_start": "2026-03-01",
			"period_end": "2026-03-31",
			"filing_date": "2026-04-04",
			"items": [
				{
					"item_description": "Diesel – Transport Fleet",
					"product_category": "Diesel",
					"quantity": 120000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.13,
				},
				{
					"item_description": "Petrol – Service Vehicles",
					"product_category": "Petrol",
					"quantity": 35000,
					"unit": "Liters",
					"duty_rate_per_unit": 0.16,
				},
			],
			"status_target": "Approved",
		},
	]

	for r in returns:
		tp = _get_taxpayer(r["taxpayer_tin"])
		if not tp:
			continue

		existing = frappe.db.exists("Excise Duty Return", {
			"taxpayer": tp, "excise_type": r["excise_type"], "period_start": r["period_start"]
		})
		if existing:
			print(f"  Excise {r['excise_type']} for {r['taxpayer_tin']} exists, skipping")
			continue

		doc = frappe.new_doc("Excise Duty Return")
		doc.taxpayer = tp
		doc.excise_type = r["excise_type"]
		doc.fiscal_year = fy
		doc.return_period = r["return_period"]
		doc.period_start = r["period_start"]
		doc.period_end = r["period_end"]
		doc.filing_date = r["filing_date"]

		for item in r["items"]:
			doc.append("items", item)

		doc.currency = "USD"
		doc.insert()

		if r["status_target"] in ("Submitted", "Approved"):
			doc.submit()

		if r["status_target"] == "Approved":
			doc.db_set("status", "Approved")
			doc.db_set("approved_by", "agent@etax.demo")

		print(f"  ✓ Created Excise Duty Return: {doc.name} [{r['status_target']}]")

	frappe.db.commit()
