import frappe
from frappe.utils import today, now_datetime, add_to_date


@frappe.whitelist()
def create_demo_data():
	"""Create sample QMS data for POC demonstration."""

	# ── QMS Settings ──
	if not frappe.db.exists("QMS Settings"):
		settings = frappe.new_doc("QMS Settings")
	else:
		settings = frappe.get_doc("QMS Settings")
	settings.enable_qms = 1
	settings.hospital_name = "Saint Joseph Hospital"
	settings.default_country_code = "+961"
	settings.default_language = "English"
	settings.enable_feedback = 1
	settings.enable_qr_code = 1
	settings.enable_online_booking = 1
	settings.data_retention_days = 365
	settings.save(ignore_permissions=True)

	# ── Locations ──
	locations = [
		{"location_name": "Main Hospital", "location_type": "Hospital", "is_active": 1},
		{"location_name": "Laboratory Department", "location_type": "Department", "is_active": 1, "parent_location": None},
		{"location_name": "Insurance Office", "location_type": "Department", "is_active": 1, "parent_location": None},
	]
	location_map = {}
	for loc in locations:
		if not frappe.db.exists("QMS Location", {"location_name": loc["location_name"]}):
			doc = frappe.new_doc("QMS Location")
			doc.update(loc)
			doc.insert(ignore_permissions=True)
			location_map[loc["location_name"]] = doc.name
		else:
			location_map[loc["location_name"]] = frappe.db.get_value(
				"QMS Location", {"location_name": loc["location_name"]}, "name"
			)

	# Link departments to main hospital
	main = location_map.get("Main Hospital")
	for dept in ["Laboratory Department", "Insurance Office"]:
		name = location_map.get(dept)
		if name and main:
			frappe.db.set_value("QMS Location", name, "parent_location", main)

	# ── Services (2-level hierarchy) ──
	services = [
		# Top-level
		{"service_name": "Laboratory", "service_code": "LAB", "ticket_prefix": "LAB",
		 "location": location_map.get("Laboratory Department"), "is_active": 1, "priority": 1,
		 "estimated_service_time": 15, "color": "#e74c3c"},
		{"service_name": "Insurance", "service_code": "INS", "ticket_prefix": "INS",
		 "location": location_map.get("Insurance Office"), "is_active": 1, "priority": 2,
		 "estimated_service_time": 10, "color": "#3498db"},
		{"service_name": "Reception", "service_code": "REC", "ticket_prefix": "R",
		 "location": location_map.get("Main Hospital"), "is_active": 1, "priority": 3,
		 "estimated_service_time": 5, "color": "#2ecc71"},
		# Sub-services
		{"service_name": "Blood Test", "service_code": "LAB-BLD", "ticket_prefix": "BLD",
		 "location": location_map.get("Laboratory Department"), "is_active": 1, "priority": 1,
		 "estimated_service_time": 20, "color": "#c0392b", "_parent_code": "LAB"},
		{"service_name": "Urine Test", "service_code": "LAB-URN", "ticket_prefix": "URN",
		 "location": location_map.get("Laboratory Department"), "is_active": 1, "priority": 2,
		 "estimated_service_time": 10, "color": "#e67e22", "_parent_code": "LAB"},
		{"service_name": "Insurance Verification", "service_code": "INS-VER", "ticket_prefix": "VER",
		 "location": location_map.get("Insurance Office"), "is_active": 1, "priority": 1,
		 "estimated_service_time": 8, "color": "#2980b9", "_parent_code": "INS"},
	]
	service_map = {}
	for svc in services:
		parent_code = svc.pop("_parent_code", None)
		if not frappe.db.exists("QMS Service", {"service_code": svc["service_code"]}):
			doc = frappe.new_doc("QMS Service")
			doc.update(svc)
			if parent_code and parent_code in service_map:
				doc.parent_service = service_map[parent_code]
			doc.insert(ignore_permissions=True)
			service_map[svc["service_code"]] = doc.name
		else:
			service_map[svc["service_code"]] = frappe.db.get_value(
				"QMS Service", {"service_code": svc["service_code"]}, "name"
			)

	# ── Counters ──
	counters_data = [
		{"counter_name": "Counter 1 - Lab", "counter_number": 1,
		 "location": location_map.get("Laboratory Department"),
		 "status": "Available", "is_active": 1,
		 "services": ["LAB", "LAB-BLD", "LAB-URN"]},
		{"counter_name": "Counter 2 - Lab", "counter_number": 2,
		 "location": location_map.get("Laboratory Department"),
		 "status": "Available", "is_active": 1,
		 "services": ["LAB", "LAB-BLD", "LAB-URN"]},
		{"counter_name": "Counter 3 - Insurance", "counter_number": 3,
		 "location": location_map.get("Insurance Office"),
		 "status": "Available", "is_active": 1,
		 "services": ["INS", "INS-VER"]},
		{"counter_name": "Counter 4 - Reception", "counter_number": 4,
		 "location": location_map.get("Main Hospital"),
		 "status": "Available", "is_active": 1,
		 "services": ["REC"]},
		{"counter_name": "Counter 5 - Reception", "counter_number": 5,
		 "location": location_map.get("Main Hospital"),
		 "status": "Available", "is_active": 1,
		 "services": ["REC"]},
	]
	counter_map = {}
	for ctr in counters_data:
		svc_codes = ctr.pop("services")
		if not frappe.db.exists("QMS Counter", {"counter_name": ctr["counter_name"]}):
			doc = frappe.new_doc("QMS Counter")
			doc.update(ctr)
			for code in svc_codes:
				if code in service_map:
					doc.append("services", {"service": service_map[code]})
			doc.insert(ignore_permissions=True)
			counter_map[ctr["counter_name"]] = doc.name
		else:
			counter_map[ctr["counter_name"]] = frappe.db.get_value(
				"QMS Counter", {"counter_name": ctr["counter_name"]}, "name"
			)

	# ── Sample Tickets (today) ──
	import random
	statuses_pool = ["Waiting", "Waiting", "Waiting", "Completed", "Completed",
	                 "Completed", "Completed", "Called", "Serving", "No Show"]
	svc_codes_for_tickets = ["LAB", "LAB-BLD", "LAB-URN", "INS", "INS-VER", "REC"]
	names_pool = [
		"Ahmad Haddad", "Sara El Khoury", "Nabil Mansour", "Layla Farah",
		"Omar Nassar", "Rima Saab", "Karim Jaber", "Nour Hajj",
		"Fadi Chouaib", "Maya Kanaan", "Tarek Salameh", "Dina Azar",
		"Ali Harb", "Hana Moussa", "Sami Rizk", "Lina Karam",
		"Jad Atallah", "Rana Bou Khalil", "Wael Gerges", "Mira Dagher",
	]

	existing_tickets = frappe.db.count("QMS Queue Ticket", {"token_date": today()})
	if existing_tickets < 5:
		for i, name in enumerate(names_pool):
			svc_code = svc_codes_for_tickets[i % len(svc_codes_for_tickets)]
			svc_name = service_map.get(svc_code)
			if not svc_name:
				continue
			svc_doc = frappe.get_doc("QMS Service", svc_name)
			status = statuses_pool[i % len(statuses_pool)]

			ticket = frappe.new_doc("QMS Queue Ticket")
			ticket.token_date = today()
			ticket.service = svc_name
			ticket.location = svc_doc.location
			ticket.patient_name = name
			ticket.patient_phone = f"+961 {random.randint(70000000, 79999999)}"
			ticket.status = status
			ticket.priority = "VIP" if i == 0 else ("High" if i == 3 else "Normal")
			ticket.source = random.choice(["Walk-in", "Kiosk", "QR Code"])
			ticket.check_in_time = add_to_date(now_datetime(), minutes=-(len(names_pool) - i) * 7)
			if status in ("Called", "Serving", "Completed"):
				ticket.called_time = add_to_date(ticket.check_in_time, minutes=random.randint(2, 10))
			if status in ("Serving", "Completed"):
				ticket.service_start_time = ticket.called_time
			if status == "Completed":
				ticket.service_end_time = add_to_date(ticket.service_start_time, minutes=random.randint(3, 15))
			ticket.insert(ignore_permissions=True)

	# ── Feedback Form Template ──
	if not frappe.db.exists("QMS Feedback Form Template", {"form_name": "Default Feedback"}):
		fb = frappe.new_doc("QMS Feedback Form Template")
		fb.form_name = "Default Feedback"
		fb.location = location_map.get("Main Hospital")
		fb.is_active = 1
		fb.append("feedback_fields", {
			"field_label": "Overall Experience",
			"field_type": "Rating",
			"is_required": 1,
			"sort_order": 1,
		})
		fb.append("feedback_fields", {
			"field_label": "Comments",
			"field_type": "Textarea",
			"is_required": 0,
			"sort_order": 2,
		})
		fb.append("actions", {
			"trigger_condition": "Rating Below Threshold",
			"threshold_value": 3,
			"action_type": "Create ToDo",
			"action_target": "Administrator",
			"action_message": "Low rating feedback received - follow up required",
		})
		fb.insert(ignore_permissions=True)

	# ── Display Screen Template ──
	if not frappe.db.exists("QMS Display Screen Template", {"template_name": "Main Display"}):
		ds = frappe.new_doc("QMS Display Screen Template")
		ds.template_name = "Main Display"
		ds.location = location_map.get("Main Hospital")
		ds.screen_type = "Queue Display"
		ds.language = "Both"
		ds.header_text = "Queue Display Board"
		ds.header_text_ar = "\u0644\u0648\u062d\u0629 \u0639\u0631\u0636 \u0627\u0644\u0637\u0627\u0628\u0648\u0631"
		ds.background_color = "#1a1a2e"
		ds.text_color = "#ffffff"
		ds.accent_color = "#e94560"
		ds.show_now_serving = 1
		ds.show_waiting_list = 1
		ds.max_tickets_displayed = 15
		ds.auto_refresh_interval = 5
		ds.insert(ignore_permissions=True)

	# ── Ticket Screen Settings ──
	if not frappe.db.exists("QMS Ticket Screen Settings", {"settings_name": "Default Ticket Screen"}):
		ts = frappe.new_doc("QMS Ticket Screen Settings")
		ts.settings_name = "Default Ticket Screen"
		ts.location = location_map.get("Main Hospital")
		ts.language = "Both"
		ts.header_text = "Welcome"
		ts.header_text_ar = "\u0645\u0631\u062d\u0628\u0627\u064b"
		ts.background_color = "#ffffff"
		ts.text_color = "#333333"
		ts.accent_color = "#5e64ff"
		ts.show_qr_code = 1
		ts.show_wait_time = 1
		ts.show_queue_position = 1
		ts.insert(ignore_permissions=True)

	frappe.db.commit()
	return "Demo data created successfully!"
