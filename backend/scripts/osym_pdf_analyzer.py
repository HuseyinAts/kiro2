"""
ÖSYM PDF Analyzer
Analyzes PDF structure to understand question format
"""
import json
import re
from pathlib import Path
from typing import Any

import pdfplumber


def analyze_pdf_structure(pdf_path: str) -> dict[str, Any]:
    """Analyze the structure of an ÖSYM PDF"""

    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path}")
    print(f"{'='*80}\n")

    analysis = {
        "file": pdf_path,
        "total_pages": 0,
        "page_samples": [],
        "detected_patterns": {"questions": [], "options": [], "subjects": []},
    }

    with pdfplumber.open(pdf_path) as pdf:
        analysis["total_pages"] = len(pdf.pages)
        print(f"Total pages: {len(pdf.pages)}")

        # Analyze first 5 pages in detail
        for i, page in enumerate(pdf.pages[:5]):
            print(f"\n--- Page {i+1} ---")
            text = page.extract_text()

            if text:
                # Sample first 500 characters
                sample = text[:500]
                analysis["page_samples"].append(
                    {"page_num": i + 1, "sample_text": sample}
                )

                print(f"Sample text:\n{sample}\n")

                # Detect question patterns
                question_patterns = re.findall(r"^\d+\.\s+", text, re.MULTILINE)
                if question_patterns:
                    print(f"Found {len(question_patterns)} question markers")
                    analysis["detected_patterns"]["questions"].extend(
                        question_patterns[:3]
                    )

                # Detect option patterns (A), B), C), D), E)
                option_patterns = re.findall(r"[A-E]\)", text)
                if option_patterns:
                    print(
                        f"Found {len(option_patterns)} option markers: {set(option_patterns)}"
                    )
                    analysis["detected_patterns"]["options"] = list(
                        set(option_patterns)
                    )

                # Detect subject headers (TÜRKÇE, MATEMATİK, etc.)
                subjects = re.findall(
                    r"(TÜRKÇE|MATEMATİK|FEN BİLİMLERİ|SOSYAL BİLİMLER|FIZIK|KIMYA|BIYOLOJI|TARIH|COĞRAFYA|FELSEFE)",
                    text,
                )
                if subjects:
                    print(f"Found subjects: {set(subjects)}")
                    analysis["detected_patterns"]["subjects"].extend(
                        list(set(subjects))
                    )

    return analysis


def quick_extraction_test(pdf_path: str, page_num: int = 5):
    """Quick test to extract text from a specific page"""

    print(f"\n{'='*80}")
    print(f"Quick Extraction Test - Page {page_num}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        if page_num <= len(pdf.pages):
            page = pdf.pages[page_num - 1]
            text = page.extract_text()

            # Try to extract tables (for answer grids)
            tables = page.extract_tables()

            print("Text Content:")
            print(text)

            if tables:
                print(f"\n\nFound {len(tables)} tables:")
                for i, table in enumerate(tables):
                    print(f"\nTable {i+1}:")
                    for row in table[:5]:  # First 5 rows
                        print(row)


if __name__ == "__main__":
    # Test with 2024 TYT
    tyt_2024_path = Path(
        "C:/Users/husey/kiro2/osym/tyt/yks_tyt_2024_kitapcik_T24kt.pdf"
    )

    if tyt_2024_path.exists():
        print("=" * 80)
        print("ÖSYM PDF ANALYSIS")
        print("=" * 80)

        # Structural analysis
        analysis = analyze_pdf_structure(str(tyt_2024_path))

        # Save analysis to JSON
        output_path = Path("C:/Users/husey/kiro2/backend/osym_pdf_analysis.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"\n\nAnalysis saved to: {output_path}")

        # Quick extraction test on a sample page
        quick_extraction_test(str(tyt_2024_path), page_num=5)

    else:
        print(f"Error: PDF not found at {tyt_2024_path}")
