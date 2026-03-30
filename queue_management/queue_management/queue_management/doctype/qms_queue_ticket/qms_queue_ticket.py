import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds


class QMSQueueTicket(Document):

	@staticmethod
	def on_doctype_update():
		"""Add composite indexes for common QMS query patterns."""
		frappe.db.add_index(
			"QMS Queue Ticket",
			fields=["token_date", "status", "service", "check_in_time"],
			index_name="idx_queue_lookup",
		)
		frappe.db.add_index(
			"QMS Queue Ticket",
			fields=["location", "status", "token_date"],
			index_name="idx_location_status",
		)

	_valid_transitions = {
		"Waiting": ["Called", "Cancelled", "On Hold"],
		"Called": ["Serving", "No Show", "Waiting", "On Hold", "Completed"],
		"Serving": ["Completed", "On Hold", "Waiting"],
		"On Hold": ["Called", "Waiting", "Cancelled"],
		"Completed": [],
		"Cancelled": [],
		"No Show": ["Called", "Waiting"],
	}

	def validate(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_status = self.get_doc_before_save().status if self.get_doc_before_save() else None
			if old_status and old_status in self._valid_transitions:
				allowed = self._valid_transitions[old_status]
				if self.status not in allowed:
					frappe.throw(f"Cannot change status from {old_status} to {self.status}")

	def before_insert(self):
		self.check_in_time = now_datetime()
		if not self.ticket_number:
			self.ticket_number = self.generate_ticket_number()

	def generate_ticket_number(self):
		prefix = self.get_ticket_prefix()
		# Use MAX on the numeric suffix to survive deletions and avoid duplicates
		result = frappe.db.sql(
			"""SELECT MAX(CAST(REGEXP_SUBSTR(ticket_number, '[0-9]+$') AS UNSIGNED))
			   FROM `tabQMS Queue Ticket`
			   WHERE token_date = %s AND service = %s
			   FOR UPDATE""",
			(self.token_date, self.service)
		)
		last_num = result[0][0] if result and result[0][0] else 0
		return f"{prefix}{(last_num + 1):03d}"

	def get_ticket_prefix(self):
		if self.service:
			service_prefix = frappe.db.get_value("QMS Service", self.service, "ticket_prefix")
			if service_prefix:
				return service_prefix
		return frappe.db.get_single_value("QMS Settings", "default_ticket_prefix") or "T"

	def before_save(self):
		self.compute_timings()

	# Sentinel value used by return-to-queue to sort returned tickets first.
	_RETURN_SENTINEL = "2000-01-01 00:00:00"

	def compute_timings(self):
		if self.called_time and self.check_in_time:
			# Skip bogus sentinel check_in_time used for FIFO priority
			if str(self.check_in_time).startswith("2000-01-01"):
				self.wait_time_mins = 0
			else:
				diff = time_diff_in_seconds(self.called_time, self.check_in_time)
				if diff and diff > 0:
					self.wait_time_mins = round(diff / 60, 1)

		if self.service_end_time and self.service_start_time:
			diff = time_diff_in_seconds(self.service_end_time, self.service_start_time)
			if diff and diff > 0:
				self.service_duration_mins = round(diff / 60, 1)
