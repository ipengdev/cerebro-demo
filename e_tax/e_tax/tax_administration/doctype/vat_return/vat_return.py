# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class VATReturn(Document):
	def validate(self):
		self.calculate_vat()

	def calculate_vat(self):
		self.taxable_sales = flt(self.total_sales) - flt(self.exempt_sales) - flt(self.zero_rated_sales)
		self.output_vat = flt(self.taxable_sales) * flt(self.output_vat_rate) / 100

		self.taxable_purchases = flt(self.total_purchases) - flt(self.exempt_purchases)
		self.input_vat = flt(self.taxable_purchases) * flt(self.input_vat_rate) / 100

		self.net_vat = flt(self.output_vat) - flt(self.input_vat)

		net_after_credit = flt(self.net_vat) - flt(self.vat_credit_brought_forward)
		if net_after_credit > 0:
			self.vat_payable = net_after_credit
			self.vat_refund_due = 0
		else:
			self.vat_payable = 0
			self.vat_refund_due = abs(net_after_credit)

	def on_submit(self):
		self.db_set("status", "Submitted")
		self.db_set("submitted_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
