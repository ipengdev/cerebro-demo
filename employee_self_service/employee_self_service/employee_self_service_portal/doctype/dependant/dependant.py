import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Dependant(Document):
	def validate(self):
		self.set_full_name()
		self.validate_dates()
		self.validate_primary()
		self.validate_insurance_dates()

	def set_full_name(self):
		parts = [self.first_name, self.middle_name, self.last_name]
		self.full_name = " ".join(p for p in parts if p)

	def validate_dates(self):
		if self.date_of_birth and getdate(self.date_of_birth) > getdate(nowdate()):
			frappe.throw(_("Date of Birth cannot be in the future."))

	def validate_insurance_dates(self):
		for row in self.get("medical_insurance_detail", []):
			if row.start_date and row.end_date:
				if getdate(row.end_date) < getdate(row.start_date):
					frappe.throw(
						_("Row {0}: Insurance End Date cannot be before Start Date.").format(row.idx)
					)

	def validate_primary(self):
		"""Ensure only one primary dependant per relationship type per employee."""
		if self.is_primary:
			existing = frappe.db.exists(
				"Dependant",
				{
					"employee": self.employee,
					"relationship_type": self.relationship_type,
					"is_primary": 1,
					"name": ("!=", self.name),
				},
			)
			if existing:
				frappe.throw(
					_("Employee {0} already has a primary {1}: {2}").format(
						self.employee, self.relationship_type, existing
					)
				)
