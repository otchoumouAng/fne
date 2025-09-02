import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.renderPDF import drawToFile

def generate_invoice_pdf(filepath, invoice_data, client_data, company_data):
    """
    Génère un fichier PDF pour une facture.
    """
    doc = SimpleDocTemplate(filepath,
                            rightMargin=2*cm,
                            leftMargin=2*cm,
                            topMargin=2*cm,
                            bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    header_style = styles['h1']
    header_style.alignment = TA_RIGHT
    p_header = Paragraph(f"FACTURE #{invoice_data['details']['id']}", header_style)
    story.append(p_header)

    # QR Code FNE
    if invoice_data['details'].get('fne_qr_code'):
        qr_code_content = invoice_data['details']['fne_qr_code']
        qr_code = qr.QrCodeWidget(qr_code_content)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[45./width,0,0,45./height,0,0])
        d.add(qr_code)
        # This is a bit complex, we'll place it in a table to align it
        header_table_data = [[p_header, d]]
        header_table = Table(header_table_data, colWidths=[12*cm, 4*cm])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story = [header_table] # Replace story with the table

    story.append(Spacer(1, 1*cm))

    # --- Company and Client Info ---
    company_address = f"""
    <b>{company_data.get('name', 'Votre Entreprise')}</b><br/>
    {company_data.get('address', 'Votre Adresse')}<br/>
    Tel: {company_data.get('phone', 'Votre Tel')}<br/>
    Email: {company_data.get('email', 'Votre Email')}<br/>
    N° Contribuable: {company_data.get('tax_id', 'Votre N° CC')}
    """
    client_address = f"""
    <b>Facturé à :</b><br/>
    {client_data.get('name', '')}<br/>
    {client_data.get('address', '')}<br/>
    {client_data.get('phone', '')}<br/>
    {client_data.get('email', '')}
    """

    p_style_left = ParagraphStyle(name='left', parent=styles['Normal'], alignment=TA_LEFT)
    p_company = Paragraph(company_address, p_style_left)
    p_client = Paragraph(client_address, p_style_left)

    info_table_data = [[p_company, p_client]]
    info_table = Table(info_table_data, colWidths=[8*cm, 8*cm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 1*cm))

    # --- Invoice Dates and NIM ---
    p_style_right = ParagraphStyle(name='right', parent=styles['Normal'], alignment=TA_RIGHT)
    date_info = f"""
    Date d'émission: {invoice_data['details']['issue_date']}<br/>
    Date d'échéance: {invoice_data['details']['due_date']}
    """
    nim_info = f"<b>NIM FNE:</b> {invoice_data['details'].get('fne_nim', 'N/A')}"
    story.append(Paragraph(date_info, styles['Normal']))
    if invoice_data['details'].get('fne_nim'):
        story.append(Paragraph(nim_info, styles['Normal']))

    story.append(Spacer(1, 1*cm))

    # --- Line Items Table ---
    table_header = ['Description', 'Qté', 'Prix U. HT', 'Total HT']
    table_data = [table_header]

    subtotal = 0
    total_vat = 0

    for item in invoice_data['items']:
        total_ht = item['quantity'] * item['unit_price']
        subtotal += total_ht
        total_vat += total_ht * (item['tax_rate'] / 100.0)

        row = [
            Paragraph(item['description'], styles['Normal']),
            item['quantity'],
            f"{item['unit_price']:.2f}",
            f"{total_ht:.2f}"
        ]
        table_data.append(row)

    items_table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'), # Align description to the left
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5*cm))

    # --- Totals ---
    grand_total = subtotal + total_vat
    totals_data = [
        ['Total HT:', f"{subtotal:.2f} €"],
        ['Montant TVA:', f"{total_vat:.2f} €"],
        ['Total TTC:', f"{grand_total:.2f} €"],
    ]
    totals_table = Table(totals_data, colWidths=[3*cm, 3*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,2), (1,2), 'Helvetica-Bold'), # Bold for the grand total
    ]))

    # Wrap the totals table in another table to align it to the right
    wrapper_table = Table([[totals_table]], colWidths=[16*cm], hAlign='RIGHT')
    story.append(wrapper_table)

    # --- Footer ---
    story.append(Spacer(1, 2*cm))
    footer_text = "Merci pour votre confiance."
    story.append(Paragraph(footer_text, styles['Italic']))

    doc.build(story)
    print(f"PDF généré avec succès à l'emplacement : {filepath}")
    return True
