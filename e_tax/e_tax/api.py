# Copyright (c) 2026, iPeng Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_dashboard_stats():
	"""Get dashboard statistics for e-Tax portal."""
	stats = {}

	# Taxpayer stats
	stats["total_taxpayers"] = frappe.db.count("Taxpayer", {"status": "Active"})
	stats["enterprise_taxpayers"] = frappe.db.count("Taxpayer", {"status": "Active", "taxpayer_type": "Enterprise"})
	stats["individual_taxpayers"] = frappe.db.count("Taxpayer", {"status": "Active", "taxpayer_type": "Individual"})

	# Enterprise Declarations
	stats["enterprise_declarations"] = frappe.db.count("Enterprise Declaration", {"docstatus": 1})
	stats["enterprise_declarations_pending"] = frappe.db.count("Enterprise Declaration", {"status": "Submitted"})
	stats["enterprise_declarations_approved"] = frappe.db.count("Enterprise Declaration", {"status": "Approved"})
	stats["total_income_tax"] = flt(
		frappe.db.sql("SELECT COALESCE(SUM(income_tax_amount), 0) FROM `tabEnterprise Declaration` WHERE docstatus=1")[0][0]
	)

	# VAT Returns
	stats["vat_returns"] = frappe.db.count("VAT Return", {"docstatus": 1})
	stats["vat_returns_pending"] = frappe.db.count("VAT Return", {"status": "Submitted"})
	stats["vat_approved"] = frappe.db.count("VAT Return", {"status": "Approved"})
	stats["total_vat_collected"] = flt(
		frappe.db.sql("SELECT COALESCE(SUM(vat_payable), 0) FROM `tabVAT Return` WHERE docstatus=1")[0][0]
	)

	# Personal Income Tax
	stats["personal_income_tax"] = frappe.db.count("Personal Income Tax", {"docstatus": 1})
	stats["pit_pending"] = frappe.db.count("Personal Income Tax", {"status": "Submitted"})
	stats["pit_approved"] = frappe.db.count("Personal Income Tax", {"status": "Approved"})
	stats["total_pit_collected"] = flt(
		frappe.db.sql("SELECT COALESCE(SUM(tax_payable), 0) FROM `tabPersonal Income Tax` WHERE docstatus=1")[0][0]
	)

	# Customs
	stats["customs_declarations"] = frappe.db.count("Customs Declaration", {"docstatus": 1})
	stats["customs_pending"] = frappe.db.count("Customs Declaration", {"status": "Submitted"})
	stats["customs_approved"] = frappe.db.count("Customs Declaration", {"status": "Approved"})
	stats["total_customs_duty"] = flt(
		frappe.db.sql("SELECT COALESCE(SUM(total_duties_and_taxes), 0) FROM `tabCustoms Declaration` WHERE docstatus=1")[0][0]
	)

	# Excise Duty
	stats["excise_returns"] = frappe.db.count("Excise Duty Return", {"docstatus": 1})
	stats["excise_pending"] = frappe.db.count("Excise Duty Return", {"status": "Submitted"})
	stats["excise_approved"] = frappe.db.count("Excise Duty Return", {"status": "Approved"})
	stats["total_excise_duty"] = flt(
		frappe.db.sql("SELECT COALESCE(SUM(total_excise_duty), 0) FROM `tabExcise Duty Return` WHERE docstatus=1")[0][0]
	)

	# Total Revenue
	stats["total_revenue"] = (
		flt(stats["total_income_tax"])
		+ flt(stats["total_vat_collected"])
		+ flt(stats["total_pit_collected"])
		+ flt(stats["total_customs_duty"])
		+ flt(stats["total_excise_duty"])
	)

	# Aggregate totals
	stats["total_filings"] = (
		stats["enterprise_declarations"]
		+ stats["vat_returns"]
		+ stats["personal_income_tax"]
		+ stats["customs_declarations"]
		+ stats["excise_returns"]
	)
	stats["total_pending"] = (
		stats["enterprise_declarations_pending"]
		+ stats["vat_returns_pending"]
		+ stats["pit_pending"]
		+ stats["customs_pending"]
		+ stats["excise_pending"]
	)
	stats["total_approved"] = (
		stats["enterprise_declarations_approved"]
		+ stats["vat_approved"]
		+ stats["pit_approved"]
		+ stats["customs_approved"]
		+ stats["excise_approved"]
	)

	# Tax Rates & Reference data
	stats["tax_types"] = frappe.db.count("Tax Type", {"is_active": 1})
	stats["tax_rates"] = frappe.db.count("Tax Rate")

	return stats


@frappe.whitelist()
def get_recent_filings(limit=15):
	"""Get recent filings across all declaration types."""
	filings = []

	for doctype, label in [
		("Enterprise Declaration", "Enterprise Declaration"),
		("VAT Return", "VAT Return"),
		("Personal Income Tax", "Personal Income Tax"),
		("Customs Declaration", "Customs Declaration"),
		("Excise Duty Return", "Excise Duty Return"),
	]:
		records = frappe.get_list(
			doctype,
			fields=["name", "taxpayer_name", "status", "creation", "filing_date"],
			order_by="creation desc",
			limit_page_length=limit,
		)
		for r in records:
			r["declaration_type"] = label
			filings.append(r)

	filings.sort(key=lambda x: x.get("creation"), reverse=True)
	return filings[:limit]


