"""CNSS Employee Leaving Notice — إشعار ترك العمل PDF builder.

Generates one page per employee matching the official CNSS leaving notice form.
"""

from frappe.utils import flt, formatdate
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

from .pdf_builder import (
    CnssPageBuilder, ar, fmt_number, LIGHT_BLUE, LIGHT_GRAY, BORDER,
)


def build_cnss_leaving(data):
    """Build CNSS Employee Leaving Notice PDF (one page per employee).

    Args:
        data: dict with keys:
            company_name, tax_id, address, phone,
            employees (list of dicts with employee data)
    """
    pb = CnssPageBuilder(pagesize=A4)
    W, H = pb.W, pb.H  # 595 x 842
    ML = 25
    MR = W - 25
    MT = H - 25
    MB = 25

    employees = data.get("employees", [])

    for emp_idx, emp in enumerate(employees):
        if emp_idx > 0:
            pb.new_page(A4)

        y = MT

        # ═══════════════════════════════════════════════════════
        #  Header
        # ═══════════════════════════════════════════════════════
        pb.text_c(W / 2, y, "الصندوق الوطني للضمان الإجتماعي", size=14, bold=True)
        y -= 16
        pb.text_c(W / 2, y, "بيروت - لبنان", size=9)
        y -= 20
        pb.text_c(W / 2, y, "إشعار ترك العمل", size=16, bold=True)

        # Underline
        tw = 140
        pb.hline(W / 2 - tw / 2, W / 2 + tw / 2, y - 2, width=1.5)
        y -= 8

        # Numbers on the right
        pb.text_r(MR, y, "رقم المؤسسة في الصندوق", size=7)
        pb.text_r(MR - 140, y, data["tax_id"], size=8, bold=True)
        y -= 14
        pb.text_r(MR, y, "رقم الأجير في الصندوق", size=7)
        pb.text_r(MR - 140, y, emp.get("cnss_number", ""), size=8, bold=True)

        # Header line
        y -= 10
        pb.hline(ML, MR, y, width=1.5)
        y -= 18

        # ═══════════════════════════════════════════════════════
        #  Employer declaration
        # ═══════════════════════════════════════════════════════
        pb.text_r(MR, y, "أن رب العمل الموقع أدناه المسؤول عن مؤسسة :", size=9)
        pb.text_r(MR - 250, y, data["company_name"], size=9, bold=True)
        y -= 18
        pb.text_r(MR, y, "الكائنة في :", size=9)
        pb.text_r(MR - 60, y, data["address"], size=8)
        y -= 22

        # Employee info
        pb.text_r(MR, y,
                  "يشعر الصندوق الوطني للضمان الإجتماعي بأن الأجير / المستخدم :",
                  size=9)
        pb.text_r(MR - 330, y, emp.get("employee_name", ""), size=9, bold=True)
        y -= 28

        # ═══════════════════════════════════════════════════════
        #  Employee details section
        # ═══════════════════════════════════════════════════════
        pb.text_r(MR, y, "بيانات الأجير", size=10, bold=True)
        y -= 4
        pb.hline(ML, MR, y, width=0.8)
        y -= 16

        details = [
            ("القسم :", emp.get("department", "")),
            ("المسمّى الوظيفي :", emp.get("designation", "")),
            ("تاريخ الإلتحاق بالعمل :", formatdate(emp.get("date_of_joining"), "dd/MM/yyyy") if emp.get("date_of_joining") else ""),
            ("تاريخ ترك العمل :", formatdate(emp.get("relieving_date"), "dd/MM/yyyy") if emp.get("relieving_date") else ""),
            ("مدة الخدمة :", f'{emp.get("years_of_service", "")} سنة'),
            ("سبب ترك العمل :", emp.get("reason_for_leaving", "")),
        ]

        for label, value in details:
            pb.text_r(MR, y, label, size=8)
            pb.text_r(MR - 120, y, str(value), size=8, bold=True)
            y -= 16

        y -= 10

        # ═══════════════════════════════════════════════════════
        #  Financial details
        # ═══════════════════════════════════════════════════════
        pb.text_r(MR, y, "البيانات المالية", size=10, bold=True)
        y -= 4
        pb.hline(ML, MR, y, width=0.8)
        y -= 16

        financials = [
            ("آخر أجر شهري :", f'{fmt_number(emp.get("last_salary", 0))} ل.ل.'),
            ("تعويض نهاية الخدمة المستحق :", f'{fmt_number(emp.get("eos_due", 0))} ل.ل.'),
        ]

        for label, value in financials:
            pb.text_r(MR, y, label, size=8)
            pb.text_r(MR - 160, y, value, size=8, bold=True)
            y -= 16

        y -= 10

        # ═══════════════════════════════════════════════════════
        #  Legal notice
        # ═══════════════════════════════════════════════════════
        box_top = y
        box_h = 35
        pb.box(ML, box_top - box_h, MR - ML, box_h)
        pb.text_r(MR - 5, box_top - 12,
                  "ملاحظة هامة:", size=7, bold=True)
        pb.text_r(MR - 5, box_top - 25,
                  "يجب إبلاغ الصندوق الوطني للضمان الإجتماعي بترك الأجير للعمل خلال مهلة أقصاها خمسة عشر يوماً من تاريخ ترك العمل.",
                  size=7)
        y = box_top - box_h - 14

        # ═══════════════════════════════════════════════════════
        #  Declaration
        # ═══════════════════════════════════════════════════════
        pb.text_r(MR, y,
                  "إن رب العمل الموقع أدناه يشهد على مسؤوليته أن المعلومات المصرح بها أعلاه هي مطابقة للحقيقة والواقع",
                  size=7)
        y -= 30

        # ═══════════════════════════════════════════════════════
        #  Signatures
        # ═══════════════════════════════════════════════════════
        pb.text_r(MR, y, "توقيع الأجير", size=7)
        pb.text_c(W / 2, y, "ختم المؤسسة وتوقيع رب العمل", size=7)
        pb.text_l(ML, y, "التاريخ: ___/___/ 20____", size=7)
        y -= 35
        pb.text_r(MR, y, "___________________________", size=7)
        pb.text_c(W / 2, y, "___________________________", size=7)

    return pb.get_pdf_bytes()
