"""CNSS 190A — Monthly Contributions Table overlay builder.

Stamps data onto the official blank CNSS 190A form PDF.
All coordinates are in visual landscape space (842 wide × 595 tall).
Grid-calibrated from blank form analysis.
"""

from frappe.utils import flt
from .cnss_overlay import (
    LandscapeOverlayBuilder, merge_overlay, fmt_western,
)

# -- Column centres (visual x) — calibrated from grid lines --------
#    Grid vertical lines: 802, 775, 739, 626, 590, 482, 356, 262, ...
COL_EMP_COUNT = 757      # عدد الأجراء    (cell 739–775, center 757)
COL_WAGES = 683          # الأجور ولواحقها (cell 626–739, center 683)
COL_SUBS_DUE = 536       # الاشتراكات المستحقة (cell 482–590, center 536)
COL_DUE = 309            # المتوجب         (cell 262–356, center 309)

# -- Row centres (visual y) — calibrated from grid lines -----------
#    Grid horizontal lines: 415 (data top), 345, 272, 199 (table bottom)
ROW_BRANCH3 = 380        # فرع /3/ المرض والأمومة (9%)   [415–345 → 380]
ROW_BRANCH1 = 309        # فرع /1/ نهاية الخدمة (8.5%)   [345–272 → 309]
ROW_BRANCH2 = 236        # فرع /2/ التعويضات العائلية (6%) [272–199 → 236]

# -- المتوجب column: numbers go ON the "x———" blank line (upper part of cell)
#    Extracted from blank form text positions:
#    Branch 3: "x———" at cy=397, Branch 1: cy=328, Branch 2: cy=255
DUE_Y_BRANCH3 = 395      # slightly below the x-line baseline at 397
DUE_Y_BRANCH1 = 326      # slightly below the x-line baseline at 328
DUE_Y_BRANCH2 = 253      # slightly below the x-line baseline at 255


def build_cnss_190a(data):
    """Build CNSS 190A monthly form PDF by overlaying data on the blank form."""
    ob = LandscapeOverlayBuilder()
    totals = data["totals"]
    emp_count = str(data["employee_count"])

    # -- Period in title -------------------------------------------
    period = "{} / {}".format(data["month_name"], data["year"])
    ob.text_c(460, 562, period, size=10, bold=True)

    # -- Company info (right side) — aligned with pre-printed labels
    ob.text_r(728, 508, data["company_name"], size=8, bold=True)
    tax_id = data.get("tax_id") or ""
    if tax_id:
        ob.text_r(725, 470, tax_id, size=8, bold=True)

    # -- Branch rows -----------------------------------------------
    branches = [
        {"y": ROW_BRANCH3, "due_y": DUE_Y_BRANCH3, "wages": totals["medical_capped"], "due": totals["branch3_due"], "rate": "9"},
        {"y": ROW_BRANCH1, "due_y": DUE_Y_BRANCH1, "wages": totals["gross"], "due": totals["employer_eos"], "rate": "8.5"},
        {"y": ROW_BRANCH2, "due_y": DUE_Y_BRANCH2, "wages": totals["family_capped"], "due": totals["employer_family"], "rate": "6"},
    ]

    for br in branches:
        y = br["y"]
        ob.text_c(COL_EMP_COUNT, y, emp_count, size=9)
        ob.number_c(COL_WAGES, y, br["wages"], size=9)
        ob.number_c(COL_SUBS_DUE, y, br["due"], size=8)
        # المتوجب number positioned ON the "x———" blank line
        ob.number_c(COL_DUE, br["due_y"], br["due"], size=9, bold=True)
        # Calculation annotation below data, within formula area
        ann = "\u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643\u0627\u062a = {} x %{} = {}".format(
            fmt_western(br["wages"]), br["rate"], fmt_western(br["due"])
        )
        ob.text_r(625, y - 18, ann, size=6)

    # -- Bottom summary -------------------------------------------
    total_subs = (
        flt(totals["branch3_due"])
        + flt(totals["employer_eos"])
        + flt(totals["employer_family"])
    )
    ob.number_r(590, 190, total_subs, size=9, bold=True)

    return merge_overlay("cnss_190a_blank.pdf", ob.get_overlay_bytes())
