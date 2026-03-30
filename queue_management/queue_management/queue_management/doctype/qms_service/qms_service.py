import frappe
from frappe.model.document import Document

class QMSService(Document):
	def validate(self):
		if self.parent_service and self.parent_service == self.name:
			frappe.throw("A service cannot be its own parent.")
