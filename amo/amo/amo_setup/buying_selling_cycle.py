"""
AMO Buying & Selling Cycle Demo Data
=====================================

Creates the full buying and selling transaction cycle for sample AMO companies:

**Selling Cycle:**
  Quotation -> Sales Order -> Sales Invoice -> Payment Entry (Receive)

**Buying Cycle:**
  Request for Quotation -> Purchase Order -> Purchase Invoice -> Payment Entry (Pay)

All documents are submitted (docstatus=1) and interconnected via ERPNext's
standard reference chain so that print formats and reports work correctly.
"""

import frappe
from frappe.utils import getdate, add_days, add_months, flt
from amo.amo_setup.company_definitions import get_all_companies, COUNTRY_CURRENCY


# -- Master Data Definitions --

SUPPLIER_GROUPS = [
	"Office Suppliers",
	"Cleaning Services",
	"Educational Publishers",
	"IT Vendors",
	"Religious Goods",
	"Agricultural Suppliers",
	"Maintenance Contractors",
]

SUPPLIERS = [
	{"name": "LibanPapier SARL", "group": "Office Suppliers", "country": "Lebanon", "currency": "LBP"},
	{"name": "CleanTech Lebanon", "group": "Cleaning Services", "country": "Lebanon", "currency": "LBP"},
	{"name": "Librairie Antoine", "group": "Educational Publishers", "country": "Lebanon", "currency": "LBP"},
	{"name": "TechVision Middle East", "group": "IT Vendors", "country": "Lebanon", "currency": "LBP"},
	{"name": "BeitNour Religious Supplies", "group": "Religious Goods", "country": "Lebanon", "currency": "LBP"},
	{"name": "Mount Lebanon Farms", "group": "Agricultural Suppliers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Samir Maintenance Co.", "group": "Maintenance Contractors", "country": "Lebanon", "currency": "LBP"},
	{"name": "Cartoleria Roma SRL", "group": "Office Suppliers", "country": "Italy", "currency": "EUR"},
	{"name": "CanadianOffice Direct", "group": "Office Suppliers", "country": "Canada", "currency": "CAD"},
	{"name": "Aussie Supplies Pty Ltd", "group": "Office Suppliers", "country": "Australia", "currency": "AUD"},
]

CUSTOMERS = [
	{"name": "Saint Joseph Parish - Beirut", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Notre Dame Parish - Jounieh", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Maronite Eparchy of Baalbek", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Association des Parents - Hadath", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Lebanese Ministry of Education", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Zahle Cultural Association", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Holy Land Pilgrimage Tours", "group": "Institutional Buyers", "country": "Lebanon", "currency": "LBP"},
	{"name": "Parrocchia San Maron - Roma", "group": "Institutional Buyers", "country": "Italy", "currency": "EUR"},
	{"name": "Our Lady of Lebanon Centre - Toronto", "group": "Institutional Buyers", "country": "Canada", "currency": "CAD"},
	{"name": "Maronite Diocese of Australia", "group": "Institutional Buyers", "country": "Australia", "currency": "AUD"},
]

SELLING_ITEMS = [
	{"item_code": "AMO-OFF-001", "rate": 8},
	{"item_code": "AMO-OFF-002", "rate": 5},
	{"item_code": "AMO-OFF-003", "rate": 65},
	{"item_code": "AMO-EDU-001", "rate": 45},
	{"item_code": "AMO-EDU-002", "rate": 180},
	{"item_code": "AMO-REL-001", "rate": 40},
	{"item_code": "AMO-AGR-001", "rate": 35},
]

BUYING_ITEMS = [
	{"item_code": "AMO-OFF-001", "rate": 5},
	{"item_code": "AMO-OFF-002", "rate": 3},
	{"item_code": "AMO-OFF-003", "rate": 45},
	{"item_code": "AMO-CLN-001", "rate": 8},
	{"item_code": "AMO-EDU-001", "rate": 30},
	{"item_code": "AMO-EDU-002", "rate": 120},
	{"item_code": "AMO-REL-001", "rate": 25},
	{"item_code": "AMO-AGR-001", "rate": 20},
	{"item_code": "AMO-IT-001", "rate": 15},
	{"item_code": "AMO-MNT-001", "rate": 4},
]

SELLING_SCENARIOS = [
	{
		"title": "Educational Materials Supply",
		"items": [
			{"item_code": "AMO-EDU-001", "qty": 50},
			{"item_code": "AMO-OFF-001", "qty": 100},
			{"item_code": "AMO-OFF-002", "qty": 30},
		],
	},
	{
		"title": "Religious Supplies Order",
		"items": [
			{"item_code": "AMO-REL-001", "qty": 20},
			{"item_code": "AMO-AGR-001", "qty": 15},
		],
	},
	{
		"title": "IT and Office Equipment",
		"items": [
			{"item_code": "AMO-OFF-003", "qty": 10},
			{"item_code": "AMO-OFF-001", "qty": 200},
		],
	},
]

