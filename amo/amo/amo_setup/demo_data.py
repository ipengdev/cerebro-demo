# Copyright (c) 2026, iPeng Holdings and contributors
# For license information, please see license.txt
"""
AMO Demo Data Generator
Creates realistic demo Employee records with all fields populated,
including Arabic translatable fields. All records use a [DEMO] prefix
for easy identification and cleanup.
"""

import random
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate

DEMO_PREFIX = "[DEMO]"

# ── Lebanese Names ────────────────────────────────────────────────────
MALE_FIRST_NAMES = [
	("Elie", "إيلي"),
	("Georges", "جورج"),
	("Tony", "طوني"),
	("Charbel", "شربل"),
	("Maroun", "مارون"),
	("Pierre", "بيار"),
	("Antoine", "أنطوان"),
	("Fadi", "فادي"),
	("Youssef", "يوسف"),
	("Michel", "ميشال"),
	("Hanna", "حنّا"),
	("Boutros", "بطرس"),
	("Sami", "سامي"),
	("Nabil", "نبيل"),
	("Karim", "كريم"),
	("Walid", "وليد"),
	("Rami", "رامي"),
	("Samir", "سمير"),
	("Elias", "إلياس"),
	("Tanios", "طانيوس"),
	("Habib", "حبيب"),
	("Ghassan", "غسّان"),
	("Nassim", "نسيم"),
	("Fouad", "فؤاد"),
	("Jamil", "جميل"),
]

FEMALE_FIRST_NAMES = [
	("Rania", "رانيا"),
	("Maria", "ماريا"),
	("Yara", "يارا"),
	("Nadia", "نادية"),
	("Layla", "ليلى"),
	("Maya", "مايا"),
	("Rita", "ريتا"),
	("Therese", "تيريز"),
	("Carla", "كارلا"),
	("Joelle", "جويل"),
	("Mirna", "ميرنا"),
	("Lina", "لينا"),
	("Samira", "سميرة"),
	("Hala", "هالة"),
	("Dina", "دينا"),
	("Noura", "نورا"),
	("Rima", "ريما"),
	("Zeina", "زينة"),
	("Patricia", "باتريسيا"),
	("Sandra", "ساندرا"),
	("Ghada", "غادة"),
	("Celine", "سيلين"),
	("Nadine", "نادين"),
	("Mona", "منى"),
	("Nayla", "نايلة"),
]

LAST_NAMES = [
	("Daher", "ضاهر"),
	("Khoury", "خوري"),
	("Haddad", "حدّاد"),
	("Frem", "فرام"),
	("Najjar", "نجّار"),
	("Mouawad", "معوّض"),
	("Gemayel", "الجميّل"),
	("Aoun", "عون"),
	("Sfeir", "صفير"),
	("Boustany", "بستاني"),
	("Saade", "سعادة"),
	("Salameh", "سلامة"),
	("Chamoun", "شمعون"),
	("Rizk", "رزق"),
	("Tabet", "تابت"),
	("Nasr", "نصر"),
	("Abi Khalil", "أبي خليل"),
	("El-Khoury", "الخوري"),
	("Barakat", "بركات"),
	("Makhlouf", "مخلوف"),
	("Hajj", "حاج"),
	("Abou Jaoude", "أبو جودة"),
	("Frangieh", "فرنجيّة"),
	("Geagea", "جعجع"),
	("Azar", "عازار"),
]

MOTHER_FIRST_NAMES = [
	("Maryam", "مريم"),
	("Aida", "عايدة"),
	("Souad", "سعاد"),
	("Lamia", "لمياء"),
	("Wafa", "وفاء"),
	("Dalal", "دلال"),
	("Hind", "هند"),
	("Sahar", "سحر"),
	("Najwa", "نجوى"),
	("Rawda", "روضة"),
]

FATHER_FIRST_NAMES = [
	("Joseph", "جوزيف"),
	("Boutros", "بطرس"),
	("Georges", "جورج"),
	("Antoine", "أنطوان"),
	("Mikhael", "ميخائيل"),
	("Hanna", "حنّا"),
	("Ibrahim", "إبراهيم"),
	("Elias", "إلياس"),
	("Youssef", "يوسف"),
	("Charbel", "شربل"),
]

LEBANESE_TOWNS = [
	("Beirut", "بيروت"),
	("Jounieh", "جونية"),
	("Byblos", "جبيل"),
	("Tripoli", "طرابلس"),
	("Sidon", "صيدا"),
	("Zahle", "زحلة"),
	("Batroun", "البترون"),
	("Antelias", "أنطلياس"),
	("Broummana", "برمّانا"),
	("Ehden", "إهدن"),
	("Beit Meri", "بيت مري"),
	("Dekwaneh", "الدكوانة"),
	("Jezzine", "جزّين"),
	("Baabda", "بعبدا"),
	("Zouk Mosbeh", "ذوق مصبح"),
]

NATIONALITIES = [
	("Lebanese", "لبنانيّة"),
]

UNIVERSITIES = [
	("Antonine University", "الجامعة الأنطونيّة"),
	("Saint Joseph University", "جامعة القدّيس يوسف"),
	("Lebanese University", "الجامعة اللبنانيّة"),
	("Holy Spirit University of Kaslik", "جامعة الروح القدس - الكسليك"),
	("Lebanese American University", "الجامعة اللبنانيّة الأميركيّة"),
	("Notre Dame University", "جامعة سيّدة اللويزة"),
	("Balamand University", "جامعة البلمند"),
]

DEGREES = [
	("Bachelor of Arts", "إجازة في الآداب"),
	("Bachelor of Science", "إجازة في العلوم"),
	("Master of Business Administration", "ماجستير إدارة أعمال"),
	("Master of Education", "ماجستير في التربية"),
	("License in Theology", "إجازة في اللاهوت"),
	("Bachelor of Engineering", "إجازة في الهندسة"),
	("Master of Computer Science", "ماجستير علوم الحاسوب"),
	("Diploma in Accounting", "دبلوم في المحاسبة"),
]

DESIGNATIONS = [
	"Teacher",
	"Administrator",
	"Accountant",
	"Secretary",
	"Librarian",
	"Maintenance Worker",
	"Cook",
	"Driver",
	"Guard",
	"IT Support",
	"HR Officer",
	"Finance Officer",
	"Project Manager",
	"Social Worker",
	"Nurse",
]

DEPARTMENTS = [
	"Administration",
	"Finance",
	"Human Resources",
	"IT",
	"Maintenance",
	"Education",
	"Social Services",
]

BANKS = [
	"Bank Audi",
	"Byblos Bank",
	"Blom Bank",
	"Bank of Beirut",
	"Banque Libano-Française",
	"Fransabank",
	"Credit Libanais",
	"Bankmed",
]

HOBBIES = [
	"Reading", "Hiking", "Swimming", "Photography", "Cooking",
	"Gardening", "Music", "Painting", "Chess", "Volleyball",
]

