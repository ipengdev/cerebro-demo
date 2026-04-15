app_name = "amo"
app_title = "AMO"
app_publisher = "iPeng Holding"
app_description = "Antonine Maronite Order - ERP Management"
app_email = "admin@ipengholding.com"
app_license = "mit"
required_apps = ["frappe", "erpnext", "hrms"]

add_to_apps_screen = [
	{
		"name": "amo",
		"logo": "/assets/amo/images/amo-icon.png",
		"title": "AMO",
		"route": "/app/amo-dashboard",
	}
]

after_install = "amo.amo_setup.setup.after_install"
after_migrate = "amo.amo_setup.setup.after_migrate"

# Website pages
website_route_rules = [
	{"from_route": "/amo-dashboard", "to_route": "amo-dashboard"},
]

# Workspace sidebar
# Fixtures
fixtures = [
	{"dt": "Role", "filters": [["name", "in", [
		"AMO Admin",
		"AMO Finance Manager",
		"AMO HR Manager",
		"AMO Project Manager",
		"AMO University Admin",
		"AMO School Admin",
		"AMO Monastery Admin",
	]]]},
	{"dt": "Print Format", "filters": [["name", "in", [
		"Lebanese Payslip",
	]]]},
	{"dt": "Report", "filters": [["name", "in", [
		"CNSS Monthly Declaration",
		"CNSS Yearly Declaration",
		"Employee Joining Report",
		"Employee Leaving Report",
	]]]},
	{"dt": "Page", "filters": [["name", "in", [
		"mof-forms",
		"cnss-reports",
	]]]},
]

# DocType JS overrides
doctype_js = {}

# Jinja template extensions
jinja = {}

# Document Events - AMO specific
doc_events = {}

# Scheduled Tasks
scheduler_events = {
	"cron": {
		"0 1 * * *": [
			"amo.amo_setup.depreciation.process_daily_depreciation",
		],
		"0 0 1 * *": [
			"amo.amo_setup.budget.check_monthly_budget_alerts",
		],
	}
}

# Override whitelisted methods
override_whitelisted_methods = {}

# Page definitions for dashboards
page_js = {}
