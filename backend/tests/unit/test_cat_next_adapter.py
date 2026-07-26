"""
G4-B — POST /api/v1/cat/next adaptör testleri.

İki katman:
  1. Saf IRT türevleri (irt_engine) — panel alanlarının psikometrik tabanı.
  2. HTTP adaptörü (app/api/cat.py) — frontend sözleşmesiyle BİREBİR parite.

Sözleşme kaynağı: frontend/src/kiro/api/api-client.ts:356-396 (CatNextArgs/CatNextResult)
Tüketici:         frontend/src/kiro/screens/AdaptifTestPage.tsx

Redis/DB YOK — get_cat_service tek DI dikişi olarak override edilir
(app/api/cat.py:43 get_cat_service; get_redis'i override etmek yetmez çünkü
None gelince gerçek aioredis istemcisi kurmayı dener — cat.py:46-58).
"""

from __future__ import annotations

import math

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.services import irt_engine as ie
from app.services.cat_session import CATState


@pytest.fixture(autouse=True)
def _limiter_kapali():
    """slowapi limiter'ı Redis-destekli (core/ddos_protection.py:70 storage_uri).

    Birim testler Redis'siz çalışır; açık bırakılırsa her istek bağlantı
    denemesinde takılır. Sınırın KENDİSİ üretimde aktif kalır.
    """
    from core.ddos_protection import limiter

    onceki = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = onceki


# ---------------------------------------------------------------------------
# 1. Saf IRT türevleri
# ---------------------------------------------------------------------------


def test_theta_percentile_monoton_azalan_ve_ortalama_50():
    """Üst yüzde θ arttıkça küçülür; θ=0 (ortalama öğrenci) → üst %50."""
    assert ie.theta_percentile(0.0) == 50
    assert ie.theta_percentile(1.0) < ie.theta_percentile(0.0)
    assert ie.theta_percentile(-1.0) > ie.theta_percentile(0.0)


def test_theta_percentile_uc_degerlerde_1_99_araliginda_kalir():
    """Ekran '≈ üst %{topPct}' basar (AdaptifTestPage.tsx:260) — %0 anlamsız olur."""
    assert ie.theta_percentile(4.0) >= 1
    assert ie.theta_percentile(-4.0) <= 99


def test_marginal_reliability_se_ile_duser():
    """guvenilirlik = 100·(1 - SE²) — klasik marjinal güvenilirlik."""
    assert ie.marginal_reliability(1.0) == 0
    assert ie.marginal_reliability(0.45) == 80
    assert ie.marginal_reliability(0.0) == 100


def test_marginal_reliability_se_1den_buyukse_negatife_dusmez():
    """Prior SE=1.0 üstü ilk maddelerde görülebilir; ekran '%-24' basmamalı."""
    assert ie.marginal_reliability(1.5) == 0


def test_expected_net_theta_ile_monoton_artar():
    """netTahmini = TYT Mat 40 soruda beklenen net (D - Y/4)."""
    dusuk = ie.expected_net(-1.0)
    orta = ie.expected_net(0.0)
    yuksek = ie.expected_net(1.0)
    assert dusuk < orta < yuksek
    assert dusuk >= 0 and yuksek <= 40


def test_expected_net_negatif_donmez():
    """Çok düşük θ'da D - Y/4 negatife gider; ekran '~-3 net' basmamalı."""
    assert ie.expected_net(-4.0) >= 0


def test_items_to_target_se_hedefe_ulasmissa_sifir():
    assert (
        ie.items_to_target_se(se=0.40, theta=0.0, item_params=[], target_se=0.45) == 0
    )


def test_items_to_target_se_butceyle_sinirli():
    """Bu havuzda SE 0.45'e 12 maddede ulaşılamaz — 'kalan' bütçeyi aşmamalı."""
    kalan = ie.items_to_target_se(
        se=0.95, theta=0.0, item_params=[], target_se=0.45, remaining_budget=3
    )
    assert 0 <= kalan <= 3


