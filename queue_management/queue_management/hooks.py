app_name = "queue_management"
app_title = "Queue Management"
app_publisher = "Queue Management"
app_description = "Queue Management System"
app_email = "admin@example.com"
app_license = "mit"
required_apps = ["frappe"]

add_to_apps_screen = [
{
"name": "queue_management",
"logo": "/assets/queue_management/images/qms-icon.svg",
"title": "Queue Management",
"route": "/app/qms-dashboard",
"has_permission": "queue_management.qms_api.has_qms_permission",
}
]

after_install = "queue_management.setup.after_install"
after_migrate = "queue_management.setup.after_migrate"

# Protect QMS staff session tokens from being wiped by frappe.clear_cache()
persistent_cache_keys = [
	"qms_staff_session*",
	"qms_display_portal_session*",
]

fixtures = [
{"dt": "Role", "filters": [["name", "in", ["QMS Operator", "Healthcare Administrator"]]]},
]

# Document Events
doc_events = {
"QMS Queue Ticket": {
"after_insert": "queue_management.qms_api.on_ticket_created",
"on_update": "queue_management.qms_api.on_ticket_updated",
},
"QMS Feedback Response": {
"after_insert": "queue_management.qms_api.on_feedback_submitted",
},
"QMS Staff Assignment": {
"on_update": "queue_management.qms_api.on_staff_assignment_updated",
"after_insert": "queue_management.qms_api.on_staff_assignment_updated",
},
}

# Scheduled Tasks
scheduler_events = {
"cron": {
"0 0 * * *": [
"queue_management.qms_api.cleanup_stale_tickets",
"queue_management.qms_api.purge_old_records",
"queue_management.qms_session_store.cleanup_old_sessions",
],
"0 7 * * *": [
"queue_management.qms_api.send_appointment_reminders",
],
}
}

# Website Route Rules
website_route_rules = [
{"from_route": "/queue", "to_route": "queue"},
{"from_route": "/queue/patient", "to_route": "qms_kiosk"},
{"from_route": "/queue/ticket", "to_route": "qms_kiosk"},
{"from_route": "/queue/staff", "to_route": "qms_call_screen"},
{"from_route": "/queue/login", "to_route": "qms_call_screen"},
{"from_route": "/queue/<path:app_path>", "to_route": "queue"},
{"from_route": "/qms-display", "to_route": "qms_display"},
]
