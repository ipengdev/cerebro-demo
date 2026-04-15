"""R3 — New Employee Registration overlay builder.

Stamps data onto the original blank R3 form PDF.
"""
from frappe.utils import flt, getdate, cint
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, translate, to_ar_num


def build_r3_pdf(emp, comp):
    """Build R3 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder()
    addr = comp.get("address") or {}

    # ── Company Info ──────────────────────────────────────────
    ob.text_r(495, 757, translate(comp.get("company_name") or comp.get("name")), size=8)
    ob.text_r(310, 757, translate(comp.get("trade_name") or ""), size=7)

    # Registration number boxes (y≈740)
    tax_id = comp.get("tax_id") or ""
    if tax_id:
        ob.digit_boxes(430, 734, tax_id, box_width=13, size=8)

    # ── Employee Identification ───────────────────────────────
    # Has personal tax number? checkboxes (نعم / كلا)
    personal_tax = emp.get("tax_id") or ""
    ob.checkbox(345, 700, bool(personal_tax), size=7)  # نعم
    ob.checkbox(310, 700, not bool(personal_tax), size=7)  # كلا
    if personal_tax:
        ob.digit_boxes(205, 700, personal_tax, box_width=13, size=7)

    # 1. Name
    ob.text_r(490, 682, translate(emp.get("first_name") or emp.get("employee_name") or ""), size=8)
    # 2. Surname
    ob.text_r(280, 667, translate(emp.get("last_name") or emp.get("family_name") or ""), size=8)
    # 3. Father's name
    ob.text_r(490, 646, translate(emp.get("father_name") or ""), size=8)
    # 4. Mother's name and maiden name
    ob.text_r(280, 631, translate(emp.get("mother_name") or ""), size=8)
    # 5. Gender checkboxes (ذكر / أنثى)
    gender = (emp.get("gender") or "").lower()
    ob.checkbox(420, 614, gender in ("male", "ذكر"), size=7)
    ob.checkbox(370, 614, gender in ("female", "أنثى"), size=7)
    # 6. Nationality
    ob.text_r(350, 594, translate(emp.get("nationality") or "", "nationality"), size=7)
    # 7. Birth place
    ob.text_r(490, 581, translate(emp.get("place_of_birth") or emp.get("mohafaza") or "", "city"), size=7)
    # 8. Date of birth
    dob = emp.get("date_of_birth")
    if dob:
        d = getdate(dob)
        ob.text_c(228, 581, to_ar_num(str(d.day).zfill(2)), size=7)
        ob.text_c(205, 581, to_ar_num(str(d.month).zfill(2)), size=7)
        ob.text_c(170, 581, to_ar_num(str(d.year)), size=7)
    # 9. Register number
    ob.text_r(490, 562, emp.get("register_number") or "", size=7)
    # 10. Register place
    ob.text_r(355, 562, translate(emp.get("register_place") or "", "city"), size=7)
    # 11. ID card number
    ob.text_r(210, 562, emp.get("national_id_number") or "", size=7)
    # 12. Marital status checkboxes
    marital = (emp.get("marital_status") or "").lower()
    ob.checkbox(400, 549, marital in ("single", "أعزب"), size=7)
    ob.checkbox(347, 549, marital in ("married", "متزوج"), size=7)
    ob.checkbox(305, 549, marital in ("widowed", "أرمل"), size=7)
    ob.checkbox(268, 549, marital in ("divorced", "مطلق"), size=7)
    # 13. Children count (only show if > 0)
    children = cint(emp.get("number_of_dependent_children", 0))
    if children:
        ob.text_c(210, 534, to_ar_num(str(children)), size=7)
    # 14. Work start date
    joining = emp.get("date_of_joining")
    if joining:
        d = getdate(joining)
        ob.text_c(375, 539, to_ar_num(str(d.day).zfill(2)), size=7)
        ob.text_c(345, 539, to_ar_num(str(d.month).zfill(2)), size=7)
        ob.text_c(310, 539, to_ar_num(str(d.year)), size=7)
    # 15. Social security number
    ob.text_r(210, 522, emp.get("social_security_number") or emp.get("cnss_number") or "", size=7)
    # 16. Pay type checkboxes
    salary_mode = (emp.get("salary_mode") or "Monthly").lower()
    ob.checkbox(198, 522, salary_mode == "monthly", size=7)
    ob.checkbox(135, 522, salary_mode == "daily", size=7)
    ob.checkbox(88, 522, salary_mode in ("hourly", "hour"), size=7)

    # ── Spouse Information ────────────────────────────────────
    spouse_name = translate(emp.get("spouse_name") or "")
    ob.text_r(490, 498, spouse_name, size=7)

    # ── Address Section ───────────────────────────────────────
    # Employee address
    emp_state = translate(emp.get("state") or addr.get("state") or "", "state")
    emp_city = translate(emp.get("city") or addr.get("city") or "", "city")
    emp_addr1 = emp.get("current_address") or addr.get("address_line1") or ""

    ob.text_r(490, 254, emp_state, size=7)  # محافظة
    ob.text_r(370, 254, emp_city, size=7)   # قضاء
    ob.text_r(490, 242, emp_addr1[:50], size=6)  # الشارع
    ob.text_r(490, 218, emp.get("cell_phone") or addr.get("phone") or "", size=7)  # هاتف

    # ── Declaration ───────────────────────────────────────────
    ob.text_r(490, 151, translate(emp.get("employee_name") or ""), size=7)

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r3_blank.pdf", overlay_bytes)