def test_replay_theta_history_son_eleman_tam_eap_ile_ayni():
    """uygulananlar[] her maddeden sonraki θ/SE'yi ister — prefix replay deterministik."""
    items = [
        ie.ItemParams(question_id="q1", a=1.0, b=-0.5, c=0.20),
        ie.ItemParams(question_id="q2", a=1.1, b=0.0, c=0.20),
        ie.ItemParams(question_id="q3", a=0.9, b=0.5, c=0.20),
    ]
    responses = [1, 0, 1]
    gecmis = ie.replay_theta_history(responses, items)
    tam = ie.eap_update(responses, items)

    assert len(gecmis) == 3
    assert math.isclose(gecmis[-1].theta, tam.theta, abs_tol=1e-9)
    assert math.isclose(gecmis[-1].se, tam.se, abs_tol=1e-9)


def test_replay_theta_history_bos_yanitta_bos_liste():
    assert ie.replay_theta_history([], []) == []


def test_ability_band_sadece_uc_kanonik_deger_uretir():
    """AdaptifTestPage.tsx:37-41 SEVIYE sözlüğünde fallback YOK — dördüncü değer TypeError."""
    for theta in (-4.0, -0.31, -0.3, 0.0, 0.49, 0.5, 4.0):
        assert ie.ability_band(theta) in {"zayif", "orta", "guclu"}
    assert ie.ability_band(-1.0) == "zayif"
    assert ie.ability_band(0.0) == "orta"
    assert ie.ability_band(1.0) == "guclu"


# ---------------------------------------------------------------------------
# 2. HTTP adaptörü — sahte servis
# ---------------------------------------------------------------------------

_SORULAR = {
    "q-1": {
        "question_id": "q-1",
        "stem": "12 + 8 × 2 işleminin sonucu kaçtır?",
        "options": {"A": "40", "B": "28", "C": "20", "D": "32", "E": "36"},
        "correct_option": "B",
        "konu": "İşlem Önceliği",
        "topic_id": "t-1",
        "subject_id": "MATEMATIK",
        "irt": {"difficulty": -1.2, "discrimination": 1.0, "guessing": 0.20},
    },
    "q-2": {
        "question_id": "q-2",
        "stem": "x² - 5x + 6 = 0 denkleminin kökleri toplamı kaçtır?",
        "options": {"A": "2", "B": "3", "C": "5", "D": "6", "E": "1"},
        "correct_option": "C",
        "konu": "Denklemler",
        "topic_id": "t-2",
        "subject_id": "MATEMATIK",
        "irt": {"difficulty": 0.4, "discrimination": 1.05, "guessing": 0.20},
    },
}


