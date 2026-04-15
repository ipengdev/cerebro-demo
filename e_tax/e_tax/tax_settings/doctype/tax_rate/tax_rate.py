# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TaxRate(Document):
	def validate(self):
		if self.effective_to and self.effective_from and self.effective_from > self.effective_to:
			frappe.throw("Effective To must be after Effective From")
