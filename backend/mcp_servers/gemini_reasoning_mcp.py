"""
Gemini 3 Pro Reasoning Engine MCP Server
Google Gemini 3 modelini MCP protokolü üzerinden sunar
"""

import os
import sys

import google.generativeai as genai
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Gemini Reasoning Engine")

# API Key kontrolü
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_API_KEY environment variable bulunamadı", file=sys.stderr)
    sys.exit(1)

# Gemini yapılandırması
genai.configure(api_key=API_KEY)

# Model seçimi (Gemini 3 Pro veya fallback)
try:
    MODEL = genai.GenerativeModel("gemini-exp-1206")  # En yeni experimental model
    print("✅ Gemini Experimental 1206 modeli yüklendi", file=sys.stderr)
except Exception:
    try:
        MODEL = genai.GenerativeModel("gemini-2.0-flash-exp")
        print("✅ Gemini 2.0 Flash Experimental modeli yüklendi", file=sys.stderr)
    except Exception as e:
        print(f"❌ Gemini model yüklenemedi: {e}", file=sys.stderr)
        sys.exit(1)


@mcp.tool()
async def gemini_reasoning_engine(
    prompt: str,
    context: str | None = None,
    thinking_mode: bool = True
) -> str:
    """
    Google Gemini modelini kullanarak karmaşık akıl yürütme, sistem tasarımı,
    kod analizi ve gereksinim analizi yapar.

    Args:
        prompt: Gemini'ye gönderilecek soru veya görev
        context: Ek bağlam bilgisi (opsiyonel)
        thinking_mode: Detaylı akıl yürütme modu (varsayılan: true)

    Returns:
        Gemini'nin detaylı yanıtı

    Example:
        >>> gemini_reasoning_engine(
        ...     prompt="Bu design.md dosyasını analiz et",
        ...     context="FastAPI backend projesi",
        ...     thinking_mode=True
        ... )
        "🤖 Gemini Analizi: ..."
    """
    try:
        # Prompt'u hazırla
        full_prompt = prompt

        if context:
            full_prompt = f"Bağlam:\n{context}\n\nGörev:\n{prompt}"

        if thinking_mode:
            full_prompt = (
                "Lütfen adım adım düşünerek ve akıl yürütme sürecini göstererek yanıtla.\n\n"
                + full_prompt
            )

        # Gemini'ye istek gönder
        response = MODEL.generate_content(full_prompt)
        result_text = response.text

        return f"🤖 Gemini Yanıtı:\n\n{result_text}"

    except Exception as e:
        return f"❌ Gemini API Hatası: {e!s}"


@mcp.tool()
async def gemini_code_review(code: str, language: str = "python") -> str:
    """
    Kod incelemesi ve optimizasyon önerileri.

    Args:
        code: İncelenecek kod
        language: Programlama dili (varsayılan: python)

    Returns:
        Detaylı kod incelemesi ve öneriler
    """
    prompt = f"""
Aşağıdaki {language} kodunu detaylı olarak incele:

```{language}
{code}
```

Lütfen şunları analiz et:
1. Kod kalitesi ve okunabilirlik
2. Performans optimizasyonları
3. Güvenlik açıkları
4. Best practice uygulamaları
5. Refactoring önerileri
"""

    try:
        response = MODEL.generate_content(prompt)
        return f"🔍 Kod İncelemesi:\n\n{response.text}"
    except Exception as e:
        return f"❌ Hata: {e!s}"


@mcp.tool()
async def gemini_design_analysis(design_doc: str) -> str:
    """
    Sistem tasarım dokümanı analizi.

    Args:
        design_doc: Design.md dosyasının içeriği

    Returns:
        Mimari analiz ve iyileştirme önerileri
    """
    prompt = f"""
Aşağıdaki sistem tasarım dokümanını analiz et:

{design_doc}

Lütfen şunları değerlendir:
1. Mimari tasarım kalitesi
2. Bileşen yapısı ve sorumluluklar
3. Veri modeli tasarımı
4. API tasarımı
5. Güvenlik ve performans konuları
6. İyileştirme önerileri
"""

    try:
        response = MODEL.generate_content(prompt)
        return f"🏗️ Tasarım Analizi:\n\n{response.text}"
    except Exception as e:
        return f"❌ Hata: {e!s}"


@mcp.tool()
async def gemini_requirements_analysis(requirements_doc: str) -> str:
    """
    Gereksinim dokümanı analizi.

    Args:
        requirements_doc: Requirements.md dosyasının içeriği

    Returns:
        Gereksinim analizi ve eksiklik tespiti
    """
    prompt = f"""
Aşağıdaki gereksinim dokümanını analiz et:

{requirements_doc}

Lütfen şunları kontrol et:
1. User story kalitesi
2. Acceptance criteria eksiksizliği
3. EARS formatına uygunluk
4. Testable property'ler
5. Eksik veya belirsiz gereksinimler
6. İyileştirme önerileri
"""

    try:
        response = MODEL.generate_content(prompt)
        return f"📋 Gereksinim Analizi:\n\n{response.text}"
    except Exception as e:
        return f"❌ Hata: {e!s}"


@mcp.resource("gemini://health")
async def gemini_health() -> str:
    """Gemini servis sağlık kontrolü"""
    try:
        # Basit bir test isteği
        response = MODEL.generate_content("Test")
        return f"✅ Gemini servisi aktif. Model: {MODEL.model_name}"
    except Exception as e:
        return f"❌ Gemini servisi kullanılamıyor: {e!s}"


if __name__ == "__main__":
    # Run MCP server with stdio transport (for IDE integration)
    mcp.run(transport="stdio")
