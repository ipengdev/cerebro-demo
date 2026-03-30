import frappe
from frappe import _
from frappe.utils import nowdate, getdate, get_first_day, get_last_day, add_months


def check_app_permission():
	"""Check if the current user has permission to access the ESS portal."""
	if frappe.session.user == "Guest":
		return False
	# Any logged-in user linked to an employee can access
	return bool(get_current_employee())


def get_current_employee():
	"""Get the Employee record linked to the current user."""
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		"name",
	)
	if not employee:
		# Also check by company_email or personal_email
		employee = frappe.db.get_value(
			"Employee",
			{
				"status": "Active",
				"company_email": frappe.session.user,
			},
			"name",
		)
	if not employee:
		employee = frappe.db.get_value(
			"Employee",
			{
				"status": "Active",
				"personal_email": frappe.session.user,
			},
			"name",
		)
	return employee


@frappe.whitelist()
def get_employee_details():
	"""Get current employee details."""
	employee_id = get_current_employee()
	if not employee_id:
		frappe.throw(_("No employee record found for your user account"), frappe.DoesNotExistError)

	employee = frappe.get_doc("Employee", employee_id)
	return {
		"name": employee.name,
		"employee_name": employee.employee_name,
		"company": employee.company,
		"department": employee.department,
		"designation": employee.designation,
		"date_of_joining": employee.date_of_joining,
		"date_of_birth": employee.date_of_birth,
		"gender": employee.gender,
		"status": employee.status,
		"personal_email": employee.personal_email,
		"company_email": employee.company_email,
		"cell_phone": employee.cell_phone,
		"emergency_phone_number": employee.emergency_phone_number,
		"reports_to": employee.reports_to,
		"reports_to_name": frappe.db.get_value("Employee", employee.reports_to, "employee_name") if employee.reports_to else None,
		"image": employee.image,
		"holiday_list": employee.holiday_list,
	}


@frappe.whitelist()
def get_leave_balance():
	"""Get leave balance for the current employee."""
	employee_id = get_current_employee()
	if not employee_id:
		frappe.throw(_("No employee record found"), frappe.DoesNotExistError)

	try:
		from hrms.hr.doctype.leave_application.leave_application import get_leave_details
	except ImportError:
		frappe.throw(_("HRMS app is required for leave balance. Please install frappe/hrms."))

	year = getdate(nowdate()).year
	date = nowdate()

	leave_details = get_leave_details(employee_id, date)
	leave_allocation = leave_details.get("leave_allocation", {})

	result = []
	for leave_type, data in leave_allocation.items():
		result.append({
			"leave_type": leave_type,
			"total_leaves_allocated": data.get("total_leaves", 0),
			"leaves_taken": data.get("leaves_taken", 0),
			"remaining_leaves": data.get("remaining_leaves", 0),
		})

	return result


@frappe.whitelist()
def get_leave_applications():
	"""Get all leave applications for the current employee."""
	employee_id = get_current_employee()
	if not employee_id:
		frappe.throw(_("No employee record found"), frappe.DoesNotExistError)

	leaves = frappe.get_all(
		"Leave Application",
		filters={"employee": employee_id},
		fields=[
			"name", "leave_type", "from_date", "to_date",
			"total_leave_days", "status", "description", "posting_date"
		],
		order_by="posting_date desc",
		limit_page_length=50,
	)

	return leaves


@frappe.whitelist()
def get_recent_leaves():
	"""Get recent leave applications (last 5)."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	return frappe.get_all(
		"Leave Application",
		filters={"employee": employee_id},
		fields=["name", "leave_type", "from_date", "to_date", "status"],
		order_by="posting_date desc",
		limit_page_length=5,
	)


@frappe.whitelist()
def get_leave_types():
	"""Get available leave types."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	# Get leave types that have allocation for this employee
	allocations = frappe.get_all(
		"Leave Allocation",
		filters={
			"employee": employee_id,
			"docstatus": 1,
			"from_date": ("<=", nowdate()),
			"to_date": (">=", nowdate()),
		},
		fields=["leave_type"],
		distinct=True,
	)

	leave_types = [{"name": a.leave_type} for a in allocations]

	# If no allocations, return all active leave types
	if not leave_types:
		leave_types = frappe.get_all(
			"Leave Type",
			filters={"is_active": 1},
			fields=["name"],
		)

	return leave_types


@frappe.whitelist()
def apply_leave(leave_type, from_date, to_date, half_day=0, reason=None):
	"""Submit a leave application."""
	employee_id = get_current_employee()
	if not employee_id:
		frappe.throw(_("No employee record found"), frappe.DoesNotExistError)

	leave_app = frappe.get_doc({
		"doctype": "Leave Application",
		"employee": employee_id,
		"leave_type": leave_type,
		"from_date": from_date,
		"to_date": to_date,
		"half_day": int(half_day),
		"description": reason,
		"status": "Open",
		"leave_approver": frappe.db.get_value("Employee", employee_id, "leave_approver"),
	})

	leave_app.insert()
	leave_app.submit()
	frappe.db.commit()

	return {"name": leave_app.name, "status": leave_app.status}


