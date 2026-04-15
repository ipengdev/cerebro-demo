import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime, add_days


class Delegation(Document):
	def validate(self):
		self.validate_dates()
		self.validate_users()
		self.validate_overlap()

	def validate_dates(self):
		if getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))

		if self.docstatus == 0 and getdate(self.start_date) < getdate(nowdate()):
			frappe.throw(_("Start Date cannot be in the past."))

	def validate_users(self):
		if self.user == self.delegate:
			frappe.throw(_("User and Delegate cannot be the same person."))

		if not frappe.db.exists("User", self.user):
			frappe.throw(_("User {0} does not exist.").format(self.user))

		if not frappe.db.exists("User", self.delegate):
			frappe.throw(_("Delegate {0} does not exist.").format(self.delegate))

		if not frappe.db.get_value("User", self.user, "enabled"):
			frappe.throw(_("User {0} is disabled.").format(self.user))

		if not frappe.db.get_value("User", self.delegate, "enabled"):
			frappe.throw(_("Delegate {0} is disabled.").format(self.delegate))

	def validate_overlap(self):
		"""Ensure no active/pending delegation overlaps for the same user."""
		overlapping = frappe.db.sql(
			"""
			SELECT name FROM `tabDelegation`
			WHERE user = %s
				AND name != %s
				AND docstatus = 1
				AND status IN ('Pending', 'Active')
				AND start_date <= %s
				AND end_date >= %s
			""",
			(self.user, self.name or "", self.end_date, self.start_date),
			as_dict=True,
		)

		if overlapping:
			frappe.throw(
				_("An overlapping delegation {0} already exists for user {1}.").format(
					overlapping[0].name, self.user
				)
			)

	def on_submit(self):
		self.db_set("status", "Pending")

		# If start date is today, activate immediately
		if getdate(self.start_date) <= getdate(nowdate()):
			self.activate_delegation()

	def on_cancel(self):
		if self.status == "Active":
			self.deactivate_delegation()

		self.db_set("status", "Cancelled")

	def activate_delegation(self):
		"""Copy roles from user to delegate and store them for later restoration."""
		roles_to_assign = self._get_roles_to_delegate()

		if not roles_to_assign:
			frappe.throw(_("No roles found to delegate from user {0}.").format(self.user))

		# Get roles the delegate already has
		existing_delegate_roles = {
			r.role for r in frappe.get_all("Has Role", filters={"parent": self.delegate}, fields=["role"])
		}

		# Only add roles the delegate doesn't already have
		new_roles = [r for r in roles_to_assign if r not in existing_delegate_roles]

		if new_roles:
			delegate_user = frappe.get_doc("User", self.delegate)
			for role in new_roles:
				delegate_user.append("roles", {"role": role})
			delegate_user.save(ignore_permissions=True)

		# Store the roles we actually added (for clean restoration)
		self.db_set("assigned_roles", json.dumps(new_roles))
		self.db_set("status", "Active")
		self.db_set("activated_on", now_datetime())

		self._send_notification(
			to_user=self.delegate,
			subject=_("Delegation Activated: {0}").format(self.name),
			message=_(
				"You have been delegated roles from {0} ({1}).<br>"
				"Delegation period: {2} to {3}.<br>"
				"Roles delegated: {4}"
			).format(
				self.user_full_name or self.user,
				self.user,
				self.start_date,
				self.end_date,
				", ".join(new_roles) if new_roles else _("No new roles (already had all)"),
			),
		)

		# Also notify the delegator
		self._send_notification(
			to_user=self.user,
			subject=_("Delegation Activated: {0}").format(self.name),
			message=_(
				"Your roles have been delegated to {0} ({1}).<br>"
				"Delegation period: {2} to {3}."
			).format(
				self.delegate_full_name or self.delegate,
				self.delegate,
				self.start_date,
				self.end_date,
			),
		)

		frappe.msgprint(_("Delegation {0} activated successfully.").format(self.name), alert=True)

	def deactivate_delegation(self):
		"""Remove delegated roles from the delegate."""
		assigned_roles = self._get_assigned_roles()

		if assigned_roles:
			# Check which of these roles are not needed by other active delegations
			other_active_roles = self._get_roles_from_other_active_delegations()
			roles_to_remove = [r for r in assigned_roles if r not in other_active_roles]

			if roles_to_remove:
				delegate_user = frappe.get_doc("User", self.delegate)
				delegate_user.roles = [r for r in delegate_user.roles if r.role not in roles_to_remove]
				delegate_user.save(ignore_permissions=True)

		self.db_set("status", "Completed")
		self.db_set("deactivated_on", now_datetime())

		self._send_notification(
			to_user=self.delegate,
			subject=_("Delegation Completed: {0}").format(self.name),
			message=_(
				"The delegation of roles from {0} ({1}) has ended.<br>"
				"The delegated roles have been removed from your account."
			).format(self.user_full_name or self.user, self.user),
		)

		self._send_notification(
			to_user=self.user,
			subject=_("Delegation Completed: {0}").format(self.name),
			message=_(
				"Your delegation to {0} ({1}) has ended.<br>"
				"The delegated roles have been restored."
			).format(self.delegate_full_name or self.delegate, self.delegate),
		)

	def _get_roles_to_delegate(self):
		"""Get the list of roles to delegate based on delegation type."""
		system_roles = {"Administrator", "Guest", "All"}

		if self.delegation_type == "Specific Roles":
			return [
				r.role
				for r in self.roles_to_delegate
				if r.role not in system_roles
			]
		else:
			# All Roles - get all non-system roles from the user
			user_roles = frappe.get_all(
				"Has Role",
				filters={"parent": self.user, "role": ["not in", list(system_roles)]},
				fields=["role"],
			)
			return [r.role for r in user_roles]

	def _get_assigned_roles(self):
		"""Parse stored assigned roles JSON."""
		if self.assigned_roles:
			try:
				return json.loads(self.assigned_roles)
			except (json.JSONDecodeError, TypeError):
				return []
		return []

	def _get_roles_from_other_active_delegations(self):
		"""Get roles assigned by other active delegations to the same delegate."""
		other_delegations = frappe.get_all(
			"Delegation",
			filters={
				"delegate": self.delegate,
				"name": ["!=", self.name],
				"docstatus": 1,
				"status": "Active",
			},
			fields=["assigned_roles"],
		)

		roles = set()
		for d in other_delegations:
			if d.assigned_roles:
				try:
					roles.update(json.loads(d.assigned_roles))
				except (json.JSONDecodeError, TypeError):
					pass

		return roles

	def _send_notification(self, to_user, subject, message):
		"""Send a system notification to a user."""
		try:
			notification = frappe.new_doc("Notification Log")
			notification.for_user = to_user
			notification.from_user = frappe.session.user
			notification.subject = subject
			notification.type = "Alert"
			notification.email_content = message
			notification.document_type = "Delegation"
			notification.document_name = self.name
			notification.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				title=_("Delegation Notification Error"),
				message=frappe.get_traceback(),
			)