BUYING_SCENARIOS = [
	{
		"title": "Office Supplies Restock",
		"items": [
			{"item_code": "AMO-OFF-001", "qty": 500},
			{"item_code": "AMO-OFF-002", "qty": 100},
			{"item_code": "AMO-OFF-003", "qty": 20},
		],
	},
	{
		"title": "Cleaning and Maintenance Supplies",
		"items": [
			{"item_code": "AMO-CLN-001", "qty": 40},
			{"item_code": "AMO-MNT-001", "qty": 100},
		],
	},
	{
		"title": "Educational and Lab Materials",
		"items": [
			{"item_code": "AMO-EDU-001", "qty": 100},
			{"item_code": "AMO-EDU-002", "qty": 15},
			{"item_code": "AMO-IT-001", "qty": 30},
		],
	},
	{
		"title": "Religious and Agricultural Goods",
		"items": [
			{"item_code": "AMO-REL-001", "qty": 50},
			{"item_code": "AMO-AGR-001", "qty": 40},
		],
	},
]

EXCHANGE_RATES = [
	{"from_currency": "EUR", "to_currency": "LBP", "exchange_rate": 98500},
	{"from_currency": "CAD", "to_currency": "LBP", "exchange_rate": 65000},
	{"from_currency": "AUD", "to_currency": "LBP", "exchange_rate": 58000},
	{"from_currency": "SYP", "to_currency": "LBP", "exchange_rate": 6.5},
	{"from_currency": "CHF", "to_currency": "LBP", "exchange_rate": 102000},
	{"from_currency": "USD", "to_currency": "LBP", "exchange_rate": 89500},
	{"from_currency": "LBP", "to_currency": "EUR", "exchange_rate": 0.0000102},
	{"from_currency": "LBP", "to_currency": "CAD", "exchange_rate": 0.0000154},
	{"from_currency": "LBP", "to_currency": "AUD", "exchange_rate": 0.0000172},
	{"from_currency": "LBP", "to_currency": "SYP", "exchange_rate": 0.154},
]


# -- Main Entry Point --

@frappe.whitelist()
def create_buying_selling_cycle():
	"""Create the full buying and selling cycle for AMO sample companies."""
	frappe.only_for("Administrator")

	print("=" * 60)
	print("AMO BUYING & SELLING CYCLE - Starting")
	print("=" * 60)

	# Disable notifications to avoid workflow_state errors on Sales Order
	frappe.flags.in_import = True
	frappe.flags.mute_emails = True

	# Monkeypatch Italian e-invoicing validations (too many custom fields to install)
	_orig_si_validate = None
	_orig_si_on_submit = None
	try:
		from erpnext.regional.italy import utils as italy_utils
		_orig_si_validate = italy_utils.sales_invoice_validate
		_orig_si_on_submit = italy_utils.sales_invoice_on_submit
		italy_utils.sales_invoice_validate = lambda doc, *a, **kw: None
		italy_utils.sales_invoice_on_submit = lambda doc, *a, **kw: None
	except Exception:
		pass

	_ensure_custom_fields()
	_ensure_fiscal_years()
	_ensure_currency_exchange_rates()
	_create_supplier_groups()
	_create_suppliers()
	_create_customer_groups()
	_create_customers()
	_setup_item_defaults()
	_ensure_company_stock_settings()
	_ensure_company_addresses()
	# Buying first to build stock for selling
	_create_buying_cycles()
	_create_selling_cycles()

	# Restore Italian validations
	try:
		from erpnext.regional.italy import utils as italy_utils
		if _orig_si_validate:
			italy_utils.sales_invoice_validate = _orig_si_validate
		if _orig_si_on_submit:
			italy_utils.sales_invoice_on_submit = _orig_si_on_submit
	except Exception:
		pass

	frappe.flags.in_import = False
	frappe.flags.mute_emails = False
	frappe.db.commit()
	print("=" * 60)
	print("AMO BUYING & SELLING CYCLE - Complete!")
	print("=" * 60)


# -- Prerequisites --

