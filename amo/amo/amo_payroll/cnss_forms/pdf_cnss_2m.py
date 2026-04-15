"""CNSS 2M \u2014 \u0625\u0641\u0627\u062f\u0629 \u0639\u0645\u0644 (Work Certificate) overlay builder.

Stamps data onto the official blank CNSS 2M form PDF.
One page per employee.  Coordinates are in portrait A4 space (595 x 842).
"""

from frappe.utils import flt, formatdate, getdate
from .cnss_overlay import (
    PortraitOverlayBuilder, merge_overlay, fmt_western, ar,
)

MONTH_NAMES_AR = {
    1: "\u0643\u0627\u0646\u0648\u0646 \u0627\u0644\u062b\u0627\u0646\u064a",
    2: "\u0634\u0628\u0627\u0637",
    3: "\u0622\u0630\u0627\u0631",
    4: "\u0646\u064a\u0633\u0627\u0646",
    5: "\u0623\u064a\u0627\u0631",
    6: "\u062d\u0632\u064a\u0631\u0627\u0646",
    7: "\u062a\u0645\u0648\u0632",
    8: "\u0622\u0628",
    9: "\u0623\u064a\u0644\u0648\u0644",
    10: "\u062a\u0634\u0631\u064a\u0646 \u0627\u0644\u0623\u0648\u0644",
    11: "\u062a\u0634\u0631\u064a\u0646 \u0627\u0644\u062b\u0627\u0646\u064a",
    12: "\u0643\u0627\u0646\u0648\u0646 \u0627\u0644\u0623\u0648\u0644",
}

# -- Y positions for key form fields (portrait A4, origin bottom-left) --
# Calibrated from blank form grid analysis
Y_COMPANY_NAME = 712       # company name on underline at ov_y=708
Y_EMP_NAME = 672           # "yufid an al-ajir :" underline at ov_y=671
Y_WORK_PERIOD = 650        # "amal khilal al-sitta ashhur ..."

# -- Digit box cell centres (overlay x coords, left to right) ----------
# Company boxes: 7 cells, box spans ov_y 708–731, center y=716
COMPANY_BOX_CELLS = [36.6, 55.9, 75.4, 95.7, 119.3, 143.0, 164.2]
COMPANY_BOX_Y = 716
# Employee boxes: 7 cells, box spans ov_y 666–689, center y=674
EMPLOYEE_BOX_CELLS = [36.6, 55.9, 75.4, 97.2, 120.8, 143.0, 164.2]
EMPLOYEE_BOX_Y = 674

# -- Monthly table --
TABLE_HEADER_Y = 615
TABLE_ROW_START = 594
TABLE_ROW_H = 25
TABLE_ROWS = 7

# -- Table column x positions --
COL_MONTH = 546            # \u0627\u0644\u0634\u0647\u0631 (rightmost)
COL_DAYS = 440             # \u0639\u062f\u062f \u0627\u064a\u0627\u0645 \u0627\u0648 \u0627\u0633\u0627\u0628\u064a\u0639
COL_FROM1 = 360            # \u0645\u0646 (first period)
COL_TO1 = 300              # \u0627\u0644\u0649 (first period)
COL_FROM2 = 215            # \u0645\u0646 (second period)
COL_TO2 = 155              # \u0627\u0644\u0649 (second period)
COL_FROM3 = 95             # \u0645\u0646 (first/last month)
COL_TO3 = 40               # \u0627\u0644\u0649 (first/last month)

# -- Salary section --
Y_SALARY_BOX_TOP = 405
Y_SALARY_TOTAL = 370
Y_SALARY_DETAIL_LABEL = 355
Y_SALARY_ROW_START = 340
Y_SALARY_ROW_H = 18

# -- Checkboxes --
Y_CHECKBOX_SALARY_CONT = 248
Y_CHECKBOX_SALARY_STOP = 230
Y_CHECKBOX_NOT_WORK = 208
Y_CHECKBOX_WORK = 188
X_CHECKBOX = 457


def _place_digits_in_cells(ob, cell_centres, y, digits_str, size=9):
    """Place digits right-justified into exact cell centre positions."""
    digits = str(digits_str).strip()
    if not digits:
        return
    # Right-justify: last digit goes in rightmost cell
    n_cells = len(cell_centres)
    offset = n_cells - len(digits)
    for i, ch in enumerate(digits):
        cell_idx = offset + i
        if 0 <= cell_idx < n_cells:
            ob.text_c(cell_centres[cell_idx], y, ch, size=size)


def build_cnss_2m(data):
    """Build CNSS 2M work certificate PDF (one page per employee)."""
    ob = PortraitOverlayBuilder()
    employees = data.get("employees", [])

    for emp_idx, emp in enumerate(employees):
        if emp_idx > 0:
            ob.new_page()

        # -- Company CNSS number (digit boxes) ---------------------
        tax_id = data.get("tax_id") or ""
        if tax_id:
            _place_digits_in_cells(ob, COMPANY_BOX_CELLS, COMPANY_BOX_Y, tax_id)

        # -- Employee CNSS number (digit boxes) --------------------
        cnss_num = emp.get("cnss_number") or ""
        if cnss_num:
            _place_digits_in_cells(ob, EMPLOYEE_BOX_CELLS, EMPLOYEE_BOX_Y, cnss_num)

        # -- Company name (on underline below "ان رب العمل...") ----
        ob.text_r(540, Y_COMPANY_NAME, data["company_name"], size=8, bold=True)

        # -- Employee name -----------------------------------------
        ob.text_r(390, Y_EMP_NAME, emp.get("employee_name", ""), size=8, bold=True)

        # -- Work period (months worked count) ---------------------
        months_worked = emp.get("months_worked", 0)
        ob.text_c(310, Y_WORK_PERIOD, str(months_worked), size=9, bold=True)

        # -- Monthly breakdown table -------------------------------
        monthly_data = emp.get("monthly_data", [])
        for i in range(TABLE_ROWS):
            y = TABLE_ROW_START - i * TABLE_ROW_H
            if i < len(monthly_data):
                m = monthly_data[i]
                # Month name
                month_name = m.get("month_name", "")
                ob.text_c(COL_MONTH, y, month_name, size=7)
                # Days worked
                ob.text_c(COL_DAYS, y, str(m.get("days_worked", "")), size=7)
                # Date range
                from_d = formatdate(m.get("from_date"), "dd/MM/yyyy") if m.get("from_date") else ""
                to_d = formatdate(m.get("to_date"), "dd/MM/yyyy") if m.get("to_date") else ""
                ob.text_c(COL_FROM1, y, from_d, size=6)
                ob.text_c(COL_TO1, y, to_d, size=6)

        # -- Salary section ----------------------------------------
        last_3m_total = emp.get("last_3m_total", 0)
        ob.number_r(170, Y_SALARY_TOTAL, last_3m_total, size=8, bold=True)

        last_3m_salaries = emp.get("last_3m_salaries", [])
        for j, sal in enumerate(last_3m_salaries):
            y = Y_SALARY_ROW_START - j * Y_SALARY_ROW_H
            ob.text_r(480, y, sal.get("month_name", ""), size=7)
            ob.number_r(235, y, sal.get("amount", 0), size=7)

        # -- Checkboxes --------------------------------------------
        salary_cont = emp.get("salary_continued", True)
        ob.checkbox(X_CHECKBOX, Y_CHECKBOX_SALARY_CONT, salary_cont)
        ob.checkbox(X_CHECKBOX, Y_CHECKBOX_SALARY_STOP, not salary_cont)

    return merge_overlay("cnss_2m_blank.pdf", ob.get_overlay_bytes())
