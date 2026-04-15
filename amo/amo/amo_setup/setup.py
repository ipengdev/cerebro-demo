import frappe
from frappe.utils import now_datetime, getdate, add_months, add_days
from amo.amo_setup.company_definitions import (
	COMPANY_GROUPS,
	COUNTRY_CURRENCY,
	COUNTRY_TIMEZONE,
	get_all_companies,
)
from amo.amo_setup.buying_selling_cycle import (
	create_buying_selling_cycle as _create_buying_selling_cycle,
)


def after_install():
	"""Called after app install - create roles only."""
	_create_roles()
	frappe.db.commit()


def after_migrate():
	"""Called after bench migrate."""
	_create_roles()
	_ensure_mof_salary_component_fields()
	_seed_lebanon_addresses()
	frappe.db.commit()


def _seed_lebanon_addresses():
	"""Seed Lebanese address hierarchy if tables exist."""
	try:
		from amo.mof_address.seed_data import seed_lebanon_addresses
		seed_lebanon_addresses()
	except Exception:
		frappe.logger().warning("Skipping Lebanon address seeding (tables may not exist yet)")


def _create_roles():
	"""Ensure AMO roles exist."""
	roles = [
		"AMO Admin",
		"AMO Finance Manager",
		"AMO HR Manager",
		"AMO Project Manager",
		"AMO University Admin",
		"AMO School Admin",
		"AMO Monastery Admin",
	]
	for role_name in roles:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)


@frappe.whitelist()
def execute_full_setup():
	"""Master setup function - creates all AMO companies and demo data.
	Run via: bench --site <sitename> execute amo.amo_setup.setup.execute_full_setup
	"""
	frappe.only_for("Administrator")

	print("=" * 60)
	print("AMO FULL SETUP - Starting")
	print("=" * 60)

	_create_roles()
	_ensure_currencies()
	_create_company_groups()
	_create_all_companies()
	_create_cost_centers()
	_create_demo_gl_entries()
	_create_demo_journal_vouchers()
	_create_demo_bank_accounts()
	_create_demo_expenses()
	_setup_budgets()
	_create_fixed_assets()
	_create_projects()
	_create_inventory_items()
	_create_payroll_setup()
	_create_university_reporting_data()
	_create_buying_selling_cycle()

	frappe.db.commit()
	print("=" * 60)
	print("AMO FULL SETUP - Complete!")
	print(f"Created {len(get_all_companies())} companies with demo data.")
	print("=" * 60)


# ── Currency Setup ──────────────────────────────────────────────────────

def _ensure_currencies():
	"""Ensure all required currencies are enabled."""
	print("Setting up currencies...")
	currencies = ["LBP", "USD", "EUR", "CAD", "AUD", "CHF", "SYP"]
	for c in currencies:
		if frappe.db.exists("Currency", c):
			frappe.db.set_value("Currency", c, "enabled", 1)
		else:
			frappe.get_doc({
				"doctype": "Currency",
				"currency_name": c,
				"enabled": 1,
				"fraction": "Cents",
			}).insert(ignore_permissions=True)
	frappe.db.commit()


# ── Company Group & Company Creation ────────────────────────────────────

def _create_company_groups():
	"""Create the AMO parent and sub-group companies."""
	print("Creating company groups...")

	# Create parent AMO company first
	if not frappe.db.exists("Company", "AMO"):
		_create_company_doc(
			name="AMO",
			abbr="AMO",
			country="Lebanon",
			currency="LBP",
			is_group=1,
			parent_company=None,
		)

	# Create sub-groups
	subgroups = [
		("AMO - Monasteries", "AMO-MON"),
		("AMO - Schools", "AMO-SCH"),
		("AMO - University", "AMO-UNI"),
		("AMO - Social and Cultural Organizations", "AMO-SCO"),
	]
	for sg_name, sg_abbr in subgroups:
		if not frappe.db.exists("Company", sg_name):
			_create_company_doc(
				name=sg_name,
				abbr=sg_abbr,
				country="Lebanon",
				currency="LBP",
				is_group=1,
				parent_company="AMO",
			)

	frappe.db.commit()


def _create_all_companies():
	"""Create all 52 leaf companies."""
	print("Creating 52 companies...")
	companies = get_all_companies()
	for i, comp in enumerate(companies):
		if not frappe.db.exists("Company", comp["name"]):
			_create_company_doc(
				name=comp["name"],
				abbr=comp["abbr"],
				country=comp["country"],
				currency=comp["currency"],
				is_group=0,
				parent_company=comp["group"],
			)
			if (i + 1) % 10 == 0:
				frappe.db.commit()
				print(f"  Created {i + 1}/{len(companies)} companies...")

	frappe.db.commit()
	print(f"  All {len(companies)} companies created.")


def _create_company_doc(name, abbr, country, currency, is_group=0, parent_company=None):
	"""Create a single Company document."""
	try:
		company = frappe.get_doc({
			"doctype": "Company",
			"company_name": name,
			"abbr": abbr,
			"country": country,
			"default_currency": currency,
			"is_group": is_group,
			"parent_company": parent_company,
			"chart_of_accounts": _get_coa_template(country),
			"enable_perpetual_inventory": 1,
		})
		company.insert(ignore_permissions=True, ignore_mandatory=True)
		frappe.db.commit()
	except frappe.DuplicateEntryError:
		pass
	except Exception as e:
		print(f"  Warning creating {name}: {e}")


def _get_coa_template(country):
	"""Get the best COA template for the country (built-in if available)."""
	coa_map = {
		"Australia": "Australia - Chart of Accounts with Account Numbers",
		"Canada": "Canada - Plan comptable pour les provinces francophones",
	}
	return coa_map.get(country, "Standard")


# ── Cost Centers ────────────────────────────────────────────────────────