def _ensure_custom_fields():
	"""Ensure required custom fields exist (e.g. for Italian e-invoicing)."""
	print("Ensuring custom fields...")
	custom_fields = [
		{"dt": "Address", "fieldname": "country_code", "label": "Country Code",
		 "fieldtype": "Data", "insert_after": "country", "fetch_from": "country.code"},
		{"dt": "Sales Taxes and Charges", "fieldname": "tax_exemption_reason",
		 "label": "Tax Exemption Reason", "fieldtype": "Select", "insert_after": "included_in_print_rate",
		 "options": "\nN1-Escluse ex art. 15\nN2-Non Soggette\nN3-Non Imponibili\nN4-Esenti\nN5-Regime del margine\nN6-Inversione Contabile\nN7-IVA assolta in altro stato UE"},
		{"dt": "Sales Taxes and Charges", "fieldname": "tax_exemption_law",
		 "label": "Tax Exempt Under", "fieldtype": "Text", "insert_after": "tax_exemption_reason"},
		{"dt": "Sales Invoice", "fieldname": "company_fiscal_regime",
		 "label": "Company Fiscal Regime", "fieldtype": "Data", "insert_after": "company",
		 "fetch_from": "company.fiscal_regime", "read_only": 1},
		{"dt": "Sales Invoice", "fieldname": "company_tax_id",
		 "label": "Company Tax ID", "fieldtype": "Data", "insert_after": "company_fiscal_regime",
		 "fetch_from": "company.tax_id", "read_only": 1},
		{"dt": "Sales Invoice", "fieldname": "company_fiscal_code",
		 "label": "Company Fiscal Code", "fieldtype": "Data", "insert_after": "company_tax_id",
		 "fetch_from": "company.fiscal_code", "read_only": 1},
		{"dt": "Sales Invoice", "fieldname": "customer_fiscal_code",
		 "label": "Customer Fiscal Code", "fieldtype": "Data", "insert_after": "customer"},
		{"dt": "Mode of Payment", "fieldname": "mode_of_payment_code",
		 "label": "Mode of Payment Code", "fieldtype": "Data", "insert_after": "type"},
		{"dt": "Payment Schedule", "fieldname": "mode_of_payment_code",
		 "label": "Mode of Payment Code", "fieldtype": "Data", "insert_after": "mode_of_payment",
		 "fetch_from": "mode_of_payment.mode_of_payment_code", "read_only": 1},
	]
	for cf in custom_fields:
		cf_name = f"{cf['dt']}-{cf['fieldname']}"
		if not frappe.db.exists("Custom Field", cf_name):
			try:
				doc = {"doctype": "Custom Field"}
				doc.update(cf)
				frappe.get_doc(doc).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Custom field warning ({cf_name}): {e}")
	frappe.db.commit()
	# Ensure DB columns are created for any new custom fields
	affected_dts = set(cf["dt"] for cf in custom_fields)
	for dt in affected_dts:
		frappe.clear_cache(doctype=dt)
		try:
			frappe.db.updatedb(dt)
		except Exception:
			pass
	frappe.db.commit()

	# Set mode_of_payment_code on Wire Transfer for Italian e-invoicing (MP05 = Bonifico)
	if frappe.db.exists("Mode of Payment", "Wire Transfer"):
		current_code = frappe.db.get_value("Mode of Payment", "Wire Transfer", "mode_of_payment_code")
		if not current_code:
			frappe.db.set_value("Mode of Payment", "Wire Transfer", "mode_of_payment_code", "MP05")


def _ensure_fiscal_years():
	"""Ensure fiscal years exist for 2025 and 2026."""
	print("Ensuring fiscal years...")
	for year in [2025, 2026]:
		fy_name = str(year)
		if not frappe.db.exists("Fiscal Year", fy_name):
			try:
				frappe.get_doc({
					"doctype": "Fiscal Year",
					"year": fy_name,
					"year_start_date": f"{year}-01-01",
					"year_end_date": f"{year}-12-31",
				}).insert(ignore_permissions=True)
			except Exception:
				pass
	frappe.db.commit()


