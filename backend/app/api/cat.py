"""
KIRO2 — CAT API Router
=======================
Endpoint'ler:
  POST   /api/v1/cat/sessions              → Yeni oturum başlat
  POST   /api/v1/cat/sessions/{id}/answer  → Yanıt gönder, sonraki soru al
  GET    /api/v1/cat/sessions/{id}         → Oturum durumunu sorgula
  DELETE /api/v1/cat/sessions/{id}         → Oturumu iptal et

Neden 3 endpoint, tek "soru ver" değil?
  - start: placement ve warm-up mantığı farklı
  - answer: θ güncelle + sonraki seç (atomik)
  - GET:    frontend reconnect sonrası state yenile
  - DELETE: kullanıcı oturumu yarıda bırakırsa temizlik
"""

# DİKKAT: `from __future__ import annotations` EKLEME.
# slowapi'nin @limiter.limit sarmalayıcısı functools.wraps kullanır; wrapper'ın
# __globals__'ı slowapi modülünü gösterir. Annotation'lar string'e dönerse
# FastAPI `CatNextRequest`i o namespace'te çözemez ve gövde parametresini QUERY
# param sanıp her isteğe 422 döner. Repo'daki diğer @limiter.limit kullanımları
# (api/enhanced_chat.py, api/osym_routes.py) da bu yüzden future-import'suz.

