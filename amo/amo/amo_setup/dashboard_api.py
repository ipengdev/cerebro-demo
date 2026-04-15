import frappe
from frappe.utils import getdate, add_months, flt

# ── Shared helpers ──────────────────────────────────────────────────────

UNI_CONDITION = "je.company LIKE '%%Antonine University%%'"
AMO_CONDITION = "(je.company LIKE '%%AMO%%' OR je.company LIKE '%%Monastery%%' OR je.company LIKE '%%Antonine%%')"

FACULTIES = [
	"Faculty of Arts and Sciences",
	"Faculty of Business Administration",
	"Faculty of Engineering",
	"Faculty of Music",
	"Faculty of Public Health",
]


def _uni_conditions(company=None):
	if company:
		return "je.company = %s", [company]
	return UNI_CONDITION, []


def _date_range(months_back=6):
	today = getdate()
	return add_months(today, -months_back), today


# ═══════════════════════════════════════════════════════════════════════
# 1. Faculty & Program Financial Visibility
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_faculty_program_data(company=None):
	"""Faculty-level revenue, expenses, surplus, and per-faculty KPIs."""
	frappe.only_for(["Administrator", "AMO Admin", "AMO University Admin", "AMO Finance Manager"])

	cond, params = _uni_conditions(company)
	start, _ = _date_range(12)

	# Revenue & expenses per faculty
	faculty_data = frappe.db.sql(f"""
		SELECT
			CASE
				WHEN je.user_remark LIKE '%%Faculty of Arts%%' THEN 'Faculty of Arts and Sciences'
				WHEN je.user_remark LIKE '%%Faculty of Business%%' THEN 'Faculty of Business Administration'
				WHEN je.user_remark LIKE '%%Faculty of Engineering%%' THEN 'Faculty of Engineering'
				WHEN je.user_remark LIKE '%%Faculty of Music%%' THEN 'Faculty of Music'
				WHEN je.user_remark LIKE '%%Faculty of Public Health%%' THEN 'Faculty of Public Health'
				ELSE 'Other'
			END as faculty,
			SUM(CASE WHEN je.user_remark LIKE '%%Tuition Revenue%%' THEN jea.credit_in_account_currency ELSE 0 END) as revenue,
			SUM(CASE WHEN je.user_remark LIKE '%%Faculty Expenses%%' THEN jea.debit_in_account_currency ELSE 0 END) as expenses
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND je.posting_date >= %s
			AND (je.user_remark LIKE '%%Tuition Revenue%%' OR je.user_remark LIKE '%%Faculty Expenses%%')
		GROUP BY faculty
		HAVING faculty != 'Other'
		ORDER BY revenue DESC
	""", params + [start], as_dict=True)

	# Monthly trend per faculty
	monthly = frappe.db.sql(f"""
		SELECT
			CASE
				WHEN je.user_remark LIKE '%%Faculty of Arts%%' THEN 'Arts & Sciences'
				WHEN je.user_remark LIKE '%%Faculty of Business%%' THEN 'Business'
				WHEN je.user_remark LIKE '%%Faculty of Engineering%%' THEN 'Engineering'
				WHEN je.user_remark LIKE '%%Faculty of Music%%' THEN 'Music'
				WHEN je.user_remark LIKE '%%Faculty of Public Health%%' THEN 'Public Health'
				ELSE 'Other'
			END as faculty,
			DATE_FORMAT(je.posting_date, '%%Y-%%m') as period,
			SUM(CASE WHEN je.user_remark LIKE '%%Tuition Revenue%%' THEN jea.credit_in_account_currency ELSE 0 END) as revenue,
			SUM(CASE WHEN je.user_remark LIKE '%%Faculty Expenses%%' THEN jea.debit_in_account_currency ELSE 0 END) as expenses
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND je.posting_date >= %s
			AND (je.user_remark LIKE '%%Tuition Revenue%%' OR je.user_remark LIKE '%%Faculty Expenses%%')
		GROUP BY faculty, period
		HAVING faculty != 'Other'
		ORDER BY period, faculty
	""", params + [start], as_dict=True)

	# Compute KPIs
	total_revenue = sum(flt(r.revenue) for r in faculty_data)
	total_expenses = sum(flt(r.expenses) for r in faculty_data)
	for row in faculty_data:
		row["surplus"] = flt(row.revenue) - flt(row.expenses)
		row["margin_pct"] = round(row["surplus"] / flt(row.revenue) * 100, 1) if flt(row.revenue) else 0

	return {
		"faculty_data": faculty_data,
		"monthly_trend": monthly,
		"totals": {
			"revenue": total_revenue,
			"expenses": total_expenses,
			"surplus": total_revenue - total_expenses,
			"margin_pct": round((total_revenue - total_expenses) / total_revenue * 100, 1) if total_revenue else 0,
		},
	}


