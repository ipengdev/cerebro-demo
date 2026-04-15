# Country-specific Chart of Accounts templates for AMO companies
# Each country gets a localized COA structure

def get_chart_of_accounts(country, company_type="monastery"):
	"""Return chart of accounts tree for a given country and company type."""
	base_accounts = _get_base_accounts(country)

	# Add education-specific accounts for schools and universities
	if company_type in ("school", "university"):
		base_accounts = _add_education_accounts(base_accounts, company_type)

	return base_accounts


def _get_base_accounts(country):
	"""Standard COA structure, adapted by country."""
	# Map country to standard ERPNext template name
	country_coa_map = {
		"Lebanon": "Lebanon - Chart of Accounts",
		"Canada": "Canada - Chart of Accounts",
		"Australia": "Australia - Chart of Accounts",
		"Belgium": "Belgium - PCMN Chart of Accounts",
		"Italy": "Italy - Piano dei Conti",
		"Switzerland": "Switzerland - Chart of Accounts",
		"Syria": "Syria - Chart of Accounts",
	}
	return country_coa_map.get(country, "Standard")


def get_additional_accounts(company_name, company_type, country):
	"""Return list of additional account dicts to create after COA setup."""
	currency = {
		"Lebanon": "LBP", "Canada": "CAD", "Australia": "AUD",
		"Belgium": "EUR", "Italy": "EUR", "Switzerland": "CHF", "Syria": "SYP",
	}.get(country, "LBP")

	accounts = []

	# ── Cash & Bank accounts ─────────────────────────────────────────────
	accounts.extend([
		{
			"account_name": "Main Cash Account",
			"parent_account": f"Cash In Hand - {company_name}",
			"account_type": "Cash",
			"account_currency": currency,
		},
		{
			"account_name": "USD Cash Account",
			"parent_account": f"Cash In Hand - {company_name}",
			"account_type": "Cash",
			"account_currency": "USD",
		},
		{
			"account_name": "Primary Bank Account",
			"parent_account": f"Bank Accounts - {company_name}",
			"account_type": "Bank",
			"account_currency": currency,
		},
		{
			"account_name": "USD Bank Account",
			"parent_account": f"Bank Accounts - {company_name}",
			"account_type": "Bank",
			"account_currency": "USD",
		},
	])

	# ── Multi-currency accounts ──────────────────────────────────────────
	if country == "Lebanon":
		accounts.append({
			"account_name": "EUR Bank Account",
			"parent_account": f"Bank Accounts - {company_name}",
			"account_type": "Bank",
			"account_currency": "EUR",
		})

	# ── Fixed Asset accounts ─────────────────────────────────────────────
	accounts.extend([
		{
			"account_name": "Buildings",
			"parent_account": f"Fixed Assets - {company_name}",
			"account_type": "Fixed Asset",
			"account_currency": currency,
		},
		{
			"account_name": "Furniture and Equipment",
			"parent_account": f"Fixed Assets - {company_name}",
			"account_type": "Fixed Asset",
			"account_currency": currency,
		},
		{
			"account_name": "Vehicles",
			"parent_account": f"Fixed Assets - {company_name}",
			"account_type": "Fixed Asset",
			"account_currency": currency,
		},
		{
			"account_name": "IT Equipment",
			"parent_account": f"Fixed Assets - {company_name}",
			"account_type": "Fixed Asset",
			"account_currency": currency,
		},
		{
			"account_name": "Capital Work in Progress",
			"parent_account": f"Fixed Assets - {company_name}",
			"account_type": "Capital Work in Progress",
			"account_currency": currency,
		},
		{
			"account_name": "Accumulated Depreciation - Buildings",
			"parent_account": f"Depreciation - {company_name}",
			"account_type": "Accumulated Depreciation",
			"account_currency": currency,
		},
		{
			"account_name": "Accumulated Depreciation - Equipment",
			"parent_account": f"Depreciation - {company_name}",
			"account_type": "Accumulated Depreciation",
			"account_currency": currency,
		},
	])

	# ── Expense accounts ─────────────────────────────────────────────────
	accounts.extend([
		{
			"account_name": "Utilities Expense",
			"parent_account": f"Administrative Expenses - {company_name}",
			"account_type": "Expense Account",
			"account_currency": currency,
		},
		{
			"account_name": "Maintenance Expense",
			"parent_account": f"Administrative Expenses - {company_name}",
			"account_type": "Expense Account",
			"account_currency": currency,
		},
		{
			"account_name": "Travel Expense",
			"parent_account": f"Administrative Expenses - {company_name}",
			"account_type": "Expense Account",
			"account_currency": currency,
		},
		{
			"account_name": "Charitable Activities Expense",
			"parent_account": f"Administrative Expenses - {company_name}",
			"account_type": "Expense Account",
			"account_currency": currency,
		},
	])

	# ── Education-specific accounts ──────────────────────────────────────
	if company_type in ("school", "university"):
		accounts.extend([
			{
				"account_name": "Tuition Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
			{
				"account_name": "Registration Fees Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
			{
				"account_name": "Scholarships Expense",
				"parent_account": f"Administrative Expenses - {company_name}",
				"account_type": "Expense Account",
				"account_currency": currency,
			},
			{
				"account_name": "Financial Aid Expense",
				"parent_account": f"Administrative Expenses - {company_name}",
				"account_type": "Expense Account",
				"account_currency": currency,
			},
			{
				"account_name": "Laboratory Materials Expense",
				"parent_account": f"Administrative Expenses - {company_name}",
				"account_type": "Expense Account",
				"account_currency": currency,
			},
		])

	if company_type == "university":
		accounts.extend([
			{
				"account_name": "Research Grants Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
			{
				"account_name": "Faculty Compensation",
				"parent_account": f"Administrative Expenses - {company_name}",
				"account_type": "Expense Account",
				"account_currency": currency,
			},
			{
				"account_name": "Program Development Expense",
				"parent_account": f"Administrative Expenses - {company_name}",
				"account_type": "Expense Account",
				"account_currency": currency,
			},
		])

	# ── Donation/Revenue accounts for monasteries ────────────────────────
	if company_type == "monastery":
		accounts.extend([
			{
				"account_name": "Donations Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
			{
				"account_name": "Liturgical Services Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
			{
				"account_name": "Agricultural Revenue",
				"parent_account": f"Direct Income - {company_name}",
				"account_type": "Income Account",
				"account_currency": currency,
			},
		])

	return accounts


def _add_education_accounts(coa_template, company_type):
	"""Augment COA for education entities."""
	return coa_template
