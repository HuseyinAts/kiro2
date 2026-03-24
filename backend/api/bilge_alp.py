"""
Bilge Alp NPC API — Streaming YKS Rehber NPC

FAZ-5: Alem Haritasi + NPC Sistemi
SSE streaming endpoint for realm NPC chat.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from core.dependencies import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bilge-alp", tags=["bilge-alp"])

# ---------------------------------------------------------------------------
# NPC personality per realm
# ---------------------------------------------------------------------------

NPC_PERSONAS: dict[str, dict[str, str]] = {
    "fizik": {
        "name": "Aristo",
        "title": "Fizik Ustası",
        "personality": "Newton ve Einstein'ın bilgeliğini taşıyan bir fizik dehası. Formülleri şiir gibi anlatır.",
        "style": "Analitik, meraklı, örnek çoklu.",
    },
    "kimya": {
        "name": "Marie",
        "title": "Kimya Üstadı",
        "personality": "Maddelerin dönüşümünü büyü gibi anlatan bir kimyacı. Deneylerle açıklar.",
        "style": "Sistematik, pratik, güvenlik bilincli.",
    },
    "biyoloji": {
        "name": "Darwin",
        "title": "Hayat Bilgesi",
        "personality": "Doğanın tüm sırlarını bilen, yaşamı anlayan bir biyolog.",
        "style": "Gözlemci, meraklı, doğa sevdalısı.",
    },
    "matematik": {
        "name": "Gauss",
        "title": "Sayılar Ustası",
        "personality": "Matematiği bir sanat formu olarak gören ve her problemi zarafetle çözen dahi.",
        "style": "Kesin, adım adım, ispat odaklı.",
    },
    "geometri": {
        "name": "Öklid",
        "title": "Uzay Mimarı",
        "personality": "Şekillerin ve uzayın sırlarını çözen antik geometri ustası.",
        "style": "Görsel, ispat odaklı, çizim sever.",
    },
    "tarih": {
        "name": "Timur",
        "title": "Tarih Anlatıcısı",
        "personality": "Tarihin sayfalarında yaşayan, olayları hikaye gibi anlatan bilge.",
        "style": "Anlatıcı, bağlantılı, kronolojik.",
    },
    "cografya": {
        "name": "İbn Batuta",
        "title": "Dünya Gezgini",
        "personality": "Dünyanın her köşesini gezen, coğrafyayı yaşayan bir kaşif.",
        "style": "Macera dolu, görsel, analitik.",
    },
    "turkce": {
        "name": "Yunus",
        "title": "Dil Şairi",
        "personality": "Türkçeyi şiirle, dilin güzelliğini aşkla anlatan bir dil ustası.",
        "style": "Şiirsel, örnekli, kültürel.",
    },
    "edebiyat": {
        "name": "Fuzuli",
        "title": "Kelime Büyücüsü",
        "personality": "Edebiyatı büyük bir nehir gibi akan, her eseri ruhundan anlayan şair.",
        "style": "Lirik, çözümleyici, bağlantılı.",
    },
    "felsefe": {
        "name": "Farabi",
        "title": "Akıl Ustası",
        "personality": "Sorular sormayı, düşünmeyi, var olmayı sorgulayan Doğu'nun filozofu.",
        "style": "Sorgulayıcı, diyalog, sistematik.",
    },
    "din": {
        "name": "Mevlana",
        "title": "Hikmet Rehberi",
        "personality": "Ahlak, değerler ve anlam üzerine derin bilgelikle rehberlik eden.",
        "style": "Sakin, anlayışlı, değer odaklı.",
    },
    "oba": {
        "name": "Dede Korkut",
        "title": "Oba Beyi",
        "personality": "Obayı yöneten, takım ruhunu ve dayanışmayı öğreten kadim bilge.",
        "style": "Lider, motive edici, hikayeci.",
    },
}

DEFAULT_PERSONA = {
    "name": "Bilge Alp",
    "title": "YKS Rehberi",
    "personality": "YKS'nin tüm alanlarında deneyimli, öğrencilere yol gösteren bilge.",
    "style": "Teşvik edici, yapılandırılmış, pratik.",
}

# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------


def _build_system_prompt(realm_slug: str, bkt_score: float, quest_step: int) -> str:
    persona = NPC_PERSONAS.get(realm_slug, DEFAULT_PERSONA)
    mastery_pct = int(bkt_score * 100)

    zpd_hint = ""
    if bkt_score < 0.40:
        zpd_hint = (
            "Öğrenci yeni başlıyor — temel kavramları basit dille anlat, cesaretlendir."
        )
    elif bkt_score < 0.70:
        zpd_hint = "Öğrenci orta seviyede — bağlantılar kur, derinleştir, pratik yap."
    else:
        zpd_hint = "Öğrenci ustalaşıyor — ileri düzey bağlantılar, sınav stratejisi, mükemmelleştir."

    quest_hint = ""
    if quest_step == 0:
        quest_hint = "Görev henüz başlamadı — öğrenciyi keşfetmeye davet et."
    elif quest_step >= 1:
        quest_hint = (
            f"Görev adım {quest_step}'de — ilerlemeyi kutla, sonraki adımı teşvik et."
        )

    return f"""Sen {persona["name"]}'sın, {persona["title"]} — {realm_slug.upper()} ALEMI'nin rehberi.

