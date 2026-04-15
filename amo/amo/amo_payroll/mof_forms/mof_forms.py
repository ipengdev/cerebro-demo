"""Lebanese Ministry of Finance (MoF) Official Tax Forms — PDF Generation.

Generates printable PDF versions of:
- R3:  طلب تسجيل مستخدم/أجير جديد  (New Employee Registration)
- R4:  بيان معلومات من المستخدم/الأجير الى رب العمل  (Employee Info Statement)
- R5:  تصريح سنوي عن ضريبة الدخل على الرواتب والأجور  (Annual Tax Declaration)
- R6:  كشف سنوي إفرادي بإجمالي إيرادات المستخدم/الأجير  (Annual Individual Income)
- R7:  كشف إجمالي بالمستخدمين الذين تركوا العمل خلال السنة  (Employees Who Left)
- R10: بيان دوري بتأدية ضريبة الرواتب والأجور  (Periodic Tax Statement)
"""

import os
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, get_last_day, date_diff, cint

from amo.amo_payroll.doctype.payroll_constants.payroll_constants import PayrollConstants
from amo.amo_payroll.report.mof_utils import compute_annual_tax, get_employee_tax_deductions


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# ── Salary component classification via custom fields ────────
# The fields `mof_r5_r10_line` and `mof_r6_line` on Salary Component
# hold the MoF report line mapping.  Values look like "100 - …".
# We extract the numeric prefix as the line code.

# Legacy hardcoded fallback lists (used when custom field is empty)
TRANSPORT_COMPONENTS = [
    "Transport Allowance", "Transportation Allowance", "بدل نقل",
]
REPRESENTATION_COMPONENTS = [
    "Representation Allowance", "بدل تمثيل",
]
FAMILY_SPOUSE_COMPONENTS = [
    "Family Allowance - LB", "تعويض عائلي عن الزوجة",
]
FAMILY_CHILD_COMPONENTS = [
    "Family Allowance Children", "تعويض عائلي عن الأولاد",
]
HOUSING_COMPONENTS = [
    "Housing Allowance", "Housing Allowance - LB", "بدل سكن",
]
CAR_COMPONENTS = [
    "Car Allowance", "بدل سيارة",
]
FOOD_COMPONENTS = [
    "Food Allowance", "Meal Vouchers", "بدل طعام",
]
CLOTHING_COMPONENTS = [
    "Clothing Allowance", "بدل ملبس",
]
FUND_COMPONENTS = [
    "Fund Compensation", "تعويض صندوق",
]
HEALTH_COMPONENTS = [
    "Health Insurance", "تأمينات صحية",
]
EDUCATION_COMPONENTS = [
    "Schooling Allowance", "Education Grant", "منح تعليم",
]
MARRIAGE_COMPONENTS = [
    "Marriage Grant", "منح زواج",
]
BIRTH_COMPONENTS = [
    "Birth Grant", "منح ولادة",
]
SICK_COMPONENTS = [
    "Sick Leave Assistance", "مساعدات مرضية",
]
DEATH_COMPONENTS = [
    "Death Assistance", "مساعدات وفاة",
]
EOS_COMPONENTS = [
    "End of Service Indemnity", "Leave Encashment",
]
CNSS_EE_COMPONENTS = [
    "CNSS Employee", "CNSS Employee - Sickness (2%)", "CNSS Employee - Maternity (1%)",
    "NSSF Employee Contribution",
]
TAX_COMPONENTS_CACHE = None

# Cache: component_name → {"r5_r10": "100", "r6": "150"}
_COMPONENT_MAP_CACHE = None


def _reset_caches():
    """Reset all module-level caches (call at top of each report entry point)."""
    global _COMPONENT_MAP_CACHE, TAX_COMPONENTS_CACHE
    _COMPONENT_MAP_CACHE = None
    TAX_COMPONENTS_CACHE = None


