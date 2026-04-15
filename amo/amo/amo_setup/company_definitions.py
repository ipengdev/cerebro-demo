# AMO Company Definitions
# Based on official data from https://antonins.org
# 52 Companies organized under AMO group

COMPANY_GROUPS = {
	"AMO": {
		"abbr": "AMO",
		"country": "Lebanon",
		"currency": "LBP",
		"children": ["AMO - Monasteries", "AMO - Schools", "AMO - University", "AMO - Social and Cultural Organizations"],
	},
	"AMO - Monasteries": {
		"abbr": "AMO-MON",
		"country": "Lebanon",
		"currency": "LBP",
		"parent": "AMO",
	},
	"AMO - Schools": {
		"abbr": "AMO-SCH",
		"country": "Lebanon",
		"currency": "LBP",
		"parent": "AMO",
	},
	"AMO - University": {
		"abbr": "AMO-UNI",
		"country": "Lebanon",
		"currency": "LBP",
		"parent": "AMO",
	},
	"AMO - Social and Cultural Organizations": {
		"abbr": "AMO-SCO",
		"country": "Lebanon",
		"currency": "LBP",
		"parent": "AMO",
	},
}

# Currency mapping per country
COUNTRY_CURRENCY = {
	"Lebanon": "LBP",
	"Canada": "CAD",
	"Australia": "AUD",
	"Belgium": "EUR",
	"Italy": "EUR",
	"Syria": "SYP",
}

# Timezone mapping
COUNTRY_TIMEZONE = {
	"Lebanon": "Asia/Beirut",
	"Canada": "America/Toronto",
	"Australia": "Australia/Sydney",
	"Belgium": "Europe/Brussels",
	"Italy": "Europe/Rome",
	"Syria": "Asia/Damascus",
}

# ── 6 Foreign Monasteries ──────────────────────────────────────────────
# Source: https://antonins.org/في-لبنان-والخارج/ (في العالم section)
FOREIGN_MONASTERIES = [
	{
		"name": "Mar Yohanna Maroun Monastery - Rome",
		"name_ar": "دير مار يوحنا مارون - روما",
		"abbr": "MON-IT",
		"country": "Italy",
	},
	{
		"name": "Mar Charbel Monastery - Windsor",
		"name_ar": "دير مار شربل - وندسور",
		"abbr": "MON-CA",
		"country": "Canada",
	},
	{
		"name": "Beit Mar Maroun - Brussels",
		"name_ar": "بيت مار مارون - بروكسيل",
		"abbr": "MON-BE",
		"country": "Belgium",
	},
	{
		"name": "Our Lady of Lebanon Monastery - Toronto",
		"name_ar": "دير سيّدة لبنان - تورنتو",
		"abbr": "MON-CH",
		"country": "Canada",
	},
	{
		"name": "Mar Antonios Monastery - Banias",
		"name_ar": "دير مار انطونيوس - بانياس",
		"abbr": "MON-SY",
		"country": "Syria",
	},
	{
		"name": "Mar Charbel Monastery - Melbourne",
		"name_ar": "دير مار شربل - ملبورن",
		"abbr": "MON-AU",
		"country": "Australia",
	},
]

