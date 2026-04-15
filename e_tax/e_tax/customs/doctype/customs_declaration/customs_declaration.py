# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class CustomsDeclaration(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		self.total_cif_value = 0
		self.total_customs_duty = 0
		self.total_vat_on_imports = 0

		for item in self.items:
			item.cif_value = flt(item.fob_value) + flt(item.freight) + flt(item.insurance)
			item.customs_duty = flt(item.cif_value) * flt(item.duty_rate) / 100
			item.vat_amount = (flt(item.cif_value) + flt(item.customs_duty)) * flt(item.vat_rate) / 100
			item.total_taxes = flt(item.customs_duty) + flt(item.vat_amount)

			self.total_cif_value += flt(item.cif_value)
			self.total_customs_duty += flt(item.customs_duty)
			self.total_vat_on_imports += flt(item.vat_amount)

		self.total_duties_and_taxes = (
			flt(self.total_customs_duty)
			+ flt(self.total_vat_on_imports)
			+ flt(self.total_other_charges)
		)
		self.balance_due = flt(self.total_duties_and_taxes) - flt(self.amount_paid)

	def on_submit(self):
		self.db_set("status", "Submitted")
		self.db_set("submitted_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
