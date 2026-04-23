#!/usr/bin/env python3
"""
Google Gemini MCP Server
Model Context Protocol sunucusu - Gemini 3 Pro entegrasyonu
Eğitim içeriği üretimi ve soru analizi için optimize edilmiş
"""

import asyncio
import json
import os
from typing import Any

import google.generativeai as genai
from fastmcp import FastMCP

# MCP sunucusunu başlat
mcp = FastMCP("Gemini Education")

# Gemini API yapılandırması
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable bulunamadı")

genai.configure(api_key=GOOGLE_API_KEY)

# Model seçimi (Gemini 2.0 Flash veya mevcut en iyi model)
try:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
except Exception:
    model = genai.GenerativeModel("gemini-1.5-pro")


@mcp.tool()
async def generate_educational_content(
    subject: str,
    topic: str,
    difficulty: str = "orta",
    content_type: str = "açıklama"
) -> str:
    """
    Belirli bir konu için eğitim içeriği üretir.
    
    Args:
        subject: Ders adı (Matematik, Türkçe, Fen Bilimleri, vb.)
        topic: Konu başlığı
        difficulty: Zorluk seviyesi (kolay, orta, zor)
        content_type: İçerik tipi (açıklama, örnek, alıştırma)
    
    Returns:
        Üretilen eğitim içeriği
    
    Example:
        >>> generate_educational_content("Matematik", "Üçgenler", "orta", "açıklama")
        "Üçgenler, üç kenarı ve üç köşesi olan geometrik şekillerdir..."
    """
    prompt = f"""
    Türk Milli Eğitim Bakanlığı müfredatına uygun olarak aşağıdaki konuda eğitim içeriği hazırla:
    
    Ders: {subject}
    Konu: {topic}
    Zorluk Seviyesi: {difficulty}
    İçerik Tipi: {content_type}
    
    İçerik öğrenci dostu, anlaşılır ve öğretici olmalıdır.
    Türkçe dilbilgisi kurallarına dikkat et.
    """

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        return f"Hata: {e!s}"


@mcp.tool()
async def analyze_student_answer(
    question: str,
    student_answer: str,
    correct_answer: str,
    subject: str
) -> dict[str, Any]:
    """
    Öğrenci cevabını analiz eder ve geri bildirim sağlar.
    
    Args:
        question: Soru metni
        student_answer: Öğrencinin verdiği cevap
        correct_answer: Doğru cevap
        subject: Ders adı
    
    Returns:
        Analiz sonucu (doğruluk, açıklama, öneriler)
    
    Example:
        >>> analyze_student_answer("2+2=?", "4", "4", "Matematik")
        {"is_correct": True, "feedback": "Doğru cevap!", "score": 100}
    """
    prompt = f"""
    Aşağıdaki öğrenci cevabını analiz et:
    
    Ders: {subject}
    Soru: {question}
    Öğrenci Cevabı: {student_answer}
    Doğru Cevap: {correct_answer}
    
    JSON formatında şu bilgileri ver:
    - is_correct: boolean (doğru mu?)
    - score: 0-100 arası puan
    - feedback: Türkçe geri bildirim
    - suggestions: İyileştirme önerileri listesi
    
    Sadece JSON döndür, başka açıklama ekleme.
    """

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        result_text = response.text.strip()

        # JSON parse et
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()

        return json.loads(result_text)
    except Exception as e:
        return {
            "is_correct": False,
            "score": 0,
            "feedback": f"Analiz hatası: {e!s}",
            "suggestions": []
        }


@mcp.tool()
async def generate_exam_question(
    subject: str,
    topic: str,
    difficulty: str = "orta",
    question_type: str = "çoktan seçmeli"
) -> dict[str, Any]:
    """
    Sınav sorusu üretir (LGS/YKS formatında).
    
    Args:
        subject: Ders adı
        topic: Konu başlığı
        difficulty: Zorluk seviyesi (kolay, orta, zor)
        question_type: Soru tipi (çoktan seçmeli, açık uçlu, doğru-yanlış)
    
    Returns:
        Üretilen soru ve cevap seçenekleri
    
    Example:
        >>> generate_exam_question("Matematik", "Kesirler", "orta", "çoktan seçmeli")
        {"question": "1/2 + 1/4 = ?", "options": ["1/6", "3/4", "2/6", "1/8"], "correct": "B"}
    """
    prompt = f"""
    MEB müfredatına uygun {question_type} soru üret:
    
    Ders: {subject}
    Konu: {topic}
    Zorluk: {difficulty}
    
    JSON formatında şu bilgileri ver:
    - question: Soru metni
    - options: Seçenekler listesi (A, B, C, D)
    - correct_answer: Doğru seçenek harfi
    - explanation: Çözüm açıklaması
    - bloom_level: Bloom taksonomisi seviyesi
    
    Sadece JSON döndür.
    """

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        result_text = response.text.strip()

        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()

        return json.loads(result_text)
    except Exception as e:
        return {
            "question": "",
            "options": [],
            "correct_answer": "",
            "explanation": f"Hata: {e!s}",
            "bloom_level": ""
        }


@mcp.tool()
async def create_learning_path(
    student_level: str,
    target_exam: str,
    weak_topics: list[str],
    time_available: int
) -> dict[str, Any]:
    """
    Öğrenci için kişiselleştirilmiş öğrenme yolu oluşturur.
    
    Args:
        student_level: Öğrenci seviyesi (başlangıç, orta, ileri)
        target_exam: Hedef sınav (LGS, YKS-TYT, YKS-AYT)
        weak_topics: Zayıf olunan konular listesi
        time_available: Mevcut çalışma süresi (gün)
    
    Returns:
        Öğrenme yolu planı
    
    Example:
        >>> create_learning_path("orta", "LGS", ["Kesirler", "Üçgenler"], 30)
        {"plan": [...], "daily_schedule": {...}, "milestones": [...]}
    """
    prompt = f"""
    Aşağıdaki öğrenci için kişiselleştirilmiş öğrenme yolu oluştur:
    
    Seviye: {student_level}
    Hedef Sınav: {target_exam}
    Zayıf Konular: {', '.join(weak_topics)}
    Süre: {time_available} gün
    
    JSON formatında şu bilgileri ver:
    - weekly_plan: Haftalık çalışma planı
    - daily_schedule: Günlük çalışma programı
    - topics_sequence: Konu sıralaması
    - milestones: Ara hedefler
    - estimated_improvement: Tahmini gelişim yüzdesi
    
    Sadece JSON döndür.
    """

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        result_text = response.text.strip()

        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()

        return json.loads(result_text)
    except Exception as e:
        return {
            "weekly_plan": [],
            "daily_schedule": {},
            "topics_sequence": [],
            "milestones": [],
            "estimated_improvement": 0,
            "error": str(e)
        }


@mcp.resource("gemini://health")
async def gemini_health() -> str:
    """Gemini API sağlık durumunu kontrol eder"""
    try:
        response = await asyncio.to_thread(
            model.generate_content,
            "Merhaba, test mesajı"
        )
        return f"✅ Gemini API aktif - Model: {model.model_name}"
    except Exception as e:
        return f"❌ Gemini API hatası: {e!s}"


if __name__ == "__main__":
    # MCP sunucusunu stdio transport ile çalıştır
    mcp.run(transport="stdio")
