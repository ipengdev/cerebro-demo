import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


class SoftwareLicense(Document):
    def validate(self):
        self.available_licenses = (self.total_licenses or 0) - (self.used_licenses or 0)
        if self.expiry_date and getdate(self.expiry_date) < getdate(nowdate()):
            self.status = "Expired"
