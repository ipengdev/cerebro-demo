import frappe
from frappe.model.document import Document

class QMSLocation(Document):
	def validate(self):
		if self.parent_location and self.parent_location == self.name:
			frappe.throw("A location cannot be its own parent.")