# ── 25 Monasteries in Lebanon ──────────────────────────────────────────
# Source: https://antonins.org/في-لبنان-والخارج/ (في لبنان section)
LEBANON_MONASTERIES = [
	{
		"name": "Mar Eshaiya Monastery - Broummana",
		"name_ar": "دير مار أشعيا - المتن",
		"abbr": "ML01",
	},
	{
		"name": "Mar Abda Mushammer Monastery - Zoukrit",
		"name_ar": "دير مار عبدا المشمّر - زكريت",
		"abbr": "ML02",
	},
	{
		"name": "Mar Elias Monastery - Antelias",
		"name_ar": "دير مار الياس - انطلياس",
		"abbr": "ML03",
	},
	{
		"name": "Sts. Sergius and Bacchus Monastery - Ehden",
		"name_ar": "دير مار سركيس وباخوس - اهدن",
		"abbr": "ML04",
	},
	{
		"name": "Mar Yohanna Al-Qalaa Monastery - Beit Meri",
		"name_ar": "دير مار يوحنّا القلعة - بيت مري",
		"abbr": "ML05",
	},
	{
		"name": "Mar Elias Monastery - Qornayel",
		"name_ar": "دير مار الياس - قرنايل",
		"abbr": "ML06",
	},
	{
		"name": "Mar Semaan Al-Ammoudi Monastery - Ain El-Qabou",
		"name_ar": "دير مار سمعان العامودي - عين القبو",
		"abbr": "ML07",
	},
	{
		"name": "Sts. Peter and Paul Monastery - Qattine",
		"name_ar": "دير القدّيسين بطرس وبولس - قطّين",
		"abbr": "ML08",
	},
	{
		"name": "Mar Antonios Monastery - Hadath",
		"name_ar": "دير مار أنطونيوس - الحدت - بعبدا",
		"abbr": "ML09",
	},
	{
		"name": "Mar Nohra Monastery - Fatqa",
		"name_ar": "دير مار نوهرا - القنزوح - فتقا",
		"abbr": "ML10",
	},
	{
		"name": "Mar Roukoz Monastery - Dekwaneh",
		"name_ar": "دير مار روكز - الدكوانة",
		"abbr": "ML11",
	},
	{
		"name": "Mar Youssef Monastery - Zahle",
		"name_ar": "دير مار يوسف - زحلة",
		"abbr": "ML12",
	},
	{
		"name": "Mar Antonios Paduan Monastery - Jezzine",
		"name_ar": "دير مار انطونيوس البدواني - جزّين",
		"abbr": "ML13",
	},
	{
		"name": "Mar Elias Monastery - Qab Elias",
		"name_ar": "دير مار الياس - قب الياس",
		"abbr": "ML14",
	},
	{
		"name": "Mar Adna Monastery - Al-Nammoura",
		"name_ar": "دير مار أدنا - النمّورة",
		"abbr": "ML15",
	},
	{
		"name": "Mar Nohra Monastery - Qornet El-Hamra",
		"name_ar": "دير مار نوهرا - قرنة الحمرا",
		"abbr": "ML16",
	},
	{
		"name": "Our Lady of Succour Monastery - Shimlan",
		"name_ar": "دير سيّدة المعونات - شملان",
		"abbr": "ML17",
	},
	{
		"name": "Mar Roukoz Monastery - Housh Hala",
		"name_ar": "دير مار روكز - حوش حالا",
		"abbr": "ML18",
	},
	{
		"name": "Our Lady of Salvation Monastery - Al-Mina",
		"name_ar": "دير سيّدة النجاة - المينا",
		"abbr": "ML19",
	},
	{
		"name": "Mar Youssef Monastery - Bahrssaf",
		"name_ar": "دير مار يوسف - بحرصاف",
		"abbr": "ML20",
	},
	{
		"name": "Mar Elias Monastery - Al-Knayseh",
		"name_ar": "دير مار الياس - الكنيسة",
		"abbr": "ML21",
	},
	{
		"name": "Sts. Sergius and Bacchus Monastery - Kfardlaqous",
		"name_ar": "دير مار سركيس وباخوس - كفردلاقوس زغرتا",
		"abbr": "ML22",
	},
	{
		"name": "Mar Yohanna the Baptist Monastery - Ajaltoun",
		"name_ar": "دير مار يوحنّا المعمدان - عجلتون",
		"abbr": "ML23",
	},
	{
		"name": "The Lord's Monastery - Marjayoun",
		"name_ar": "دير الرب - مرجعيون",
		"abbr": "ML24",
	},
	{
		"name": "Our Lady of the Seeds Monastery - Baabda",
		"name_ar": "دير سيدة الزروع - بعبدا",
		"abbr": "ML25",
	},
]

# ── 12 Schools ──────────────────────────────────────────────────────────
# Source: https://antonins.org/المؤسسات-التربوية/
SCHOOLS = [
	{
		"name": "Antonine Institute - Hadath",
		"name_ar": "المعهد الأنطوني - الحدت - بعبدا",
		"abbr": "SCH01",
	},
	{
		"name": "Mar Maroun Antonine School - Hadath",
		"name_ar": "مدرسة مار مارون الأنطونية - الحدت",
		"abbr": "SCH02",
	},
	{
		"name": "Lycee des Peres Antonins - Baabda",
		"name_ar": "ثانوية الآباء الأنطونيين - بعبدا",
		"abbr": "SCH03",
	},
	{
		"name": "Antonine Fathers School - Bouchrieh",
		"name_ar": "مدرسة الآباء الأنطونيين - البوشرية",
		"abbr": "SCH04",
	},
	{
		"name": "Antonine International School - Dekwaneh",
		"name_ar": "المدرسة الأنطونية الدولية - الدكوانة",
		"abbr": "SCH05",
	},
	{
		"name": "Mar Roukoz School - Housh Hala",
		"name_ar": "مدرسة مار روكز - حوش حالا - رياق",
		"abbr": "SCH06",
	},
	{
		"name": "Antonine International School - Ajaltoun",
		"name_ar": "المدرسة الأنطونية الدولية - عجلتون",
		"abbr": "SCH07",
	},
	{
		"name": "Our Lady of the Assumption School - Hasroun",
		"name_ar": "مدرسة سيدة الانتقال - حصرون",
		"abbr": "SCH08",
	},
	{
		"name": "Al-Khoury Mansour School - Qlaiaa",
		"name_ar": "مدرسة الخوري منصور - القليعة - مرجعيون",
		"abbr": "SCH09",
	},
	{
		"name": "Al-Salam Antonine School - Zahle",
		"name_ar": "مدرسة السلام الأنطونية - زحلة",
		"abbr": "SCH10",
	},
	{
		"name": "Social Guidance Antonine School - Al-Marouj",
		"name_ar": "مدرسة التوجيه الإجتماعي للآباء الأنطونيين - المروج",
		"abbr": "SCH11",
	},
	{
		"name": "Our Lady of Salvation School - Al-Mina",
		"name_ar": "مدرسة سيدة النجاة - المينا - طرابلس",
		"abbr": "SCH12",
	},
]