def check_and_manage_delegations():
	"""Scheduled task to activate/deactivate delegations daily.

	Runs daily at midnight:
	1. Activates delegations where start_date <= today and status is Pending
	2. Deactivates delegations where end_date < today and status is Active
	"""
	today = getdate(nowdate())

	# Activate pending delegations whose start date has arrived
	pending_delegations = frappe.get_all(
		"Delegation",
		filters={
			"docstatus": 1,
			"status": "Pending",
			"start_date": ["<=", today],
		},
		pluck="name",
	)

	for name in pending_delegations:
		try:
			doc = frappe.get_doc("Delegation", name)
			doc.activate_delegation()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				title=_("Delegation Activation Error: {0}").format(name),
				message=frappe.get_traceback(),
			)

	# Deactivate active delegations whose end date has passed
	expired_delegations = frappe.get_all(
		"Delegation",
		filters={
			"docstatus": 1,
			"status": "Active",
			"end_date": ["<", today],
		},
		pluck="name",
	)

	for name in expired_delegations:
		try:
			doc = frappe.get_doc("Delegation", name)
			doc.deactivate_delegation()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				title=_("Delegation Deactivation Error: {0}").format(name),
				message=frappe.get_traceback(),
			)


@frappe.whitelist()
def activate_delegation_manually(delegation_name):
	"""Allow HR Manager / System Manager to activate a delegation immediately."""
	frappe.has_permission("Delegation", ptype="submit", throw=True)

	doc = frappe.get_doc("Delegation", delegation_name)
	if doc.docstatus != 1 or doc.status != "Pending":
		frappe.throw(_("Only submitted delegations with Pending status can be activated."))

	doc.activate_delegation()
	frappe.db.commit()

	return {"status": "success"}


@frappe.whitelist()
def deactivate_delegation_manually(delegation_name):
	"""Allow HR Manager / System Manager to deactivate a delegation immediately."""
	frappe.has_permission("Delegation", ptype="cancel", throw=True)

	doc = frappe.get_doc("Delegation", delegation_name)
	if doc.docstatus != 1 or doc.status != "Active":
		frappe.throw(_("Only submitted delegations with Active status can be deactivated."))

	doc.deactivate_delegation()
	frappe.db.commit()

	return {"status": "success"}