CLUBS = [
	"Antonine Sports Club", "Parish Youth Group", "Scouts of Lebanon",
	"Red Cross Lebanese", "Lions Club", "Rotary Club",
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Probation"]

# Branches per AMO organizational type
BRANCHES = [
	"Headquarters",
	"Monastery",
	"School Campus",
	"University Campus",
	"Social Center",
	"Cultural Center",
	"Parish",
	"Farm",
	"Retreat House",
]

# Employee Grades (hierarchy top→bottom)
EMPLOYEE_GRADES = [
	"G1 - Director",
	"G2 - Manager",
	"G3 - Senior Officer",
	"G4 - Officer",
	"G5 - Junior",
	"G6 - Trainee",
]

# Designation hierarchy levels (designation → grade mapping for reports_to logic)
DESIGNATION_LEVEL = {
	"Administrator": 1,
	"Project Manager": 2,
	"Finance Officer": 2,
	"HR Officer": 2,
	"IT Support": 3,
	"Accountant": 3,
	"Teacher": 3,
	"Social Worker": 3,
	"Nurse": 3,
	"Secretary": 4,
	"Librarian": 4,
	"Maintenance Worker": 5,
	"Cook": 5,
	"Driver": 5,
	"Guard": 5,
}

# Grade per level
LEVEL_TO_GRADE = {
	1: "G1 - Director",
	2: "G2 - Manager",
	3: "G3 - Senior Officer",
	4: "G4 - Officer",
	5: "G5 - Junior",
}

# ── Lebanese Leave Types (per Lebanese Labour Law) ────────────────────
# Reference: Lebanese Labour Code, Articles 39–42
LEBANESE_LEAVE_TYPES = [
	{
		"leave_type_name": "Annual Leave - إجازة سنوية",
		"max_leaves_allowed": 15,
		"is_carry_forward": 1,
		"maximum_carry_forwarded_leaves": 15,
		"expire_carry_forwarded_leaves_after_days": 365,
		"allow_encashment": 1,
		"non_encashable_leaves": 0,
		"include_holiday": 0,
		"allow_negative": 0,
		"is_earned_leave": 1,
		"earned_leave_frequency": "Monthly",
		"rounding": "0.5",
	},
	{
		"leave_type_name": "Sick Leave (Full Pay) - إجازة مرضية بأجر كامل",
		"max_leaves_allowed": 15,
		"is_carry_forward": 0,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Sick Leave (Half Pay) - إجازة مرضية بنصف أجر",
		"max_leaves_allowed": 15,
		"is_carry_forward": 0,
		"is_ppl": 1,
		"fraction_of_daily_salary_per_leave": 0.5,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Maternity Leave - إجازة أمومة",
		"max_leaves_allowed": 70,
		"is_carry_forward": 0,
		"include_holiday": 1,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Paternity Leave - إجازة أبوّة",
		"max_leaves_allowed": 1,
		"is_carry_forward": 0,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Marriage Leave - إجازة زواج",
		"max_leaves_allowed": 3,
		"is_carry_forward": 0,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Bereavement Leave - إجازة وفاة",
		"max_leaves_allowed": 3,
		"is_carry_forward": 0,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Pilgrimage Leave - إجازة حج",
		"max_leaves_allowed": 15,
		"is_carry_forward": 0,
		"include_holiday": 1,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Study Leave - إجازة دراسية",
		"max_leaves_allowed": 10,
		"is_carry_forward": 0,
		"include_holiday": 0,
		"allow_negative": 0,
	},
	{
		"leave_type_name": "Leave Without Pay - إجازة بدون راتب",
		"max_leaves_allowed": 0,
		"is_lwp": 1,
		"is_carry_forward": 0,
		"include_holiday": 1,
		"allow_negative": 1,
	},
]

LEAVE_POLICY_NAME = "Lebanese Standard Leave Policy"
LEAVE_PERIOD_TEMPLATE = "AMO Leave Period {year}"

# ── HR Lifecycle Constants ────────────────────────────────────────────

INTERVIEW_ROUNDS = [
	{"round_name": "Screening Call", "skills": ["Communication", "Motivation"]},
	{"round_name": "Technical Interview", "skills": ["Domain Knowledge", "Problem Solving", "Technical Skills"]},
	{"round_name": "HR Interview", "skills": ["Communication", "Teamwork", "Cultural Fit"]},
	{"round_name": "Final Round", "skills": ["Leadership", "Strategic Thinking"]},
]

JOB_DESCRIPTIONS = {
	"Administrator": "Oversee daily operations, manage teams, and ensure organizational objectives are met.",
	"Project Manager": "Plan, execute, and close projects within scope, budget, and timeline.",
	"Finance Officer": "Manage financial operations, reporting, budgeting, and compliance.",
	"HR Officer": "Handle recruitment, employee relations, policies, and HR administration.",
	"IT Support": "Provide technical support, maintain systems, and ensure IT infrastructure reliability.",
	"Accountant": "Prepare financial statements, manage accounts, and ensure accurate bookkeeping.",
	"Teacher": "Deliver curriculum, assess students, and contribute to educational programs.",
	"Social Worker": "Provide social services, counsel clients, and coordinate community programs.",
	"Nurse": "Deliver patient care, administer treatments, and maintain health records.",
	"Secretary": "Provide administrative support, manage correspondence, and organize schedules.",
	"Librarian": "Manage library collections, assist patrons, and organize information resources.",
	"Maintenance Worker": "Perform facility maintenance, repairs, and ensure safe working conditions.",
	"Cook": "Prepare meals, manage kitchen inventory, and maintain hygiene standards.",
	"Driver": "Provide transportation services, maintain vehicles, and ensure passenger safety.",
	"Guard": "Monitor premises, enforce security protocols, and ensure safety of personnel.",
}

KRA_DEFINITIONS = [
	("Job Performance", 30),
	("Teamwork & Collaboration", 20),
	("Communication Skills", 15),
	("Initiative & Problem Solving", 15),
	("Attendance & Punctuality", 10),
	("Professional Development", 10),
]

APPRAISAL_TEMPLATE_NAME = "AMO Standard Performance Review"
APPRAISAL_CYCLE_TEMPLATE = "AMO Performance Review {year}"

# ── Asset & Inventory Demo Constants ──────────────────────────────────

# Maps asset_category -> (fixed_asset_account_prefix, list of (asset_name_template, location, price_range))
ASSET_DEFINITIONS = {
	"IT Equipment": {
		"account_prefix": "Electronic Equipment",
		"items": [
			("Dell Latitude Laptop", "Office Building", (800_000, 2_500_000)),
			("HP LaserJet Printer", "Office Building", (400_000, 1_200_000)),
			("Server Rack", "Office Building", (3_000_000, 8_000_000)),
			("Cisco Network Switch", "Office Building", (500_000, 1_500_000)),
			("UPS Battery Backup", "Office Building", (200_000, 600_000)),
		],
	},
	"Furniture and Equipment": {
		"account_prefix": "Furniture and Fixtures",
		"items": [
			("Office Desk Set", "Office Building", (300_000, 900_000)),
			("Filing Cabinet", "Office Building", (150_000, 400_000)),
			("Conference Table", "Office Building", (500_000, 1_500_000)),
			("Bookshelf", "Library", (100_000, 350_000)),
			("Whiteboard", "Classroom Block A", (80_000, 200_000)),
		],
	},
	"Vehicles": {
		"account_prefix": "Capital Equipment",
		"items": [
			("Toyota Hiace Van", "Parking Lot", (25_000_000, 45_000_000)),
			("Hyundai H-1 Minibus", "Parking Lot", (30_000_000, 55_000_000)),
			("Kia Picanto", "Parking Lot", (12_000_000, 20_000_000)),
		],
	},
	"Buildings": {
		"account_prefix": "Buildings",
		"items": [
			("Main Building", "Main Building", (500_000_000, 2_000_000_000)),
			("Guest House", "Guest House", (100_000_000, 400_000_000)),
		],
	},
	"Library Books": {
		"account_prefix": "Office Equipment",
		"items": [
			("Library Collection - Theology", "Library", (5_000_000, 15_000_000)),
			("Library Collection - Education", "Library", (3_000_000, 10_000_000)),
		],
	},
	"Laboratory Equipment": {
		"account_prefix": "Capital Equipment",
		"items": [
			("Chemistry Lab Kit Set", "Laboratory", (2_000_000, 6_000_000)),
			("Microscope Set (10 units)", "Laboratory", (3_000_000, 8_000_000)),
		],
	},
}

MAINTENANCE_TASKS = [
	("Annual Inspection", "Preventive Maintenance", "Yearly"),
	("Quarterly Service", "Preventive Maintenance", "Quarterly"),
	("Monthly Calibration", "Calibration", "Monthly"),
]

# Stock items (existing items defined in system)
STOCK_ITEM_CODES = [
	"AMO-OFF-001",  # A4 Paper Ream
	"AMO-OFF-002",  # Pen Box (12pc)
	"AMO-OFF-003",  # Printer Toner
	"AMO-CLN-001",  # Cleaning Detergent
	"AMO-EDU-001",  # Textbook Set
	"AMO-EDU-002",  # Lab Kit
	"AMO-REL-001",  # Liturgical Candles (100pc)
	"AMO-AGR-001",  # Olive Oil (5L)
	"AMO-IT-001",   # Network Cable (50m)
	"AMO-MNT-001",  # Light Bulb LED
]

# prices in LBP per unit (approx)
STOCK_ITEM_PRICES = {
	"AMO-OFF-001": (15_000, 25_000),
	"AMO-OFF-002": (8_000, 15_000),
	"AMO-OFF-003": (60_000, 120_000),
	"AMO-CLN-001": (20_000, 40_000),
	"AMO-EDU-001": (50_000, 100_000),
	"AMO-EDU-002": (150_000, 300_000),
	"AMO-REL-001": (30_000, 60_000),
	"AMO-AGR-001": (40_000, 80_000),
	"AMO-IT-001": (25_000, 50_000),
	"AMO-MNT-001": (5_000, 12_000),
}

# Lebanese Mohafazat / Cazas for National ID
MOHAFAZA_CAZA = [
	("Beirut", "بيروت", "Beirut", "بيروت"),
	("Mount Lebanon", "جبل لبنان", "Keserwan", "كسروان"),
	("Mount Lebanon", "جبل لبنان", "Metn", "المتن"),
	("Mount Lebanon", "جبل لبنان", "Baabda", "بعبدا"),
	("Mount Lebanon", "جبل لبنان", "Chouf", "الشوف"),
	("Mount Lebanon", "جبل لبنان", "Jbeil", "جبيل"),
	("North Lebanon", "لبنان الشمالي", "Tripoli", "طرابلس"),
	("North Lebanon", "لبنان الشمالي", "Batroun", "البترون"),
	("North Lebanon", "لبنان الشمالي", "Zgharta", "زغرتا"),
	("North Lebanon", "لبنان الشمالي", "Bsharri", "بشرّي"),
	("South Lebanon", "لبنان الجنوبي", "Sidon", "صيدا"),
	("South Lebanon", "لبنان الجنوبي", "Jezzine", "جزّين"),
	("Bekaa", "البقاع", "Zahle", "زحلة"),
	("Bekaa", "البقاع", "West Bekaa", "البقاع الغربي"),
]

REGISTER_PLACES = [
	("Jounieh", "جونية"),
	("Antelias", "أنطلياس"),
	("Byblos", "جبيل"),
	("Broummana", "برمّانا"),
	("Ehden", "إهدن"),
	("Zahle", "زحلة"),
	("Sidon", "صيدا"),
	("Tripoli", "طرابلس"),
	("Batroun", "البترون"),
	("Dekwaneh", "الدكوانة"),
]

PASSPORT_PLACES_OF_ISSUE = [
	("Beirut", "بيروت"),
	("Tripoli", "طرابلس"),
	("Jounieh", "جونية"),
	("Zahle", "زحلة"),
]

PROFESSIONS_PASSPORT = [
	("Employee", "موظّف"),
	("Teacher", "أستاذ"),
	("Engineer", "مهندس"),
	("Accountant", "محاسب"),
	("Administrator", "إداري"),
	("Nurse", "ممرّض"),
]


def _publish(event, stage, percent, done=False):
	frappe.publish_realtime(event, {"stage": stage, "percent": percent, "done": done})


def _get_settings():
	"""Return AMO Settings values."""
	return frappe.get_single("AMO Settings")


def _random_date(start_year, end_year):
	start = date(start_year, 1, 1)
	end = date(end_year, 12, 31)
	delta = (end - start).days
	return start + timedelta(days=random.randint(0, delta))


def _random_phone():
	prefix = random.choice(["03", "70", "71", "76", "78", "79", "81"])
	return f"+961 {prefix} {random.randint(100000, 999999)}"


def _random_iban():
	"""Generate a valid-format Lebanese IBAN (28 chars: LB + 2 check + 4 bank + 20 account)."""
	check = random.randint(10, 99)
	bank_code = f"{random.randint(1, 99):04d}"
	account = ''.join([str(random.randint(0, 9)) for _ in range(20)])
	return f"LB{check}{bank_code}{account}"


def _get_companies():
	"""Return AMO companies or the selected one from settings."""
	settings = _get_settings()
	if settings.default_company:
		return [settings.default_company]
	companies = frappe.get_all("Company", filters={"name": ("like", "AMO%")}, pluck="name")
	return companies or [frappe.defaults.get_defaults().get("company")]


def _ensure_link_value(doctype, name, **kwargs):
	"""Create a record if it doesn't exist, return the name."""
	if not frappe.db.exists(doctype, name):
		field_map = {
			"Designation": "designation_name",
			"Department": "department_name",
			"Branch": "branch",
		}
		values = {"doctype": doctype, **kwargs}
		name_field = field_map.get(doctype)
		if name_field:
			values[name_field] = name
		# Employee Grade uses Prompt autoname — must set __newname
		if doctype == "Employee Grade":
			values["__newname"] = name
		doc = frappe.get_doc(values)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_if_duplicate=True)
	return name


