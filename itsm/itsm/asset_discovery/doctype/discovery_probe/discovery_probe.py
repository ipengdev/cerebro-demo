import frappe
from frappe import _
from frappe.model.document import Document


class DiscoveryProbe(Document):
    @frappe.whitelist()
    def run_discovery(self):
        """Queue a discovery job for this probe."""
        frappe.enqueue(
            "itsm.asset_discovery.discovery_engine.run_probe",
            probe_name=self.name,
            queue="long",
            timeout=3600,
        )
        frappe.msgprint(
            _("Discovery job queued for {0}").format(self.probe_name),
            indicator="blue",
            alert=True,
        )