# ── 6 Social and Cultural Organizations ─────────────────────────────────
SOCIAL_CULTURAL_ORGS = [
	{
		"name": "Antonine Cultural Center - Beirut",
		"name_ar": "المركز الثقافي الأنطوني - بيروت",
		"abbr": "SCO01",
	},
	{
		"name": "Antonine Social Services - Baabda",
		"name_ar": "الخدمات الاجتماعية الأنطونية - بعبدا",
		"abbr": "SCO02",
	},
	{
		"name": "Antonine Heritage Foundation",
		"name_ar": "مؤسسة التراث الأنطوني",
		"abbr": "SCO03",
	},
	{
		"name": "Antonine Youth Movement",
		"name_ar": "الحركة الشبابية الأنطونية",
		"abbr": "SCO04",
	},
	{
		"name": "Antonine Media and Publishing",
		"name_ar": "الإعلام والنشر الأنطوني",
		"abbr": "SCO05",
	},
	{
		"name": "Antonine Charitable Association",
		"name_ar": "الجمعية الخيرية الأنطونية",
		"abbr": "SCO06",
	},
]

# ── 3 University Campuses ───────────────────────────────────────────────
# Source: https://antonins.org/المؤسسات-التربوية/
# الجامعة الأنطونية (بعبدا – زحلة – مجدليا)
UNIVERSITY_CAMPUSES = [
	{
		"name": "Antonine University - Baabda Campus",
		"name_ar": "الجامعة الأنطونية - حرم بعبدا",
		"abbr": "UNI01",
	},
	{
		"name": "Antonine University - Zahle Campus",
		"name_ar": "الجامعة الأنطونية - حرم زحلة",
		"abbr": "UNI02",
	},
	{
		"name": "Antonine University - Majdaliya Campus",
		"name_ar": "الجامعة الأنطونية - حرم مجدليا",
		"abbr": "UNI03",
	},
]