def _build_employee(idx, companies, fill_all, fill_translatable):
	"""Build a single employee dict with all fields populated."""
	gender = random.choice(["Male", "Female"])
	if gender == "Male":
		first_en, first_ar = random.choice(MALE_FIRST_NAMES)
	else:
		first_en, first_ar = random.choice(FEMALE_FIRST_NAMES)

	last_en, last_ar = random.choice(LAST_NAMES)
	mother_first_en, mother_first_ar = random.choice(MOTHER_FIRST_NAMES)
	mother_last_en, mother_last_ar = random.choice(LAST_NAMES)
	father_first_en, father_first_ar = random.choice(FATHER_FIRST_NAMES)
	father_last_en, father_last_ar = random.choice(LAST_NAMES)
	maiden_en, maiden_ar = random.choice(LAST_NAMES) if gender == "Female" else ("", "")
	town_en, town_ar = random.choice(LEBANESE_TOWNS)
	nat_en, nat_ar = NATIONALITIES[0]

	company = random.choice(companies)
	dob = _random_date(1970, 2000)
	doj = _random_date(2015, 2025)

	emp = {
		"doctype": "Employee",
		"naming_series": "HR-EMP-",
		"employee_number": f"{DEMO_PREFIX}-{idx:04d}",
		"first_name": first_en,
		"last_name": last_en,
		"gender": gender,
		"date_of_birth": str(dob),
		"date_of_joining": str(doj),
		"status": "Active",
		"company": company,
	}

	# Translatable fields
	if fill_translatable:
		# Store Arabic in the translation table for first_name, last_name
		emp["_translations"] = {
			"first_name": {"ar": first_ar},
			"last_name": {"ar": last_ar},
		}

	# Family info (always visible in overview tab)
	emp["mother_first_name"] = mother_first_en
	emp["mother_last_name"] = mother_last_en
	emp["father_first_name"] = father_first_en
	emp["father_last_name"] = father_last_en
	if gender == "Female":
		emp["maiden_name"] = maiden_en

	# Details section
	emp["country_of_birth"] = "Lebanon"
	emp["town_of_birth"] = town_en
	emp["nationality"] = nat_en
	emp["financial_number"] = str(random.randint(100000, 999999))
	emp["social_security_number"] = str(random.randint(100000, 999999))

	# Salutation
	emp["salutation"] = random.choice(["Mr", "Mrs", "Ms"]) if gender == "Female" else "Mr"

	# Company details
	designation = random.choice(DESIGNATIONS)
	_ensure_link_value("Designation", designation)
	emp["designation"] = designation
	emp["employment_type"] = random.choice(EMPLOYMENT_TYPES)

	# Branch
	branch = random.choice(BRANCHES)
	_ensure_link_value("Branch", branch)
	emp["branch"] = branch

	# Employee Grade (based on designation level)
	level = DESIGNATION_LEVEL.get(designation, 4)
	grade = LEVEL_TO_GRADE.get(level, "G4 - Officer")
	_ensure_link_value("Employee Grade", grade)
	emp["grade"] = grade

	# Department — use existing departments for the company
	company_abbr = frappe.db.get_value("Company", company, "abbr") or ""
	existing_depts = frappe.get_all(
		"Department",
		filters={"company": company, "is_group": 0},
		pluck="name",
		limit=20,
	)
	if existing_depts:
		emp["department"] = random.choice(existing_depts)

	if fill_all:
		# Joining tab
		emp["scheduled_confirmation_date"] = str(doj - timedelta(days=random.randint(30, 90)))
		emp["final_confirmation_date"] = str(doj + timedelta(days=random.randint(60, 180)))
		emp["notice_number_of_days"] = random.choice([30, 60, 90])
		emp["date_of_retirement"] = str(date(dob.year + 64, dob.month, dob.day))

		# Contact details
		emp["cell_number"] = _random_phone()
		email_first = first_en.lower().replace(" ", ".")
		email_last = last_en.lower().replace(" ", ".")
		emp["personal_email"] = f"{email_first}.{email_last}.demo@example.com"
		emp["company_email"] = f"{email_first}.{email_last}.demo@amo.org.lb"
		emp["prefered_contact_email"] = "Company Email"

		# Address
		street_num = random.randint(1, 200)
		emp["current_address"] = f"{street_num} {town_en} Main Street, Lebanon"
		emp["current_accommodation_type"] = random.choice(["Rented", "Owned"])
		emp["permanent_address"] = f"{street_num} {town_en} Main Street, Lebanon"
		emp["permanent_accommodation_type"] = random.choice(["Rented", "Owned"])

		# Emergency contact
		ec_first, _ = random.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES)
		ec_last, _ = random.choice(LAST_NAMES)
		emp["person_to_be_contacted"] = f"{ec_first} {ec_last}"
		emp["emergency_phone_number"] = _random_phone()
		emp["relation"] = random.choice(["Spouse", "Parent", "Sibling", "Friend"])

		# Salary
		emp["salary_mode"] = "Bank"
		emp["salary_currency"] = "LBP"
		emp["ctc"] = random.choice([2000000, 3000000, 5000000, 8000000, 12000000, 18000000])
		emp["bank_name"] = random.choice(BANKS)
		emp["bank_ac_no"] = str(random.randint(10000000, 99999999))

		# Personal details
		emp["marital_status"] = random.choice(["Single", "Married", "Divorced", "Widowed"])
		emp["blood_group"] = random.choice(BLOOD_GROUPS)
		emp["military_service"] = random.choice(["Completed", "Exempted", "Postponed", "Not Applicable"])
		if emp["military_service"] == "Completed":
			emp["military_service_completion_date"] = str(_random_date(2005, 2020))
		emp["health_details"] = random.choice([
			"No known conditions",
			"Mild asthma, controlled",
			"Requires prescription glasses",
			"No allergies",
		])
		emp["family_background"] = random.choice([
			"Married with 2 children",
			"Single",
			"Married with 3 children",
			"Divorced, 1 child",
			"Widowed",
		])

		# Hobbies & social
		emp["hobbies"] = ", ".join(random.sample(HOBBIES, k=random.randint(1, 3)))
		emp["club"] = random.choice(CLUBS)

		# Education (child table)
		uni_en, uni_ar = random.choice(UNIVERSITIES)
		deg_en, deg_ar = random.choice(DEGREES)
		grad_year = str(doj.year - random.randint(1, 10))
		emp["education"] = [{
			"school_univ": uni_en,
			"qualification": deg_en,
			"year_of_passing": grad_year,
			"class_per": str(random.choice(["Distinction", "First Class", "Second Class"])),
		}]
		# Some employees have 2 degrees
		if random.random() > 0.5:
			uni2_en, uni2_ar = random.choice(UNIVERSITIES)
			deg2_en, deg2_ar = random.choice(DEGREES)
			emp["education"].append({
				"school_univ": uni2_en,
				"qualification": deg2_en,
				"year_of_passing": str(int(grad_year) - random.randint(2, 5)),
				"class_per": str(random.choice(["Distinction", "First Class", "Second Class"])),
			})

		# Work history (child table)
		if random.random() > 0.4:
			prev_company = random.choice([
				"Lebanese Red Cross", "Ministry of Education",
				"Beirut International School", "Bank Audi SAL",
				"MEA - Middle East Airlines", "Francophone University of Lebanon",
			])
			emp["external_work_history"] = [{
				"company_name": prev_company,
				"designation": random.choice(DESIGNATIONS),
				"total_experience": random.randint(1, 10),
			}]

		# Bio / profile
		emp["bio"] = (
			f"<p>{first_en} {last_en} is a dedicated professional from {town_en}, Lebanon. "
			f"Joined the Antonine Maronite Order in {doj.year}.</p>"
		)

		# ── Personal Details child tables ──

		# Marital Status History
		marital = emp["marital_status"]
		marital_from = str(doj - timedelta(days=random.randint(0, 365)))
		emp["marital_status_history"] = [{
			"marital_status": marital,
			"from_date": marital_from,
		}]
		if marital == "Divorced":
			emp["marital_status_history"].insert(0, {
				"marital_status": "Married",
				"from_date": str(_random_date(doj.year - 5, doj.year - 1)),
				"to_date": marital_from,
			})

		# Passport Detail
		passport_issue = _random_date(2018, 2024)
		passport_expiry = date(passport_issue.year + 10, passport_issue.month, passport_issue.day)
		pp_place_en, pp_place_ar = random.choice(PASSPORT_PLACES_OF_ISSUE)
		prof_en, prof_ar = random.choice(PROFESSIONS_PASSPORT)
		emp["passport_detail"] = [{
			"passport_number": f"RL{random.randint(1000000, 9999999)}",
			"valid_upto": str(passport_expiry),
			"passport_first_name": first_en,
			"passport_last_name": last_en,
			"place_of_issue": pp_place_en,
			"date_of_issue": str(passport_issue),
			"passport_father_name": father_first_en,
			"passport_date_of_birth": str(dob),
			"place_of_birth": town_en,
			"profession": prof_en,
		}]

		# National ID
		moh_en, moh_ar, caza_en, caza_ar = random.choice(MOHAFAZA_CAZA)
		reg_en, reg_ar = random.choice(REGISTER_PLACES)
		nid_from = _random_date(2015, 2022)
		emp["national_id"] = [{
			"national_id_number": str(random.randint(100000, 999999)),
			"mohafaza": moh_en,
			"caza": caza_en,
			"register_place": reg_en,
			"register_number": str(random.randint(100, 9999)),
			"from_date": str(nid_from),
			"to_date": str(date(nid_from.year + 10, nid_from.month, nid_from.day)),
		}]

		# Religion Detail (AMO = Maronite Christian order)
		emp["religion_detail"] = [{
			"religion": "Christian",
			"rite": "Maronite",
			"from_date": str(dob),
		}]

	# Arabic translations stored via _translations dict
	if fill_translatable:
		trans = emp.get("_translations", {})
		trans["mother_first_name"] = {"ar": mother_first_ar}
		trans["mother_last_name"] = {"ar": mother_last_ar}
		trans["father_first_name"] = {"ar": father_first_ar}
		trans["father_last_name"] = {"ar": father_last_ar}
		trans["country_of_birth"] = {"ar": "لبنان"}
		trans["town_of_birth"] = {"ar": town_ar}
		trans["nationality"] = {"ar": nat_ar}
		if gender == "Female" and maiden_ar:
			trans["maiden_name"] = {"ar": maiden_ar}
		if fill_all:
			trans["person_to_be_contacted"] = {"ar": ""}  # generic
			# Passport translatable fields
			trans["_passport_first_name"] = {"ar": first_ar, "_source": first_en}
			trans["_passport_last_name"] = {"ar": last_ar, "_source": last_en}
			trans["_passport_father_name"] = {"ar": father_first_ar, "_source": father_first_en}
			trans["_passport_place_of_birth"] = {"ar": town_ar, "_source": town_en}
			trans["_passport_profession"] = {"ar": prof_ar, "_source": prof_en}
			trans["_passport_place_of_issue"] = {"ar": pp_place_ar, "_source": pp_place_en}
			# National ID translatable fields
			trans["_nid_mohafaza"] = {"ar": moh_ar, "_source": moh_en}
			trans["_nid_caza"] = {"ar": caza_ar, "_source": caza_en}
			trans["_nid_register_place"] = {"ar": reg_ar, "_source": reg_en}
		emp["_translations"] = trans

	return emp


def _save_translations(employee_doc, translations):
	"""Save translated field values in Frappe's Translation doctype."""
	for fieldname, lang_map in translations.items():
		# Child table fields use _source key for source text
		source_text = lang_map.pop("_source", None) or str(employee_doc.get(fieldname) or "")
		if not source_text:
			continue
		for lang, translated_text in lang_map.items():
			if not translated_text:
				continue
			# Check if translation already exists
			exists = frappe.db.exists("Translation", {
				"source_text": source_text,
				"language": lang,
			})
			if not exists:
				frappe.get_doc({
					"doctype": "Translation",
					"source_text": source_text,
					"translated_text": translated_text,
					"language": lang,
					"contributed": 0,
				}).insert(ignore_permissions=True)


def _assign_reporting_hierarchy():
	"""Build a reports_to hierarchy for demo employees grouped by company.

	Logic: within each company, sort employees by designation level
	(lower number = higher rank). The top person has no reports_to.
	Everyone else reports to the nearest higher-ranked employee in the same company.
	"""
	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%"), "status": "Active"},
		fields=["name", "company", "designation"],
	)

	# Group by company
	by_company = {}
	for emp in demo_employees:
		by_company.setdefault(emp.company, []).append(emp)

	for company, emps in by_company.items():
		# Sort by designation level (1=highest / Director first)
		emps.sort(key=lambda e: DESIGNATION_LEVEL.get(e.designation, 4))

		if not emps:
			continue

		# First employee is the top — no reports_to
		frappe.db.set_value("Employee", emps[0].name, "reports_to", None, update_modified=False)

		# Build a chain: each level reports to the first person found at a higher level
		managers = [emps[0]]  # stack of potential managers (highest first)
		for emp in emps[1:]:
			emp_level = DESIGNATION_LEVEL.get(emp.designation, 4)
			# Find the closest manager whose level is strictly above this employee
			manager = managers[0]  # default to top person
			for m in reversed(managers):
				m_level = DESIGNATION_LEVEL.get(m.designation, 4)
				if m_level < emp_level:
					manager = m
					break
			frappe.db.set_value("Employee", emp.name, "reports_to", manager.name, update_modified=False)
			managers.append(emp)

	frappe.db.commit()


# ── Leave Types, Policy, Allocation & Attendance helpers ──────────────


def _ensure_lebanese_leave_types():
	"""Create Lebanese leave types if they don't exist. Returns list of names."""
	names = []
	for lt_data in LEBANESE_LEAVE_TYPES:
		lt_name = lt_data["leave_type_name"]
		if not frappe.db.exists("Leave Type", lt_name):
			doc = frappe.get_doc({"doctype": "Leave Type", **lt_data})
			doc.flags.ignore_permissions = True
			doc.insert(ignore_if_duplicate=True)
		names.append(lt_name)
	return names


def _ensure_leave_policy():
	"""Create and submit the standard Lebanese leave policy. Returns policy name."""
	# Check for existing submitted policy with same title
	existing = frappe.db.get_value(
		"Leave Policy", {"title": LEAVE_POLICY_NAME, "docstatus": 1}, "name"
	)
	if existing:
		return existing

	# Also check draft
	draft = frappe.db.get_value(
		"Leave Policy", {"title": LEAVE_POLICY_NAME, "docstatus": 0}, "name"
	)
	if draft:
		doc = frappe.get_doc("Leave Policy", draft)
		doc.flags.ignore_permissions = True
		doc.submit()
		return doc.name

	# Policy detail rows — only allocatable leave types (not LWP, not event-based)
	allocatable = [
		("Annual Leave - إجازة سنوية", 15),
		("Sick Leave (Full Pay) - إجازة مرضية بأجر كامل", 15),
		("Sick Leave (Half Pay) - إجازة مرضية بنصف أجر", 15),
		("Study Leave - إجازة دراسية", 10),
	]

	details = []
	for lt_name, annual in allocatable:
		details.append({"leave_type": lt_name, "annual_allocation": annual})

	doc = frappe.get_doc({
		"doctype": "Leave Policy",
		"title": LEAVE_POLICY_NAME,
		"leave_policy_details": details,
	})
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	return doc.name


def _ensure_leave_period(company, year):
	"""Create an active Leave Period for the given company/year. Returns name."""
	period_name = LEAVE_PERIOD_TEMPLATE.format(year=year)
	# Leave Period is not a simple name lookup — search by company + dates
	existing = frappe.db.get_value(
		"Leave Period",
		{"company": company, "from_date": f"{year}-01-01", "to_date": f"{year}-12-31"},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc({
		"doctype": "Leave Period",
		"from_date": f"{year}-01-01",
		"to_date": f"{year}-12-31",
		"company": company,
		"is_active": 1,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_if_duplicate=True)
	return doc.name


def _create_leave_allocations(demo_employees, policy_name, year):
	"""Create leave allocations for demo employees based on the leave policy."""
	policy = frappe.get_doc("Leave Policy", policy_name)
	from_date = f"{year}-01-01"
	to_date = f"{year}-12-31"

	for emp_name in demo_employees:
		emp = frappe.get_doc("Employee", emp_name)
		for detail in policy.leave_policy_details:
			# Skip if allocation already exists
			exists = frappe.db.exists("Leave Allocation", {
				"employee": emp_name,
				"leave_type": detail.leave_type,
				"from_date": from_date,
				"to_date": to_date,
				"docstatus": 1,
			})
			if exists:
				continue

			alloc = frappe.get_doc({
				"doctype": "Leave Allocation",
				"employee": emp_name,
				"leave_type": detail.leave_type,
				"from_date": from_date,
				"to_date": to_date,
				"new_leaves_allocated": detail.annual_allocation,
				"carry_forward": 0,
			})
			alloc.flags.ignore_permissions = True
			alloc.flags.ignore_mandatory = True
			alloc.insert()
			alloc.submit()


def _get_holiday_dates(holiday_list_name, year):
	"""Return a set of holiday dates for the given holiday list and year."""
	holidays = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list_name, "holiday_date": ("between", [f"{year}-01-01", f"{year}-12-31"])},
		pluck="holiday_date",
	)
	return {getdate(d) for d in holidays}


