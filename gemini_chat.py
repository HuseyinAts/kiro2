"""
Gemini Chat - Claude Kullanmadan Sadece Gemini ile Sohbet
Kiro IDE'den bağımsız, doğrudan Gemini API kullanımı
"""

import os
import sys
import asyncio
from typing import Optional

# Google Generative AI import
try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai paketi bulunamadı!")
    print("Kurulum: py -m pip install google-generativeai")
    sys.exit(1)

# API Key kontrolü
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_API_KEY environment variable bulunamadı!")
    print("Lütfen .env dosyasını kontrol edin.")
    sys.exit(1)

# Gemini yapılandırması
genai.configure(api_key=API_KEY)

# Model seçimi
try:
    MODEL = genai.GenerativeModel("gemini-exp-1206")
    MODEL_NAME = "Gemini Experimental 1206"
except Exception:
    try:
        MODEL = genai.GenerativeModel("gemini-2.0-flash-exp")
        MODEL_NAME = "Gemini 2.0 Flash Experimental"
    except Exception as e:
        print(f"❌ Gemini model yüklenemedi: {e}")
        sys.exit(1)


class GeminiChat:
    """Gemini ile sohbet sınıfı"""
    
    def __init__(self):
        self.model = MODEL
        self.model_name = MODEL_NAME
        self.chat_history = []
    
    def send_message(self, message: str, thinking_mode: bool = True) -> str:
        """
        Gemini'ye mesaj gönder
        
        Args:
            message: Kullanıcı mesajı
            thinking_mode: Detaylı akıl yürütme modu
        
        Returns:
            Gemini'nin yanıtı
        """
        try:
            # Thinking mode için prompt ekle
            if thinking_mode:
                full_message = (
                    "Lütfen adım adım düşünerek ve akıl yürütme sürecini göstererek yanıtla.\n\n"
                    + message
                )
            else:
                full_message = message
            
            # Gemini'ye gönder
            response = self.model.generate_content(full_message)
            result = response.text
            
            # Geçmişe ekle
            self.chat_history.append({
                "role": "user",
                "content": message
            })
            self.chat_history.append({
                "role": "assistant",
                "content": result
            })
            
            return result
            
        except Exception as e:
            return f"❌ Hata: {str(e)}"
    
    def clear_history(self):
        """Sohbet geçmişini temizle"""
        self.chat_history = []
        print("✅ Sohbet geçmişi temizlendi")


def print_banner():
    """Başlık banner'ı yazdır"""
    print("\n" + "=" * 80)
    print("GEMINI CHAT - Claude Kullanmadan Sadece Gemini")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print("Komutlar: 'exit' (cikis), 'clear' (gecmisi temizle), 'help' (yardim)")
    print("=" * 80 + "\n")


def print_help():
    """Yardım mesajı"""
    print("\n📚 YARDIM")
    print("-" * 80)
    print("Komutlar:")
    print("  exit, quit, çıkış  - Programdan çık")
    print("  clear, temizle     - Sohbet geçmişini temizle")
    print("  help, yardım       - Bu yardım mesajını göster")
    print("\nÖzellikler:")
    print("  - Thinking Mode: Gemini adım adım düşünerek yanıtlar")
    print("  - Sohbet Geçmişi: Önceki mesajlar hatırlanır")
    print("  - Türkçe Destek: Tam Türkçe dil desteği")
    print("-" * 80 + "\n")


def interactive_mode():
    """İnteraktif sohbet modu"""
    
    print_banner()
    
    chat = GeminiChat()
    
    print("Gemini ile sohbete baslayabilirsiniz!\n")
    
    while True:
        try:
            # Kullanıcıdan mesaj al
            user_input = input("🧑 Siz: ").strip()
            
            if not user_input:
                continue
            
            # Komutları kontrol et
            if user_input.lower() in ["exit", "quit", "çıkış"]:
                print("\n👋 Görüşmek üzere!")
                break
            
            if user_input.lower() in ["clear", "temizle"]:
                chat.clear_history()
                continue
            
            if user_input.lower() in ["help", "yardım"]:
                print_help()
                continue
            
            # Gemini'ye gönder
            print("\n🤖 Gemini düşünüyor...\n")
            response = chat.send_message(user_input, thinking_mode=True)
            
            print(f"🤖 Gemini:\n{response}\n")
            print("-" * 80)
            
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"\n❌ Hata: {e}\n")


def quick_question(question: str):
    """Hızlı soru-cevap modu"""
    
    print(f"\nGemini'ye soruluyor: {question}\n")
    
    chat = GeminiChat()
    response = chat.send_message(question, thinking_mode=True)
    
    print(f"Gemini Yaniti:\n{response}\n")


def main():
    """Ana fonksiyon"""
    
    if len(sys.argv) > 1:
        # Komut satırından soru
        question = " ".join(sys.argv[1:])
        quick_question(question)
    else:
        # İnteraktif mod
        interactive_mode()


if __name__ == "__main__":
    main()
