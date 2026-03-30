import secrets
from contextlib import contextmanager

import frappe
from frappe.utils import today, now_datetime, cstr
from frappe.rate_limiter import rate_limit
from queue_management.qms_kiosk_api import reset_avg_wait_for_services
from queue_management.qms_utils import resolve_service_names_inplace


# ──────────────────────────────────────────────
# Staff credentials — loaded from QMS Staff Login DocType
# Falls back to QMS Settings fields if DocType doesn't exist
# ──────────────────────────────────────────────
def _get_staff_credentials():
    """Load staff credentials from database (QMS Staff Login docs).

    Returns dict keyed by lowercase username, each value:
        {"password_hash": ..., "display_name": ..., "counter_number": ...}
    Results are cached for 5 minutes to avoid repeated DB hits.
    """
    cache_key = "qms_staff_credentials_map"
    cached = frappe.cache.get_value(cache_key)
    if cached:
        return cached

    credentials = {}
    # Try DocType-based staff logins first
    if frappe.db.table_exists("QMS Staff Login"):
        rows = frappe.get_all(
            "QMS Staff Login",
            filters={"enabled": 1},
            fields=["username", "display_name", "counter_number", "name"],
        )
        for row in rows:
            uname = cstr(row.username).strip().lower()
            if uname:
                credentials[uname] = {
                    "docname": row.name,
                    "display_name": row.display_name or uname,
                    "counter_number": row.counter_number,
                }
    frappe.cache.set_value(cache_key, credentials, expires_in_sec=300)
    return credentials

# Cache key prefix for staff sessions
_SESSION_PREFIX = "qms_staff_session:"
# Session TTL: 30 days — portal pages run on dedicated devices and should not expire
_SESSION_TTL = 60 * 60 * 24 * 30
_SESSION_SCOPE = "staff"


def _validate_staff_session(token):
    """Validate a staff session token. Returns staff info dict or throws."""
    if not token or not isinstance(token, str) or len(token) > 128:
        frappe.throw("Invalid or expired session", frappe.AuthenticationError)
    cache_key = f"{_SESSION_PREFIX}{token}"
    staff_id = frappe.cache.get_value(cache_key)
    if not staff_id:
        # Redis miss — try DB fallback (survives Redis restarts)
        from queue_management.qms_session_store import load_session
        staff_id = load_session(token, _SESSION_SCOPE)
        if staff_id:
            # Re-populate cache from DB
            frappe.cache.set_value(cache_key, staff_id, expires_in_sec=_SESSION_TTL)
    if not staff_id:
        frappe.throw("Session expired. Please log in again.", frappe.AuthenticationError)
    # Sliding window: extend TTL on each successful validation
    frappe.cache.set_value(cache_key, staff_id, expires_in_sec=_SESSION_TTL)
    credentials = _get_staff_credentials()
    staff = credentials.get(staff_id)
    if not staff:
        frappe.throw("Invalid staff account", frappe.AuthenticationError)
    return {
        "staff_id": staff_id,
        "display_name": staff["display_name"],
        "counter_number": staff.get("counter_number"),
    }


def _get_staff_allowed_counters(staff_id):
    """Return the active counters this staff token can control."""
    credentials = _get_staff_credentials()
    staff = credentials.get(staff_id) or {}
    assigned_num = staff.get("counter_number")
    filters = {"is_active": 1}
    if assigned_num:
        filters["counter_number"] = assigned_num
    return frappe.get_all(
        "QMS Counter",
        filters=filters,
        fields=["name", "counter_name", "counter_number", "status", "location"],
        order_by="counter_number asc",
    )


def _ensure_staff_counter_access(staff, counter):
    """Ensure the requested counter belongs to the authenticated staff session."""
    allowed = _get_staff_allowed_counters(staff["staff_id"])
    allowed_names = {row.name for row in allowed}
    if counter and counter not in allowed_names:
        frappe.throw("You are not assigned to this counter", frappe.PermissionError)
    return allowed


@contextmanager
def _staff_action_context(token, counter=None):
    """Expose website staff sessions to the shared qms_api permission checks."""
    staff = _validate_staff_session(token)
    allowed = _ensure_staff_counter_access(staff, counter)
    old_auth = getattr(frappe.flags, "qms_staff_session_authenticated", None)
    old_allowed = getattr(frappe.flags, "qms_staff_allowed_counters", None)
    frappe.flags.qms_staff_session_authenticated = True
    frappe.flags.qms_staff_allowed_counters = {row.name for row in allowed}
    try:
        yield staff
    finally:
        if old_auth is None:
            if hasattr(frappe.flags, "qms_staff_session_authenticated"):
                delattr(frappe.flags, "qms_staff_session_authenticated")
        else:
            frappe.flags.qms_staff_session_authenticated = old_auth
        if old_allowed is None:
            if hasattr(frappe.flags, "qms_staff_allowed_counters"):
                delattr(frappe.flags, "qms_staff_allowed_counters")
        else:
            frappe.flags.qms_staff_allowed_counters = old_allowed


