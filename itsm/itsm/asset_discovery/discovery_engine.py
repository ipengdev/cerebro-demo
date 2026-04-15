"""
Asset Discovery Engine

Provides network discovery capabilities:
- Ping sweep (ICMP)
- TCP port scanning
- SNMP discovery
- SSH remote info collection
- External API integration (vCenter, cloud providers)
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
import subprocess
import socket
import json
import ipaddress


def run_probe(probe_name):
    """Main entry point - run a discovery probe."""
    probe = frappe.get_doc("Discovery Probe", probe_name)
    probe.db_set("status", "Running")
    probe.db_set("last_run", now_datetime())

    try:
        hosts = _get_target_hosts(probe)
        results = []

        if probe.probe_type == "Network Scan (Ping)":
            results = _ping_sweep(hosts)
        elif probe.probe_type == "Port Scan":
            results = _port_scan(hosts)
        elif probe.probe_type == "SNMP Discovery":
            results = _snmp_discovery(probe, hosts)
        elif probe.probe_type == "SSH Discovery":
            results = _ssh_discovery(probe, hosts)
        elif probe.probe_type == "API Integration":
            results = _api_discovery(probe)
        elif probe.probe_type == "Agent Based":
            results = _agent_discovery(probe)

        _save_results(probe, results)

        probe.db_set("status", "Active")
        probe.db_set("total_discovered", len(results))
        probe.db_set(
            "last_result_summary",
            f"Discovered {len(results)} hosts at {now_datetime()}",
        )
    except Exception as e:
        probe.db_set("status", "Failed")
        probe.db_set("last_result_summary", f"Error: {str(e)[:200]}")
        frappe.log_error(f"Discovery probe {probe_name} failed: {e}")


def _get_target_hosts(probe):
    """Parse target hosts from probe configuration."""
    hosts = []
    if probe.target_network:
        try:
            network = ipaddress.ip_network(probe.target_network, strict=False)
            hosts.extend([str(ip) for ip in network.hosts()])
        except ValueError:
            frappe.throw(_("Invalid network CIDR: {0}").format(probe.target_network))

    if probe.target_hosts:
        for line in probe.target_hosts.strip().split("\n"):
            host = line.strip()
            if host:
                hosts.append(host)

    return hosts


def _ping_sweep(hosts):
    """Ping sweep to discover live hosts."""
    results = []
    for host in hosts:
        try:
            # Use subprocess for ping with timeout
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", host],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                hostname = _resolve_hostname(host)
                results.append({
                    "ip_address": host,
                    "hostname": hostname,
                    "is_alive": True,
                })
        except (subprocess.TimeoutExpired, Exception):
            continue
    return results


def _port_scan(hosts, ports=None):
    """Basic TCP port scan."""
    if ports is None:
        ports = [22, 80, 443, 3389, 8080, 161, 135, 445, 3306, 5432, 1433, 8443]

    results = []
    for host in hosts:
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((host, port)) == 0:
                    service = _get_service_name(port)
                    open_ports.append({
                        "port_number": port,
                        "protocol": "TCP",
                        "service_name": service,
                        "state": "Open",
                    })
                sock.close()
            except Exception:
                continue

        if open_ports:
            hostname = _resolve_hostname(host)
            device_type = _guess_device_type(open_ports)
            results.append({
                "ip_address": host,
                "hostname": hostname,
                "open_ports": open_ports,
                "device_type": device_type,
                "is_alive": True,
            })
    return results


def _snmp_discovery(probe, hosts):
    """SNMP-based discovery (requires pysnmp or system snmpget)."""
    results = []
    community = probe.get_password("snmp_community") or "public"

    for host in hosts:
        try:
            data = _snmp_get_system_info(host, community)
            if data:
                results.append({
                    "ip_address": host,
                    "hostname": data.get("sysName", _resolve_hostname(host)),
                    "snmp_sysdescr": data.get("sysDescr"),
                    "snmp_sysname": data.get("sysName"),
                    "snmp_syslocation": data.get("sysLocation"),
                    "snmp_syscontact": data.get("sysContact"),
                    "os_detected": data.get("sysDescr", "")[:100],
                    "is_alive": True,
                })
        except Exception:
            continue
    return results


def _snmp_get_system_info(host, community):
    """Get SNMP system information using snmpget command."""
    oids = {
        "sysDescr": "1.3.6.1.2.1.1.1.0",
        "sysName": "1.3.6.1.2.1.1.5.0",
        "sysLocation": "1.3.6.1.2.1.1.6.0",
        "sysContact": "1.3.6.1.2.1.1.4.0",
    }
    data = {}
    for name, oid in oids.items():
        try:
            result = subprocess.run(
                ["snmpget", "-v2c", "-c", community, host, oid],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Parse output: OID = TYPE: VALUE
                parts = result.stdout.split(":", 1)
                if len(parts) > 1:
                    data[name] = parts[1].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return data if data else None


def _ssh_discovery(probe, hosts):
    """SSH-based discovery to collect system info."""
    results = []
    username = probe.ssh_username or "root"
    port = probe.ssh_port or 22

    for host in hosts:
        try:
            cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                "-p", str(port),
                f"{username}@{host}",
                "hostname; uname -a; cat /sys/class/dmi/id/product_serial 2>/dev/null; "
                "cat /sys/class/dmi/id/sys_vendor 2>/dev/null; "
                "cat /sys/class/dmi/id/product_name 2>/dev/null; "
                "uptime",
            ]
            if probe.ssh_key:
                cmd.insert(1, "-i")
                cmd.insert(2, frappe.get_site_path("private", "files", probe.ssh_key.split("/")[-1]))

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                results.append({
                    "ip_address": host,
                    "hostname": lines[0] if lines else host,
                    "os_detected": lines[1] if len(lines) > 1 else "",
                    "serial_number": lines[2] if len(lines) > 2 else "",
                    "manufacturer": lines[3] if len(lines) > 3 else "",
                    "model": lines[4] if len(lines) > 4 else "",
                    "uptime": lines[5] if len(lines) > 5 else "",
                    "device_type": "Server",
                    "is_alive": True,
                })
        except Exception:
            continue
    return results


def _api_discovery(probe):
    """API-based discovery for cloud and virtualization platforms."""
    results = []
    endpoint = probe.api_endpoint
    api_key = probe.get_password("api_key")
    api_type = probe.api_type

    if not endpoint or not api_key:
        return results

    import requests

    if api_type == "REST":
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
            response = requests.get(endpoint, headers=headers, timeout=30, verify=True)
            response.raise_for_status()
            data = response.json()

            # Generic REST response parsing
            items = data if isinstance(data, list) else data.get("items", data.get("results", []))
            for item in items:
                if isinstance(item, dict):
                    results.append({
                        "ip_address": item.get("ip_address", item.get("ip", "")),
                        "hostname": item.get("hostname", item.get("name", "")),
                        "os_detected": item.get("os", item.get("operating_system", "")),
                        "manufacturer": item.get("manufacturer", item.get("vendor", "")),
                        "model": item.get("model", ""),
                        "serial_number": item.get("serial_number", item.get("serial", "")),
                        "device_type": item.get("device_type", item.get("type", "")),
                        "is_alive": True,
                        "raw_data": json.dumps(item),
                    })
        except Exception as e:
            frappe.log_error(f"API Discovery error: {e}")

    return results


def _agent_discovery(probe):
    """Process heartbeats from installed agents."""
    # Agents POST their data to the heartbeat API endpoint
    # This just returns existing unprocessed heartbeat records
    return []


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
        8443: "HTTPS-Alt", 53: "DNS", 25: "SMTP", 110: "POP3",
        143: "IMAP", 993: "IMAPS", 995: "POP3S", 21: "FTP",
        23: "Telnet", 389: "LDAP", 636: "LDAPS", 5900: "VNC",
    }
    return services.get(port, f"port-{port}")


def _guess_device_type(open_ports):
    """Guess device type based on open ports."""
    port_nums = {p["port_number"] for p in open_ports}
    if 161 in port_nums and len(port_nums) <= 3:
        return "Switch"
    if 3389 in port_nums:
        return "Workstation"
    if 22 in port_nums and 80 in port_nums:
        return "Server"
    if 80 in port_nums or 443 in port_nums:
        return "Server"
    if 9100 in port_nums:
        return "Printer"
    return "Unknown"


def _save_results(probe, results):
    """Save discovery results as Discovery Result documents."""
    for result_data in results:
        # Check if existing result for same IP from same probe
        existing = frappe.db.exists(
            "Discovery Result",
            {"probe": probe.name, "ip_address": result_data.get("ip_address")},
        )

        if existing:
            # Update existing
            doc = frappe.get_doc("Discovery Result", existing)
            for key, val in result_data.items():
                if key != "open_ports" and val:
                    doc.set(key, val)
            doc.discovered_at = now_datetime()
            # Update linked asset if exists
            if doc.linked_asset:
                _update_linked_asset(doc)
        else:
            doc = frappe.get_doc({
                "doctype": "Discovery Result",
                "probe": probe.name,
                "discovered_at": now_datetime(),
                "status": "New",
                **{k: v for k, v in result_data.items() if k != "open_ports"},
            })

        # Handle ports
        if "open_ports" in result_data:
            doc.open_ports = []
            for port in result_data["open_ports"]:
                doc.append("open_ports", port)

        doc.save(ignore_permissions=True)

    frappe.db.commit()


def _update_linked_asset(discovery_result):
    """Update a linked IT Asset with latest discovery data."""
    try:
        asset = frappe.get_doc("IT Asset", discovery_result.linked_asset)
        asset.last_seen = now_datetime()
        asset.is_online = 1
        if discovery_result.hostname:
            asset.hostname = discovery_result.hostname
        if discovery_result.os_detected:
            asset.operating_system = discovery_result.os_detected
        asset.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error updating linked asset: {e}")


# --- Heartbeat API for agent-based discovery ---

@frappe.whitelist(allow_guest=False)
def receive_heartbeat(data):
    """
    Receive heartbeat data from an installed agent on an asset.
    Called via POST /api/method/itsm.asset_discovery.discovery_engine.receive_heartbeat

    Expected data (JSON):
    {
        "hostname": "server01",
        "ip_address": "192.168.1.10",
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "os": "Ubuntu 22.04",
        "cpu": "Intel Xeon E5-2680",
        "ram_gb": 64,
        "storage_gb": 500,
        "agent_version": "1.0.0",
        "serial_number": "SN12345",
        "uptime": "45 days"
    }
    """
    if isinstance(data, str):
        data = json.loads(data)

    ip_address = data.get("ip_address")
    if not ip_address:
        frappe.throw(_("ip_address is required"))

    # Find or create IT Asset by IP or serial number
    asset_name = None
    if data.get("serial_number"):
        asset_name = frappe.db.get_value(
            "IT Asset", {"serial_number": data["serial_number"]}, "name"
        )
    if not asset_name:
        asset_name = frappe.db.get_value(
            "IT Asset", {"ip_address": ip_address}, "name"
        )

    now = now_datetime()

    if asset_name:
        asset = frappe.get_doc("IT Asset", asset_name)
        asset.last_seen = now
        asset.last_heartbeat = now
        asset.is_online = 1
        asset.agent_version = data.get("agent_version", "")
        if data.get("hostname"):
            asset.hostname = data["hostname"]
        if data.get("os"):
            asset.operating_system = data["os"]
        if data.get("cpu"):
            asset.processor = data["cpu"]
        if data.get("ram_gb"):
            asset.ram_gb = data["ram_gb"]
        if data.get("storage_gb"):
            asset.storage_gb = data["storage_gb"]
        asset.discovery_source = "Agent"
        asset.save(ignore_permissions=True)
    else:
        # Create new asset from heartbeat
        asset = frappe.get_doc({
            "doctype": "IT Asset",
            "asset_name": data.get("hostname", ip_address),
            "category": _get_or_create_category("Discovered Device"),
            "asset_type": "Hardware",
            "status": "Active",
            "hostname": data.get("hostname"),
            "ip_address": ip_address,
            "mac_address": data.get("mac_address"),
            "operating_system": data.get("os"),
            "processor": data.get("cpu"),
            "ram_gb": data.get("ram_gb"),
            "storage_gb": data.get("storage_gb"),
            "serial_number": data.get("serial_number"),
            "discovery_source": "Agent",
            "last_seen": now,
            "last_heartbeat": now,
            "is_online": 1,
            "agent_version": data.get("agent_version", ""),
        })
        asset.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "ok", "asset": asset.name}


def _get_or_create_category(name):
    if not frappe.db.exists("IT Asset Category", name):
        frappe.get_doc({
            "doctype": "IT Asset Category",
            "category_name": name,
        }).insert(ignore_permissions=True)
    return name


# --- Scheduled tasks ---

def check_stale_assets():
    """Mark assets as offline if no heartbeat in 15 minutes."""
    from frappe.utils import add_to_date

    threshold = add_to_date(now_datetime(), minutes=-15)
    stale = frappe.get_all(
        "IT Asset",
        filters={
            "is_online": 1,
            "last_heartbeat": ["<", threshold],
            "discovery_source": "Agent",
        },
        pluck="name",
    )
    for name in stale:
        frappe.db.set_value("IT Asset", name, "is_online", 0)

    if stale:
        frappe.db.commit()


def run_scheduled_probes():
    """Run discovery probes that are due based on schedule."""
    schedules = frappe.get_all(
        "Discovery Schedule",
        filters={"is_active": 1},
        fields=["name", "probe", "frequency", "last_run", "next_run"],
    )

    now = now_datetime()
    for schedule in schedules:
        should_run = False
        if not schedule.last_run:
            should_run = True
        elif schedule.next_run and now >= schedule.next_run:
            should_run = True

        if should_run:
            frappe.enqueue(
                "itsm.asset_discovery.discovery_engine.run_probe",
                probe_name=schedule.probe,
                queue="long",
                timeout=3600,
            )
            frappe.db.set_value("Discovery Schedule", schedule.name, "last_run", now)
            # Calculate next run
            frequency_hours = {
                "Hourly": 1,
                "Every 6 Hours": 6,
                "Daily": 24,
                "Weekly": 168,
                "Monthly": 720,
            }
            hours = frequency_hours.get(schedule.frequency, 24)
            from frappe.utils import add_to_date

            next_run = add_to_date(now, hours=hours)
            frappe.db.set_value("Discovery Schedule", schedule.name, "next_run", next_run)

    frappe.db.commit()


# ── Zero-Config Auto Discovery ─────────────────────────────────────

@frappe.whitelist()
def auto_discover():
    """
    Zero-config network discovery: detects local subnets, pings all hosts,
    scans common ports on responders, and creates IT Asset records.
    No Discovery Probe setup needed.
    """
    frappe.only_for(["Administrator", "System Manager", "IT Manager"])

    frappe.publish_realtime("itsm_auto_discovery", {"stage": "Detecting local subnets...", "percent": 5})

    subnets = _detect_local_subnets()
    if not subnets:
        frappe.publish_realtime("itsm_auto_discovery", {
            "stage": "No local subnets detected.", "percent": 100, "done": True,
        })
        return {"hosts_found": 0, "assets_created": 0, "subnets": []}

    frappe.publish_realtime("itsm_auto_discovery", {
        "stage": f"Found {len(subnets)} subnet(s): {', '.join(subnets)}. Starting scan...",
        "percent": 10,
    })

    all_alive = []
    subnet_count = len(subnets)
    for idx, subnet in enumerate(subnets):
        pct = 10 + int(40 * (idx / subnet_count))
        frappe.publish_realtime("itsm_auto_discovery", {
            "stage": f"Ping sweep on {subnet}...", "percent": pct,
        })
        alive = _ping_sweep_subnet(subnet)
        all_alive.extend(alive)

    frappe.publish_realtime("itsm_auto_discovery", {
        "stage": f"Found {len(all_alive)} live hosts. Scanning ports...", "percent": 55,
    })

    # Port scan each alive host
    host_details = []
    total_hosts = len(all_alive)
    for idx, ip in enumerate(all_alive):
        pct = 55 + int(20 * (idx / max(total_hosts, 1)))
        if idx % 10 == 0:
            frappe.publish_realtime("itsm_auto_discovery", {
                "stage": f"Scanning {ip} ({idx+1}/{total_hosts})...", "percent": pct,
            })
        ports = _quick_port_scan(ip)
        hostname = _resolve_hostname(ip)
        device_type = _guess_device_type(ports, hostname)
        mac = _get_mac_from_arp(ip)
        host_details.append({
            "ip": ip,
            "hostname": hostname,
            "ports": ports,
            "device_type": device_type,
            "mac_address": mac,
        })

    # Collect detailed system info from reachable hosts
    frappe.publish_realtime("itsm_auto_discovery", {
        "stage": "Collecting system details...", "percent": 78,
    })
    for idx, host in enumerate(host_details):
        pct = 78 + int(10 * (idx / max(total_hosts, 1)))
        if idx % 5 == 0:
            frappe.publish_realtime("itsm_auto_discovery", {
                "stage": f"Profiling {host['ip']} ({idx+1}/{total_hosts})...", "percent": pct,
            })
        details = _collect_system_details(host["ip"], host["ports"])
        host.update(details)

    frappe.publish_realtime("itsm_auto_discovery", {
        "stage": "Creating IT Asset records...", "percent": 90,
    })

    # Create assets
    assets_created = 0
    for host in host_details:
        created = _create_asset_from_discovery(host)
        if created:
            assets_created += 1

    frappe.db.commit()

    frappe.publish_realtime("itsm_auto_discovery", {
        "stage": f"Done! Discovered {len(all_alive)} hosts, created {assets_created} new assets.",
        "percent": 100,
        "done": True,
    })

    return {
        "hosts_found": len(all_alive),
        "assets_created": assets_created,
        "subnets": subnets,
        "details": host_details,
    }


def _detect_local_subnets():
    """Detect all local network subnets from system interfaces."""
    subnets = set()
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get("addr", "")
                    mask = addr.get("netmask", "")
                    if ip and mask and not ip.startswith("127."):
                        try:
                            network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                            if network.num_addresses <= 65536:  # /16 or smaller
                                subnets.add(str(network))
                        except ValueError:
                            pass
    except ImportError:
        # Fallback: parse ip addr output
        try:
            result = subprocess.run(
                ["ip", "-4", "-o", "addr", "show"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "inet" and i + 1 < len(parts):
                        cidr = parts[i + 1]
                        try:
                            network = ipaddress.IPv4Network(cidr, strict=False)
                            ip_str = cidr.split("/")[0]
                            if not ip_str.startswith("127.") and network.num_addresses <= 65536:
                                subnets.add(str(network))
                        except ValueError:
                            pass
        except Exception:
            pass

    return sorted(subnets)


def _ping_sweep_subnet(subnet_cidr):
    """Ping sweep a subnet. Returns list of alive IPs."""
    alive = []
    try:
        network = ipaddress.IPv4Network(subnet_cidr, strict=False)
        hosts = list(network.hosts())
        # Limit to /22 (1022 hosts) max to avoid very long scans
        if len(hosts) > 1022:
            hosts = hosts[:1022]

        # Method 1: Try fping (fastest)
        try:
            result = subprocess.run(
                ["fping", "-a", "-q", "-g", subnet_cidr, "-t", "200", "-r", "1"],
                capture_output=True, text=True, timeout=max(300, len(hosts)),
            )
            alive = [ip.strip() for ip in result.stdout.strip().split("\n") if ip.strip()]
            if alive:
                return alive
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Method 2: Try ARP table after a broadcast ping (fast)
        try:
            # Send broadcast ping to populate ARP cache
            subprocess.run(
                ["ping", "-c", "2", "-W", "1", "-b", str(network.broadcast_address)],
                capture_output=True, timeout=5,
            )
            # Read ARP table
            result = subprocess.run(
                ["arp", "-n"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[2] != "(incomplete)":
                    try:
                        ip_obj = ipaddress.IPv4Address(parts[0])
                        if ip_obj in network:
                            alive.append(str(ip_obj))
                    except ValueError:
                        pass
            if alive:
                return alive
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Method 3: Parallel ping using subprocess (faster than sequential)
        import concurrent.futures
        def _ping_one(ip_str):
            try:
                r = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip_str],
                    capture_output=True, timeout=3,
                )
                return ip_str if r.returncode == 0 else None
            except Exception:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(_ping_one, [str(h) for h in hosts])
            alive = [ip for ip in results if ip]

    except Exception:
        pass
    return alive


def _quick_port_scan(ip, timeout=1):
    """Scan common ports on a single host."""
    common_ports = [22, 80, 443, 135, 139, 445, 3389, 5985, 8080, 161, 623, 9100]
    open_ports = []
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except Exception:
            pass
    return open_ports


def _resolve_hostname(ip):
    """Try reverse DNS lookup."""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except Exception:
        return ""


def _guess_device_type(ports, hostname):
    """Guess device type from open ports and hostname."""
    hostname_lower = (hostname or "").lower()

    if 9100 in ports:
        return "Printer"
    if 623 in ports:
        return "Server"
    if {80, 443}.intersection(ports) and not {22, 3389, 445}.intersection(ports):
        if any(kw in hostname_lower for kw in ["ap", "wifi", "wap", "unifi"]):
            return "Access Point"
        if any(kw in hostname_lower for kw in ["cam", "ipcam", "hikvision", "dahua"]):
            return "IP Camera"
        return "Network Device"
    if 22 in ports and 80 in ports:
        return "Server"
    if 3389 in ports or 5985 in ports:
        return "Workstation"
    if 22 in ports:
        return "Server"
    if 445 in ports or 139 in ports:
        return "Workstation"
    if 161 in ports:
        return "Network Device"
    if any(kw in hostname_lower for kw in ["printer", "print", "mfp", "laserjet"]):
        return "Printer"
    if any(kw in hostname_lower for kw in ["switch", "sw-", "router", "gw-", "fw-", "firewall"]):
        return "Network Device"
    if any(kw in hostname_lower for kw in ["srv", "server", "esxi", "vcenter", "dc-"]):
        return "Server"
    return "Other"


def _get_mac_from_arp(ip):
    """Get MAC address from ARP table."""
    try:
        result = subprocess.run(
            ["ip", "neigh", "show", ip],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if "lladdr" in parts:
                idx = parts.index("lladdr")
                if idx + 1 < len(parts):
                    return parts[idx + 1].upper()
    except Exception:
        pass
    # Fallback: arp command
    try:
        result = subprocess.run(
            ["arp", "-n", ip],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            for part in parts:
                if len(part) == 17 and part.count(":") == 5:
                    return part.upper()
    except Exception:
        pass
    return ""


def _collect_system_details(ip, ports):
    """Collect detailed system info from a host. Tries local (if it's us), then SSH."""
    details = {}

    # Check if this is the local machine
    try:
        result = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, timeout=5,
        )
        local_ips = result.stdout.strip().split()
        is_local = ip in local_ips
    except Exception:
        is_local = False

    if is_local:
        details = _collect_local_system_info()
    elif 22 in ports:
        details = _collect_ssh_system_info(ip)

    # Network info we can get for any host
    if not details.get("subnet") or not details.get("gateway"):
        net_info = _collect_network_context(ip)
        for k, v in net_info.items():
            if v and not details.get(k):
                details[k] = v

    return details


