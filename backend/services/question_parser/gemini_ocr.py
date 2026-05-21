import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import cv2
import google.generativeai as genai
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR sonucu için veri sınıfı"""
    text: str
    confidence: float
    metadata: dict[str, Any]

@dataclass
class QuestionData:
    """Soru verisi için yapılandırılmış sınıf"""
    question_number: int
    question_text: str
    options: dict[str, str]  # A, B, C, D, E
    subject: str
    topic: str
    test_id: str
    page_number: int
    correct_answer: str | None = None

class GeminiOCRService:
    """
    Tezdeki yaklaşımı takip eden Gemini tabanlı OCR servisi
    Gemini 3 Pro ile gelişmiş OCR
    """

    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: Gemini API anahtarı
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found - OCR service will be disabled")
            self.model = None
            return

        # Gemini'yi yapılandır
        genai.configure(api_key=self.api_key)

        # Gemini 1.5 Pro kullanıyoruz (daha güçlü OCR için)
        try:
            self.model = genai.GenerativeModel(
                'gemini-1.5-pro',
                generation_config={
                    'temperature': 0.1,  # OCR için düşük temperature
                    'top_p': 0.95,
                    'max_output_tokens': 8192,
                }
            )
            logger.info("Gemini OCR service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}", exc_info=True)
            self.model = None

        # Tezdeki prompt stratejisi
        self.system_prompt = """
        Sen bir YKS test kitabı OCR uzmanısın.

        Görevin:
        1. Soru metnini eksiksiz oku
        2. Şekil, grafik, tablo açıklamalarını belirt
        3. Matematiksel ifadeleri LaTeX formatında yaz
        4. Seçenekleri (A, B, C, D, E) düzgün ayır

        Format:
        - Soru numarası
        - Konu başlığı
        - Test ID
        - Soru metni
        - Seçenekler

        DİKKAT: Cevap anahtarını asla tahmin etme, sadece metni oku.
        """

    def image_to_base64(self, image: np.ndarray) -> str:
        """Görüntüyü base64'e çevir"""
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')

    async def extract_question(self, image: np.ndarray) -> dict | None:
        """
        Soru görüntüsünden yapılandırılmış veri çıkar

        Args:
            image: Soru görüntüsü (cropped)

        Returns:
            Yapılandırılmış soru verisi
        """
        if self.model is None:
            logger.warning("OCR service not available")
            return None

        prompt = """
        Bu görüntüde bir YKS/TYT/AYT sorusu var. Lütfen aşağıdaki bilgileri çıkar ve JSON formatında döndür:

        1. Soru numarası (question_number)
        2. Soru metni (question_text) - LaTeX formülleri varsa koruyarak
        3. Seçenekler (options) - A, B, C, D, E şıkları
        4. Varsa görsel/diyagram açıklaması (visual_description)

        JSON formatı:
        {
            "question_number": 1,
            "question_text": "Soru metni...",
            "options": {
                "A": "Seçenek A",
                "B": "Seçenek B",
                "C": "Seçenek C",
                "D": "Seçenek D",
                "E": "Seçenek E"
            },
            "visual_description": "Varsa görsel açıklaması..."
        }

        Sadece JSON döndür, başka açıklama yapma.
        """

        try:
            # Görüntüyü Gemini'ye gönder
            image_bytes = cv2.imencode('.png', image)[1].tobytes()
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, {'mime_type': 'image/png', 'data': image_bytes}]
            )

            # JSON'u parse et
            json_str = response.text.strip()
            # JSON bloğunu temizle
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]

            data = json.loads(json_str.strip())

            return data

        except Exception as e:
            logger.error(f"OCR hatası: {e}", exc_info=True)
            return None

    async def extract_metadata(self, image: np.ndarray, metadata_type: str) -> str:
        """
        Metadata görüntüsünden bilgi çıkar (konu, test_id, vb.)

        Args:
            image: Metadata görüntüsü
            metadata_type: 'topic', 'subject', 'test_id', 'page_number'

        Returns:
            Çıkarılan metin
        """
        if self.model is None:
            return ""

        prompts = {
            'topic': "Bu görüntüde bir konu başlığı var. Sadece konu adını döndür.",
            'subject': "Bu görüntüde bir ders adı var. Sadece ders adını döndür (Matematik, Fizik, Kimya, vb.).",
            'test_identifier': "Bu görüntüde bir test numarası/kodu var. Sadece test kodunu döndür.",
            'page_number': "Bu görüntüde bir sayfa numarası var. Sadece sayıyı döndür."
        }

        prompt = prompts.get(metadata_type, "Bu görüntüdeki metni oku ve döndür.")

        try:
            image_bytes = cv2.imencode('.png', image)[1].tobytes()
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, {'mime_type': 'image/png', 'data': image_bytes}]
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Metadata OCR hatası: {e}", exc_info=True)
            return ""

    async def batch_process(self, images: list[np.ndarray], types: list[str]) -> list[Any]:
        """
        Birden fazla görüntüyü paralel işle

        Args:
            images: Görüntü listesi
            types: Her görüntünün tipi ('question', 'topic', vb.)

        Returns:
            OCR sonuçları
        """
        tasks = []

        for image, img_type in zip(images, types):
            if img_type == 'question':
                task = self.extract_question(image)
            else:
                task = self.extract_metadata(image, img_type)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    async def batch_ocr_with_retry(
        self,
        images: list[np.ndarray],
        max_retries: int = 3
    ) -> list[dict]:
        """Batch OCR with retry mechanism"""

        results = []
        semaphore = asyncio.Semaphore(5)  # 5 concurrent requests

        async def process_single(img, idx):
            async with semaphore:
                for attempt in range(max_retries):
                    try:
                        result = await self._ocr_single_image(img, idx)
                        return result
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"OCR failed for image {idx}: {e}", exc_info=True)
                            return None
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff

        tasks = [process_single(img, i) for i, img in enumerate(images)]
        results = await asyncio.gather(*tasks)

        return [r for r in results if r is not None]

    async def _ocr_single_image(self, image: np.ndarray, idx: int) -> dict:
        """Tek görüntü için OCR"""

        # NumPy array'i PIL Image'e çevir
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Gemini'ye gönder
        prompt = f"{self.system_prompt}\n\nGörüntüyü oku ve yapılandırılmış çıktı ver:"

        response = await asyncio.to_thread(
            self.model.generate_content,
            [prompt, pil_image]
        )

        # Yanıtı parse et
        return self._parse_ocr_response(response.text, idx)

    def _parse_ocr_response(self, text: str, idx: int) -> dict:
        """OCR yanıtını yapılandırılmış formata çevir"""

        # Tezdeki veri yapısı
        result = {
            'index': idx,
            'question_number': None,
            'subject': None,
            'topic': None,
            'test_id': None,
            'question_text': '',
            'options': {},
            'has_image': False,
            'has_equation': False
        }

        # Parse logic
        lines = text.strip().split('\n')

        for line in lines:
            if line.startswith('Soru Numarası:'):
                result['question_number'] = line.split(':')[1].strip()
            elif line.startswith('Konu:'):
                result['topic'] = line.split(':')[1].strip()
            elif line.startswith('Ders:'):
                result['subject'] = line.split(':')[1].strip()
            elif line.startswith('Test ID:'):
                result['test_id'] = line.split(':')[1].strip()
            elif line.startswith('A)') or line.startswith('B)') or \
                 line.startswith('C)') or line.startswith('D)') or \
                 line.startswith('E)'):
                option = line[0]
                result['options'][option] = line[2:].strip()
            # Soru metni
            elif not any(line.startswith(x) for x in ['Soru', 'Konu:', 'Ders:', 'Test']):
                result['question_text'] += line + ' '

        # LaTeX ve görsel tespiti
        result['has_equation'] = '\\' in result['question_text'] or '$' in result['question_text']
        result['has_image'] = '[Şekil]' in result['question_text'] or '[Grafik]' in result['question_text']

        return result
