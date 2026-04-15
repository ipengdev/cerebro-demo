import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_hours, add_to_date, get_datetime


class ServiceTicket(Document):
    def validate(self):
        self.set_sla_targets()
        self.check_sla_status()

    def before_save(self):
        if self.has_value_changed("status"):
            old_status = self.get_doc_before_save()
            if old_status:
                old = old_status.status
                new = self.status

                # Track first response
                if old == "Open" and new in ("In Progress", "Pending"):
                    if not self.first_responded_on:
                        self.first_responded_on = now_datetime()

                # Track resolution
                if new == "Resolved" and not self.resolved_on:
                    self.resolved_on = now_datetime()

                # Track closure
                if new == "Closed" and not self.closed_on:
                    self.closed_on = now_datetime()
                    self.closed_by = frappe.session.user

                # Track reopening
                if old in ("Resolved", "Closed") and new in ("Open", "In Progress"):
                    self.reopened_count = (self.reopened_count or 0) + 1
                    self.resolved_on = None

    def set_sla_targets(self):
        if not self.sla_policy or (self.response_by and self.resolution_by):
            return

        policy = frappe.get_doc("SLA Policy", self.sla_policy)
        for row in policy.priorities:
            if row.priority == self.priority:
                if not self.response_by:
                    self.response_by = add_to_date(
                        self.creation or now_datetime(),
                        hours=row.response_time_hours,
                    )
                if not self.resolution_by:
                    self.resolution_by = add_to_date(
                        self.creation or now_datetime(),
                        hours=row.resolution_time_hours,
                    )
                break

    def check_sla_status(self):
        now = now_datetime()
        if self.response_by:
            response_by = get_datetime(self.response_by)
            if self.first_responded_on:
                self.response_sla_status = (
                    "Within SLA"
                    if get_datetime(self.first_responded_on) <= response_by
                    else "Breached"
                )
            elif now > response_by:
                self.response_sla_status = "Breached"

        if self.resolution_by:
            resolution_by = get_datetime(self.resolution_by)
            if self.resolved_on:
                self.resolution_sla_status = (
                    "Within SLA"
                    if get_datetime(self.resolved_on) <= resolution_by
                    else "Breached"
                )
            elif now > resolution_by:
                self.resolution_sla_status = "Breached"