# ──────────────────────────────────────────────
# Auth endpoints
# ──────────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60)
def staff_login(username, password):
    """Authenticate staff and return a session token."""
    username = (username or "").strip().lower()
    password = (password or "").strip()

    if not username or not password:
        frappe.throw("Username and password are required")

    credentials = _get_staff_credentials()
    staff = credentials.get(username)
    if not staff:
        frappe.throw("Invalid username or password")

    # Verify password via Frappe's password check (uses bcrypt/pbkdf2)
    if not frappe.db.table_exists("QMS Staff Login"):
        frappe.throw("Staff login system is not configured")
    stored_pw = frappe.utils.password.get_decrypted_password(
        "QMS Staff Login", staff["docname"], "password", raise_exception=False
    )
    if not stored_pw or stored_pw != password:
        frappe.throw("Invalid username or password")

    # Generate session token
    token = secrets.token_urlsafe(48)
    frappe.cache.set_value(f"{_SESSION_PREFIX}{token}", username, expires_in_sec=_SESSION_TTL)
    # Persist to DB so the session survives Redis restarts
    from queue_management.qms_session_store import save_session
    save_session(token, _SESSION_SCOPE, username)

    return {
        "token": token,
        "staff_id": username,
        "display_name": staff["display_name"],
    }


@frappe.whitelist(allow_guest=True)
def staff_logout(token):
    """Invalidate a staff session."""
    if token and isinstance(token, str) and len(token) <= 128:
        frappe.cache.delete_value(f"{_SESSION_PREFIX}{token}")
        from queue_management.qms_session_store import delete_session
        delete_session(token, _SESSION_SCOPE)
    return {"success": True}


# ──────────────────────────────────────────────
# Counter listing
# ──────────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def get_counters(token):
    """Get list of active counters filtered to the staff member's assigned counter."""
    staff = _validate_staff_session(token)
    return _get_staff_allowed_counters(staff["staff_id"])


# ──────────────────────────────────────────────
# Call screen data
# ──────────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def get_screen_data(token, counter):
    """Get full call screen data for a counter.

    The portal screen should render the same queue state as the Desk screen, so
    delegate to the shared loader instead of keeping a second copy of the query
    logic here.
    """
    from queue_management.qms_display_api import get_call_screen_data

    with _staff_action_context(token, counter):
        return get_call_screen_data(counter)


# ──────────────────────────────────────────────
# Ticket actions (all require valid staff session)
# ──────────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def action_call_next(token, counter):
    """Call the next waiting ticket."""
    from queue_management.qms_api import call_next_ticket
    with _staff_action_context(token, counter):
        result = call_next_ticket(counter)
    if not result:
        return {"empty": True}
    return result


@frappe.whitelist(allow_guest=True)
def action_call_ticket(token, ticket, counter):
    """Call a specific ticket."""
    from queue_management.qms_api import call_ticket
    with _staff_action_context(token, counter):
        return call_ticket(ticket, counter)


@frappe.whitelist(allow_guest=True)
def action_complete(token, ticket):
    """Complete a ticket."""
    from queue_management.qms_api import complete_ticket
    with _staff_action_context(token):
        return complete_ticket(ticket)


@frappe.whitelist(allow_guest=True)
def action_start_serving(token, ticket):
    """Move a called ticket into active service."""
    from queue_management.qms_api import start_serving
    with _staff_action_context(token):
        return start_serving(ticket)


@frappe.whitelist(allow_guest=True)
def action_hold(token, ticket, reason=None):
    """Put a ticket on hold."""
    from queue_management.qms_api import hold_ticket
    with _staff_action_context(token):
        return hold_ticket(ticket, reason)


@frappe.whitelist(allow_guest=True)
def action_no_show(token, ticket):
    """Mark ticket as no-show."""
    from queue_management.qms_api import mark_no_show
    with _staff_action_context(token):
        return mark_no_show(ticket)


@frappe.whitelist(allow_guest=True)
def action_transfer(token, ticket, to_counter=None, to_location=None, reason=None):
    """Transfer a ticket."""
    from queue_management.qms_api import transfer_ticket
    with _staff_action_context(token):
        return transfer_ticket(ticket, to_counter, to_location, reason)


@frappe.whitelist(allow_guest=True)
def action_return(token, ticket):
    """Return a transferred ticket to origin counter."""
    from queue_management.qms_api import return_ticket
    with _staff_action_context(token):
        return return_ticket(ticket)


@frappe.whitelist(allow_guest=True)
def action_start_shift(token, counter):
    """Start shift at counter."""
    from queue_management.qms_api import start_shift
    with _staff_action_context(token, counter):
        return start_shift(counter)


@frappe.whitelist(allow_guest=True)
def action_end_shift(token, counter):
    """End shift at counter."""
    from queue_management.qms_api import end_shift
    with _staff_action_context(token, counter):
        return end_shift(counter)


