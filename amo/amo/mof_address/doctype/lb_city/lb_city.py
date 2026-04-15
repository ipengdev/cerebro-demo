import frappe
from frappe.model.document import Document


class LBCity(Document):
	def before_save(self):
		if self.caza and not self.mohafaza:
			self.mohafaza = frappe.db.get_value("LB Caza", self.caza, "mohafaza")
