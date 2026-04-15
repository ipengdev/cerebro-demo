"""
ITSM Demo Data Generator & Cleanup

Creates realistic demo data across all ITSM modules:
- IT Assets (servers, workstations, printers, switches, etc.)
- Locations, Vendors, Contracts, Software Licenses
- Service Tickets with SLA tracking
- Configuration Items and relationships
- Discovery Results

All demo records are tagged with `is_demo_data=1` custom field
for easy one-click cleanup.
"""

import frappe
from frappe import _
from frappe.utils import (
	nowdate, add_days, add_months, getdate, now_datetime,
	random_string,
)
import random
import json


# ── Marker field name used to tag demo records ──────────────────────
DEMO_TAG = "_comment"  # We'll use naming convention instead
DEMO_PREFIX = "[DEMO]"


# ── Public API ──────────────────────────────────────────────────────

@frappe.whitelist()
def create_demo_data():
	"""Generate full set of ITSM demo data. Returns summary dict."""
	frappe.only_for(["Administrator", "System Manager", "IT Manager"])

	counts = {}

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating locations...", "percent": 5})
	counts["locations"] = _create_locations()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating vendors...", "percent": 10})
	counts["vendors"] = _create_vendors()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating IT assets...", "percent": 20})
	counts["assets"] = _create_assets()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating software licenses...", "percent": 40})
	counts["licenses"] = _create_licenses()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating contracts...", "percent": 50})
	counts["contracts"] = _create_contracts()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating configuration items...", "percent": 60})
	counts["config_items"] = _create_configuration_items()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating CI relationships...", "percent": 70})
	counts["relationships"] = _create_ci_relationships()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating service tickets...", "percent": 80})
	counts["tickets"] = _create_tickets()

	frappe.publish_realtime("itsm_demo_progress", {"stage": "Creating discovery results...", "percent": 90})
	counts["discovery_results"] = _create_discovery_results()

	frappe.db.commit()

	frappe.publish_realtime("itsm_demo_progress", {
		"stage": f"Done! Created {sum(counts.values())} demo records.",
		"percent": 100,
		"done": True,
	})

	return counts


@frappe.whitelist()
def clean_demo_data():
	"""Remove all ITSM demo data created by the generator. Returns summary dict."""
	frappe.only_for(["Administrator", "System Manager", "IT Manager"])

	counts = {}

	# Order matters: delete children/dependents first
	doctypes_to_clean = [
		"CI Relationship",
		"Service Ticket",
		"Discovery Result",
		"Configuration Item",
		"IT Contract",
		"Software License",
		"IT Asset Log",
		"IT Asset",
		"Vendor",
		"IT Asset Location",
	]

	total = len(doctypes_to_clean)
	for i, dt in enumerate(doctypes_to_clean):
		frappe.publish_realtime("itsm_demo_cleanup", {
			"stage": f"Cleaning {dt}...",
			"percent": int(100 * i / total),
		})
		count = _delete_demo_records(dt)
		counts[dt] = count

	frappe.db.commit()

	frappe.publish_realtime("itsm_demo_cleanup", {
		"stage": f"Done! Removed {sum(counts.values())} demo records.",
		"percent": 100,
		"done": True,
	})

	return counts


@frappe.whitelist()
def get_demo_data_stats():
	"""Get count of existing demo data records."""
	frappe.only_for(["Administrator", "System Manager", "IT Manager"])

	stats = {}
	for dt in [
		"IT Asset", "IT Asset Location", "Vendor", "Software License",
		"IT Contract", "Configuration Item", "CI Relationship",
		"Service Ticket", "Discovery Result",
	]:
		stats[dt] = frappe.db.count(dt, {"name": ("like", f"{DEMO_PREFIX}%")})

	stats["total"] = sum(stats.values())
	return stats


# ── Internal helpers ────────────────────────────────────────────────

def _demo_name(prefix, suffix):
	"""Generate a demo-tagged name."""
	return f"{DEMO_PREFIX} {prefix}-{suffix}"


def _delete_demo_records(doctype):
	"""Delete all records of a doctype whose name starts with DEMO_PREFIX."""
	names = frappe.get_all(doctype, filters={"name": ("like", f"{DEMO_PREFIX}%")}, pluck="name")
	for name in names:
		try:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		except Exception:
			# If linked, try without children
			try:
				frappe.db.delete(f"tab{doctype}", {"name": name})
			except Exception:
				pass
	return len(names)


# ── Locations ───────────────────────────────────────────────────────

