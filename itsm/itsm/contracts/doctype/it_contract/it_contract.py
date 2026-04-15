import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, add_days, date_diff


class ITContract(Document):
    def validate(self):
        self.check_expiry()

    def check_expiry(self):
        if not self.end_date:
            return
        days_left = date_diff(self.end_date, nowdate())
        if days_left < 0:
            self.status = "Expired"
        elif days_left <= (self.renewal_notice_days or 30):
            self.status = "Expiring Soon"
