import frappe
from frappe.model.document import Document


class ConfigurationItem(Document):
    def validate(self):
        if self.asset:
            asset = frappe.get_doc("IT Asset", self.asset)
            if not self.ci_name:
                self.ci_name = asset.asset_name