# Hierarchy: Entity root (auto-created) → Department (group) → Cost Center (leaf)
COST_CENTER_HIERARCHY = {
	"monastery": {
		"Administration": [
			"General Administration",
			"Human Resources",
			"Finance & Accounting",
			"Procurement & Supplies",
		],
		"Liturgical Services": [
			"Liturgy & Worship",
			"Choir & Music Ministry",
			"Religious Education",
		],
		"Agriculture": [
			"Farming Operations",
			"Livestock Management",
			"Agricultural Products & Sales",
		],
		"Maintenance": [
			"Building Maintenance",
			"Grounds & Landscaping",
			"Equipment & Vehicles",
		],
		"Community Services": [
			"Social Outreach",
			"Elderly Care",
			"Counseling & Spiritual Guidance",
		],
		"Guest House": [
			"Accommodations & Hospitality",
			"Food & Beverage",
			"Events & Retreats",
		],
	},

	"school": {
		"Administration": [
			"General Administration",
			"Human Resources",
			"Finance & Accounting",
			"Procurement & Supplies",
		],
		"Academic Programs": [
			"Primary Education",
			"Secondary Education",
			"Curriculum Development",
			"Examinations & Assessment",
		],
		"Student Services": [
			"Guidance & Counseling",
			"Health Services",
			"Extracurricular Activities",
		],
		"Library": [
			"Library Operations",
			"Digital Resources",
		],
		"Sports & Activities": [
			"Sports Programs",
			"Club Activities",
			"Competitions & Events",
		],
		"Maintenance": [
			"Building Maintenance",
			"Grounds & Landscaping",
			"Equipment & Vehicles",
		],
		"Transportation": [
			"Bus Fleet Operations",
			"Route Management & Logistics",
		],
		"Cafeteria": [
			"Food Services",
			"Kitchen Operations",
		],
	},

	"university": {
		"Administration": [
			"General Administration",
			"Human Resources",
			"Finance & Accounting",
			"Procurement & Supplies",
			"Legal Affairs",
		],
		"Faculty of Arts and Sciences": [
			"Teaching Operations",
			"Research Programs",
			"Laboratories",
		],
		"Faculty of Business Administration": [
			"Teaching Operations",
			"Research Programs",
			"Executive Education",
		],
		"Faculty of Engineering": [
			"Teaching Operations",
			"Research Programs",
			"Laboratories",
		],
		"Faculty of Music": [
			"Teaching Operations",
			"Performance & Studios",
			"Instrument Maintenance",
		],
		"Faculty of Public Health": [
			"Teaching Operations",
			"Research Programs",
			"Clinical Practice",
		],
		"Research Center": [
			"Research Grants",
			"Lab Operations",
			"Publications",
		],
		"Student Affairs": [
			"Student Housing",
			"Student Activities",
			"Career Services",
		],
		"Library": [
			"Library Operations",
			"Digital Resources",
			"Archives",
		],
		"IT Services": [
			"Infrastructure & Network",
			"Software & Systems",
			"Help Desk & Support",
		],
		"Facilities Management": [
			"Building Maintenance",
			"Grounds & Landscaping",
			"Utilities & Energy",
		],
		"Financial Aid Office": [
			"Scholarships",
			"Student Loans",
			"Work-Study Programs",
		],
		"Registrar": [
			"Enrollment Services",
			"Records Management",
			"Graduation & Ceremonies",
		],
	},

	"social_cultural": {
		"Administration": [
			"General Administration",
			"Human Resources",
			"Finance & Accounting",
		],
		"Cultural Programs": [
			"Art Exhibitions",
			"Cultural Events",
			"Heritage Preservation",
		],
		"Social Services": [
			"Social Aid Programs",
			"Community Support",
			"Rehabilitation Services",
		],
		"Events": [
			"Event Planning",
			"Venue Management",
			"Catering Services",
		],
		"Publications": [
			"Print Media",
			"Digital Media",
			"Distribution & Sales",
		],
		"Community Outreach": [
			"Partnerships & Alliances",
			"Volunteer Programs",
			"Awareness Campaigns",
		],
	},
}


def _get_entity_root_cc(company_name):
	"""Look up the actual root cost center name for a company from the DB.

	ERPNext auto-creates a root CC when a company is created, but the CC name
	may differ from the current company name if the company was renamed.
	"""
	# The root CC for a company is the one whose parent_cost_center is empty/null
	# or whose parent belongs to a different company (group parent).
	roots = frappe.db.sql("""
		SELECT name FROM `tabCost Center`
		WHERE company = %s
		  AND (parent_cost_center IS NULL OR parent_cost_center = ''
		       OR parent_cost_center NOT IN (
		           SELECT name FROM `tabCost Center` WHERE company = %s
		       ))
		ORDER BY lft
		LIMIT 1
	""", (company_name, company_name), as_dict=True)
	if roots:
		return roots[0]["name"]
	# Fallback: any CC for this company with is_group=1
	fallback = frappe.db.get_value("Cost Center",
		{"company": company_name, "is_group": 1}, "name")
	return fallback


def _create_cost_centers():
	"""Create cost centers per entity: Entity root → Department (group) → Cost Center (leaf).

	The top-level hierarchy (AMO → sub-groups → entities) is auto-created by
	ERPNext when companies are created with parent_company set.
	This function creates the department / cost-center layers inside each entity.
	"""
	print("Creating cost centers (department → cost center hierarchy)...")
	companies = get_all_companies()

	for comp in companies:
		dept_map = COST_CENTER_HIERARCHY.get(comp["type"], {
			"Administration": ["General Administration"],
		})
		# Look up the actual root CC name from the DB (handles renamed companies)
		entity_root = _get_entity_root_cc(comp["name"])
		if not entity_root:
			print(f"  WARNING: No root cost center found for {comp['name']}, skipping.")
			continue

		for dept_name, cc_names in dept_map.items():
			dept_full = f"{dept_name} - {comp['abbr']}"

			# Create department as a group node under entity root
			if not frappe.db.exists("Cost Center", dept_full):
				try:
					frappe.get_doc({
						"doctype": "Cost Center",
						"cost_center_name": dept_name,
						"company": comp["name"],
						"parent_cost_center": entity_root,
						"is_group": 1,
					}).insert(ignore_permissions=True, ignore_mandatory=True)
				except Exception as e:
					print(f"  Warning creating dept {dept_full}: {e}")
			else:
				# Ensure existing node is a group
				frappe.db.set_value("Cost Center", dept_full, "is_group", 1)

			# Create leaf cost centers under the department
			for cc_name in cc_names:
				cc_full = f"{cc_name} - {comp['abbr']}"
				if not frappe.db.exists("Cost Center", cc_full):
					try:
						frappe.get_doc({
							"doctype": "Cost Center",
							"cost_center_name": cc_name,
							"company": comp["name"],
							"parent_cost_center": dept_full,
							"is_group": 0,
						}).insert(ignore_permissions=True, ignore_mandatory=True)
					except Exception as e:
						print(f"  Warning creating CC {cc_full}: {e}")

	frappe.db.commit()
	print("  Cost centers created.")