def _load_component_map():
    """Load all Salary Component MoF field mappings into a cache dict."""
    global _COMPONENT_MAP_CACHE
    if _COMPONENT_MAP_CACHE is not None:
        return _COMPONENT_MAP_CACHE

    rows = frappe.get_all(
        "Salary Component",
        fields=["name", "mof_r5_r10_line", "mof_r6_line"],
    )
    _COMPONENT_MAP_CACHE = {}
    for r in rows:
        r5 = (r.mof_r5_r10_line or "").split(" - ")[0].strip() if r.mof_r5_r10_line else ""
        r6 = (r.mof_r6_line or "").split(" - ")[0].strip() if r.mof_r6_line else ""
        _COMPONENT_MAP_CACHE[r.name] = {"r5_r10": r5, "r6": r6}
    return _COMPONENT_MAP_CACHE


def _get_r5_r10_line(comp_name):
    """Return R5/R10 line code for a salary component (e.g. '100', '130')."""
    cmap = _load_component_map()
    entry = cmap.get(comp_name)
    if entry and entry["r5_r10"]:
        return entry["r5_r10"]
    # Fallback to legacy lists
    n = (comp_name or "").strip()
    if n in TRANSPORT_COMPONENTS:
        return "130"
    if n in REPRESENTATION_COMPONENTS:
        return "140"
    if n in CNSS_EE_COMPONENTS:
        return "150"
    return "100"


def _get_tax_components():
    global TAX_COMPONENTS_CACHE
    if TAX_COMPONENTS_CACHE is None:
        TAX_COMPONENTS_CACHE = frappe.get_all(
            "Salary Component",
            filters={"is_income_tax_component": 1},
            pluck="name",
        )
    return TAX_COMPONENTS_CACHE


def _classify_component(name):
    """Return R6 line code for a salary component.

    First checks the `mof_r6_line` custom field, then falls back to legacy lists.
    """
    cmap = _load_component_map()
    entry = cmap.get(name)
    if entry and entry["r6"]:
        return entry["r6"]

    # Legacy fallback
    n = (name or "").strip()
    for comps, code in [
        (TRANSPORT_COMPONENTS, "150"),
        (REPRESENTATION_COMPONENTS, "110"),
        (FAMILY_SPOUSE_COMPONENTS, "130"),
        (FAMILY_CHILD_COMPONENTS, "140"),
        (HOUSING_COMPONENTS, "170"),
        (CAR_COMPONENTS, "160"),
        (FOOD_COMPONENTS, "180"),
        (CLOTHING_COMPONENTS, "190"),
        (FUND_COMPONENTS, "200"),
        (HEALTH_COMPONENTS, "210"),
        (EDUCATION_COMPONENTS, "220"),
        (MARRIAGE_COMPONENTS, "230"),
        (BIRTH_COMPONENTS, "240"),
        (SICK_COMPONENTS, "250"),
        (DEATH_COMPONENTS, "260"),
    ]:
        if n in comps:
            return code
    return "100"  # default to basic salary line


def _get_employee_full(employee_id):
    """Load full employee data including child tables."""
    emp = frappe.get_doc("Employee", employee_id)
    data = emp.as_dict()

    # Compose convenience fields for PDF builders
    data["father_name"] = " ".join(
        filter(None, [data.get("father_first_name"), data.get("father_last_name")])
    )
    data["mother_name"] = " ".join(
        filter(None, [data.get("mother_first_name"), data.get("mother_last_name")])
    )
    data["family_name"] = data.get("last_name") or ""
    data["place_of_birth"] = data.get("town_of_birth") or data.get("country_of_birth") or ""

    # Get national ID info
    if emp.national_id:
        nid = emp.national_id[0]
        data["national_id_number"] = nid.national_id_number
        data["mohafaza"] = nid.mohafaza
        data["caza"] = nid.caza
        data["register_place"] = nid.register_place
        data["register_number"] = nid.register_number
    else:
        data["national_id_number"] = ""
        data["mohafaza"] = ""
        data["caza"] = ""
        data["register_place"] = ""
        data["register_number"] = ""

    return data


