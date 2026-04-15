# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ExciseDutyReturn(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		self.total_quantity = 0
		self.total_excise_duty = 0

		for item in self.items:
			item.excise_duty = flt(item.quantity) * flt(item.duty_rate_per_unit)
			self.total_quantity += flt(item.quantity)
			self.total_excise_duty += flt(item.excise_duty)

		self.balance_due = flt(self.total_excise_duty) - flt(self.amount_paid)

	def on_submit(self):
		self.db_set("status", "Submitted")
		self.db_set("submitted_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