def _generate_attendance_and_leaves(demo_employees, year):
	"""Generate attendance and leave application records for demo employees.

	For each employee, generates daily attendance from Jan 1 to today (or Dec 31),
	with realistic patterns:
	- ~3-8 sick days spread across the year
	- ~8-15 annual leave days (1-2 blocks of vacation)
	- Remaining working days = Present
	- Holidays and Sundays = skip (no attendance)
	"""
	today = getdate(nowdate())
	year_start = date(year, 1, 1)
	year_end = min(date(year, 12, 31), today)

	if year_start > today:
		return

	total = len(demo_employees)
	for idx, emp_name in enumerate(demo_employees):
		try:
			_generate_employee_attendance(emp_name, year_start, year_end)
		except Exception as e:
			frappe.log_error(f"Attendance for {emp_name}: {e}", "AMO Demo Data")

		if (idx + 1) % 5 == 0 or idx + 1 == total:
			pct = int((idx + 1) / total * 80) + 20  # 20-100% range (first 20% was employee creation)
			_publish("amo_demo_progress", f"Generating attendance {idx + 1}/{total}…", pct)

	frappe.db.commit()


def _generate_employee_attendance(emp_name, start_date, end_date):
	"""Generate attendance + leave applications for a single employee."""
	emp = frappe.get_doc("Employee", emp_name)
	company = emp.company

	# Get holiday list
	holiday_list = emp.holiday_list or frappe.db.get_value("Company", company, "default_holiday_list")
	if not holiday_list:
		return

	year = start_date.year
	holiday_dates = _get_holiday_dates(holiday_list, year)

	# Employee's actual start — don't generate attendance before joining
	emp_start = max(start_date, getdate(emp.date_of_joining))
	if emp_start > end_date:
		return

	# Build list of working days
	working_days = []
	current = emp_start
	while current <= end_date:
		if current not in holiday_dates and current.weekday() != 6:  # Sunday = 6
			working_days.append(current)
		current += timedelta(days=1)

	if not working_days:
		return

	# Plan leave days
	sick_leave_type = "Sick Leave (Full Pay) - إجازة مرضية بأجر كامل"
	annual_leave_type = "Annual Leave - إجازة سنوية"

	# Check allocations exist
	has_sick = frappe.db.exists("Leave Allocation", {
		"employee": emp_name, "leave_type": sick_leave_type, "docstatus": 1,
	})
	has_annual = frappe.db.exists("Leave Allocation", {
		"employee": emp_name, "leave_type": annual_leave_type, "docstatus": 1,
	})

	# Pick random sick days (3-8 scattered single days)
	num_sick = random.randint(3, min(8, len(working_days) // 10 + 1))
	sick_days = set()
	if has_sick and len(working_days) > 20:
		sick_candidates = random.sample(working_days, min(num_sick, len(working_days)))
		sick_days = set(sick_candidates)

	# Pick annual leave blocks (1-2 vacation blocks of 3-7 consecutive working days)
	annual_days = set()
	if has_annual and len(working_days) > 40:
		num_blocks = random.randint(1, 2)
		for _ in range(num_blocks):
			block_len = random.randint(3, 7)
			# Find a start index that gives us a block
			max_start = len(working_days) - block_len
			if max_start <= 0:
				break
			start_idx = random.randint(0, max_start)
			for j in range(block_len):
				d = working_days[start_idx + j]
				if d not in sick_days:
					annual_days.add(d)

	# Create leave applications for contiguous blocks
	_create_leave_applications_for_days(emp_name, company, sick_days, sick_leave_type, holiday_dates)
	_create_leave_applications_for_days(emp_name, company, annual_days, annual_leave_type, holiday_dates)

	all_leave_days = sick_days | annual_days

	# Create attendance records
	for day in working_days:
		# Skip if attendance already exists
		if frappe.db.exists("Attendance", {"employee": emp_name, "attendance_date": str(day)}):
			continue

		status = "Present"
		leave_type = None
		if day in sick_days:
			status = "On Leave"
			leave_type = sick_leave_type
		elif day in annual_days:
			status = "On Leave"
			leave_type = annual_leave_type

		att = frappe.get_doc({
			"doctype": "Attendance",
			"employee": emp_name,
			"attendance_date": str(day),
			"status": status,
			"company": company,
		})
		if leave_type:
			att.leave_type = leave_type
		att.flags.ignore_permissions = True
		att.flags.ignore_mandatory = True
		att.insert()
		att.submit()


def _create_leave_applications_for_days(emp_name, company, leave_days, leave_type, holiday_dates):
	"""Group leave days into contiguous blocks and create Leave Applications."""
	if not leave_days:
		return

	sorted_days = sorted(leave_days)

	# Group into contiguous blocks (allowing holidays/Sundays in between)
	blocks = []
	block_start = sorted_days[0]
	block_end = sorted_days[0]

	for i in range(1, len(sorted_days)):
		# Check if this day is "contiguous" — within 3 calendar days of prev
		# (allows weekends/holidays in between)
		gap = (sorted_days[i] - block_end).days
		if gap <= 3:
			block_end = sorted_days[i]
		else:
			blocks.append((block_start, block_end))
			block_start = sorted_days[i]
			block_end = sorted_days[i]
	blocks.append((block_start, block_end))

	for from_date, to_date in blocks:
		# Skip if overlapping application exists
		exists = frappe.db.exists("Leave Application", {
			"employee": emp_name,
			"leave_type": leave_type,
			"from_date": str(from_date),
			"to_date": str(to_date),
			"docstatus": 1,
		})
		if exists:
			continue

		try:
			la = frappe.get_doc({
				"doctype": "Leave Application",
				"employee": emp_name,
				"leave_type": leave_type,
				"from_date": str(from_date),
				"to_date": str(to_date),
				"company": company,
				"status": "Approved",
				"posting_date": str(from_date),
				"description": f"Demo {leave_type.split(' - ')[0].lower()}",
				"follow_via_email": 0,
			})
			la.flags.ignore_permissions = True
			la.flags.ignore_mandatory = True
			la.flags.ignore_validate = True
			la.insert()
			la.submit()
		except Exception as e:
			frappe.log_error(f"Leave app {emp_name} {leave_type} {from_date}: {e}", "AMO Demo Data")


def _cleanup_leave_and_attendance():
	"""Delete all leave/attendance records for demo employees, plus demo leave types/policy/period."""
	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%")},
		pluck="name",
	)

	# Delete submittable docs by cancelling then deleting
	for emp_name in demo_employees:
		for dt in ("Leave Application", "Attendance", "Leave Allocation", "Leave Policy Assignment"):
			if not frappe.db.table_exists(f"tab{dt}"):
				continue
			records = frappe.get_all(dt, filters={"employee": emp_name}, fields=["name", "docstatus"])
			for r in records:
				try:
					if r.docstatus == 1:
						doc = frappe.get_doc(dt, r.name)
						doc.flags.ignore_permissions = True
						doc.cancel()
					frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)
				except Exception:
					# Force delete if cancel fails
					frappe.db.set_value(dt, r.name, "docstatus", 2, update_modified=False)
					frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)

	# Delete Leave Policy
	policies = frappe.get_all(
		"Leave Policy", filters={"title": LEAVE_POLICY_NAME}, fields=["name", "docstatus"]
	)
	for p in policies:
		try:
			if p.docstatus == 1:
				doc = frappe.get_doc("Leave Policy", p.name)
				doc.flags.ignore_permissions = True
				doc.cancel()
			frappe.delete_doc("Leave Policy", p.name, force=True, ignore_permissions=True)
		except Exception:
			frappe.db.set_value("Leave Policy", p.name, "docstatus", 2, update_modified=False)
			frappe.delete_doc("Leave Policy", p.name, force=True, ignore_permissions=True)

	# Delete Leave Periods created by demo
	periods = frappe.get_all(
		"Leave Period",
		filters={"name": ("like", "AMO Leave Period%")},
		pluck="name",
	)
	for p in periods:
		try:
			frappe.delete_doc("Leave Period", p, force=True, ignore_permissions=True)
		except Exception:
			pass

	# Delete demo leave types
	for lt_data in LEBANESE_LEAVE_TYPES:
		lt_name = lt_data["leave_type_name"]
		if frappe.db.exists("Leave Type", lt_name):
			try:
				frappe.delete_doc("Leave Type", lt_name, force=True, ignore_permissions=True)
			except Exception:
				pass

	frappe.db.commit()


# ── HR Lifecycle helpers (Recruitment + Appraisal) ────────────────────


def _ensure_skills():
	"""Create Skill records used in interview rounds."""
	skill_names = set()
	for ir in INTERVIEW_ROUNDS:
		skill_names.update(ir["skills"])
	for name in skill_names:
		if not frappe.db.exists("Skill", name):
			frappe.get_doc({"doctype": "Skill", "skill_name": name}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)


def _ensure_interview_rounds():
	"""Create Interview Round records. Returns list of round names."""
	_ensure_skills()
	names = []
	for ir_data in INTERVIEW_ROUNDS:
		rnd_name = ir_data["round_name"]
		if not frappe.db.exists("Interview Round", rnd_name):
			doc = frappe.get_doc({
				"doctype": "Interview Round",
				"round_name": rnd_name,
				"expected_skill_set": [{"skill": s} for s in ir_data["skills"]],
			})
			doc.flags.ignore_permissions = True
			doc.insert(ignore_if_duplicate=True)
		names.append(rnd_name)
	return names


def _ensure_kras():
	"""Create KRA records for appraisals. Returns list of KRA names."""
	names = []
	for kra_name, _ in KRA_DEFINITIONS:
		if not frappe.db.exists("KRA", kra_name):
			frappe.get_doc({"doctype": "KRA", "title": kra_name}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)
		names.append(kra_name)
	return names


