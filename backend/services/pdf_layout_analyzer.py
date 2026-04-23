"""
PDF Layout Analysis Service
Advanced layout detection and structure preservation for ÖSYM PDFs
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    import pdfplumber
    import pytesseract
    from pdf2image import convert_from_path
    PDF_LIBS_AVAILABLE = True
except ImportError:
    PDF_LIBS_AVAILABLE = False
    logger.warning("PDF processing libraries not available. Install: pdfplumber, pytesseract, pdf2image, opencv-python")


class PDFLayoutAnalyzer:
    """
    Advanced PDF layout analysis for ÖSYM questions

    Features:
    - Question boundary detection
    - Visual element extraction (tables, graphs)
    - OCR for scanned PDFs
    - Metadata extraction
    """

    def __init__(self, enable_ocr: bool = True):
        self.enable_ocr = enable_ocr and PDF_LIBS_AVAILABLE

        # ÖSYM question patterns
        self.question_patterns = [
            r'(\d+)\.\s*(.+?)(?=\d+\.\s|$)',  # 1. Question text...
            r'Soru\s*(\d+)[:\.]?\s*(.+)',      # Soru 1: Question text
        ]

        # Option patterns (A-E)
        self.option_pattern = r'([A-E])\)\s*(.+?)(?=[A-E]\)|$)'

    def analyze_pdf_layout(self, pdf_path: str) -> dict[str, Any]:
        """
        Analyze PDF layout and extract structure

        Args:
            pdf_path: Path to PDF file

        Returns:
            Layout analysis results
        """
        if not PDF_LIBS_AVAILABLE:
            raise RuntimeError("PDF libraries not installed")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = []

                for i, page in enumerate(pdf.pages):
                    page_analysis = {
                        'page_number': i + 1,
                        'text': page.extract_text() or "",
                        'tables': self._extract_tables(page),
                        'images': self._detect_images(page),
                        'layout': self._analyze_page_layout(page)
                    }

                    # OCR if text extraction failed
                    if not page_analysis['text'].strip() and self.enable_ocr:
                        page_analysis['text'] = self._ocr_page(pdf_path, i)
                        page_analysis['ocr_used'] = True

                    pages.append(page_analysis)

                return {
                    'total_pages': len(pages),
                    'pages': pages,
                    'questions': self._extract_questions_from_pages(pages)
                }

        except Exception as e:
            logger.error(f"PDF layout analysis failed: {e}")
            raise

    def _extract_tables(self, page) -> list[dict[str, Any]]:
        """Extract tables from page"""
        tables = []

        try:
            page_tables = page.extract_tables()

            for idx, table in enumerate(page_tables):
                if table:
                    tables.append({
                        'index': idx,
                        'rows': len(table),
                        'cols': len(table[0]) if table else 0,
                        'data': table,
                        'bbox': None  # Could extract bounding box
                    })
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")

        return tables

    def _detect_images(self, page) -> list[dict[str, Any]]:
        """Detect images/figures in page"""
        images = []

        try:
            # Get page images
            page_images = page.images

            for idx, img in enumerate(page_images):
                images.append({
                    'index': idx,
                    'x0': img.get('x0', 0),
                    'y0': img.get('y0', 0),
                    'x1': img.get('x1', 0),
                    'y1': img.get('y1', 0),
                    'width': img.get('width', 0),
                    'height': img.get('height', 0)
                })
        except Exception as e:
            logger.warning(f"Image detection failed: {e}")

        return images

    def _analyze_page_layout(self, page) -> dict[str, Any]:
        """Analyze page layout structure"""
        return {
            'width': page.width,
            'height': page.height,
            'rotation': page.rotation or 0,
            'has_multiple_columns': self._detect_columns(page),
            'header_region': self._detect_header(page),
            'footer_region': self._detect_footer(page)
        }

    def _detect_columns(self, page) -> bool:
        """Detect if page has multiple columns"""
        # Simplified - check text distribution
        text = page.extract_text() or ""
        lines = text.split('\n')

        # If lines are consistently short, might be multi-column
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        return avg_line_length < 40

    def _detect_header(self, page) -> dict[str, float] | None:
        """Detect header region"""
        # Top 10% of page
        return {
            'y0': 0,
            'y1': page.height * 0.1,
            'x0': 0,
            'x1': page.width
        }

    def _detect_footer(self, page) -> dict[str, float] | None:
        """Detect footer region"""
        # Bottom 10% of page
        return {
            'y0': page.height * 0.9,
            'y1': page.height,
            'x0': 0,
            'x1': page.width
        }

    def _ocr_page(self, pdf_path: str, page_number: int) -> str:
        """Perform OCR on scanned page"""
        try:
            # Convert PDF page to image
            images = convert_from_path(
                pdf_path,
                first_page=page_number + 1,
                last_page=page_number + 1,
                dpi=300
            )

            if not images:
                return ""

            # Preprocess image
            img_array = np.array(images[0])
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # OCR
            text = pytesseract.image_to_string(enhanced, lang='tur')

            return text

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def _extract_questions_from_pages(self, pages: list[dict]) -> list[dict[str, Any]]:
        """Extract questions from analyzed pages"""
        questions = []

        for page in pages:
            text = page['text']

            # Find question boundaries
            for pattern in self.question_patterns:
                matches = re.finditer(pattern, text, re.DOTALL)

                for match in matches:
                    q_num = match.group(1)
                    q_text = match.group(2).strip()

                    # Extract options
                    options = self._extract_options(q_text)

                    questions.append({
                        'page': page['page_number'],
                        'question_number': int(q_num) if q_num.isdigit() else None,
                        'question_text': q_text,
                        'options': options,
                        'has_table': len(page['tables']) > 0,
                        'has_image': len(page['images']) > 0
                    })

        return questions

    def _extract_options(self, text: str) -> dict[str, str]:
        """Extract answer options A-E"""
        options = {}

        matches = re.finditer(self.option_pattern, text, re.DOTALL)

        for match in matches:
            option_letter = match.group(1)
            option_text = match.group(2).strip()
            options[option_letter] = option_text

        return options

    def extract_metadata(self, pdf_path: str) -> dict[str, Any]:
        """Extract PDF metadata (exam type, year, etc.)"""
        metadata = {
            'exam_type': None,
            'year': None,
            'section': None,
            'subject': None
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text() or ""

                    # Extract year
                    year_match = re.search(r'20\d{2}', first_page_text)
                    if year_match:
                        metadata['year'] = int(year_match.group())

                    # Extract exam type
                    if 'TYT' in first_page_text:
                        metadata['exam_type'] = 'TYT'
                    elif 'AYT' in first_page_text:
                        metadata['exam_type'] = 'AYT'
                    elif 'YDT' in first_page_text:
                        metadata['exam_type'] = 'YDT'

                    # Extract subject
                    subjects = ['Matematik', 'Fizik', 'Kimya', 'Biyoloji', 'Türkçe', 'Tarih', 'Coğrafya']
                    for subject in subjects:
                        if subject in first_page_text:
                            metadata['subject'] = subject
                            break

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")

        return metadata

    def calculate_confidence_score(self, extracted_question: dict[str, Any]) -> float:
        """
        Calculate confidence score for extracted question

        Returns:
            Confidence score 0.0-1.0
        """
        score = 0.0

        # Has question text
        if extracted_question.get('question_text'):
            score += 0.3

        # Has correct number of options (5 for ÖSYM)
        options = extracted_question.get('options', {})
        if len(options) == 5:
            score += 0.3
        elif len(options) >= 3:
            score += 0.15

        # Question number is valid
        if extracted_question.get('question_number') is not None:
            score += 0.2

        # Text quality (length check)
        q_text = extracted_question.get('question_text', '')
        if len(q_text) > 50:
            score += 0.2

        return min(score, 1.0)