def _collect_local_system_info():
    """Collect system info from the local machine."""
    info = {}
    try:
        # Hostname / FQDN
        result = subprocess.run(["hostname", "-f"], capture_output=True, text=True, timeout=5)
        fqdn = result.stdout.strip()
        if fqdn:
            info["fqdn"] = fqdn
            parts = fqdn.split(".", 1)
            if len(parts) > 1:
                info["domain"] = parts[1]

        # MAC address from the first non-loopback interface
        try:
            result = subprocess.run(
                ["ip", "-o", "link", "show"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if "loopback" in line.lower() or " lo:" in line:
                    continue
                if "link/ether" in line:
                    parts_mac = line.split("link/ether")
                    if len(parts_mac) > 1:
                        mac = parts_mac[1].strip().split()[0].upper()
                        if mac and len(mac) == 17:
                            info["mac_address"] = mac
                            break
        except Exception:
            pass

        # OS info
        try:
            result = subprocess.run(
                ["cat", "/etc/os-release"], capture_output=True, text=True, timeout=5,
            )
            os_data = {}
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    os_data[key] = val.strip('"')
            info["operating_system"] = os_data.get("NAME", "Linux")
            info["os_version"] = os_data.get("VERSION", os_data.get("VERSION_ID", ""))
        except Exception:
            info["operating_system"] = "Linux"

        # Processor
        try:
            result = subprocess.run(
                ["grep", "-m1", "model name", "/proc/cpuinfo"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                info["processor"] = result.stdout.strip().split(":", 1)[1].strip()
            # CPU count
            result = subprocess.run(
                ["nproc"], capture_output=True, text=True, timeout=5,
            )
            cores = result.stdout.strip()
            if cores and info.get("processor"):
                info["processor"] = f"{info['processor']} ({cores} cores)"
        except Exception:
            pass

        # RAM
        try:
            result = subprocess.run(
                ["grep", "MemTotal", "/proc/meminfo"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                mem_kb = int(result.stdout.strip().split()[1])
                info["ram_gb"] = round(mem_kb / 1024 / 1024, 1)
        except Exception:
            pass

        # Storage
        try:
            result = subprocess.run(
                ["df", "--total", "-BG", "--output=size"],
                capture_output=True, text=True, timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            total_line = lines[-1].strip().replace("G", "")
            info["storage_gb"] = round(float(total_line), 0)
            # Detect storage type
            result2 = subprocess.run(
                ["cat", "/sys/block/sda/queue/rotational"],
                capture_output=True, text=True, timeout=5,
            )
            rot = result2.stdout.strip()
            if rot == "0":
                info["storage_type"] = "SSD"
            elif rot == "1":
                info["storage_type"] = "HDD"
        except Exception:
            pass

        # Serial number (requires root, may fail)
        try:
            result = subprocess.run(
                ["cat", "/sys/class/dmi/id/product_serial"],
                capture_output=True, text=True, timeout=5,
            )
            serial = result.stdout.strip()
            if serial and serial.lower() not in ("none", "not specified", "to be filled by o.e.m."):
                info["serial_number"] = serial
        except Exception:
            pass

        # Manufacturer / Model
        try:
            result = subprocess.run(
                ["cat", "/sys/class/dmi/id/sys_vendor"],
                capture_output=True, text=True, timeout=5,
            )
            vendor = result.stdout.strip()
            if vendor and vendor.lower() not in ("none", "to be filled by o.e.m."):
                info["manufacturer"] = vendor
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["cat", "/sys/class/dmi/id/product_name"],
                capture_output=True, text=True, timeout=5,
            )
            model = result.stdout.strip()
            if model and model.lower() not in ("none", "to be filled by o.e.m."):
                info["model"] = model
        except Exception:
            pass

    except Exception:
        pass
    return info


def _collect_ssh_system_info(ip, timeout=10):
    """Collect system info from remote host via SSH (passwordless/key-based only)."""
    info = {}
    commands = {
        "fqdn": "hostname -f 2>/dev/null || hostname",
        "os_info": "cat /etc/os-release 2>/dev/null | head -5",
        "processor": "grep -m1 'model name' /proc/cpuinfo 2>/dev/null",
        "cores": "nproc 2>/dev/null",
        "ram": "grep MemTotal /proc/meminfo 2>/dev/null",
        "storage": "df --total -BG --output=size 2>/dev/null | tail -1",
        "serial": "cat /sys/class/dmi/id/product_serial 2>/dev/null",
        "vendor": "cat /sys/class/dmi/id/sys_vendor 2>/dev/null",
        "model": "cat /sys/class/dmi/id/product_name 2>/dev/null",
        "rotational": "cat /sys/block/sda/queue/rotational 2>/dev/null",
        "mac": "ip -o link show 2>/dev/null | grep -v loopback | grep 'link/ether' | head -1",
    }

    # Build a single SSH command that runs all at once
    combined = " && ".join(
        f'echo "####{k}####" && {v}' for k, v in commands.items()
    )

    try:
        result = subprocess.run(
            [
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
                f"root@{ip}", combined,
            ],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            return info

        # Parse sections
        sections = {}
        current_key = None
        for line in result.stdout.split("\n"):
            if line.startswith("####") and line.endswith("####"):
                current_key = line.strip("#")
            elif current_key:
                sections.setdefault(current_key, []).append(line)

        # FQDN
        fqdn = "\n".join(sections.get("fqdn", [])).strip()
        if fqdn:
            info["fqdn"] = fqdn
            parts = fqdn.split(".", 1)
            if len(parts) > 1:
                info["domain"] = parts[1]

        # OS
        os_text = "\n".join(sections.get("os_info", []))
        os_data = {}
        for line in os_text.strip().split("\n"):
            if "=" in line:
                key, val = line.split("=", 1)
                os_data[key] = val.strip('"')
        if os_data:
            info["operating_system"] = os_data.get("NAME", "Linux")
            info["os_version"] = os_data.get("VERSION", os_data.get("VERSION_ID", ""))

        # Processor
        proc = "\n".join(sections.get("processor", [])).strip()
        if proc and ":" in proc:
            info["processor"] = proc.split(":", 1)[1].strip()
        cores = "\n".join(sections.get("cores", [])).strip()
        if cores and info.get("processor"):
            info["processor"] = f"{info['processor']} ({cores} cores)"

        # RAM
        ram = "\n".join(sections.get("ram", [])).strip()
        if ram and "MemTotal" in ram:
            try:
                mem_kb = int(ram.split()[1])
                info["ram_gb"] = round(mem_kb / 1024 / 1024, 1)
            except (IndexError, ValueError):
                pass

        # Storage
        storage = "\n".join(sections.get("storage", [])).strip().replace("G", "")
        if storage:
            try:
                info["storage_gb"] = round(float(storage), 0)
            except ValueError:
                pass

        rot = "\n".join(sections.get("rotational", [])).strip()
        if rot == "0":
            info["storage_type"] = "SSD"
        elif rot == "1":
            info["storage_type"] = "HDD"

        # Serial / Vendor / Model
        serial = "\n".join(sections.get("serial", [])).strip()
        if serial and serial.lower() not in ("none", "not specified", "to be filled by o.e.m.", ""):
            info["serial_number"] = serial
        vendor = "\n".join(sections.get("vendor", [])).strip()
        if vendor and vendor.lower() not in ("none", "to be filled by o.e.m.", ""):
            info["manufacturer"] = vendor
        model = "\n".join(sections.get("model", [])).strip()
        if model and model.lower() not in ("none", "to be filled by o.e.m.", ""):
            info["model"] = model

        # MAC
        mac_line = "\n".join(sections.get("mac", [])).strip()
        if mac_line and "link/ether" in mac_line:
            mac_parts = mac_line.split("link/ether")
            if len(mac_parts) > 1:
                mac = mac_parts[1].strip().split()[0].upper()
                if mac and len(mac) == 17:
                    info["mac_address"] = mac

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return info


def _collect_network_context(ip):
    """Collect network context (subnet, gateway) for an IP."""
    info = {}
    try:
        # Find the interface that owns this IP (or routes to it)
        # First check all interfaces for a direct match
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            for i, p in enumerate(parts):
                if p == "inet" and i + 1 < len(parts):
                    cidr = parts[i + 1]  # e.g. 172.16.16.20/24
                    if "/" in cidr:
                        addr_part = cidr.split("/")[0]
                        try:
                            net = ipaddress.IPv4Network(cidr, strict=False)
                            if ipaddress.IPv4Address(ip) in net:
                                info["subnet"] = str(net)
                                break
                        except ValueError:
                            pass
            if info.get("subnet"):
                break

        # Default gateway
        result3 = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result3.stdout.strip().split("\n"):
            if "default via" in line:
                gw = line.split("via")[1].strip().split()[0]
                info["gateway"] = gw
                break

    except Exception:
        pass
    return info


def _create_asset_from_discovery(host_info):
    """Create an IT Asset from discovery data if it doesn't already exist."""
    ip = host_info["ip"]

    # Check if asset with this IP already exists
    existing = frappe.db.exists("IT Asset", {"ip_address": ip})
    if existing:
        # Update existing asset with latest details
        update_fields = {"is_online": 1, "last_seen": now_datetime()}
        for fld in ("mac_address", "processor", "ram_gb", "storage_gb", "storage_type",
                     "operating_system", "os_version", "fqdn", "domain", "subnet",
                     "gateway", "serial_number", "manufacturer", "model"):
            val = host_info.get(fld)
            if val:
                update_fields[fld] = val
        frappe.db.set_value("IT Asset", existing, update_fields)
        return False

    asset_type_map = {
        "Server": "Server",
        "Workstation": "Workstation",
        "Printer": "Printer",
        "Network Device": "Network Device",
        "Access Point": "Network Device",
        "IP Camera": "Other",
        "Other": "Other",
    }

    category_map = {
        "Server": "Server",
        "Workstation": "Desktop",
        "Printer": "Printer",
        "Network Device": "Network Switch",
        "Access Point": "Access Point",
        "IP Camera": "Other",
        "Other": "Other",
    }

    device_type = host_info.get("device_type", "Other")
    hostname = host_info.get("hostname", "") or ip
    ports = host_info.get("ports", [])

    # Use collected OS info or guess from ports
    os_name = host_info.get("operating_system", "")
    if not os_name:
        if 22 in ports and 3389 not in ports:
            os_name = "Linux"
        elif 3389 in ports or 5985 in ports:
            os_name = "Windows"

    # Resolve category - use mapped value if it exists, else fallback
    category_name = category_map.get(device_type, "Other")
    if not frappe.db.exists("IT Asset Category", category_name):
        for fallback in ["Server", "Desktop", "Other"]:
            if frappe.db.exists("IT Asset Category", fallback):
                category_name = fallback
                break
        else:
            frappe.get_doc({"doctype": "IT Asset Category", "category_name": "Other"}).insert(ignore_permissions=True)
            category_name = "Other"

    try:
        asset_data = {
            "doctype": "IT Asset",
            "asset_name": f"Discovered - {hostname}",
            "asset_type": asset_type_map.get(device_type, "Other"),
            "category": category_name,
            "status": "Active",
            "ip_address": ip,
            "hostname": hostname,
            "is_online": 1,
            "last_seen": now_datetime(),
            "operating_system": os_name,
            "discovery_source": "Network Scan",
            "notes": f"Auto-discovered on {now_datetime().strftime('%Y-%m-%d %H:%M')}.\n"
                     f"Open ports: {', '.join(str(p) for p in ports) if ports else 'none'}.\n"
                     f"Device type guess: {device_type}.",
        }

        # Add all collected hardware/network details
        for fld in ("mac_address", "os_version", "processor", "ram_gb", "storage_gb",
                     "storage_type", "fqdn", "domain", "dns_name", "subnet", "gateway",
                     "serial_number", "manufacturer", "model"):
            val = host_info.get(fld)
            if val:
                asset_data[fld] = val

        # Use hostname as dns_name if we have fqdn
        if host_info.get("fqdn") and not host_info.get("dns_name"):
            asset_data["dns_name"] = host_info["fqdn"]

        doc = frappe.get_doc(asset_data)
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        return True
    except Exception as e:
        frappe.log_error(f"Auto-discovery asset creation failed for {ip}: {e}")
        return False