def _ensure_appraisal_template():
	"""Create the standard appraisal template. Returns template name."""
	if frappe.db.exists("Appraisal Template", APPRAISAL_TEMPLATE_NAME):
		return APPRAISAL_TEMPLATE_NAME

	_ensure_kras()
	doc = frappe.get_doc({
		"doctype": "Appraisal Template",
		"template_title": APPRAISAL_TEMPLATE_NAME,
		"goals": [
			{"key_result_area": kra_name, "per_weightage": weight}
			for kra_name, weight in KRA_DEFINITIONS
		],
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_if_duplicate=True)
	return APPRAISAL_TEMPLATE_NAME


def _generate_recruitment_lifecycle(demo_employees, companies):
	"""Generate Job Openings → Job Applicants → Interviews → Job Offers for demo employees.

	Creates the full recruitment trail for ~60% of employees.
	"""
	round_names = _ensure_interview_rounds()

	# Select employees who get a recruitment history (~60%)
	selected = random.sample(demo_employees, k=max(1, int(len(demo_employees) * 0.6)))
	total = len(selected)

	# Get an admin user for interview panel
	admin_user = frappe.db.get_value(
		"User", {"enabled": 1, "name": ("not in", ["Guest", "Administrator"])}, "name"
	) or "Administrator"

	# Cache of Job Openings keyed by (designation, company)
	opening_cache = {}

	for idx, emp_name in enumerate(selected):
		try:
			emp = frappe.get_doc("Employee", emp_name)
			designation = emp.designation or "Secretary"
			company = emp.company
			department = emp.department
			doj = getdate(emp.date_of_joining)
			applicant_name = emp.employee_name

			# 1. Job Opening – reuse existing for same designation+company
			cache_key = (designation, company)
			if cache_key in opening_cache:
				opening_name = opening_cache[cache_key]
			else:
				# Check if opening already exists from a previous run
				existing = frappe.db.get_value(
					"Job Opening",
					{"designation": designation, "company": company},
					"name",
				)
				if existing:
					# Ensure it's open so applicants can be created
					frappe.db.set_value("Job Opening", existing, "status", "Open", update_modified=False)
					opening_name = existing
				else:
					posted_date = doj - timedelta(days=random.randint(45, 90))
					desc = JOB_DESCRIPTIONS.get(designation, f"Position for {designation} at {company}.")
					opening = frappe.get_doc({
						"doctype": "Job Opening",
						"job_title": f"{designation} - {company}",
						"designation": designation,
						"company": company,
						"department": department,
						"status": "Open",
						"description": f"<p>{desc}</p>",
						"posted_on": str(posted_date),
					})
					opening.flags.ignore_permissions = True
					opening.flags.ignore_mandatory = True
					opening.insert(ignore_if_duplicate=True)
					opening_name = opening.name
				opening_cache[cache_key] = opening_name

			# 2. Job Applicant
			email_first = emp.first_name.lower().replace(" ", ".")
			email_last = (emp.last_name or "applicant").lower().replace(" ", ".")
			applicant_email = f"{email_first}.{email_last}.apply@example.com"

			applicant = frappe.get_doc({
				"doctype": "Job Applicant",
				"applicant_name": applicant_name,
				"email_id": applicant_email,
				"job_title": opening_name,
				"status": "Accepted",
				"source": random.choice(["Website Listing", "Walk In", "Employee Referral"]),
				"cover_letter": (
					f"I am writing to express my interest in the {designation} position at {company}. "
					f"With my background and experience, I am confident I can contribute effectively to your team."
				),
			})
			applicant.flags.ignore_permissions = True
			applicant.flags.ignore_mandatory = True
			applicant.insert()

			# 3. Interviews (2-3 rounds)
			num_rounds = random.randint(2, min(3, len(round_names)))
			interview_date = doj - timedelta(days=random.randint(30, 60))
			for rnd_idx in range(num_rounds):
				rnd_name = round_names[rnd_idx]
				interview = frappe.get_doc({
					"doctype": "Interview",
					"job_applicant": applicant.name,
					"interview_round": rnd_name,
					"scheduled_on": str(interview_date),
					"from_time": "10:00:00",
					"to_time": "11:00:00",
					"status": "Cleared",
					"interview_details": [{"interviewer": admin_user}],
				})
				interview.flags.ignore_permissions = True
				interview.flags.ignore_mandatory = True
				interview.flags.ignore_validate = True
				interview.insert()
				interview.submit()

				# Interview Feedback
				# Get expected skills for this round
				skills = []
				for ir in INTERVIEW_ROUNDS:
					if ir["round_name"] == rnd_name:
						skills = ir["skills"]
						break

				if skills:
					feedback = frappe.get_doc({
						"doctype": "Interview Feedback",
						"interview": interview.name,
						"interviewer": admin_user,
						"result": "Cleared",
						"skill_assessment": [
							{"skill": s, "rating": random.choice([0.6, 0.8, 1.0])}
							for s in skills
						],
						"feedback": f"{applicant_name} performed well in the {rnd_name.lower()}.",
					})
					feedback.flags.ignore_permissions = True
					feedback.flags.ignore_mandatory = True
					feedback.flags.ignore_validate = True
					feedback.insert()
					feedback.submit()

				interview_date += timedelta(days=random.randint(3, 7))

			# 4. Job Offer
			offer_date = interview_date + timedelta(days=random.randint(2, 5))
			offer = frappe.get_doc({
				"doctype": "Job Offer",
				"job_applicant": applicant.name,
				"offer_date": str(min(offer_date, doj - timedelta(days=1))),
				"designation": designation,
				"company": company,
				"status": "Accepted",
				"offer_terms": [
					{"offer_term": "Date of Joining", "value": str(doj)},
					{"offer_term": "Department", "value": department or ""},
					{"offer_term": "Probationary Period", "value": "3 months"},
				],
			})
			offer.flags.ignore_permissions = True
			offer.flags.ignore_mandatory = True
			offer.flags.ignore_validate = True
			offer.insert()
			offer.submit()

			# 5. Link Employee back to Job Applicant
			frappe.db.set_value("Employee", emp_name, "job_applicant", applicant.name, update_modified=False)

		except Exception as e:
			frappe.log_error(f"Lifecycle for {emp_name}: {e}", "AMO Demo Data")

		if (idx + 1) % 5 == 0 or idx + 1 == total:
			pct = int((idx + 1) / total * 50)
			_publish("amo_demo_progress", f"Recruitment lifecycle {idx + 1}/{total}…", pct)

	# Close all Job Openings that were used
	for opening_name in opening_cache.values():
		frappe.db.set_value("Job Opening", opening_name, "status", "Closed", update_modified=False)

	frappe.db.commit()


def _generate_appraisals(demo_employees, companies, year):
	"""Generate appraisal cycle and appraisals for demo employees.

	Creates one cycle per company with appraisals for ~70% of employees.
	"""
	template_name = _ensure_appraisal_template()
	total = len(demo_employees)
	created = 0

	# Group employees by company
	by_company = {}
	for emp_name in demo_employees:
		company = frappe.db.get_value("Employee", emp_name, "company")
		by_company.setdefault(company, []).append(emp_name)

	for company, emp_names in by_company.items():
		cycle_name = APPRAISAL_CYCLE_TEMPLATE.format(year=year)
		cycle_key = f"{cycle_name} - {company}"

		# Create or reuse Appraisal Cycle
		if not frappe.db.exists("Appraisal Cycle", cycle_key):
			cycle = frappe.get_doc({
				"doctype": "Appraisal Cycle",
				"cycle_name": cycle_key,
				"company": company,
				"start_date": f"{year}-01-01",
				"end_date": f"{year}-12-31",
				"kra_evaluation_method": "Manual Rating",
			})
			cycle.flags.ignore_permissions = True
			cycle.insert(ignore_if_duplicate=True)

		# Select ~70% of employees for appraisal
		selected = random.sample(emp_names, k=max(1, int(len(emp_names) * 0.7)))

		for emp_name in selected:
			# Skip if appraisal already exists
			if frappe.db.exists("Appraisal", {
				"employee": emp_name,
				"appraisal_cycle": cycle_key,
			}):
				continue

			try:
				appraisal = frappe.get_doc({
					"doctype": "Appraisal",
					"employee": emp_name,
					"company": company,
					"appraisal_cycle": cycle_key,
					"appraisal_template": template_name,
					"start_date": f"{year}-01-01",
					"end_date": f"{year}-12-31",
					"rate_goals_manually": 1,
					"goals": [
						{
							"kra": kra_name,
							"per_weightage": weight,
							"score": round(random.uniform(2.5, 5.0), 1),
						}
						for kra_name, weight in KRA_DEFINITIONS
					],
					"remarks": random.choice([
						"Good overall performance. Meets expectations.",
						"Exceeds expectations in teamwork and communication.",
						"Strong contributor. Recommended for growth opportunities.",
						"Consistent performer. Shows initiative and dedication.",
						"Satisfactory performance with room for improvement in some areas.",
					]),
				})
				appraisal.flags.ignore_permissions = True
				appraisal.flags.ignore_mandatory = True
				appraisal.flags.ignore_validate = True
				appraisal.insert()
				appraisal.submit()
				created += 1
			except Exception as e:
				frappe.log_error(f"Appraisal for {emp_name}: {e}", "AMO Demo Data")

	frappe.db.commit()
	return created


def _cleanup_hr_lifecycle():
	"""Delete all HR lifecycle demo records (recruitment pipeline + appraisals)."""
	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%")},
		pluck="name",
	)
	demo_names_set = set(demo_employees)

	# 1. Cancel & delete Appraisals for demo employees
	for emp_name in demo_employees:
		for dt in ("Appraisal",):
			records = frappe.get_all(dt, filters={"employee": emp_name}, fields=["name", "docstatus"])
			for r in records:
				try:
					if r.docstatus == 1:
						doc = frappe.get_doc(dt, r.name)
						doc.flags.ignore_permissions = True
						doc.cancel()
					frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)
				except Exception:
					frappe.db.set_value(dt, r.name, "docstatus", 2, update_modified=False)
					frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)

	# 2. Delete Appraisal Cycles
	cycles = frappe.get_all(
		"Appraisal Cycle",
		filters={"cycle_name": ("like", "AMO Performance Review%")},
		pluck="name",
	)
	for c in cycles:
		try:
			frappe.delete_doc("Appraisal Cycle", c, force=True, ignore_permissions=True)
		except Exception:
			pass

	# 3. Appraisal Template
	if frappe.db.exists("Appraisal Template", APPRAISAL_TEMPLATE_NAME):
		try:
			frappe.delete_doc("Appraisal Template", APPRAISAL_TEMPLATE_NAME, force=True, ignore_permissions=True)
		except Exception:
			pass

	# 4. Delete Job Offers (cancel first), Interviews, Interview Feedback, Job Applicants, Job Openings
	# Job Offers linked to demo applicants
	# First find all Job Applicants with demo employee emails
	demo_emp_data = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%")},
		fields=["first_name", "last_name"],
	)
	demo_applicant_emails = set()
	for e in demo_emp_data:
		email_first = (e.first_name or "").lower().replace(" ", ".")
		email_last = (e.last_name or "applicant").lower().replace(" ", ".")
		demo_applicant_emails.add(f"{email_first}.{email_last}.apply@example.com")

	if demo_applicant_emails:
		applicants = frappe.get_all(
			"Job Applicant",
			filters={"email_id": ("in", list(demo_applicant_emails))},
			fields=["name"],
		)
		applicant_names = [a.name for a in applicants]

		# Cancel & delete Job Offers
		if applicant_names:
			for dt, fld in [
				("Job Offer", "job_applicant"),
				("Interview Feedback", "job_applicant"),
				("Interview", "job_applicant"),
			]:
				records = frappe.get_all(
					dt, filters={fld: ("in", applicant_names)}, fields=["name", "docstatus"]
				)
				for r in records:
					try:
						if r.docstatus == 1:
							doc = frappe.get_doc(dt, r.name)
							doc.flags.ignore_permissions = True
							doc.cancel()
						frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)
					except Exception:
						frappe.db.set_value(dt, r.name, "docstatus", 2, update_modified=False)
						frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)

		# Delete Job Applicants
		for a_name in applicant_names:
			try:
				frappe.delete_doc("Job Applicant", a_name, force=True, ignore_permissions=True)
			except Exception:
				pass

	# Delete Job Openings with demo pattern
	openings = frappe.get_all(
		"Job Opening",
		filters={"job_title": ("like", "% - AMO%")},
		pluck="name",
	)
	for o in openings:
		try:
			frappe.delete_doc("Job Opening", o, force=True, ignore_permissions=True)
		except Exception:
			pass

	# 5. Delete Interview Rounds created by demo
	for ir in INTERVIEW_ROUNDS:
		if frappe.db.exists("Interview Round", ir["round_name"]):
			try:
				frappe.delete_doc("Interview Round", ir["round_name"], force=True, ignore_permissions=True)
			except Exception:
				pass

	# 6. Delete Skills
	skill_names = set()
	for ir in INTERVIEW_ROUNDS:
		skill_names.update(ir["skills"])
	for s in skill_names:
		if frappe.db.exists("Skill", s):
			try:
				frappe.delete_doc("Skill", s, force=True, ignore_permissions=True)
			except Exception:
				pass

	# 7. Delete KRAs
	for kra_name, _ in KRA_DEFINITIONS:
		if frappe.db.exists("KRA", kra_name):
			try:
				frappe.delete_doc("KRA", kra_name, force=True, ignore_permissions=True)
			except Exception:
				pass

	frappe.db.commit()


# ── Asset & Inventory Lifecycle ───────────────────────────────────────

def _get_company_abbr(company):
	"""Return the abbreviation for a company."""
	return frappe.db.get_value("Company", company, "abbr") or ""


def _ensure_asset_category_accounts(companies):
	"""Ensure every Asset Category has account rows for all AMO companies."""
	categories = frappe.get_all("Asset Category", pluck="name")
	for cat_name in categories:
		cat = frappe.get_doc("Asset Category", cat_name)
		existing_companies = {row.company_name for row in cat.accounts}
		definition = ASSET_DEFINITIONS.get(cat_name)
		if not definition:
			continue
		changed = False
		for company in companies:
			if company in existing_companies:
				continue
			abbr = _get_company_abbr(company)
			fa_account = f"{definition['account_prefix']} - {abbr}"
			dep_account = f"Depreciation - {abbr}"
			acdep_account = f"Accumulated Depreciation - {abbr}"
			# Verify accounts exist
			if not frappe.db.exists("Account", fa_account):
				fa_account = frappe.db.get_value(
					"Account", {"company": company, "account_type": "Fixed Asset", "is_group": 0}, "name"
				)
			if fa_account and frappe.db.exists("Account", dep_account) and frappe.db.exists("Account", acdep_account):
				cat.append("accounts", {
					"company_name": company,
					"fixed_asset_account": fa_account,
					"depreciation_expense_account": dep_account,
					"accumulated_depreciation_account": acdep_account,
				})
				changed = True
		if changed:
			cat.flags.ignore_permissions = True
			cat.save()
	frappe.db.commit()


