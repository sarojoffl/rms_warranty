from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_report_pdf(filename, title, subtitle, field_rows):
    """Build a single-record printable report (job/claim detail sheet).

    field_rows: list of (label, value) tuples rendered as a two-column table.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", 
        parent=styles["Heading1"], 
        fontSize=15, 
        spaceAfter=2,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold"
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", 
        parent=styles["Normal"], 
        fontSize=8.5,
        textColor=colors.HexColor("#64748b"), 
        spaceAfter=12
    )

    # Corporate Branding Header
    company_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0091b3"),
        spaceAfter=2
    )
    info_style = ParagraphStyle(
        "CompanyInfo",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8
    )

    elements = [
        Paragraph("GLOBAL LINK TECHNOLOGY PVT. LTD.", company_style),
        Paragraph("Manbhawan Road, Lalitpur | Phone: 9851402916 | Service Desk System", info_style),
        Spacer(1, 4),
        Paragraph(title, title_style)
    ]
    if subtitle:
        elements.append(Paragraph(subtitle, subtitle_style))

    table_data = [["Field", "Detail"]] + [
        [label, "" if value in (None, "") else str(value)] for label, value in field_rows
    ]
    table = Table(table_data, colWidths=[2.2 * inch, 4.8 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0091b3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Signature: ______________________", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
