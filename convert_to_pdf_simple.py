#!/usr/bin/env python3
"""Convert KIRO2 Ultra-Deep Analysis Report to PDF - Simple Version"""
import sys
import codecs
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib import colors
import re

# Force UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def escape_html(text):
    """Escape HTML special characters"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

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

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=24
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=10,
        spaceBefore=15,
        leading=20
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#424242'),
        spaceAfter=8,
        spaceBefore=10,
        leading=16
    )

    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#616161'),
        spaceAfter=6,
        spaceBefore=8,
        leading=14
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=7,
        fontName='Courier',
        leading=9,
        leftIndent=10,
        spaceAfter=4,
        spaceBefore=4
    )

    # Build PDF content
    story = []

    # Parse markdown content
    lines = content.split('\n')
    in_code_block = False
    code_buffer = []

    print(f"📄 Processing {len(lines)} lines...")

    for i, line in enumerate(lines):
        # Progress indicator every 500 lines
        if i % 500 == 0 and i > 0:
            print(f"   Progress: {i}/{len(lines)} lines ({i*100//len(lines)}%)")

        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End of code block - add as preformatted text
                if code_buffer:
                    code_text = '\n'.join(code_buffer)
                    # Use Preformatted for code blocks (safer)
                    story.append(Preformatted(code_text, code_style))
                    story.append(Spacer(1, 0.2*cm))
                code_buffer = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Skip empty lines
        if not line.strip():
            story.append(Spacer(1, 0.2*cm))
            continue

        try:
            # Handle headings
            if line.startswith('# '):
                text = escape_html(line[2:].strip())
                story.append(PageBreak())
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 0.5*cm))
            elif line.startswith('## '):
                text = escape_html(line[3:].strip())
                story.append(Paragraph(text, h1_style))
            elif line.startswith('### '):
                text = escape_html(line[4:].strip())
                story.append(Paragraph(text, h2_style))
            elif line.startswith('#### '):
                text = escape_html(line[5:].strip())
                story.append(Paragraph(text, h3_style))

            # Handle list items
            elif line.strip().startswith(('- ', '* ', '+ ')):
                text = escape_html(line.strip()[2:])
                story.append(Paragraph(f'• {text}', body_style))

            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line.strip()):
                text = escape_html(line.strip())
                story.append(Paragraph(text, body_style))

            # Regular paragraph
            else:
                if line.strip():
                    text = escape_html(line.strip())
                    story.append(Paragraph(text, body_style))

        except Exception as e:
            # Skip problematic lines
            print(f"   Warning: Skipped line {i}: {str(e)[:50]}")
            continue

    # Build PDF
    print(f"🔨 Building PDF with {len(story)} elements...")
    doc.build(story)

    # Check file size
    pdf_size = pdf_file.stat().st_size
    pdf_size_mb = pdf_size / (1024 * 1024)
    page_breaks = len([s for s in story if isinstance(s, PageBreak)])

    print(f"\n✅ PDF Created Successfully!")
    print(f"=" * 50)
    print(f"📁 File: {pdf_file.absolute()}")
    print(f"📊 Size: {pdf_size_mb:.2f} MB")
    print(f"📄 Estimated Pages: ~{page_breaks + 1}")
    print(f"📝 Elements: {len(story)}")
    print(f"=" * 50)

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