def _generate_assets(companies, demo_employees):
	"""Create Assets across AMO companies + movements, maintenance, and repairs.

	Lifecycle per asset:
	1. Asset created (submitted) with purchase date
	2. Asset Movement – Issue to an employee custodian
	3. Asset Maintenance schedule (for ~50% of movable assets)
	4. Asset Repair (for ~20% of assets)
	"""
	_ensure_asset_category_accounts(companies)

	year = getdate(nowdate()).year
	admin_user = frappe.db.get_value(
		"User", {"enabled": 1, "name": ("not in", ["Guest", "Administrator"])}, "name"
	) or "Administrator"

	# Group demo employees by company for custodian assignment
	emp_by_company = {}
	for emp_name in demo_employees:
		company = frappe.db.get_value("Employee", emp_name, "company")
		emp_by_company.setdefault(company, []).append(emp_name)

	all_assets = []
	total_steps = sum(len(d["items"]) for d in ASSET_DEFINITIONS.values()) * len(companies)
	step = 0

	for company in companies:
		abbr = _get_company_abbr(company)
		company_emps = emp_by_company.get(company, [])

		for cat_name, cat_def in ASSET_DEFINITIONS.items():
			for asset_template, location, (price_low, price_high) in cat_def["items"]:
				step += 1
				asset_label = f"{asset_template} - {abbr}"

				# Skip if asset already exists
				if frappe.db.exists("Asset", {"asset_name": asset_label, "company": company}):
					existing = frappe.db.get_value("Asset", {"asset_name": asset_label, "company": company}, "name")
					all_assets.append(existing)
					continue

				purchase_date = date(year - random.randint(1, 4), random.randint(1, 12), random.randint(1, 28))
				purchase_amount = random.randint(price_low, price_high)

				try:
					asset = frappe.get_doc({
						"doctype": "Asset",
						"asset_name": asset_label,
						"item_code": frappe.db.get_value("Item", {"asset_category": cat_name, "is_fixed_asset": 1}, "name"),
						"asset_category": cat_name,
						"company": company,
						"location": location,
						"purchase_date": str(purchase_date),
						"available_for_use_date": str(purchase_date + timedelta(days=random.randint(1, 14))),
						"purchase_amount": purchase_amount,
						"asset_quantity": 1,
						"calculate_depreciation": 0,
						"asset_owner": "Company",
						"asset_owner_company": company,
					})
					asset.flags.ignore_permissions = True
					asset.flags.ignore_mandatory = True
					asset.flags.ignore_validate = True
					asset.insert()
					asset.submit()
					all_assets.append(asset.name)

					# -- Asset Movement: Issue to employee custodian --
					if company_emps and cat_name not in ("Buildings",):
						custodian = random.choice(company_emps)
						try:
							movement = frappe.get_doc({
								"doctype": "Asset Movement",
								"company": company,
								"purpose": "Issue",
								"transaction_date": str(purchase_date + timedelta(days=random.randint(2, 30))),
								"assets": [{
									"asset": asset.name,
									"source_location": location,
									"target_location": location,
									"to_employee": custodian,
								}],
							})
							movement.flags.ignore_permissions = True
							movement.flags.ignore_mandatory = True
							movement.flags.ignore_validate = True
							movement.insert()
							movement.submit()
						except Exception as e:
							frappe.log_error(f"Asset Movement for {asset.name}: {e}", "AMO Demo Data")

				except Exception as e:
					frappe.log_error(f"Asset {asset_label} @ {company}: {e}", "AMO Demo Data")

				if step % 5 == 0 or step == total_steps:
					pct = int(step / total_steps * 30) + 5
					_publish("amo_demo_progress", f"Assets {step}/{total_steps}…", pct)

	frappe.db.commit()

	# -- Asset Maintenance (for ~50% of non-building assets) --
	movable_assets = [
		a for a in all_assets
		if frappe.db.get_value("Asset", a, "asset_category") not in ("Buildings",)
	]
	maint_assets = random.sample(movable_assets, k=max(1, int(len(movable_assets) * 0.5)))

	# Create a maintenance team per company if needed
	maint_teams = {}
	for company in companies:
		team_name = f"AMO Maintenance - {_get_company_abbr(company)}"
		if not frappe.db.exists("Asset Maintenance Team", team_name):
			team = frappe.get_doc({
				"doctype": "Asset Maintenance Team",
				"maintenance_team_name": team_name,
				"company": company,
				"maintenance_manager": admin_user,
				"maintenance_team_members": [{"team_member": admin_user, "maintenance_role": "Maintenance Manager"}],
			})
			team.flags.ignore_permissions = True
			team.flags.ignore_mandatory = True
			team.insert(ignore_if_duplicate=True)
		maint_teams[company] = team_name

	for asset_name in maint_assets:
		company = frappe.db.get_value("Asset", asset_name, "company")
		team_name = maint_teams.get(company)
		if not team_name:
			continue
		if frappe.db.exists("Asset Maintenance", {"asset_name": asset_name}):
			continue
		try:
			tasks = []
			for task_name, mtype, period in MAINTENANCE_TASKS[:random.randint(1, len(MAINTENANCE_TASKS))]:
				tasks.append({
					"maintenance_task": task_name,
					"maintenance_type": mtype,
					"periodicity": period,
					"start_date": str(date(year, 1, 1)),
					"end_date": str(date(year, 12, 31)),
					"maintenance_status": "Planned",
					"assign_to": admin_user,
				})
			maint = frappe.get_doc({
				"doctype": "Asset Maintenance",
				"asset_name": asset_name,
				"company": company,
				"maintenance_team": team_name,
				"maintenance_tasks": tasks,
			})
			maint.flags.ignore_permissions = True
			maint.flags.ignore_mandatory = True
			maint.insert()
		except Exception as e:
			frappe.log_error(f"Maintenance for {asset_name}: {e}", "AMO Demo Data")

	frappe.db.commit()

	# -- Asset Repair (for ~20% of movable assets) --
	repair_assets = random.sample(movable_assets, k=max(1, int(len(movable_assets) * 0.2)))
	for asset_name in repair_assets:
		company = frappe.db.get_value("Asset", asset_name, "company")
		try:
			failure_date = date(year, random.randint(1, 6), random.randint(1, 28))
			completed = random.random() < 0.7
			repair = frappe.get_doc({
				"doctype": "Asset Repair",
				"asset": asset_name,
				"company": company,
				"failure_date": str(failure_date),
				"repair_status": "Completed" if completed else "Pending",
				"completion_date": str(failure_date + timedelta(days=random.randint(3, 21))) if completed else None,
				"repair_cost": random.randint(50_000, 500_000),
				"description": random.choice([
					"Routine repair after malfunction detected during inspection.",
					"Component replacement required due to wear and tear.",
					"Emergency repair – equipment stopped working during operation.",
					"Scheduled repair as part of maintenance plan.",
				]),
			})
			repair.flags.ignore_permissions = True
			repair.flags.ignore_mandatory = True
			repair.insert()
		except Exception as e:
			frappe.log_error(f"Repair for {asset_name}: {e}", "AMO Demo Data")

	frappe.db.commit()
	return len(all_assets)


def _generate_inventory_lifecycle(companies):
	"""Generate full inventory/warehouse lifecycle:

	1. Material Requests (purchase type) for consumable items
	2. Stock Entry – Material Receipt (items received into Stores warehouse)
	3. Stock Entry – Material Transfer (Stores → Finished Goods or between warehouses)
	4. Stock Entry – Material Issue (consumption)
	"""
	year = getdate(nowdate()).year
	total_companies = len(companies)

	# Verify stock items exist
	valid_items = []
	for code in STOCK_ITEM_CODES:
		if frappe.db.exists("Item", code):
			valid_items.append(code)

	if not valid_items:
		return 0

	all_created = {"material_request": 0, "stock_receipt": 0, "stock_transfer": 0, "stock_issue": 0}

	for cidx, company in enumerate(companies):
		abbr = _get_company_abbr(company)
		stores_wh = f"Stores - {abbr}"
		finished_wh = f"Finished Goods - {abbr}"

		if not frappe.db.exists("Warehouse", stores_wh):
			continue

		# -- 1. Material Requests (2-4 per company) --
		num_mrs = random.randint(2, 4)
		for mr_idx in range(num_mrs):
			mr_date = date(year, random.randint(1, 6), random.randint(1, 28))
			schedule = mr_date + timedelta(days=random.randint(7, 30))
			items_sample = random.sample(valid_items, k=random.randint(3, min(6, len(valid_items))))

			try:
				mr = frappe.get_doc({
					"doctype": "Material Request",
					"material_request_type": "Purchase",
					"company": company,
					"transaction_date": str(mr_date),
					"schedule_date": str(schedule),
					"set_warehouse": stores_wh,
					"items": [
						{
							"item_code": item_code,
							"qty": random.randint(5, 50),
							"schedule_date": str(schedule),
							"warehouse": stores_wh,
							"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
						}
						for item_code in items_sample
					],
				})
				mr.flags.ignore_permissions = True
				mr.flags.ignore_mandatory = True
				mr.insert()
				mr.submit()
				all_created["material_request"] += 1
			except Exception as e:
				frappe.log_error(f"Material Request @ {company}: {e}", "AMO Demo Data")

		# -- 2. Stock Entry – Material Receipt (3-5 per company, populate stock) --
		num_receipts = random.randint(3, 5)
		for sr_idx in range(num_receipts):
			receipt_date = date(year, random.randint(1, 8), random.randint(1, 28))
			items_sample = random.sample(valid_items, k=random.randint(2, min(5, len(valid_items))))

			try:
				se = frappe.get_doc({
					"doctype": "Stock Entry",
					"stock_entry_type": "Material Receipt",
					"company": company,
					"posting_date": str(receipt_date),
					"to_warehouse": stores_wh,
					"items": [
						{
							"item_code": item_code,
							"qty": random.randint(10, 100),
							"t_warehouse": stores_wh,
							"basic_rate": random.randint(*STOCK_ITEM_PRICES.get(item_code, (10_000, 50_000))),
							"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
						}
						for item_code in items_sample
					],
				})
				se.flags.ignore_permissions = True
				se.flags.ignore_mandatory = True
				se.insert()
				se.submit()
				all_created["stock_receipt"] += 1
			except Exception as e:
				frappe.log_error(f"Stock Receipt @ {company}: {e}", "AMO Demo Data")

		frappe.db.commit()

		# -- 3. Stock Entry – Material Transfer (2-3 per company) --
		if frappe.db.exists("Warehouse", finished_wh):
			num_transfers = random.randint(2, 3)
			for tr_idx in range(num_transfers):
				transfer_date = date(year, random.randint(2, 9), random.randint(1, 28))
				# Pick items that have stock in stores
				items_with_stock = []
				for item_code in valid_items:
					qty = frappe.db.get_value(
						"Bin",
						{"item_code": item_code, "warehouse": stores_wh},
						"actual_qty",
					) or 0
					if qty > 5:
						items_with_stock.append((item_code, qty))
				if not items_with_stock:
					continue

				transfer_items = random.sample(
					items_with_stock, k=min(random.randint(2, 4), len(items_with_stock))
				)
				try:
					se = frappe.get_doc({
						"doctype": "Stock Entry",
						"stock_entry_type": "Material Transfer",
						"company": company,
						"posting_date": str(transfer_date),
						"from_warehouse": stores_wh,
						"to_warehouse": finished_wh,
						"items": [
							{
								"item_code": item_code,
								"qty": random.randint(2, min(10, int(qty * 0.5))),
								"s_warehouse": stores_wh,
								"t_warehouse": finished_wh,
								"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
							}
							for item_code, qty in transfer_items
						],
					})
					se.flags.ignore_permissions = True
					se.flags.ignore_mandatory = True
					se.insert()
					se.submit()
					all_created["stock_transfer"] += 1
				except Exception as e:
					frappe.log_error(f"Stock Transfer @ {company}: {e}", "AMO Demo Data")

		# -- 4. Stock Entry – Material Issue (1-3 per company, consumption) --
		num_issues = random.randint(1, 3)
		for iss_idx in range(num_issues):
			issue_date = date(year, random.randint(3, 10), random.randint(1, 28))
			items_with_stock = []
			for item_code in valid_items:
				qty = frappe.db.get_value(
					"Bin",
					{"item_code": item_code, "warehouse": stores_wh},
					"actual_qty",
				) or 0
				if qty > 3:
					items_with_stock.append((item_code, qty))
			if not items_with_stock:
				continue

			issue_items = random.sample(
				items_with_stock, k=min(random.randint(1, 3), len(items_with_stock))
			)
			try:
				se = frappe.get_doc({
					"doctype": "Stock Entry",
					"stock_entry_type": "Material Issue",
					"company": company,
					"posting_date": str(issue_date),
					"from_warehouse": stores_wh,
					"items": [
						{
							"item_code": item_code,
							"qty": random.randint(1, min(5, int(qty * 0.3))),
							"s_warehouse": stores_wh,
							"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
						}
						for item_code, qty in issue_items
					],
				})
				se.flags.ignore_permissions = True
				se.flags.ignore_mandatory = True
				se.insert()
				se.submit()
				all_created["stock_issue"] += 1
			except Exception as e:
				frappe.log_error(f"Stock Issue @ {company}: {e}", "AMO Demo Data")

		frappe.db.commit()

		pct = int((cidx + 1) / total_companies * 35) + 55
		_publish("amo_demo_progress", f"Inventory {cidx + 1}/{total_companies} companies…", pct)

	return all_created


