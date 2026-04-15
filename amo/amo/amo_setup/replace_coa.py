"""Replace Chart of Accounts for companies that have a built-in country-specific COA."""

import frappe
from frappe.utils.nestedset import rebuild_tree


# Country → COA template mapping (only countries with built-in COAs)
COUNTRY_COA = {
	"Australia": "Australia - Chart of Accounts with Account Numbers",
	"Canada": "Canada - Plan comptable pour les provinces francophones",
}


def execute():
	"""Replace COA for companies whose country has a built-in template."""
	companies = frappe.db.sql("""
		SELECT name, abbr, country, chart_of_accounts
		FROM tabCompany
		WHERE country IN %(countries)s
	""", {"countries": list(COUNTRY_COA.keys())}, as_dict=True)

	if not companies:
		print("No companies found needing COA replacement.")
		return

	for comp in companies:
		target_coa = COUNTRY_COA[comp.country]
		if comp.chart_of_accounts == target_coa:
			print(f"  SKIP (already using correct COA): {comp.name}")
			continue

		print(f"\n{'='*60}")
		print(f"  Replacing COA for: {comp.name} ({comp.abbr})")
		print(f"  Country: {comp.country}")
		print(f"  Old COA: {comp.chart_of_accounts}")
		print(f"  New COA: {target_coa}")
		print(f"{'='*60}")

		_replace_company_coa(comp.name, comp.abbr, comp.country, target_coa)

	frappe.db.commit()
	print("\nDone! COA replacement complete.")


def _replace_company_coa(company, abbr, country, new_coa):
	"""Delete existing accounts and install country-specific COA."""
	# Step 1: Delete all transactional data referencing accounts
	_delete_company_transactions(company)
	frappe.db.commit()

	# Step 2: Delete all existing accounts
	_delete_company_accounts(company)
	frappe.db.commit()

	# Step 3: Install new COA (bypasses root-company validation)
	_install_coa(company, new_coa, country)
	frappe.db.commit()

	# Step 4: Update company record
	frappe.db.set_value("Company", company, "chart_of_accounts", new_coa)

	# Step 5: Set default accounts
	_set_default_accounts(company, abbr)
	frappe.db.commit()

	count = frappe.db.count("Account", {"company": company})
	print(f"  Installed {count} accounts with {new_coa}")


def _delete_company_transactions(company):
	"""Delete all demo transactions for a company."""
	# Order matters - delete children before parents

	# GL Entries
	frappe.db.sql("DELETE FROM `tabGL Entry` WHERE company = %s", company)

	# Journal Entry children then parent
	je_names = frappe.db.sql_list(
		"SELECT name FROM `tabJournal Entry` WHERE company = %s", company
	)
	if je_names:
		frappe.db.sql(
			"DELETE FROM `tabJournal Entry Account` WHERE parent IN %s",
			[je_names],
		)
		frappe.db.sql("DELETE FROM `tabJournal Entry` WHERE company = %s", company)
		print(f"  Deleted {len(je_names)} journal entries")

	# Payment Entry children then parent
	pe_names = frappe.db.sql_list(
		"SELECT name FROM `tabPayment Entry` WHERE company = %s", company
	)
	if pe_names:
		for child in ["Payment Entry Reference", "Payment Entry Deduction"]:
			frappe.db.sql(f"DELETE FROM `tab{child}` WHERE parent IN %s", [pe_names])
		frappe.db.sql("DELETE FROM `tabPayment Entry` WHERE company = %s", company)

	# Bank Account
	frappe.db.sql("DELETE FROM `tabBank Account` WHERE company = %s", company)

	# Budget
	frappe.db.sql("DELETE FROM `tabBudget` WHERE company = %s", company)

	# Asset
	asset_names = frappe.db.sql_list(
		"SELECT name FROM tabAsset WHERE company = %s", company
	)
	if asset_names:
		for child in [
			"Asset Depreciation Schedule",
			"Asset Finance Book",
			"Depreciation Schedule",
		]:
			if frappe.db.table_exists(f"tab{child}"):
				frappe.db.sql(f"DELETE FROM `tab{child}` WHERE parent IN %s", [asset_names])
		frappe.db.sql("DELETE FROM tabAsset WHERE company = %s", company)


def _delete_company_accounts(company):
	"""Delete all accounts for a company (leaf first, then groups)."""
	# Disable foreign key checks temporarily for nested set
	frappe.db.sql("SET FOREIGN_KEY_CHECKS = 0")

	# Clear company default account references first
	comp_doc = frappe.get_doc("Company", company)
	account_fields = [
		"default_bank_account", "default_cash_account",
		"default_receivable_account", "default_payable_account",
		"default_expense_account", "default_income_account",
		"round_off_account", "write_off_account",
		"discount_allowed_account", "discount_received_account",
		"exchange_gain_loss_account", "unrealized_exchange_gain_loss_account",
		"default_deferred_revenue_account", "default_deferred_expense_account",
		"cost_center", "round_off_cost_center",
		"depreciation_expense_account", "capital_work_in_progress_account",
		"asset_received_but_not_billed", "expenses_included_in_asset_valuation",
		"default_expense_claim_payable_account",
		"default_inventory_account", "stock_adjustment_account",
		"stock_received_but_not_billed", "expenses_included_in_valuation",
		"default_provisional_account",
	]
	for field in account_fields:
		if hasattr(comp_doc, field) and comp_doc.get(field):
			frappe.db.set_value("Company", company, field, None)

	# Also clear default_finance_book if set
	if hasattr(comp_doc, "default_finance_book"):
		frappe.db.set_value("Company", company, "default_finance_book", None)

	frappe.db.commit()

	# Delete accounts - leaf nodes first (order by lft DESC)
	frappe.db.sql("""
		DELETE FROM tabAccount WHERE company = %s ORDER BY lft DESC
	""", company)

	frappe.db.sql("SET FOREIGN_KEY_CHECKS = 1")
	print(f"  Deleted existing accounts for {company}")


def _install_coa(company, chart_template, country):
	"""Install a chart of accounts from template."""
	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
		create_charts,
	)

	# Bypass root-company validation since we're intentionally installing
	# a different COA for a child company in a different country
	frappe.local.flags.ignore_root_company_validation = True
	try:
		create_charts(company, chart_template=chart_template)
	finally:
		frappe.local.flags.ignore_root_company_validation = False
	print(f"  Installed chart: {chart_template}")


def _set_default_accounts(company, abbr):
	"""Set default accounts on the company after COA installation."""
	_manual_set_defaults(company, abbr)


def _manual_set_defaults(company, abbr):
	"""Manually find and set critical default accounts."""
	def find_account(filters):
		filters["company"] = company
		return frappe.db.get_value("Account", filters, "name")

	updates = {}

	# Try to find common default accounts
	receivable = find_account({"account_type": "Receivable", "is_group": 0})
	if receivable:
		updates["default_receivable_account"] = receivable

	payable = find_account({"account_type": "Payable", "is_group": 0})
	if payable:
		updates["default_payable_account"] = payable

	bank = find_account({"account_type": "Bank", "is_group": 0})
	if bank:
		updates["default_bank_account"] = bank

	cash = find_account({"account_type": "Cash", "is_group": 0})
	if cash:
		updates["default_cash_account"] = cash

	for field, value in updates.items():
		frappe.db.set_value("Company", company, field, value)
