# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class PersonalIncomeTax(Document):
	def validate(self):
		self.calculate_tax()

	def calculate_tax(self):
		self.total_income = (
			flt(self.employment_income)
			+ flt(self.other_employment_benefits)
			+ flt(self.business_income)
			+ flt(self.rental_income)
			+ flt(self.investment_income)
			+ flt(self.other_income)
		)

		self.total_deductions = (
			flt(self.social_security_contributions)
			+ flt(self.pension_contributions)
			+ flt(self.insurance_premiums)
			+ flt(self.charitable_donations)
			+ flt(self.other_deductions)
		)

		self.taxable_income = max(0, flt(self.total_income) - flt(self.total_deductions))
		self.tax_computed = flt(self.taxable_income) * flt(self.tax_rate) / 100

		net_tax = flt(self.tax_computed) - flt(self.tax_withheld)
		if net_tax > 0:
			self.tax_payable = net_tax
			self.tax_refund = 0
		else:
			self.tax_payable = 0
			self.tax_refund = abs(net_tax)

	def on_submit(self):
		self.db_set("status", "Submitted")
		self.db_set("submitted_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
