"""R6 — Annual Individual Income Statement overlay builder.

Stamps data onto the original blank R6 form PDF.
"""
from frappe.utils import flt, getdate, formatdate
from .pdf_overlay import OverlayBuilder, merge_overlay, ar, fmt_number, translate, to_ar_num


def build_r6_pdf(data):
    """Build R6 PDF by overlaying data on the blank form."""
    ob = OverlayBuilder()
    comp = data["company"]
    addr = comp.get("address") or {}
    emp = data["employee"]
    year = data["year"]
    lines = data["lines"]
    line_310 = data["line_310"]

    # ── Company Info ──────────────────────────────────────────
    ob.text_r(500, 772, translate(comp.get("company_name") or comp.get("name")), size=8)
    ob.text_r(500, 756, translate(comp.get("trade_name") or ""), size=7)

    # Registration number boxes
    tax_id = comp.get("tax_id") or ""
    if tax_id:
        ob.digit_boxes(490, 739, tax_id, box_width=13, size=8)

    # Year
    ob.text_c(60, 772, to_ar_num(str(year)), size=8)

    # Employee/wage count
    ob.text_c(60, 746, to_ar_num(str(data.get("emp_count", ""))), size=7)

    # Number entered from
    ob.text_c(38, 702, to_ar_num(str(data.get("emp_count", ""))), size=7)

    # ── Employee Info ─────────────────────────────────────────
    emp_name = translate(emp.get("employee_name") or "")
    father = translate(emp.get("father_name") or "")
    surname = translate(emp.get("last_name") or emp.get("family_name") or "")

    ob.text_r(500, 689, emp_name, size=8)
    ob.text_r(360, 689, father, size=7)
    ob.text_r(225, 689, surname, size=7)

    # Personal registration number
    personal_tax_id = emp.get("tax_id") or ""
    if personal_tax_id:
        ob.digit_boxes(470, 654, personal_tax_id, box_width=13, size=8)

    # Salary type checkboxes (شهري / يومي / بالساعة)
    salary_type = data.get("salary_type", "Monthly")
    ob.checkbox(138, 644, salary_type == "Monthly", size=7)
    ob.checkbox(95, 644, salary_type == "Daily", size=7)
    ob.checkbox(50, 644, salary_type == "Hourly", size=7)

    # Job type (designation) — translated to Arabic
    ob.text_r(340, 644, translate(emp.get("designation") or "", "designation"), size=7)

    # Marital status checkboxes
    marital = data.get("marital_status", "Single")
    ob.checkbox(470, 622, marital == "Single", size=7)
    ob.checkbox(420, 622, marital == "Married", size=7)
    ob.checkbox(375, 622, marital == "Widowed", size=7)
    ob.checkbox(340, 622, marital == "Divorced", size=7)

    # Children count
    ob.text_c(300, 622, to_ar_num(str(data.get("dep_count", 0) or "")), size=7)

    # Dependents count for family deduction
    dep_benefit = data.get("dep_count", 0)
    ob.text_c(180, 622, to_ar_num(str(dep_benefit)) if dep_benefit else "", size=7)

    # Work period from/to
    wf = data.get("work_from")
    wt = data.get("work_to")
    if wf:
        d = getdate(wf)
        ob.text_c(430, 606, to_ar_num(str(d.day).zfill(2)), size=6)
        ob.text_c(405, 606, to_ar_num(str(d.month).zfill(2)), size=6)
        ob.text_c(375, 606, to_ar_num(str(d.year)), size=6)
    if wt:
        d = getdate(wt)
        ob.text_c(310, 606, to_ar_num(str(d.day).zfill(2)), size=6)
        ob.text_c(285, 606, to_ar_num(str(d.month).zfill(2)), size=6)
        ob.text_c(255, 606, to_ar_num(str(d.year)), size=6)

    # ── Address ───────────────────────────────────────────────
    emp_addr = emp.get("current_address") or ""
    emp_state = translate(emp.get("state") or addr.get("state") or "", "state")
    emp_city = translate(emp.get("city") or addr.get("city") or "", "city")
    if emp_state:
        ob.text_r(520, 556, emp_state, size=6)   # محافظة
    if emp_city:
        ob.text_r(370, 556, emp_city, size=6)    # قضاء
    if emp_addr:
        ob.text_r(520, 544, emp_addr[:60], size=6)  # الشارع

    # ── Income Table ──────────────────────────────────────────
    # Three columns: Total (col1), Non-taxable (col2), Taxable (col3)
    col_total = 345
    col_nontax = 215
    col_tax = 90

    # Row Y positions
    income_y = {
        "100": 455, "110": 437, "120": 420, "130": 403, "140": 387,
        "150": 371, "160": 354, "170": 339, "180": 322, "190": 305,
        "200": 289, "210": 273, "220": 257, "230": 241,
        "240": 225, "250": 209, "260": 193, "300": 177,
    }

    for code, y in income_y.items():
        vals = lines.get(code, {})
        if flt(vals.get("total")):
            ob.number_c(col_total, y, vals["total"], size=6)
        if flt(vals.get("non_taxable")):
            ob.number_c(col_nontax, y, vals["non_taxable"], size=6)
        if flt(vals.get("taxable")):
            ob.number_c(col_tax, y, vals["taxable"], size=6)

    # Line 310 - Total
    if flt(line_310.get("total")):
        ob.number_c(col_total, 152, line_310["total"], size=7, bold=True)
    if flt(line_310.get("non_taxable")):
        ob.number_c(col_nontax, 152, line_310["non_taxable"], size=7)
    if flt(line_310.get("taxable")):
        ob.number_c(col_tax, 152, line_310["taxable"], size=7)

    # Deductions
    # Line 330 - Family deduction
    if flt(data.get("line_330")):
        ob.number_c(280, 119, data["line_330"], size=7)
    # Line 340 - Other deductions (CNSS)
    if flt(data.get("line_340")):
        ob.number_c(280, 102, data["line_340"], size=7)

    # Line 350 - Net taxable
    if flt(data.get("line_350")):
        ob.number_c(280, 76, data["line_350"], size=7, bold=True)
    # Line 360 - Annual tax
    if flt(data.get("line_360")):
        ob.number_c(280, 59, data["line_360"], size=7, bold=True)

    overlay_bytes = ob.get_overlay_bytes()
    return merge_overlay("r6_blank.pdf", overlay_bytes)