# ═══════════════════════════════════════════════════════════════════════
# 2. Cost Allocation & Academic Transparency
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_cost_allocation_data(company=None):
	"""Cost breakdown: admin vs academic, cost-center allocation."""
	frappe.only_for(["Administrator", "AMO Admin", "AMO University Admin", "AMO Finance Manager"])

	cond, params = _uni_conditions(company)
	start, _ = _date_range(12)

	# Admin vs academic expenses
	cost_split = frappe.db.sql(f"""
		SELECT
			CASE
				WHEN jea.account LIKE '%%Administrative%%' THEN 'Administrative'
				ELSE 'Academic'
			END as category,
			SUM(jea.debit_in_account_currency) as amount
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND je.posting_date >= %s
			AND jea.debit_in_account_currency > 0
			AND jea.account LIKE '%%Expenses%%'
		GROUP BY category
	""", params + [start], as_dict=True)

	# Per-faculty admin ratio
	faculty_cost = frappe.db.sql(f"""
		SELECT
			CASE
				WHEN je.user_remark LIKE '%%Faculty of Arts%%' THEN 'Arts & Sciences'
				WHEN je.user_remark LIKE '%%Faculty of Business%%' THEN 'Business'
				WHEN je.user_remark LIKE '%%Faculty of Engineering%%' THEN 'Engineering'
				WHEN je.user_remark LIKE '%%Faculty of Music%%' THEN 'Music'
				WHEN je.user_remark LIKE '%%Faculty of Public Health%%' THEN 'Public Health'
				ELSE 'General'
			END as faculty,
			SUM(jea.debit_in_account_currency) as total_cost
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND je.posting_date >= %s
			AND je.user_remark LIKE '%%Faculty Expenses%%'
		GROUP BY faculty
		ORDER BY total_cost DESC
	""", params + [start], as_dict=True)

	# Cost center breakdown (from cost center tree)
	cc_data = frappe.db.sql(f"""
		SELECT
			jea.cost_center,
			SUM(jea.debit_in_account_currency) as amount
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND je.posting_date >= %s
			AND jea.debit_in_account_currency > 0
			AND jea.cost_center IS NOT NULL AND jea.cost_center != ''
		GROUP BY jea.cost_center
		ORDER BY amount DESC
		LIMIT 15
	""", params + [start], as_dict=True)

	total = sum(flt(r.amount) for r in cost_split)
	admin_total = sum(flt(r.amount) for r in cost_split if r.category == "Administrative")

	return {
		"cost_split": cost_split,
		"faculty_cost": faculty_cost,
		"cost_center_breakdown": cc_data,
		"kpis": {
			"total_expenses": total,
			"admin_ratio_pct": round(admin_total / total * 100, 1) if total else 0,
			"academic_ratio_pct": round((total - admin_total) / total * 100, 1) if total else 0,
		},
	}


