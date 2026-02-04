"""
ÖSYM Question Extractor
Extracts questions from ÖSYM PDF files and structures them for database import
"""
import pdfplumber
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime


class OSYMQuestionExtractor:
    """Extract and structure questions from ÖSYM PDF files"""

    # Subject mappings
    SUBJECT_KEYWORDS = {
        "TÜRKÇE": "Türkçe",
        "MATEMATİK": "Matematik",
        "FEN BİLİMLERİ": "Fen Bilimleri",
        "SOSYAL BİLİMLER": "Sosyal Bilimler",
        "FİZİK": "Fizik",
        "KİMYA": "Kimya",
        "BİYOLOJİ": "Biyoloji",
        "TARİH": "Tarih",
        "COĞRAFYA": "Coğrafya",
        "FELSEFE": "Felsefe",
        "DİN KÜLTÜRÜ": "Din Kültürü",
        "İNGİLİZCE": "İngilizce",
        "ALMANCA": "Almanca",
        "FRANSIZCA": "Fransızca",
    }

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.questions = []
        self.answer_key = {}
        self.metadata = {
            "file": str(self.pdf_path.name),
            "extraction_date": datetime.now().isoformat(),
            "total_questions": 0,
        }

    def extract_exam_info(self, text: str) -> Dict[str, str]:
        """Extract exam type and year from PDF"""
        info = {"exam_type": "TYT", "year": None}  # Default

        # Extract year
        year_match = re.search(r"20\d{2}", text)
        if year_match:
            info["year"] = int(year_match.group())

        # Extract exam type
        if "TYT" in text or "TEMEL YETERLİLİK" in text:
            info["exam_type"] = "TYT"
        elif "AYT" in text or "ALAN YETERLİLİK" in text:
            info["exam_type"] = "AYT"

        return info

    def extract_current_subject(self, text: str) -> Optional[str]:
        """Detect current subject from page header"""
        for keyword, subject in self.SUBJECT_KEYWORDS.items():
            if keyword in text.upper():
                return subject
        return None

    def extract_questions_from_page(
        self, page_text: str, current_subject: str
    ) -> List[Dict]:
        """Extract questions from a single page"""
        questions = []

        # Split by question numbers (1., 2., 3., etc.)
        question_pattern = r"(\d+)\.\s+(.*?)(?=\n\d+\.\s+|\Z)"
        matches = re.finditer(question_pattern, page_text, re.DOTALL)

        for match in matches:
            question_num = int(match.group(1))
            question_block = match.group(2).strip()

            # Extract options
            options_dict = self.extract_options(question_block)

            if not options_dict:
                # No options found, might be a multi-part question
                continue

            # Extract question stem (text before options)
            stem = self.extract_stem(question_block, options_dict)

            question = {
                "question_number": question_num,
                "subject": current_subject,
                "stem": stem.strip(),
                "options": options_dict,
                "correct_answer": None,  # Will be filled from answer key
                "source": "ÖSYM",
                "exam_type": self.metadata.get("exam_type", "TYT"),
                "year": self.metadata.get("year"),
            }

            questions.append(question)

        return questions

    def extract_options(self, question_block: str) -> Dict[str, str]:
        """Extract A), B), C), D), E) options"""
        options = {}

        # Pattern: A) text B) text C) text...
        option_pattern = r"([A-E])\)\s*(.*?)(?=[A-E]\)|\Z)"
        matches = re.finditer(option_pattern, question_block, re.DOTALL)

        for match in matches:
            letter = match.group(1)
            text = match.group(2).strip()

            # Clean up: remove extra whitespace
            text = re.sub(r"\s+", " ", text)

            if text:  # Only add if not empty
                options[letter] = text

        return (
            options if len(options) >= 4 else {}
        )  # Valid question has at least 4 options

    def extract_stem(self, question_block: str, options: Dict[str, str]) -> str:
        """Extract question stem (text before options)"""

        # Find first option position
        first_option = None
        for letter in ["A", "B", "C", "D", "E"]:
            pattern = f"{letter}\\)"
            match = re.search(pattern, question_block)
            if match:
                first_option = match.start()
                break

        if first_option:
            stem = question_block[:first_option]
        else:
            stem = question_block

        return stem.strip()

    def extract_answer_key(self, pdf) -> Dict[int, str]:
        """
        Extract answer key from PDF (Wave 2A improvement)

        Uses improved multi-strategy extraction:
        - Strategy 1: Table format with section headers (most common 2018-2024)
        - Strategy 2: Simple sequential format (2010-2015)
        - Strategy 3: Section-based format with subject names
        - Strategy 4: Multi-column dense format
        - Strategy 5: Fallback pattern

        Expected improvement: 14% -> 80%+ success rate
        """
        from improved_answer_key_extractor import ImprovedAnswerKeyExtractor

        # Use improved extractor
        extractor = ImprovedAnswerKeyExtractor(debug=False)
        answer_key = extractor.extract_from_pdf(pdf, pages_to_check=10)

        return answer_key

    def extract_all_questions(self) -> List[Dict]:
        """Main extraction method"""

        print(f"\n{'='*80}")
        print(f"Extracting questions from: {self.pdf_path.name}")
        print(f"{'='*80}\n")

        with pdfplumber.open(self.pdf_path) as pdf:
            # Extract exam info from first page
            first_page_text = pdf.pages[0].extract_text()
            exam_info = self.extract_exam_info(first_page_text)
            self.metadata.update(exam_info)

            print(f"Exam Type: {exam_info['exam_type']}")
            print(f"Year: {exam_info['year']}")

            # Extract answer key first
            self.answer_key = self.extract_answer_key(pdf)
            print(f"\nAnswer key extracted: {len(self.answer_key)} answers")

            # Extract questions from all pages
            current_subject = None

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()

                if not page_text:
                    continue

                # Update current subject if new section starts
                detected_subject = self.extract_current_subject(page_text)
                if detected_subject:
                    current_subject = detected_subject
                    print(f"\nPage {i+1}: Subject detected - {current_subject}")

                # Extract questions from this page
                if current_subject:
                    page_questions = self.extract_questions_from_page(
                        page_text, current_subject
                    )

                    # Add correct answers from answer key
                    for q in page_questions:
                        q_num = q["question_number"]
                        if q_num in self.answer_key:
                            q["correct_answer"] = self.answer_key[q_num]

                    self.questions.extend(page_questions)

        self.metadata["total_questions"] = len(self.questions)

        print(f"\n{'='*80}")
        print(f"Extraction complete!")
        print(f"Total questions extracted: {len(self.questions)}")
        print(
            f"Questions with answers: {sum(1 for q in self.questions if q['correct_answer'])}"
        )
        print(f"{'='*80}\n")

        return self.questions

    def save_to_json(self, output_path: str):
        """Save extracted questions to JSON"""
        output = {"metadata": self.metadata, "questions": self.questions}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Questions saved to: {output_path}")

    def get_database_format(self) -> List[Dict]:
        """Convert to database-ready format"""
        db_questions = []

        for q in self.questions:
            # Map difficulty based on question stats (will be updated later)
            # For now, use ÖSYM standard distribution
            difficulty = "orta"  # Default

            db_question = {
                "subject": q["subject"],
                "topic": q["subject"],  # Will be refined with NLP
                "subtopic": None,
                "difficulty": difficulty,
                "exam_type": q["exam_type"],
                "stem": q["stem"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": None,  # ÖSYM doesn't provide explanations
                "bloom_level": None,  # Will be classified with NLP
                "source": "ÖSYM",
                "year": q["year"],
                "status": "active",
                "quality_score": 10.0,  # ÖSYM questions are gold standard
            }

            db_questions.append(db_question)

        return db_questions


def main():
    """Test extraction on 2024 TYT"""

    # Test with 2024 TYT
    pdf_path = "C:/Users/husey/kiro2/osym/tyt/yks_tyt_2024_kitapcik_T24kt.pdf"

    extractor = OSYMQuestionExtractor(pdf_path)
    questions = extractor.extract_all_questions()

    # Save raw extraction
    extractor.save_to_json("C:/Users/husey/kiro2/backend/osym_tyt_2024_extracted.json")

    # Show sample questions
    print("\n" + "=" * 80)
    print("SAMPLE QUESTIONS")
    print("=" * 80 + "\n")

    for q in questions[:3]:  # First 3 questions
        print(f"\nQuestion {q['question_number']} ({q['subject']})")
        print(f"Stem: {q['stem'][:150]}...")
        print(f"Options: {list(q['options'].keys())}")
        print(f"Correct Answer: {q['correct_answer']}")

    # Get database format
    db_format = extractor.get_database_format()
    print(f"\n\nDatabase-ready format: {len(db_format)} questions")


if __name__ == "__main__":
    main()
