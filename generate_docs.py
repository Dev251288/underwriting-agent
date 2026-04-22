"""
Generate synthetic demo documents for Rajesh Kumar Sharma's home loan application.
Run: python generate_docs.py
Output: uploads/ directory
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

UPLOADS = Path(__file__).parent / "uploads"
UPLOADS.mkdir(exist_ok=True)

# ── Constants ────────────────────────────────────────────────────────────────

A = {  # applicant
    "name": "Rajesh Kumar Sharma",
    "dob": "15-03-1985",
    "dob_slash": "15/03/1985",
    "aadhaar": "1234 5678 9012",
    "pan": "ABCPS1234D",
    "addr1": "Flat 4B, Sunrise Apartments, Koramangala",
    "addr2": "Bengaluru, Karnataka - 560034",
    "mobile": "+91-9876543210",
    "email": "rajesh.sharma@email.com",
    "gender": "Male",
    "father": "Ram Prakash Sharma",
}

E = {  # employer
    "name": "Infosys Limited",
    "addr": "Electronics City Phase 1, Bengaluru - 560100",
    "tan": "BLRI00236F",
    "pan": "INFTX00001A",
    "emp_id": "INF-BGK-45892",
    "dept": "Engineering – Cloud Services",
    "uan": "100456789123",
    "pf_no": "KN/BLR/1234/56/45892",
    "designation": "Senior Software Engineer",
}

S = {  # salary (monthly)
    "basic": 77_031,
    "hra": 30_812,
    "special": 46_219,
    "gross": 154_062,
    "pf_ee": 9_244,   # employee PF (12% of basic)
    "pf_er": 8_756,   # employer PF contribution shown on slip
    "tds": 11_062,
    "prof_tax": 200,
    "net": 125_000,   # deliberately different from gross (mismatch bait)
}

PROP = {
    "addr": "Flat 4B, Sunrise Apartments, Koramangala, Bengaluru - 560034",
    "survey": "Survey No. 34/2B, Koramangala Village, Bengaluru South Taluk",
    "khata": "Khata No. 1892/34/2B",
    "reg_no": "DOR-BLR-2015-45672",
    "area": "1,250 sq.ft (Super Built-Up)",
    "consideration": "1,15,00,000",
    "seller": "Prestige Estates Projects Limited",
    "reg_date": "10-08-2015",
    "stamp_duty": "6,90,000",
    "reg_fee": "92,000",
}

def inr(n: int) -> str:
    """Indian comma-separated currency string."""
    s = f"{n:,}"
    return s


def inr_sym(n: int) -> str:
    return f"\u20b9{inr(n)}"


STYLES = getSampleStyleSheet()


def ps(name: str, **kw) -> ParagraphStyle:
    """Quick ParagraphStyle factory."""
    return ParagraphStyle(name, parent=STYLES["Normal"], **kw)


TITLE  = ps("T", fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
H1     = ps("H1", fontSize=11, fontName="Helvetica-Bold", spaceAfter=3)
H2     = ps("H2", fontSize=9,  fontName="Helvetica-Bold", spaceAfter=2)
BODY   = ps("B",  fontSize=8,  spaceAfter=2, leading=11)
SMALL  = ps("S",  fontSize=7,  spaceAfter=1, leading=9)
CENTER = ps("C",  fontSize=8,  alignment=TA_CENTER)
RIGHT  = ps("R",  fontSize=8,  alignment=TA_RIGHT)
GOVT   = ps("G",  fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)
NOTE   = ps("N",  fontSize=7,  textColor=colors.HexColor("#555555"), spaceAfter=1)


# ── 1. Aadhaar Card ───────────────────────────────────────────────────────────

def make_aadhaar() -> None:
    path = UPLOADS / "aadhaar_rajesh.pdf"
    CW, CH = 85.6 * mm, 54 * mm  # ISO/IEC 7810 ID-1 card size
    c = canvas.Canvas(str(path), pagesize=(CW, CH))

    # Navy background
    c.setFillColor(colors.HexColor("#00205B"))
    c.rect(0, 0, CW, CH, fill=1, stroke=0)

    # White card body
    c.setFillColor(colors.white)
    c.roundRect(1.5 * mm, 1.5 * mm, CW - 3 * mm, CH - 3 * mm, 2 * mm, fill=1, stroke=0)

    # Saffron header strip
    c.setFillColor(colors.HexColor("#FF6700"))
    c.rect(1.5 * mm, CH - 10 * mm, CW - 3 * mm, 8.5 * mm, fill=1, stroke=0)

    # Header text
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(3 * mm, CH - 5.5 * mm, "भारत सरकार / Government of India")
    c.setFont("Helvetica", 5.5)
    c.drawString(3 * mm, CH - 8.5 * mm, "Unique Identification Authority of India (UIDAI)")

    # AADHAAR word-mark
    c.setFillColor(colors.HexColor("#00205B"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(3 * mm, CH - 18 * mm, "आधार")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(22 * mm, CH - 18 * mm, "Aadhaar")

    # Photo placeholder
    c.setFillColor(colors.HexColor("#E8E8E8"))
    c.rect(CW - 22 * mm, CH - 44 * mm, 19 * mm, 22 * mm, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 5)
    c.drawCentredString(CW - 12.5 * mm, CH - 34 * mm, "Photo")

    # Name and details
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(3 * mm, CH - 23 * mm, A["name"])

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, CH - 27 * mm, f"DOB: {A['dob']}   Gender: {A['gender']}")

    c.setFont("Helvetica", 6.5)
    c.drawString(3 * mm, CH - 31 * mm, A["addr1"])
    c.drawString(3 * mm, CH - 34.5 * mm, A["addr2"])

    # Aadhaar number — large and prominent
    c.setFillColor(colors.HexColor("#00205B"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(3 * mm, CH - 44 * mm, A["aadhaar"])

    # QR placeholder
    c.setFillColor(colors.HexColor("#DDDDDD"))
    c.rect(CW - 22 * mm, CH - 51 * mm, 19 * mm, 6 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 4.5)
    c.drawCentredString(CW - 12.5 * mm, CH - 48.5 * mm, "Digital QR Code")

    # Meri Pehchaan tagline
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica-Oblique", 5.5)
    c.drawString(3 * mm, CH - 50 * mm, "Meri Pehchaan")

    c.save()
    print(f"  OK {path.name}")


# ── 2. PAN Card ───────────────────────────────────────────────────────────────

def make_pan() -> None:
    path = UPLOADS / "pan_card_rajesh.pdf"
    CW, CH = 85.6 * mm, 54 * mm
    c = canvas.Canvas(str(path), pagesize=(CW, CH))

    # White background
    c.setFillColor(colors.white)
    c.rect(0, 0, CW, CH, fill=1, stroke=0)

    # Blue border
    c.setStrokeColor(colors.HexColor("#003580"))
    c.setLineWidth(1.5)
    c.roundRect(1 * mm, 1 * mm, CW - 2 * mm, CH - 2 * mm, 2 * mm, fill=0, stroke=1)

    # Header
    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(CW / 2, CH - 7 * mm, "INCOME TAX DEPARTMENT")
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(CW / 2, CH - 10.5 * mm, "GOVT. OF INDIA")

    # Ashoka Pillar placeholder
    c.setFillColor(colors.HexColor("#E8E8E8"))
    c.circle(CW - 14 * mm, CH - 10 * mm, 5 * mm, fill=1)
    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica-Bold", 4)
    c.drawCentredString(CW - 14 * mm, CH - 10.5 * mm, "☸")

    # PAN label
    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(3 * mm, CH - 15.5 * mm, "Permanent Account Number")

    # PAN number — large
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(3 * mm, CH - 23 * mm, A["pan"])

    # Photo box
    c.setFillColor(colors.HexColor("#F0F0F0"))
    c.rect(CW - 22 * mm, CH - 43 * mm, 19 * mm, 20 * mm, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#999999"))
    c.setFont("Helvetica", 5)
    c.drawCentredString(CW - 12.5 * mm, CH - 34 * mm, "Photo")

    # Fields
    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica", 6)
    c.drawString(3 * mm, CH - 29 * mm, "Name")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, CH - 33 * mm, A["name"].upper())

    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica", 6)
    c.drawString(3 * mm, CH - 37 * mm, "Father's Name")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(3 * mm, CH - 40.5 * mm, A["father"].upper())

    c.setFillColor(colors.HexColor("#003580"))
    c.setFont("Helvetica", 6)
    c.drawString(3 * mm, CH - 44.5 * mm, "Date of Birth")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, CH - 48 * mm, A["dob_slash"])

    # Signature line
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.line(3 * mm, CH - 52 * mm, 30 * mm, CH - 52 * mm)
    c.setFont("Helvetica", 5.5)
    c.drawString(3 * mm, CH - 52.5 * mm, "Signature")

    c.save()
    print(f"  OK {path.name}")


# ── 3. Salary Slips (Jan / Feb / Mar 2026) ───────────────────────────────────

def make_salary_slip(month: str, month_num: int) -> None:
    filename = f"salary_slip_{month.lower()}2026.pdf"
    path = UPLOADS / filename
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    story = []

    # Company header
    story.append(Paragraph(E["name"].upper(), ps("H", fontSize=16, fontName="Helvetica-Bold",
                                                  alignment=TA_CENTER, textColor=colors.HexColor("#003580"))))
    story.append(Paragraph(E["addr"], ps("HA", fontSize=8, alignment=TA_CENTER,
                                          textColor=colors.HexColor("#555555"))))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#003580")))
    story.append(Spacer(1, 2*mm))

    # Slip title
    story.append(Paragraph(f"PAY SLIP – {month.upper()} 2026", ps("ST", fontSize=11,
                                                                     fontName="Helvetica-Bold",
                                                                     alignment=TA_CENTER)))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 4*mm))

    # Employee info table
    ei = [
        ["Employee ID", E["emp_id"], "Department", E["dept"]],
        ["Employee Name", A["name"], "Designation", E["designation"]],
        ["PAN", A["pan"], "UAN", E["uan"]],
        ["PF Account", E["pf_no"], "Bank A/C", "XXXX XXXX 4521 (HDFC)"],
        ["Pay Period", f"01/{month_num:02d}/2026 – {_last_day(month_num)}/{month_num:02d}/2026",
         "Pay Date", f"05/{month_num:02d}/2026"],
    ]
    t = Table(ei, colWidths=[38*mm, 55*mm, 38*mm, 55*mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003580")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#003580")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F7FA"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    # Earnings vs Deductions
    story.append(Paragraph("EARNINGS & DEDUCTIONS", ps("ED", fontSize=9,
                                                         fontName="Helvetica-Bold",
                                                         textColor=colors.HexColor("#003580"))))
    story.append(Spacer(1, 2*mm))

    earn_ded = [
        ["EARNINGS", "Amount (Rs.)", "DEDUCTIONS", "Amount (Rs.)"],
        ["Basic Salary", inr(S["basic"]), "Provident Fund (EE)", inr(S["pf_ee"])],
        ["House Rent Allowance", inr(S["hra"]), "Income Tax (TDS)", inr(S["tds"])],
        ["Special Allowance", inr(S["special"]), "Professional Tax", inr(S["prof_tax"])],
        ["", "", "", ""],
        ["GROSS SALARY", inr(S["gross"]), "TOTAL DEDUCTIONS", inr(S["pf_ee"] + S["tds"] + S["prof_tax"])],
    ]
    t2 = Table(earn_ded, colWidths=[65*mm, 30*mm, 65*mm, 30*mm])
    t2.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003580")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F9F9F9")]),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    # Net Pay box
    net_data = [["NET PAY (Amount Credited to Bank)", inr_sym(S["net"])]]
    nt = Table(net_data, colWidths=[140*mm, 40*mm])
    nt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#003580")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
    ]))
    story.append(nt)
    story.append(Spacer(1, 4*mm))

    # PF note
    story.append(Paragraph(
        f"Employer PF Contribution (12% of Basic): {inr_sym(S['pf_er'])}  |  "
        f"Total CTC Components this month: {inr_sym(S['gross'] + S['pf_er'])}",
        ps("PF", fontSize=7.5, textColor=colors.HexColor("#555555"))
    ))
    story.append(Spacer(1, 6*mm))

    # Signatures
    sig = [["", ""],
           ["_______________________________", "_______________________________"],
           ["Employee Signature", "Authorised Signatory – HR & Payroll"]]
    st = Table(sig, colWidths=[90*mm, 90*mm])
    st.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(st)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "This is a computer-generated pay slip and does not require a physical signature. "
        "For queries contact: payroll.india@infosys.com",
        ps("FOOT", fontSize=6.5, textColor=colors.HexColor("#888888"), alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"  OK {path.name}")


def _last_day(month: int) -> int:
    import calendar
    return calendar.monthrange(2026, month)[1]


# ── 4. Bank Statement ─────────────────────────────────────────────────────────

def make_bank_statement() -> None:
    path = UPLOADS / "hdfc_bank_statement_6m.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    story = []

    # Header
    story.append(Paragraph("HDFC BANK LIMITED", ps("BH", fontSize=18, fontName="Helvetica-Bold",
                                                     textColor=colors.HexColor("#004B87"),
                                                     alignment=TA_CENTER)))
    story.append(Paragraph("Koramangala Branch, 100 Feet Road, Bengaluru – 560034  |  IFSC: HDFC0001234",
                            ps("BS", fontSize=7.5, alignment=TA_CENTER,
                               textColor=colors.HexColor("#555555"))))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#004B87")))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph("ACCOUNT STATEMENT", ps("AS", fontSize=11, fontName="Helvetica-Bold",
                                                     alignment=TA_CENTER)))
    story.append(Spacer(1, 3*mm))

    # Account details
    ad = [
        ["Account Holder", A["name"], "Account Number", "XXXX XXXX 4521"],
        ["Account Type", "Savings Account", "Branch", "Koramangala, Bengaluru"],
        ["IFSC Code", "HDFC0001234", "MICR Code", "560240001"],
        ["Statement Period", "01-Oct-2025 to 31-Mar-2026", "Currency", "INR"],
        ["Customer ID", "CIF-78234561", "PAN Linked", A["pan"]],
    ]
    at = Table(ad, colWidths=[38*mm, 60*mm, 38*mm, 50*mm])
    at.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#004B87")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#004B87")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#EBF3FB"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(at)
    story.append(Spacer(1, 5*mm))

    # Summary
    story.append(Paragraph("ACCOUNT SUMMARY", ps("SH", fontSize=9, fontName="Helvetica-Bold",
                                                   textColor=colors.HexColor("#004B87"))))
    story.append(Spacer(1, 2*mm))
    summ = [
        ["Opening Balance (01-Oct-2025)", "", inr_sym(245_000)],
        ["Total Credits (Oct 2025 – Mar 2026)", "", inr_sym(795_000)],
        ["Total Debits (Oct 2025 – Mar 2026)", "", inr_sym(567_400)],
        ["Closing Balance (31-Mar-2026)", "", inr_sym(472_600)],
        ["Average Monthly Balance", "", inr_sym(280_000)],
        ["Minimum Balance (period)", "", inr_sym(142_000)],
        ["Maximum Balance (period)", "", inr_sym(521_000)],
    ]
    st2 = Table(summ, colWidths=[100*mm, 30*mm, 50*mm])
    st2.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EBF3FB")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -2), [colors.white, colors.HexColor("#F9F9F9")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(st2)
    story.append(Spacer(1, 5*mm))

    # Transactions
    story.append(Paragraph("TRANSACTION DETAILS", ps("TH", fontSize=9, fontName="Helvetica-Bold",
                                                       textColor=colors.HexColor("#004B87"))))
    story.append(Spacer(1, 2*mm))

    txn_header = ["Date", "Description", "Ref No.", "Debit (Rs.)", "Credit (Rs.)", "Balance (Rs.)"]

    months_data = [
        ("Oct 2025", 10, 245_000),
        ("Nov 2025", 11, None),
        ("Dec 2025", 12, None),
        ("Jan 2026",  1, None),
        ("Feb 2026",  2, None),
        ("Mar 2026",  3, None),
    ]

    all_txns = [txn_header]
    bal = 245_000

    for label, mo, _ in months_data:
        yr = 2025 if mo >= 10 else 2026
        # opening row
        all_txns.append([f"01/{mo:02d}/{yr}", f"── {label} ──", "", "", "", inr(bal)])

        # Salary credit on 5th — NOTE: Rs.1,25,000 (net) not Rs.1,54,062 (gross) — DELIBERATE MISMATCH
        bal += 125_000
        all_txns.append([f"05/{mo:02d}/{yr}", "NEFT CR-INFOSYS LTD-SALARY",
                          f"N{yr}{mo:02d}050001", "", inr(125_000), inr(bal)])

        # EMI deductions
        bal -= 9_000
        all_txns.append([f"07/{mo:02d}/{yr}", "EMI-HDFC PERSONAL LOAN-NACH",
                          f"N{yr}{mo:02d}070002", inr(9_000), "", inr(bal)])
        bal -= 8_000
        all_txns.append([f"10/{mo:02d}/{yr}", "CC MIN PAY-ICICI BANK-NACH",
                          f"N{yr}{mo:02d}100003", inr(8_000), "", inr(bal)])
        bal -= 5_500
        all_txns.append([f"12/{mo:02d}/{yr}", "LIC PREMIUM-NACH",
                          f"N{yr}{mo:02d}120004", inr(5_500), "", inr(bal)])

        # Living expenses
        bal -= 18_000
        all_txns.append([f"15/{mo:02d}/{yr}", "UPI-GROCERY/UTILITIES/MISC",
                          f"U{yr}{mo:02d}150005", inr(18_000), "", inr(bal)])
        bal -= 3_500
        all_txns.append([f"20/{mo:02d}/{yr}", "NACH-SOCIETY MAINTENANCE",
                          f"N{yr}{mo:02d}200006", inr(3_500), "", inr(bal)])
        bal -= 8_000
        all_txns.append([f"25/{mo:02d}/{yr}", "ATM WDL / MISC PAYMENTS",
                          f"A{yr}{mo:02d}250007", inr(8_000), "", inr(bal)])

    txn_table = Table(all_txns,
                      colWidths=[18*mm, 65*mm, 25*mm, 20*mm, 20*mm, 22*mm])
    style = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#004B87")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ])
    # Highlight monthly salary credit rows in light green
    row = 1
    for i, txn in enumerate(all_txns[1:], start=1):
        if "INFOSYS LTD-SALARY" in str(txn[1]):
            style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#E8F5E9"))
            style.add("FONTNAME", (0, i), (-1, i), "Helvetica-Bold")
        elif "──" in str(txn[1]):
            style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#EBF3FB"))
            style.add("FONTNAME", (0, i), (-1, i), "Helvetica-Bold")

    txn_table.setStyle(style)
    story.append(txn_table)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "Note: Salary credited reflects net take-home pay after statutory deductions at source. "
        "This statement is digitally generated and is valid without signature.",
        ps("BFOOTER", fontSize=7, textColor=colors.HexColor("#666666"))
    ))

    doc.build(story)
    print(f"  OK {path.name}")


# ── 5. Form 16 ────────────────────────────────────────────────────────────────

def make_form16() -> None:
    path = UPLOADS / "form16_fy2024.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Paragraph("FORM 16", ps("F16T", fontSize=16, fontName="Helvetica-Bold",
                                          alignment=TA_CENTER,
                                          textColor=colors.HexColor("#8B0000"))))
    story.append(Paragraph("[See rule 31(1)(a)]", ps("F16S", fontSize=9, alignment=TA_CENTER,
                                                       textColor=colors.HexColor("#555555"))))
    story.append(Paragraph(
        "Certificate under Section 203 of the Income-tax Act, 1961 for tax deducted at source "
        "from income chargeable under the head 'Salaries'",
        ps("F16D", fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#333333"))
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#8B0000")))
    story.append(Spacer(1, 3*mm))

    # Part A
    story.append(Paragraph("PART A – TDS CERTIFICATE", ps("PA", fontSize=10,
                                                            fontName="Helvetica-Bold",
                                                            textColor=colors.HexColor("#8B0000"))))
    story.append(Spacer(1, 2*mm))

    pa_data = [
        ["Name and address of Employer", E["name"] + "\n" + E["addr"]],
        ["TAN of Deductor", E["tan"]],
        ["PAN of Deductor", E["pan"]],
        ["Name and address of Employee", A["name"] + "\n" + A["addr1"] + "\n" + A["addr2"]],
        ["PAN of Employee", A["pan"]],
        ["Assessment Year", "2024-25"],
        ["Period of Employment (FY 2023-24)", "01-Apr-2023 to 31-Mar-2024"],
        ["Total Amount of Tax Deposited / Remitted", inr_sym(1_32_744)],
    ]
    pa_table = Table(pa_data, colWidths=[80*mm, 100*mm])
    pa_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#FFF5F5"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pa_table)
    story.append(Spacer(1, 5*mm))

    # Part B
    story.append(Paragraph("PART B – DETAILS OF SALARY PAID AND TAX DEDUCTED",
                            ps("PB", fontSize=10, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#8B0000"))))
    story.append(Spacer(1, 2*mm))

    pb_data = [
        ["Particulars", "Amount (Rs.)"],
        ["1. Gross Salary (a+b+c)", inr(18_48_744)],
        ["   a. Salary as per provisions of section 17(1)", inr(18_48_744)],
        ["   b. Value of perquisites u/s 17(2)", "NIL"],
        ["   c. Profits in lieu of salary u/s 17(3)", "NIL"],
        ["2. Less: Allowances exempt under section 10", ""],
        ["   a. HRA Exemption [Sec 10(13A)]", inr(3_69_744)],
        ["3. Net Salary (1 - 2)", inr(14_79_000)],
        ["4. Deductions under Chapter VI-A", ""],
        ["   a. 80C – Employee PF Contribution", inr(1_10_928)],
        ["   b. 80C – Other (LIC / ELSS / PPF)", inr(50_000)],
        ["   c. 80D – Health Insurance Premium", inr(25_000)],
        ["   Total Chapter VI-A Deductions", inr(1_85_928)],
        ["5. Standard Deduction (Section 16(ia))", inr(50_000)],
        ["6. Total Taxable Income (3 - 4 - 5)", inr(12_43_072)],
        ["7. Tax on Total Income", inr(1_32_744)],
        ["8. Surcharge", "NIL"],
        ["9. Health and Education Cess (4%)", inr(5_310)],
        ["10. Tax Payable", inr(1_38_054)],
        ["11. Relief under Section 89", "NIL"],
        ["12. Net Tax Payable", inr(1_38_054)],
        ["13. Total Tax Deducted at Source (TDS)", inr(1_32_744)],
    ]
    pb_table = Table(pb_data, colWidths=[130*mm, 50*mm])
    pb_style = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8B0000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF9F9")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 5),
    ])
    # Bold key summary rows
    for row_idx in [1, 3+3, 14, 22]:
        if row_idx < len(pb_data):
            pb_style.add("FONTNAME", (0, row_idx), (-1, row_idx), "Helvetica-Bold")
            pb_style.add("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#FFE4E4"))
    pb_table.setStyle(pb_style)
    story.append(pb_table)
    story.append(Spacer(1, 5*mm))

    # Certification
    story.append(Paragraph(
        "CERTIFICATION: I, the undersigned, do hereby certify that a sum of "
        f"{inr_sym(1_32_744)} has been deducted at source and deposited to the "
        "credit of the Central Government as per the provisions of Chapter XVII-B of the "
        "Income-tax Act, 1961.",
        BODY
    ))
    story.append(Spacer(1, 8*mm))

    sig2 = [["", ""],
            ["_______________________________", ""],
            [f"Authorised Signatory", ""],
            [f"Designation: VP – Human Resources", ""],
            [f"{E['name']}", ""],
            ["Date: 15-Jun-2024", f"TRACES Verification: Enabled"]]
    st3 = Table(sig2, colWidths=[90*mm, 90*mm])
    st3.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8),
                              ("TOPPADDING", (0, 0), (-1, -1), 1)]))
    story.append(st3)

    doc.build(story)
    print(f"  OK {path.name}")


# ── 6. Sale Agreement ─────────────────────────────────────────────────────────

def make_sale_agreement() -> None:
    path = UPLOADS / "sale_agreement_koramangala.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=25*mm, rightMargin=25*mm)
    story = []

    story.append(Paragraph("AGREEMENT FOR SALE OF IMMOVABLE PROPERTY", ps("SAT", fontSize=13,
                                                                             fontName="Helvetica-Bold",
                                                                             alignment=TA_CENTER)))
    story.append(Paragraph(f"(Registered under the Karnataka Stamps Act, 1957)",
                            ps("SAS", fontSize=8, alignment=TA_CENTER,
                               textColor=colors.HexColor("#555555"))))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "This Agreement for Sale is entered into on this <b>15th day of February 2026</b>, "
        "at Bengaluru, Karnataka, between:",
        BODY
    ))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("<b>THE VENDOR / SELLER:</b>", H2))
    story.append(Paragraph(
        f"<b>{PROP['seller']}</b>, a company incorporated under the Companies Act, 2013, "
        "having its registered office at 130/1, Ulsoor Road, Bengaluru – 560042, Karnataka, "
        "represented by its Authorised Signatory Mr. Venkatesh Narayanan "
        "(hereinafter referred to as the <b>'Vendor'</b>)",
        BODY
    ))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("<b>AND</b>", CENTER))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("<b>THE PURCHASER / BUYER:</b>", H2))
    story.append(Paragraph(
        f"<b>{A['name']}</b>, S/o. {A['father']}, aged about 41 years, residing at "
        f"{A['addr1']}, {A['addr2']}, "
        f"PAN: {A['pan']}, Aadhaar: {A['aadhaar']} "
        "(hereinafter referred to as the <b>'Purchaser'</b>)",
        BODY
    ))
    story.append(Spacer(1, 4*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("<b>PROPERTY DESCRIPTION:</b>", H2))

    prop_data = [
        ["Property", PROP["addr"]],
        ["Survey / Khata", f"{PROP['survey']}\n{PROP['khata']}"],
        ["Built-up Area", PROP["area"]],
        ["Floor", "4th Floor, Tower A, Sunrise Apartments"],
        ["Property Type", "Residential Apartment"],
    ]
    pt = Table(prop_data, colWidths=[45*mm, 110*mm])
    pt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F5F5"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>CONSIDERATION AND PAYMENT SCHEDULE:</b>", H2))
    story.append(Paragraph(
        f"The total Sale Consideration agreed between the parties is "
        f"<b>Rs. {PROP['consideration']}/- (Rupees One Crore Fifteen Lakhs Only)</b>, "
        "payable as follows:",
        BODY
    ))
    pay_data = [
        ["Milestone", "Amount (Rs.)", "Date"],
        ["Booking Amount (Token)", "11,50,000", "15-Nov-2024"],
        ["On execution of this Agreement", "34,50,000", "15-Feb-2026"],
        ["On possession / registration", "69,00,000", "On completion"],
        ["TOTAL CONSIDERATION", "1,15,00,000", ""],
    ]
    pyt = Table(pay_data, colWidths=[80*mm, 40*mm, 40*mm])
    pyt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EEEEEE")),
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(pyt)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "The Vendor assures the Purchaser that the property is free from all encumbrances, "
        "liens, charges, mortgages, attachments and court proceedings. The Vendor shall execute "
        "the absolute Sale Deed upon receipt of full consideration. The Purchaser is availing a "
        "Home Loan from HDFC Bank / any other bank of their choice, and the Vendor agrees to "
        "provide all necessary documents and NOC as required by the lending institution.",
        BODY
    ))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("<b>STAMP DUTY AND REGISTRATION:</b>", H2))
    story.append(Paragraph(
        f"Stamp Duty payable: Rs. {PROP['stamp_duty']}/- | "
        f"Registration Fee: Rs. {PROP['reg_fee']}/- | "
        f"Registration Document No.: {PROP['reg_no']}",
        BODY
    ))
    story.append(Spacer(1, 6*mm))

    # Signatures
    sig = [
        ["VENDOR", "", "PURCHASER"],
        ["", "", ""],
        ["_______________________", "", "_______________________"],
        [PROP["seller"], "", A["name"]],
        ["(Authorised Signatory)", "", ""],
        ["Date: 15-02-2026", "", "Date: 15-02-2026"],
    ]
    sigt = Table(sig, colWidths=[70*mm, 20*mm, 70*mm])
    sigt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(sigt)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Witnessed by: 1. ____________________  2. ____________________  "
        "Sub-Registrar: Koramangala, Bengaluru South",
        SMALL
    ))

    doc.build(story)
    print(f"  OK {path.name}")


# ── 7. Title Deed ─────────────────────────────────────────────────────────────

def make_title_deed() -> None:
    path = UPLOADS / "property_title_deed.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=25*mm, rightMargin=25*mm)
    story = []

    story.append(Paragraph("OFFICE OF THE SUB-REGISTRAR", ps("TDG", fontSize=10,
                                                               fontName="Helvetica-Bold",
                                                               alignment=TA_CENTER,
                                                               textColor=colors.HexColor("#8B0000"))))
    story.append(Paragraph("Koramangala, Bengaluru South, Karnataka", ps("TDGA", fontSize=8,
                                                                           alignment=TA_CENTER)))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("CERTIFIED COPY OF REGISTERED SALE DEED", ps("TDT", fontSize=13,
                                                                          fontName="Helvetica-Bold",
                                                                          alignment=TA_CENTER)))
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#8B0000")))
    story.append(Spacer(1, 3*mm))

    reg_data = [
        ["Registration Number", PROP["reg_no"]],
        ["Book Number", "Book I – Volume 4521"],
        ["Registration Date", PROP["reg_date"]],
        ["Document Type", "Absolute Sale Deed"],
        ["Sub-Registrar Office", "Koramangala, Bengaluru South"],
        ["District", "Bengaluru Urban"],
        ["State", "Karnataka"],
    ]
    rt = Table(reg_data, colWidths=[65*mm, 100*mm])
    rt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#FFF5F5"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(rt)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("<b>PARTIES TO THE DEED:</b>", H2))
    story.append(Paragraph(
        f"<b>Vendor:</b> {PROP['seller']}, Bengaluru<br/>"
        f"<b>Purchaser:</b> {A['name']}, S/o {A['father']}, "
        f"residing at {A['addr1']}, {A['addr2']}, PAN: {A['pan']}",
        BODY
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>SCHEDULE OF PROPERTY:</b>", H2))
    prop_sched = [
        ["Description of Property", PROP["addr"]],
        ["Survey / Khata Details", f"{PROP['survey']}\n{PROP['khata']}"],
        ["Registered Area", PROP["area"]],
        ["Boundaries (North)", "Common Corridor"],
        ["Boundaries (South)", "Open Car Parking"],
        ["Boundaries (East)", "Flat 4A"],
        ["Boundaries (West)", "Flat 4C"],
        ["Nature of Title", "Freehold / Absolute Ownership"],
    ]
    pst = Table(prop_sched, colWidths=[50*mm, 115*mm])
    pst.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pst)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>CONSIDERATION DETAILS:</b>", H2))
    story.append(Paragraph(
        f"Total Sale Consideration: <b>Rs. {PROP['consideration']}/- "
        f"(Rupees One Crore Fifteen Lakhs Only)</b><br/>"
        f"Stamp Duty Paid: Rs. {PROP['stamp_duty']}/- | "
        f"Registration Charges: Rs. {PROP['reg_fee']}/-<br/>"
        "Mode of Payment: RTGS / NEFT as per bank receipts on record",
        BODY
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "By virtue of this Deed, the Vendor doth hereby convey, sell, transfer and assign "
        f"unto the Purchaser <b>{A['name']}</b>, all that piece and parcel of immovable "
        "property described in the Schedule above, TO HAVE AND TO HOLD the said property "
        "unto and to the use of the Purchaser absolutely and forever, free from all "
        "encumbrances, charges, liens and claims whatsoever.",
        BODY
    ))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("<b>CERTIFICATION BY SUB-REGISTRAR:</b>", H2))
    story.append(Paragraph(
        f"Certified that this document was presented for registration on {PROP['reg_date']} "
        f"and registered as Document No. {PROP['reg_no']} in Book I, Volume 4521 "
        "of the office of the Sub-Registrar, Koramangala, Bengaluru South.",
        BODY
    ))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "Sd/-  V.R. Krishnaswamy, Sub-Registrar, Koramangala",
        ps("SR", fontSize=8, fontName="Helvetica-Bold")
    ))
    story.append(Paragraph(f"Date: {PROP['reg_date']}   Seal: [OFFICE SEAL]", SMALL))

    doc.build(story)
    print(f"  OK {path.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nGenerating synthetic documents -> {UPLOADS}/\n")

    make_aadhaar()
    make_pan()

    for month, num in [("jan", 1), ("feb", 2), ("mar", 3)]:
        make_salary_slip(month.capitalize(), num)

    make_bank_statement()
    make_form16()
    make_sale_agreement()
    make_title_deed()

    print(f"\nDone. {len(list(UPLOADS.iterdir()))} files in {UPLOADS}/")
    print("\nIncome mismatch summary (for Agent 2b / Agent 4 to catch):")
    print(f"  Salary slips   -> Gross: Rs.{S['gross']:,}  |  Net: Rs.{S['net']:,}")
    print(f"  Bank statement -> Salary credit: Rs.{S['net']:,}  (net amount)")
    print(f"  Apparent gap   -> Rs.{S['gross']:,} declared vs Rs.{S['net']:,} in bank")
    print(f"  Explained by   -> PF Rs.{S['pf_ee']:,} + TDS Rs.{S['tds']:,} + PT Rs.{S['prof_tax']:,} = Rs.{S['pf_ee']+S['tds']+S['prof_tax']:,}")
