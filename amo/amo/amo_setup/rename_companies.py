"""Rename AMO companies to match official antonins.org names and add Arabic translations."""

import frappe
from amo.amo_setup.company_definitions import RENAME_MAP, ARABIC_NAMES


def execute():
	"""Main entry point: rename companies then create Arabic translations."""
	rename_companies()
	frappe.db.commit()
	create_arabic_translations()
	frappe.db.commit()
	fix_toronto_country()
	frappe.db.commit()
	print("Done. All companies renamed and Arabic translations created.")


def rename_companies():
	"""Rename existing Company docs from old names to new names."""
	renamed = 0
	skipped = 0
	for old_name, new_name in RENAME_MAP.items():
		if old_name == new_name:
			continue
		if not frappe.db.exists("Company", old_name):
			print(f"  SKIP (not found): {old_name}")
			skipped += 1
			continue
		if frappe.db.exists("Company", new_name):
			print(f"  SKIP (target exists): {new_name}")
			skipped += 1
			continue
		try:
			frappe.rename_doc("Company", old_name, new_name, force=True)
			frappe.db.commit()
			print(f"  OK: {old_name}  →  {new_name}")
			renamed += 1
		except Exception as e:
			print(f"  ERROR renaming '{old_name}': {e}")
			skipped += 1
	print(f"\nRenamed {renamed} companies, skipped {skipped}")


def fix_toronto_country():
	"""
	The Toronto monastery was previously under Switzerland (MON-CH).
	Update its country and currency after rename using direct SQL
	to avoid cost center validation issues.
	"""
	toronto = "Our Lady of Lebanon Monastery - Toronto"
	if frappe.db.exists("Company", toronto):
		current_country = frappe.db.get_value("Company", toronto, "country")
		if current_country != "Canada":
			frappe.db.sql("""
				UPDATE `tabCompany`
				SET country = 'Canada', default_currency = 'CAD'
				WHERE name = %s
			""", (toronto,))
			print(f"  Updated {toronto} country to Canada / CAD")


def create_arabic_translations():
	"""Create Translation entries for all company names (English → Arabic)."""
	created = 0
	for english_name, arabic_name in ARABIC_NAMES.items():
		if not arabic_name:
			continue
		# Check if translation already exists
		exists = frappe.db.exists("Translation", {
			"source_text": english_name,
			"language": "ar",
		})
		if exists:
			continue
		try:
			frappe.get_doc({
				"doctype": "Translation",
				"language": "ar",
				"source_text": english_name,
				"translated_text": arabic_name,
			}).insert(ignore_permissions=True)
			created += 1
		except Exception as e:
			print(f"  ERROR creating translation for '{english_name}': {e}")
	print(f"Created {created} Arabic translations")

	# Also add translations for group companies
	group_arabic = {
		"AMO": "الرهبانية الأنطونية المارونية",
		"AMO - Monasteries": "الرهبانية الأنطونية - الأديرة",
		"AMO - Schools": "الرهبانية الأنطونية - المدارس",
		"AMO - University": "الرهبانية الأنطونية - الجامعة",
		"AMO - Social and Cultural Organizations": "الرهبانية الأنطونية - المنظمات الاجتماعية والثقافية",
	}
	for en, ar in group_arabic.items():
		exists = frappe.db.exists("Translation", {
			"source_text": en,
			"language": "ar",
		})
		if not exists:
			try:
				frappe.get_doc({
					"doctype": "Translation",
					"language": "ar",
					"source_text": en,
					"translated_text": ar,
				}).insert(ignore_permissions=True)
			except Exception:
				pass
