#!/usr/bin/env python3
"""Convert KIRO2 Ultra-Deep Analysis Report to PDF"""
import sys
import codecs
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Force UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def convert_markdown_to_pdf():
    """Convert the markdown report to PDF with proper formatting"""
    print("🔄 Converting Markdown to PDF...")

    # File paths
    md_file = Path("KIRO2_ULTRA_DEEP_ANALYSIS_REPORT.md")
    pdf_file = Path("KIRO2_ULTRA_DEEP_ANALYSIS_REPORT.pdf")

    if not md_file.exists():
        print(f"❌ Error: {md_file} not found")
        return False

    # Read markdown content
    print(f"📖 Reading {md_file.name}...")
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    print(f"📝 Creating PDF document...")
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="KIRO2 Ultra-Deep Technical Analysis Report",
        author="Claude Code Analysis",
        subject="Production Readiness Assessment for Teknofest 2025"
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles for Turkish text
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=28
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=12,
        spaceBefore=12,
        leading=22
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#424242'),
        spaceAfter=10,
        spaceBefore=10,
        leading=18
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        leading=10,
        leftIndent=20,
        rightIndent=20,
        spaceAfter=6,
        spaceBefore=6,
        backColor=colors.HexColor('#f5f5f5'),
        borderColor=colors.HexColor('#e0e0e0'),
        borderWidth=1,
        borderPadding=5
    )

    # Build PDF content
    story = []

    # Parse markdown content
    lines = content.split('\n')
    in_code_block = False
    code_buffer = []

    print(f"📄 Processing {len(lines)} lines...")

    for i, line in enumerate(lines):
        # Progress indicator
        if i % 1000 == 0:
            print(f"   Progress: {i}/{len(lines)} lines ({i*100//len(lines)}%)")

        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End of code block
                if code_buffer:
                    code_text = '<br/>'.join(code_buffer)
                    story.append(Paragraph(f'<font face="Courier">{code_text}</font>', code_style))
                    story.append(Spacer(1, 0.2*cm))
                code_buffer = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
            continue

        if in_code_block:
            # Escape HTML in code
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            code_buffer.append(escaped)
            continue

        # Skip empty lines
        if not line.strip():
            story.append(Spacer(1, 0.3*cm))
            continue

        # Handle headings
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(PageBreak())
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.5*cm))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading1_style))
            story.append(Spacer(1, 0.3*cm))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading2_style))
            story.append(Spacer(1, 0.2*cm))

        # Handle list items
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            story.append(Paragraph(f'• {text}', body_style))

        # Handle numbered lists
        elif line[0].isdigit() and '. ' in line[:5]:
            story.append(Paragraph(line.strip(), body_style))

        # Handle bold/emphasis (simple approach)
        elif '**' in line or '__' in line:
            # Properly handle ** for bold
            import re
            text = line
            # Replace **text** with <b>text</b>
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            # Replace __text__ with <i>text</i>
            text = re.sub(r'__([^_]+)__', r'<i>\1</i>', text)
            # Escape any remaining special chars
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Re-enable our tags
            text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
            text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
            story.append(Paragraph(text, body_style))

        # Regular paragraph
        else:
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))

    # Build PDF
    print(f"🔨 Building PDF with {len(story)} elements...")
    doc.build(story)

    # Check file size
    pdf_size = pdf_file.stat().st_size
    pdf_size_mb = pdf_size / (1024 * 1024)

    print(f"\n✅ PDF created successfully!")
    print(f"📊 File: {pdf_file}")
    print(f"📊 Size: {pdf_size_mb:.2f} MB")
    print(f"📊 Pages: ~{len([s for s in story if isinstance(s, PageBreak)]) + 1}")

    return True

if __name__ == '__main__':
    try:
        success = convert_markdown_to_pdf()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
