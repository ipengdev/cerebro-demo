"""Overlay utility for stamping data onto original MoF blank PDF forms.

Uses reportlab to create a transparent overlay and pypdf to merge it
onto the original blank form, producing an exact-looking filled form.
"""

import io
import os
import arabic_reshaper
from bidi.algorithm import get_display

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ── Paths ────────────────────────────────────────────────────────
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "pdf_templates")

# ── Font Registration ────────────────────────────────────────────
_fonts_registered = False


def _register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont("ArFont", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("ArFontBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    _fonts_registered = True


# ── Arabic text ──────────────────────────────────────────────────
def _has_arabic(text):
    """Check if text contains Arabic characters."""
    if not text:
        return False
    return any(
        '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F'
        or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF'
        for c in str(text)
    )


def ar(text):
    """Reshape and bidi-reorder Arabic text for PDF rendering."""
    if not text:
        return ""
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def smart_ar(text):
    """Apply Arabic reshaping only if text contains Arabic characters."""
    if not text:
        return ""
    text = str(text)
    if _has_arabic(text):
        return ar(text)
    return text


def to_ar_num(text):
    """Convert Western digits 0-9 to Eastern Arabic numerals ٠-٩."""
    if not text:
        return ""
    _EASTERN = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return str(text).translate(_EASTERN)


def fmt_number(val):
    """Format a number with commas using Eastern Arabic numerals."""
    from frappe.utils import flt
    v = flt(val)
    if v == 0:
        return ""
    return to_ar_num("{:,.0f}".format(v))


# ── Arabic Translation Maps ─────────────────────────────────────
_GENDER_AR = {
    "male": "ذكر",
    "female": "أنثى",
}

_NATIONALITY_AR = {
    "lebanese": "لبناني", "lebanon": "لبناني",
    "syrian": "سوري", "syria": "سوري",
    "palestinian": "فلسطيني", "palestine": "فلسطيني",
    "jordanian": "أردني", "jordan": "أردني",
    "iraqi": "عراقي", "iraq": "عراقي",
    "egyptian": "مصري", "egypt": "مصري",
    "saudi": "سعودي", "saudi arabian": "سعودي", "saudi arabia": "سعودي",
    "emirati": "إماراتي", "united arab emirates": "إماراتي",
    "kuwaiti": "كويتي", "kuwait": "كويتي",
    "bahraini": "بحريني", "bahrain": "بحريني",
    "qatari": "قطري", "qatar": "قطري",
    "omani": "عماني", "oman": "عماني",
    "yemeni": "يمني", "yemen": "يمني",
    "tunisian": "تونسي", "tunisia": "تونسي",
    "algerian": "جزائري", "algeria": "جزائري",
    "moroccan": "مغربي", "morocco": "مغربي",
    "libyan": "ليبي", "libya": "ليبي",
    "sudanese": "سوداني", "sudan": "سوداني",
    "turkish": "تركي", "turkey": "تركي",
    "iranian": "إيراني", "iran": "إيراني",
    "french": "فرنسي", "france": "فرنسي",
    "american": "أمريكي", "united states": "أمريكي",
    "british": "بريطاني", "united kingdom": "بريطاني",
    "canadian": "كندي", "canada": "كندي",
    "german": "ألماني", "germany": "ألماني",
    "italian": "إيطالي", "italy": "إيطالي",
    "spanish": "إسباني", "spain": "إسباني",
    "australian": "أسترالي", "australia": "أسترالي",
    "brazilian": "برازيلي", "brazil": "برازيلي",
    "armenian": "أرمني", "armenia": "أرمني",
    "greek": "يوناني", "greece": "يوناني",
}

_MARITAL_AR = {
    "single": "أعزب",
    "married": "متزوج",
    "widowed": "أرمل",
    "divorced": "مطلق",
}

_SALARY_MODE_AR = {
    "monthly": "شهري",
    "daily": "يومي",
    "hourly": "بالساعة",
    "hour": "بالساعة",
}

# Lebanese Governorates (Mohafazat)
_STATE_AR = {
    "beirut": "بيروت",
    "mount lebanon": "جبل لبنان",
    "north lebanon": "لبنان الشمالي", "north": "الشمال",
    "south lebanon": "لبنان الجنوبي", "south": "الجنوب",
    "bekaa": "البقاع", "beqaa": "البقاع",
    "nabatieh": "النبطية", "nabatiyeh": "النبطية",
    "akkar": "عكّار",
    "baalbek-hermel": "بعلبك - الهرمل", "baalbek hermel": "بعلبك - الهرمل",
}

# Lebanese Districts (Cazas) and common cities
_CITY_AR = {
    # Mount Lebanon
    "metn": "المتن", "el metn": "المتن",
    "kesrouan": "كسروان", "keserwan": "كسروان",
    "baabda": "بعبدا",
    "jbeil": "جبيل", "byblos": "جبيل",
    "chouf": "الشوف",
    "aley": "عاليه",
    # Beirut
    "beirut": "بيروت",
    # North
    "tripoli": "طرابلس",
    "koura": "الكورة",
    "bsharri": "بشرّي",
    "zgharta": "زغرتا",
    "batroun": "البترون",
    "minnieh-dinniyeh": "المنية - الضنية",
    # South
    "sidon": "صيدا", "saida": "صيدا",
    "tyre": "صور", "sour": "صور",
    "jezzine": "جزّين",
    # Bekaa
    "zahle": "زحلة", "zahleh": "زحلة",
    "baalbek": "بعلبك",
    "hermel": "الهرمل",
    "west bekaa": "البقاع الغربي", "western bekaa": "البقاع الغربي",
    "rashaya": "راشيا",
    # Nabatieh
    "nabatieh": "النبطية", "nabatiyeh": "النبطية",
    "hasbaya": "حاصبيا",
    "marjayoun": "مرجعيون",
    "bint jbeil": "بنت جبيل",
    # Akkar
    "akkar": "عكّار",
    # Other common cities/towns
    "jounieh": "جونيه",
    "antelias": "أنطلياس",
    "jal el dib": "جل الديب",
    "hazmieh": "الحازمية",
    "sin el fil": "سن الفيل",
    "dekwaneh": "الدكوانة",
    "bourj hammoud": "برج حمود",
    "achrafieh": "الأشرفية",
    "hamra": "الحمرا",
    "verdun": "فردان",
    "ras beirut": "رأس بيروت",
    "bsalim": "بصاليم",
    "broummana": "برمّانا",
    "bikfaya": "بكفيا",
    "beit meri": "بيت مري",
    "dbayeh": "ضبيه",
    "zouk mosbeh": "ذوق مصبح",
    "zouk mikael": "ذوق مكايل",
    "ghazir": "غزير",
    "jouret el ballout": "جورة البلوط",
    "ehden": "اهدن",
    "bcharre": "بشري",
    "douma": "دوما",
    "hadath": "الحدث",
    "choueifat": "الشويفات",
    "damour": "الدامور",
    "jiyeh": "الجية",
}

# Common designations/job titles
_DESIGNATION_AR = {
    "chief executive officer": "الرئيس التنفيذي",
    "ceo": "الرئيس التنفيذي",
    "chief financial officer": "المدير المالي",
    "cfo": "المدير المالي",
    "chief operating officer": "مدير العمليات",
    "coo": "مدير العمليات",
    "chief technology officer": "المدير التقني",
    "cto": "المدير التقني",
    "general manager": "المدير العام",
    "manager": "مدير",
    "director": "مدير",
    "assistant manager": "مساعد مدير",
    "supervisor": "مشرف",
    "senior engineer": "مهندس أول",
    "engineer": "مهندس",
    "junior engineer": "مهندس مبتدئ",
    "senior accountant": "محاسب أول",
    "accountant": "محاسب",
    "junior accountant": "محاسب مبتدئ",
    "analyst": "محلل",
    "senior analyst": "محلل أول",
    "consultant": "مستشار",
    "senior consultant": "مستشار أول",
    "associate": "معاون",
    "senior associate": "معاون أول",
    "administrative assistant": "مساعد إداري",
    "administrative officer": "موظف إداري",
    "secretary": "سكرتير",
    "receptionist": "موظف استقبال",
    "human resources manager": "مدير الموارد البشرية",
    "hr manager": "مدير الموارد البشرية",
    "hr officer": "موظف موارد بشرية",
    "it manager": "مدير تكنولوجيا المعلومات",
    "it officer": "موظف تكنولوجيا المعلومات",
    "sales manager": "مدير المبيعات",
    "sales representative": "مندوب مبيعات",
    "marketing manager": "مدير التسويق",
    "project manager": "مدير مشروع",
    "team leader": "قائد فريق",
    "driver": "سائق",
    "cleaner": "عامل نظافة",
    "security guard": "حارس أمن",
    "technician": "فنّي",
    "electrician": "كهربائي",
    "plumber": "سبّاك",
    "carpenter": "نجّار",
    "painter": "دهّان",
    "mechanic": "ميكانيكي",
    "welder": "لحّام",
    "foreman": "رئيس عمّال",
    "laborer": "عامل",
    "worker": "عامل",
    "intern": "متدرّب",
    "trainee": "متدرّب",
}

# Country translations (for company country)
_COUNTRY_AR = {
    "lebanon": "لبنان",
    "syria": "سوريا",
    "jordan": "الأردن",
    "iraq": "العراق",
    "egypt": "مصر",
    "saudi arabia": "المملكة العربية السعودية",
    "united arab emirates": "الإمارات العربية المتحدة",
    "kuwait": "الكويت",
    "bahrain": "البحرين",
    "qatar": "قطر",
    "oman": "عمان",
    "france": "فرنسا",
    "united states": "الولايات المتحدة",
    "united kingdom": "المملكة المتحدة",
    "canada": "كندا",
    "germany": "ألمانيا",
    "italy": "إيطاليا",
}


def translate(value, category=None):
    """Translate a field value to Arabic.

    Args:
        value: The English value to translate
        category: One of 'gender', 'nationality', 'marital', 'salary_mode',
                  'state', 'city', 'designation', 'country'

    Returns:
        Arabic translation if found, original value otherwise.
        If value is already Arabic, returns as-is.
    """
    if not value:
        return ""
    text = str(value).strip()
    # If already Arabic, return as-is
    if _has_arabic(text):
        return text

    key = text.lower()
    maps = {
        "gender": _GENDER_AR,
        "nationality": _NATIONALITY_AR,
        "marital": _MARITAL_AR,
        "salary_mode": _SALARY_MODE_AR,
        "state": _STATE_AR,
        "city": _CITY_AR,
        "designation": _DESIGNATION_AR,
        "country": _COUNTRY_AR,
    }
    if category and category in maps:
        result = maps[category].get(key)
        if result:
            return result

    # Auto-detect: try all maps
    for m in maps.values():
        if key in m:
            return m[key]

    # Fallback: check Frappe's Translation doctype for Arabic
    try:
        import frappe
        translated = frappe.db.get_value(
            "Translation",
            {"source_text": text, "language": "ar"},
            "translated_text",
        )
        if translated:
            return translated
    except Exception:
        pass

    return text


# ── Overlay Builder ──────────────────────────────────────────────
class OverlayBuilder:
    """Creates a transparent overlay canvas for stamping data onto a blank PDF."""

    def __init__(self, pagesize=A4):
        _register_fonts()
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=pagesize)
        self.pages = []  # list of BytesIO buffers, one per page

    def text_r(self, x, y, text, size=8, bold=False):
        """Draw right-aligned text (Arabic/RTL) at (x, y)."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(black)
        self.c.drawRightString(x, y, ar(str(text)) if text else "")

    def text_l(self, x, y, text, size=8, bold=False):
        """Draw left-aligned text at (x, y). Auto-reshapes Arabic."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(black)
        self.c.drawString(x, y, smart_ar(text) if text else "")

    def text_c(self, x, y, text, size=8, bold=False):
        """Draw center-aligned text at (x, y). Auto-reshapes Arabic."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(black)
        self.c.drawCentredString(x, y, smart_ar(text) if text else "")

    def number_r(self, x, y, val, size=8, bold=False):
        """Draw a formatted number right-aligned."""
        self.text_l(x, y, fmt_number(val), size=size, bold=bold)

    def number_c(self, x, y, val, size=8, bold=False):
        """Draw a formatted number centered."""
        self.text_c(x, y, fmt_number(val), size=size, bold=bold)

    def checkbox(self, x, y, checked, size=7):
        """Draw an X mark at checkbox position if checked."""
        if checked:
            self.c.setFont("ArFontBold", size)
            self.c.setFillColor(black)
            self.c.drawCentredString(x, y, "X")

    def digit_boxes(self, x_start, y, digits_str, box_width=12, size=8):
        """Draw individual digits in sequential boxes (right to left), using Eastern Arabic numerals."""
        if not digits_str:
            return
        digits_str = to_ar_num(str(digits_str).strip())
        for i, ch in enumerate(digits_str):
            self.text_c(x_start - i * box_width, y, ch, size=size)

    def new_page(self, pagesize=None):
        """Finish current page and start a new one."""
        self.c.showPage()
        if pagesize:
            self.c.setPageSize(pagesize)

    def get_overlay_bytes(self):
        """Return the overlay PDF as bytes."""
        self.c.save()
        return self.buf.getvalue()


def merge_overlay(blank_pdf_name, overlay_bytes):
    """Merge overlay onto the blank form PDF template.

    Args:
        blank_pdf_name: filename in pdf_templates/ (e.g. 'r3_blank.pdf')
        overlay_bytes: bytes of the overlay PDF

    Returns:
        bytes of the merged PDF
    """
    blank_path = os.path.join(TEMPLATES_DIR, blank_pdf_name)
    blank_reader = PdfReader(blank_path)
    overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
    writer = PdfWriter()

    for i, page in enumerate(blank_reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