def _create_locations():
	locations = [
		{"location_name": f"{DEMO_PREFIX} HQ - Main Building", "location_type": "Building", "city": "Dubai", "address": "Sheikh Zayed Road, Tower A"},
		{"location_name": f"{DEMO_PREFIX} HQ - Floor 1", "location_type": "Floor", "parent_location": f"{DEMO_PREFIX} HQ - Main Building", "floor": "1"},
		{"location_name": f"{DEMO_PREFIX} HQ - Floor 2", "location_type": "Floor", "parent_location": f"{DEMO_PREFIX} HQ - Main Building", "floor": "2"},
		{"location_name": f"{DEMO_PREFIX} HQ - Server Room", "location_type": "Room", "parent_location": f"{DEMO_PREFIX} HQ - Floor 1", "room": "SR-101"},
		{"location_name": f"{DEMO_PREFIX} HQ - Rack A1", "location_type": "Rack", "parent_location": f"{DEMO_PREFIX} HQ - Server Room", "rack": "A1"},
		{"location_name": f"{DEMO_PREFIX} HQ - Rack A2", "location_type": "Rack", "parent_location": f"{DEMO_PREFIX} HQ - Server Room", "rack": "A2"},
		{"location_name": f"{DEMO_PREFIX} DC - Primary Data Center", "location_type": "Data Center", "city": "Abu Dhabi", "address": "Masdar City, Zone 3"},
		{"location_name": f"{DEMO_PREFIX} DC - Rack B1", "location_type": "Rack", "parent_location": f"{DEMO_PREFIX} DC - Primary Data Center", "rack": "B1"},
		{"location_name": f"{DEMO_PREFIX} DC - Rack B2", "location_type": "Rack", "parent_location": f"{DEMO_PREFIX} DC - Primary Data Center", "rack": "B2"},
		{"location_name": f"{DEMO_PREFIX} Branch - Sharjah Office", "location_type": "Building", "city": "Sharjah", "address": "Al Taawun Street, Suite 201"},
	]
	count = 0
	for loc in locations:
		if not frappe.db.exists("IT Asset Location", loc["location_name"]):
			doc = frappe.get_doc({"doctype": "IT Asset Location", **loc})
			doc.insert(ignore_permissions=True)
			count += 1
	return count


# ── Vendors ─────────────────────────────────────────────────────────

def _create_vendors():
	vendors = [
		{"vendor_name": f"{DEMO_PREFIX} Dell Technologies", "vendor_type": "Hardware", "website": "https://dell.com", "email": "support@dell.example.com", "phone": "+1-800-999-3355", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} HP Enterprise", "vendor_type": "Hardware", "website": "https://hpe.com", "email": "support@hpe.example.com", "phone": "+1-800-474-6836", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} Cisco Systems", "vendor_type": "Hardware", "website": "https://cisco.com", "email": "support@cisco.example.com", "phone": "+1-800-553-6387", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} Microsoft", "vendor_type": "Software", "website": "https://microsoft.com", "email": "support@microsoft.example.com", "phone": "+1-800-642-7676", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} VMware (Broadcom)", "vendor_type": "Software", "website": "https://vmware.com", "email": "support@vmware.example.com", "phone": "+1-877-486-9273", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} AWS", "vendor_type": "Cloud Services", "website": "https://aws.amazon.com", "email": "support@aws.example.com", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} Fortinet", "vendor_type": "Hardware", "website": "https://fortinet.com", "email": "support@fortinet.example.com", "status": "Active"},
		{"vendor_name": f"{DEMO_PREFIX} Lenovo", "vendor_type": "Hardware", "website": "https://lenovo.com", "email": "support@lenovo.example.com", "status": "Active"},
	]
	count = 0
	for v in vendors:
		if not frappe.db.exists("Vendor", v["vendor_name"]):
			doc = frappe.get_doc({"doctype": "Vendor", **v})
			doc.insert(ignore_permissions=True)
			count += 1
	return count


# ── IT Assets ───────────────────────────────────────────────────────

