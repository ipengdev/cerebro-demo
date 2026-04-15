app_name = "e_tax"
app_title = "e-Tax"
app_publisher = "iPeng Holding"
app_description = "Electronic Tax Filing System for Tax and Customs Board"
app_email = "admin@ipengholding.com"
app_license = "mit"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "e_tax",
		"logo": "/assets/e_tax/images/e-tax-logo.svg",
		"title": "e-Tax",
		"route": "/e-tax",
	}
]

after_install = "e_tax.setup.after_install"
after_migrate = "e_tax.setup.after_migrate"

website_route_rules = [
	{"from_route": "/e-tax/<path:app_path>", "to_route": "e-tax"},
]

fixtures = [
	{
		"dt": "Role",
		"filters": [["name", "in", [
			"Tax Officer",
			"Tax Filer",
			"Customs Officer",
			"Tax Auditor",
		]]],
	},
]

# Request Events
# ----------------
# before_request = ["e_tax.utils.before_request"]
# after_request = ["e_tax.utils.after_request"]

# Job Events
# ----------
# before_job = ["e_tax.utils.before_job"]
# after_job = ["e_tax.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"e_tax.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