# ── Old-to-New name mapping for migration ──────────────────────────────
RENAME_MAP = {
	# Foreign Monasteries
	"Monastery of St. Charbel - Italy": "Mar Yohanna Maroun Monastery - Rome",
	"Monastery of St. Anthony - Canada": "Mar Charbel Monastery - Windsor",
	"Monastery of Our Lady - Belgium": "Beit Mar Maroun - Brussels",
	"Monastery of St. Rafqa - Switzerland": "Our Lady of Lebanon Monastery - Toronto",
	"Monastery of Mar Elias - Syria": "Mar Antonios Monastery - Banias",
	"Monastery of St. Maroun - Australia": "Mar Charbel Monastery - Melbourne",
	# Lebanese Monasteries
	"Monastery of St. Isaiah - Broumana": "Mar Eshaiya Monastery - Broummana",
	"Monastery of Our Lady of Tamish": "Mar Abda Mushammer Monastery - Zoukrit",
	"Monastery of Mar Roukoz - Dekwaneh": "Mar Elias Monastery - Antelias",
	"Monastery of Our Lady of Balamand": "Sts. Sergius and Bacchus Monastery - Ehden",
	"Monastery of St. Elias - Ghazir": "Mar Yohanna Al-Qalaa Monastery - Beit Meri",
	"Monastery of St. Anthony - Houb": "Mar Elias Monastery - Qornayel",
	"Monastery of Our Lady of Mayfouq": "Mar Semaan Al-Ammoudi Monastery - Ain El-Qabou",
	"Monastery of St. Doumit - Ajaltoun": "Sts. Peter and Paul Monastery - Qattine",
	"Monastery of Mar Abda - Jbeil": "Mar Antonios Monastery - Hadath",
	"Monastery of Our Lady of Louaize": "Mar Nohra Monastery - Fatqa",
	"Monastery of St. John - Khinchara": "Mar Roukoz Monastery - Dekwaneh",
	"Monastery of Mar Semaan - Ain Traz": "Mar Youssef Monastery - Zahle",
	"Monastery of Our Lady of Bkerke": "Mar Antonios Paduan Monastery - Jezzine",
	"Monastery of St. George - Dlebta": "Mar Elias Monastery - Qab Elias",
	"Monastery of Mar Sassine - Beit Meri": "Mar Adna Monastery - Al-Nammoura",
	"Monastery of Our Lady of Machmouchi": "Mar Nohra Monastery - Qornet El-Hamra",
	"Monastery of St. Anthony the Great - Kozhaya": "Our Lady of Succour Monastery - Shimlan",
	"Monastery of Mar Maroun - Annaya": "Mar Roukoz Monastery - Housh Hala",
	"Monastery of Our Lady of Qannoubine": "Our Lady of Salvation Monastery - Al-Mina",
	"Monastery of St. Nohra - Barsa": "Mar Youssef Monastery - Bahrssaf",
	"Monastery of Mar Challita - Fghal": "Mar Elias Monastery - Al-Knayseh",
	"Monastery of Our Lady of Hammatoura": "Sts. Sergius and Bacchus Monastery - Kfardlaqous",
	"Monastery of St. Michael - Bzoummar": "Mar Yohanna the Baptist Monastery - Ajaltoun",
	"Monastery of Mar Antonios - Baabda": "The Lord's Monastery - Marjayoun",
	"Monastery of Our Lady of the Fields - Jezzine": "Our Lady of the Seeds Monastery - Baabda",
	# Schools
	"Antonine School - Broumana": "Antonine Institute - Hadath",
	"Antonine School - Ajaltoun": "Mar Maroun Antonine School - Hadath",
	"Antonine School - Ghazir": "Lycee des Peres Antonins - Baabda",
	"Antonine School - Baabda": "Antonine Fathers School - Bouchrieh",
	"Antonine School - Ain Traz": "Antonine International School - Dekwaneh",
	"Antonine School - Jbeil": "Mar Roukoz School - Housh Hala",
	"Antonine School - Dekwaneh": "Antonine International School - Ajaltoun",
	"Antonine School - Tripoli": "Our Lady of the Assumption School - Hasroun",
	"Antonine School - Sidon": "Al-Khoury Mansour School - Qlaiaa",
	"Antonine School - Jounieh": "Al-Salam Antonine School - Zahle",
	"Antonine School - Zahle": "Social Guidance Antonine School - Al-Marouj",
	"Antonine School - Beit Meri": "Our Lady of Salvation School - Al-Mina",
	# University
	"Antonine University - Hadath Campus": "Antonine University - Zahle Campus",
	"Antonine University - Nabi Ayla Campus": "Antonine University - Majdaliya Campus",
	# Social and Cultural keep same names
}

# Build a lookup of new names → Arabic names
_ALL_ITEMS = FOREIGN_MONASTERIES + LEBANON_MONASTERIES + SCHOOLS + SOCIAL_CULTURAL_ORGS + UNIVERSITY_CAMPUSES
ARABIC_NAMES = {item["name"]: item["name_ar"] for item in _ALL_ITEMS}


def get_all_companies():
	"""Return flat list of all 52 company dicts with group/country info."""
	companies = []

	# Foreign monasteries
	for m in FOREIGN_MONASTERIES:
		companies.append({
			"name": m["name"],
			"name_ar": m["name_ar"],
			"abbr": m["abbr"],
			"country": m["country"],
			"currency": COUNTRY_CURRENCY[m["country"]],
			"group": "AMO - Monasteries",
			"type": "monastery",
		})

	# Lebanese monasteries
	for m in LEBANON_MONASTERIES:
		companies.append({
			"name": m["name"],
			"name_ar": m["name_ar"],
			"abbr": m["abbr"],
			"country": "Lebanon",
			"currency": "LBP",
			"group": "AMO - Monasteries",
			"type": "monastery",
		})

	# Schools
	for s in SCHOOLS:
		companies.append({
			"name": s["name"],
			"name_ar": s["name_ar"],
			"abbr": s["abbr"],
			"country": "Lebanon",
			"currency": "LBP",
			"group": "AMO - Schools",
			"type": "school",
		})

	# Social and Cultural orgs
	for o in SOCIAL_CULTURAL_ORGS:
		companies.append({
			"name": o["name"],
			"name_ar": o["name_ar"],
			"abbr": o["abbr"],
			"country": "Lebanon",
			"currency": "LBP",
			"group": "AMO - Social and Cultural Organizations",
			"type": "social_cultural",
		})

	# University campuses
	for u in UNIVERSITY_CAMPUSES:
		companies.append({
			"name": u["name"],
			"name_ar": u["name_ar"],
			"abbr": u["abbr"],
			"country": "Lebanon",
			"currency": "LBP",
			"group": "AMO - University",
			"type": "university",
		})

	return companies