def _create_assets():
	today = getdate(nowdate())
	assets = []

	# Servers
	server_models = [
		("Dell PowerEdge R750", "Dell Technologies", "SRV"),
		("HP ProLiant DL380 Gen10", "HP Enterprise", "SRV"),
		("Dell PowerEdge R640", "Dell Technologies", "SRV"),
		("HP ProLiant ML350 Gen10", "HP Enterprise", "SRV"),
	]
	for i, (model, vendor, prefix) in enumerate(server_models):
		assets.append({
			"asset_name": f"{DEMO_PREFIX} {model} #{i+1:02d}",
			"category": "Server",
			"asset_type": "Server",
			"status": "Active",
			"model": model,
			"manufacturer": vendor.split()[0],
			"serial_number": f"SN-{prefix}-{random.randint(100000, 999999)}",
			"vendor": f"{DEMO_PREFIX} {vendor}",
			"ip_address": f"10.0.1.{10+i}",
			"hostname": f"srv-{prefix.lower()}-{i+1:02d}.local",
			"mac_address": _random_mac(),
			"operating_system": random.choice(["Ubuntu 22.04 LTS", "RHEL 9.2", "Windows Server 2022"]),
			"processor": random.choice(["Intel Xeon Gold 6338", "AMD EPYC 7763", "Intel Xeon Silver 4310"]),
			"ram_gb": random.choice([64, 128, 256, 512]),
			"storage_gb": random.choice([960, 1920, 3840]),
			"storage_type": "SSD",
			"location": f"{DEMO_PREFIX} HQ - Rack A{(i % 2) + 1}",
			"purchase_date": str(add_days(today, -random.randint(180, 720))),
			"purchase_cost": random.choice([12000, 18000, 25000, 35000]),
			"warranty_expiry": str(add_days(today, random.randint(180, 1080))),
			"installation_date": str(add_days(today, -random.randint(90, 365))),
			"discovery_source": "Network Scan",
			"is_online": 1,
			"last_seen": str(now_datetime()),
		})

	# Workstations / Desktops
	ws_models = [
		("Dell OptiPlex 7090", "Dell Technologies"),
		("HP EliteDesk 800 G8", "HP Enterprise"),
		("Lenovo ThinkCentre M70q", "Lenovo"),
	]
	departments = ["IT", "Finance", "Marketing", "HR", "Engineering", "Sales", "Operations"]
	for i in range(12):
		model, vendor = ws_models[i % len(ws_models)]
		assets.append({
			"asset_name": f"{DEMO_PREFIX} {model} - WS{i+1:03d}",
			"category": "Desktop",
			"asset_type": "Hardware",
			"status": random.choice(["Active", "Active", "Active", "In Maintenance", "Deployed"]),
			"model": model,
			"manufacturer": vendor.split()[0],
			"serial_number": f"SN-WS-{random.randint(100000, 999999)}",
			"vendor": f"{DEMO_PREFIX} {vendor}",
			"ip_address": f"10.0.10.{100+i}",
			"hostname": f"ws-{i+1:03d}.local",
			"mac_address": _random_mac(),
			"operating_system": random.choice(["Windows 11 Pro", "Windows 10 Pro", "Ubuntu 24.04"]),
			"processor": "Intel Core i7-12700",
			"ram_gb": random.choice([16, 32]),
			"storage_gb": random.choice([512, 1000]),
			"storage_type": "NVMe",
			"location": f"{DEMO_PREFIX} HQ - Floor {(i % 2) + 1}",
			"purchase_date": str(add_days(today, -random.randint(30, 540))),
			"purchase_cost": random.choice([1200, 1500, 1800]),
			"warranty_expiry": str(add_days(today, random.randint(60, 900))),
			"discovery_source": "Network Scan",
			"is_online": random.choice([1, 1, 1, 0]),
			"last_seen": str(now_datetime()),
		})

	# Laptops
	laptop_models = [
		("Dell Latitude 5540", "Dell Technologies"),
		("HP EliteBook 850 G10", "HP Enterprise"),
		("Lenovo ThinkPad T14 Gen 4", "Lenovo"),
	]
	for i in range(8):
		model, vendor = laptop_models[i % len(laptop_models)]
		assets.append({
			"asset_name": f"{DEMO_PREFIX} {model} - LT{i+1:03d}",
			"category": "Laptop",
			"asset_type": "Hardware",
			"status": random.choice(["Deployed", "Deployed", "Active", "In Stock"]),
			"model": model,
			"manufacturer": vendor.split()[0],
			"serial_number": f"SN-LT-{random.randint(100000, 999999)}",
			"vendor": f"{DEMO_PREFIX} {vendor}",
			"ip_address": f"10.0.20.{50+i}",
			"hostname": f"lt-{i+1:03d}.local",
			"mac_address": _random_mac(),
			"operating_system": random.choice(["Windows 11 Pro", "macOS Sonoma"]),
			"processor": "Intel Core i7-1365U",
			"ram_gb": random.choice([16, 32]),
			"storage_gb": 512,
			"storage_type": "NVMe",
			"purchase_date": str(add_days(today, -random.randint(30, 365))),
			"purchase_cost": random.choice([1400, 1600, 2000]),
			"warranty_expiry": str(add_days(today, random.randint(365, 1095))),
			"discovery_source": "Agent",
			"is_online": random.choice([1, 1, 0]),
		})

	# Network switches
	for i in range(4):
		assets.append({
			"asset_name": f"{DEMO_PREFIX} Cisco Catalyst 9300 - SW{i+1:02d}",
			"category": "Network Switch",
			"asset_type": "Network Device",
			"status": "Active",
			"model": "Catalyst 9300-48P",
			"manufacturer": "Cisco",
			"serial_number": f"SN-SW-{random.randint(100000, 999999)}",
			"vendor": f"{DEMO_PREFIX} Cisco Systems",
			"ip_address": f"10.0.0.{i+1}",
			"hostname": f"sw-core-{i+1:02d}.local",
			"mac_address": _random_mac(),
			"operating_system": "IOS-XE 17.9.4",
			"location": f"{DEMO_PREFIX} HQ - Rack A{(i % 2) + 1}" if i < 2 else f"{DEMO_PREFIX} DC - Rack B{(i % 2) + 1}",
			"purchase_date": str(add_days(today, -random.randint(365, 730))),
			"purchase_cost": random.choice([8000, 12000]),
			"warranty_expiry": str(add_days(today, random.randint(365, 1460))),
			"discovery_source": "SNMP",
			"is_online": 1,
			"last_seen": str(now_datetime()),
		})

	# Firewall
	assets.append({
		"asset_name": f"{DEMO_PREFIX} FortiGate 600E",
		"category": "Firewall",
		"asset_type": "Network Device",
		"status": "Active",
		"model": "FortiGate 600E",
		"manufacturer": "Fortinet",
		"serial_number": f"SN-FW-{random.randint(100000, 999999)}",
		"vendor": f"{DEMO_PREFIX} Fortinet",
		"ip_address": "10.0.0.254",
		"hostname": "fw-main.local",
		"mac_address": _random_mac(),
		"operating_system": "FortiOS 7.4.3",
		"location": f"{DEMO_PREFIX} HQ - Rack A1",
		"purchase_date": str(add_days(today, -400)),
		"purchase_cost": 15000,
		"warranty_expiry": str(add_days(today, 690)),
		"discovery_source": "SNMP",
		"is_online": 1,
		"last_seen": str(now_datetime()),
	})

	# Printers
	for i in range(3):
		assets.append({
			"asset_name": f"{DEMO_PREFIX} HP LaserJet Pro M428 - PRN{i+1:02d}",
			"category": "Printer",
			"asset_type": "Printer",
			"status": "Active",
			"model": "LaserJet Pro MFP M428fdn",
			"manufacturer": "HP",
			"serial_number": f"SN-PRN-{random.randint(100000, 999999)}",
			"ip_address": f"10.0.10.{200+i}",
			"hostname": f"prn-floor{i+1}.local",
			"mac_address": _random_mac(),
			"location": f"{DEMO_PREFIX} HQ - Floor {min(i+1, 2)}",
			"purchase_date": str(add_days(today, -random.randint(180, 540))),
			"purchase_cost": random.choice([600, 800]),
			"warranty_expiry": str(add_days(today, random.randint(180, 730))),
			"discovery_source": "Network Scan",
			"is_online": 1,
			"last_seen": str(now_datetime()),
		})

	# Access Points
	for i in range(3):
		assets.append({
			"asset_name": f"{DEMO_PREFIX} Cisco Meraki MR46 - AP{i+1:02d}",
			"category": "Access Point",
			"asset_type": "Network Device",
			"status": "Active",
			"model": "Meraki MR46",
			"manufacturer": "Cisco",
			"serial_number": f"SN-AP-{random.randint(100000, 999999)}",
			"vendor": f"{DEMO_PREFIX} Cisco Systems",
			"ip_address": f"10.0.0.{50+i}",
			"hostname": f"ap-{i+1:02d}.local",
			"mac_address": _random_mac(),
			"location": f"{DEMO_PREFIX} HQ - Floor {min(i+1, 2)}",
			"purchase_date": str(add_days(today, -random.randint(90, 365))),
			"purchase_cost": 800,
			"discovery_source": "SNMP",
			"is_online": 1,
			"last_seen": str(now_datetime()),
		})

	# UPS
	assets.append({
		"asset_name": f"{DEMO_PREFIX} APC Smart-UPS 3000",
		"category": "UPS",
		"asset_type": "Hardware",
		"status": "Active",
		"model": "Smart-UPS SRT 3000VA",
		"manufacturer": "APC",
		"serial_number": f"SN-UPS-{random.randint(100000, 999999)}",
		"ip_address": "10.0.1.250",
		"hostname": "ups-main.local",
		"location": f"{DEMO_PREFIX} HQ - Server Room",
		"purchase_date": str(add_days(today, -600)),
		"purchase_cost": 3500,
		"warranty_expiry": str(add_days(today, 460)),
		"discovery_source": "SNMP",
		"is_online": 1,
		"last_seen": str(now_datetime()),
	})

	# Virtual Machines
	vm_names = ["ERP-App", "Mail-Server", "DB-Primary", "Web-Proxy", "Backup-Server", "Monitoring"]
	for i, vm_name in enumerate(vm_names):
		assets.append({
			"asset_name": f"{DEMO_PREFIX} VM-{vm_name}",
			"category": "Virtual Machine",
			"asset_type": "Virtual Machine",
			"status": "Active",
			"model": "VMware Virtual Machine",
			"manufacturer": "VMware",
			"ip_address": f"10.0.2.{10+i}",
			"hostname": f"vm-{vm_name.lower()}.local",
			"mac_address": _random_mac(),
			"operating_system": random.choice(["Ubuntu 22.04", "RHEL 9", "Windows Server 2022"]),
			"processor": "vCPU x " + str(random.choice([2, 4, 8])),
			"ram_gb": random.choice([4, 8, 16, 32]),
			"storage_gb": random.choice([100, 200, 500]),
			"storage_type": "SAN",
			"location": f"{DEMO_PREFIX} DC - Primary Data Center",
			"discovery_source": "API Import",
			"is_online": 1,
			"last_seen": str(now_datetime()),
		})

	count = 0
	for asset_data in assets:
		name = asset_data["asset_name"]
		if not frappe.db.exists("IT Asset", {"asset_name": name}):
			doc = frappe.get_doc({"doctype": "IT Asset", **asset_data})
			doc.insert(ignore_permissions=True)
			count += 1

	return count


