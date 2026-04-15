# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Setup e-Tax application after installation."""
	create_roles()
	create_default_tax_types()
	create_default_fiscal_year()


def after_migrate():
	"""Run after migration."""
	create_roles()


def create_roles():
	"""Create custom roles for e-Tax."""
	roles = [
		{"role_name": "Tax Officer", "desk_access": 1},
		{"role_name": "Tax Filer", "desk_access": 1},
		{"role_name": "Customs Officer", "desk_access": 1},
		{"role_name": "Tax Auditor", "desk_access": 1},
	]

	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.new_doc("Role")
			role.role_name = role_data["role_name"]
			role.desk_access = role_data["desk_access"]
			role.insert(ignore_permissions=True)

	frappe.db.commit()


def create_default_tax_types():
	"""Create default tax types."""
	tax_types = [
		{"type_name": "Corporate Income Tax", "category": "Income Tax"},
		{"type_name": "Social Tax", "category": "Social Tax"},
		{"type_name": "Value Added Tax", "category": "VAT"},
		{"type_name": "Unemployment Insurance", "category": "Unemployment Insurance"},
		{"type_name": "Mandatory Pension Fund", "category": "Pension Fund"},
		{"type_name": "Alcohol Excise Duty", "category": "Excise Duty"},
		{"type_name": "Tobacco Excise Duty", "category": "Excise Duty"},
		{"type_name": "Fuel Excise Duty", "category": "Excise Duty"},
		{"type_name": "Packaging Excise Duty", "category": "Excise Duty"},
		{"type_name": "Customs Import Duty", "category": "Customs Duty"},
		{"type_name": "Personal Income Tax", "category": "Personal Income Tax"},
	]

	for tt in tax_types:
		if not frappe.db.exists("Tax Type", tt["type_name"]):
			doc = frappe.new_doc("Tax Type")
			doc.type_name = tt["type_name"]
			doc.category = tt["category"]
			doc.is_active = 1
			doc.insert(ignore_permissions=True)

	frappe.db.commit()


def create_default_fiscal_year():
	"""Create default fiscal year."""
	import datetime

	year = datetime.date.today().year
	name = str(year)

	if not frappe.db.exists("Tax Fiscal Year", name):
		doc = frappe.new_doc("Tax Fiscal Year")
		doc.year_name = name
		doc.start_date = f"{year}-01-01"
		doc.end_date = f"{year}-12-31"
		doc.is_active = 1
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
