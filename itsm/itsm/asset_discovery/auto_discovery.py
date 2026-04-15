"""
Zero-Config Auto Discovery

Automatically detects local network interfaces and scans
the entire reachable network without any user configuration.
Uses ARP, ping sweep, port scan, and hostname resolution.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
import subprocess
import socket
import json
import ipaddress
import os
import re
import struct


@frappe.whitelist()
def run_auto_discovery():
	"""
	Zero-config network discovery. Detects all local subnets,
	scans them via ARP + ping + port scan, and creates Discovery Results
	and IT Assets automatically.

	Returns progress info dict.
	"""
	frappe.only_for(["Administrator", "IT Manager", "System Manager"])

	frappe.publish_realtime("itsm_discovery_progress", {"stage": "Detecting network interfaces...", "percent": 5})

	networks = _detect_local_networks()
	if not networks:
		frappe.throw(_("Could not detect any local network interfaces."))

	# Create or get the auto-discovery probe
	probe_name = _get_or_create_auto_probe(networks)

	frappe.publish_realtime("itsm_discovery_progress", {"stage": f"Found {len(networks)} network(s). Starting scan...", "percent": 10})

	all_results = []

	# Phase 1: ARP table (instant, already-known hosts)
	frappe.publish_realtime("itsm_discovery_progress", {"stage": "Reading ARP table...", "percent": 15})
	arp_hosts = _read_arp_table()
	all_results.extend(arp_hosts)

	# Phase 2: Ping sweep each network
	total_nets = len(networks)
	for i, net in enumerate(networks):
		pct = 20 + int(40 * i / max(total_nets, 1))
		frappe.publish_realtime("itsm_discovery_progress", {
			"stage": f"Ping scanning {net}...",
			"percent": pct,
		})
		ping_results = _fast_ping_sweep(str(net))
		# Merge - avoid duplicate IPs
		known_ips = {r["ip_address"] for r in all_results}
		for r in ping_results:
			if r["ip_address"] not in known_ips:
				all_results.append(r)
				known_ips.add(r["ip_address"])

	# Phase 3: Port scan discovered hosts (top ports only for speed)
	frappe.publish_realtime("itsm_discovery_progress", {"stage": f"Port scanning {len(all_results)} hosts...", "percent": 65})
	all_results = _quick_port_scan(all_results)

	# Phase 4: Resolve hostnames and guess device types
	frappe.publish_realtime("itsm_discovery_progress", {"stage": "Resolving hostnames...", "percent": 80})
	for r in all_results:
		if not r.get("hostname"):
			r["hostname"] = _resolve_hostname(r["ip_address"])
		if not r.get("device_type") or r["device_type"] == "Unknown":
			r["device_type"] = _guess_device_type_from_info(r)

	# Phase 5: Save results and create assets
	frappe.publish_realtime("itsm_discovery_progress", {"stage": "Saving discovered assets...", "percent": 90})
	created, updated = _save_auto_discovery_results(probe_name, all_results)

	frappe.publish_realtime("itsm_discovery_progress", {
		"stage": f"Done! Found {len(all_results)} hosts. Created {created} assets, updated {updated}.",
		"percent": 100,
		"done": True,
	})

	return {
		"total_discovered": len(all_results),
		"assets_created": created,
		"assets_updated": updated,
		"networks_scanned": [str(n) for n in networks],
	}


def _detect_local_networks():
	"""Detect all local network interfaces and their subnets."""
	networks = []

	try:
		# Use `ip addr` on Linux
		result = subprocess.run(
			["ip", "-4", "-o", "addr", "show"],
			capture_output=True, text=True, timeout=10,
		)
		if result.returncode == 0:
			for line in result.stdout.strip().split("\n"):
				parts = line.split()
				# Format: index: iface inet x.x.x.x/prefix ...
				for i, part in enumerate(parts):
					if part == "inet" and i + 1 < len(parts):
						cidr = parts[i + 1]
						try:
							net = ipaddress.ip_network(cidr, strict=False)
							# Skip loopback and link-local
							if net.is_loopback or net.is_link_local:
								continue
							# Skip tiny networks (< /30) or huge (/8)
							if net.prefixlen < 8 or net.prefixlen > 30:
								continue
							networks.append(net)
						except ValueError:
							continue
	except (subprocess.TimeoutExpired, FileNotFoundError):
		pass

	if not networks:
		# Fallback: use hostname resolution
		try:
			hostname = socket.gethostname()
			local_ip = socket.gethostbyname(hostname)
			if local_ip and not local_ip.startswith("127."):
				net = ipaddress.ip_network(f"{local_ip}/24", strict=False)
				networks.append(net)
		except Exception:
			pass

	return networks


def _read_arp_table():
	"""Read system ARP table for already-known hosts."""
	results = []
	try:
		result = subprocess.run(
			["ip", "neigh", "show"],
			capture_output=True, text=True, timeout=10,
		)
		if result.returncode == 0:
			for line in result.stdout.strip().split("\n"):
				if not line.strip():
					continue
				parts = line.split()
				if len(parts) >= 4 and parts[-1] in ("REACHABLE", "STALE", "DELAY"):
					ip = parts[0]
					mac = ""
					for j, p in enumerate(parts):
						if p == "lladdr" and j + 1 < len(parts):
							mac = parts[j + 1]
							break
					try:
						ipaddress.ip_address(ip)
					except ValueError:
						continue
					results.append({
						"ip_address": ip,
						"mac_address": mac,
						"hostname": "",
						"is_alive": True,
						"open_ports": [],
						"device_type": "Unknown",
						"discovery_method": "ARP",
					})
	except (subprocess.TimeoutExpired, FileNotFoundError):
		pass

	return results


def _fast_ping_sweep(network_cidr):
	"""Fast ping sweep using fping if available, fallback to parallel ping."""
	results = []

	# Try fping first (much faster)
	try:
		result = subprocess.run(
			["fping", "-a", "-g", network_cidr, "-q", "-r", "1", "-t", "500"],
			capture_output=True, text=True, timeout=120,
		)
		# fping prints alive hosts to stderr with -a flag... or stdout
		output = result.stdout.strip() or result.stderr.strip()
		for line in output.split("\n"):
			ip = line.strip().split()[0] if line.strip() else ""
			if ip:
				try:
					ipaddress.ip_address(ip)
					results.append({
						"ip_address": ip,
						"hostname": "",
						"mac_address": "",
						"is_alive": True,
						"open_ports": [],
						"device_type": "Unknown",
						"discovery_method": "Ping",
					})
				except ValueError:
					continue
		if results:
			return results
	except (FileNotFoundError, subprocess.TimeoutExpired):
		pass

	# Fallback: parallel ping using xargs
	try:
		net = ipaddress.ip_network(network_cidr, strict=False)
		hosts = [str(ip) for ip in net.hosts()]
		# Limit to /24 max for performance
		if len(hosts) > 254:
			hosts = hosts[:254]

		# Write hosts to a temp approach, use shell parallel ping
		host_list = "\n".join(hosts)
		result = subprocess.run(
			["bash", "-c",
			 f'echo "{host_list}" | xargs -P 50 -I {{}} bash -c \'ping -c1 -W1 {{}} >/dev/null 2>&1 && echo {{}}\'' ],
			capture_output=True, text=True, timeout=120,
		)
		for line in result.stdout.strip().split("\n"):
			ip = line.strip()
			if ip:
				try:
					ipaddress.ip_address(ip)
					results.append({
						"ip_address": ip,
						"hostname": "",
						"mac_address": "",
						"is_alive": True,
						"open_ports": [],
						"device_type": "Unknown",
						"discovery_method": "Ping",
					})
				except ValueError:
					continue
	except (subprocess.TimeoutExpired, Exception):
		pass

	return results


def _quick_port_scan(hosts):
	"""Quick port scan on key ports for device type identification."""
	key_ports = [22, 80, 443, 3389, 8080, 161, 445, 3306, 5432, 8443, 9100, 631, 53]

	for host in hosts:
		open_ports = []
		ip = host["ip_address"]
		for port in key_ports:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.settimeout(0.5)
				if sock.connect_ex((ip, port)) == 0:
					open_ports.append({
						"port_number": port,
						"protocol": "TCP",
						"service_name": _get_service_name(port),
						"state": "Open",
					})
				sock.close()
			except Exception:
				continue
		host["open_ports"] = open_ports

	return hosts


def _resolve_hostname(ip):
	"""Reverse DNS lookup."""
	try:
		hostname = socket.getfqdn(ip)
		return hostname if hostname != ip else ""
	except Exception:
		return ""


def _get_service_name(port):
	"""Get common service name for a port."""
	services = {
		22: "SSH", 80: "HTTP", 443: "HTTPS", 3389: "RDP",
		8080: "HTTP-Alt", 161: "SNMP", 135: "RPC", 445: "SMB",
		3306: "MySQL", 5432: "PostgreSQL", 1433: "MSSQL",
		8443: "HTTPS-Alt", 53: "DNS", 25: "SMTP", 631: "IPP",
		9100: "Printer", 5900: "VNC",
	}
	return services.get(port, f"port-{port}")


def _guess_device_type_from_info(host):
	"""Guess device type based on open ports and hostname patterns."""
	port_nums = {p["port_number"] for p in host.get("open_ports", [])}
	hostname = (host.get("hostname") or "").lower()

	# Printer detection
	if 9100 in port_nums or 631 in port_nums:
		return "Printer"
	if any(kw in hostname for kw in ("printer", "prn", "hp-", "canon", "xerox", "epson")):
		return "Printer"

	# Network device detection
	if 161 in port_nums and len(port_nums) <= 2:
		return "Switch"
	if any(kw in hostname for kw in ("switch", "sw-", "ap-", "wap")):
		return "Switch"
	if any(kw in hostname for kw in ("router", "rtr", "gw-", "gateway")):
		return "Router"
	if any(kw in hostname for kw in ("fw-", "firewall", "pfsense", "fortigate")):
		return "Firewall"
	if any(kw in hostname for kw in ("ap-", "access-point", "unifi")):
		return "Access Point"

	# Server detection
	if 22 in port_nums and (80 in port_nums or 443 in port_nums or 8080 in port_nums):
		return "Server"
	if 3306 in port_nums or 5432 in port_nums or 1433 in port_nums:
		return "Server"
	if any(kw in hostname for kw in ("server", "srv", "db-", "web-", "app-", "mail")):
		return "Server"

	# Workstation detection
	if 3389 in port_nums:
		return "Workstation"
	if 445 in port_nums and 80 not in port_nums:
		return "Workstation"
	if any(kw in hostname for kw in ("desktop", "pc-", "ws-", "laptop", "workstation")):
		return "Workstation"

	if port_nums:
		return "Server"

	return "Unknown"


def _get_or_create_auto_probe(networks):
	"""Get or create the auto-discovery probe."""
	probe_name = frappe.db.get_value(
		"Discovery Probe",
		{"probe_name": "Auto Discovery", "probe_type": "Network Scan (Ping)"},
		"name",
	)
	if probe_name:
		probe = frappe.get_doc("Discovery Probe", probe_name)
		probe.target_network = str(networks[0]) if networks else ""
		probe.target_hosts = "\n".join(str(n) for n in networks[1:]) if len(networks) > 1 else ""
		probe.status = "Active"
		probe.last_run = now_datetime()
		probe.save(ignore_permissions=True)
		return probe.name

	probe = frappe.get_doc({
		"doctype": "Discovery Probe",
		"probe_name": "Auto Discovery",
		"probe_type": "Network Scan (Ping)",
		"target_network": str(networks[0]) if networks else "",
		"target_hosts": "\n".join(str(n) for n in networks[1:]) if len(networks) > 1 else "",
		"status": "Active",
		"last_run": now_datetime(),
		"description": "Automatic zero-config network discovery. Scans all local subnets.",
	})
	probe.insert(ignore_permissions=True)
	frappe.db.commit()
	return probe.name


def _save_auto_discovery_results(probe_name, results):
	"""Save discovery results and auto-create IT Assets."""
	created = 0
	updated = 0

	for r in results:
		ip = r.get("ip_address")
		if not ip:
			continue

		# Save/update Discovery Result
		existing_result = frappe.db.get_value(
			"Discovery Result",
			{"probe": probe_name, "ip_address": ip},
			"name",
		)
		if existing_result:
			doc = frappe.get_doc("Discovery Result", existing_result)
			doc.hostname = r.get("hostname") or doc.hostname
			doc.mac_address = r.get("mac_address") or doc.mac_address
			doc.device_type = r.get("device_type") or doc.device_type
			doc.discovered_at = now_datetime()
		else:
			doc = frappe.get_doc({
				"doctype": "Discovery Result",
				"probe": probe_name,
				"ip_address": ip,
				"hostname": r.get("hostname", ""),
				"mac_address": r.get("mac_address", ""),
				"device_type": r.get("device_type", "Unknown"),
				"discovered_at": now_datetime(),
				"status": "New",
			})

		# Set ports
		doc.open_ports = []
		for port in r.get("open_ports", []):
			doc.append("open_ports", port)

		doc.save(ignore_permissions=True)

		# Auto-create or update IT Asset
		asset_name = frappe.db.get_value("IT Asset", {"ip_address": ip}, "name")
		if not asset_name and r.get("mac_address"):
			asset_name = frappe.db.get_value("IT Asset", {"mac_address": r["mac_address"]}, "name")

		device_type = r.get("device_type", "Unknown")
		asset_type = _device_type_to_asset_type(device_type)
		category = _device_type_to_category(device_type)

		if asset_name:
			# Update existing
			asset = frappe.get_doc("IT Asset", asset_name)
			asset.last_seen = now_datetime()
			asset.is_online = 1
			if r.get("hostname") and not asset.hostname:
				asset.hostname = r["hostname"]
			if r.get("mac_address") and not asset.mac_address:
				asset.mac_address = r["mac_address"]
			asset.save(ignore_permissions=True)

			doc.status = "Matched"
			doc.linked_asset = asset_name
			doc.save(ignore_permissions=True)
			updated += 1
		else:
			# Create new asset
			hostname = r.get("hostname") or ip
			asset_name_val = hostname if hostname != ip else f"{device_type}-{ip}"

			asset = frappe.get_doc({
				"doctype": "IT Asset",
				"asset_name": asset_name_val,
				"hostname": r.get("hostname", ""),
				"ip_address": ip,
				"mac_address": r.get("mac_address", ""),
				"asset_type": asset_type,
				"category": category if frappe.db.exists("IT Asset Category", category) else None,
				"status": "Active",
				"discovery_source": "Network Scan",
				"last_seen": now_datetime(),
				"is_online": 1,
			})
			asset.insert(ignore_permissions=True)

			doc.status = "Created Asset"
			doc.linked_asset = asset.name
			doc.auto_created = 1
			doc.save(ignore_permissions=True)
			created += 1

	frappe.db.commit()
	return created, updated


def _device_type_to_asset_type(device_type):
	"""Map discovery device type to IT Asset asset_type."""
	mapping = {
		"Server": "Server",
		"Workstation": "Hardware",
		"Router": "Network Device",
		"Switch": "Network Device",
		"Firewall": "Network Device",
		"Printer": "Printer",
		"Access Point": "Network Device",
		"Storage": "Server",
		"Virtual Machine": "Virtual Machine",
	}
	return mapping.get(device_type, "Hardware")


def _device_type_to_category(device_type):
	"""Map discovery device type to IT Asset Category name."""
	mapping = {
		"Server": "Server",
		"Workstation": "Desktop",
		"Router": "Router",
		"Switch": "Network Switch",
		"Firewall": "Firewall",
		"Printer": "Printer",
		"Access Point": "Access Point",
		"Storage": "Storage Device",
		"Virtual Machine": "Virtual Machine",
	}
	return mapping.get(device_type, "Desktop")
