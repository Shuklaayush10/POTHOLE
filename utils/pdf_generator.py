import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(report, filepath, current_app):
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    normal_style = styles['Normal']
    
    elements = []
    
    # Title
    elements.append(Paragraph("Pothole Analysis Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Details Table
    data = [
        ["Report ID:", str(report.id)],
        ["Date/Time:", report.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        ["Location:", f"Lat: {report.latitude}, Lng: {report.longitude}" if report.latitude else "Not Provided"],
        ["Severity:", report.severity],
        ["Dimensions:", f"Area: {report.area} px\u00b2"],
        ["Recommended Action:", report.recommendation]
    ]
    
    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Image
    processed_image_path = os.path.join(current_app.config['PROCESSED_FOLDER'], report.processed_image)
    if os.path.exists(processed_image_path):
        elements.append(Paragraph("Processed Image:", styles['Heading2']))
        elements.append(Spacer(1, 10))
        img = Image(processed_image_path, width=400, height=300)
        elements.append(img)
    
    doc.build(elements)
    return filepath
