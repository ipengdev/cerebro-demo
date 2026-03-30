import frappe
from frappe.model.document import Document


class QMSStaffLogin(Document):
    def before_save(self):
        if self.username:
            self.username = self.username.strip().lower()
