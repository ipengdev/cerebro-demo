import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, add_days


class ITAsset(Document):
    def validate(self):
        self.validate_warranty()
        self.set_status_color()

    def validate_warranty(self):
        if self.warranty_expiry and getdate(self.warranty_expiry) < getdate(nowdate()):
            frappe.msgprint(
                _("Warranty for {0} has expired on {1}").format(
                    self.asset_name, self.warranty_expiry
                ),
                indicator="orange",
                alert=True,
            )

    def set_status_color(self):
        status_map = {
            "Active": "green",
            "Deployed": "green",
            "In Stock": "blue",
            "In Maintenance": "orange",
            "Retired": "gray",
            "Disposed": "red",
            "Lost": "red",
            "Stolen": "red",
        }
        self.indicator_color = status_map.get(self.status, "gray")

    def on_update(self):
        self.create_log("Updated")

    def after_insert(self):
        self.create_log("Created")

    def create_log(self, action):
        if not frappe.flags.in_migrate:
            frappe.get_doc({
                "doctype": "IT Asset Log",
                "asset": self.name,
                "action": action,
                "timestamp": frappe.utils.now_datetime(),
                "user": frappe.session.user,
                "details": f"Asset {action}: {self.asset_name} ({self.status})",
            }).insert(ignore_permissions=True)
