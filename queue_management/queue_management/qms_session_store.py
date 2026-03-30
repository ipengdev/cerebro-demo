"""DB-backed session store for QMS portal pages.

QMS portal sessions (staff call screen, display board) are stored in Redis for
fast lookups, with a MariaDB fallback table so they survive Redis restarts.

The table ``_qms_portal_session`` is created automatically on first use.
"""
import frappe
from frappe.utils import now_datetime

_TABLE = "_qms_portal_session"
_TABLE_READY = False


def _ensure_table():
    """Create the session table if it doesn't exist (idempotent)."""
    global _TABLE_READY
    if _TABLE_READY:
        return
    if not frappe.db.sql(
        "SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=%s",
        (_TABLE,),
    ):
        frappe.db.sql(f"""
            CREATE TABLE `{_TABLE}` (
                `token`      VARCHAR(128) NOT NULL,
                `scope`      VARCHAR(32)  NOT NULL DEFAULT 'staff',
                `username`   VARCHAR(140) NOT NULL,
                `created`    DATETIME     NOT NULL,
                `last_used`  DATETIME     NOT NULL,
                PRIMARY KEY (`token`),
                INDEX `idx_scope_username` (`scope`, `username`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        frappe.db.commit()
    _TABLE_READY = True


def save_session(token, scope, username):
    """Persist a session token to the DB (INSERT or UPDATE)."""
    _ensure_table()
    now = now_datetime()
    frappe.db.sql(
        f"REPLACE INTO `{_TABLE}` (`token`, `scope`, `username`, `created`, `last_used`) "
        "VALUES (%s, %s, %s, %s, %s)",
        (token, scope, username, now, now),
    )
    frappe.db.commit()


def load_session(token, scope, max_age_seconds=60 * 60 * 24 * 30):
    """Look up a non-expired session token in the DB. Returns username or None."""
    _ensure_table()
    row = frappe.db.sql(
        f"""SELECT `username` FROM `{_TABLE}`
            WHERE `token`=%s AND `scope`=%s
              AND `last_used` >= DATE_SUB(NOW(), INTERVAL %s SECOND)
            LIMIT 1""",
        (token, scope, max_age_seconds),
    )
    if row:
        # Touch last_used
        frappe.db.sql(
            f"UPDATE `{_TABLE}` SET `last_used`=%s WHERE `token`=%s AND `scope`=%s",
            (now_datetime(), token, scope),
        )
        frappe.db.commit()
        return row[0][0]
    return None


def delete_session(token, scope):
    """Remove a session from the DB."""
    _ensure_table()
    frappe.db.sql(f"DELETE FROM `{_TABLE}` WHERE `token`=%s AND `scope`=%s", (token, scope))
    frappe.db.commit()


def cleanup_old_sessions(max_age_days=30):
    """Remove sessions older than *max_age_days* (called from scheduler)."""
    _ensure_table()
    frappe.db.sql(
        f"DELETE FROM `{_TABLE}` WHERE `last_used` < DATE_SUB(NOW(), INTERVAL %s DAY)",
        (max_age_days,),
    )
    frappe.db.commit()