@frappe.whitelist()
def rebuild_cost_centers():
	"""Delete non-root cost centers and recreate with proper hierarchy.

	Run via: bench --site <sitename> execute amo.amo_setup.setup.rebuild_cost_centers
	"""
	frappe.only_for("Administrator")
	print("Rebuilding cost center tree...")

	# --- Step 1: delete all non-root cost centers for each entity --------
	companies = get_all_companies()
	for comp in companies:
		# Find the actual root CC name from DB (handles old/renamed names)
		entity_root = _get_entity_root_cc(comp["name"])
		children = frappe.db.sql("""
			SELECT name FROM `tabCost Center`
			WHERE company = %s AND name != %s
			ORDER BY rgt - lft ASC
		""", (comp["name"], entity_root or ""), as_dict=True)
		for cc in children:
			try:
				frappe.delete_doc("Cost Center", cc["name"], force=True, ignore_permissions=True)
			except Exception as e:
				print(f"  Could not delete {cc['name']}: {e}")

	# Also delete "Main" cost centers under group companies
	for grp_name, grp_info in COMPANY_GROUPS.items():
		main_cc = f"Main - {grp_info['abbr']}"
		if frappe.db.exists("Cost Center", main_cc):
			try:
				frappe.delete_doc("Cost Center", main_cc, force=True, ignore_permissions=True)
			except Exception as e:
				print(f"  Could not delete {main_cc}: {e}")

	frappe.db.commit()
	print("  Old cost centers deleted.")

	# --- Step 2: fix parent links so tree mirrors company hierarchy ------
	_fix_cost_center_parent_links()
	frappe.db.commit()

	# --- Step 3: rebuild nested-set lft/rgt ------------------------------
	from frappe.utils.nestedset import rebuild_tree
	rebuild_tree("Cost Center")
	frappe.db.commit()

	# --- Step 4: create department → cost center nodes -------------------
	_create_cost_centers()
	print("  Cost center tree rebuilt.")


def _fix_cost_center_parent_links():
	"""Ensure root cost centers mirror the company parent hierarchy.

	AMO - AMO  (root, no parent)
	  |- AMO - Monasteries - AMO-MON   (parent = AMO - AMO)
	  |    |- <entity root CC>          (parent = AMO - Monasteries - AMO-MON)
	  |- AMO - Schools - AMO-SCH        (parent = AMO - AMO)
	  ...

	Uses DB lookups for actual CC names to handle renamed companies.
	"""
	print("  Fixing cost center parent links...")

	# Group companies -> parent is AMO root
	amo_root = "AMO - AMO"
	for grp_name, grp_info in COMPANY_GROUPS.items():
		cc_name = _get_entity_root_cc(grp_name)
		if not cc_name:
			print(f"  WARNING: No root CC for group {grp_name}")
			continue
		if grp_name == "AMO":
			frappe.db.sql(
				"UPDATE `tabCost Center` SET parent_cost_center = '', is_group = 1 WHERE name = %s",
				(cc_name,),
			)
		elif "parent" in grp_info:
			parent_grp = grp_info["parent"]
			parent_cc = _get_entity_root_cc(parent_grp)
			if parent_cc:
				frappe.db.sql(
					"UPDATE `tabCost Center` SET parent_cost_center = %s, is_group = 1 WHERE name = %s",
					(parent_cc, cc_name),
				)

	# Entity (leaf) companies -> parent is their group's root cost center
	companies = get_all_companies()
	for comp in companies:
		entity_cc = _get_entity_root_cc(comp["name"])
		if not entity_cc:
			print(f"  WARNING: No root CC for entity {comp['name']}")
			continue
		grp = comp["group"]
		parent_cc = _get_entity_root_cc(grp)
		if parent_cc:
			frappe.db.sql(
				"UPDATE `tabCost Center` SET parent_cost_center = %s, is_group = 1 WHERE name = %s",
				(parent_cc, entity_cc),
			)


@frappe.whitelist()
def fix_cost_center_tree():
	"""Fix parent links and rebuild nested-set without deleting any cost centers.

	Run via: bench --site <sitename> execute amo.amo_setup.setup.fix_cost_center_tree
	"""
	frappe.only_for("Administrator")
	print("Fixing cost center tree hierarchy...")

	# Step 1: fix parent links so tree mirrors company hierarchy
	_fix_cost_center_parent_links()
	frappe.db.commit()

	# Step 2: rebuild nested-set lft/rgt
	from frappe.utils.nestedset import rebuild_tree
	rebuild_tree("Cost Center")
	frappe.db.commit()

	# Step 3: create any missing department/CC nodes
	_create_cost_centers()

	print("Done. Cost center tree fixed.")


# ── GL & Journal Voucher Demo Data ──────────────────────────────────────