def _get_company_data(company_name):
    """Load company data with address."""
    comp = frappe.get_doc("Company", company_name)
    data = comp.as_dict()

    # Try to load linked address
    addr = frappe.db.sql("""
        SELECT a.address_line1, a.address_line2, a.city, a.state, a.pincode,
               a.country, a.phone, a.fax, a.email_id
        FROM tabAddress a
        JOIN `tabDynamic Link` dl ON dl.parent = a.name AND dl.parenttype = 'Address'
        WHERE dl.link_doctype = 'Company' AND dl.link_name = %s
        LIMIT 1
    """, company_name, as_dict=True)

    if addr:
        data["address"] = addr[0]
    else:
        # Fallback: try parent company address
        parent = comp.parent_company
        if parent:
            addr = frappe.db.sql("""
                SELECT a.address_line1, a.address_line2, a.city, a.state, a.pincode,
                       a.country, a.phone, a.fax, a.email_id
                FROM tabAddress a
                JOIN `tabDynamic Link` dl ON dl.parent = a.name AND dl.parenttype = 'Address'
                WHERE dl.link_doctype = 'Company' AND dl.link_name = %s
                LIMIT 1
            """, parent, as_dict=True)
            if addr:
                data["address"] = addr[0]
            else:
                data["address"] = frappe._dict()
        else:
            data["address"] = frappe._dict()

    return data


def _get_salary_slips(company, start_date, end_date, employee=None):
    """Get submitted salary slips with component details."""
    filters = {
        "company": company,
        "start_date": (">=", start_date),
        "end_date": ("<=", end_date),
        "docstatus": 1,
    }
    if employee:
        filters["employee"] = employee

    slips = frappe.get_all(
        "Salary Slip",
        filters=filters,
        fields=["name", "employee", "employee_name", "start_date", "end_date",
                "gross_pay", "total_deduction", "net_pay"],
        order_by="employee_name, start_date",
    )

    # Load component details for all slips
    slip_names = [s.name for s in slips]
    details = {}
    if slip_names:
        all_details = frappe.get_all(
            "Salary Detail",
            filters={"parent": ("in", slip_names)},
            fields=["parent", "salary_component", "amount", "parentfield"],
        )
        for d in all_details:
            details.setdefault(d.parent, []).append(d)

    for s in slips:
        s.details = details.get(s.name, [])

    return slips


def _render_template(template_name, context):
    """Render a Jinja template from the templates directory."""
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters["fmt_number"] = lambda v: "{:,.0f}".format(flt(v)) if flt(v) else ""
    env.filters["fmt_date"] = lambda v: formatdate(v, "dd/MM/yyyy") if v else ""
    template = env.get_template(template_name)
    return template.render(**context)


# ════════════════════════════════════════════════════════════════
#  R3 — New Employee Registration
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_r3_data(employee):
    """Gather data for R3 form (new employee registration)."""
    emp = _get_employee_full(employee)
    comp = _get_company_data(emp.company)
    return {"employee": emp, "company": comp}


@frappe.whitelist()
def generate_r3_pdf(employee):
    """Generate R3 form PDF for an employee."""
    data = get_r3_data(employee)
    from .pdf_r3 import build_r3_pdf
    pdf = build_r3_pdf(data["employee"], data["company"])
    frappe.local.response.filename = f"R3_{employee}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  R4 — Employee Information Statement
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_r4_data(employee):
    """Gather data for R4 form (employee info statement to employer)."""
    emp = _get_employee_full(employee)
    comp = _get_company_data(emp.company)

    # Count dependents
    dep_count = 0
    try:
        dep_count = cint(frappe.db.get_value("Employee", employee, "number_of_dependent_children"))
    except Exception:
        pass

    # Build dependents list from available data (children not tracked individually in standard)
    dependents = []

    return {"employee": emp, "company": comp, "dep_count": dep_count, "dependents": dependents}