class _FakeCatService:
    """CATSessionService'in adaptörün dokunduğu yüzeyi. Redis/DB yok."""

    def __init__(self) -> None:
        self.db = None  # _check_answer testte monkeypatch'lenir
        self.states: dict[str, CATState] = {}
        self.start_cagrilari: list[dict] = []
        self.submit_cagrilari: list[dict] = []
        self.skip_cagrilari: list[dict] = []
        self._sayac = 0

    async def get_session_state(self, session_id: str) -> CATState | None:
        return self.states.get(session_id)

    async def fetch_question_detail(self, question_id: str) -> dict | None:
        return _SORULAR.get(question_id)

    async def start_session(self, **kw) -> dict:
        self.start_cagrilari.append(kw)
        self._sayac += 1
        sid = f"oturum-{self._sayac}"
        self.states[sid] = CATState(
            session_id=sid,
            user_id=kw["user_id"],
            subject_id=kw["subject_id"],
            theta=0.0,
            se=1.0,
            is_guest=kw.get("is_guest", False),
            pending_question_id="q-1",
        )
        return {
            "session_id": sid,
            "question": _SORULAR["q-1"],
            "theta": 0.0,
            "se": 1.0,
            "n_questions": 0,
            "phase": "warm_up",
            "is_complete": False,
        }

    async def skip_question(self, **kw) -> dict:
        """Omit: θ'ya girmez, bütçeden düşer, tekrar sunulmaz."""
        self.skip_cagrilari.append(kw)
        st = self.states[kw["session_id"]]
        st.answered_ids.append(kw["question_id"])
        st.skipped_ids.append(kw["question_id"])
        sunulan = st.n_questions + len(st.skipped_ids)
        bitti = sunulan >= kw.get("max_items", 12)
        st.state = "completed" if bitti else st.state
        st.pending_question_id = "" if bitti else "q-2"
        return {
            "is_complete": bitti,
            "theta": st.theta,
            "se": st.se,
            "n_questions": st.n_questions,
            "termination_reason": "max_questions" if bitti else None,
            "next_question": None if bitti else _SORULAR["q-2"],
            "phase": "completed" if bitti else "core",
        }

    async def submit_answer(self, **kw) -> dict:
        self.submit_cagrilari.append(kw)
        st = self.states[kw["session_id"]]
        st.answered_ids.append(kw["question_id"])
        st.responses.append(1 if kw["is_correct"] else 0)
        st.item_params.append(
            {"question_id": kw["question_id"], "a": 1.0, "b": -1.2, "c": 0.20}
        )
        st.n_questions += 1
        st.theta, st.se = 0.35, 0.80
        bitti = st.n_questions >= kw.get("max_items", 12)
        st.state = "completed" if bitti else st.state
        st.pending_question_id = "" if bitti else "q-2"
        return {
            "is_complete": bitti,
            "theta": st.theta,
            "se": st.se,
            "n_questions": st.n_questions,
            "termination_reason": "max_questions" if bitti else None,
            "next_question": None if bitti else _SORULAR["q-2"],
            "phase": "completed" if bitti else "core",
            "feedback": {"is_correct": kw["is_correct"], "correct_option": "B"},
        }


@pytest.fixture
def istemci(monkeypatch):
    """İzole FastAPI + cat router; get_cat_service ve get_optional_user override.

    ENVIRONMENT=development: aksi halde cat_sid çerezi Secure işaretlenir ve
    httpx onu http://testserver'a geri göndermez (oturum turlayamaz).
    """
    monkeypatch.setenv("ENVIRONMENT", "development")
    from app.api.cat import get_cat_service, get_optional_user, router

    app = FastAPI()
    app.include_router(router)
    servis = _FakeCatService()
    app.dependency_overrides[get_cat_service] = lambda: servis
    app.dependency_overrides[get_optional_user] = lambda: None  # misafir

    async def _dogru_mu(db, question_id, secilen_harf):
        soru = _SORULAR.get(question_id)
        return bool(soru and soru["correct_option"] == secilen_harf)

    import app.api.cat as cat_modul

    orijinal = cat_modul._check_answer
    cat_modul._check_answer = _dogru_mu
    try:
        with TestClient(app) as c:
            c._servis = servis
            yield c
    finally:
        cat_modul._check_answer = orijinal
        app.dependency_overrides.clear()


def test_ilk_cagri_sozlesmedeki_tum_alanlari_doner(istemci):
    """CatNextResult'ın 11 alanı da dolu gelmeli — ekran hepsini render ediyor."""
    r = istemci.post("/api/v1/cat/next", json={"madde": 0})
    assert r.status_code == 200, r.text
    g = r.json()
    for alan in (
        "item",
        "theta",
        "se",
        "done",
        "seviye",
        "topPct",
        "netTahmini",
        "madde",
        "kalanTahmini",
        "guvenilirlik",
        "uygulananlar",
    ):
        assert alan in g, f"sözleşme alanı eksik: {alan}"


def test_ilk_cagri_bos_oturum_durumu(istemci):
    g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
    assert g["madde"] == 0
    assert g["uygulananlar"] == []
    assert g["done"] is False