# ═══════════════════════════════════════════════════════════════════════
# 3. Tuition & Scholarship Governance
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_tuition_scholarship_data(company=None):
	"""Tuition collection, scholarship burden, receivables aging."""
	frappe.only_for(["Administrator", "AMO Admin", "AMO University Admin", "AMO Finance Manager"])

	cond, params = _uni_conditions(company)
	today = getdate()
	year_start = getdate(f"{today.year}-01-01")

	# Tuition by month and campus
	tuition = frappe.db.sql(f"""
		SELECT
			je.company as campus,
			DATE_FORMAT(je.posting_date, '%%Y-%%m') as period,
			SUM(jea.credit_in_account_currency) as revenue
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond} AND je.posting_date >= %s AND je.user_remark LIKE '%%Tuition%%'
		GROUP BY je.company, period
		ORDER BY period
	""", params + [year_start], as_dict=True)

	# Scholarship by month and campus
	scholarships = frappe.db.sql(f"""
		SELECT
			je.company as campus,
			DATE_FORMAT(je.posting_date, '%%Y-%%m') as period,
			SUM(jea.debit_in_account_currency) as disbursed
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond} AND je.posting_date >= %s AND je.user_remark LIKE '%%Scholarship%%'
		GROUP BY je.company, period
		ORDER BY period
	""", params + [year_start], as_dict=True)

	# Per-faculty tuition
	faculty_tuition = frappe.db.sql(f"""
		SELECT
			CASE
				WHEN je.user_remark LIKE '%%Faculty of Arts%%' THEN 'Arts & Sciences'
				WHEN je.user_remark LIKE '%%Faculty of Business%%' THEN 'Business'
				WHEN je.user_remark LIKE '%%Faculty of Engineering%%' THEN 'Engineering'
				WHEN je.user_remark LIKE '%%Faculty of Music%%' THEN 'Music'
				WHEN je.user_remark LIKE '%%Faculty of Public Health%%' THEN 'Public Health'
				ELSE 'Other'
			END as faculty,
			SUM(jea.credit_in_account_currency) as revenue
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond} AND je.posting_date >= %s AND je.user_remark LIKE '%%Tuition%%'
		GROUP BY faculty
		HAVING faculty != 'Other'
		ORDER BY revenue DESC
	""", params + [year_start], as_dict=True)

	# Receivables (accounts receivable entries)
	receivables = frappe.db.sql(f"""
		SELECT
			je.company as campus,
			DATEDIFF(CURDATE(), je.posting_date) as age_days,
			SUM(jea.debit_in_account_currency) as amount
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
			AND jea.account LIKE '%%Receivable%%'
			AND jea.debit_in_account_currency > 0
		GROUP BY je.company, CASE
			WHEN DATEDIFF(CURDATE(), je.posting_date) <= 30 THEN '0-30'
			WHEN DATEDIFF(CURDATE(), je.posting_date) <= 60 THEN '31-60'
			WHEN DATEDIFF(CURDATE(), je.posting_date) <= 90 THEN '61-90'
			ELSE '90+'
		END
	""", params, as_dict=True)

	# Compute KPIs
	total_tuition = sum(flt(r.revenue) for r in tuition)
	total_scholarship = sum(flt(r.disbursed) for r in scholarships)

	return {
		"tuition_by_month": tuition,
		"scholarships_by_month": scholarships,
		"faculty_tuition": faculty_tuition,
		"receivables": receivables,
		"kpis": {
			"total_tuition": total_tuition,
			"total_scholarship": total_scholarship,
			"scholarship_burden_pct": round(total_scholarship / total_tuition * 100, 1) if total_tuition else 0,
			"collection_rate_pct": round((total_tuition - sum(flt(r.amount) for r in receivables)) / total_tuition * 100, 1) if total_tuition else 100,
		},
	}


# ═══════════════════════════════════════════════════════════════════════
# 4. Grant & Research Project Control
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_grant_research_data(company=None):
	"""Project budgets, grant utilization, completion tracking."""
	frappe.only_for(["Administrator", "AMO Admin", "AMO University Admin", "AMO Finance Manager"])

	cond_company = ""
	params = []
	if company:
		cond_company = "AND p.company = %s"
		params = [company]

	# Project status + budget
	projects = frappe.db.sql(f"""
		SELECT
			p.name, p.project_name, p.company, p.status,
			p.expected_start_date, p.expected_end_date,
			p.estimated_costing as budget,
			p.total_costing_amount as actual_cost,
			p.percent_complete
		FROM `tabProject` p
		WHERE (p.company LIKE '%%Antonine University%%' OR p.company LIKE '%%AMO%%')
			{cond_company}
		ORDER BY p.status, p.expected_end_date
	""", params, as_dict=True)

	# Grant entries from JE
	grants = frappe.db.sql("""
		SELECT
			je.company,
			SUM(jea.credit_in_account_currency) as total_grants
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE je.user_remark LIKE '%%Grant%%' OR je.user_remark LIKE '%%Research%%'
		GROUP BY je.company
	""", as_dict=True)

	# Budget utilization from Budget doctype
	budgets = frappe.db.sql("""
		SELECT
			b.company,
			b.name as budget_name,
			b.budget_amount,
			b.from_fiscal_year,
			b.cost_center
		FROM `tabBudget` b
		WHERE b.company LIKE '%%Antonine University%%' OR b.company LIKE '%%AMO%%'
		ORDER BY b.company
	""", as_dict=True)

	# KPIs
	total_budget = sum(flt(p.budget) for p in projects)
	total_actual = sum(flt(p.actual_cost) for p in projects)
	completed = [p for p in projects if p.status == "Completed"]
	on_budget = [p for p in completed if flt(p.actual_cost) <= flt(p.budget)] if completed else []

	return {
		"projects": projects,
		"grants": grants,
		"budgets": budgets,
		"kpis": {
			"total_projects": len(projects),
			"open_projects": len([p for p in projects if p.status == "Open"]),
			"completed_projects": len(completed),
			"budget_vs_actual_pct": round(total_actual / total_budget * 100, 1) if total_budget else 0,
			"on_budget_pct": round(len(on_budget) / len(completed) * 100, 1) if completed else 100,
			"total_grant_amount": sum(flt(g.total_grants) for g in grants),
		},
	}