import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db, get_redis
from app.schemas.cat_schemas import (
    CatNextItem,
    CatNextRequest,
    CatNextResponse,
    CatUygulananItem,
    FeedbackResponse,
    SessionStateResponse,
    StartSessionRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services import irt_engine as irt
from app.services.cat_session import CATSessionService, CATState
from core.ddos_protection import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cat", tags=["CAT"])

# ── Yerleştirme (POST /next) politikası ──────────────────────────
# Oturum kimliği HttpOnly çerezle taşınır: frontend sözleşmesi (CatNextResult)
# oturumId DÖNDÜRMEZ, dolayısıyla istemci onu geri gönderemez. live() zaten
# credentials:'include' kullanıyor → çerez otomatik turlar, ekran kodu değişmez.
CAT_SID_COOKIE = "cat_sid"
CAT_SID_COOKIE_PATH = "/api/v1/cat"

# Yerleştirme dersi. Sözleşmede ders alanı YOK; tek tüketici ekran (Adaptif Test)
# "TYT Matematik" başlığını sabit basıyor.
PLACEMENT_SUBJECT = "MATEMATIK"

# 12 madde + SE≤0.45. Üretim havuzu bootstrap IRT parametreleriyle (a≈1.00,
# c=0.20, b∈[-1.05,0.89]) motorun varsayılan SE 0.35 eşiği 20 maddede bile
# yakalanmaz (ölçüm: 20 maddede SE≈0.51). Panelin θ-yakınsama grafiği de
# x eksenini tam 12 maddeye göre çizer.
PLACEMENT_MAX_ITEMS = 12
PLACEMENT_SE_STOP = 0.45

_OPTION_LETTERS = ("A", "B", "C", "D", "E")
_GUEST_PREFIX = "guest:"

# Auth'suz uç → hız sınırı ZORUNLU. Dürüst kullanım 12 maddede ~13 istek;
# 30/dk bunu rahat karşılar ama sınırsız misafir-oturum üretimini keser.
PLACEMENT_RATE_LIMIT = "30/minute"


# ── Dependency: CATSessionService ────────────────────────────────


def get_cat_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> CATSessionService:
    if redis is None:
        try:
            import os

            import redis.asyncio as _aioredis

            _url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis = _aioredis.from_url(_url, decode_responses=False)
        except Exception:
            pass
    return CATSessionService(redis=redis, db=db)


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> User | None:
    """
    get_current_user'ın 401 fırlatmayan ikizi — misafir yerleştirme için.

    Kanonik doğrulamayı (blacklist + JWT decode + cookie fallback) yeniden
    yazmak yerine ona delege eder; yalnız "kimlik yok" durumunu None'a çevirir.
    Repo'daki iki mevcut get_current_user_optional bu iş için kullanılamaz:
    core/auth.py:299 auto_error=True HTTPBearer'a bağlı olduğu için anonim
    istekte 403 üretir, core/learning_path_auth.py:308 ise cookie okumaz
    (frontend cookie-auth kullanıyor) ve AuthenticatedUser döndürmez.
    """
    kimlik_sunuldu = bool(credentials and credentials.credentials) or bool(
        request.cookies.get("access_token")
    )
    if not kimlik_sunuldu:
        return None
    # Kimlik SUNULDU ama geçersiz/süresi dolmuş/blacklist'li ise 401 fırlasın:
    # sessizce misafire düşürmek, öğrencinin ölçülen θ'sını kalıcılaştırılamaz
    # hale getirir ve istemcinin tek yeniden-giriş yolunu (401 → /login) keser.
    return await get_current_user(request=request, credentials=credentials)


# ── Endpoints ────────────────────────────────────────────────────


@router.post(
    "/sessions",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni CAT oturumu başlat",
    description="""
    Belirtilen ders için yeni bir adaptif test oturumu başlatır.

    - Önceki aktif oturumu iptal eder.
    - İlk soru warm-up (kolay) bölgesinden seçilir.
    - Redis'te 1 saatlik oturum açılır.
    """,
)
async def start_cat_session(
    body: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    service: CATSessionService = Depends(get_cat_service),
) -> StartSessionResponse:
    try:
        result = await service.start_session(
            user_id=str(current_user.id),
            subject_id=str(body.subject_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return StartSessionResponse(**result)


@router.post(
    "/sessions/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    summary="Yanıt gönder — θ güncelle — sonraki soruyu al",
    description="""
    Bir soruyu yanıtlar ve sonucu döndürür.

    **Oturum bitme koşulları:**
    - `se < 0.35` — θ yeterince hassas tahmin edildi
    - `n_questions >= 20` — maksimum soru sayısına ulaşıldı

    Bitmişse `is_complete=true` ve `next_question=null` gelir.
    """,
)
async def submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    service: CATSessionService = Depends(get_cat_service),
) -> SubmitAnswerResponse:
    # Önce oturumun bu kullanıcıya ait olduğunu doğrula
    state = await service.get_session_state(session_id)
    if not state or state.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oturum bulunamadı veya süresi dolmuş",
        )

    # Doğru mu?  — DB'den doğru seçeneği al
    is_correct = await _check_answer(
        service.db, str(body.question_id), body.get_selected()
    )

    try:
        result = await service.submit_answer(
            session_id=session_id,
            question_id=str(body.question_id),
            is_correct=is_correct,
            response_ms=body.response_ms,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    # FeedbackResponse: doğru şıkkı ekle
    _svc_fb = result.get("feedback", {})
    _co = _svc_fb.get("correct_option") if isinstance(_svc_fb, dict) else None
    result["feedback"] = FeedbackResponse(
        is_correct=is_correct,
        correct_option=_co,
    )
    return SubmitAnswerResponse(**result)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionStateResponse,
    summary="Oturum durumunu getir",
)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: CATSessionService = Depends(get_cat_service),
) -> SessionStateResponse:
    state = await service.get_session_state(session_id)
    if not state or state.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")

    return SessionStateResponse(
        session_id=state.session_id,
        state=state.state,
        theta=state.theta,
        se=state.se,
        n_questions=state.n_questions,
        warm_up_done=state.warm_up_done,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Oturumu iptal et",
)
async def abandon_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: CATSessionService = Depends(get_cat_service),
):
    # DİKKAT: `-> None` dönüş anotasyonu EKLEME.
    #
    # Hata İKİ koşulun BİRLİKTE olmasıyla çıkar (27 Tem 2026 ölçümü):
    #   (a) `from __future__ import annotations` dosyanın başında VAR, ve
    #   (b) bu fonksiyonda `-> None` dönüş anotasyonu VAR.
    # (a) anotasyonu string'e çevirir; FastAPI 0.103.2 onu get_type_hints ile
    # NoneType'a çözer, NoneType truthy olduğu için 204'ün "gövde yasak"
    # assert'i modül import'unda patlar → TÜM CAT router'ı kayıtsız kalır
    # (/api/v1/cat/* → 404). (a) YOKSA `-> None` düz None objesidir (falsy)
    # ve sorun çıkmaz — ölçüldü. Yeni FastAPI sürümlerinde None özel-durumlu.
    #
    # Bu dosyada (a) zaten YASAK (bkz. dosya başı slowapi notu); yine de bu
    # anotasyonu eklemeyin: iki yasak birbirini yedekler.
    state = await service.get_session_state(session_id)
    if not state or state.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Erişim reddedildi")
    await service.abandon_session(session_id)


# ── Yerleştirme adaptörü: POST /api/v1/cat/next ──────────────────


def _sahiplik_uyuyor(state: CATState, sahip: str | None) -> bool:
    """Çerezdeki/gövdedeki oturum bu isteğin sahibine mi ait?"""
    if sahip is None:
        # Misafir yalnız misafir oturumunu sürdürebilir; giriş yapmış birinin
        # oturumunu çerezle devralmak IDOR olurdu.
        return state.user_id.startswith(_GUEST_PREFIX)
    return state.user_id == sahip


