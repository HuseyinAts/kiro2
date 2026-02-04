"""
BERT Plagiarism Model Setup
Downloads and configures multilingual BERT model for Turkish question plagiarism detection
"""
import os
import numpy as np
from typing import List, Dict
import json
from pathlib import Path

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print(
        "WARNING: sentence-transformers not installed. Install with: pip install sentence-transformers"
    )


class PlagiarismModelSetup:
    """Setup and manage BERT model for plagiarism detection"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize plagiarism model setup

        Args:
            model_name: Sentence-BERT model name (supports Turkish)
        """
        self.model_name = model_name
        self.model = None
        self.embeddings_dir = Path(__file__).parent / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)

    def download_model(self) -> bool:
        """Download BERT model (one-time setup)"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("❌ sentence-transformers not available")
            return False

        try:
            print(f"📥 Downloading model: {self.model_name}")
            print("   This may take a few minutes on first run...")

            self.model = SentenceTransformer(self.model_name)

            print(f"✅ Model downloaded successfully!")
            print(
                f"   Model dimension: {self.model.get_sentence_embedding_dimension()}"
            )
            return True

        except Exception as e:
            print(f"❌ Failed to download model: {str(e)}")
            return False

    def load_osym_questions_mock(self) -> List[Dict]:
        """
        Load OSYM questions (MOCK for security)
        In production, this would load from secure database
        """
        # MOCK data - In production, load from secure OSYM database
        mock_questions = [
            {
                "id": "osym_mat_001",
                "text": "Bir fonksiyonun türevi alınırken hangi kurallar uygulanır?",
                "konu": "Matematik",
                "alt_konu": "Türev",
            },
            {
                "id": "osym_fiz_001",
                "text": "Newton'un hareket yasaları nelerdir?",
                "konu": "Fizik",
                "alt_konu": "Hareket",
            },
            {
                "id": "osym_kim_001",
                "text": "Periyodik tabloda elementler nasıl sıralanır?",
                "konu": "Kimya",
                "alt_konu": "Periyodik Tablo",
            },
            # Add more OSYM questions here...
        ]

        print(f"📚 Loaded {len(mock_questions)} OSYM questions (MOCK)")
        print("   ⚠️  In production: Load from secure OSYM database")

        return mock_questions

    def generate_embeddings(self, questions: List[Dict]) -> np.ndarray:
        """
        Generate BERT embeddings for questions

        Args:
            questions: List of question dictionaries

        Returns:
            numpy array of embeddings (N x 384)
        """
        if self.model is None:
            if not self.download_model():
                raise RuntimeError("Failed to load BERT model")

        # Extract question texts
        texts = [q["text"] for q in questions]

        print(f"🧠 Generating embeddings for {len(texts)} questions...")

        # Generate embeddings (batched for efficiency)
        embeddings = self.model.encode(
            texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True
        )

        print(f"✅ Generated embeddings: shape {embeddings.shape}")

        return embeddings

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        questions: List[Dict],
        filename: str = "osym_embeddings.npy",
    ):
        """Save embeddings and metadata to disk"""
        embeddings_path = self.embeddings_dir / filename
        metadata_path = self.embeddings_dir / filename.replace(".npy", "_metadata.json")

        # Save embeddings
        np.save(embeddings_path, embeddings)
        print(f"💾 Saved embeddings to: {embeddings_path}")

        # Save metadata (question IDs, topics, etc.)
        metadata = {
            "question_ids": [q["id"] for q in questions],
            "konular": [q["konu"] for q in questions],
            "alt_konular": [q["alt_konu"] for q in questions],
            "model_name": self.model_name,
            "embedding_dim": embeddings.shape[1],
            "total_questions": len(questions),
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"📄 Saved metadata to: {metadata_path}")

    def load_embeddings(self, filename: str = "osym_embeddings.npy") -> tuple:
        """Load embeddings and metadata from disk"""
        embeddings_path = self.embeddings_dir / filename
        metadata_path = self.embeddings_dir / filename.replace(".npy", "_metadata.json")

        if not embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {embeddings_path}")

        # Load embeddings
        embeddings = np.load(embeddings_path)
        print(f"📂 Loaded embeddings: shape {embeddings.shape}")

        # Load metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        print(f"📄 Loaded metadata: {metadata['total_questions']} questions")

        return embeddings, metadata

    def test_model_performance(self) -> Dict:
        """Test model inference speed and quality"""
        if self.model is None:
            if not self.download_model():
                return {"error": "Failed to load model"}

        # Test questions
        test_texts = [
            "Bir fonksiyonun türevi nasıl alınır?",
            "Newton'un ikinci yasası nedir?",
            "Periyodik tabloda elementler nasıl gruplanır?",
        ]

        print("\n🧪 Testing model performance...")

        import time

        # Test inference speed
        start_time = time.time()
        embeddings = self.model.encode(test_texts)
        elapsed = time.time() - start_time

        avg_time_ms = (elapsed / len(test_texts)) * 1000

        results = {
            "model_name": self.model_name,
            "embedding_dim": embeddings.shape[1],
            "test_questions": len(test_texts),
            "total_time_ms": round(elapsed * 1000, 2),
            "avg_time_per_question_ms": round(avg_time_ms, 2),
            "performance": "✅ PASS"
            if avg_time_ms < 100
            else "⚠️  SLOW (target: <100ms)",
        }

        print(f"\n📊 Performance Results:")
        for key, value in results.items():
            print(f"   {key}: {value}")

        return results

    def setup_complete_pipeline(self):
        """Complete setup: download model, generate embeddings, save"""
        print("=" * 80)
        print("BERT PLAGIARISM MODEL SETUP - COMPLETE PIPELINE")
        print("=" * 80)
        print()

        # Step 1: Download model
        print("STEP 1: Download BERT Model")
        print("-" * 80)
        if not self.download_model():
            return False
        print()

        # Step 2: Test performance
        print("STEP 2: Test Model Performance")
        print("-" * 80)
        self.test_model_performance()
        print()

        # Step 3: Load OSYM questions
        print("STEP 3: Load OSYM Questions")
        print("-" * 80)
        osym_questions = self.load_osym_questions_mock()
        print()

        # Step 4: Generate embeddings
        print("STEP 4: Generate Embeddings")
        print("-" * 80)
        embeddings = self.generate_embeddings(osym_questions)
        print()

        # Step 5: Save embeddings
        print("STEP 5: Save Embeddings")
        print("-" * 80)
        self.save_embeddings(embeddings, osym_questions)
        print()

        print("=" * 80)
        print("✅ SETUP COMPLETE!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Update PlagiarismDetectionService to use these embeddings")
        print("2. Add real OSYM questions to secure database")
        print("3. Re-run embedding generation with full dataset")
        print()

        return True


def main():
    """Main entry point"""
    setup = PlagiarismModelSetup()

    # Run complete setup pipeline
    success = setup.setup_complete_pipeline()

    if success:
        print("🚀 Plagiarism detection model is ready!")
    else:
        print("❌ Setup failed. Check errors above.")
        print()
        print("Common issues:")
        print(
            "- sentence-transformers not installed: pip install sentence-transformers"
        )
        print("- No internet connection (model download requires internet)")
        print("- Insufficient disk space (~500MB needed)")


if __name__ == "__main__":
    main()
