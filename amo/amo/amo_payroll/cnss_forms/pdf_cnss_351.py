"""CNSS 351 — Annual Contributions Table overlay builder.

Stamps data onto the official blank CNSS 351 form PDF.
All coordinates are in visual landscape space (842 wide × 595 tall).
Grid-calibrated from blank form analysis.
"""

from frappe.utils import flt
from .cnss_overlay import (
    LandscapeOverlayBuilder, merge_overlay, fmt_western,
)

# -- Column centres (visual x) — calibrated from grid lines --------
#    Grid vertical lines: 804, 777, 741, 637, 597, 498, 358, 241, ...
COL_EMP_COUNT = 759      # عدد الأجراء    (cell 741–777, center 759)
COL_WAGES = 689          # الأجور ولواحقها (cell 637–741, center 689)
COL_SUBS_DUE = 547       # الاشتراكات المستحقة (cell 498–597, center 547)
COL_DUE = 299            # المتوجب         (cell 241–358, center 299)

# -- Row centres (visual y) — calibrated from grid lines -----------
#    Grid horizontal lines: 394 (data top), 331, 258, 206 (table bottom)
ROW_BRANCH3 = 363        # فرع /3/ المرض والأمومة (9%)   [394–331 → 363]
ROW_BRANCH1 = 295        # فرع /1/ نهاية الخدمة (8.5%)   [331–258 → 295]
ROW_BRANCH2 = 232        # فرع /2/ التعويضات العائلية (6%) [258–206 → 232]


def build_cnss_351(data):
    """Build CNSS 351 annual form PDF by overlaying data on the blank form."""
    ob = LandscapeOverlayBuilder()
    totals = data["totals"]
    emp_count = str(data["employee_count"])

    # -- Year in title (dots area after "لعام") ----------------------
    ob.text_c(445, 555, str(data["year"]), size=10, bold=True)

    # -- Company info (right side) — aligned with pre-printed labels
    ob.text_r(723, 491, data["company_name"], size=8, bold=True)
    tax_id = data.get("tax_id") or ""
    if tax_id:
        ob.text_r(723, 463, tax_id, size=8, bold=True)

    # -- Branch rows -----------------------------------------------
    branches = [
        {"y": ROW_BRANCH3, "wages": totals["medical_capped"], "due": totals["branch3_due"], "rate": "9"},
        {"y": ROW_BRANCH1, "wages": totals["gross"], "due": totals["employer_eos"], "rate": "8.5"},
        {"y": ROW_BRANCH2, "wages": totals["family_capped"], "due": totals["employer_family"], "rate": "6"},
    ]

    for br in branches:
        y = br["y"]
        ob.text_c(COL_EMP_COUNT, y, emp_count, size=9)
        ob.number_c(COL_WAGES, y, br["wages"], size=9)
        ob.number_c(COL_SUBS_DUE, y, br["due"], size=8)
        ob.number_c(COL_DUE, y, br["due"], size=9, bold=True)
        # Calculation annotation
        ann = "\u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643\u0627\u062a = {} x %{} = {}".format(
            fmt_western(br["wages"]), br["rate"], fmt_western(br["due"])
        )
        ob.text_r(635, y - 18, ann, size=6)

    # -- Bottom summary -------------------------------------------
    total_subs = (
        flt(totals["branch3_due"])
        + flt(totals["employer_eos"])
        + flt(totals["employer_family"])
    )
    ob.number_r(595, 190, total_subs, size=9, bold=True)

    return merge_overlay("cnss_351_blank.pdf", ob.get_overlay_bytes())