def _sunulan_harfler(secenekler_map: dict) -> list[str]:
    """
    İstemciye GÖNDERİLEN şıkların harf sırası.

    `secim` alanı bu dizinin İNDEKSİDİR. Boş bir şık elenirse (örn. option_c
    boş) A..E sabit dizisi ile hizalama bozulur ve öğrencinin doğru cevabı
    yanlış sayılır — bu yüzden hem gönderim hem puanlama TEK kaynaktan türer.
    """
    return [h for h in _OPTION_LETTERS if secenekler_map.get(h)]


def _madde(soru: dict | None) -> CatNextItem:
    """Servis sözlüğünü sözleşmedeki maddeye çevir — doğru şık ASLA taşınmaz."""
    if not soru:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yerleştirme sorusu getirilemedi",
        )
    secenekler_map = soru.get("options") or {}
    return CatNextItem(
        id=str(soru["question_id"]),
        b=float(soru["irt"]["difficulty"]),
        konu=soru.get("konu") or soru.get("subject_id") or "",
        soru=soru["stem"],
        secenekler=[str(secenekler_map[h]) for h in _sunulan_harfler(secenekler_map)],
    )


def _panel(state: CATState, soru: dict | None, *, done: bool) -> CatNextResponse:
    """θ/SE'den motor panelini kur. İstemci bu değerlerin HİÇBİRİNİ hesaplamaz."""
    item_params = state.get_item_params_objects()
    gecmis = irt.replay_theta_history(state.responses, item_params)
    uygulananlar = [
        CatUygulananItem(
            b=float(state.item_params[i].get("b", 0.0)),
            ok=bool(state.responses[i]),
            theta=sonuc.theta,
            se=sonuc.se,
        )
        for i, sonuc in enumerate(gecmis)
    ]

    kalan = (
        0
        if done
        else irt.items_to_target_se(
            se=state.se,
            theta=state.theta,
            item_params=item_params,
            target_se=PLACEMENT_SE_STOP,
            # Bütçe: cevaplanan + atlanan (omit de bir madde sunumudur).
            remaining_budget=max(
                0,
                PLACEMENT_MAX_ITEMS - state.n_questions - len(state.skipped_ids),
            ),
        )
    )

    return CatNextResponse(
        item=_madde(soru),
        theta=round(state.theta, 4),
        se=round(state.se, 4),
        done=done,
        seviye=irt.ability_band(state.theta),
        # SE geçilir: yüzdelik ölçüm hatasına göre %50'ye çekilsin
        # (yerleştirmede SE~0.6-1.0; Φ(θ̂) aşırı özgüvenli olurdu).
        topPct=irt.theta_percentile(state.theta, se=state.se),
        netTahmini=irt.expected_net(state.theta),
        madde=state.n_questions,
        kalanTahmini=kalan,
        guvenilirlik=irt.marginal_reliability(state.se),
        uygulananlar=uygulananlar,
    )