def test_item_dogru_sikki_sizdirmaz(istemci):
    """Omit<CatItem,'dogru'> — doğru şık yanıttan ÖNCE istemciye inemez."""
    g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
    assert set(g["item"]) == {"id", "b", "konu", "soru", "secenekler"}
    ham = istemci.post("/api/v1/cat/next", json={"madde": 0}).text
    assert "correct_option" not in ham
    assert '"dogru"' not in ham


def test_item_secenekler_harf_sirasinda_duz_liste(istemci):
    """secim = secenekler dizisinin 0-tabanlı indeksi (AdaptifTestPage.tsx:183)."""
    g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
    assert g["item"]["secenekler"] == ["40", "28", "20", "32", "36"]
    assert g["item"]["konu"] == "İşlem Önceliği"


def test_seviye_sadece_kanonik_uc_degerden_biri(istemci):
    g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
    assert g["seviye"] in {"zayif", "orta", "guclu"}


def test_ilk_cagri_cat_sid_cerezi_birakir(istemci):
    """Oturum kimliği HttpOnly çerezle taşınır — sözleşme birebir korunur."""
    r = istemci.post("/api/v1/cat/next", json={"madde": 0})
    assert "cat_sid" in r.cookies or "cat_sid" in istemci.cookies


def test_secim_indeksi_harfe_cevrilir_ve_dogru_sayilir(istemci):
    """secim=1 → 'B' → q-1'in doğru şıkkı → is_correct=True servise gitmeli."""
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    istemci.post("/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": 1})
    assert istemci._servis.submit_cagrilari[-1]["is_correct"] is True


def test_yanlis_secim_indeksi_yanlis_sayilir(istemci):
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    istemci.post("/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": 0})
    assert istemci._servis.submit_cagrilari[-1]["is_correct"] is False


def test_secim_null_omit_thetaya_yazilmaz(istemci):
    """'Emin değilim' = UYGULANMADI; θ'ya yanlış yanıt olarak GİRMEZ.

    Yanlış saymak dürüst belirsizliği kör tahminden ağır cezalandırıyordu
    (θ_true=+1.0, 6/12 omit → θ̂=-1.04; kör tahminde -0.56).
    """
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    g = istemci.post(
        "/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": None}
    ).json()
    assert istemci._servis.submit_cagrilari == [], "omit EAP'ye yanıt olarak girdi"
    assert istemci._servis.skip_cagrilari[-1]["question_id"] == "q-1"
    assert g["uygulananlar"] == [], "atlanan madde uygulanmış gibi panele düştü"


def test_omit_ayni_maddeyi_tekrar_sunmaz_ve_butceden_duser(istemci):
    """Atlanan madde yeniden sorulmaz ama 12 madde bütçesinden düşer."""
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    g = istemci.post(
        "/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": None}
    ).json()
    assert g["item"]["id"] != "q-1"
    assert g["kalanTahmini"] <= 11


def test_tamamen_omit_edilen_oturum_prior_dondurur(istemci):
    """12/12 'Emin değilim' → sıfır bilgi: θ prior'da, güvenilirlik %0."""
    from app.api.cat import PLACEMENT_MAX_ITEMS

    istemci.post("/api/v1/cat/next", json={"madde": 0})
    g = None
    for i in range(PLACEMENT_MAX_ITEMS):
        sid = next(iter(istemci._servis.states))
        madde_id = istemci._servis.states[sid].pending_question_id
        g = istemci.post(
            "/api/v1/cat/next",
            json={"madde": i + 1, "maddeId": madde_id, "secim": None},
        ).json()
    assert g["theta"] == 0.0, "sıfır bilgiden θ üretildi"
    assert g["guvenilirlik"] == 0, "sıfır bilgiye güvenilirlik atandı"
    assert g["done"] is True