@frappe.whitelist()
def generate_r4_pdf(employee):
    """Generate R4 form PDF for an employee."""
    data = get_r4_data(employee)
    from .pdf_r4 import build_r4_pdf
    pdf = build_r4_pdf(data["employee"], data["company"], data["dep_count"], data["dependents"])
    frappe.local.response.filename = f"R4_{employee}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  R5 — Annual Income Tax Declaration on Salaries
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_r5_data(company, year):
    """Gather data for R5 annual tax declaration."""
    _reset_caches()
    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    comp = _get_company_data(company)
    constants = PayrollConstants.get_active_constants(company, start_date)
    tax_comps = _get_tax_components()

    slips = _get_salary_slips(company, start_date, end_date)

    # Aggregate per employee
    emp_totals = {}
    for s in slips:
        if s.employee not in emp_totals:
            emp_totals[s.employee] = {
                "gross": 0, "transport": 0, "representation": 0,
                "tax_withheld": 0, "cnss_ee": 0,
            }
        et = emp_totals[s.employee]
        et["gross"] += flt(s.gross_pay)
        for d in s.details:
            comp_name = d.salary_component
            line = _get_r5_r10_line(comp_name)
            if d.parentfield == "earnings":
                if line == "130":
                    et["transport"] += flt(d.amount)
                elif line == "140":
                    et["representation"] += flt(d.amount)
            elif d.parentfield == "deductions":
                if comp_name in tax_comps:
                    et["tax_withheld"] += flt(d.amount)
                elif line == "150":
                    et["cnss_ee"] += flt(d.amount)

    # Compute tax lines (board vs employees - all as employees for now)
    employees = {
        "count": len(emp_totals),
        "line_100": sum(e["gross"] for e in emp_totals.values()),  # Salaries + supplements
        "line_110": 0,  # Cash/in-kind benefits
        "line_120": 0,  # Total paid (computed)
        "line_130": sum(e["transport"] for e in emp_totals.values()),  # Transport deduction
        "line_140": sum(e["representation"] for e in emp_totals.values()),  # Representation
        "line_150": 0,  # Other deductions (CNSS etc.)
        "line_160": 0,  # Net amounts (computed)
        "line_170": 0,  # Family deduction (computed)
        "line_180": 0,  # Taxable (computed)
        "line_190": 0,  # Tax due (computed)
    }

    # Line 120 = 100 + 110
    employees["line_120"] = employees["line_100"] + employees["line_110"]

    # Line 150 = CNSS employee deductions
    employees["line_150"] = sum(e["cnss_ee"] for e in emp_totals.values())

    # Line 160 = 120 - 130 - 140 - 150
    employees["line_160"] = (employees["line_120"] - employees["line_130"]
                             - employees["line_140"] - employees["line_150"])

    # Family deduction (aggregate from all employees)
    total_family_ded = 0
    for emp_id in emp_totals:
        total_family_ded += get_employee_tax_deductions(emp_id, constants)
    employees["line_170"] = total_family_ded

    # Line 180 = 160 - 170 (taxable)
    employees["line_180"] = max(0, employees["line_160"] - employees["line_170"])

    # Line 190 = tax due (sum of individual taxes)
    total_tax_due = 0
    for emp_id, et in emp_totals.items():
        indiv_gross = et["gross"] - et["transport"] - et["representation"] - et["cnss_ee"]
        indiv_ded = get_employee_tax_deductions(emp_id, constants)
        indiv_taxable = max(0, indiv_gross - indiv_ded)
        total_tax_due += compute_annual_tax(indiv_taxable)
    employees["line_190"] = total_tax_due

    total_tax_withheld = sum(e["tax_withheld"] for e in emp_totals.values())

    # Board members (empty for now)
    board = {k: 0 for k in ["count", "line_100", "line_110", "line_120", "line_130",
                             "line_140", "line_150", "line_160", "line_170", "line_180", "line_190"]}

    # Lump sum
    lump_sum = {"line_240": 0, "line_250": 0}

    # Totals
    totals = {
        "line_251": employees["line_180"] + board["line_180"],
        "line_260": employees["line_190"] + board["line_190"] + lump_sum["line_250"],
        "line_261": total_tax_withheld,
        "line_262": 0,  # balance (computed)
        "line_270": 0,  # verification penalty
        "line_280": 0,  # collection penalty
        "line_290": 0,  # balance due (computed)
        "line_300": 0,  # balance refundable (computed)
    }
    totals["line_262"] = totals["line_260"] - totals["line_261"]
    if totals["line_262"] > 0:
        totals["line_290"] = totals["line_262"] + totals["line_270"] + totals["line_280"]
    else:
        totals["line_300"] = abs(totals["line_262"])

    # Periodic payments (quarterly)
    payments = []
    for q in range(4):
        q_start = f"{year}-{q*3+1:02d}-01"
        q_end = get_last_day(f"{year}-{q*3+3:02d}-01")
        q_tax = frappe.db.sql("""
            SELECT COALESCE(SUM(sd.amount), 0)
            FROM `tabSalary Detail` sd
            JOIN `tabSalary Slip` ss ON ss.name = sd.parent
            WHERE ss.company = %s AND ss.start_date >= %s AND ss.end_date <= %s
              AND ss.docstatus = 1 AND sd.parentfield = 'deductions'
              AND sd.salary_component IN %s
        """, (company, q_start, str(q_end), tax_comps or ["__none__"]))[0][0]
        payments.append({
            "date": str(q_end),
            "amount": flt(q_tax),
        })

    return {
        "company": comp,
        "year": year,
        "start_date": start_date,
        "end_date": end_date,
        "board": board,
        "employees": employees,
        "lump_sum": lump_sum,
        "totals": totals,
        "payments": payments,
        "total_paid": sum(p["amount"] for p in payments),
    }