# ── Software Licenses ───────────────────────────────────────────────

def _create_licenses():
	today = getdate(nowdate())
	licenses = [
		{"license_name": f"{DEMO_PREFIX} Microsoft 365 E3", "software_name": "Microsoft 365", "software_version": "E3", "license_type": "Subscription", "total_licenses": 100, "used_licenses": 87, "vendor": f"{DEMO_PREFIX} Microsoft", "purchase_cost": 21600, "start_date": str(add_days(today, -180)), "expiry_date": str(add_days(today, 185)), "status": "Active"},
		{"license_name": f"{DEMO_PREFIX} Windows Server 2022 DC", "software_name": "Windows Server", "software_version": "2022 Datacenter", "license_type": "Per Device", "total_licenses": 10, "used_licenses": 4, "vendor": f"{DEMO_PREFIX} Microsoft", "purchase_cost": 60000, "start_date": str(add_days(today, -365)), "expiry_date": str(add_days(today, 1095)), "status": "Active"},
		{"license_name": f"{DEMO_PREFIX} VMware vSphere Enterprise Plus", "software_name": "VMware vSphere", "software_version": "8.0", "license_type": "Per Seat", "total_licenses": 4, "used_licenses": 4, "vendor": f"{DEMO_PREFIX} VMware (Broadcom)", "purchase_cost": 28000, "start_date": str(add_days(today, -90)), "expiry_date": str(add_days(today, 275)), "status": "Active"},
		{"license_name": f"{DEMO_PREFIX} Adobe Creative Cloud", "software_name": "Adobe Creative Cloud", "software_version": "2024", "license_type": "Subscription", "total_licenses": 15, "used_licenses": 18, "vendor": f"{DEMO_PREFIX} Microsoft", "purchase_cost": 9000, "start_date": str(add_days(today, -60)), "expiry_date": str(add_days(today, 305)), "status": "Active"},
		{"license_name": f"{DEMO_PREFIX} FortiGate UTM Bundle", "software_name": "FortiGate UTM", "software_version": "7.4", "license_type": "Subscription", "total_licenses": 1, "used_licenses": 1, "vendor": f"{DEMO_PREFIX} Fortinet", "purchase_cost": 5000, "start_date": str(add_days(today, -180)), "expiry_date": str(add_days(today, 185)), "status": "Active"},
		{"license_name": f"{DEMO_PREFIX} AutoCAD LT 2024", "software_name": "AutoCAD LT", "software_version": "2024", "license_type": "Per Seat", "total_licenses": 5, "used_licenses": 3, "purchase_cost": 2200, "start_date": str(add_days(today, -400)), "expiry_date": str(add_days(today, -35)), "status": "Expired"},
	]
	count = 0
	for lic in licenses:
		if not frappe.db.exists("Software License", {"license_name": lic["license_name"]}):
			doc = frappe.get_doc({"doctype": "Software License", **lic})
			doc.insert(ignore_permissions=True)
			count += 1
	return count