@router.post(
    "/next",
    response_model=CatNextResponse,
    summary="Adaptif yerleştirme — sonraki madde (misafir de kullanabilir)",
    description="""
    Tek uçlu yerleştirme akışı (Adaptif Test ekranının sözleşmesi).

    - `maddeId` YOKSA yeni oturum başlar (ekranın mount/yeniden-dene çağrısı).
    - `maddeId` VARSA o madde cevaplanır, θ güncellenir, sonraki madde döner.
    - `secim` 0-tabanlı şık indeksidir; `null` = "Emin değilim" (yanlış sayılır).

    Oturum `cat_sid` HttpOnly çerezinde taşınır. Auth ZORUNLU DEĞİL: giriş
    yapılmamışsa misafir oturumu açılır ve hiçbir kalıcı tabloya yazılmaz.
    """,
)
@limiter.limit(PLACEMENT_RATE_LIMIT)
async def cat_next(
    # Parametre SIRASI önemli: slowapi'nin @limiter.limit sarmalayıcısı
    # `request`i ilk konumda arar, `response`u da başlık iliştirmek için ister
    # (bkz. api/enhanced_chat.py GF24 notu).
    request: Request,
    response: Response,
    body: CatNextRequest,
    current_user: User | None = Depends(get_optional_user),
    service: CATSessionService = Depends(get_cat_service),
) -> CatNextResponse:
    sahip = str(current_user.id) if current_user else None

    session_id = body.oturumId or request.cookies.get(CAT_SID_COOKIE)
    onceki = await service.get_session_state(session_id) if session_id else None
    bizim = onceki is not None and _sahiplik_uyuyor(onceki, sahip)

    # Süresi dolmuş / yabancı / kapanmış oturum → sessizce yeniden başla.
    # Ekranın hata sınırı yok; 4xx kullanıcıyı kilitler.
    state = onceki if (bizim and onceki.is_active()) else None

    if state is None or not body.maddeId:
        misafir = sahip is None
        # Misafir kimliğini KORU: her çağrıda yeni guest:<uuid> üretmek
        # cat:active:{user_id}:{subject} anahtarını hiç eşleştirmez, önceki
        # oturum kapatılmaz ve her yenilemede 1 saatlik oturum birikir.
        if misafir and bizim and onceki.user_id.startswith(_GUEST_PREFIX):
            uid = onceki.user_id
        else:
            uid = sahip or f"{_GUEST_PREFIX}{uuid.uuid4()}"
        try:
            sonuc = await service.start_session(
                user_id=uid,
                subject_id=PLACEMENT_SUBJECT,
                is_guest=misafir,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc

        response.set_cookie(
            key=CAT_SID_COOKIE,
            value=sonuc["session_id"],
            httponly=True,
            secure=os.getenv("ENVIRONMENT", "development") != "development",
            samesite="lax",
            max_age=3600,  # CAT_SESSION_TTL ile aynı
            path=CAT_SID_COOKIE_PATH,
        )
        yeni_state = await service.get_session_state(sonuc["session_id"])
        return _panel(yeni_state, sonuc["question"], done=False)

    # Mevcut oturuma cevap.
    # GÜVENLİK: yanıt YALNIZCA sunucunun bu oturumda servis ettiği maddeye
    # verilebilir. Aksi halde hangi sorunun puanlanacağını istemci seçer ve
    # yanıttaki uygulananlar[].ok alanı, auth'suz bu ucu tüm question_bank için
    # cevap-anahtarı oracle'ına çevirir (~4 istekte bir sorunun cevabı çıkar).
    if body.maddeId != state.pending_question_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu madde bu oturumda sunulmadı",
        )

    sunulan = await service.fetch_question_detail(body.maddeId)
    if not sunulan:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yerleştirme sorusu getirilemedi",
        )

    # Şık harfi, İSTEMCİYE GÖNDERİLEN dizinin indeksinden türetilir (hizalama).
    harfler = _sunulan_harfler(sunulan.get("options") or {})
    harf = (
        harfler[body.secim]
        if body.secim is not None and 0 <= body.secim < len(harfler)
        else None
    )
    try:
        if harf is None:
            # "Emin değilim" → OMIT: madde UYGULANMAMIŞ sayılır, θ'ya girmez.
            # Yanlış (0) kodlamak dürüst belirsizliği kör tahminden ağır
            # cezalandırırdı (θ_true=+1.0, 6/12 omit → θ̂=-1.04 vs -0.56).
            sonuc = await service.skip_question(
                session_id=state.session_id,
                question_id=body.maddeId,
                max_items=PLACEMENT_MAX_ITEMS,
            )
        else:
            sonuc = await service.submit_answer(
                session_id=state.session_id,
                question_id=body.maddeId,
                is_correct=harf == str(sunulan.get("correct_option") or "").upper(),
                max_items=PLACEMENT_MAX_ITEMS,
                se_threshold=PLACEMENT_SE_STOP,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    guncel = await service.get_session_state(state.session_id)
    # Bitişte servis next_question=None döner; sözleşmede `item` opsiyonel
    # değil, o yüzden az önce cevaplanan maddeyi veririz (ekran done'da
    # kullanmaz). `sunulan` zaten elimizde — ek DB turu YOK.
    return _panel(
        guncel,
        sonuc.get("next_question") or sunulan,
        done=bool(sonuc["is_complete"]),
    )


# ── Yardımcı ──────────────────────────────────────────────────────


async def _check_answer(db, question_id: str, selected_option: str) -> bool:
    """DB'den doğru şıkkı çek, karşılaştır."""
    from sqlalchemy import text

    try:
        result = await db.execute(
            text(
                "SELECT correct_answer FROM question_bank WHERE id = :qid AND is_active = TRUE"
            ),
            {"qid": question_id},
        )
        row = result.fetchone()
        if not row:
            # Logla ama False dön — soru yoksa yanlış cevap say
            return False
        return row.correct_answer.upper() == selected_option.upper()
    except Exception as e:
        logger.error("CAT doğru cevap DB sorgusu HATASI q=%s: %s", question_id, e)
        return False
