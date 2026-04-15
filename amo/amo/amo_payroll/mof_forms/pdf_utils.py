"""Shared utilities for drawing MoF form PDFs with reportlab.

Provides Arabic text rendering, common drawing primitives, and
coordinate helpers for A4 (595.28 x 841.89 pt) right-to-left forms.
"""

import io
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ── Constants ────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4  # 595.28 x 841.89
MARGIN = 12 * mm
GREEN = HexColor("#2e7d32")
LIGHT_GREEN = HexColor("#e8f5e9")
GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#eeeeee")

# ── Font Registration ────────────────────────────────────────────
_fonts_registered = False


def _register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont("ArFont", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("ArFontBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    _fonts_registered = True


# ── Arabic text helper ───────────────────────────────────────────
def ar(text):
    """Reshape and apply bidi to Arabic text for correct PDF rendering."""
    if not text:
        return ""
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def ar_or_latin(text):
    """Return text as-is if Latin, apply Arabic reshaping if Arabic."""
    if not text:
        return ""
    text = str(text)
    # Check if any Arabic character exists
    has_arabic = any("\u0600" <= ch <= "\u06ff" or "\ufb50" <= ch <= "\ufdff"
                     or "\ufe70" <= ch <= "\ufeff" for ch in text)
    if has_arabic:
        return ar(text)
    return text


# ── Drawing helpers ──────────────────────────────────────────────
class FormPDF:
    """Wrapper around reportlab canvas with convenience methods for MoF forms."""

    def __init__(self):
        _register_fonts()
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=A4)
        self.c.setTitle("MoF Form")
        self.y = PAGE_H - MARGIN  # current y cursor (top of page)

    def save(self):
        self.c.save()
        return self.buf.getvalue()

    def new_page(self):
        self.c.showPage()
        self.y = PAGE_H - MARGIN

    # ── Text drawing ──────────────────────────────────
    def text_ar(self, x, y, text, size=9, bold=False, color=black):
        """Draw Arabic text right-aligned at x,y."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawRightString(x, y, ar(text))
        self.c.setFillColor(black)

    def text_left(self, x, y, text, size=9, bold=False, color=black):
        """Draw left-aligned text (for Latin or values)."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, str(text) if text else "")
        self.c.setFillColor(black)

    def text_center(self, x, y, text, size=9, bold=False, color=black):
        """Draw centered text."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawCentredString(x, y, ar_or_latin(text))
        self.c.setFillColor(black)

    def text_value(self, x, y, text, size=9, bold=False):
        """Draw a data value (could be Arabic or Latin)."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.drawString(x, y, ar_or_latin(text))

    def text_rtl_in_box(self, x, y, w, text, size=9, bold=False):
        """Draw Arabic text right-aligned within a box area."""
        font = "ArFontBold" if bold else "ArFont"
        self.c.setFont(font, size)
        self.c.drawRightString(x + w - 2, y, ar(text))

    # ── Geometry ──────────────────────────────────────
    def rect(self, x, y, w, h, fill=False, stroke=True, fill_color=None, line_width=0.5):
        """Draw a rectangle. y is the bottom-left."""
        self.c.setLineWidth(line_width)
        if fill and fill_color:
            self.c.setFillColor(fill_color)
        if fill:
            self.c.rect(x, y, w, h, fill=1, stroke=1 if stroke else 0)
            self.c.setFillColor(black)
        else:
            self.c.rect(x, y, w, h, fill=0, stroke=1)

    def line(self, x1, y1, x2, y2, width=0.5, color=black):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(width)
        self.c.line(x1, y1, x2, y2)
        self.c.setStrokeColor(black)

    def hline(self, x, y, w, width=0.5):
        """Horizontal line from (x,y) going right by w."""
        self.c.setLineWidth(width)
        self.c.line(x, y, x + w, y)

    # ── Form elements ─────────────────────────────────
    def checkbox(self, x, y, checked=False, size=8):
        """Draw a checkbox square, filled with X if checked."""
        self.rect(x, y, size, size)
        if checked:
            self.c.setFont("ArFontBold", size - 1)
            self.c.drawCentredString(x + size / 2, y + 1, "×")

    def field_boxes(self, x, y, count, box_size=12, values=""):
        """Draw a row of boxes (for registration number, etc.) filled with characters."""
        values = str(values) if values else ""
        for i in range(count):
            bx = x - (i * (box_size + 1))  # RTL: boxes go right-to-left
            self.rect(bx, y, box_size, box_size + 2)
            if i < len(values):
                self.c.setFont("ArFont", 8)
                self.c.drawCentredString(bx + box_size / 2, y + 2, values[i])

    def field_boxes_ltr(self, x, y, count, box_size=12, values=""):
        """Draw boxes left-to-right."""
        values = str(values) if values else ""
        for i in range(count):
            bx = x + (i * (box_size + 1))
            self.rect(bx, y, box_size, box_size + 2)
            if i < len(values):
                self.c.setFont("ArFont", 8)
                self.c.drawCentredString(bx + box_size / 2, y + 2, values[i])

    def labeled_field(self, x, y, label, value="", label_width=100, field_width=120, size=9):
        """Draw a labeled field: Arabic label right-aligned, then underlined value."""
        self.text_ar(x, y, label, size=size)
        vx = x - label_width - 2
        self.text_value(vx - field_width + 5, y, value, size=size)
        self.hline(vx - field_width, y - 2, field_width)

    def section_header(self, x, y, w, text, size=10):
        """Draw a section header with green background."""
        self.rect(x, y - 2, w, 14, fill=True, fill_color=LIGHT_GREEN)
        self.text_ar(x + w - 4, y, text, size=size, bold=True, color=GREEN)

    def table_row(self, x, y, col_widths, texts, height=14, header=False, sizes=None):
        """Draw a table row with cells."""
        cx = x
        for i, (w, t) in enumerate(zip(col_widths, texts)):
            if header:
                self.rect(cx, y, w, height, fill=True, fill_color=LIGHT_GREEN)
            else:
                self.rect(cx, y, w, height)
            sz = sizes[i] if sizes else (8 if not header else 7)
            self.text_center(cx + w / 2, y + 3, t, size=sz, bold=header)
            cx += w

    def dotted_line(self, x, y, w):
        """Draw a dotted underline for a form field."""
        self.c.setDash(1, 2)
        self.c.setLineWidth(0.3)
        self.c.line(x, y, x + w, y)
        self.c.setDash()

    def form_field_row(self, right_x, y, label, value="", dot_width=150, num="", size=9):
        """Draw a numbered form field: num. label .......... value"""
        if num:
            self.text_ar(right_x, y, f".{num}", size=7, color=GREEN)
            right_x -= 12
        self.text_ar(right_x, y, label, size=size)
        # Calculate label width
        font = "ArFont"
        self.c.setFont(font, size)
        lw = self.c.stringWidth(ar(label), font, size)
        vx = right_x - lw - 5
        self.dotted_line(vx - dot_width, y - 1, dot_width)
        if value:
            self.text_value(vx - dot_width + 3, y, value, size=size)

    def number_format(self, value):
        """Format a number for display (with comma separators)."""
        from frappe.utils import flt
        v = flt(value)
        if v == 0:
            return ""
        return "{:,.0f}".format(v)
