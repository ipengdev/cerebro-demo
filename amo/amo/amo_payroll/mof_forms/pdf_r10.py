"""R10 — Periodic Tax Payment Statement overlay builder.

Stamps data onto the original blank R10 form PDF.
"""
from frappe.utils import flt, getdate
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, fmt_number, translate, to_ar_num


def build_r10_pdf(data):
    """Build R10 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder()
    comp = data["company"]
    addr = comp.get("address") or {}
    year = data["year"]
    board = data["board"]
    emp = data["employees"]
    lump = data["lump_sum"]
    totals = data["totals"]
    start_date = data.get("start_date", f"{year}-01-01")
    end_date = data.get("end_date", f"{year}-12-31")

    # ── Company Info ──────────────────────────────────────────
    ob.text_r(510, 772, translate(comp.get("company_name") or comp.get("name")), size=8)
    ob.text_r(510, 712, translate(comp.get("trade_name") or ""), size=7)

    # Registration number boxes
    tax_id = comp.get("tax_id") or ""
    if tax_id:
        ob.digit_boxes(498, 752, tax_id, box_width=13, size=8)

    # ── Year / Period ─────────────────────────────────────────
    sd = getdate(start_date)
    ed = getdate(end_date)

    # Fiscal year from/to (RTL: from has year/month/day, to has day/month/year)
    ob.text_c(242, 746, to_ar_num(str(sd.year)), size=7)            # from.year
    ob.text_c(210, 746, to_ar_num(str(sd.month).zfill(2)), size=7)  # from.month
    ob.text_c(183, 746, to_ar_num(str(sd.day).zfill(2)), size=7)    # from.day
    ob.text_c(120, 746, to_ar_num(str(ed.day).zfill(2)), size=7)    # to.day
    ob.text_c(90, 746, to_ar_num(str(ed.month).zfill(2)), size=7)   # to.month
    ob.text_c(58, 746, to_ar_num(str(ed.year)), size=7)             # to.year

    # Period from/to
    ob.text_c(242, 732, to_ar_num(str(sd.year)), size=7)            # from.year
    ob.text_c(210, 732, to_ar_num(str(sd.month).zfill(2)), size=7)  # from.month
    ob.text_c(183, 732, to_ar_num(str(sd.day).zfill(2)), size=7)    # from.day
    ob.text_c(120, 732, to_ar_num(str(ed.day).zfill(2)), size=7)    # to.day
    ob.text_c(90, 732, to_ar_num(str(ed.month).zfill(2)), size=7)   # to.month
    ob.text_c(58, 732, to_ar_num(str(ed.year)), size=7)             # to.year

    # ── Representative ────────────────────────────────────────
    rep_name = comp.get("company_representative") or ""
    ob.text_r(420, 694, rep_name, size=7)

    # ── Main Address ──────────────────────────────────────────
    ob.text_r(520, 647, translate(addr.get("state") or "", "state"), size=7)     # محافظة
    ob.text_r(372, 647, translate(addr.get("city") or "", "city"), size=7)       # قضاء (same line)
    ob.text_r(520, 624, addr.get("address_line1") or "", size=7)                # الشارع
    ob.text_r(345, 588, addr.get("phone") or "", size=7)                        # هاتف
    ob.text_r(520, 564, addr.get("email_id") or "", size=7)                     # البريد الالكتروني

    # ── Counts ────────────────────────────────────────────────
    ob.text_c(398, 454, to_ar_num(str(board.get("count", 0) or "")), size=8)
    ob.text_c(398, 441, to_ar_num(str(emp.get("count", 0) or "")), size=8)

    # ── Tax Table ─────────────────────────────────────────────
    col_b = 325
    col_e = 140

    lines_y = {
        100: 394, 110: 379, 120: 364,
        130: 348, 140: 332, 150: 316,
        160: 302, 170: 287, 180: 272, 190: 256,
    }

    for code, y in lines_y.items():
        bval = board.get(f"line_{code}", 0)
        eval_ = emp.get(f"line_{code}", 0)
        if flt(bval):
            ob.number_c(col_b, y, bval, size=7)
        if flt(eval_):
            ob.number_c(col_e, y, eval_, size=7)

    # ── Lump Sum ──────────────────────────────────────────────
    if flt(lump.get("line_240")):
        ob.number_c(195, 209, lump["line_240"], size=7)
    if flt(lump.get("line_250")):
        ob.number_c(195, 192, lump["line_250"], size=7)

    # ── Totals ────────────────────────────────────────────────
    t_y = {260: 162, 270: 146, 280: 132, 290: 116, 300: 102}
    for code, y in t_y.items():
        val = totals.get(f"line_{code}", 0)
        if flt(val):
            ob.number_c(195, y, val, size=7)

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r10_blank.pdf", overlay_bytes)