@frappe.whitelist()
def generate_r5_pdf(company, year):
    """Generate R5 annual tax declaration PDF."""
    data = get_r5_data(company, int(year))
    from .pdf_r5 import build_r5_pdf
    pdf = build_r5_pdf(data)
    frappe.local.response.filename = f"R5_{company}_{year}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  R6 — Annual Individual Income Statement
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_r6_data(company, year, employee):
    """Gather data for R6 individual annual income statement."""
    _reset_caches()
    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    comp = _get_company_data(company)
    emp = _get_employee_full(employee)
    constants = PayrollConstants.get_active_constants(company, start_date)

    slips = _get_salary_slips(company, start_date, end_date, employee)

    # R6 income lines
    lines = {str(c): {"total": 0, "non_taxable": 0, "taxable": 0}
             for c in [100, 110, 120, 130, 140, 150, 160, 170, 180, 190,
                       200, 210, 220, 230, 240, 250, 260, 300]}

    total_cnss = 0
    total_tax = 0
    tax_comps = _get_tax_components()

    # Non-taxable R6 line codes (fully exempt per Lebanese law)
    NON_TAXABLE_CODES = {"150", "210", "220", "230", "240", "250", "260"}

    for s in slips:
        for d in s.details:
            comp_name = d.salary_component
            amt = flt(d.amount)
            if d.parentfield == "earnings":
                code = _classify_component(comp_name)
                lines[code]["total"] += amt
                if code in NON_TAXABLE_CODES:
                    lines[code]["non_taxable"] += amt
                else:
                    lines[code]["taxable"] += amt
            elif d.parentfield == "deductions":
                if comp_name in tax_comps:
                    total_tax += amt
                elif _get_r5_r10_line(comp_name) == "150":
                    total_cnss += amt

    # Line 310 = total of all lines
    line_310 = {"total": 0, "non_taxable": 0, "taxable": 0}
    for code, vals in lines.items():
        line_310["total"] += vals["total"]
        line_310["non_taxable"] += vals["non_taxable"]
        line_310["taxable"] += vals["taxable"]

    # Family deduction
    family_ded = get_employee_tax_deductions(employee, constants)

    # Net taxable
    net_taxable = max(0, line_310["taxable"] - family_ded)
    annual_tax = compute_annual_tax(net_taxable)

    # Employee count for the company/year
    emp_count = frappe.db.count("Salary Slip", {
        "company": company,
        "start_date": (">=", start_date),
        "end_date": ("<=", end_date),
        "docstatus": 1,
    })

    # Salary type
    salary_mode = emp.get("salary_mode") or "Monthly"
    payroll_freq = frappe.db.get_value("Salary Structure Assignment", {
        "employee": employee, "docstatus": 1, "company": company
    }, "salary_structure")

    # Work period
    joining = emp.get("date_of_joining")
    relieving = emp.get("relieving_date")
    work_from = max(getdate(start_date), getdate(joining)) if joining else getdate(start_date)
    work_to = min(getdate(end_date), getdate(relieving)) if relieving else getdate(end_date)

    # Marital status
    marital = emp.get("marital_status") or "Single"

    # Dependents count
    dep_count = 0
    try:
        dep_count = cint(frappe.db.get_value("Employee", employee, "number_of_dependent_children"))
    except Exception:
        pass

    return {
        "company": comp,
        "employee": emp,
        "year": year,
        "emp_count": emp_count,
        "lines": lines,
        "line_310": line_310,
        "line_330": family_ded,
        "line_340": total_cnss,
        "line_350": net_taxable,
        "line_360": annual_tax,
        "total_tax_withheld": total_tax,
        "salary_type": salary_mode,
        "work_from": work_from,
        "work_to": work_to,
        "marital_status": marital,
        "dep_count": dep_count,
    }


