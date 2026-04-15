import frappe
from frappe import _
from frappe.model.document import Document


class DiscoveryResult(Document):
    @frappe.whitelist()
    def create_it_asset(self):
        """Create an IT Asset from this discovery result."""
        if self.linked_asset:
            frappe.throw(_("This result is already linked to asset {0}").format(self.linked_asset))

        device_type_map = {
            "Server": "Server",
            "Workstation": "Hardware",
            "Router": "Network Device",
            "Switch": "Network Device",
            "Firewall": "Network Device",
            "Printer": "Printer",
            "Access Point": "Network Device",
            "Storage": "Server",
            "Virtual Machine": "Virtual Machine",
        }

        asset = frappe.get_doc({
            "doctype": "IT Asset",
            "asset_name": self.hostname or self.ip_address,
            "category": self._get_or_create_category(),
            "asset_type": device_type_map.get(self.device_type, "Hardware"),
            "status": "Active",
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "operating_system": self.os_detected,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "discovery_source": "Network Scan",
            "last_seen": self.discovered_at,
            "is_online": 1,
        })
        asset.insert(ignore_permissions=True)

        self.linked_asset = asset.name
        self.auto_created = 1
        self.status = "Created Asset"
        self.save(ignore_permissions=True)

        frappe.msgprint(
            _("IT Asset {0} created successfully").format(asset.name),
            indicator="green",
            alert=True,
        )
        return asset.name

    def _get_or_create_category(self):
        cat_name = self.device_type or "Discovered Device"
        if not frappe.db.exists("IT Asset Category", cat_name):
            frappe.get_doc({
                "doctype": "IT Asset Category",
                "category_name": cat_name,
            }).insert(ignore_permissions=True)
        return cat_name