@frappe.whitelist()
def get_attendance(year=None, month=None):
	"""Get attendance records for a specific month."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	if not year or not month:
		today = getdate(nowdate())
		year = today.year
		month = today.month

	year = int(year)
	month = int(month)

	from_date = get_first_day(f"{year}-{month:02d}-01")
	to_date = get_last_day(f"{year}-{month:02d}-01")

	return frappe.get_all(
		"Attendance",
		filters={
			"employee": employee_id,
			"attendance_date": ("between", [from_date, to_date]),
			"docstatus": 1,
		},
		fields=["name", "attendance_date", "status", "working_hours"],
		order_by="attendance_date asc",
	)


@frappe.whitelist()
def get_payslips():
	"""Get salary slips for the current employee."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	slips = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": employee_id,
			"docstatus": 1,
		},
		fields=[
			"name", "start_date", "end_date", "gross_pay",
			"total_deduction", "net_pay", "posting_date"
		],
		order_by="start_date desc",
		limit_page_length=24,
	)

	# Add earnings and deductions detail for each slip
	for slip in slips:
		slip["earnings"] = frappe.get_all(
			"Salary Detail",
			filters={"parent": slip.name, "parentfield": "earnings"},
			fields=["salary_component", "amount"],
		)
		slip["deductions"] = frappe.get_all(
			"Salary Detail",
			filters={"parent": slip.name, "parentfield": "deductions"},
			fields=["salary_component", "amount"],
		)

	return slips


@frappe.whitelist()
def get_holidays():
	"""Get holidays for the current year from the employee's holiday list."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	holiday_list = frappe.db.get_value("Employee", employee_id, "holiday_list")

	if not holiday_list:
		# Fallback to company default
		company = frappe.db.get_value("Employee", employee_id, "company")
		holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")

	if not holiday_list:
		return []

	holidays = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list},
		fields=["name", "holiday_date", "description", "weekly_off"],
		order_by="holiday_date asc",
	)

	# Filter to current year
	current_year = getdate(nowdate()).year
	holidays = [h for h in holidays if getdate(h.holiday_date).year == current_year]

	return holidays


@frappe.whitelist()
def get_upcoming_holidays():
	"""Get upcoming holidays (next 5)."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	holiday_list = frappe.db.get_value("Employee", employee_id, "holiday_list")

	if not holiday_list:
		company = frappe.db.get_value("Employee", employee_id, "company")
		holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")

	if not holiday_list:
		return []

	return frappe.get_all(
		"Holiday",
		filters={
			"parent": holiday_list,
			"holiday_date": (">=", nowdate()),
		},
		fields=["name", "holiday_date", "description"],
		order_by="holiday_date asc",
		limit_page_length=5,
	)


@frappe.whitelist()
def get_certificate_requests():
	"""Get certificate requests by the employee (uses ToDo as a workaround)."""
	employee_id = get_current_employee()
	if not employee_id:
		return []

	# Use ToDo doctype as certificate request tracker
	return frappe.get_all(
		"ToDo",
		filters={
			"allocated_to": frappe.session.user,
			"reference_type": "Employee",
			"reference_name": employee_id,
			"description": ("like", "%[Certificate Request]%"),
		},
		fields=["name", "description", "status", "date", "creation"],
		order_by="creation desc",
	)


@frappe.whitelist()
def request_certificate(certificate_type, purpose=None):
	"""Create a certificate request (stored as a ToDo)."""
	employee_id = get_current_employee()
	if not employee_id:
		frappe.throw(_("No employee record found"), frappe.DoesNotExistError)

	employee_name = frappe.db.get_value("Employee", employee_id, "employee_name")

	# Get HR Manager / reports to
	hr_users = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager"},
		fields=["parent"],
		limit_page_length=1,
	)
	assigned_to = hr_users[0].parent if hr_users else frappe.session.user

	todo = frappe.get_doc({
		"doctype": "ToDo",
		"allocated_to": frappe.session.user,
		"assigned_by": frappe.session.user,
		"reference_type": "Employee",
		"reference_name": employee_id,
		"description": f"[Certificate Request] {certificate_type} - {employee_name} ({employee_id}). Purpose: {purpose or 'N/A'}",
		"status": "Open",
		"priority": "Medium",
	})
	todo.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name": todo.name,
		"status": "Open",
		"certificate_type": certificate_type,
	}


@frappe.whitelist()
def get_user_theme():
	theme = frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
	return theme.lower()