@frappe.whitelist()
def generate_r6_pdf(company, year, employee):
    """Generate R6 individual annual income PDF."""
    data = get_r6_data(company, int(year), employee)
    from .pdf_r6 import build_r6_pdf
    pdf = build_r6_pdf(data)
    frappe.local.response.filename = f"R6_{employee}_{year}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  R10 — Periodic Tax Payment Statement
# ════════════════════════════════════════════════════════════════
QUARTER_MAP = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12),
}


@frappe.whitelist()
def get_r10_data(company, year, period_type="Annual", quarter=None):
    """Gather data for R10 periodic tax payment statement."""
    _reset_caches()
    year = int(year)
    comp = _get_company_data(company)
    constants = PayrollConstants.get_active_constants(company, f"{year}-01-01")
    tax_comps = _get_tax_components()

    if period_type == "Quarterly" and quarter:
        sm, em = QUARTER_MAP.get(quarter, (1, 3))
        start_date = f"{year}-{sm:02d}-01"
        end_date = str(get_last_day(f"{year}-{em:02d}-01"))
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

    slips = _get_salary_slips(company, start_date, end_date)

    # Aggregate
    emp_set = set()
    total_gross = 0
    total_transport = 0
    total_representation = 0
    total_cnss_ee = 0
    total_tax_withheld = 0

    emp_data = {}
    for s in slips:
        emp_set.add(s.employee)
        total_gross += flt(s.gross_pay)
        if s.employee not in emp_data:
            emp_data[s.employee] = {"gross": 0, "transport": 0, "rep": 0, "cnss": 0, "tax": 0}
        emp_data[s.employee]["gross"] += flt(s.gross_pay)
        for d in s.details:
            line = _get_r5_r10_line(d.salary_component)
            if d.parentfield == "earnings":
                if line == "130":
                    total_transport += flt(d.amount)
                    emp_data[s.employee]["transport"] += flt(d.amount)
                elif line == "140":
                    total_representation += flt(d.amount)
                    emp_data[s.employee]["rep"] += flt(d.amount)
            elif d.parentfield == "deductions":
                if d.salary_component in tax_comps:
                    total_tax_withheld += flt(d.amount)
                    emp_data[s.employee]["tax"] += flt(d.amount)
                elif line == "150":
                    total_cnss_ee += flt(d.amount)
                    emp_data[s.employee]["cnss"] += flt(d.amount)

    # Board (empty for now)
    board = {k: 0 for k in ["count", "line_100", "line_110", "line_120", "line_130",
                             "line_140", "line_150", "line_160", "line_170", "line_180", "line_190"]}

    # Employees section
    employees = {
        "count": len(emp_set),
        "line_100": total_gross,
        "line_110": 0,
        "line_120": total_gross,
        "line_130": total_transport,
        "line_140": total_representation,
        "line_150": total_cnss_ee,
        "line_160": total_gross - total_transport - total_representation - total_cnss_ee,
        "line_170": 0,
        "line_180": 0,
        "line_190": 0,
    }

    # Family deduction
    total_family = 0
    total_tax_due = 0
    for emp_id, ed in emp_data.items():
        fam = get_employee_tax_deductions(emp_id, constants)
        total_family += fam
        indiv_net = ed["gross"] - ed["transport"] - ed["rep"] - ed["cnss"]
        indiv_taxable = max(0, indiv_net - fam)
        total_tax_due += compute_annual_tax(indiv_taxable)

    employees["line_170"] = total_family
    employees["line_180"] = max(0, employees["line_160"] - total_family)
    employees["line_190"] = total_tax_due

    # Lump sum
    lump_sum = {"line_240": 0, "line_250": 0}

    # Totals
    totals = {
        "line_260": employees["line_180"] + board["line_180"],
        "line_270": employees["line_190"] + board["line_190"] + lump_sum["line_250"],
        "line_280": 0,  # verification penalty
        "line_290": 0,  # collection penalty
        "line_300": 0,  # total due
    }
    totals["line_300"] = (totals["line_270"] + totals["line_280"]
                          + totals["line_290"] - total_tax_withheld)

    return {
        "company": comp,
        "year": year,
        "start_date": start_date,
        "end_date": end_date,
        "period_type": period_type,
        "quarter": quarter,
        "board": board,
        "employees": employees,
        "lump_sum": lump_sum,
        "totals": totals,
        "total_tax_withheld": total_tax_withheld,
    }


