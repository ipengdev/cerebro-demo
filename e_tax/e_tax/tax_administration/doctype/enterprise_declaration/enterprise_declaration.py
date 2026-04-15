# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class EnterpriseDeclaration(Document):
	def validate(self):
		self.calculate_taxes()

	def calculate_taxes(self):
		self.taxable_income = flt(self.gross_revenue) - flt(self.allowable_deductions)
		self.income_tax_amount = flt(self.taxable_income) * flt(self.income_tax_rate) / 100

		self.social_tax_amount = flt(self.total_payroll) * flt(self.social_tax_rate) / 100
		self.unemployment_insurance_amount = flt(self.total_payroll) * flt(self.unemployment_insurance_rate) / 100
		self.pension_fund_amount = flt(self.total_payroll) * flt(self.pension_fund_rate) / 100

		self.total_tax_liability = (
			flt(self.income_tax_amount)
			+ flt(self.social_tax_amount)
			+ flt(self.unemployment_insurance_amount)
			+ flt(self.pension_fund_amount)
		)
		self.balance_due = flt(self.total_tax_liability) - flt(self.total_paid)

	def on_submit(self):
		self.db_set("status", "Submitted")
		self.db_set("submitted_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
