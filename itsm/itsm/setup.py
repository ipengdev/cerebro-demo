"""ITSM post-install setup: create roles, default data, and workspace."""

import frappe
from frappe import _


def after_install():
    create_roles()
    create_default_data()
    frappe.db.commit()


def create_roles():
    """Create IT Manager and IT User roles if they don't exist."""
    for role_name in ("IT Manager", "IT User"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)


def create_default_data():
    """Create default categories, ticket types, CI types, relationship types, and SLA."""

    # Default IT Asset Categories
    categories = [
        "Desktop", "Laptop", "Server", "Network Switch", "Router",
        "Firewall", "Access Point", "Printer", "Scanner", "Monitor",
        "Mobile Phone", "Tablet", "Virtual Machine", "Cloud Instance",
        "Storage Device", "UPS", "IP Phone", "Video Conferencing",
    ]
    for cat in categories:
        if not frappe.db.exists("IT Asset Category", cat):
            frappe.get_doc({
                "doctype": "IT Asset Category",
                "category_name": cat,
            }).insert(ignore_permissions=True)

    # Default Ticket Types
    ticket_types = [
        {"type_name": "Incident", "default_priority": "High", "description": "Unplanned service interruption or degradation"},
        {"type_name": "Service Request", "default_priority": "Medium", "description": "Standard request for service"},
        {"type_name": "Change Request", "default_priority": "Medium", "description": "Request for change to IT infrastructure"},
        {"type_name": "Problem", "default_priority": "High", "description": "Root cause of one or more incidents"},
        {"type_name": "Maintenance", "default_priority": "Low", "description": "Planned maintenance activity"},
    ]
    for tt in ticket_types:
        if not frappe.db.exists("Ticket Type", tt["type_name"]):
            frappe.get_doc({"doctype": "Ticket Type", **tt}).insert(ignore_permissions=True)

    # Default CI Types
    ci_types = [
        {"type_name": "Application", "description": "Software application or service"},
        {"type_name": "Database", "description": "Database instance"},
        {"type_name": "Operating System", "description": "OS instance"},
        {"type_name": "Virtual Machine", "description": "Virtual machine"},
        {"type_name": "Container", "description": "Container or pod"},
        {"type_name": "Network Service", "description": "DNS, DHCP, Load Balancer, etc."},
        {"type_name": "Cloud Service", "description": "Cloud-hosted service"},
        {"type_name": "Business Service", "description": "Business-facing service"},
        {"type_name": "Cluster", "description": "Server or application cluster"},
        {"type_name": "API", "description": "API endpoint or integration"},
    ]
    for ci in ci_types:
        if not frappe.db.exists("CI Type", ci["type_name"]):
            frappe.get_doc({"doctype": "CI Type", **ci}).insert(ignore_permissions=True)

    # Default CI Relationship Types
    rel_types = [
        {"relationship_type": "Depends On", "reverse_label": "Depended By", "description": "Service dependency"},
        {"relationship_type": "Runs On", "reverse_label": "Hosts", "description": "Application runs on infrastructure"},
        {"relationship_type": "Connected To", "reverse_label": "Connected To", "description": "Network connectivity"},
        {"relationship_type": "Managed By", "reverse_label": "Manages", "description": "Management relationship"},
        {"relationship_type": "Part Of", "reverse_label": "Contains", "description": "Composition relationship"},
        {"relationship_type": "Backed Up By", "reverse_label": "Backs Up", "description": "Backup relationship"},
        {"relationship_type": "Clustered With", "reverse_label": "Clustered With", "description": "Cluster membership"},
    ]
    for rt in rel_types:
        if not frappe.db.exists("CI Relationship Type", rt["relationship_type"]):
            frappe.get_doc({"doctype": "CI Relationship Type", **rt}).insert(ignore_permissions=True)

    # Default SLA Policy
    if not frappe.db.exists("SLA Policy", "Standard SLA"):
        sla = frappe.get_doc({
            "doctype": "SLA Policy",
            "policy_name": "Standard SLA",
            "is_default": 1,
            "is_active": 1,
            "description": "Default SLA policy for all ticket types",
            "priorities": [
                {"priority": "Urgent", "response_time_hours": 0.5, "resolution_time_hours": 4},
                {"priority": "High", "response_time_hours": 1, "resolution_time_hours": 8},
                {"priority": "Medium", "response_time_hours": 4, "resolution_time_hours": 24},
                {"priority": "Low", "response_time_hours": 8, "resolution_time_hours": 72},
            ],
        })
        sla.insert(ignore_permissions=True)

    # Default Service Catalog
    if not frappe.db.exists("Service Catalog", "IT Service Catalog"):
        catalog = frappe.get_doc({
            "doctype": "Service Catalog",
            "catalog_name": "IT Service Catalog",
            "description": "Standard IT services available to employees",
            "is_active": 1,
            "items": [
                {"item_name": "New Laptop Request", "category": "Hardware", "fulfillment_time_hours": 48, "requires_approval": 1},
                {"item_name": "Software Installation", "category": "Software", "fulfillment_time_hours": 4, "requires_approval": 0},
                {"item_name": "VPN Access", "category": "Access", "fulfillment_time_hours": 2, "requires_approval": 1},
                {"item_name": "Email Account Setup", "category": "Email", "fulfillment_time_hours": 1, "requires_approval": 0},
                {"item_name": "Network Access", "category": "Network", "fulfillment_time_hours": 4, "requires_approval": 1},
                {"item_name": "Password Reset", "category": "Access", "fulfillment_time_hours": 0.5, "requires_approval": 0},
                {"item_name": "New Monitor Request", "category": "Hardware", "fulfillment_time_hours": 24, "requires_approval": 1},
                {"item_name": "Printer Setup", "category": "Hardware", "fulfillment_time_hours": 2, "requires_approval": 0},
            ],
        })
        catalog.insert(ignore_permissions=True)