@frappe.whitelist()
def get_revenue_by_type():
	"""Get revenue breakdown by tax type for charts."""
	return {
		"labels": [
			"Income Tax",
			"VAT",
			"Personal Income Tax",
			"Customs Duty",
			"Excise Duty",
		],
		"datasets": [
			{
				"values": [
					flt(frappe.db.sql("SELECT COALESCE(SUM(income_tax_amount), 0) FROM `tabEnterprise Declaration` WHERE docstatus=1")[0][0]),
					flt(frappe.db.sql("SELECT COALESCE(SUM(vat_payable), 0) FROM `tabVAT Return` WHERE docstatus=1")[0][0]),
					flt(frappe.db.sql("SELECT COALESCE(SUM(tax_payable), 0) FROM `tabPersonal Income Tax` WHERE docstatus=1")[0][0]),
					flt(frappe.db.sql("SELECT COALESCE(SUM(total_duties_and_taxes), 0) FROM `tabCustoms Declaration` WHERE docstatus=1")[0][0]),
					flt(frappe.db.sql("SELECT COALESCE(SUM(total_excise_duty), 0) FROM `tabExcise Duty Return` WHERE docstatus=1")[0][0]),
				]
			}
		],
	}


@frappe.whitelist()
def get_monthly_filings():
	"""Get monthly filing trends for the current year."""
	import datetime

	current_year = datetime.date.today().year
	months = []
	enterprise_counts = []
	vat_counts = []
	pit_counts = []
	customs_counts = []
	excise_counts = []

	for month in range(1, 13):
		months.append(datetime.date(current_year, month, 1).strftime("%b"))

		for dt, counts_list in [
			("Enterprise Declaration", enterprise_counts),
			("VAT Return", vat_counts),
			("Personal Income Tax", pit_counts),
			("Customs Declaration", customs_counts),
			("Excise Duty Return", excise_counts),
		]:
			count = frappe.db.count(dt, {
				"filing_date": ["between", [
					f"{current_year}-{month:02d}-01",
					f"{current_year}-{month:02d}-31"
				]],
				"docstatus": 1
			})
			counts_list.append(count)

	return {
		"labels": months,
		"datasets": [
			{"name": "Enterprise", "values": enterprise_counts},
			{"name": "VAT", "values": vat_counts},
			{"name": "Personal IT", "values": pit_counts},
			{"name": "Customs", "values": customs_counts},
			{"name": "Excise", "values": excise_counts},
		],
	}


@frappe.whitelist()
def approve_filing(doctype, name):
	"""Approve a tax filing."""
	doc = frappe.get_doc(doctype, name)
	if doc.status not in ("Submitted", "Under Review"):
		frappe.throw(f"Cannot approve a filing with status: {doc.status}")

	doc.db_set("status", "Approved")
	doc.db_set("approved_by", frappe.session.user)
	frappe.msgprint(f"{doctype} {name} has been approved.", indicator="green", alert=True)
	return {"status": "Approved"}


@frappe.whitelist()
def reject_filing(doctype, name, reason=""):
	"""Reject a tax filing."""
	doc = frappe.get_doc(doctype, name)
	if doc.status not in ("Submitted", "Under Review"):
		frappe.throw(f"Cannot reject a filing with status: {doc.status}")

	doc.db_set("status", "Rejected")
	if reason:
		doc.db_set("remarks", reason)
	frappe.msgprint(f"{doctype} {name} has been rejected.", indicator="red", alert=True)
	return {"status": "Rejected"}


@frappe.whitelist()
def create_demo_data():
	"""Create demo data (users, taxpayers, declarations). Admin only."""
	if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
		frappe.throw("Only administrators can create demo data.", frappe.PermissionError)

	from e_tax.demo import load_demo_data
	load_demo_data()
	return {"message": "Demo data created successfully"}


@frappe.whitelist()
def clear_demo_data():
	"""Clear all demo data. Admin only."""
	if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
		frappe.throw("Only administrators can clear demo data.", frappe.PermissionError)

	from e_tax.demo import clear_demo_data as _clear
	_clear()
	return {"message": "Demo data cleared successfully"}


@frappe.whitelist()
def get_demo_data_status():
	"""Check whether demo data exists."""
	has_demo_users = any(
		frappe.db.exists("User", email)
		for email in ["company@etax.demo", "person@etax.demo", "agent@etax.demo"]
	)
	demo_taxpayers = frappe.db.count("Taxpayer", {
		"tax_identification_number": ["in", ["TIN-ENT-001", "TIN-ENT-002", "TIN-ENT-003", "TIN-IND-001", "TIN-IND-002"]]
	})
	return {
		"has_demo_data": has_demo_users or demo_taxpayers > 0,
		"demo_users": has_demo_users,
		"demo_taxpayers": demo_taxpayers,
	}