def test_cevap_sonrasi_uygulananlar_dolar(istemci):
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    g = istemci.post(
        "/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": 1}
    ).json()
    assert g["madde"] == 1
    assert len(g["uygulananlar"]) == 1
    u = g["uygulananlar"][0]
    assert set(u) == {"b", "ok", "theta", "se"}
    assert u["ok"] is True


def test_misafir_oturumu_db_persist_etmez(istemci):
    """Misafir user_id gerçek bir users satırı değil — FK/RLS yazımı denenmemeli."""
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    kw = istemci._servis.start_cagrilari[-1]
    assert kw["is_guest"] is True
    assert kw["user_id"].startswith("guest:")


def test_yerlestirme_butcesi_12_madde_ile_sinirli(istemci):
    """Kullanıcı kararı: 12 madde + SE≤0.45 (panelin θ SVG'si de 12 maddeye çizili)."""
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    istemci.post("/api/v1/cat/next", json={"madde": 1, "maddeId": "q-1", "secim": 1})
    kw = istemci._servis.submit_cagrilari[-1]
    assert kw["max_items"] == 12
    assert kw["se_threshold"] == pytest.approx(0.45)


def test_bitisde_item_yine_dolu_ve_kalan_sifir(istemci):
    """CatNextResult.item opsiyonel DEĞİL; done=true'da da tip sağlanmalı."""
    from app.api.cat import PLACEMENT_MAX_ITEMS

    istemci.post("/api/v1/cat/next", json={"madde": 0})
    g = None
    for i in range(PLACEMENT_MAX_ITEMS):
        g = istemci.post(
            "/api/v1/cat/next",
            json={"madde": i + 1, "maddeId": "q-1" if i == 0 else "q-2", "secim": 1},
        ).json()
    assert g["done"] is True
    assert g["kalanTahmini"] == 0
    assert g["item"]["id"]


def test_bilinmeyen_oturum_kimligi_yeni_oturum_baslatir(istemci):
    """Süresi dolmuş çerez/oturumId ekranı kilitlememeli — sessizce yeniden başlar."""
    r = istemci.post(
        "/api/v1/cat/next", json={"madde": 0, "oturumId": "olmayan-oturum"}
    )
    assert r.status_code == 200
    assert len(istemci._servis.start_cagrilari) == 1


def test_yabanci_madde_id_cevap_anahtari_oracle_acmaz(istemci):
    """P0: istemci hangi sorunun puanlanacağını SEÇEMEZ.

    Aksi halde auth'suz uç, ~4 istekte bir sorunun cevabını sızdıran bir
    oracle'a döner: yanıttaki uygulananlar[].ok doğru/yanlış bilgisini verir.
    """
    istemci.post("/api/v1/cat/next", json={"madde": 0})  # sunucu q-1 sundu
    for k in range(5):
        r = istemci.post(
            "/api/v1/cat/next", json={"madde": 1, "maddeId": "q-2", "secim": k}
        )
        assert r.status_code == 409, f"secim={k} için oracle açık: {r.status_code}"
    assert istemci._servis.submit_cagrilari == []


def test_sunulan_madde_disinda_puanlama_yok(istemci):
    """Sunucunun sunduğu madde cevaplanabilir; başkası 409."""
    g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
    sunulan = g["item"]["id"]
    ok = istemci.post(
        "/api/v1/cat/next", json={"madde": 1, "maddeId": sunulan, "secim": 1}
    )
    assert ok.status_code == 200
    assert istemci._servis.submit_cagrilari[-1]["question_id"] == sunulan


