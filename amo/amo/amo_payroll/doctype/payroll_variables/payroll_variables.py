import frappe
from frappe.model.document import Document


class PayrollVariables(Document):
	def validate(self):
		if self.effective_to and self.effective_from > self.effective_to:
			frappe.throw("Effective To date must be after Effective From date")

		self.validate_unique_variable_names()

	def validate_unique_variable_names(self):
		"""Ensure no duplicate variable names in the table."""
		seen = set()
		for row in self.variables:
			if row.variable_name in seen:
				frappe.throw(f"Duplicate variable name: {row.variable_name}")
			seen.add(row.variable_name)

	@staticmethod
	def get_active_variables(company, date=None):
		"""Get the active payroll variables for a company on a given date."""
		if not date:
			date = frappe.utils.today()

		filters = {
			"company": company,
			"is_active": 1,
			"effective_from": ("<=", date),
		}

		variables = frappe.get_all(
			"Payroll Variables",
			filters=filters,
			or_filters=[
				["effective_to", "is", "not set"],
				["effective_to", ">=", date],
			],
			order_by="effective_from desc",
			limit=1,
		)

		if variables:
			return frappe.get_doc("Payroll Variables", variables[0].name)
		return None
