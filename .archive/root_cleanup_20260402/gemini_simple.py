# -*- coding: utf-8 -*-
"""
Gemini Simple Chat - Basit Gemini Sohbet
Claude kullanmadan sadece Gemini
"""

import os
import sys

try:
    import google.generativeai as genai
except ImportError:
    print("Hata: google-generativeai paketi bulunamadi!")
    print("Kurulum: py -m pip install google-generativeai")
    sys.exit(1)

# API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Hata: GOOGLE_API_KEY bulunamadi!")
    print(".env dosyasini kontrol edin.")
    sys.exit(1)

# Gemini yapilandirmasi
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel("gemini-exp-1206")
    print("Model: Gemini Experimental 1206")
except:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print("Model: Gemini 2.0 Flash Experimental")

print("=" * 60)
print("GEMINI CHAT - Claude Olmadan")
print("=" * 60)
print("Komutlar: 'exit' (cikis), 'help' (yardim)")
print("=" * 60)
print()

# Sohbet dongusu
while True:
    try:
        # Kullanicidan mesaj al
        user_input = input("\nSiz: ").strip()
        
        if not user_input:
            continue
        
        # Komutlar
        if user_input.lower() in ["exit", "quit", "cikis"]:
            print("\nGorusmek uzere!")
            break
        
        if user_input.lower() in ["help", "yardim"]:
            print("\nKomutlar:")
            print("  exit, quit, cikis - Programdan cik")
            print("  help, yardim - Yardim mesaji")
            continue
        
        # Gemini'ye gonder
        print("\nGemini dusunuyor...")
        
        # Thinking mode ekle
        full_prompt = "Lutfen adim adim dusun ve detayli yanit ver.\n\n" + user_input
        
        response = model.generate_content(full_prompt)
        result = response.text
        
        print(f"\nGemini:\n{result}")
        print("-" * 60)
        
    except KeyboardInterrupt:
        print("\n\nGorusmek uzere!")
        break
    except Exception as e:
        print(f"\nHata: {e}")