def _create_demo_gl_entries():
	"""Create demo GL entries via Journal Entries for selected companies."""
	print("Creating demo GL entries...")
	# Create sample entries for a few representative companies
	sample_companies = _get_sample_companies()

	for comp in sample_companies:
		_create_sample_journal_entry(
			comp["name"], comp["abbr"], comp["currency"],
			"Opening Balance Entry",
			debit_account=f"Cash In Hand - {comp['abbr']}",
			credit_account=f"Capital Account - {comp['abbr']}",
			amount=500000,
		)
	frappe.db.commit()
	print("  Demo GL entries created.")


def _create_demo_journal_vouchers():
	"""Create sample journal vouchers."""
	print("Creating demo journal vouchers...")
	sample_companies = _get_sample_companies()
	today = getdate()

	for comp in sample_companies:
		# Monthly expense JV
		for month_offset in range(6):
			posting_date = add_months(today, -month_offset)
			_create_sample_journal_entry(
				comp["name"], comp["abbr"], comp["currency"],
				f"Monthly Expenses - {posting_date.strftime('%B %Y')}",
				debit_account=f"Administrative Expenses - {comp['abbr']}",
				credit_account=f"Cash In Hand - {comp['abbr']}",
				amount=25000 + (month_offset * 1000),
				posting_date=posting_date,
			)

		# Multi-currency JV for Lebanese companies
		if comp["country"] == "Lebanon":
			_create_multi_currency_jv(comp)

	frappe.db.commit()
	print("  Demo journal vouchers created.")


def _create_multi_currency_jv(comp):
	"""Create a multi-currency journal voucher for Lebanese companies."""
	try:
		jv = frappe.get_doc({
			"doctype": "Journal Entry",
			"posting_date": getdate(),
			"company": comp["name"],
			"multi_currency": 1,
			"voucher_type": "Journal Entry",
			"accounts": [
				{
					"account": f"Cash In Hand - {comp['abbr']}",
					"debit_in_account_currency": 100000,
					"account_currency": "LBP",
				},
				{
					"account": f"Cash In Hand - {comp['abbr']}",
					"credit_in_account_currency": 100000,
					"account_currency": "LBP",
				},
			],
			"user_remark": "Multi-currency Demo Entry",
		})
		jv.insert(ignore_permissions=True, ignore_mandatory=True)
	except Exception:
		pass


def _create_sample_journal_entry(company, abbr, currency, title, debit_account, credit_account, amount, posting_date=None):
	"""Helper to create a sample journal entry."""
	if not posting_date:
		posting_date = getdate()
	try:
		jv = frappe.get_doc({
			"doctype": "Journal Entry",
			"posting_date": posting_date,
			"company": company,
			"voucher_type": "Journal Entry",
			"accounts": [
				{
					"account": debit_account,
					"debit_in_account_currency": amount,
				},
				{
					"account": credit_account,
					"credit_in_account_currency": amount,
				},
			],
			"user_remark": title,
		})
		jv.insert(ignore_permissions=True, ignore_mandatory=True)
	except Exception:
		pass


# ── Bank Accounts & Cash Management ─────────────────────────────────────

def _create_demo_bank_accounts():
	"""Create bank accounts and payment entries."""
	print("Creating bank accounts and cash management data...")
	sample_companies = _get_sample_companies()

	for comp in sample_companies:
		# Create Bank Account document with unique name per company
		acct_name = f"Primary Bank {comp['abbr']}"
		if not frappe.db.exists("Bank Account", {"company": comp["name"], "account_name": acct_name}):
			# Find the GL bank account
			gl_bank = frappe.db.get_value("Account", {
				"company": comp["name"], "account_type": "Bank", "is_group": 0,
			}, "name")
			if not gl_bank:
				gl_bank = frappe.db.get_value("Account", {
					"company": comp["name"], "account_type": "Bank",
				}, "name")
			try:
				frappe.get_doc({
					"doctype": "Bank Account",
					"account_name": acct_name,
					"bank": _ensure_bank("Bank of Beirut" if comp["country"] == "Lebanon" else "International Bank"),
					"company": comp["name"],
					"account": gl_bank,
					"is_default": 1,
					"is_company_account": 1,
				}).insert(ignore_permissions=True, ignore_mandatory=True)
			except Exception as e:
				print(f"    Bank account warning ({comp['name']}): {e}")

	frappe.db.commit()
	print("  Bank accounts created.")


def _ensure_bank(bank_name):
	"""Ensure bank exists."""
	if not frappe.db.exists("Bank", bank_name):
		frappe.get_doc({"doctype": "Bank", "bank_name": bank_name}).insert(ignore_permissions=True)
	return bank_name


# ── Expenses Demo Data ──────────────────────────────────────────────────

def _create_demo_expenses():
	"""Create demo expense entries."""
	print("Creating demo expense entries...")
	sample_companies = _get_sample_companies()
	today = getdate()

	expense_types = [
		"Utilities Expense", "Maintenance Expense",
		"Travel Expense", "Charitable Activities Expense",
	]

	for comp in sample_companies:
		for i, exp_type in enumerate(expense_types):
			for month in range(3):
				_create_sample_journal_entry(
					comp["name"], comp["abbr"], comp["currency"],
					f"{exp_type} - Month {month + 1}",
					debit_account=f"Administrative Expenses - {comp['abbr']}",
					credit_account=f"Cash In Hand - {comp['abbr']}",
					amount=5000 + (i * 1000) + (month * 500),
					posting_date=add_months(today, -month),
				)

	frappe.db.commit()
	print("  Expense entries created.")


# ── Budget & Planning ───────────────────────────────────────────────────

