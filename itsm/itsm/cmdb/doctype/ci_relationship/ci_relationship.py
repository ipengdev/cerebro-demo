import frappe
from frappe import _
from frappe.model.document import Document


class CIRelationship(Document):
    def validate(self):
        if not self.source_ci and not self.source_asset:
            frappe.throw(_("Either Source CI or Source Asset is required"))
        if not self.target_ci and not self.target_asset:
            frappe.throw(_("Either Target CI or Target Asset is required"))