# ═══════════════════════════════════════════════════════════════════════
# 5. Multi-Year Academic Financial Planning
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_multiyear_planning_data(company=None):
	"""Historical trends and projection data for multi-year planning."""
	frappe.only_for(["Administrator", "AMO Admin", "AMO Finance Manager"])

	cond, params = _uni_conditions(company)

	# Yearly revenue & expenses (all available years)
	yearly = frappe.db.sql(f"""
		SELECT
			YEAR(je.posting_date) as year,
			SUM(CASE WHEN je.user_remark LIKE '%%Tuition Revenue%%' THEN jea.credit_in_account_currency ELSE 0 END) as tuition_revenue,
			SUM(CASE WHEN je.user_remark LIKE '%%Faculty Expenses%%' THEN jea.debit_in_account_currency ELSE 0 END) as faculty_expenses,
			SUM(CASE WHEN je.user_remark LIKE '%%Scholarship%%' THEN jea.debit_in_account_currency ELSE 0 END) as scholarship_cost,
			SUM(CASE WHEN jea.debit_in_account_currency > 0 AND jea.account LIKE '%%Expenses%%'
				THEN jea.debit_in_account_currency ELSE 0 END) as total_expenses,
			SUM(CASE WHEN jea.credit_in_account_currency > 0 THEN jea.credit_in_account_currency ELSE 0 END) as total_revenue
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE {cond}
		GROUP BY YEAR(je.posting_date)
		ORDER BY year
	""", params, as_dict=True)

	# Budget amounts by year
	budget_by_year = frappe.db.sql("""
		SELECT
			b.from_fiscal_year as year,
			SUM(b.budget_amount) as budget
		FROM `tabBudget` b
		WHERE b.company LIKE '%%Antonine University%%' OR b.company LIKE '%%AMO%%'
		GROUP BY b.from_fiscal_year
		ORDER BY year
	""", as_dict=True)

	# Asset base
	assets = frappe.db.sql("""
		SELECT
			YEAR(a.purchase_date) as year,
			SUM(a.net_purchase_amount) as value,
			COUNT(*) as count
		FROM `tabAsset` a
		WHERE a.company LIKE '%%AMO%%' OR a.company LIKE '%%Antonine%%'
		GROUP BY YEAR(a.purchase_date)
		ORDER BY year
	""", as_dict=True)

	# Simple 3-year projection based on average growth
	projection = []
	if yearly:
		last = yearly[-1]
		rev_growth = 0.05  # Default 5%
		exp_growth = 0.03  # Default 3%
		if len(yearly) >= 2:
			prev = yearly[-2]
			if flt(prev.total_revenue):
				rev_growth = (flt(last.total_revenue) - flt(prev.total_revenue)) / flt(prev.total_revenue)
			if flt(prev.total_expenses):
				exp_growth = (flt(last.total_expenses) - flt(prev.total_expenses)) / flt(prev.total_expenses)
		for i in range(1, 4):
			projection.append({
				"year": int(last.year) + i,
				"projected_revenue": round(flt(last.total_revenue) * (1 + rev_growth) ** i),
				"projected_expenses": round(flt(last.total_expenses) * (1 + exp_growth) ** i),
			})
			projection[-1]["projected_surplus"] = projection[-1]["projected_revenue"] - projection[-1]["projected_expenses"]

	return {
		"yearly_financials": yearly,
		"budget_by_year": budget_by_year,
		"assets_by_year": assets,
		"projection": projection,
	}