def _setup_budgets():
	"""Create budgets for companies."""
	print("Setting up budgets...")
	sample_companies = _get_sample_companies()
	fiscal_year = _ensure_fiscal_year()

	for comp in sample_companies:
		if not frappe.db.exists("Budget", {"company": comp["name"], "from_fiscal_year": fiscal_year}):
			# Use the entity root cost center (auto-created with the company)
			cc = f"{comp['name']} - {comp['abbr']}"
			if not frappe.db.exists("Cost Center", cc):
				continue
			expr_acct = frappe.db.get_value("Account", {"company": comp["name"], "account_name": "Administrative Expenses"}, "name")
			if not cc or not expr_acct:
				continue
			try:
				budget = frappe.get_doc({
					"doctype": "Budget",
					"company": comp["name"],
					"from_fiscal_year": fiscal_year,
					"to_fiscal_year": fiscal_year,
					"budget_against": "Cost Center",
					"cost_center": cc,
					"account": expr_acct,
					"budget_amount": 600000,
					"applicable_on_booking_actual_expenses": 1,
					"action_if_annual_budget_exceeded": "Warn",
					"action_if_accumulated_monthly_budget_exceeded": "Warn",
				})
				budget.insert(ignore_permissions=True, ignore_mandatory=True)
			except Exception as e:
				print(f"    Budget warning ({comp['name']}): {e}")

	frappe.db.commit()
	print("  Budgets created.")


def _ensure_fiscal_year():
	"""Ensure current fiscal year exists."""
	year = getdate().year
	fy_name = f"{year}"
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
	return fy_name


# ── Fixed Assets ────────────────────────────────────────────────────────

def _create_fixed_assets():
	"""Create asset categories, locations, and demo assets."""
	print("Setting up fixed assets...")

	# Asset Categories
	categories = [
		{"name": "Buildings", "depreciation_method": "Straight Line", "total_number_of_depreciations": 480, "frequency_of_depreciation": 1},
		{"name": "Furniture and Equipment", "depreciation_method": "Straight Line", "total_number_of_depreciations": 120, "frequency_of_depreciation": 1},
		{"name": "Vehicles", "depreciation_method": "Straight Line", "total_number_of_depreciations": 60, "frequency_of_depreciation": 1},
		{"name": "IT Equipment", "depreciation_method": "Straight Line", "total_number_of_depreciations": 36, "frequency_of_depreciation": 1},
		{"name": "Library Books", "depreciation_method": "Straight Line", "total_number_of_depreciations": 60, "frequency_of_depreciation": 1},
		{"name": "Laboratory Equipment", "depreciation_method": "Straight Line", "total_number_of_depreciations": 84, "frequency_of_depreciation": 1},
	]

	for cat in categories:
		if not frappe.db.exists("Asset Category", cat["name"]):
			try:
				frappe.get_doc({
					"doctype": "Asset Category",
					"asset_category_name": cat["name"],
					"enable_cwip_accounting": 1,
					"finance_books": [{
						"depreciation_method": cat["depreciation_method"],
						"total_number_of_depreciations": cat["total_number_of_depreciations"],
						"frequency_of_depreciation": cat["frequency_of_depreciation"],
					}],
				}).insert(ignore_permissions=True, ignore_mandatory=True)
			except Exception:
				pass

	# Asset Locations
	locations = [
		"Main Building", "Chapel", "Library", "Dormitory", "Kitchen",
		"Farm", "Workshop", "Guest House", "Office Building",
		"Classroom Block A", "Classroom Block B", "Laboratory",
		"Auditorium", "Sports Complex", "Parking Lot",
	]

	for loc in locations:
		if not frappe.db.exists("Location", loc):
			try:
				frappe.get_doc({
					"doctype": "Location",
					"location_name": loc,
				}).insert(ignore_permissions=True)
			except Exception:
				pass

	# Create Fixed Asset Items (required by ERPNext for Asset creation)
	fixed_asset_items = [
		{"item_code": "AMO-FA-BLD", "item_name": "Building", "asset_category": "Buildings"},
		{"item_code": "AMO-FA-FRN", "item_name": "Furniture and Equipment", "asset_category": "Furniture and Equipment"},
		{"item_code": "AMO-FA-VEH", "item_name": "Vehicle", "asset_category": "Vehicles"},
		{"item_code": "AMO-FA-ITE", "item_name": "IT Equipment", "asset_category": "IT Equipment"},
		{"item_code": "AMO-FA-LIB", "item_name": "Library Books", "asset_category": "Library Books"},
		{"item_code": "AMO-FA-LAB", "item_name": "Laboratory Equipment", "asset_category": "Laboratory Equipment"},
	]
	for fa_item in fixed_asset_items:
		if not frappe.db.exists("Item", fa_item["item_code"]):
			try:
				frappe.get_doc({
					"doctype": "Item",
					"item_code": fa_item["item_code"],
					"item_name": fa_item["item_name"],
					"item_group": "All Item Groups",
					"is_fixed_asset": 1,
					"is_stock_item": 0,
					"asset_category": fa_item["asset_category"],
				}).insert(ignore_permissions=True)
			except Exception:
				pass

	# Create demo assets for sample companies
	sample_companies = _get_sample_companies()
	today = getdate()

	asset_templates = [
		{"name": "Main Building", "category": "Buildings", "item_code": "AMO-FA-BLD", "location": "Main Building", "value": 5000000},
		{"name": "Office Furniture Set", "category": "Furniture and Equipment", "item_code": "AMO-FA-FRN", "location": "Office Building", "value": 50000},
		{"name": "Transport Van", "category": "Vehicles", "item_code": "AMO-FA-VEH", "location": "Parking Lot", "value": 120000},
		{"name": "Server Rack", "category": "IT Equipment", "item_code": "AMO-FA-ITE", "location": "Office Building", "value": 30000},
	]

	for comp in sample_companies[:5]:
		for tmpl in asset_templates:
			asset_name = f"{tmpl['name']} - {comp['abbr']}"
			if not frappe.db.exists("Asset", {"asset_name": asset_name, "company": comp["name"]}):
				try:
					frappe.get_doc({
						"doctype": "Asset",
						"asset_name": asset_name,
						"item_code": tmpl["item_code"],
						"asset_category": tmpl["category"],
						"company": comp["name"],
						"location": tmpl["location"],
						"purchase_date": add_months(today, -24),
						"available_for_use_date": add_months(today, -23),
						"gross_purchase_amount": tmpl["value"],
						"net_purchase_amount": tmpl["value"],
						"asset_owner": "Company",
						"asset_type": "Existing Asset",
					}).insert(ignore_permissions=True, ignore_mandatory=True)
				except Exception as e:
					print(f"    Asset warning ({asset_name}): {e}")

	# WIP Asset
	for comp in sample_companies[:3]:
		wip_name = f"New Wing Construction - {comp['abbr']}"
		if not frappe.db.exists("Asset", {"asset_name": wip_name, "company": comp["name"]}):
			try:
				frappe.get_doc({
					"doctype": "Asset",
					"asset_name": wip_name,
					"item_code": "AMO-FA-BLD",
					"asset_category": "Buildings",
					"company": comp["name"],
					"location": "Main Building",
					"purchase_date": add_months(today, -6),
					"gross_purchase_amount": 2000000,
					"net_purchase_amount": 2000000,
					"asset_owner": "Company",
					"asset_type": "Existing Asset",
				}).insert(ignore_permissions=True, ignore_mandatory=True)
			except Exception as e:
				print(f"    WIP Asset warning ({wip_name}): {e}")

	frappe.db.commit()
	print("  Fixed assets setup complete.")


