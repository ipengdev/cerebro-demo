"""Precision calibration: draw red markers at current coordinates on blank forms."""
import os, io, fitz, frappe
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color, red, blue, green
from reportlab.pdfgen import canvas as rl_canvas

TEMPLATES = "/home/ipeng/frappe-bench/apps/amo/amo/amo_payroll/mof_forms/pdf_templates"
OUT = "/tmp/mof_calib"

def draw_markers(coords, pagesize=A4):
    """Draw labeled red markers at coordinates on a transparent overlay."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=pagesize)
    for label, x, y, align in coords:
        # Draw a short red horizontal line at the y position
        c.setStrokeColor(red)
        c.setLineWidth(0.8)
        if align == 'r':
            c.line(x - 80, y, x, y)  # line extending left from right-align point
        elif align == 'c':
            c.line(x - 30, y, x + 30, y)
        else:
            c.line(x, y, x + 80, y)
        # Draw a small blue dot at the exact coordinate
        c.setFillColor(blue)
        c.circle(x, y, 1.5, fill=1, stroke=0)
        # Draw label
        c.setFont("Helvetica", 4)
        c.setFillColor(Color(0, 0.5, 0))
        c.drawString(x + 3, y + 2, label)
    c.save()
    buf.seek(0)
    return buf

def merge_on_blank(blank_name, marker_buf):
    blank = PdfReader(os.path.join(TEMPLATES, blank_name))
    markers = PdfReader(marker_buf)
    w = PdfWriter()
    page = blank.pages[0]
    page.merge_page(markers.pages[0])
    w.add_page(page)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()

def render_png(pdf_bytes, name):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pix = doc[0].get_pixmap(dpi=200)
    path = os.path.join(OUT, f"{name}_markers.png")
    pix.save(path)
    doc.close()
    print(f"  {path} ({os.path.getsize(path)})")

def run():
    os.makedirs(OUT, exist_ok=True)

    # R5 current coordinates
    r5_coords = [
        ("company", 515, 775, 'r'),
        ("trade", 515, 727, 'r'),
        ("state", 520, 695, 'r'),
        ("city", 390, 683, 'r'),
        ("line2", 520, 671, 'r'),
        ("line1", 520, 659, 'r'),
        ("phone", 520, 618, 'r'),
        ("email", 520, 590, 'r'),
        ("board_cnt", 400, 493, 'c'),
        ("emp_cnt", 400, 481, 'c'),
        ("L100", 330, 435, 'c'),
        ("L110", 330, 419, 'c'),
        ("L120", 330, 403, 'c'),
        ("L130", 330, 387, 'c'),
        ("L140", 330, 371, 'c'),
        ("L150", 330, 355, 'c'),
        ("L160", 330, 339, 'c'),
        ("L170", 330, 323, 'c'),
        ("L180", 330, 307, 'c'),
        ("L190", 330, 291, 'c'),
        ("yr_from", 242, 747, 'c'),
        ("yr_to", 58, 747, 'c'),
        ("per_from", 242, 734, 'c'),
        ("per_to", 58, 734, 'c'),
    ]
    print("R5 markers...")
    buf = draw_markers(r5_coords)
    pdf = merge_on_blank("r5_blank.pdf", buf)
    render_png(pdf, "r5")

    # R10 current coordinates
    r10_coords = [
        ("company", 510, 775, 'r'),
        ("trade", 510, 715, 'r'),
        ("state", 520, 650, 'r'),
        ("city", 372, 650, 'r'),
        ("street", 520, 627, 'r'),
        ("phone", 345, 591, 'r'),
        ("email", 520, 567, 'r'),
        ("board_cnt", 398, 457, 'c'),
        ("emp_cnt", 398, 444, 'c'),
        ("L100", 325, 397, 'c'),
        ("L110", 325, 382, 'c'),
        ("L120", 325, 367, 'c'),
        ("L130", 325, 351, 'c'),
        ("L140", 325, 335, 'c'),
        ("L150", 325, 319, 'c'),
        ("L160", 325, 305, 'c'),
        ("L170", 325, 290, 'c'),
        ("L180", 325, 275, 'c'),
        ("L190", 325, 259, 'c'),
        ("yr_from", 242, 749, 'c'),
        ("yr_to", 58, 749, 'c'),
        ("rep", 420, 697, 'r'),
    ]
    print("R10 markers...")
    buf = draw_markers(r10_coords)
    pdf = merge_on_blank("r10_blank.pdf", buf)
    render_png(pdf, "r10")

    # R6 current coordinates
    r6_coords = [
        ("company", 500, 775, 'r'),
        ("trade", 500, 759, 'r'),
        ("year", 60, 775, 'c'),
        ("emp_cnt", 60, 749, 'c'),
        ("emp_name", 500, 692, 'r'),
        ("father", 360, 692, 'r'),
        ("surname", 225, 692, 'r'),
        ("desig", 340, 647, 'r'),
        ("salary_chk", 138, 647, 'c'),
        ("marital", 470, 625, 'c'),
        ("dep_cnt", 300, 625, 'c'),
        ("dep_ben", 180, 625, 'c'),
        ("wk_from", 430, 609, 'c'),
        ("wk_to", 310, 609, 'c'),
        ("state", 520, 559, 'r'),
        ("city", 370, 559, 'r'),
        ("addr", 520, 547, 'r'),
        ("L100", 345, 455, 'c'),
        ("L110", 345, 437, 'c'),
        ("L120", 345, 420, 'c'),
        ("L310", 345, 152, 'c'),
        ("L330", 280, 122, 'c'),
        ("L340", 280, 105, 'c'),
        ("L350", 280, 79, 'c'),
        ("L360", 280, 62, 'c'),
    ]
    print("R6 markers...")
    buf = draw_markers(r6_coords)
    pdf = merge_on_blank("r6_blank.pdf", buf)
    render_png(pdf, "r6")

    # R3 current coordinates
    r3_coords = [
        ("company", 495, 760, 'r'),
        ("trade", 310, 760, 'r'),
        ("name", 490, 685, 'r'),
        ("surname", 280, 670, 'r'),
        ("father", 490, 649, 'r'),
        ("mother", 280, 634, 'r'),
        ("gender_m", 420, 617, 'c'),
        ("gender_f", 370, 617, 'c'),
        ("nation", 350, 597, 'r'),
        ("birth_pl", 490, 584, 'r'),
        ("dob", 228, 584, 'c'),
        ("reg_num", 490, 565, 'r'),
        ("reg_pl", 355, 565, 'r'),
        ("id_num", 210, 565, 'r'),
        ("marital", 400, 552, 'c'),
        ("join_d", 375, 542, 'c'),
        ("state", 490, 257, 'r'),
        ("city", 370, 257, 'r'),
        ("street", 490, 245, 'r'),
        ("phone", 490, 221, 'r'),
        ("decl_name", 490, 154, 'r'),
    ]
    print("R3 markers...")
    buf = draw_markers(r3_coords)
    pdf = merge_on_blank("r3_blank.pdf", buf)
    render_png(pdf, "r3")

    # R4 current coordinates
    r4_coords = [
        ("company", 500, 749, 'r'),
        ("trade", 500, 725, 'r'),
        ("name", 490, 655, 'r'),
        ("surname", 280, 642, 'r'),
        ("father", 490, 615, 'r'),
        ("mother", 280, 600, 'r'),
        ("gender_m", 415, 585, 'c'),
        ("nation", 350, 570, 'r'),
        ("birth_pl", 490, 555, 'r'),
        ("dob", 200, 555, 'c'),
        ("reg_num", 490, 539, 'r'),
        ("marital", 400, 507, 'c'),
        ("salary", 195, 487, 'c'),
        ("dep_cnt", 440, 455, 'c'),
        ("spouse", 490, 427, 'r'),
        ("state", 490, 185, 'r'),
        ("city", 370, 185, 'r'),
        ("street", 490, 172, 'r'),
        ("phone", 490, 147, 'r'),
        ("email", 490, 117, 'r'),
        ("decl_name", 490, 89, 'r'),
    ]
    print("R4 markers...")
    buf = draw_markers(r4_coords)
    pdf = merge_on_blank("r4_blank.pdf", buf)
    render_png(pdf, "r4")

    print("All marker images created!")