# ═══════════════════════════════════════════════════════════════════════
# 6. Rector Executive Dashboard
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_rector_dashboard_data():
	"""Top-level executive summary for the Rector."""
	frappe.only_for(["Administrator", "AMO Admin"])

	today = getdate()
	year_start = getdate(f"{today.year}-01-01")
	prev_year_start = getdate(f"{today.year - 1}-01-01")
	prev_year_end = getdate(f"{today.year - 1}-12-31")

	# Current year totals
	current = frappe.db.sql("""
		SELECT
			SUM(CASE WHEN jea.credit_in_account_currency > 0 THEN jea.credit_in_account_currency ELSE 0 END) as revenue,
			SUM(CASE WHEN jea.debit_in_account_currency > 0 AND jea.account LIKE '%%Expenses%%'
				THEN jea.debit_in_account_currency ELSE 0 END) as expenses
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE je.posting_date >= %s AND je.company LIKE '%%Antonine University%%'
	""", [year_start], as_dict=True)

	# Previous year totals
	previous = frappe.db.sql("""
		SELECT
			SUM(CASE WHEN jea.credit_in_account_currency > 0 THEN jea.credit_in_account_currency ELSE 0 END) as revenue,
			SUM(CASE WHEN jea.debit_in_account_currency > 0 AND jea.account LIKE '%%Expenses%%'
				THEN jea.debit_in_account_currency ELSE 0 END) as expenses
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE je.posting_date >= %s AND je.posting_date <= %s AND je.company LIKE '%%Antonine University%%'
	""", [prev_year_start, prev_year_end], as_dict=True)

	# Per-faculty operating margin
	faculty_margins = frappe.db.sql("""
		SELECT
			CASE
				WHEN je.user_remark LIKE '%%Faculty of Arts%%' THEN 'Arts & Sciences'
				WHEN je.user_remark LIKE '%%Faculty of Business%%' THEN 'Business'
				WHEN je.user_remark LIKE '%%Faculty of Engineering%%' THEN 'Engineering'
				WHEN je.user_remark LIKE '%%Faculty of Music%%' THEN 'Music'
				WHEN je.user_remark LIKE '%%Faculty of Public Health%%' THEN 'Public Health'
				ELSE 'Other'
			END as faculty,
			SUM(CASE WHEN je.user_remark LIKE '%%Tuition Revenue%%' THEN jea.credit_in_account_currency ELSE 0 END) as revenue,
			SUM(CASE WHEN je.user_remark LIKE '%%Faculty Expenses%%' THEN jea.debit_in_account_currency ELSE 0 END) as expenses
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE je.posting_date >= %s AND je.company LIKE '%%Antonine University%%'
			AND (je.user_remark LIKE '%%Tuition Revenue%%' OR je.user_remark LIKE '%%Faculty Expenses%%')
		GROUP BY faculty
		HAVING faculty != 'Other'
		ORDER BY revenue DESC
	""", [year_start], as_dict=True)

	for row in faculty_margins:
		row["margin"] = flt(row.revenue) - flt(row.expenses)
		row["margin_pct"] = round(row["margin"] / flt(row.revenue) * 100, 1) if flt(row.revenue) else 0

	# Organization-wide summary
	org_summary = {
		"total_companies": frappe.db.count("Company", {"parent_company": ["like", "AMO%"]}),
		"total_assets": _get_total_asset_value(),
		"total_projects": frappe.db.count("Project", {
			"company": ["like", "%AMO%"],
		}) + frappe.db.count("Project", {
			"company": ["like", "%Antonine%"],
		}),
		"open_projects": frappe.db.count("Project", {
			"company": ["like", "%Antonine%"],
			"status": "Open",
		}),
	}

	# Group breakdown
	groups = frappe.db.sql("""
		SELECT parent_company as grp, COUNT(*) as count
		FROM `tabCompany`
		WHERE parent_company LIKE 'AMO%%'
		GROUP BY parent_company
	""", as_dict=True)

	cur = current[0] if current else {"revenue": 0, "expenses": 0}
	prev = previous[0] if previous else {"revenue": 0, "expenses": 0}
	cur_rev = flt(cur.revenue)
	cur_exp = flt(cur.expenses)
	prev_rev = flt(prev.revenue)
	prev_exp = flt(prev.expenses)

	return {
		"current_year": {"revenue": cur_rev, "expenses": cur_exp, "surplus": cur_rev - cur_exp},
		"previous_year": {"revenue": prev_rev, "expenses": prev_exp, "surplus": prev_rev - prev_exp},
		"growth": {
			"revenue_pct": round((cur_rev - prev_rev) / prev_rev * 100, 1) if prev_rev else 0,
			"expense_pct": round((cur_exp - prev_exp) / prev_exp * 100, 1) if prev_exp else 0,
		},
		"operating_margin_pct": round((cur_rev - cur_exp) / cur_rev * 100, 1) if cur_rev else 0,
		"faculty_margins": faculty_margins,
		"org_summary": org_summary,
		"groups": groups,
	}


# ── Shared utility ─────────────────────────────────────────────────────

def _get_total_asset_value():
	result = frappe.db.sql("""
		SELECT COALESCE(SUM(net_purchase_amount), 0) as total
		FROM `tabAsset`
		WHERE company LIKE '%%AMO%%' OR company LIKE '%%Monastery%%'
		OR company LIKE '%%Antonine%%'
	""", as_dict=True)
	return flt(result[0].total) if result else 0