# ── Project Management ──────────────────────────────────────────────────

def _create_projects():
	"""Create demo projects."""
	print("Creating projects...")
	sample_companies = _get_sample_companies()
	today = getdate()

	project_templates = {
		"monastery": [
			{"name": "Chapel Restoration", "type": "Internal", "status": "Open"},
			{"name": "Agricultural Development", "type": "Internal", "status": "Open"},
			{"name": "Guest House Renovation", "type": "Internal", "status": "Open"},
		],
		"school": [
			{"name": "Curriculum Development 2026", "type": "Internal", "status": "Open"},
			{"name": "Campus Expansion", "type": "Internal", "status": "Open"},
			{"name": "Digital Learning Platform", "type": "Internal", "status": "Open"},
		],
		"university": [
			{"name": "Research Lab Setup", "type": "Internal", "status": "Open"},
			{"name": "Accreditation Preparation", "type": "Internal", "status": "Open"},
			{"name": "Student Portal Development", "type": "Internal", "status": "Open"},
			{"name": "Faculty Development Program", "type": "Internal", "status": "Open"},
		],
		"social_cultural": [
			{"name": "Annual Cultural Festival", "type": "Internal", "status": "Open"},
			{"name": "Community Outreach Program", "type": "Internal", "status": "Open"},
		],
	}

	for comp in sample_companies:
		templates = project_templates.get(comp["type"], [])
		for tmpl in templates:
			proj_name = f"{tmpl['name']} - {comp['name']}"
			# Create or get the project
			project_doc_name = frappe.db.get_value("Project", {"project_name": proj_name}, "name")
			if not project_doc_name:
				try:
					project = frappe.get_doc({
						"doctype": "Project",
						"project_name": proj_name,
						"company": comp["name"],
						"project_type": tmpl["type"],
						"status": tmpl["status"],
						"expected_start_date": today,
						"expected_end_date": add_months(today, 6),
						"cost_center": f"{comp['name']} - {comp['abbr']}",
					})
					project.insert(ignore_permissions=True, ignore_mandatory=True)
					project_doc_name = project.name
				except Exception as e:
					print(f"    Project warning ({proj_name}): {e}")
					continue

			# Add tasks (runs even if project already existed)
			for idx, task_name in enumerate([
				"Planning", "Procurement", "Execution", "Review", "Completion"
			]):
				if not frappe.db.exists("Task", {"subject": f"{task_name} - {proj_name}"}):
					try:
						frappe.get_doc({
							"doctype": "Task",
							"subject": f"{task_name} - {proj_name}",
							"project": project_doc_name,
							"company": comp["name"],
							"status": "Open" if idx > 0 else "Working",
							"exp_start_date": add_months(today, idx),
							"exp_end_date": add_months(today, idx + 1),
						}).insert(ignore_permissions=True, ignore_mandatory=True)
					except Exception:
						pass
# ── Inventory ───────────────────────────────────────────────────────────

def _create_inventory_items():
	"""Create inventory items and warehouses."""
	print("Setting up inventory...")

	# Item Groups
	item_groups = [
		"Office Supplies", "Cleaning Supplies", "Kitchen Supplies",
		"Educational Materials", "Religious Items", "Agricultural Supplies",
		"IT Consumables", "Maintenance Supplies",
	]

	for group_name in item_groups:
		if not frappe.db.exists("Item Group", group_name):
			try:
				frappe.get_doc({
					"doctype": "Item Group",
					"item_group_name": group_name,
					"parent_item_group": "All Item Groups",
				}).insert(ignore_permissions=True)
			except Exception:
				pass

	# Items
	items = [
		{"item_code": "AMO-OFF-001", "item_name": "A4 Paper Ream", "item_group": "Office Supplies", "stock_uom": "Nos", "valuation_rate": 5},
		{"item_code": "AMO-OFF-002", "item_name": "Pen Box (12pc)", "item_group": "Office Supplies", "stock_uom": "Nos", "valuation_rate": 3},
		{"item_code": "AMO-OFF-003", "item_name": "Printer Toner", "item_group": "Office Supplies", "stock_uom": "Nos", "valuation_rate": 45},
		{"item_code": "AMO-CLN-001", "item_name": "Cleaning Detergent", "item_group": "Cleaning Supplies", "stock_uom": "Nos", "valuation_rate": 8},
		{"item_code": "AMO-EDU-001", "item_name": "Textbook Set", "item_group": "Educational Materials", "stock_uom": "Nos", "valuation_rate": 30},
		{"item_code": "AMO-EDU-002", "item_name": "Lab Kit", "item_group": "Educational Materials", "stock_uom": "Nos", "valuation_rate": 120},
		{"item_code": "AMO-REL-001", "item_name": "Liturgical Candles (100pc)", "item_group": "Religious Items", "stock_uom": "Nos", "valuation_rate": 25},
		{"item_code": "AMO-AGR-001", "item_name": "Olive Oil (5L)", "item_group": "Agricultural Supplies", "stock_uom": "Nos", "valuation_rate": 20},
		{"item_code": "AMO-IT-001", "item_name": "Network Cable (50m)", "item_group": "IT Consumables", "stock_uom": "Nos", "valuation_rate": 15},
		{"item_code": "AMO-MNT-001", "item_name": "Light Bulb LED", "item_group": "Maintenance Supplies", "stock_uom": "Nos", "valuation_rate": 4},
	]

	for item in items:
		if not frappe.db.exists("Item", item["item_code"]):
			try:
				frappe.get_doc({
					"doctype": "Item",
					"item_code": item["item_code"],
					"item_name": item["item_name"],
					"item_group": item["item_group"],
					"stock_uom": item["stock_uom"],
					"is_stock_item": 1,
					"valuation_rate": item["valuation_rate"],
				}).insert(ignore_permissions=True)
			except Exception:
				pass

	frappe.db.commit()
	print("  Inventory items created.")