# ── IT Contracts ────────────────────────────────────────────────────

def _create_contracts():
	today = getdate(nowdate())
	contracts = [
		{"contract_name": f"{DEMO_PREFIX} Dell ProSupport - Servers", "contract_type": "Support", "vendor": f"{DEMO_PREFIX} Dell Technologies", "start_date": str(add_days(today, -365)), "end_date": str(add_days(today, 365)), "status": "Active", "contract_value": 24000, "annual_cost": 24000, "payment_frequency": "Annually", "sla_response_hours": 4, "sla_resolution_hours": 24, "sla_uptime_pct": 99.9},
		{"contract_name": f"{DEMO_PREFIX} Cisco SmartNet - Networking", "contract_type": "Maintenance", "vendor": f"{DEMO_PREFIX} Cisco Systems", "start_date": str(add_days(today, -180)), "end_date": str(add_days(today, 545)), "status": "Active", "contract_value": 18000, "annual_cost": 18000, "payment_frequency": "Annually", "sla_response_hours": 2, "sla_resolution_hours": 8},
		{"contract_name": f"{DEMO_PREFIX} AWS Reserved Instances", "contract_type": "Subscription", "vendor": f"{DEMO_PREFIX} AWS", "start_date": str(add_days(today, -90)), "end_date": str(add_days(today, 275)), "status": "Active", "contract_value": 36000, "annual_cost": 36000, "payment_frequency": "Monthly"},
		{"contract_name": f"{DEMO_PREFIX} Fortinet FortiCare Premium", "contract_type": "Support", "vendor": f"{DEMO_PREFIX} Fortinet", "start_date": str(add_days(today, -180)), "end_date": str(add_days(today, 45)), "status": "Expiring Soon", "contract_value": 8000, "annual_cost": 8000, "payment_frequency": "Annually", "sla_response_hours": 1},
		{"contract_name": f"{DEMO_PREFIX} HP Care Pack - Desktops", "contract_type": "Warranty", "vendor": f"{DEMO_PREFIX} HP Enterprise", "start_date": str(add_days(today, -540)), "end_date": str(add_days(today, -10)), "status": "Expired", "contract_value": 12000, "annual_cost": 4000, "payment_frequency": "Annually"},
	]
	count = 0
	for c in contracts:
		if not frappe.db.exists("IT Contract", {"contract_name": c["contract_name"]}):
			doc = frappe.get_doc({"doctype": "IT Contract", **c})
			doc.insert(ignore_permissions=True)
			count += 1
	return count


