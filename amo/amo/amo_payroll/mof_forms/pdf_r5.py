"""R5 — Annual Tax Declaration overlay builder.

Stamps data onto the original blank R5 form PDF.
"""
from frappe.utils import flt, getdate
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, fmt_number, translate, to_ar_num


def build_r5_pdf(data):
    """Build R5 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder()
    comp = data["company"]
    addr = comp.get("address") or {}
    year = data["year"]
    board = data["board"]
    emp = data["employees"]
    lump = data["lump_sum"]
    totals = data["totals"]
    payments = data.get("payments", [])

    # ── Company Info ──────────────────────────────────────────
    ob.text_r(515, 769, translate(comp.get("company_name") or comp.get("name")), size=8)
    ob.text_r(515, 724, translate(comp.get("trade_name") or ""), size=8)

    # Registration number (digit boxes)
    tax_id = comp.get("tax_id") or ""
    if tax_id:
        ob.digit_boxes(502, 751, tax_id, box_width=13, size=8)

    # ── Year / Period ─────────────────────────────────────────
    # Fiscal year from/to (RTL: from has year/month/day, to has day/month/year)
    ob.text_c(242, 749, to_ar_num(str(year)), size=7)   # from.year
    ob.text_c(210, 749, to_ar_num("01"), size=7)        # from.month
    ob.text_c(183, 749, to_ar_num("01"), size=7)        # from.day
    ob.text_c(120, 749, to_ar_num("31"), size=7)        # to.day
    ob.text_c(90, 749, to_ar_num("12"), size=7)         # to.month
    ob.text_c(58, 749, to_ar_num(str(year)), size=7)    # to.year

    # Period from/to
    ob.text_c(242, 732, to_ar_num(str(year)), size=7)   # from.year
    ob.text_c(210, 732, to_ar_num("01"), size=7)        # from.month
    ob.text_c(183, 732, to_ar_num("01"), size=7)        # from.day
    ob.text_c(120, 732, to_ar_num("31"), size=7)        # to.day
    ob.text_c(90, 732, to_ar_num("12"), size=7)         # to.month
    ob.text_c(58, 732, to_ar_num(str(year)), size=7)    # to.year

    # ── Main Address (عنوان المركز الرئيسي) ───────────────────
    ob.text_r(520, 692, translate(addr.get("state") or "", "state"), size=7)   # محافظة
    ob.text_r(390, 680, translate(addr.get("city") or "", "city"), size=7)     # قضاء
    ob.text_r(520, 668, addr.get("address_line2") or "", size=7)              # منطقة - بلدة
    ob.text_r(520, 656, addr.get("address_line1") or "", size=7)              # الشارع
    ob.text_r(520, 615, addr.get("phone") or "", size=7)                     # هاتف
    ob.text_r(520, 587, addr.get("email_id") or "", size=7)                  # البريد الالكتروني

    # ── Counts ────────────────────────────────────────────────
    ob.text_c(400, 490, to_ar_num(str(board.get("count", 0) or "")), size=8)
    ob.text_c(400, 478, to_ar_num(str(emp.get("count", 0) or "")), size=8)

    # ── Tax Table (Board col ≈ x=330, Employee col ≈ x=140) ──
    col_b = 330
    col_e = 140

    lines_y = {
        100: 432, 110: 416, 120: 400,
        130: 384, 140: 368, 150: 352,
        160: 336, 170: 320, 180: 304, 190: 288,
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
        ob.number_c(195, 256, lump["line_240"], size=7)
    if flt(lump.get("line_250")):
        ob.number_c(195, 240, lump["line_250"], size=7)

    # ── Totals (left) ─────────────────────────────────────────
    t_y = {251: 210, 260: 194, 261: 178, 262: 163,
           270: 148, 280: 133, 290: 118, 300: 103}
    for code, y in t_y.items():
        val = totals.get(f"line_{code}", 0)
        if flt(val):
            ob.number_c(195, y, val, size=7)

    # ── Periodic Payments (right) ─────────────────────────────
    pay_y = [196, 178, 150, 135]
    for i, py in enumerate(pay_y):
        if i < len(payments):
            p = payments[i]
            if flt(p.get("amount")):
                ob.number_c(520, py, p["amount"], size=7)
            if p.get("date"):
                d = getdate(p["date"])
                ob.text_c(455, py, to_ar_num(d.strftime("%d/%m/%Y")), size=6)

    total_paid = data.get("total_paid", 0)
    if flt(total_paid):
        ob.number_c(520, 103, total_paid, size=7)

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r5_blank.pdf", overlay_bytes)