def test_secim_indeksi_bos_sikli_soruda_kaymaz(istemci):
    """P1: boş şık elenince A..E sabit dizisiyle hizalama bozulurdu.

    q-3'te option_B boş → istemciye [A,C,D,E] gider. secim=1 ekranda 'B'
    etiketli ama GERÇEKTE option_C'dir; doğru cevap C olduğu için ok=True olmalı.
    """
    servis = istemci._servis
    _SORULAR["q-3"] = {
        "question_id": "q-3",
        "stem": "Boş şıklı soru",
        "options": {"A": "bir", "B": "", "C": "uc", "D": "dort", "E": "bes"},
        "correct_option": "C",
        "konu": "Kenar Durum",
        "topic_id": "t-3",
        "subject_id": "MATEMATIK",
        "irt": {"difficulty": 0.0, "discrimination": 1.0, "guessing": 0.20},
    }
    try:
        g = istemci.post("/api/v1/cat/next", json={"madde": 0}).json()
        sid = next(iter(servis.states))
        servis.states[sid].pending_question_id = "q-3"
        g = istemci.post(
            "/api/v1/cat/next", json={"madde": 1, "maddeId": "q-3", "secim": 1}
        ).json()
        assert g["uygulananlar"][-1]["ok"] is True, "boş şık indeks kaymasına yol açtı"
    finally:
        _SORULAR.pop("q-3", None)


def test_misafir_kimligi_yenilemede_korunur(istemci):
    """P0: her çağrıda yeni guest:<uuid> üretmek oturum sızıntısı yaratır.

    cat:active:{user_id}:{subject} anahtarı user_id'ye bağlı; kimlik değişirse
    önceki oturum hiç kapatılmaz ve her yenilemede 1 saatlik oturum birikir.
    """
    istemci.post("/api/v1/cat/next", json={"madde": 0})
    istemci.post("/api/v1/cat/next", json={"madde": 0})  # sayfa yenileme
    kimlikler = {kw["user_id"] for kw in istemci._servis.start_cagrilari}
    assert len(istemci._servis.start_cagrilari) == 2
    assert len(kimlikler) == 1, f"misafir kimliği değişti: {kimlikler}"


def test_gecersiz_token_sessizce_misafire_dusurulmez():
    """P1: kimlik SUNULDUYSA ama geçersizse 401 dönmeli (istemcinin tek /login yolu)."""
    from app.api.cat import get_optional_user

    app = FastAPI()

    @app.get("/probe")
    async def probe(u=Depends(get_optional_user)):
        return {"misafir": u is None}

    with TestClient(app) as c:
        assert c.get("/probe").json()["misafir"] is True  # kimlik YOK → misafir
        r = c.get("/probe", headers={"Authorization": "Bearer bozuk.token.degeri"})
        assert r.status_code == 401, (
            f"geçersiz token misafire düşürüldü: {r.status_code}"
        )


def test_cerez_uretimde_httponly_secure_lax(monkeypatch):
    """cat_sid oturum kimliği taşır: prod'da HttpOnly + Secure + SameSite=Lax."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.api.cat import (
        CAT_SID_COOKIE_PATH,
        get_cat_service,
        get_optional_user,
        router,
    )

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cat_service] = lambda: _FakeCatService()
    app.dependency_overrides[get_optional_user] = lambda: None

    with TestClient(app) as c:
        ham = c.post("/api/v1/cat/next", json={"madde": 0}).headers["set-cookie"]

    assert "cat_sid=" in ham
    assert "HttpOnly" in ham
    assert "Secure" in ham
    assert "SameSite=lax" in ham.replace("samesite", "SameSite")
    assert f"Path={CAT_SID_COOKIE_PATH}" in ham


def test_baskasinin_oturumu_devralinamaz(istemci):
    """Sahiplik ihlali: çerez başka bir kullanıcının oturumuna işaret ediyorsa devralma YOK."""
    servis = istemci._servis
    servis.states["yabanci"] = CATState(
        session_id="yabanci", user_id="kurban-123", subject_id="MATEMATIK"
    )
    r = istemci.post(
        "/api/v1/cat/next",
        json={"madde": 1, "maddeId": "q-1", "secim": 1, "oturumId": "yabanci"},
    )
    assert r.status_code == 200
    assert servis.submit_cagrilari == []  # yabancı oturuma yazılmadı
    assert len(servis.start_cagrilari) == 1  # yerine yeni oturum açıldı