def _ensure_currency_exchange_rates():
	"""Create currency exchange rates for demo foreign transactions."""
	print("Setting up exchange rates...")
	today = getdate()
	for rate_def in EXCHANGE_RATES:
		exists = frappe.db.exists("Currency Exchange", {
			"from_currency": rate_def["from_currency"],
			"to_currency": rate_def["to_currency"],
		})
		if not exists:
			try:
				frappe.get_doc({
					"doctype": "Currency Exchange",
					"from_currency": rate_def["from_currency"],
					"to_currency": rate_def["to_currency"],
					"exchange_rate": rate_def["exchange_rate"],
					"date": add_months(today, -6),
					"for_buying": 1,
					"for_selling": 1,
				}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Exchange rate warning ({rate_def['from_currency']}->{rate_def['to_currency']}): {e}")
	frappe.db.commit()


def _ensure_company_addresses():
	"""Create a default address for sample companies that don't have one."""
	print("Ensuring company addresses...")
	sample_companies = _get_sample_companies()

	country_addresses = {
		"Italy": {"address_line1": "Via della Conciliazione 10", "city": "Rome", "pincode": "00193"},
		"Canada": {"address_line1": "1430 Huron Church Rd", "city": "Windsor", "pincode": "N9C 2K4"},
		"Belgium": {"address_line1": "Rue de Stassart 32", "city": "Brussels", "pincode": "1050"},
		"Syria": {"address_line1": "Banias Road", "city": "Banias", "pincode": "00000"},
		"Australia": {"address_line1": "105 Canning St", "city": "Melbourne", "pincode": "3070"},
		"Lebanon": {"address_line1": "Jounieh Highway", "city": "Jounieh", "pincode": "1200"},
		"Switzerland": {"address_line1": "Bahnhofstrasse 1", "city": "Zurich", "pincode": "8001"},
	}

	for comp in sample_companies:
		company = comp["name"]
		country = comp["country"]

		# Check if company already has an address linked
		existing = frappe.db.exists("Dynamic Link", {
			"link_doctype": "Company",
			"link_name": company,
			"parenttype": "Address",
		})
		if existing:
			continue

		addr_info = country_addresses.get(country, {"address_line1": "Main Street", "city": "City", "pincode": "00000"})
		try:
			addr = frappe.get_doc({
				"doctype": "Address",
				"address_title": company,
				"address_type": "Office",
				"address_line1": addr_info["address_line1"],
				"city": addr_info["city"],
				"pincode": addr_info["pincode"],
				"country": country,
				"country_code": _get_country_code(country),
				"is_primary_address": 1,
				"is_shipping_address": 1,
				"links": [{"link_doctype": "Company", "link_name": company}],
			})
			addr.insert(ignore_permissions=True)
		except Exception as e:
			print(f"  Address warning ({company}): {e}")

	frappe.db.commit()
	print("  Company addresses set.")

	# Set fiscal_regime, tax_id, fiscal_code for Italian companies (required for e-invoicing)
	for comp in sample_companies:
		if comp["country"] == "Italy":
			company = comp["name"]
			updates = {}
			if not frappe.db.get_value("Company", company, "fiscal_regime"):
				updates["fiscal_regime"] = "RF01-Ordinario"
			if not frappe.db.get_value("Company", company, "tax_id"):
				updates["tax_id"] = "IT12345678901"
			if not frappe.db.get_value("Company", company, "fiscal_code"):
				updates["fiscal_code"] = "ABCDEF90A01H501Z"
			for field, value in updates.items():
				frappe.db.set_value("Company", company, field, value)
			if updates:
				print(f"  Set Italian fiscal fields for {company}: {list(updates.keys())}")

	# Set tax_id on Italian customers (required for non-individual e-invoicing)
	for cust in CUSTOMERS:
		if cust["country"] == "Italy":
			if not frappe.db.get_value("Customer", cust["name"], "tax_id"):
				frappe.db.set_value("Customer", cust["name"], "tax_id", "IT98765432109")
				print(f"  Set tax_id for customer {cust['name']}")

	# Ensure Italian customers have an address with country_code
	for cust in CUSTOMERS:
		if cust["country"] == "Italy":
			existing = frappe.db.exists("Dynamic Link", {
				"link_doctype": "Customer",
				"link_name": cust["name"],
				"parenttype": "Address",
			})
			if not existing:
				try:
					addr = frappe.get_doc({
						"doctype": "Address",
						"address_title": cust["name"],
						"address_type": "Billing",
						"address_line1": "Piazza Venezia 1",
						"city": "Rome",
						"pincode": "00186",
						"country": "Italy",
						"country_code": "IT",
						"is_primary_address": 1,
						"links": [{"link_doctype": "Customer", "link_name": cust["name"]}],
					})
					addr.insert(ignore_permissions=True)
					print(f"  Created address for customer {cust['name']}")
				except Exception as e:
					print(f"  Customer address warning ({cust['name']}): {e}")

	frappe.db.commit()


# -- Supplier & Customer Setup --

def _create_supplier_groups():
	"""Create supplier groups."""
	print("Creating supplier groups...")
	for group_name in SUPPLIER_GROUPS:
		if not frappe.db.exists("Supplier Group", group_name):
			try:
				frappe.get_doc({
					"doctype": "Supplier Group",
					"supplier_group_name": group_name,
				}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Supplier group warning ({group_name}): {e}")
	frappe.db.commit()


def _create_suppliers():
	"""Create supplier records."""
	print("Creating suppliers...")
	for supp in SUPPLIERS:
		if not frappe.db.exists("Supplier", supp["name"]):
			try:
				frappe.get_doc({
					"doctype": "Supplier",
					"supplier_name": supp["name"],
					"supplier_group": supp["group"],
					"country": supp["country"],
					"default_currency": supp["currency"],
					"supplier_type": "Company",
				}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Supplier warning ({supp['name']}): {e}")
	frappe.db.commit()
	print(f"  {len(SUPPLIERS)} suppliers ready.")


def _create_customer_groups():
	"""Create customer groups."""
	print("Creating customer groups...")
	for grp in ["Institutional Buyers", "Parents & Families", "Parishes", "Event Organizers", "University Students"]:
		if not frappe.db.exists("Customer Group", grp):
			try:
				frappe.get_doc({
					"doctype": "Customer Group",
					"customer_group_name": grp,
					"parent_customer_group": "All Customer Groups",
				}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Customer group warning ({grp}): {e}")
	frappe.db.commit()


def _create_customers():
	"""Create customer records."""
	print("Creating customers...")
	for cust in CUSTOMERS:
		if not frappe.db.exists("Customer", cust["name"]):
			try:
				frappe.get_doc({
					"doctype": "Customer",
					"customer_name": cust["name"],
					"customer_group": cust["group"],
					"customer_type": "Company",
					"territory": "All Territories",
					"default_currency": cust["currency"],
				}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"  Customer warning ({cust['name']}): {e}")
	frappe.db.commit()
	print(f"  {len(CUSTOMERS)} customers ready.")


def _setup_item_defaults():
	"""Ensure stock items have item defaults for each sample company."""
	print("Setting up item defaults for sample companies...")
	sample_companies = _get_sample_companies()

	for comp in sample_companies:
		abbr = comp["abbr"]
		company = comp["name"]

		warehouse = _get_warehouse(company, abbr)
		if not warehouse:
			continue

		income_account = _get_income_account(company)
		expense_account = _get_expense_account(company)

		all_items = list({i["item_code"] for i in BUYING_ITEMS} | {i["item_code"] for i in SELLING_ITEMS})
		for item_code in all_items:
			if not frappe.db.exists("Item", item_code):
				continue
			existing = frappe.db.exists("Item Default", {
				"parent": item_code, "company": company,
			})
			if not existing:
				try:
					item_doc = frappe.get_doc("Item", item_code)
					item_doc.append("item_defaults", {
						"company": company,
						"default_warehouse": warehouse,
						"income_account": income_account,
						"expense_account": expense_account,
					})
					item_doc.save(ignore_permissions=True)
				except Exception as e:
					print(f"  Item default warning ({item_code} / {company}): {e}")

	frappe.db.commit()
	print("  Item defaults set.")


def _ensure_company_stock_settings():
	"""Set required default accounts on sample companies for stock transactions."""
	print("Setting company stock defaults...")
	sample_companies = _get_sample_companies()

	for comp in sample_companies:
		company = comp["name"]
		abbr = comp["abbr"]
		updates = {}

		# Stock Received But Not Billed
		srnb = frappe.db.get_value("Account", {
			"company": company, "account_type": "Stock Received But Not Billed", "is_group": 0,
		}, "name")
		if srnb:
			current = frappe.db.get_value("Company", company, "stock_received_but_not_billed")
			if not current:
				updates["stock_received_but_not_billed"] = srnb

		# Default Expense Account
		expense = _get_expense_account(company)
		if expense:
			current = frappe.db.get_value("Company", company, "default_expense_account")
			if not current:
				updates["default_expense_account"] = expense

		# Default Income Account
		income = _get_income_account(company)
		if income:
			current = frappe.db.get_value("Company", company, "default_income_account")
			if not current:
				updates["default_income_account"] = income

		# Default Inventory Account
		inv_acct = frappe.db.get_value("Account", {
			"company": company, "account_type": "Stock", "is_group": 0,
		}, "name")
		if inv_acct:
			current = frappe.db.get_value("Company", company, "default_inventory_account")
			if not current:
				updates["default_inventory_account"] = inv_acct

		# Round Off Cost Center
		leaf_cc = _get_leaf_cost_center(company)
		if leaf_cc:
			current = frappe.db.get_value("Company", company, "round_off_cost_center")
			if not current:
				updates["round_off_cost_center"] = leaf_cc

		if updates:
			for field, value in updates.items():
				frappe.db.set_value("Company", company, field, value)

	frappe.db.commit()
	print("  Company stock defaults set.")


# -- Selling Cycle --

def _create_selling_cycles():
	"""Quotation -> Sales Order -> Sales Invoice -> Payment Entry (Receive)."""
	print("Creating selling cycles...")
	sample_companies = _get_sample_companies()
	cycle_count = 0

	for comp_idx, comp in enumerate(sample_companies):
		company = comp["name"]
		abbr = comp["abbr"]
		currency = comp["currency"]

		# Pick customers matching company currency
		company_customers = [c for c in CUSTOMERS if c["currency"] == currency]
		if not company_customers:
			company_customers = [c for c in CUSTOMERS if c["currency"] == "LBP"]

		warehouse = _get_warehouse(company, abbr)
		income_account = _get_income_account(company)
		debtors_account = _get_debtors_account(company)
		cash_account = _get_cash_account(company, abbr)
		cost_center = _get_leaf_cost_center(company)

		if not all([warehouse, income_account, debtors_account, cash_account, cost_center]):
			print(f"  Skipping selling cycle for {company} - missing accounts/CC")
			continue

		for scenario_idx, scenario in enumerate(SELLING_SCENARIOS):
			# Selling in Mar-Apr 2026 (after all buying stock is received)
			day_offset = (comp_idx * 5) + (scenario_idx * 15) + 60
			base_date = add_days(getdate("2026-01-01"), day_offset)

			customer = company_customers[scenario_idx % len(company_customers)]
			tag = f"{scenario['title']} - {abbr}-{scenario_idx + 1}"

			items = _build_selling_items(scenario["items"], warehouse, income_account, cost_center)
			if not items:
				continue

			try:
				# 1. Quotation
				quotation = _create_quotation(company, currency, customer["name"], items, base_date, tag)
				if not quotation:
					continue

				# 2. Sales Order
				so_date = add_days(base_date, 3)
				sales_order = _create_sales_order(company, currency, customer["name"], items, so_date, quotation, tag)
				if not sales_order:
					continue

				# 3. Sales Invoice
				si_date = add_days(so_date, 5)
				sales_invoice = _create_sales_invoice(company, currency, customer["name"], items, si_date, sales_order, debtors_account, tag, country=comp["country"], cost_center=cost_center)
				if not sales_invoice:
					continue

				# 4. Payment Entry (Receive)
				pe_date = add_days(si_date, 7)
				_create_payment_entry_receive(sales_invoice, pe_date, cash_account)

				cycle_count += 1
				print(f"  [OK] Selling: {tag}")

			except Exception as e:
				print(f"  [FAIL] Selling: {tag} -> {e}")

		frappe.db.commit()

	print(f"  {cycle_count} selling cycles completed.")


def _build_selling_items(item_list, warehouse, income_account, cost_center):
	"""Build item rows for selling documents."""
	rows = []
	rate_map = {i["item_code"]: i["rate"] for i in SELLING_ITEMS}
	for item in item_list:
		rate = rate_map.get(item["item_code"])
		if not rate:
			continue
		rows.append({
			"item_code": item["item_code"],
			"qty": item["qty"],
			"rate": rate,
			"uom": "Nos",
			"conversion_factor": 1,
			"warehouse": warehouse,
			"income_account": income_account,
			"cost_center": cost_center,
		})
	return rows


def _create_quotation(company, currency, customer, items, posting_date, tag):
	"""Create and submit a Quotation."""
	doc = frappe.get_doc({
		"doctype": "Quotation",
		"quotation_to": "Customer",
		"party_name": customer,
		"company": company,
		"currency": currency,
		"transaction_date": posting_date,
		"valid_till": add_days(posting_date, 365),
		"items": items,
		"title": tag,
	})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()
	return doc.name


def _create_sales_order(company, currency, customer, items, transaction_date, quotation_name, tag):
	"""Create and submit a Sales Order linked to quotation."""
	delivery_date = add_days(transaction_date, 7)
	so_items = []
	qt_items = frappe.get_all("Quotation Item", filters={"parent": quotation_name},
		fields=["name", "item_code"], order_by="idx")
	qt_map = {qi["item_code"]: qi["name"] for qi in qt_items}

	for item in items:
		row = dict(item)
		row["delivery_date"] = delivery_date
		row["prevdoc_docname"] = quotation_name
		qi_name = qt_map.get(item["item_code"])
		if qi_name:
			row["quotation_item"] = qi_name
		so_items.append(row)

	doc = frappe.get_doc({
		"doctype": "Sales Order",
		"customer": customer,
		"company": company,
		"currency": currency,
		"transaction_date": transaction_date,
		"delivery_date": delivery_date,
		"items": so_items,
		"title": tag,
	})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()
	return doc.name


def _create_sales_invoice(company, currency, customer, items, posting_date, sales_order_name, debtors_account, tag, country=None, cost_center=None):
	"""Create and submit a Sales Invoice linked to Sales Order."""
	so_items = frappe.get_all("Sales Order Item", filters={"parent": sales_order_name},
		fields=["name", "item_code"], order_by="idx")
	so_map = {si["item_code"]: si["name"] for si in so_items}

	si_items = []
	for item in items:
		row = dict(item)
		row["sales_order"] = sales_order_name
		so_detail = so_map.get(item["item_code"])
		if so_detail:
			row["so_detail"] = so_detail
		si_items.append(row)

	doc_data = {
		"doctype": "Sales Invoice",
		"customer": customer,
		"company": company,
		"currency": currency,
		"posting_date": posting_date,
		"posting_time": "10:00:00",
		"set_posting_time": 1,
		"due_date": add_days(posting_date, 30),
		"debit_to": debtors_account,
		"update_stock": 1,
		"items": si_items,
	}

	# Italian e-invoicing requires taxes, company_address, customer_address
	if country == "Italy":
		vat_account = frappe.db.get_value("Account", {
			"company": company, "account_type": "Tax", "is_group": 0,
		}, "name")
		if not vat_account:
			# Create a VAT output account
			abbr = frappe.db.get_value("Company", company, "abbr")
			vat_account = f"VAT Output - {abbr}"
			if not frappe.db.exists("Account", vat_account):
				parent = frappe.db.get_value("Account", {
					"company": company, "root_type": "Liability", "is_group": 1,
				}, "name")
				frappe.get_doc({
					"doctype": "Account",
					"account_name": "VAT Output",
					"company": company,
					"parent_account": parent,
					"account_type": "Tax",
					"is_group": 0,
				}).insert(ignore_permissions=True)
		if vat_account:
			doc_data["taxes"] = [{
				"charge_type": "On Net Total",
				"account_head": vat_account,
				"description": "IVA 22%",
				"rate": 22,
				"cost_center": cost_center,
			}]
		# Set company_address
		comp_addr = frappe.db.get_value("Dynamic Link", {
			"link_doctype": "Company", "link_name": company, "parenttype": "Address",
		}, "parent")
		if comp_addr:
			doc_data["company_address"] = comp_addr
		# Set customer_address
		cust_addr = frappe.db.get_value("Dynamic Link", {
			"link_doctype": "Customer", "link_name": customer, "parenttype": "Address",
		}, "parent")
		if cust_addr:
			doc_data["customer_address"] = cust_addr

		# Set payment schedule with mode_of_payment for e-invoicing
		doc_data["payment_schedule"] = [{
			"due_date": add_days(posting_date, 30),
			"invoice_portion": 100,
			"mode_of_payment": "Wire Transfer",
		}]

	doc = frappe.get_doc(doc_data)
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()
	return doc.name


def _create_payment_entry_receive(invoice_name, posting_date, paid_to_account):
	"""Create and submit a Payment Entry (Receive) against a Sales Invoice."""
	existing = frappe.db.get_value(
		"Payment Entry Reference",
		{"reference_name": invoice_name, "reference_doctype": "Sales Invoice"},
		"parent",
	)
	if existing:
		return existing

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	pe = get_payment_entry("Sales Invoice", invoice_name)
	pe.posting_date = posting_date
	pe.reference_no = f"RCV-{invoice_name}"
	pe.reference_date = posting_date
	pe.paid_to = paid_to_account
	pe.insert(ignore_permissions=True, ignore_mandatory=True)
	pe.submit()
	return pe.name


# -- Buying Cycle --

def _create_buying_cycles():
	"""RFQ -> Purchase Order -> Purchase Invoice -> Payment Entry (Pay)."""
	print("Creating buying cycles...")
	sample_companies = _get_sample_companies()
	cycle_count = 0

	for comp_idx, comp in enumerate(sample_companies):
		company = comp["name"]
		abbr = comp["abbr"]
		currency = comp["currency"]

		company_suppliers = [s for s in SUPPLIERS if s["currency"] == currency]
		if not company_suppliers:
			company_suppliers = [s for s in SUPPLIERS if s["currency"] == "LBP"]

		warehouse = _get_warehouse(company, abbr)
		expense_account = _get_expense_account(company)
		creditors_account = _get_creditors_account(company)
		cash_account = _get_cash_account(company, abbr)
		cost_center = _get_leaf_cost_center(company)

		if not all([warehouse, expense_account, creditors_account, cash_account, cost_center]):
			print(f"  Skipping buying cycle for {company} - missing accounts/CC")
			continue

		for scenario_idx, scenario in enumerate(BUYING_SCENARIOS):
			# Buying in Jan 2026
			day_offset = (comp_idx * 4) + (scenario_idx * 8) + 3
			base_date = add_days(getdate("2026-01-01"), day_offset % 28)

			supplier = company_suppliers[scenario_idx % len(company_suppliers)]
			tag = f"{scenario['title']} - {abbr}-{scenario_idx + 1}"

			items = _build_buying_items(scenario["items"], warehouse, expense_account, cost_center)
			if not items:
				continue

			try:
				# 1. RFQ
				rfq = _create_request_for_quotation(company, currency, supplier["name"], items, base_date, tag)

				# 2. Purchase Order
				po_date = add_days(base_date, 5)
				purchase_order = _create_purchase_order(company, currency, supplier["name"], items, po_date, tag, rfq)
				if not purchase_order:
					continue

				# 3. Purchase Invoice
				pi_date = add_days(po_date, 7)
				purchase_invoice = _create_purchase_invoice(company, currency, supplier["name"], items, pi_date, purchase_order, creditors_account, tag)
				if not purchase_invoice:
					continue

				# 4. Payment Entry (Pay)
				pe_date = add_days(pi_date, 7)
				_create_payment_entry_pay(purchase_invoice, pe_date, cash_account)

				cycle_count += 1
				print(f"  [OK] Buying: {tag}")

			except Exception as e:
				print(f"  [FAIL] Buying: {tag} -> {e}")

		frappe.db.commit()

	print(f"  {cycle_count} buying cycles completed.")


def _build_buying_items(item_list, warehouse, expense_account, cost_center):
	"""Build item rows for buying documents."""
	rows = []
	rate_map = {i["item_code"]: i["rate"] for i in BUYING_ITEMS}
	for item in item_list:
		rate = rate_map.get(item["item_code"])
		if not rate:
			continue
		rows.append({
			"item_code": item["item_code"],
			"qty": item["qty"],
			"rate": rate,
			"uom": "Nos",
			"conversion_factor": 1,
			"warehouse": warehouse,
			"expense_account": expense_account,
			"cost_center": cost_center,
		})
	return rows


def _create_request_for_quotation(company, currency, supplier, items, posting_date, tag):
	"""Create and submit a Request for Quotation."""
	try:
		rfq_items = []
		for item in items:
			rfq_items.append({
				"item_code": item["item_code"],
				"qty": item["qty"],
				"rate": item["rate"],
				"uom": "Nos",
				"conversion_factor": 1,
				"warehouse": item["warehouse"],
				"schedule_date": add_days(posting_date, 14),
			})
		doc = frappe.get_doc({
			"doctype": "Request for Quotation",
			"company": company,
			"currency": currency,
			"transaction_date": posting_date,
			"message_for_supplier": f"Please provide your best quotation for: {tag}",
			"items": rfq_items,
			"suppliers": [{"supplier": supplier}],
			"title": tag,
		})
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		doc.submit()
		return doc.name
	except Exception as e:
		print(f"    RFQ warning ({tag}): {e}")
		return None


def _create_purchase_order(company, currency, supplier, items, posting_date, tag, rfq_name=None):
	"""Create and submit a Purchase Order."""
	po_items = []
	for item in items:
		row = {
			"item_code": item["item_code"],
			"qty": item["qty"],
			"rate": item["rate"],
			"uom": "Nos",
			"conversion_factor": 1,
			"warehouse": item["warehouse"],
			"expense_account": item["expense_account"],
			"cost_center": item["cost_center"],
			"schedule_date": add_days(posting_date, 7),
		}
		if rfq_name:
			row["request_for_quotation"] = rfq_name
		po_items.append(row)

	doc = frappe.get_doc({
		"doctype": "Purchase Order",
		"supplier": supplier,
		"company": company,
		"currency": currency,
		"transaction_date": posting_date,
		"schedule_date": add_days(posting_date, 7),
		"items": po_items,
		"title": tag,
	})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()
	return doc.name


def _create_purchase_invoice(company, currency, supplier, items, posting_date, po_name, creditors_account, tag):
	"""Create and submit a Purchase Invoice linked to a Purchase Order."""
	po_items = frappe.get_all("Purchase Order Item", filters={"parent": po_name},
		fields=["name", "item_code"], order_by="idx")
	po_map = {pi["item_code"]: pi["name"] for pi in po_items}

	pi_items = []
	for item in items:
		row = dict(item)
		row["purchase_order"] = po_name
		po_detail = po_map.get(item["item_code"])
		if po_detail:
			row["po_detail"] = po_detail
			row["purchase_order_item"] = po_detail
		pi_items.append(row)

	doc = frappe.get_doc({
		"doctype": "Purchase Invoice",
		"supplier": supplier,
		"company": company,
		"currency": currency,
		"posting_date": posting_date,
		"posting_time": "10:00:00",
		"set_posting_time": 1,
		"due_date": add_days(posting_date, 30),
		"credit_to": creditors_account,
		"update_stock": 1,
		"items": pi_items,
	})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()
	return doc.name


def _create_payment_entry_pay(invoice_name, posting_date, paid_from_account):
	"""Create and submit a Payment Entry (Pay) against a Purchase Invoice."""
	existing = frappe.db.get_value(
		"Payment Entry Reference",
		{"reference_name": invoice_name, "reference_doctype": "Purchase Invoice"},
		"parent",
	)
	if existing:
		return existing

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	pe = get_payment_entry("Purchase Invoice", invoice_name)
	pe.posting_date = posting_date
	pe.reference_no = f"PAY-{invoice_name}"
	pe.reference_date = posting_date
	pe.paid_from = paid_from_account
	pe.insert(ignore_permissions=True, ignore_mandatory=True)
	pe.submit()
	return pe.name


# -- Account, Warehouse & Cost Center Helpers --

def _get_sample_companies():
	"""Return a representative sample of companies for demo data."""
	companies = get_all_companies()
	sample = []
	seen_types = set()
	seen_countries = set()

	for comp in companies:
		key = (comp["type"], comp["country"])
		if key not in seen_types or comp["country"] not in seen_countries:
			sample.append(comp)
			seen_types.add(key)
			seen_countries.add(comp["country"])
		if len(sample) >= 15:
			break

	for comp in companies:
		if comp["type"] == "university" and comp not in sample:
			sample.append(comp)

	return sample


def _get_warehouse(company, abbr):
	"""Get the default stock warehouse for a company."""
	wh = f"Stores - {abbr}"
	if frappe.db.exists("Warehouse", wh):
		return wh
	return frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")


def _get_income_account(company):
	"""Get the income account for selling."""
	return (
		frappe.db.get_value("Account", {"company": company, "account_name": "Sales", "is_group": 0}, "name")
		or frappe.db.get_value("Account", {"company": company, "account_name": "Service", "is_group": 0}, "name")
		or frappe.db.get_value("Account", {"company": company, "root_type": "Income", "is_group": 0}, "name")
	)


def _get_expense_account(company):
	"""Get the expense account for buying."""
	return (
		frappe.db.get_value("Account", {"company": company, "account_name": "Cost of Goods Sold", "is_group": 0}, "name")
		or frappe.db.get_value("Account", {"company": company, "root_type": "Expense", "is_group": 0}, "name")
	)


def _get_debtors_account(company):
	"""Get the receivable (Debtors) account."""
	return frappe.db.get_value("Account", {
		"company": company, "account_type": "Receivable", "is_group": 0,
	}, "name")


def _get_creditors_account(company):
	"""Get the payable (Creditors) account."""
	return frappe.db.get_value("Account", {
		"company": company, "account_type": "Payable", "is_group": 0,
		"account_name": ["like", "%Creditor%"],
	}, "name") or frappe.db.get_value("Account", {
		"company": company, "account_type": "Payable", "is_group": 0,
	}, "name")


def _get_cash_account(company, abbr):
	"""Get the cash account for payments."""
	cash = f"Cash - {abbr}"
	if frappe.db.exists("Account", cash):
		return cash
	return (
		frappe.db.get_value("Account", {"company": company, "account_name": "Cash In Hand", "is_group": 0}, "name")
		or frappe.db.get_value("Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name")
	)


def _get_country_code(country):
	"""Return ISO country code for a country name."""
	mapping = {
		"Italy": "IT", "Canada": "CA", "Belgium": "BE",
		"Syria": "SY", "Australia": "AU", "Lebanon": "LB",
		"Switzerland": "CH", "France": "FR", "Germany": "DE",
	}
	return mapping.get(country, "")


def _get_leaf_cost_center(company):
	"""Get a leaf (non-group) cost center for a company."""
	cc = frappe.db.get_value("Cost Center", {
		"company": company, "is_group": 0,
	}, "name")
	if cc:
		return cc
	# Fallback: create a General Administration leaf cost center
	root_cc = frappe.db.get_value("Cost Center", {"company": company, "is_group": 1}, "name")
	if root_cc:
		abbr = frappe.db.get_value("Company", company, "abbr")
		leaf_name = f"General Administration - {abbr}"
		if not frappe.db.exists("Cost Center", leaf_name):
			try:
				frappe.get_doc({
					"doctype": "Cost Center",
					"cost_center_name": "General Administration",
					"company": company,
					"parent_cost_center": root_cc,
					"is_group": 0,
				}).insert(ignore_permissions=True)
			except Exception:
				pass
		return leaf_name
	return None