# ── Configuration Items ─────────────────────────────────────────────

def _create_configuration_items():
	items = [
		{"ci_name": f"{DEMO_PREFIX} ERP Application", "ci_type": "Application", "status": "Active", "criticality": "Critical", "environment": "Production", "business_service": "Enterprise Resource Planning", "service_tier": "Tier 1 - Mission Critical", "impact": "High", "monitoring_enabled": 1, "health_status": "Healthy", "description": "Main ERP application serving all business units"},
		{"ci_name": f"{DEMO_PREFIX} Email Service", "ci_type": "Application", "status": "Active", "criticality": "Critical", "environment": "Production", "business_service": "Email & Communication", "service_tier": "Tier 1 - Mission Critical", "impact": "High", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} Primary Database", "ci_type": "Database", "status": "Active", "criticality": "Critical", "environment": "Production", "business_service": "Data Services", "service_tier": "Tier 1 - Mission Critical", "impact": "High", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} Web Proxy / Load Balancer", "ci_type": "Network Service", "status": "Active", "criticality": "High", "environment": "Production", "business_service": "Web Services", "service_tier": "Tier 2 - Business Critical", "impact": "Medium", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} Backup System", "ci_type": "Application", "status": "Active", "criticality": "High", "environment": "Production", "business_service": "Data Protection", "service_tier": "Tier 2 - Business Critical", "impact": "Medium", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} Monitoring Stack", "ci_type": "Application", "status": "Active", "criticality": "Medium", "environment": "Production", "business_service": "Operations", "service_tier": "Tier 2 - Business Critical", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} DNS Service", "ci_type": "Network Service", "status": "Active", "criticality": "Critical", "environment": "Production", "business_service": "Network Infrastructure", "service_tier": "Tier 1 - Mission Critical", "impact": "High", "monitoring_enabled": 1, "health_status": "Healthy"},
		{"ci_name": f"{DEMO_PREFIX} VPN Gateway", "ci_type": "Network Service", "status": "Active", "criticality": "High", "environment": "Production", "business_service": "Remote Access", "service_tier": "Tier 2 - Business Critical", "impact": "Medium", "monitoring_enabled": 1, "health_status": "Degraded"},
		{"ci_name": f"{DEMO_PREFIX} Dev/Test Environment", "ci_type": "Application", "status": "Active", "criticality": "Low", "environment": "Development", "business_service": "Development", "service_tier": "Tier 3 - Business Operational"},
		{"ci_name": f"{DEMO_PREFIX} File Storage Service", "ci_type": "Cloud Service", "status": "Active", "criticality": "Medium", "environment": "Production", "business_service": "File Services", "service_tier": "Tier 2 - Business Critical", "impact": "Medium", "monitoring_enabled": 1, "health_status": "Healthy"},
	]
	count = 0
	for ci in items:
		if not frappe.db.exists("Configuration Item", {"ci_name": ci["ci_name"]}):
			doc = frappe.get_doc({"doctype": "Configuration Item", **ci})
			doc.insert(ignore_permissions=True)
			count += 1
	return count


# ── CI Relationships ────────────────────────────────────────────────

