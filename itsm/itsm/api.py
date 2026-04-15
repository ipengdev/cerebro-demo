"""
ITSM REST API endpoints for external integrations.

All endpoints are under: /api/method/itsm.api.*
"""

import frappe
from frappe import _
import json


@frappe.whitelist(allow_guest=False)
def get_asset_summary():
    """Get asset summary stats for dashboard."""
    total = frappe.db.count("IT Asset")
    by_status = frappe.db.sql("""
        SELECT status, COUNT(*) as count FROM `tabIT Asset` GROUP BY status
    """, as_dict=True)
    by_type = frappe.db.sql("""
        SELECT asset_type, COUNT(*) as count FROM `tabIT Asset` GROUP BY asset_type
    """, as_dict=True)
    online = frappe.db.count("IT Asset", {"is_online": 1})
    offline = total - online

    # Warranty alerts
    from frappe.utils import nowdate, add_days
    warranty_expiring = frappe.db.count(
        "IT Asset",
        {
            "warranty_expiry": ["between", [nowdate(), add_days(nowdate(), 90)]],
            "status": ["not in", ["Disposed", "Retired"]],
        },
    )

    return {
        "total": total,
        "by_status": {r["status"]: r["count"] for r in by_status},
        "by_type": {r["asset_type"]: r["count"] for r in by_type},
        "online": online,
        "offline": offline,
        "warranty_expiring_90_days": warranty_expiring,
    }


