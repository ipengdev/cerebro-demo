import frappe
from frappe.model.document import Document

class QMSStaffAssignment(Document):
	def validate(self):
		if not self.is_active:
			return
		existing = frappe.db.get_value(
			"QMS Staff Assignment",
			{"employee": self.employee, "is_active": 1, "name": ("!=", self.name)},
			"name"
		)
		if existing:
			frappe.throw(
				f"Employee {self.employee_name} is already assigned to another counter "
				f"(Assignment: {existing}). Deactivate the existing assignment first."
			)
