import frappe
from queue_management.install import create_qms_custom_fields


def after_install():
	create_qms_custom_fields()
	_create_roles()
	_sync_workspace_sidebar()


def after_migrate():
	create_qms_custom_fields()
	_create_roles()
	_sync_workspace_sidebar()


def _create_roles():
	"""Ensure QMS roles exist."""
	for role_name in ("QMS Operator", "Healthcare Administrator"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _sync_workspace_sidebar():
	"""Ensure QMS workspace sidebar is synced from JSON fixture."""
	import json, os

	json_path = os.path.join(
		os.path.dirname(__file__),
		"workspace_sidebar",
		"queue_management.json",
	)
	if not os.path.exists(json_path):
		return

	with open(json_path) as f:
		data = json.load(f)

	name = data["name"]

	# Delete existing and recreate
	frappe.db.sql("DELETE FROM `tabWorkspace Sidebar Item` WHERE parent=%s", name)
	frappe.db.sql("DELETE FROM `tabWorkspace Sidebar` WHERE name=%s", name)

	sidebar = frappe.new_doc("Workspace Sidebar")
	sidebar.name = name
	sidebar.title = data["title"]
	sidebar.module = data["module"]
	sidebar.app = data["app"]
	sidebar.standard = data["standard"]
	sidebar.header_icon = data.get("header_icon", "")

	for item in data.get("items", []):
		item_type = item.get("type", "Link")
		if item_type == "Card Break":
			item_type = "Section Break"

		sidebar.append("items", {
			"label": item["label"],
			"link_type": item.get("link_type", "DocType"),
			"link_to": item.get("link_to", ""),
			"type": item_type,
			"icon": item.get("icon", ""),
			"child": item.get("child", 0),
			"indent": item.get("indent", 0),
			"collapsible": item.get("collapsible", 1),
			"keep_closed": item.get("keep_closed", 0),
			"show_arrow": item.get("show_arrow", 0),
		})

	sidebar.db_insert()
	for i, row in enumerate(sidebar.items):
		row.parent = sidebar.name
		row.parenttype = "Workspace Sidebar"
		row.parentfield = "items"
		row.idx = i + 1
		row.db_insert()

	frappe.db.commit()