def _cleanup_assets_and_inventory():
	"""Delete all demo asset and inventory lifecycle records."""
	companies = _get_companies()

	# 1. Delete Asset Repairs for demo assets
	for company in companies:
		abbr = _get_company_abbr(company)
		repairs = frappe.get_all("Asset Repair", filters={"company": company}, pluck="name")
		for r in repairs:
			try:
				frappe.delete_doc("Asset Repair", r, force=True, ignore_permissions=True)
			except Exception:
				pass

	# 2. Delete Asset Maintenance
	for company in companies:
		maint_records = frappe.get_all("Asset Maintenance", filters={"company": company}, pluck="name")
		for m in maint_records:
			try:
				frappe.delete_doc("Asset Maintenance", m, force=True, ignore_permissions=True)
			except Exception:
				pass

	# 3. Delete Maintenance Teams
	for company in companies:
		abbr = _get_company_abbr(company)
		team_name = f"AMO Maintenance - {abbr}"
		if frappe.db.exists("Asset Maintenance Team", team_name):
			try:
				frappe.delete_doc("Asset Maintenance Team", team_name, force=True, ignore_permissions=True)
			except Exception:
				pass

	# 4. Cancel & delete Asset Movements
	for company in companies:
		movements = frappe.get_all("Asset Movement", filters={"company": company}, fields=["name", "docstatus"])
		for m in movements:
			try:
				if m.docstatus == 1:
					doc = frappe.get_doc("Asset Movement", m.name)
					doc.flags.ignore_permissions = True
					doc.cancel()
				frappe.delete_doc("Asset Movement", m.name, force=True, ignore_permissions=True)
			except Exception:
				frappe.db.set_value("Asset Movement", m.name, "docstatus", 2, update_modified=False)
				frappe.delete_doc("Asset Movement", m.name, force=True, ignore_permissions=True)

	# 5. Cancel & delete Assets (only demo-created ones with AMO abbr pattern)
	for company in companies:
		abbr = _get_company_abbr(company)
		assets = frappe.get_all(
			"Asset",
			filters={"company": company, "asset_name": ("like", f"% - {abbr}")},
			fields=["name", "docstatus"],
		)
		for a in assets:
			try:
				if a.docstatus == 1:
					doc = frappe.get_doc("Asset", a.name)
					doc.flags.ignore_permissions = True
					doc.cancel()
				frappe.delete_doc("Asset", a.name, force=True, ignore_permissions=True)
			except Exception:
				frappe.db.set_value("Asset", a.name, "docstatus", 2, update_modified=False)
				frappe.delete_doc("Asset", a.name, force=True, ignore_permissions=True)

	# 6. Cancel & delete Stock Entries
	for company in companies:
		# Delete in reverse order (issues first, then transfers, then receipts)
		entries = frappe.get_all(
			"Stock Entry",
			filters={"company": company},
			fields=["name", "docstatus"],
			order_by="posting_date desc, creation desc",
		)
		for se in entries:
			try:
				if se.docstatus == 1:
					doc = frappe.get_doc("Stock Entry", se.name)
					doc.flags.ignore_permissions = True
					doc.cancel()
				frappe.delete_doc("Stock Entry", se.name, force=True, ignore_permissions=True)
			except Exception:
				# Force-delete via SQL if standard cancel fails (e.g. sle_doc bug)
				frappe.db.sql("DELETE FROM `tabStock Entry Detail` WHERE parent=%s", se.name)
				frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE voucher_no=%s", se.name)
				frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no=%s", se.name)
				frappe.db.sql("UPDATE `tabStock Entry` SET docstatus=2 WHERE name=%s", se.name)
				frappe.delete_doc("Stock Entry", se.name, force=True, ignore_permissions=True)

	# 7. Cancel & delete Material Requests
	for company in companies:
		mrs = frappe.get_all(
			"Material Request",
			filters={"company": company},
			fields=["name", "docstatus"],
		)
		for mr in mrs:
			try:
				if mr.docstatus == 1:
					doc = frappe.get_doc("Material Request", mr.name)
					doc.flags.ignore_permissions = True
					doc.cancel()
				frappe.delete_doc("Material Request", mr.name, force=True, ignore_permissions=True)
			except Exception:
				frappe.db.set_value("Material Request", mr.name, "docstatus", 2, update_modified=False)
				frappe.delete_doc("Material Request", mr.name, force=True, ignore_permissions=True)

	# 8. Remove Asset Category account rows for AMO companies
	categories = frappe.get_all("Asset Category", pluck="name")
	for cat_name in categories:
		cat = frappe.get_doc("Asset Category", cat_name)
		original_len = len(cat.accounts)
		non_amo = [row for row in cat.accounts if row.company_name not in companies]
		if len(non_amo) < original_len:
			# Keep at least one row to avoid mandatory error
			cat.accounts = non_amo if non_amo else cat.accounts[:1]
			cat.flags.ignore_permissions = True
			cat.save()

	frappe.db.commit()


# ── Public API (whitelisted) ──────────────────────────────────────────

@frappe.whitelist()
def create_demo_data():
	"""Create demo employee records with all fields filled."""
	frappe.only_for(["System Manager", "AMO Admin"])

	settings = _get_settings()
	count = settings.number_of_employees or 20
	fill_all = settings.fill_all_fields
	fill_translatable = settings.fill_translatable_fields
	companies = _get_companies()

	if not companies:
		frappe.throw(_("No AMO companies found. Run AMO setup first."))

	_publish("amo_demo_progress", "Starting demo data creation…", 0)

	created = 0
	for i in range(count):
		try:
			emp_data = _build_employee(i + 1, companies, fill_all, fill_translatable)
			translations = emp_data.pop("_translations", {})

			doc = frappe.get_doc(emp_data)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert()

			# Save field translations
			if translations:
				_save_translations(doc, translations)

			created += 1
			pct = int((i + 1) / count * 100)
			_publish("amo_demo_progress", f"Created {created}/{count} employees…", pct)

		except Exception as e:
			frappe.log_error(f"Demo employee {i+1}: {e}", "AMO Demo Data")
			continue

	frappe.db.commit()

	# Build reporting hierarchy per company
	_assign_reporting_hierarchy()

	_publish("amo_demo_progress", f"Created {created} demo employees. Setting up leaves…", 80, done=False)

	return {"created": created}


@frappe.whitelist()
def generate_demo_attendance():
	"""Create Lebanese leave types, policy, allocations, attendance & leave applications for demo employees."""
	frappe.only_for(["System Manager", "AMO Admin"])

	companies = _get_companies()
	year = getdate(nowdate()).year

	_publish("amo_demo_progress", "Creating Lebanese leave types…", 5)
	_ensure_lebanese_leave_types()

	_publish("amo_demo_progress", "Creating leave policy…", 10)
	policy_name = _ensure_leave_policy()

	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%"), "status": "Active"},
		pluck="name",
	)

	if not demo_employees:
		_publish("amo_demo_progress", "No demo employees found", 100, done=True)
		return {"message": "No demo employees found"}

	# Create leave periods per company
	_publish("amo_demo_progress", "Creating leave periods…", 12)
	for company in companies:
		_ensure_leave_period(company, year)

	# Create leave allocations
	_publish("amo_demo_progress", "Allocating leaves to employees…", 15)
	_create_leave_allocations(demo_employees, policy_name, year)
	frappe.db.commit()

	# Generate attendance & leave applications
	_publish("amo_demo_progress", "Generating attendance records…", 20)
	_generate_attendance_and_leaves(demo_employees, year)

	_publish("amo_demo_progress", "Done — attendance & leaves generated", 100, done=True)
	return {"employees": len(demo_employees)}


@frappe.whitelist()
def generate_demo_lifecycle():
	"""Create full HR lifecycle: recruitment pipeline (Job Opening → Applicant → Interview → Offer) + Appraisals."""
	frappe.only_for(["System Manager", "AMO Admin"])

	companies = _get_companies()
	year = getdate(nowdate()).year

	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%"), "status": "Active"},
		pluck="name",
	)

	if not demo_employees:
		_publish("amo_demo_progress", "No demo employees found", 100, done=True)
		return {"message": "No demo employees found"}

	_publish("amo_demo_progress", "Generating recruitment lifecycle…", 5)
	_generate_recruitment_lifecycle(demo_employees, companies)

	_publish("amo_demo_progress", "Generating appraisals…", 55)
	appraisal_count = _generate_appraisals(demo_employees, companies, year)

	_publish("amo_demo_progress", f"Done — recruitment pipeline & {appraisal_count} appraisals created", 100, done=True)
	return {"employees": len(demo_employees), "appraisals": appraisal_count}


@frappe.whitelist()
def generate_demo_assets_inventory():
	"""Create full asset lifecycle (assets, movements, maintenance, repairs) + inventory lifecycle (MR, stock entries)."""
	frappe.only_for(["System Manager", "AMO Admin"])

	companies = _get_companies()
	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%"), "status": "Active"},
		pluck="name",
	)

	_publish("amo_demo_progress", "Creating assets & movements…", 5)
	asset_count = _generate_assets(companies, demo_employees)

	_publish("amo_demo_progress", "Creating inventory lifecycle…", 50)
	inv_counts = _generate_inventory_lifecycle(companies)

	summary = (
		f"Done — {asset_count} assets, {inv_counts['material_request']} MRs, "
		f"{inv_counts['stock_receipt']} receipts, {inv_counts['stock_transfer']} transfers, "
		f"{inv_counts['stock_issue']} issues"
	)
	_publish("amo_demo_progress", summary, 100, done=True)
	return {"assets": asset_count, **inv_counts}


@frappe.whitelist()
def link_existing_demo_data():
	"""Tag existing employees as demo data by prefixing employee_number with [DEMO]."""
	frappe.only_for(["System Manager", "AMO Admin"])

	settings = _get_settings()
	companies = _get_companies()

	if not companies:
		frappe.throw(_("No AMO companies found. Run AMO setup first."))

	_publish("amo_demo_progress", "Scanning existing employees…", 0)

	filters = {"company": ("in", companies)}
	employees = frappe.get_all(
		"Employee",
		filters=filters,
		fields=["name", "employee_number"],
	)

	tagged = 0
	total = len(employees)
	for i, emp in enumerate(employees):
		emp_number = emp.employee_number or ""
		if emp_number.startswith(DEMO_PREFIX):
			continue
		new_number = f"{DEMO_PREFIX}-{emp_number}" if emp_number else f"{DEMO_PREFIX}-{emp.name}"
		frappe.db.set_value("Employee", emp.name, "employee_number", new_number, update_modified=False)
		tagged += 1
		pct = int((i + 1) / total * 100) if total else 100
		_publish("amo_demo_progress", f"Tagged {tagged}/{total} employees…", pct)

	frappe.db.commit()
	_publish("amo_demo_progress", f"Done — tagged {tagged} employees as demo data", 100, done=True)

	return {"tagged": tagged}


