from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
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


def build_tabular_report_pdf(filename, title, subtitle, headers, rows, col_widths=None, summary_notes=None):
    """Build a professional multi-record tabular PDF report in landscape orientation.

    filename: suggested HTTP attachment filename
    title: main title (e.g. "REPAIR JOBS REPORT")
    subtitle: filter description (e.g. "Status: Pending | Client: Nabil Bank")
    headers: list of column header strings
    rows: list of row lists/tuples containing strings or Paragraphs
    col_widths: optional list of column width values in inches
    summary_notes: optional summary text (e.g. "Total Records: 12")
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "ReportCompanyHeader",
        parent=styles["Normal"],
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )
    company_sub = ParagraphStyle(
        "ReportCompanySub",
        parent=styles["Normal"],
        fontSize=8.5,
        fontName="Helvetica",
        textColor=colors.HexColor("#475569"),
    )
    doc_title_style = ParagraphStyle(
        "ReportDocTitle",
        parent=styles["Heading1"],
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0284c7"),
        alignment=2,
    )
    doc_sub_style = ParagraphStyle(
        "ReportDocSub",
        parent=styles["Normal"],
        fontSize=8.5,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#334155"),
        alignment=2,
    )

    th_style = ParagraphStyle(
        "THStyle",
        parent=styles["Normal"],
        fontSize=8.5,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#ffffff"),
    )
    td_style = ParagraphStyle(
        "TDStyle",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica",
        textColor=colors.HexColor("#0f172a"),
        leading=10,
    )

    # 1. Header: Company Left, Report Title Right
    header_data = [
        [
            Paragraph("GLOBAL LINK TECHNOLOGY PVT. LTD.", company_style),
            Paragraph(title.upper(), doc_title_style),
        ],
        [
            Paragraph("Manbhawan Road, Lalitpur &nbsp;|&nbsp; Service Desk Operations Report", company_sub),
            Paragraph(subtitle if subtitle else "", doc_sub_style),
        ],
    ]
    header_table = Table(header_data, colWidths=[5.5 * inch, 4.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    elements = [
        header_table,
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=8, spaceBefore=0),
    ]

    if summary_notes:
        summary_style = ParagraphStyle(
            "SummaryNote",
            parent=styles["Normal"],
            fontSize=8.5,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=8,
        )
        elements.append(Paragraph(str(summary_notes), summary_style))

    # 2. Main Table
    table_data = []
    # Headers
    header_row = [Paragraph(str(h), th_style) for h in headers]
    table_data.append(header_row)

    # Data Rows
    for row in rows:
        formatted_row = []
        for cell in row:
            val_str = "—" if cell in (None, "") else str(cell)
            formatted_row.append(Paragraph(val_str, td_style))
        table_data.append(formatted_row)

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    # Alternating row backgrounds
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8fafc")))
    table.setStyle(TableStyle(t_style))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