KİŞİLİK: {persona["personality"]}
ANLATIM TARZI: {persona["style"]}

ÖĞRENCİ DURUMU:
- Ustalık: %{mastery_pct} (BKT skoru: {bkt_score:.2f})
- {zpd_hint}
- {quest_hint}

KURALLLAR:
1. Her zaman Türkçe konuş, sıcak ve cesaretlendirici ol.
2. YKS/TYT/AYT formatında düşün — pratik, sınav odaklı.
3. Cevapları kısa tut (3-5 cümle), gerekirse listele.
4. Emoji kullanabilirsin ama aşırıya kaçma.
5. Matematik formülleri için LaTeX formatı kullan ($...$).
6. Öğrencinin seviyesine uygun dil kullan."""


# ---------------------------------------------------------------------------
# LLM streaming helper
# ---------------------------------------------------------------------------


async def _stream_llm_response(  # type: ignore[return]
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
):
    """Stream tokens from LLM. Falls back to mock if LLM unavailable."""
    try:
        import os

        import httpx

        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
            "LITELLM_API_KEY"
        )
        if not api_key:
            raise ValueError("No LLM API key configured")

        messages = [
            *history[-8:],  # keep last 8 turns
            {"role": "user", "content": user_message},
        ]

        async with (
            httpx.AsyncClient(timeout=30) as client,
            client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 512,
                    "system": system_prompt,
                    "messages": messages,
                    "stream": True,
                },
            ) as resp,
        ):
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "content_block_delta":
                            yield event["delta"].get("text", "")
                    except (json.JSONDecodeError, KeyError):
                        pass

    except Exception as e:
        logger.warning("LLM unavailable, using mock response: %s", e)
        # Fallback mock response
        mock = f"Merhaba! Şu an tam olarak bağlanamıyorum ama yardımcı olmaya hazırım. '{user_message}' konusunda sana rehberlik edebilirim. Devam edelim mi?"
        for char in mock:
            yield char
            await asyncio.sleep(0.015)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/chat")
async def bilge_alp_chat(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StreamingResponse:
    """SSE streaming NPC chat. BKT score fetched from DB (not client)."""
    logger.debug("NPC chat: user=%s", current_user.id)
    try:
        body = await request.json()
    except Exception:
        body = {}

    realm_slug = str(body.get("realm_slug", "matematik"))
    quest_step = int(body.get("quest_step", 0))
    user_message = str(body.get("message", "Merhaba")).strip()[:500]
    history: list[dict[str, str]] = body.get("history", [])

    # Fetch BKT score from DB instead of trusting client
    bkt_score = 0.0
    try:
        from sqlalchemy import func as sa_func
        from sqlalchemy import select

        from core.database import get_db_session_context
        from models.gamification import BKTState

        async with get_db_session_context() as db:
            result = await db.execute(
                select(sa_func.avg(BKTState.p_learn)).where(
                    BKTState.student_id == str(current_user.id),
                    BKTState.topic_id.like(f"{realm_slug}%"),
                )
            )
            avg_mastery = result.scalar()
            if avg_mastery is not None:
                bkt_score = float(avg_mastery)
    except Exception as e:
        logger.warning("BKT score fetch failed, using default 0.0: %s", e)

    # Sanitize history
    clean_history = [
        {"role": h["role"], "content": str(h["content"])[:500]}
        for h in history
        if isinstance(h, dict) and h.get("role") in ("user", "assistant")
    ]

    system_prompt = _build_system_prompt(realm_slug, bkt_score, quest_step)

    async def event_generator():
        try:
            async for token in _stream_llm_response(  # type: ignore[misc]
                system_prompt, clean_history, user_message
            ):
                if token:
                    yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Stream error: %s", e)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Branching Dialog — NPC secim bazli diyalog
# ---------------------------------------------------------------------------

# Her realm+step icin NPC secenekleri
NPC_DIALOG_BRANCHES: dict[str, dict[int, dict]] = {
    "matematik": {
        0: {
            "npc_message": "Hosgeldin, genc matematikci! Sayilar diyarina katilmak istiyorsun. Sana nasil rehberlik edeyim?",
            "choices": [
                {
                    "id": "basic",
                    "text": "Temelden baslayalim",
                    "effect": "Temel kavramlardan basla, cesaretlendir.",
                },
                {
                    "id": "challenge",
                    "text": "Beni zorlayacak sorular ver",
                    "effect": "Zor sorularla basla, ustunluk test et.",
                },
                {
                    "id": "explore",
                    "text": "Bu alemin sirlari neler?",
                    "effect": "Matematiksel guzelliklerden bahset, motivasyon ver.",
                },
            ],
        },
        3: {
            "npc_message": "Buyuk ilerleme! Artik fonksiyonlarin dilini konusuyorsun. Simdi ne yapmak istersin?",
            "choices": [
                {
                    "id": "practice",
                    "text": "Pratik yapmak istiyorum",
                    "effect": "Quiz moduna yonlendir.",
                },
                {
                    "id": "theory",
                    "text": "Teoriyi derinlestirelim",
                    "effect": "Kavramsak derinlik, ispat ve baglantilar.",
                },
                {
                    "id": "exam",
                    "text": "Sinav stratejisi ogren",
                    "effect": "YKS sinav taktikleri ve zaman yonetimi.",
                },
            ],
        },
    },
    "fizik": {
        0: {
            "npc_message": "Ben Aristo, fizik diyarinin rehberiyim! Kuvvetler ve hareket dunyasina hosgeldin. Nereden baslamak istersin?",
            "choices": [
                {
                    "id": "newton",
                    "text": "Newton'un yasalarini ogren",
                    "effect": "Temel mekanik, F=ma, momentum.",
                },
                {
                    "id": "energy",
                    "text": "Enerji nedir?",
                    "effect": "Enerji korunumu, kinetik-potansiyel donusum.",
                },
                {
                    "id": "daily",
                    "text": "Gunluk hayatta fizik",
                    "effect": "Gercek hayat ornekleri ile fizik kavramlari.",
                },
            ],
        },
    },
}

# Her realm icin varsayilan dialog (tanimlanmamis step'ler icin)
DEFAULT_DIALOG = {
    "npc_message": "Merhaba! Bu alemde sana rehberlik etmeye hazirim. Ne ogrenmek istersin?",
    "choices": [
        {
            "id": "learn",
            "text": "Konu anlatimi istiyorum",
            "effect": "Konu anlatim modu.",
        },
        {
            "id": "quiz",
            "text": "Soru cozmek istiyorum",
            "effect": "Soru cozme moduna gec.",
        },
        {
            "id": "hint",
            "text": "Ipucu ve strateji ver",
            "effect": "Sinav stratejisi modu.",
        },
    ],
}


@router.post("/dialog-options")
async def get_dialog_options(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """NPC branching dialog seceneklerini getir. Frontend secim butonu gosterir."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    realm_slug = str(body.get("realm_slug", "matematik"))
    quest_step = int(body.get("quest_step", 0))
    chosen_id = body.get("chosen_id")  # Onceki secim (None ise ilk diyalog)

    realm_dialogs = NPC_DIALOG_BRANCHES.get(realm_slug, {})
    dialog = realm_dialogs.get(quest_step, DEFAULT_DIALOG)

    persona = NPC_PERSONAS.get(realm_slug, DEFAULT_PERSONA)

    # Eger bir secim yapildiysa, secimin etkisini mesaja ekle
    chosen_effect = None
    if chosen_id:
        for choice in dialog.get("choices", []):
            if choice["id"] == chosen_id:
                chosen_effect = choice["effect"]
                break

    return {
        "npc_name": persona["name"],
        "npc_title": persona["title"],
        "realm_slug": realm_slug,
        "quest_step": quest_step,
        "message": dialog["npc_message"],
        "choices": dialog.get("choices", []),
        "chosen_effect": chosen_effect,
    }