@frappe.whitelist()
def backfill_demo_data():
	"""Add missing fields to existing demo employees (department, employment type, child tables)."""
	frappe.only_for(["System Manager", "AMO Admin"])

	settings = _get_settings()
	fill_translatable = settings.fill_translatable_fields

	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%")},
		pluck="name",
	)

	total = len(demo_employees)
	if total == 0:
		_publish("amo_demo_progress", "No demo employees to update", 100, done=True)
		return {"updated": 0}

	_publish("amo_demo_progress", "Backfilling missing data…", 0)

	updated = 0
	for i, emp_name in enumerate(demo_employees):
		try:
			doc = frappe.get_doc("Employee", emp_name)
			changed = False

			# Company details
			if not doc.employment_type:
				doc.employment_type = random.choice(EMPLOYMENT_TYPES)
				changed = True

			if not doc.department:
				existing_depts = frappe.get_all(
					"Department",
					filters={"company": doc.company, "is_group": 0},
					pluck="name",
					limit=20,
				)
				if existing_depts:
					doc.department = random.choice(existing_depts)
					changed = True

			# Branch
			if not doc.branch:
				branch = random.choice(BRANCHES)
				_ensure_link_value("Branch", branch)
				doc.branch = branch
				changed = True

			# Employee Grade (based on designation)
			if not doc.grade:
				level = DESIGNATION_LEVEL.get(doc.designation, 4)
				grade = LEVEL_TO_GRADE.get(level, "G4 - Officer")
				_ensure_link_value("Employee Grade", grade)
				doc.grade = grade
				changed = True

			dob = getdate(doc.date_of_birth)
			doj = getdate(doc.date_of_joining)
			first_en = doc.first_name or ""
			last_en = doc.last_name or ""
			gender = doc.gender or "Male"

			# Pick consistent random names for family fields
			father_first_en, father_first_ar = random.choice(FATHER_FIRST_NAMES)
			town_en, town_ar = random.choice(LEBANESE_TOWNS)
			pp_place_en, pp_place_ar = random.choice(PASSPORT_PLACES_OF_ISSUE)
			prof_en, prof_ar = random.choice(PROFESSIONS_PASSPORT)
			moh_en, moh_ar, caza_en, caza_ar = random.choice(MOHAFAZA_CAZA)
			reg_en, reg_ar = random.choice(REGISTER_PLACES)

			# Marital Status History
			if not doc.marital_status_history:
				marital = doc.marital_status or random.choice(["Single", "Married", "Divorced", "Widowed"])
				if not doc.marital_status:
					doc.marital_status = marital
				marital_from = str(doj - timedelta(days=random.randint(0, 365)))
				doc.append("marital_status_history", {
					"marital_status": marital,
					"from_date": marital_from,
				})
				if marital == "Divorced":
					doc.append("marital_status_history", {
						"marital_status": "Married",
						"from_date": str(_random_date(doj.year - 5, doj.year - 1)),
						"to_date": marital_from,
					})
				changed = True

			# Passport Detail
			if not doc.passport_detail:
				passport_issue = _random_date(2018, 2024)
				passport_expiry = date(passport_issue.year + 10, passport_issue.month, passport_issue.day)
				doc.append("passport_detail", {
					"passport_number": f"RL{random.randint(1000000, 9999999)}",
					"valid_upto": str(passport_expiry),
					"passport_first_name": first_en,
					"passport_last_name": last_en,
					"place_of_issue": pp_place_en,
					"date_of_issue": str(passport_issue),
					"passport_father_name": doc.father_first_name or father_first_en,
					"passport_date_of_birth": str(dob),
					"place_of_birth": doc.town_of_birth or town_en,
					"profession": prof_en,
				})
				changed = True

			# National ID
			if not doc.national_id:
				nid_from = _random_date(2015, 2022)
				doc.append("national_id", {
					"national_id_number": str(random.randint(100000, 999999)),
					"mohafaza": moh_en,
					"caza": caza_en,
					"register_place": reg_en,
					"register_number": str(random.randint(100, 9999)),
					"from_date": str(nid_from),
					"to_date": str(date(nid_from.year + 10, nid_from.month, nid_from.day)),
				})
				changed = True

			# Religion Detail
			if not doc.religion_detail:
				doc.append("religion_detail", {
					"religion": "Christian",
					"rite": "Maronite",
					"from_date": str(dob),
				})
				changed = True

			# Personal details scalars
			if not doc.blood_group:
				doc.blood_group = random.choice(BLOOD_GROUPS)
				changed = True
			if not doc.military_service:
				doc.military_service = random.choice(["Completed", "Exempted", "Postponed", "Not Applicable"])
				if doc.military_service == "Completed":
					doc.military_service_completion_date = str(_random_date(2005, 2020))
				changed = True
			if not doc.hobbies:
				doc.hobbies = ", ".join(random.sample(HOBBIES, k=random.randint(1, 3)))
				changed = True
			if not doc.club:
				doc.club = random.choice(CLUBS)
				changed = True
			if not doc.health_details:
				doc.health_details = random.choice([
					"No known conditions",
					"Mild asthma, controlled",
					"Requires prescription glasses",
					"No allergies",
				])
				changed = True
			if not doc.family_background:
				doc.family_background = random.choice([
					"Married with 2 children",
					"Single",
					"Married with 3 children",
					"Divorced, 1 child",
					"Widowed",
				])
				changed = True

			if changed:
				doc.flags.ignore_permissions = True
				doc.flags.ignore_mandatory = True
				doc.save()

				# Translations for child table fields
				if fill_translatable:
					trans = {}
					if doc.passport_detail:
						trans["_pp_place_of_issue"] = {"ar": pp_place_ar, "_source": pp_place_en}
						trans["_pp_profession"] = {"ar": prof_ar, "_source": prof_en}
						trans["_pp_place_of_birth"] = {"ar": town_ar, "_source": doc.town_of_birth or town_en}
					if doc.national_id:
						trans["_nid_mohafaza"] = {"ar": moh_ar, "_source": moh_en}
						trans["_nid_caza"] = {"ar": caza_ar, "_source": caza_en}
						trans["_nid_register_place"] = {"ar": reg_ar, "_source": reg_en}
					if trans:
						_save_translations(doc, trans)

				updated += 1

		except Exception as e:
			frappe.log_error(f"Backfill emp {emp_name}: {e}", "AMO Demo Data")

		pct = int((i + 1) / total * 100)
		_publish("amo_demo_progress", f"Updated {updated}/{total} employees…", pct)

	frappe.db.commit()

	# Build / rebuild reporting hierarchy per company
	_assign_reporting_hierarchy()

	_publish("amo_demo_progress", f"Done — updated {updated} demo employees", 100, done=True)

	return {"updated": updated}


@frappe.whitelist()
def clear_demo_data():
	"""Delete all demo employee records, leave/attendance, and their linked translations."""
	frappe.only_for(["System Manager", "AMO Admin"])

	_publish("amo_demo_cleanup", "Cleaning leave & attendance records…", 0)

	# Clean up leave types, policy, allocations, attendance first
	_cleanup_leave_and_attendance()

	_publish("amo_demo_cleanup", "Cleaning recruitment & appraisal records…", 10)

	# Clean up HR lifecycle (recruitment pipeline + appraisals)
	_cleanup_hr_lifecycle()

	_publish("amo_demo_cleanup", "Cleaning assets & inventory…", 15)

	# Clean up assets, movements, maintenance, repairs, stock entries, material requests
	_cleanup_assets_and_inventory()

	_publish("amo_demo_cleanup", "Scanning demo employees…", 20)

	# Find demo employees
	demo_employees = frappe.get_all(
		"Employee",
		filters={"employee_number": ("like", f"{DEMO_PREFIX}%")},
		fields=["name", "first_name", "last_name", "employee_number"],
	)

	total = len(demo_employees)
	if total == 0:
		_publish("amo_demo_cleanup", "No demo data to clean", 100, done=True)
		return {"deleted": 0}

	deleted = 0
	for i, emp in enumerate(demo_employees):
		try:
			# Delete linked child docs first (Salary Structure Assignment, etc.)
			_delete_linked_records(emp.name)

			# Remove translations for this employee's fields
			_remove_translations(emp)

			# Delete the employee
			frappe.delete_doc("Employee", emp.name, force=True, ignore_permissions=True)
			deleted += 1

		except Exception as e:
			frappe.log_error(f"Clear demo emp {emp.name}: {e}", "AMO Demo Data")

		pct = int((i + 1) / total * 100)
		_publish("amo_demo_cleanup", f"Deleted {deleted}/{total} employees…", pct)

	frappe.db.commit()
	_publish("amo_demo_cleanup", f"Done — deleted {deleted} demo employees", 100, done=True)

	return {"deleted": deleted}


def _delete_linked_records(employee_name):
	"""Delete records linked to a demo employee before deleting the employee."""
	linked_doctypes = [
		"Salary Structure Assignment",
		"Salary Slip",
		"Employee Benefit Application",
		"Employee Benefit Claim",
		"Leave Allocation",
		"Leave Application",
		"Attendance",
		"Employee Checkin",
		"Employee Advance",
		"Expense Claim",
		"Additional Salary",
		"Employee Separation",
		"Employee Transfer",
		"Employee Promotion",
		"Employee Skill Map",
	]
	for dt in linked_doctypes:
		if not frappe.db.table_exists(f"tab{dt}"):
			continue
		try:
			records = frappe.get_all(dt, filters={"employee": employee_name}, pluck="name")
			for r in records:
				frappe.delete_doc(dt, r, force=True, ignore_permissions=True)
		except Exception:
			pass


def _remove_translations(emp):
	"""Remove translations created for demo employee field values."""
	values_to_clean = [
		emp.first_name,
		emp.last_name,
	]
	for val in values_to_clean:
		if not val:
			continue
		translations = frappe.get_all(
			"Translation",
			filters={"source_text": val},
			pluck="name",
		)
		for t in translations:
			try:
				frappe.delete_doc("Translation", t, force=True, ignore_permissions=True)
			except Exception:
				pass


@frappe.whitelist()
def get_demo_data_stats():
	"""Return counts of demo records by type."""
	demo_filter = {"employee_number": ("like", f"{DEMO_PREFIX}%")}
	employee_count = frappe.db.count("Employee", filters=demo_filter)

	translation_count = 0
	attendance_count = 0
	leave_app_count = 0
	leave_alloc_count = 0

	if employee_count:
		demo_emps = frappe.get_all("Employee", filters=demo_filter, fields=["name", "first_name", "last_name"])
		emp_names = [e.name for e in demo_emps]

		# Translations
		source_texts = set()
		for e in demo_emps:
			if e.first_name:
				source_texts.add(e.first_name)
			if e.last_name:
				source_texts.add(e.last_name)
		if source_texts:
			translation_count = frappe.db.count(
				"Translation", filters={"source_text": ("in", list(source_texts))}
			)

		# Attendance & Leaves
		attendance_count = frappe.db.count("Attendance", filters={"employee": ("in", emp_names)})
		leave_app_count = frappe.db.count("Leave Application", filters={"employee": ("in", emp_names)})
		leave_alloc_count = frappe.db.count("Leave Allocation", filters={"employee": ("in", emp_names)})

		# HR Lifecycle
		appraisal_count = frappe.db.count("Appraisal", filters={"employee": ("in", emp_names)})

	# Recruitment counts (not tied to employee link, use pattern match)
	job_opening_count = frappe.db.count("Job Opening", filters={"job_title": ("like", "% - AMO%")})
	job_applicant_count = 0
	interview_count = 0
	job_offer_count = 0
	if job_opening_count:
		# Job Applicants linked to demo openings
		demo_openings = frappe.get_all("Job Opening", filters={"job_title": ("like", "% - AMO%")}, pluck="name")
		if demo_openings:
			job_applicant_count = frappe.db.count("Job Applicant", filters={"job_title": ("in", demo_openings)})
			demo_applicants = frappe.get_all("Job Applicant", filters={"job_title": ("in", demo_openings)}, pluck="name")
			if demo_applicants:
				interview_count = frappe.db.count("Interview", filters={"job_applicant": ("in", demo_applicants)})
				job_offer_count = frappe.db.count("Job Offer", filters={"job_applicant": ("in", demo_applicants)})

	# Asset & Inventory counts (scoped to AMO companies)
	amo_companies = _get_companies()
	asset_count = 0
	asset_movement_count = 0
	asset_maintenance_count = 0
	asset_repair_count = 0
	material_request_count = 0
	stock_entry_count = 0
	if amo_companies:
		company_filter = {"company": ("in", amo_companies)}
		asset_count = frappe.db.count("Asset", filters=company_filter)
		asset_movement_count = frappe.db.count("Asset Movement", filters=company_filter)
		asset_maintenance_count = frappe.db.count("Asset Maintenance", filters=company_filter)
		asset_repair_count = frappe.db.count("Asset Repair", filters=company_filter)
		material_request_count = frappe.db.count("Material Request", filters=company_filter)
		stock_entry_count = frappe.db.count("Stock Entry", filters=company_filter)

	total = (employee_count + translation_count + attendance_count + leave_app_count
		+ leave_alloc_count + appraisal_count + job_opening_count + job_applicant_count
		+ interview_count + job_offer_count + asset_count + asset_movement_count
		+ asset_maintenance_count + asset_repair_count + material_request_count + stock_entry_count)
	return {
		"Employee": employee_count,
		"Translation": translation_count,
		"Attendance": attendance_count,
		"Leave Application": leave_app_count,
		"Leave Allocation": leave_alloc_count,
		"Job Opening": job_opening_count,
		"Job Applicant": job_applicant_count,
		"Interview": interview_count,
		"Job Offer": job_offer_count,
		"Appraisal": appraisal_count,
		"Asset": asset_count,
		"Asset Movement": asset_movement_count,
		"Asset Maintenance": asset_maintenance_count,
		"Asset Repair": asset_repair_count,
		"Material Request": material_request_count,
		"Stock Entry": stock_entry_count,
		"total": total,
	}
