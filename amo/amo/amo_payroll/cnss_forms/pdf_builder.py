"""Shared CNSS PDF builder utilities.

Provides common drawing primitives and the CnssPageBuilder class
for generating CNSS official forms with reportlab.
"""

import io
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ── Font Registration ─────────────────────────────────────────
_fonts_registered = False


def _register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont("ArFont", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("ArFontBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    _fonts_registered = True


# ── Arabic text helpers ───────────────────────────────────────
def ar(text):
    """Reshape and bidi-reorder Arabic text for PDF rendering."""
    if not text:
        return ""
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _has_arabic(text):
    if not text:
        return False
    return any(
        "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
        or "\uFB50" <= ch <= "\uFDFF" or "\uFE70" <= ch <= "\uFEFF"
        for ch in str(text)
    )


def smart_ar(text):
    if not text:
        return ""
    text = str(text)
    return ar(text) if _has_arabic(text) else text


def to_ar_num(text):
    """Convert Western digits 0-9 to Eastern Arabic numerals ٠-٩."""
    if not text:
        return ""
    _EASTERN = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return str(text).translate(_EASTERN)


def fmt_number(val):
    """Format a number with comma separators."""
    from frappe.utils import flt
    v = flt(val)
    if v == 0:
        return ""
    return "{:,.0f}".format(v)


def fmt_number_ar(val):
    """Format a number with commas using Eastern Arabic numerals."""
    s = fmt_number(val)
    return to_ar_num(s) if s else ""


# ── Colors ────────────────────────────────────────────────────
LIGHT_BLUE = HexColor("#d6e4f0")
LIGHT_GRAY = HexColor("#f0f0f0")
HEADER_BLUE = HexColor("#4472c4")
BORDER = black


# ── CnssPageBuilder ──────────────────────────────────────────
class CnssPageBuilder:
    """Canvas wrapper providing high-level drawing primitives for CNSS forms."""

    def __init__(self, pagesize=A4):
        _register_fonts()
        self.buf = io.BytesIO()
        self.pagesize = pagesize
        self.c = canvas.Canvas(self.buf, pagesize=pagesize)
        self.W, self.H = pagesize

    # ── Text drawing ─────────────────────────────────────────
    def text_r(self, x, y, text, size=8, bold=False, color=black):
        """Right-aligned Arabic text."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawRightString(x, y, ar(str(text)) if text else "")

    def text_l(self, x, y, text, size=8, bold=False, color=black):
        """Left-aligned text, auto-reshapes Arabic."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, smart_ar(text) if text else "")

    def text_c(self, x, y, text, size=8, bold=False, color=black):
        """Center-aligned text, auto-reshapes Arabic."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawCentredString(x, y, smart_ar(text) if text else "")

    def number_r(self, x, y, val, size=8, bold=False):
        """Formatted number, right-aligned."""
        s = fmt_number(val)
        if s:
            self.text_l(x, y, s, size=size, bold=bold)

    def number_c(self, x, y, val, size=8, bold=False):
        """Formatted number, centered."""
        s = fmt_number(val)
        if s:
            self.text_c(x, y, s, size=size, bold=bold)

    # ── Drawing primitives ───────────────────────────────────
    def box(self, x, y, w, h, fill=None, stroke=True, line_width=0.5):
        """Draw a rectangle. (x, y) = bottom-left corner."""
        if fill:
            self.c.setFillColor(fill)
            self.c.rect(x, y, w, h, fill=1, stroke=0)
        if stroke:
            self.c.setStrokeColor(BORDER)
            self.c.setLineWidth(line_width)
            self.c.rect(x, y, w, h, fill=0, stroke=1)

    def line(self, x1, y1, x2, y2, width=0.5, dash=None):
        self.c.setStrokeColor(BORDER)
        self.c.setLineWidth(width)
        if dash:
            self.c.setDash(*dash)
        self.c.line(x1, y1, x2, y2)
        if dash:
            self.c.setDash()

    def hline(self, x1, x2, y, width=0.5):
        self.line(x1, y, x2, y, width=width)

    def vline(self, x, y1, y2, width=0.5):
        self.line(x, y1, x, y2, width=width)

    def checkbox(self, x, y, checked, size=10):
        """Draw checkbox box; X inside if checked."""
        self.box(x, y, size, size)
        if checked:
            self.c.setFont("ArFontBold", size - 2)
            self.c.setFillColor(black)
            self.c.drawCentredString(x + size / 2, y + 2, "X")

    # ── Table helpers ────────────────────────────────────────
    def table_header_row(self, x, y, col_widths, labels, row_h=16, size=6, fill=LIGHT_BLUE):
        """Draw a single header row with filled background.

        x, y: top-left of the row.
        col_widths: list of column widths.
        labels: list of strings.
        """
        # Fill
        total_w = sum(col_widths)
        self.box(x, y - row_h, total_w, row_h, fill=fill, stroke=True)

        # Column separators and labels
        cx = x
        for i, w in enumerate(col_widths):
            if i > 0:
                self.vline(cx, y, y - row_h)
            mid_x = cx + w / 2
            lbl = labels[i] if i < len(labels) else ""
            if "\n" in str(lbl):
                parts = str(lbl).split("\n")
                line_h = row_h / (len(parts) + 1)
                for j, part in enumerate(parts):
                    self.text_c(mid_x, y - line_h * (j + 1), part, size=size, bold=True)
            else:
                self.text_c(mid_x, y - row_h / 2 - size / 3, lbl, size=size, bold=True)
            cx += w

    def table_data_row(self, x, y, col_widths, values, row_h=14, size=7, bold=False, fill=None):
        """Draw a single data row.

        x, y: top-left of the row.
        values: list of strings/numbers.
        """
        total_w = sum(col_widths)
        if fill:
            self.box(x, y - row_h, total_w, row_h, fill=fill, stroke=False)
        self.box(x, y - row_h, total_w, row_h, stroke=True)

        cx = x
        for i, w in enumerate(col_widths):
            if i > 0:
                self.vline(cx, y, y - row_h)
            mid_x = cx + w / 2
            val = values[i] if i < len(values) else ""
            if val is not None and val != "":
                self.text_c(mid_x, y - row_h / 2 - size / 3, str(val), size=size, bold=bold)
            cx += w

    # ── Page management ──────────────────────────────────────
    def new_page(self, pagesize=None):
        self.c.showPage()
        if pagesize:
            self.c.setPageSize(pagesize)
            self.W, self.H = pagesize

    def get_pdf_bytes(self):
        self.c.save()
        return self.buf.getvalue()
