import frappe


def verify():
	"""Print entire cost center tree hierarchy."""
	rows = frappe.db.sql("""
		SELECT name, parent_cost_center, is_group, company
		FROM `tabCost Center`
		ORDER BY lft
	""", as_dict=True)

	# Build parent lookup
	children_map = {}
	roots = []
	for r in rows:
		p = r["parent_cost_center"] or ""
		children_map.setdefault(p, []).append(r)
		if not p:
			roots.append(r)

	def print_tree(node, depth=0):
		g = " [G]" if node["is_group"] else ""
		indent = "  " * depth + ("|- " if depth else "")
		print(f"{indent}{node['name']}{g}")
		for child in children_map.get(node["name"], []):
			print_tree(child, depth + 1)

	for root in roots:
		print_tree(root)

	# Summary
	total = len(rows)
	groups = sum(1 for r in rows if r["is_group"])
	leaves = total - groups
	print(f"\nTotal: {total} cost centers ({groups} groups, {leaves} leaves)")


def test_fix():
	"""Test direct SQL update of parent_cost_center."""
	name = "Antonine School - Ain Traz - SCH05"
	parent = "AMO - Schools - AMO-SCH"
	print(f"Before: {frappe.db.get_value('Cost Center', name, 'parent_cost_center')}")
	frappe.db.sql(
		"UPDATE `tabCost Center` SET parent_cost_center = %s WHERE name = %s",
		(parent, name),
	)
	frappe.db.commit()
	print(f"After:  {frappe.db.get_value('Cost Center', name, 'parent_cost_center')}")
	# Check how many rows matched
	affected = frappe.db.sql(
		"SELECT COUNT(*) FROM `tabCost Center` WHERE name = %s",
		(name,),
	)[0][0]
	print(f"Rows matched: {affected}")
	exists = frappe.db.exists("Cost Center", name)
	print(f"Exists: {exists}")
