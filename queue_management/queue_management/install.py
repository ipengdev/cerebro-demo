import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_qms_custom_fields():
	# Only create Employee custom fields if Employee doctype exists (requires ERPNext/HRMS)
	if not frappe.db.exists("DocType", "Employee"):
		frappe.logger().info("QMS: Employee doctype not found — skipping custom field creation. Install ERPNext/HRMS for Employee integration.")
		return

	custom_fields = {
		"Employee": [
			{
				"fieldname": "qms_section",
				"fieldtype": "Section Break",
				"label": "Queue Management",
				"insert_after": "attendance_device_id",
				"collapsible": 1,
			},
			{
				"fieldname": "qms_counter",
				"fieldtype": "Link",
				"label": "Assigned Counter",
				"options": "QMS Counter",
				"insert_after": "qms_section",
				"read_only": 1,
			},
			{
				"fieldname": "qms_column_break",
				"fieldtype": "Column Break",
				"insert_after": "qms_counter",
			},
			{
				"fieldname": "qms_role",
				"fieldtype": "Data",
				"label": "QMS Role",
				"insert_after": "qms_column_break",
				"read_only": 1,
			},
		]
	}
	create_custom_fields(custom_fields)
