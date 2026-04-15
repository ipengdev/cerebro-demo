# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TaxFiscalYear(Document):
	def validate(self):
		if self.start_date and self.end_date and self.start_date >= self.end_date:
			frappe.throw("End Date must be after Start Date")
