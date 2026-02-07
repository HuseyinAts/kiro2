"""
Batch Import ÖSYM PDFs
Process all TYT and AYT PDFs and import to database
"""
import asyncio
from pathlib import Path
import sys
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.osym_question_extractor import OSYMQuestionExtractor
from scripts.import_osym_to_db import OSYMDatabaseImporter


class BatchOSYMImporter:
    """Batch process and import ÖSYM PDFs"""

    def __init__(self, osym_dir: str):
        self.osym_dir = Path(osym_dir)
        self.tyt_dir = self.osym_dir / "tyt"
        self.ayt_dir = self.osym_dir / "ayt"
        self.output_dir = Path("C:/Users/husey/kiro2/backend/osym_extracted")
        self.output_dir.mkdir(exist_ok=True)

        self.total_pdfs = 0
        self.successful_extractions = 0
        self.failed_extractions = 0
        self.total_questions = 0

    def get_all_pdfs(self) -> List[Path]:
        """Get all PDF files from TYT and AYT directories"""
        pdfs = []

        # TYT PDFs
        if self.tyt_dir.exists():
            tyt_pdfs = list(self.tyt_dir.glob("*.pdf"))
            print(f"Found {len(tyt_pdfs)} TYT PDFs")
            pdfs.extend(tyt_pdfs)

        # AYT PDFs
        if self.ayt_dir.exists():
            ayt_pdfs = list(self.ayt_dir.glob("*.pdf"))
            print(f"Found {len(ayt_pdfs)} AYT PDFs")
            pdfs.extend(ayt_pdfs)

        self.total_pdfs = len(pdfs)
        return pdfs

    def extract_pdf(self, pdf_path: Path) -> str:
        """Extract questions from a single PDF"""

        print(f"\n{'='*80}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*80}")

        try:
            extractor = OSYMQuestionExtractor(str(pdf_path))
            questions = extractor.extract_all_questions()

            if questions:
                # Save to JSON
                output_file = self.output_dir / f"{pdf_path.stem}_extracted.json"
                extractor.save_to_json(str(output_file))

                self.successful_extractions += 1
                self.total_questions += len(questions)

                print(f"[OK] Extracted {len(questions)} questions")
                return str(output_file)
            else:
                print("[WARN] No questions extracted")
                self.failed_extractions += 1
                return None

        except Exception as e:
            print(f"[ERROR] Failed to extract: {e}")
            self.failed_extractions += 1
            return None

    async def import_all_extractions(self):
        """Import all extracted JSON files to database"""

        print(f"\n{'='*80}")
        print("Importing Extracted Questions to Database")
        print(f"{'='*80}\n")

        importer = OSYMDatabaseImporter()
        await importer.connect()

        # Get all JSON files
        json_files = list(self.output_dir.glob("*_extracted.json"))
        print(f"Found {len(json_files)} extraction files\n")

        for json_file in json_files:
            print(f"\nImporting: {json_file.name}")
            try:
                await importer.import_from_json(str(json_file))
            except Exception as e:
                print(f"[ERROR] Import failed: {e}")

        # Show statistics
        await importer.get_statistics()
        await importer.close()

    async def run(self):
        """Main batch processing"""

        print("\n" + "=" * 80)
        print("ÖSYM BATCH PDF IMPORTER")
        print("=" * 80 + "\n")

        # Step 1: Extract all PDFs
        print("Step 1: Extracting questions from PDFs...")
        print("-" * 80)

        pdfs = self.get_all_pdfs()

        if not pdfs:
            print("[ERROR] No PDF files found!")
            return

        # Extract each PDF
        for i, pdf in enumerate(pdfs, 1):
            print(f"\nProcessing [{i}/{self.total_pdfs}]")
            self.extract_pdf(pdf)

        # Summary
        print(f"\n{'='*80}")
        print("Extraction Summary")
        print(f"{'='*80}")
        print(f"Total PDFs processed: {self.total_pdfs}")
        print(f"[OK] Successful: {self.successful_extractions}")
        print(f"[ERROR] Failed: {self.failed_extractions}")
        print(f"Total questions extracted: {self.total_questions}")
        print(f"{'='*80}\n")

        # Step 2: Import to database
        print("\nStep 2: Importing to database...")
        print("-" * 80)

        await self.import_all_extractions()

        print(f"\n{'='*80}")
        print("BATCH IMPORT COMPLETE!")
        print(f"{'='*80}\n")


async def main():
    """Main entry point"""

    osym_dir = "C:/Users/husey/kiro2/osym"

    if not Path(osym_dir).exists():
        print(f"[ERROR] ÖSYM directory not found: {osym_dir}")
        return

    batch_importer = BatchOSYMImporter(osym_dir)
    await batch_importer.run()


if __name__ == "__main__":
    asyncio.run(main())
