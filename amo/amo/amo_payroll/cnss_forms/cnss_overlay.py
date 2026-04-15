"""Overlay utility for stamping data onto official CNSS blank PDF forms.

Handles both landscape forms (190A, 351 — stored as portrait A4 with /Rotate=90)
and portrait forms (2M — standard A4).

Uses reportlab to create a transparent overlay and pypdf to merge it
onto the official blank form, producing an exact-looking filled form.
"""

import io
import os

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.pdfgen import canvas

# Import shared utilities from MoF overlay
from amo.amo_payroll.mof_forms.pdf_overlay import (
	_register_fonts, ar, smart_ar, to_ar_num, fmt_number, translate,
)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "pdf_templates")


def fmt_western(val):
	"""Format a number with commas using Western (standard 0-9) digits."""
	from frappe.utils import flt
	v = flt(val)
	if v == 0:
		return ""
	return "{:,.0f}".format(v)


# ── Landscape Overlay Builder ────────────────────────────────────
class LandscapeOverlayBuilder:
	"""Creates overlay for landscape CNSS forms (190A, 351).

	The blank PDFs are stored as portrait A4 (595×842) with /Rotate=90.
	This builder transforms the canvas so callers draw in visual
	landscape coordinates:
	  x: 0 (left) → 842 (right)
	  y: 0 (bottom) → 595 (top)
	"""

	def __init__(self):
		_register_fonts()
		self.buf = io.BytesIO()
		self.c = canvas.Canvas(self.buf, pagesize=A4)  # 595×842 portrait
		self._apply_landscape_transform()

	def _apply_landscape_transform(self):
		self.c.translate(595, 0)
		self.c.rotate(90)

	# ── Text drawing ─────────────────────────────────────────
	def text_r(self, x, y, text, size=8, bold=False):
		"""Draw right-aligned text (Arabic/RTL) at visual (x, y)."""
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawRightString(x, y, ar(str(text)) if text else "")

	def text_l(self, x, y, text, size=8, bold=False):
		"""Draw left-aligned text at visual (x, y)."""
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawString(x, y, smart_ar(text) if text else "")

	def text_c(self, x, y, text, size=8, bold=False):
		"""Draw center-aligned text at visual (x, y)."""
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawCentredString(x, y, smart_ar(text) if text else "")

	def number_r(self, x, y, val, size=8, bold=False):
		"""Draw right-aligned formatted number (Western digits)."""
		self.text_r(x, y, fmt_western(val), size=size, bold=bold)

	def number_c(self, x, y, val, size=8, bold=False):
		"""Draw centered formatted number."""
		self.text_c(x, y, fmt_western(val), size=size, bold=bold)

	def digit_boxes(self, x_start, y, digits_str, box_width=12, size=8):
		"""Draw individual digits right-to-left in sequential boxes."""
		if not digits_str:
			return
		for i, ch in enumerate(str(digits_str).strip()):
			self.text_c(x_start - i * box_width, y, ch, size=size)

	def new_page(self):
		"""Finish current page and start a new landscape page."""
		self.c.showPage()
		self.c.setPageSize(A4)
		self._apply_landscape_transform()

	def get_overlay_bytes(self):
		"""Return the overlay PDF as bytes."""
		self.c.save()
		return self.buf.getvalue()


# ── Portrait Overlay Builder ─────────────────────────────────────
class PortraitOverlayBuilder:
	"""Creates overlay for portrait CNSS forms (2M).

	Standard A4 coordinates:
	  x: 0 (left) → 595 (right)
	  y: 0 (bottom) → 842 (top)
	"""

	def __init__(self):
		_register_fonts()
		self.buf = io.BytesIO()
		self.c = canvas.Canvas(self.buf, pagesize=A4)

	def text_r(self, x, y, text, size=8, bold=False):
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawRightString(x, y, ar(str(text)) if text else "")

	def text_l(self, x, y, text, size=8, bold=False):
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawString(x, y, smart_ar(text) if text else "")

	def text_c(self, x, y, text, size=8, bold=False):
		font = "ArFontBold" if bold else "ArFont"
		self.c.setFont(font, size)
		self.c.setFillColor(black)
		self.c.drawCentredString(x, y, smart_ar(text) if text else "")

	def number_r(self, x, y, val, size=8, bold=False):
		self.text_r(x, y, fmt_western(val), size=size, bold=bold)

	def number_c(self, x, y, val, size=8, bold=False):
		self.text_c(x, y, fmt_western(val), size=size, bold=bold)

	def checkbox(self, x, y, checked, size=7):
		"""Draw an X mark at checkbox position if checked."""
		if checked:
			self.c.setFont("ArFontBold", size)
			self.c.setFillColor(black)
			self.c.drawCentredString(x, y, "X")

	def digit_boxes(self, x_start, y, digits_str, box_width=12, size=8):
		if not digits_str:
			return
		for i, ch in enumerate(str(digits_str).strip()):
			self.text_c(x_start - i * box_width, y, ch, size=size)

	def new_page(self):
		self.c.showPage()
		self.c.setPageSize(A4)

	def get_overlay_bytes(self):
		self.c.save()
		return self.buf.getvalue()


# ── Merge ────────────────────────────────────────────────────────
def merge_overlay(blank_pdf_name, overlay_bytes):
	"""Merge overlay onto the blank CNSS form PDF template.

	Args:
		blank_pdf_name: filename in pdf_templates/ (e.g. 'cnss_190a_blank.pdf')
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

	# If overlay has more pages than blank (extra detail pages), add them as-is
	for i in range(len(blank_reader.pages), len(overlay_reader.pages)):
		writer.add_page(overlay_reader.pages[i])

	output = io.BytesIO()
	writer.write(output)
	return output.getvalue()
