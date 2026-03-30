import frappe
from frappe.model.document import Document

class QMSPatientFormTemplate(Document):
	def validate(self):
		for field in self.form_fields:
			if not field.field_name:
				field.field_name = frappe.scrub(field.field_label)
