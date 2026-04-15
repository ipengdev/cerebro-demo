"""R7 — Summary of employees who left during the year — overlay builder.

Stamps data onto the original blank R7 form PDF (406.5 x 441.0 pt).
"""
from frappe.utils import getdate, cint
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, smart_ar, translate, to_ar_num

# R7 page is smaller than A4
PAGE_W = 406.5
PAGE_H = 441.0

# ── Header field positions ────────────────────────────────────
COMPANY_NAME_X = 340
COMPANY_NAME_Y = 387

TRADE_NAME_X = 340
TRADE_NAME_Y = 377

MOF_REG_X = 340
MOF_REG_Y = 367

YEAR_X = 100
YEAR_Y = 387

CNSS_REG_X = 155
CNSS_REG_Y = 362

# ── Table layout ─────────────────────────────────────────────
FIRST_ROW_Y = 313
ROW_SPACING = 12
MAX_ROWS_PER_PAGE = 25

# Column x-positions
COL_NAME_X = 395        # right-aligned
COL_TAX_REG_X = 278     # centered
COL_CNSS_X = 196        # centered
COL_START_DATE_X = 115   # centered
COL_END_DATE_X = 40      # centered

FONT_SIZE = 6
HEADER_FONT_SIZE = 7


def _stamp_header(ob, data):
    """Stamp the header fields on the current page."""
    comp = data["company"]

    # Company name (right-aligned)
    ob.text_r(COMPANY_NAME_X, COMPANY_NAME_Y,
              translate(comp.get("company_name") or comp.get("name")),
              size=HEADER_FONT_SIZE)

    # Trade name
    ob.text_r(TRADE_NAME_X, TRADE_NAME_Y,
              translate(comp.get("trade_name") or ""),
              size=HEADER_FONT_SIZE)

    # MoF registration number
    mof_reg = comp.get("tax_id") or ""
    if mof_reg:
        ob.text_c(MOF_REG_X, MOF_REG_Y, to_ar_num(mof_reg), size=HEADER_FONT_SIZE)

    # Year
    ob.text_c(YEAR_X, YEAR_Y, to_ar_num(str(data["year"])), size=HEADER_FONT_SIZE)

    # CNSS registration number
    cnss_reg = comp.get("cnss_number") or comp.get("nssf_number") or ""
    if cnss_reg:
        ob.text_c(CNSS_REG_X, CNSS_REG_Y, to_ar_num(cnss_reg), size=HEADER_FONT_SIZE)


def _fmt_date(d):
    """Format a date as dd/mm/yyyy in Eastern Arabic numerals."""
    if not d:
        return ""
    dt = getdate(d)
    return to_ar_num(dt.strftime("%d/%m/%Y"))


def build_r7_pdf(data):
    """Build R7 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder(pagesize=(PAGE_W, PAGE_H))
    employees = data.get("employees", [])

    # Stamp first page header
    _stamp_header(ob, data)

    row_idx = 0
    for emp in employees:
        if row_idx >= MAX_ROWS_PER_PAGE:
            # Start new page
            ob.new_page(pagesize=(PAGE_W, PAGE_H))
            _stamp_header(ob, data)
            row_idx = 0

        y = FIRST_ROW_Y - (row_idx * ROW_SPACING)

        # Employee name (right-aligned, trilateral)
        name = emp.get("employee_name") or ""
        ob.text_r(COL_NAME_X, y, smart_ar(name), size=FONT_SIZE)

        # Personal tax registration (MoF)
        tax_reg = emp.get("tax_id") or ""
        if tax_reg:
            ob.text_c(COL_TAX_REG_X, y, to_ar_num(tax_reg), size=FONT_SIZE)

        # CNSS subscription number
        cnss_num = emp.get("cnss_number") or ""
        if cnss_num:
            ob.text_c(COL_CNSS_X, y, to_ar_num(str(cint(cnss_num))), size=FONT_SIZE)

        # Start date (date_of_joining)
        ob.text_c(COL_START_DATE_X, y, _fmt_date(emp.get("date_of_joining")), size=FONT_SIZE)

        # End date (relieving_date)
        ob.text_c(COL_END_DATE_X, y, _fmt_date(emp.get("relieving_date")), size=FONT_SIZE)

        row_idx += 1

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r7_blank.pdf", overlay_bytes)