@frappe.whitelist()
def generate_r10_pdf(company, year, period_type="Annual", quarter=None):
    """Generate R10 periodic tax payment statement PDF."""
    data = get_r10_data(company, int(year), period_type, quarter)
    from .pdf_r10 import build_r10_pdf
    pdf = build_r10_pdf(data)
    suffix = f"_{quarter}" if quarter else ""
    frappe.local.response.filename = f"R10_{company}_{year}{suffix}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  R7 — Summary of Employees Who Left During the Year
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_r7_data(company, year):
    """Gather data for R7 — employees who left during the year."""
    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    comp = _get_company_data(company)

    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Left",
            "relieving_date": ("between", [start_date, end_date]),
        },
        fields=[
            "name as employee",
            "employee_name",
            "ctc as cnss_number",
            "date_of_joining",
            "relieving_date",
        ],
        order_by="relieving_date asc",
    )

    return {
        "company": comp,
        "year": year,
        "employees": employees,
    }


@frappe.whitelist()
def generate_r7_pdf(company, year):
    """Generate R7 summary of employees who left during the year PDF."""
    data = get_r7_data(company, int(year))
    from .pdf_r7 import build_r7_pdf
    pdf = build_r7_pdf(data)
    frappe.local.response.filename = f"R7_{company}_{year}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


# ════════════════════════════════════════════════════════════════
#  Bulk Generation
# ════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_available_forms():
    """Return list of available MoF forms."""
    return [
        {"form": "R3", "title": "طلب تسجيل مستخدم/أجير جديد", "title_en": "New Employee Registration",
         "requires": ["employee"]},
        {"form": "R4", "title": "بيان معلومات من المستخدم/الأجير الى رب العمل",
         "title_en": "Employee Information Statement", "requires": ["employee"]},
        {"form": "R5", "title": "تصريح سنوي عن ضريبة الدخل على الرواتب والأجور",
         "title_en": "Annual Tax Declaration", "requires": ["company", "year"]},
        {"form": "R6", "title": "كشف سنوي إفرادي بإجمالي إيرادات المستخدم/الأجير",
         "title_en": "Annual Individual Income Statement", "requires": ["company", "year", "employee"]},
        {"form": "R7", "title": "كشف إجمالي بالمستخدمين الذين تركوا العمل خلال السنة",
         "title_en": "Employees Who Left During the Year", "requires": ["company", "year"]},
        {"form": "R10", "title": "بيان دوري بتأدية ضريبة الرواتب والأجور",
         "title_en": "Periodic Tax Payment Statement", "requires": ["company", "year"]},
    ]
