from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_report_pdf(filename, title, subtitle, field_rows):
    """Build a clean, minimalist real-world service receipt / claim document.

    field_rows: list of (label, value) tuples rendered in a clean formatted grid.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    # Typography Styles - Monochrome & Professional
    company_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )
    company_sub = ParagraphStyle(
        "CompanySub",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e293b"),
        alignment=2,  # Right aligned
    )
    doc_sub_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontSize=8.5,
        fontName="Helvetica",
        textColor=colors.HexColor("#64748b"),
        alignment=2,
    )

    cell_label_style = ParagraphStyle(
        "CellLabel",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#334155"),
    )
    cell_val_style = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#0f172a"),
    )

    # 1. Header: Company Info on Left, Document Title on Right
    header_data = [
        [
            Paragraph("GLOBAL LINK TECHNOLOGY PVT. LTD.", company_style),
            Paragraph(title.upper(), doc_title_style),
        ],
        [
            Paragraph("Manbhawan Road, Lalitpur &nbsp;|&nbsp; Phone: 9851402916", company_sub),
            Paragraph(subtitle if subtitle else "", doc_sub_style),
        ],
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.3 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    elements = [
        header_table,
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f172a"), spaceAfter=12, spaceBefore=0),
    ]

    # 2. Main Details Table - 2 Columns (Clean Grid Layout)
    table_rows = []
    for label, val in field_rows:
        val_str = "—" if val in (None, "") else str(val)
        table_rows.append([
            Paragraph(str(label), cell_label_style),
            Paragraph(val_str, cell_val_style),
        ])

    table = Table(table_rows, colWidths=[2.2 * inch, 5.3 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)

    # 3. Signatures & Footer Notice
    elements.append(Spacer(1, 30))

    sig_label_style = ParagraphStyle("SigLabel", parent=styles["Normal"], fontSize=8.5, fontName="Helvetica", alignment=1)
    sig_data = [
        [
            Paragraph("______________________________<br/><b>Client Signature</b>", sig_label_style),
            Paragraph("______________________________<br/><b>Authorized Signature</b>", sig_label_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.75 * inch, 3.75 * inch])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 24))
    notice_style = ParagraphStyle(
        "Notice",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )
    elements.append(Paragraph("Thank you for choosing Global Link Technology Pvt. Ltd. Please keep this slip for your records.", notice_style))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response

