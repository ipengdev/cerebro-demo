"""ITSM notification configuration."""

import frappe


def get_notification_config():
    return {
        "for_doctype": {
            "Service Ticket": {"status": ("in", ("Open", "In Progress", "Pending"))},
            "IT Contract": {"status": "Expiring Soon"},
            "Software License": {"status": "Expired"},
        },
    }