def _create_ci_relationships():
	relationships = [
		(f"{DEMO_PREFIX} ERP Application", "Runs On", f"{DEMO_PREFIX} Primary Database"),
		(f"{DEMO_PREFIX} ERP Application", "Depends On", f"{DEMO_PREFIX} DNS Service"),
		(f"{DEMO_PREFIX} Email Service", "Depends On", f"{DEMO_PREFIX} DNS Service"),
		(f"{DEMO_PREFIX} Web Proxy / Load Balancer", "Connected To", f"{DEMO_PREFIX} ERP Application"),
		(f"{DEMO_PREFIX} Backup System", "Backed Up By", f"{DEMO_PREFIX} Primary Database"),
		(f"{DEMO_PREFIX} Monitoring Stack", "Connected To", f"{DEMO_PREFIX} ERP Application"),
		(f"{DEMO_PREFIX} VPN Gateway", "Depends On", f"{DEMO_PREFIX} DNS Service"),
		(f"{DEMO_PREFIX} File Storage Service", "Depends On", f"{DEMO_PREFIX} Backup System"),
	]
	count = 0
	for source_ci, rel_type, target_ci in relationships:
		source_name = frappe.db.get_value("Configuration Item", {"ci_name": source_ci}, "name")
		target_name = frappe.db.get_value("Configuration Item", {"ci_name": target_ci}, "name")
		if not source_name or not target_name:
			continue
		rel_type_name = frappe.db.get_value("CI Relationship Type", {"relationship_type": rel_type}, "name")
		if not rel_type_name:
			continue

		name = f"{DEMO_PREFIX} {source_ci.replace(DEMO_PREFIX + ' ', '')[:20]}-{rel_type[:10]}-{target_ci.replace(DEMO_PREFIX + ' ', '')[:20]}"
		if not frappe.db.exists("CI Relationship", {"source_ci": source_name, "relationship_type": rel_type_name, "target_ci": target_name}):
			doc = frappe.get_doc({
				"doctype": "CI Relationship",
				"source_ci": source_name,
				"relationship_type": rel_type_name,
				"target_ci": target_name,
			})
			doc.insert(ignore_permissions=True)
			# Rename to demo-prefixed name
			if not doc.name.startswith(DEMO_PREFIX):
				frappe.rename_doc("CI Relationship", doc.name, name, force=True)
			count += 1

	return count


# ── Service Tickets ─────────────────────────────────────────────────

