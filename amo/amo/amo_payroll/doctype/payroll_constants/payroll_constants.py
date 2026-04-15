import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PayrollConstants(Document):
	def before_save(self):
		if self.from_date:
			self.effective_from = self.from_date
		# Compute totals from sickness + maternity
		self.employer_nssf_medical_percentage = (
			flt(self.employer_nssf_sickness_percentage)
			+ flt(self.employer_nssf_maternity_percentage)
		)
		self.employee_nssf_medical_percentage = (
			flt(self.employee_nssf_sickness_percentage)
			+ flt(self.employee_nssf_maternity_percentage)
		)

	def validate(self):
		if self.effective_to and self.effective_from > self.effective_to:
			frappe.throw("Effective To date must be after Effective From date")

	@staticmethod
	def get_active_constants(company, date=None):
		"""Get the active payroll constants for a company on a given date."""
		if not date:
			date = frappe.utils.today()

		filters = {
			"company": company,
			"is_active": 1,
			"effective_from": ("<=", date),
		}

		constants = frappe.get_all(
			"Payroll Constants",
			filters=filters,
			or_filters=[
				["effective_to", "is", "not set"],
				["effective_to", ">=", date],
			],
			order_by="effective_from desc",
			limit=1,
		)

		if constants:
			return frappe.get_doc("Payroll Constants", constants[0].name)
		return None
