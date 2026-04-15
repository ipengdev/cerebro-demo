app_name = "itsm"
app_title = "ITSM"
app_publisher = "iPeng Holdings"
app_description = "IT Assets and Services Management"
app_email = "admin@ipengholding.com"
app_license = "mit"

required_apps = ["frappe"]

app_include_css = "/assets/itsm/css/itsm.css"

add_to_apps_screen = [
	{
		"name": "itsm",
		"logo": "/assets/itsm/images/itsm-logo.svg",
		"title": "ITSM",
		"route": "/app/itsm-dashboard",
	}
]

# Roles
# -----
# Custom roles for the ITSM app

after_install = "itsm.setup.after_install"

# Scheduled Tasks
# ---------------
scheduler_events = {
	"cron": {
		"*/5 * * * *": [
			"itsm.asset_discovery.discovery_engine.check_stale_assets",
		],
		"0 * * * *": [
			"itsm.asset_discovery.discovery_engine.run_scheduled_probes",
		],
	},
}

# Notification config
notification_config = "itsm.notifications.get_notification_config"

# Default log clearing
default_log_clearing_doctypes = {
	"IT Asset Log": 90,
	"Discovery Result": 60,
}
# ignore_translatable_strings_from = []

