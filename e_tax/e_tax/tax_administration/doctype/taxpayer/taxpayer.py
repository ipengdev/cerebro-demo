# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Taxpayer(Document):
	def validate(self):
		if self.taxpayer_type == "Enterprise" and not self.enterprise_name:
			frappe.throw("Enterprise Name is required for Enterprise taxpayer type")