@frappe.whitelist(allow_guest=True)
def action_take_break(token, counter):
    """Put counter on break."""
    from queue_management.qms_api import take_break
    with _staff_action_context(token, counter):
        return take_break(counter)


@frappe.whitelist(allow_guest=True)
def action_reset_kiosk_avg_wait(token, counter):
    """Reset kiosk average wait calculations for the counter's services."""
    with _staff_action_context(token, counter):
        services = [row.service for row in frappe.get_all(
            "QMS Counter Service",
            filters={"parent": counter},
            fields=["service"],
        )]
        if not services:
            return {"success": True, "reset_count": 0, "services": []}
        reset_at = reset_avg_wait_for_services(services)
    return {
        "success": True,
        "reset_count": len(services),
        "services": services,
        "reset_at": reset_at,
    }


@frappe.whitelist(allow_guest=True)
def get_peer_counter_preview(token, counter):
    """Get a read-only preview of other counters' activity (batch-optimized)."""
    staff = _validate_staff_session(token)
    _ensure_staff_counter_access(staff, counter)
    peer_counters = frappe.get_all(
        "QMS Counter",
        filters={"is_active": 1, "name": ("!=", counter)},
        fields=["name", "counter_name", "counter_number", "status"],
        order_by="counter_number asc",
    )
    if not peer_counters:
        return []

    peer_names = [pc.name for pc in peer_counters]

    # Batch: all serving tickets across peers
    all_serving = frappe.get_all(
        "QMS Queue Ticket",
        filters={"counter": ("in", peer_names), "status": ("in", ["Called", "Serving"]), "token_date": today()},
        fields=["name", "ticket_number", "service", "patient_name", "called_time", "status", "counter"],
        order_by="called_time asc",
    )
    resolve_service_names_inplace(all_serving)
    serving_map = {}
    for s in all_serving:
        serving_map.setdefault(s.counter, []).append(s)

    # Batch: counter-service mapping
    all_cs = frappe.get_all(
        "QMS Counter Service", filters={"parent": ("in", peer_names)}, fields=["parent", "service"],
    )
    svc_map = {}
    for cs in all_cs:
        svc_map.setdefault(cs.parent, []).append(cs.service)

    # Batch: on-hold counts
    oh_rows = frappe.db.sql(
        """SELECT counter, COUNT(*) as cnt FROM `tabQMS Queue Ticket`
           WHERE counter IN ({}) AND status='On Hold' AND token_date=%s
           GROUP BY counter""".format(", ".join(["%s"] * len(peer_names))),
        (*peer_names, today()), as_dict=True,
    )
    oh_map = {r.counter: r.cnt for r in oh_rows}

    # Batch: directly-assigned waiting counts
    dw_rows = frappe.db.sql(
        """SELECT counter, COUNT(*) as cnt FROM `tabQMS Queue Ticket`
           WHERE counter IN ({}) AND status='Waiting' AND token_date=%s
           GROUP BY counter""".format(", ".join(["%s"] * len(peer_names))),
        (*peer_names, today()), as_dict=True,
    )
    dw_map = {r.counter: r.cnt for r in dw_rows}

    # Batch: unassigned waiting tickets by service
    all_svcs = list({s for svcs in svc_map.values() for s in svcs})
    uw_map = {}
    if all_svcs:
        uw_rows = frappe.db.sql(
            """SELECT service, COUNT(*) as cnt FROM `tabQMS Queue Ticket`
               WHERE status='Waiting' AND token_date=%s AND service IN ({})
               AND (counter IS NULL OR counter='')
               GROUP BY service""".format(", ".join(["%s"] * len(all_svcs))),
            (today(), *all_svcs), as_dict=True,
        )
        uw_map = {r.service: r.cnt for r in uw_rows}

    result = []
    for pc in peer_counters:
        pc_svcs = svc_map.get(pc.name, [])
        direct_waiting = dw_map.get(pc.name, 0)
        svc_waiting = sum(uw_map.get(s, 0) for s in pc_svcs) if pc_svcs else 0
        result.append({
            "name": pc.name,
            "counter_name": pc.counter_name,
            "counter_number": pc.counter_number,
            "status": pc.status,
            "serving": serving_map.get(pc.name, []),
            "waiting_count": max(direct_waiting, svc_waiting),
            "on_hold_count": oh_map.get(pc.name, 0),
        })
    return result


@frappe.whitelist(allow_guest=True)
def get_transfer_options(token, counter):
    """Get available counters and locations for transfer dialog."""
    staff = _validate_staff_session(token)
    _ensure_staff_counter_access(staff, counter)
    counters = frappe.get_all(
        "QMS Counter",
        filters={"is_active": 1, "name": ("!=", counter)},
        fields=["name", "counter_name", "counter_number", "status", "location"],
    )
    locations = frappe.get_all(
        "QMS Location",
        filters={"is_active": 1},
        fields=["name", "location_name", "location_type"],
    )
    return {"counters": counters, "locations": locations}