@frappe.whitelist(allow_guest=False)
def get_ticket_summary():
    """Get ticket summary stats for dashboard."""
    total = frappe.db.count("Service Ticket")
    by_status = frappe.db.sql("""
        SELECT status, COUNT(*) as count FROM `tabService Ticket` GROUP BY status
    """, as_dict=True)
    by_priority = frappe.db.sql("""
        SELECT priority, COUNT(*) as count FROM `tabService Ticket` GROUP BY priority
    """, as_dict=True)

    open_tickets = frappe.db.count(
        "Service Ticket", {"status": ["in", ["Open", "In Progress", "Pending"]]}
    )

    # SLA breach count
    sla_breached = frappe.db.count(
        "Service Ticket",
        {
            "resolution_sla_status": "Breached",
            "status": ["not in", ["Closed", "Cancelled"]],
        },
    )

    # Average resolution time (last 30 days)
    from frappe.utils import add_days, nowdate
    avg_resolution = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, creation, resolved_on)) as avg_hours
        FROM `tabService Ticket`
        WHERE resolved_on IS NOT NULL
        AND creation >= %(start)s
    """, {"start": add_days(nowdate(), -30)}, as_dict=True)

    return {
        "total": total,
        "by_status": {r["status"]: r["count"] for r in by_status},
        "by_priority": {r["priority"]: r["count"] for r in by_priority},
        "open_tickets": open_tickets,
        "sla_breached": sla_breached,
        "avg_resolution_hours": round(avg_resolution[0].avg_hours or 0, 1) if avg_resolution else 0,
    }


@frappe.whitelist(allow_guest=False)
def get_contract_alerts():
    """Get contracts that are expiring soon."""
    from frappe.utils import nowdate, add_days

    expiring = frappe.get_all(
        "IT Contract",
        filters={
            "end_date": ["between", [nowdate(), add_days(nowdate(), 60)]],
            "status": ["not in", ["Cancelled", "Expired"]],
        },
        fields=["name", "contract_name", "vendor", "end_date", "contract_value"],
        order_by="end_date asc",
    )

    expired = frappe.db.count(
        "IT Contract",
        {"status": "Expired"},
    )

    total_active = frappe.db.count(
        "IT Contract",
        {"status": "Active"},
    )

    return {
        "expiring_60_days": expiring,
        "expired_count": expired,
        "active_count": total_active,
    }


@frappe.whitelist(allow_guest=False)
def get_license_summary():
    """Get software license compliance summary."""
    total = frappe.db.count("Software License")
    active = frappe.db.count("Software License", {"status": "Active"})
    expired = frappe.db.count("Software License", {"status": "Expired"})

    # Over-allocated licenses
    over_allocated = frappe.db.sql("""
        SELECT name, license_name, software_name, total_licenses, used_licenses
        FROM `tabSoftware License`
        WHERE used_licenses > total_licenses AND status = 'Active'
    """, as_dict=True)

    return {
        "total": total,
        "active": active,
        "expired": expired,
        "over_allocated": over_allocated,
    }


@frappe.whitelist(allow_guest=False)
def bulk_import_assets(assets):
    """Bulk import IT Assets from JSON data.

    Args:
        assets: JSON string or list of asset dicts
    """
    if isinstance(assets, str):
        assets = json.loads(assets)

    created = 0
    errors = []

    for asset_data in assets:
        try:
            doc = frappe.get_doc({"doctype": "IT Asset", **asset_data})
            doc.insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            errors.append({
                "asset": asset_data.get("asset_name", "Unknown"),
                "error": str(e),
            })

    frappe.db.commit()
    return {"created": created, "errors": errors}


@frappe.whitelist(allow_guest=False)
def get_dashboard_stats():
    """Comprehensive stats for the ITSM workspace dashboard."""
    from frappe.utils import nowdate, add_days, getdate, now_datetime

    today = nowdate()

    # ── Summary counts ──
    open_tickets = frappe.db.count("Service Ticket", {"status": "Open"})
    in_progress = frappe.db.count("Service Ticket", {"status": "In Progress"})
    pending = frappe.db.count("Service Ticket", {"status": ["in", ["Pending", "On Hold"]]})
    sla_breached = frappe.db.count("Service Ticket", {
        "resolution_sla_status": "Breached",
        "status": ["not in", ["Closed", "Cancelled"]],
    })
    active_assets = frappe.db.count("IT Asset", {"status": "Active"})
    resolved_today = frappe.db.count("Service Ticket", {"resolved_on": [">=", today]})
    total_tickets = frappe.db.count("Service Ticket")
    closed_tickets = frappe.db.count("Service Ticket", {"status": "Closed"})

    # ── By status ──
    by_status = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabService Ticket`
        GROUP BY status
    """, as_dict=True)

    # ── By priority ──
    by_priority = frappe.db.sql("""
        SELECT priority, COUNT(*) as count
        FROM `tabService Ticket`
        GROUP BY priority
    """, as_dict=True)

    # ── By category ──
    by_category = frappe.db.sql("""
        SELECT ticket_category, COUNT(*) as count
        FROM `tabService Ticket`
        WHERE ticket_category IS NOT NULL AND ticket_category != ''
        GROUP BY ticket_category
        ORDER BY count DESC LIMIT 10
    """, as_dict=True)

    # ── Trend: tickets created & resolved per day (last 14 days) ──
    start_14 = add_days(today, -13)
    trend_created = frappe.db.sql("""
        SELECT DATE(creation) as day, COUNT(*) as cnt
        FROM `tabService Ticket`
        WHERE DATE(creation) >= %(start)s
        GROUP BY DATE(creation) ORDER BY day
    """, {"start": start_14}, as_dict=True)
    trend_resolved = frappe.db.sql("""
        SELECT DATE(resolved_on) as day, COUNT(*) as cnt
        FROM `tabService Ticket`
        WHERE DATE(resolved_on) >= %(start)s AND resolved_on IS NOT NULL
        GROUP BY DATE(resolved_on) ORDER BY day
    """, {"start": start_14}, as_dict=True)

    # ── Recent tickets (last 10) ──
    recent_tickets = frappe.get_all(
        "Service Ticket",
        fields=["name", "subject", "status", "priority", "assigned_to", "creation"],
        order_by="creation desc",
        limit=10,
    )

    # ── Top assignees ──
    top_assignees = frappe.db.sql("""
        SELECT assigned_to, COUNT(*) as cnt,
            SUM(CASE WHEN status IN ('Closed', 'Resolved') THEN 1 ELSE 0 END) as resolved_cnt
        FROM `tabService Ticket`
        WHERE assigned_to IS NOT NULL AND assigned_to != ''
        GROUP BY assigned_to ORDER BY cnt DESC LIMIT 5
    """, as_dict=True)

    # ── Overdue tickets ──
    overdue_tickets = frappe.get_all(
        "Service Ticket",
        filters={
            "resolution_by": ["<", now_datetime()],
            "status": ["not in", ["Closed", "Cancelled", "Resolved"]],
        },
        fields=["name", "subject", "priority", "assigned_to", "resolution_by"],
        order_by="resolution_by asc",
        limit=10,
    )

    # ── Average resolution time (hours, last 30 days) ──
    avg_res = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, creation, resolved_on)) as avg_hours
        FROM `tabService Ticket`
        WHERE resolved_on IS NOT NULL AND creation >= %(start)s
    """, {"start": add_days(today, -30)}, as_dict=True)
    avg_resolution_hours = round(avg_res[0].avg_hours or 0, 1) if avg_res and avg_res[0].avg_hours else 0

    # ── SLA compliance rate ──
    total_with_sla = frappe.db.count("Service Ticket", {"resolution_by": ["is", "set"]})
    sla_met = frappe.db.count("Service Ticket", {
        "resolution_sla_status": ["!=", "Breached"],
        "resolution_by": ["is", "set"],
        "status": ["in", ["Resolved", "Closed"]],
    })
    sla_compliance = round((sla_met / total_with_sla * 100) if total_with_sla else 100, 1)

    return {
        "open_tickets": open_tickets,
        "in_progress": in_progress,
        "pending": pending,
        "sla_breached": sla_breached,
        "active_assets": active_assets,
        "resolved_today": resolved_today,
        "total_tickets": total_tickets,
        "closed_tickets": closed_tickets,
        "avg_resolution_hours": avg_resolution_hours,
        "sla_compliance": sla_compliance,
        "by_status": {r["status"]: r["count"] for r in by_status},
        "by_priority": {r["priority"]: r["count"] for r in by_priority},
        "by_category": {r["ticket_category"]: r["count"] for r in by_category if r["ticket_category"]},
        "trend_created": {str(r["day"]): r["cnt"] for r in trend_created},
        "trend_resolved": {str(r["day"]): r["cnt"] for r in trend_resolved},
        "recent_tickets": recent_tickets,
        "top_assignees": top_assignees,
        "overdue_tickets": overdue_tickets,
    }


@frappe.whitelist(allow_guest=False)
def get_ticket_activity(ticket_name):
    """Get activity timeline for a specific ticket."""
    from frappe.utils import pretty_date

    if not ticket_name or not frappe.db.exists("Service Ticket", ticket_name):
        return []

    activities = []

    # Creation
    doc = frappe.get_doc("Service Ticket", ticket_name)
    activities.append({
        "type": "creation",
        "text": "Ticket created",
        "by": doc.owner,
        "by_name": frappe.utils.get_fullname(doc.owner),
        "dt": str(doc.creation),
        "ago": pretty_date(doc.creation),
    })

    # Version log (which tracks field changes)
    versions = frappe.get_all(
        "Version",
        filters={"ref_doctype": "Service Ticket", "docname": ticket_name},
        fields=["data", "owner", "creation"],
        order_by="creation asc",
        limit=30,
    )

    for v in versions:
        try:
            data = json.loads(v.data) if isinstance(v.data, str) else v.data
            changed = data.get("changed", [])
            for ch in changed:
                field_name, old_val, new_val = ch[0], ch[1], ch[2]
                if field_name == "status":
                    activities.append({
                        "type": "status_change",
                        "text": f"Status changed from <b>{old_val}</b> to <b>{new_val}</b>",
                        "by": v.owner,
                        "by_name": frappe.utils.get_fullname(v.owner),
                        "dt": str(v.creation),
                        "ago": pretty_date(v.creation),
                    })
                elif field_name == "assigned_to":
                    new_name = frappe.utils.get_fullname(new_val) if new_val else "Unassigned"
                    activities.append({
                        "type": "assignment",
                        "text": f"Assigned to <b>{new_name}</b>",
                        "by": v.owner,
                        "by_name": frappe.utils.get_fullname(v.owner),
                        "dt": str(v.creation),
                        "ago": pretty_date(v.creation),
                    })
                elif field_name == "escalation_level":
                    activities.append({
                        "type": "escalation",
                        "text": f"Escalated to Level {new_val}",
                        "by": v.owner,
                        "by_name": frappe.utils.get_fullname(v.owner),
                        "dt": str(v.creation),
                        "ago": pretty_date(v.creation),
                    })
                elif field_name == "priority":
                    activities.append({
                        "type": "status_change",
                        "text": f"Priority changed from <b>{old_val}</b> to <b>{new_val}</b>",
                        "by": v.owner,
                        "by_name": frappe.utils.get_fullname(v.owner),
                        "dt": str(v.creation),
                        "ago": pretty_date(v.creation),
                    })
        except Exception:
            pass

    # Comments
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Service Ticket",
            "reference_name": ticket_name,
            "comment_type": ["in", ["Comment", "Info"]],
        },
        fields=["content", "owner", "creation", "comment_type"],
        order_by="creation asc",
        limit=20,
    )

    for c in comments:
        activities.append({
            "type": "comment" if c.comment_type == "Comment" else "escalation",
            "text": frappe.utils.strip_html_tags(c.content or "")[:120],
            "by": c.owner,
            "by_name": frappe.utils.get_fullname(c.owner),
            "dt": str(c.creation),
            "ago": pretty_date(c.creation),
        })

    # Sort reverse chronological
    activities.sort(key=lambda x: x["dt"], reverse=True)
    return activities[:20]