# ── Payroll Setup ───────────────────────────────────────────────────────

def _create_payroll_setup():
	"""Create payroll components per country."""
	print("Setting up payroll...")

	# Country-specific payroll components
	payroll_configs = {
		"Lebanon": {
			"components": [
				{"name": "Basic Salary", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Transportation Allowance", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "NSSF Employee Contribution", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "NSSF Employer Contribution", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "End of Service Indemnity", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Housing Allowance - LB", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Family Allowance - LB", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Income Tax - LB", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Canada": {
			"components": [
				{"name": "Basic Salary - CA", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "CPP Employee", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "CPP Employer", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "EI Employee", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "EI Employer", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Federal Tax - CA", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Provincial Tax - CA", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Health Insurance - CA", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Australia": {
			"components": [
				{"name": "Basic Salary - AU", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Superannuation", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "PAYG Withholding", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Medicare Levy", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Leave Loading", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Belgium": {
			"components": [
				{"name": "Basic Salary - BE", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Social Security - BE", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Income Tax - BE", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Meal Vouchers - BE", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "13th Month Salary - BE", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Holiday Pay - BE", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Italy": {
			"components": [
				{"name": "Basic Salary - IT", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "INPS Contribution", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "IRPEF", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "TFR (Severance)", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "13th Month - IT", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "14th Month - IT", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Switzerland": {
			"components": [
				{"name": "Basic Salary - CH", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "AHV/IV/EO", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "ALV (Unemployment)", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "BVG (Pension)", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Quellensteuer (Withholding Tax)", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "KTG (Daily Sickness)", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
			],
		},
		"Syria": {
			"components": [
				{"name": "Basic Salary - SY", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Social Insurance - SY", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Income Tax - SY", "type": "Deduction", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Housing Allowance - SY", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
				{"name": "Transport Allowance - SY", "type": "Earning", "based_on": "", "amount_based_on_formula": 0},
			],
		},
	}

	for country, config in payroll_configs.items():
		for comp_data in config["components"]:
			if not frappe.db.exists("Salary Component", comp_data["name"]):
				try:
					frappe.get_doc({
						"doctype": "Salary Component",
						"salary_component": comp_data["name"],
						"type": comp_data["type"],
						"salary_component_abbr": comp_data["name"][:10].upper().replace(" ", ""),
					}).insert(ignore_permissions=True, ignore_mandatory=True)
				except Exception:
					pass

	# Create salary structures per country
	_create_salary_structures(payroll_configs)

	frappe.db.commit()
	print("  Payroll setup complete.")


def _create_salary_structures(payroll_configs):
	"""Create salary structures for each country."""
	companies = get_all_companies()
	country_companies = {}
	for comp in companies:
		country_companies.setdefault(comp["country"], []).append(comp)

	for country, comps in country_companies.items():
		config = payroll_configs.get(country, payroll_configs["Lebanon"])
		ss_name = f"AMO Standard - {country}"

		if not frappe.db.exists("Salary Structure", ss_name):
			try:
				earnings = []
				deductions = []
				for comp_data in config["components"]:
					row = {
						"salary_component": comp_data["name"],
						"amount": 3000 if comp_data["type"] == "Earning" else 500,
						"formula": "",
					}
					if comp_data["type"] == "Earning":
						earnings.append(row)
					else:
						deductions.append(row)

				frappe.get_doc({
					"doctype": "Salary Structure",
					"name": ss_name,
					"company": comps[0]["name"],
					"is_active": "Yes",
					"payroll_frequency": "Monthly",
					"currency": COUNTRY_CURRENCY.get(country, "LBP"),
					"earnings": earnings,
					"deductions": deductions,
				}).insert(ignore_permissions=True, ignore_mandatory=True)
			except Exception:
				pass


# ── University Reporting Data ───────────────────────────────────────────

def _create_university_reporting_data():
	"""Create demo data for university-specific reporting."""
	print("Creating university reporting data...")

	# Create custom fields for tuition and scholarship tracking
	# using journal entries with specific remarks for filtering

	university_companies = [c for c in get_all_companies() if c["type"] == "university"]
	today = getdate()

	faculties = [
		"Faculty of Arts and Sciences",
		"Faculty of Business Administration",
		"Faculty of Engineering",
		"Faculty of Music",
		"Faculty of Public Health",
	]

	programs = {
		"Faculty of Arts and Sciences": ["BA English", "BA Psychology", "BS Mathematics", "BS Biology"],
		"Faculty of Business Administration": ["BBA", "MBA", "BS Accounting"],
		"Faculty of Engineering": ["BE Computer Science", "BE Civil", "BE Electrical"],
		"Faculty of Music": ["BA Music Performance", "BA Musicology"],
		"Faculty of Public Health": ["BS Nursing", "BS Nutrition", "MPH"],
	}

	for comp in university_companies:
		# Faculty budget entries
		for fac in faculties:
			for month in range(6):
				posting_date = add_months(today, -month)
				# Revenue (tuition)
				_create_sample_journal_entry(
					comp["name"], comp["abbr"], comp["currency"],
					f"Tuition Revenue - {fac} - {posting_date.strftime('%b %Y')}",
					debit_account=f"Cash In Hand - {comp['abbr']}",
					credit_account=f"Direct Income - {comp['abbr']}",
					amount=150000 + (month * 10000),
					posting_date=posting_date,
				)
				# Expenses
				_create_sample_journal_entry(
					comp["name"], comp["abbr"], comp["currency"],
					f"Faculty Expenses - {fac} - {posting_date.strftime('%b %Y')}",
					debit_account=f"Administrative Expenses - {comp['abbr']}",
					credit_account=f"Cash In Hand - {comp['abbr']}",
					amount=80000 + (month * 5000),
					posting_date=posting_date,
				)

		# Scholarship entries
		for month in range(6):
			posting_date = add_months(today, -month)
			_create_sample_journal_entry(
				comp["name"], comp["abbr"], comp["currency"],
				f"Scholarship Disbursement - {posting_date.strftime('%b %Y')}",
				debit_account=f"Administrative Expenses - {comp['abbr']}",
				credit_account=f"Cash In Hand - {comp['abbr']}",
				amount=45000 + (month * 3000),
				posting_date=posting_date,
			)

	frappe.db.commit()
	print("  University reporting data created.")


# ── Helpers ─────────────────────────────────────────────────────────────

def _get_sample_companies():
	"""Return a representative sample of companies for demo data."""
	companies = get_all_companies()
	sample = []

	# Pick companies across all types and countries
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

	# Ensure all universities are included
	for comp in companies:
		if comp["type"] == "university" and comp not in sample:
			sample.append(comp)

	return sample


# ════════════════════════════════════════════════════════════════
#  MoF Report — Custom Fields on Salary Component
# ════════════════════════════════════════════════════════════════

_MOF_R5_R10_OPTIONS = "\n".join([
	"",
	"100 - Salaries & Supplements (رواتب واجور ومكافآت وملحقاتها)",
	"110 - Cash/In-Kind Benefits (تعويضات ومنافع نقدية وعينية)",
	"130 - Transport Deduction (بدل نقل)",
	"140 - Representation Deduction (بدل تمثيل)",
	"150 - Other Deductions / CNSS (اقتطاعات اخرى)",
])

_MOF_R6_OPTIONS = "\n".join([
	"",
	"100 - Basic Salary (الراتب الأساسي)",
	"110 - Representation (بدل تمثيل)",
	"120 - Overtime (عمل إضافي)",
	"130 - Family Allowance Spouse (تعويض عائلي عن الزوجة)",
	"140 - Family Allowance Children (تعويض عائلي عن الأولاد)",
	"150 - Transport (بدل نقل)",
	"160 - Car Allowance (بدل سيارة)",
	"170 - Housing (بدل سكن)",
	"180 - Food (بدل طعام)",
	"190 - Clothing (بدل ملبس)",
	"200 - Fund Compensation (تعويض صندوق)",
	"210 - Health Insurance (تأمينات صحية)",
	"220 - Education Grants (منح تعليم)",
	"230 - Marriage Grants (منح زواج)",
	"240 - Birth Grants (منح ولادة)",
	"250 - Sick Leave Assistance (مساعدات مرضية)",
	"260 - Death Assistance (مساعدات وفاة)",
	"300 - Other Income (إيرادات أخرى)",
])

_MOF_CUSTOM_FIELDS = [
	{
		"fieldname": "mof_r5_r10_line",
		"label": "MoF R5/R10 Line",
		"fieldtype": "Select",
		"options": _MOF_R5_R10_OPTIONS,
		"description": "Maps this component to the corresponding line on MoF R5 (Annual Tax Declaration) and R10 (Periodic Tax Statement) reports.",
		"insert_after": "type",
	},
	{
		"fieldname": "mof_r6_line",
		"label": "MoF R6 Line",
		"fieldtype": "Select",
		"options": _MOF_R6_OPTIONS,
		"description": "Maps this component to the corresponding line on MoF R6 (Annual Individual Income Statement) report.",
		"insert_after": "mof_r5_r10_line",
	},
]


def _ensure_mof_salary_component_fields():
	"""Create MoF mapping custom fields on Salary Component if they don't exist."""
	for f in _MOF_CUSTOM_FIELDS:
		key = {"dt": "Salary Component", "fieldname": f["fieldname"]}
		if not frappe.db.exists("Custom Field", key):
			frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "Salary Component",
				**f,
			}).insert(ignore_permissions=True)
		else:
			# Update options in case they changed
			cf_name = frappe.db.get_value("Custom Field", key)
			frappe.db.set_value("Custom Field", cf_name, "options", f["options"])

	# Auto-populate field values for known CNSS split components
	_AUTO_MAPPINGS = {
		"CNSS Employee - Sickness (2%)": {"mof_r5_r10_line": "150", "mof_r6_line": ""},
		"CNSS Employee - Maternity (1%)": {"mof_r5_r10_line": "150", "mof_r6_line": ""},
		"CNSS Employer - Maternity (1%)": {"mof_r5_r10_line": "150", "mof_r6_line": ""},
	}
	for comp_name, mappings in _AUTO_MAPPINGS.items():
		if frappe.db.exists("Salary Component", comp_name):
			for field, prefix in mappings.items():
				if not prefix:
					continue
				current = frappe.db.get_value("Salary Component", comp_name, field)
				if not current:
					# Find the full option value by matching the prefix
					options = _MOF_R5_R10_OPTIONS if "r5" in field else _MOF_R6_OPTIONS
					for opt in options.split("\n"):
						if opt.startswith(prefix + " "):
							frappe.db.set_value("Salary Component", comp_name, field, opt)
							break
