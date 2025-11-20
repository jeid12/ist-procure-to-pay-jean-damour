import os
import re
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import logging

logger = logging.getLogger(__name__)

def extract_text_from_image(image_path):
    """Extract text from image using OCR (placeholder for real OCR)"""
    try:
        # In production, use pytesseract
        # import pytesseract
        # from PIL import Image
        # image = Image.open(image_path)
        # text = pytesseract.image_to_string(image)
        # return text
        
        # Placeholder implementation
        logger.info(f"Extracting text from image: {image_path}")
        return ""
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using OCR (placeholder for real OCR)"""
    try:
        # In production, use pdf2image and pytesseract
        # from pdf2image import convert_from_path
        # import pytesseract
        # images = convert_from_path(pdf_path)
        # text = ""
        # for image in images:
        #     text += pytesseract.image_to_string(image) + "\n"
        # return text
        
        # Placeholder implementation
        logger.info(f"Extracting text from PDF: {pdf_path}")
        return ""
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return ""

def extract_proforma_data(file_path):
    """Extract vendor and item information from proforma invoice"""
    try:
        # Determine file type
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png']:
            text = extract_text_from_image(file_path)
        elif ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return {}
        
        # Extract information using regex patterns
        data = {}
        
        # Extract vendor name (looking for common patterns)
        vendor_patterns = [
            r'(?:Company|Vendor|Supplier):\s*(.+)',
            r'^([A-Z][A-Za-z\s&]+(?:Ltd|Inc|Corp|LLC))',
        ]
        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                data['vendor_name'] = match.group(1).strip()
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            data['vendor_email'] = email_match.group(0)
        
        # Extract phone
        phone_pattern = r'(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            data['vendor_phone'] = phone_match.group(0)
        
        # Extract total amount
        amount_pattern = r'(?:Total|Amount|Sum):\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        amount_match = re.search(amount_pattern, text, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            data['total_amount'] = float(amount_str)
        
        logger.info(f"Extracted data: {data}")
        return data
    
    except Exception as e:
        logger.error(f"Proforma extraction failed: {str(e)}")
        return {}

def validate_receipt_against_po(receipt_path, purchase_order):
    """Validate receipt data against purchase order"""
    try:
        # Extract text from receipt
        ext = os.path.splitext(receipt_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png']:
            text = extract_text_from_image(receipt_path)
        elif ext == '.pdf':
            text = extract_text_from_pdf(receipt_path)
        else:
            return {'valid': False, 'message': 'Unsupported file type'}
        
        # Extract amount from receipt
        amount_pattern = r'(?:Total|Amount|Sum):\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        amount_match = re.search(amount_pattern, text, re.IGNORECASE)
        
        if amount_match:
            receipt_amount = float(amount_match.group(1).replace(',', ''))
            po_amount = float(purchase_order.total_amount)
            
            # Allow 1% variance
            variance = abs(receipt_amount - po_amount) / po_amount
            
            if variance <= 0.01:
                return {
                    'valid': True,
                    'message': 'Receipt matches PO',
                    'receipt_amount': receipt_amount,
                    'po_amount': po_amount
                }
            else:
                return {
                    'valid': False,
                    'message': 'Amount mismatch',
                    'receipt_amount': receipt_amount,
                    'po_amount': po_amount,
                    'variance': variance * 100
                }
        
        return {'valid': False, 'message': 'Could not extract amount from receipt'}
    
    except Exception as e:
        logger.error(f"Receipt validation failed: {str(e)}")
        return {'valid': False, 'message': str(e)}

def generate_po_document(purchase_order):
    """Generate PDF document for purchase order"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Title
        title = Paragraph(f"PURCHASE ORDER", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # PO Info
        po_data = [
            ['PO Number:', purchase_order.po_number],
            ['Date:', purchase_order.created_at.strftime('%Y-%m-%d')],
            ['Status:', purchase_order.get_status_display()],
        ]
        
        po_table = Table(po_data, colWidths=[2*inch, 3*inch])
        po_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(po_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Vendor Information
        if purchase_order.vendor_name:
            vendor_title = Paragraph("<b>Vendor Information</b>", styles['Heading2'])
            elements.append(vendor_title)
            elements.append(Spacer(1, 0.1*inch))
            
            vendor_data = [
                ['Name:', purchase_order.vendor_name],
                ['Email:', purchase_order.vendor_email or 'N/A'],
                ['Phone:', purchase_order.vendor_phone or 'N/A'],
                ['Address:', purchase_order.vendor_address or 'N/A'],
            ]
            
            vendor_table = Table(vendor_data, colWidths=[1.5*inch, 4*inch])
            vendor_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(vendor_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Items
        items_title = Paragraph("<b>Items</b>", styles['Heading2'])
        elements.append(items_title)
        elements.append(Spacer(1, 0.1*inch))
        
        items = purchase_order.purchase_request.items.all()
        if items.exists():
            item_data = [['Item', 'Description', 'Qty', 'Unit Price', 'Total']]
            for item in items:
                item_data.append([
                    item.item_name,
                    item.description[:50],
                    str(item.quantity),
                    f'${item.unit_price:,.2f}',
                    f'${item.total_price:,.2f}'
                ])
            
            item_table = Table(item_data, colWidths=[1.5*inch, 2*inch, 0.5*inch, 1*inch, 1*inch])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(item_table)
        
        # Total
        elements.append(Spacer(1, 0.3*inch))
        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            alignment=TA_RIGHT
        )
        total = Paragraph(f"<b>Total Amount: ${purchase_order.total_amount:,.2f}</b>", total_style)
        elements.append(total)
        
        # Notes
        if purchase_order.notes:
            elements.append(Spacer(1, 0.3*inch))
            notes_title = Paragraph("<b>Notes</b>", styles['Heading2'])
            elements.append(notes_title)
            notes = Paragraph(purchase_order.notes, styles['Normal'])
            elements.append(notes)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Create file object
        filename = f'PO_{purchase_order.po_number}.pdf'
        return ContentFile(buffer.read(), name=filename)
    
    except Exception as e:
        logger.error(f"PO document generation failed: {str(e)}")
        raise