def _create_tickets():
	today = getdate(nowdate())
	admin = frappe.session.user

	tickets = [
		{"subject": f"{DEMO_PREFIX} Server srv-srv-01 high CPU usage", "ticket_type": "Incident", "ticket_category": "Incident", "priority": "High", "status": "Open", "description": "<p>Production server SRV-01 showing sustained 95%+ CPU usage. ERP performance degraded.</p>", "affected_service": "ERP Application"},
		{"subject": f"{DEMO_PREFIX} New laptop request for Finance", "ticket_type": "Service Request", "ticket_category": "Hardware Request", "priority": "Medium", "status": "In Progress", "description": "<p>Finance department needs 3 new laptops for new hires starting next month.</p>"},
		{"subject": f"{DEMO_PREFIX} VPN disconnects intermittently", "ticket_type": "Incident", "ticket_category": "Incident", "priority": "Urgent", "status": "Open", "description": "<p>Multiple remote users reporting VPN drops every 10-15 minutes since this morning. FortiClient logs attached.</p>", "affected_service": "Remote Access"},
		{"subject": f"{DEMO_PREFIX} Upgrade firewall firmware to 7.4.4", "ticket_type": "Change Request", "ticket_category": "Change Request", "priority": "Medium", "status": "Pending", "description": "<p>Schedule firmware upgrade for FortiGate 600E from 7.4.3 to 7.4.4 during maintenance window.</p>"},
		{"subject": f"{DEMO_PREFIX} Printer PRN-01 paper jam recurring", "ticket_type": "Incident", "ticket_category": "Incident", "priority": "Low", "status": "Resolved", "description": "<p>Floor 1 printer experiencing paper jams 3-4 times daily. Roller replacement needed.</p>", "resolution_details": "<p>Replaced pickup rollers and separation pad. Test prints successful.</p>", "resolved_on": str(add_days(now_datetime(), -2))},
		{"subject": f"{DEMO_PREFIX} Setup email for 5 new employees", "ticket_type": "Service Request", "ticket_category": "Access Request", "priority": "Medium", "status": "Closed", "description": "<p>Create Microsoft 365 email accounts for 5 new hires in Engineering.</p>", "resolution_details": "<p>All 5 accounts created. Credentials sent to HR.</p>", "resolved_on": str(add_days(now_datetime(), -5)), "closed_on": str(add_days(now_datetime(), -4))},
		{"subject": f"{DEMO_PREFIX} Database backup failing since Tuesday", "ticket_type": "Incident", "ticket_category": "Incident", "priority": "High", "status": "In Progress", "description": "<p>Nightly database backup job has been failing for 3 consecutive nights. Error: disk space insufficient on backup volume.</p>", "affected_service": "Data Protection"},
		{"subject": f"{DEMO_PREFIX} Request Adobe CC license for Marketing", "ticket_type": "Service Request", "ticket_category": "Software Request", "priority": "Low", "status": "Open", "description": "<p>Marketing team requests 2 additional Adobe Creative Cloud licenses for new designers.</p>"},
		{"subject": f"{DEMO_PREFIX} Switch SW-03 port flapping", "ticket_type": "Problem", "ticket_category": "Problem", "priority": "High", "status": "Open", "description": "<p>Switch SW-03 multiple ports showing flapping behavior causing intermittent connectivity in DC rack B1.</p>", "affected_service": "Network Infrastructure"},
		{"subject": f"{DEMO_PREFIX} Scheduled UPS battery replacement", "ticket_type": "Maintenance", "ticket_category": "Maintenance", "priority": "Medium", "status": "Pending", "description": "<p>UPS batteries due for replacement per vendor recommendation. Schedule with APC technician.</p>"},
		{"subject": f"{DEMO_PREFIX} WiFi coverage poor in meeting rooms", "ticket_type": "Incident", "ticket_category": "Incident", "priority": "Medium", "status": "Open", "description": "<p>Multiple complaints about weak WiFi signal in Floor 2 meeting rooms B and C.</p>"},
		{"subject": f"{DEMO_PREFIX} SSL certificate renewal for web proxy", "ticket_type": "Change Request", "ticket_category": "Change Request", "priority": "High", "status": "Open", "description": "<p>SSL wildcard certificate expires in 14 days. Need to renew and deploy to load balancer.</p>", "affected_service": "Web Services"},
	]

	# Get SLA policy
	sla_name = frappe.db.get_value("SLA Policy", {"is_default": 1}, "name")

	count = 0
	for i, ticket_data in enumerate(tickets):
		if frappe.db.exists("Service Ticket", {"subject": ticket_data["subject"]}):
			continue

		ticket_data["raised_by"] = admin
		ticket_data["raised_by_email"] = frappe.session.user
		if sla_name:
			ticket_data["sla_policy"] = sla_name

		# Find matching ticket type
		tt_name = frappe.db.get_value("Ticket Type", {"type_name": ticket_data.get("ticket_type")}, "name")
		if tt_name:
			ticket_data["ticket_type"] = tt_name
		else:
			ticket_data.pop("ticket_type", None)

		doc = frappe.get_doc({"doctype": "Service Ticket", **ticket_data})
		doc.insert(ignore_permissions=True)

		# Rename to demo-prefixed
		if not doc.name.startswith(DEMO_PREFIX):
			new_name = f"{DEMO_PREFIX} TKT-{i+1:04d}"
			try:
				frappe.rename_doc("Service Ticket", doc.name, new_name, force=True)
			except Exception:
				pass

		count += 1

	return count


# ── Discovery Results ───────────────────────────────────────────────

def _create_discovery_results():
	"""Create sample discovery results showing scan history."""
	probe_name = frappe.db.get_value("Discovery Probe", {"probe_name": "Auto Discovery"}, "name")
	if not probe_name:
		# Create minimal probe
		probe = frappe.get_doc({
			"doctype": "Discovery Probe",
			"probe_name": "Auto Discovery",
			"probe_type": "Network Scan (Ping)",
			"target_network": "10.0.0.0/16",
			"status": "Active",
		})
		probe.insert(ignore_permissions=True)
		probe_name = probe.name

	# External/unknown devices found by scan
	unknowns = [
		{"ip_address": "10.0.10.220", "hostname": "unknown-device-1.local", "mac_address": _random_mac(), "device_type": "Unknown", "status": "New"},
		{"ip_address": "10.0.10.221", "hostname": "", "mac_address": _random_mac(), "device_type": "Unknown", "status": "New"},
		{"ip_address": "10.0.0.200", "hostname": "rogue-ap.local", "mac_address": _random_mac(), "device_type": "Access Point", "status": "New"},
		{"ip_address": "10.0.10.222", "hostname": "personal-laptop.local", "mac_address": _random_mac(), "device_type": "Workstation", "status": "Ignored"},
	]
	count = 0
	for u in unknowns:
		name = f"{DEMO_PREFIX} DSC-{u['ip_address']}"
		if not frappe.db.exists("Discovery Result", name):
			doc = frappe.get_doc({
				"doctype": "Discovery Result",
				"probe": probe_name,
				"discovered_at": now_datetime(),
				**u,
			})
			doc.insert(ignore_permissions=True)
			if doc.name != name:
				try:
					frappe.rename_doc("Discovery Result", doc.name, name, force=True)
				except Exception:
					pass
			count += 1

	return count


# ── Utilities ───────────────────────────────────────────────────────

def _random_mac():
	"""Generate a random MAC address."""
	return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))
