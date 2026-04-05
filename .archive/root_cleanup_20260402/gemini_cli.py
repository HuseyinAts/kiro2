"""
Gemini CLI - Komut satırından Gemini kullanımı
"""

import os
import sys
import google.generativeai as genai

# API Key kontrolü
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_API_KEY bulunamadı!")
    print("\nÇözüm:")
    print("1. .env dosyasını açın")
    print("2. GOOGLE_API_KEY=your_key_here satırını kontrol edin")
    sys.exit(1)

# Gemini yapılandırması
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel("gemini-exp-1206")
    print("✅ Gemini Experimental 1206 yüklendi\n")
except Exception:
    model = genai.GenerativeModel("gemin