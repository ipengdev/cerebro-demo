"""R4 — Employee Information Statement overlay builder.

Stamps data onto the original blank R4 form PDF (2 pages).
Page 1: Employee personal info
Page 2: Dependents table (landscape)
"""
from frappe.utils import flt, getdate, cint
from reportlab.lib.pagesizes import A4, landscape
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, translate, to_ar_num


def build_r4_pdf(emp, comp, dep_count, dependents):
    """Build R4 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder()
    addr = comp.get("address") or {}

    # ═══════════════ PAGE 1 (Portrait) ═══════════════════════

    # ── Company Info ──────────────────────────────────────────
    ob.text_r(500, 746, translate(comp.get("company_name") or comp.get("name")), size=8)
    ob.text_r(500, 722, translate(comp.get("trade_name") or ""), size=7)

    # Registration number boxes
    tax_id = comp.get("tax_id") or ""
    if tax_id:
        ob.digit_boxes(230, 739, tax_id, box_width=13, size=8)

    # ── Employee Identification ───────────────────────────────
    # Has personal tax number? checkboxes
    personal_tax = emp.get("tax_id") or ""
    ob.checkbox(345, 684, bool(personal_tax), size=7)  # نعم
    ob.checkbox(310, 684, not bool(personal_tax), size=7)  # كلا
    if personal_tax:
        ob.digit_boxes(200, 684, personal_tax, box_width=13, size=7)

    # 1. Name
    ob.text_r(490, 652, translate(emp.get("first_name") or emp.get("employee_name") or ""), size=8)
    # 2. Surname
    ob.text_r(280, 639, translate(emp.get("last_name") or emp.get("family_name") or ""), size=8)
    # 3. Father's name
    ob.text_r(490, 612, translate(emp.get("father_name") or ""), size=8)
    # 4. Mother's name
    ob.text_r(280, 597, translate(emp.get("mother_name") or ""), size=8)
    # 5. Gender
    gender = (emp.get("gender") or "").lower()
    ob.checkbox(415, 582, gender in ("male", "ذكر"), size=7)
    ob.checkbox(358, 582, gender in ("female", "أنثى"), size=7)
    # 6. Nationality
    ob.text_r(350, 567, translate(emp.get("nationality") or "", "nationality"), size=7)
    # 7. Birth place
    ob.text_r(490, 552, translate(emp.get("place_of_birth") or emp.get("mohafaza") or "", "city"), size=7)
    # 8. Date of birth
    dob = emp.get("date_of_birth")
    if dob:
        d = getdate(dob)
        ob.text_c(200, 552, to_ar_num(str(d.day).zfill(2)), size=7)
        ob.text_c(170, 552, to_ar_num(str(d.month).zfill(2)), size=7)
        ob.text_c(120, 552, to_ar_num(str(d.year)), size=7)
    # 9. Register number
    ob.text_r(490, 536, emp.get("register_number") or "", size=7)
    # 10. Register place
    ob.text_r(340, 536, translate(emp.get("register_place") or "", "city"), size=7)
    # 11. ID card number
    ob.text_r(200, 536, emp.get("national_id_number") or "", size=7)
    # 12. Marital status
    marital = (emp.get("marital_status") or "").lower()
    ob.checkbox(400, 504, marital in ("single", "أعزب"), size=7)
    ob.checkbox(345, 504, marital in ("married", "متزوج"), size=7)
    ob.checkbox(300, 504, marital in ("widowed", "أرمل"), size=7)
    ob.checkbox(260, 504, marital in ("divorced", "مطلق"), size=7)
    # 13. Pay type
    salary_mode = (emp.get("salary_mode") or "Monthly").lower()
    ob.checkbox(195, 484, salary_mode == "monthly", size=7)
    ob.checkbox(135, 484, salary_mode == "daily", size=7)
    ob.checkbox(88, 484, salary_mode in ("hourly", "hour"), size=7)
    # 14. Children on employee's charge
    ob.text_c(440, 452, to_ar_num(str(dep_count)) if dep_count else "", size=7)

    # ── Spouse Section ────────────────────────────────────────
    spouse_name = translate(emp.get("spouse_name") or "")
    ob.text_r(490, 424, spouse_name, size=7)

    # ── Address ───────────────────────────────────────────────
    emp_state = translate(emp.get("state") or addr.get("state") or "", "state")
    emp_city = translate(emp.get("city") or addr.get("city") or "", "city")
    emp_addr1 = emp.get("current_address") or addr.get("address_line1") or ""

    ob.text_r(490, 182, emp_state, size=7)   # محافظة
    ob.text_r(370, 182, emp_city, size=7)    # قضاء
    ob.text_r(490, 169, emp_addr1[:50], size=6)  # الشارع
    ob.text_r(490, 144, emp.get("cell_phone") or addr.get("phone") or "", size=7)  # هاتف
    ob.text_r(490, 114, addr.get("email_id") or emp.get("personal_email") or "", size=7)  # البريد الالكتروني

    # ── Declaration ───────────────────────────────────────────
    ob.text_r(490, 86, translate(emp.get("employee_name") or ""), size=7)

    # ═══════════════ PAGE 2 (Landscape) ══════════════════════
    ob.new_page(pagesize=landscape(A4))

    # Dependents table (up to 6 rows)
    # Row Y positions for landscape page (595pt height, table area roughly y=420-540)
    row_start_y = 461
    row_height = 40

    for i, dep in enumerate(dependents[:6]):
        y = row_start_y - i * row_height
        # Name
        ob.text_r(780, y, dep.get("name") or "", size=7)
        # DOB
        if dep.get("date_of_birth"):
            d = getdate(dep["date_of_birth"])
            ob.text_c(580, y, to_ar_num(d.strftime("%d/%m/%Y")), size=6)

    # Total family deduction
    if dep_count:
        ob.text_l(100, 254, to_ar_num(str(dep_count)), size=8)

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r4_blank.pdf", overlay_bytes)
