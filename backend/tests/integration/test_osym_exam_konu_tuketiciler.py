"""Faz 1'in (da59ef871) ders->konu gocunun KIRDIGI tuketiciler + 2 testsiz dal.

----------------------------------------------------------------------------
NEDEN BU DOSYA VAR (olculdu — tahmin degil)
----------------------------------------------------------------------------
`da59ef871` `get_subject_performance`'in gruplama anahtarini `subject` ->
`(subject, primary_topic_id)` yapti. Motor+API ayagi olculdu ve gecti (kova
1 -> 13, sum(total_questions) 40 -> 40). AMA kova KARDINALITESI 1'den 13'e
ciktigi icin listeyi SAYAN/ETIKETLEYEN tuketiciler sessizce bozuldu:

  core/osym_exam_engine.py:2171  KonuPerformansi(konu=sp.subject)
  Canli olcum (oturum 5d2269fc-9f98-4666-9b2a-3d4960b68b80):
      konu_performanslari.konu : ['matematik'] x13
      zayif_konular            : ['matematik'] x11
      guclu_konular            : ['matematik'] x1   <- AYNI ders hem zayif hem guclu
      services/ogretmen_service.py:210 -> sinav_sayisi: 13  <- TEK sinav 13 sayiliyor

Degisiklikten ONCE (tek kova) bu ciktilar YAPISAL OLARAK IMKANSIZDI.

**Hicbir test yakalamadi** cunku `session_to_sinav_sonucu`'ya yapilan 4/4
referans `AsyncMock(return_value=None)`:
  tests/unit/test_api_coverage_final.py:455,470,485
  tests/unit/test_services_remaining_batch1.py:869
  tests/fast/test_api_coverage_batch14.py:1010,1025,1055,1072
Tuketici test paketleri regresyondan SONRA 58/58 YESIL kaldi. Bu yuzden bu
dosyada **AsyncMock YOK**: gercek Postgres, gercek motor, gercek servis.

----------------------------------------------------------------------------
TEK ISLEM (TRANSACTION) DISIPLINI — kalici yazim SIFIR
----------------------------------------------------------------------------
Kardes dosya (`test_osym_exam_konu_kirilimi.py`) fikstur satirlarini COMMIT
edip teardown'da DELETE ediyor (motor ayri baglanti kullandigi icin mecburdu).
Bu dosya bunun yerine motorun `get_db_session_context` adini fiksturun
**kendi AsyncSession'ina** yonlendirir. Sonuc: motor commit edilmemis satirlari
ayni islem icinde GORUR ve teardown tek `ROLLBACK` olur — DB'ye kalici tek bir
satir yazilmaz. T5 bu sayede `question_bank`'a dokunabilir (bkz. T5 docstring).

Bu bir davranis stub'i DEGIL, bir baglanti yonlendirmesidir: SQL, ORM
modelleri ve satirlar gercektir. Alet her kosumda `_dialect_postgres_mi` ile
dogrulanir — sessizce SQLite'a dusulemez.
"""

from __future__ import annotations

import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

# canli_maker/_dialect_postgres_mi TEK kaynakta kalsin (drift olmasin) diye
# kardes modulden alinir; pytest fikstur adini bu modulun namespace'inde gorur.
from tests.integration.test_osym_exam_konu_kirilimi import (  # noqa: F401
    _dialect_postgres_mi,
    canli_maker,
)

DERS = "MATEMATIK"

# Kapidan (mv_safe_for_beta) deterministik aday havuzu.
# `correct_answer` NULL/'' olan soru DISLANIR: motor cevabi metinsel
# karsilastirdigi icin NULL cevap "bos" sayilir ve %100 dogru kovasi
# kurulamaz (yanlis-RED uretirdi).
ADAY_SQL = text(
    """
    WITH aday AS (
        SELECT qb.id                                                  AS question_id,
               th.code                                                AS topic_code,
               th.name_tr                                             AS topic_name,
               row_number() OVER (PARTITION BY th.code ORDER BY qb.id) AS satir_no,
               count(*)     OVER (PARTITION BY th.code)                AS konu_soru
        FROM mv_safe_for_beta   m
        JOIN question_bank      qb ON qb.id = m.id
        JOIN topic_hierarchy    th ON th.id = qb.primary_topic_id
        JOIN question_metadata  qm ON qm.id = qb.id
        JOIN question_content   qc ON qc.id = qb.id
        WHERE qm.subject_area = :ders
          AND qc.correct_answer IS NOT NULL
          AND qc.correct_answer <> ''
    )
    SELECT question_id, topic_code, topic_name, satir_no
    FROM aday
    WHERE konu_soru >= :asgari
    ORDER BY topic_code, satir_no
    """
)

OTURUM_INSERT_SQL = text(
    """
    INSERT INTO exam_sessions
        (id, organization_id, student_id, exam_type, exam_name,
         total_questions, duration_minutes, status,
         current_question_index, time_spent_seconds,
         total_correct, total_wrong, total_empty, raw_score,
         estimated_ability, ability_confidence)
    VALUES
        (:sid, :org, :ogr, CAST('TYT' AS examtype), 'B3 tuketici bekcisi',
         :toplam, 40, 'completed', 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
    """
)

SORU_INSERT_SQL = text(
    "INSERT INTO exam_questions "
    "(id, exam_session_id, question_id, question_order) "
    "VALUES (gen_random_uuid()::text, :sid, :qid, :sira)"
)

# CAST(:dogru AS boolean): parametre tipi asyncpg'de 'unknown' kalmasin.
# `qc.id` (`:qid` DEGIL) SELECT listesinde: ayni parametre hem `varchar` kolona
# hem `qc.id = :qid` karsilastirmasina girince asyncpg
# `AmbiguousParameterError: inconsistent types deduced for parameter $2` verdi
# (olculdu, bu dosyanin ilk kosumu).
CEVAP_INSERT_SQL = text(
    """
    INSERT INTO student_answers
        (id, exam_session_id, question_id, selected_answer, is_correct,
         response_time_seconds, answer_changes, time_to_first_answer)
    SELECT gen_random_uuid()::text, :sid, qc.id,
           CASE WHEN CAST(:dogru AS boolean) THEN qc.correct_answer
                ELSE CASE WHEN qc.correct_answer = 'A' THEN 'B' ELSE 'A' END
           END,
           CAST(:dogru AS boolean), 12.0, 0, 12.0
    FROM question_content qc
    WHERE qc.id = :qid
    """
)


# ---------------------------------------------------------------------------
# Ortak kurulum
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def geri_alinan_oturum(canli_maker, monkeypatch):  # noqa: F811
    """Tek AsyncSession; hicbir sey COMMIT EDILMEZ, teardown = ROLLBACK.

    Motorun modul-global `get_db_session_context` adi bu ayni oturuma
    yonlendirilir, boylece motor commit edilmemis fikstur satirlarini gorur.
    """
    import core.osym_exam_engine as motor_modulu

    async with canli_maker() as db:
        assert _dialect_postgres_mi(db), (
            "Olcum aleti arizali: Postgres'e bagli DEGIL "
            f"(dialect={db.get_bind().dialect.name}). SQLite'a dusuldu."
        )

        @asynccontextmanager
        async def _paylasilan_kapi():
            yield db

        monkeypatch.setattr(motor_modulu, "get_db_session_context", _paylasilan_kapi)
        try:
            yield db
        finally:
            await db.rollback()


async def _konu_havuzu(db, asgari: int) -> dict[str, dict]:
    """topic_code -> {'topic_name': ..., 'question_ids': [...]} (deterministik)."""
    satirlar = (
        (await db.execute(ADAY_SQL, {"ders": DERS, "asgari": asgari})).mappings().all()
    )
    havuz: dict[str, dict] = {}
    for satir in satirlar:
        kayit = havuz.setdefault(
            satir["topic_code"],
            {"topic_name": satir["topic_name"], "question_ids": []},
        )
        kayit["question_ids"].append(satir["question_id"])
    return havuz


async def _sinav_kur(db, kovalar: list[dict]) -> dict:
    """Gercek exam_session + exam_questions + student_answers kurar (COMMIT YOK).

    `kovalar` sirasi = `question_order` sirasi. Motorun okuma sorgusu
    `ORDER BY ExamQuestion.question_order` oldugu icin bu sira dogrudan
    `subject_stats` sozlugunun EKLENME sirasini belirler — T4 bunu kullanir.
    """
    ogrenci = (
        await db.execute(
            text("SELECT id, organization_id FROM student_profiles ORDER BY id LIMIT 1")
        )
    ).first()
    if ogrenci is None:
        pytest.skip("student_profiles bos — exam_sessions FK'si karsilanamiyor")

    session_id = f"pytest-tuketici-{uuid.uuid4()}"
    tum_sorular = [(k, qid) for k in kovalar for qid in k["question_ids"]]

    await db.execute(
        OTURUM_INSERT_SQL,
        {
            "sid": session_id,
            "org": ogrenci.organization_id,
            "ogr": ogrenci.id,
            "toplam": len(tum_sorular),
        },
    )
    for sira, (kova, qid) in enumerate(tum_sorular, start=1):
        await db.execute(SORU_INSERT_SQL, {"sid": session_id, "qid": qid, "sira": sira})
        await db.execute(
            CEVAP_INSERT_SQL,
            {"sid": session_id, "qid": qid, "dogru": bool(kova["dogru"])},
        )

    dogru = sum(len(k["question_ids"]) for k in kovalar if k["dogru"])
    yanlis = len(tum_sorular) - dogru
    _oturumu_bellege_yaz(session_id, len(tum_sorular), dogru, yanlis)

    return {
        "session_id": session_id,
        "kovalar": kovalar,
        "toplam_soru": len(tum_sorular),
        "dogru": dogru,
        "yanlis": yanlis,
    }


def _oturumu_bellege_yaz(session_id: str, toplam: int, dogru: int, yanlis: int) -> str:
    """L1 (`active_sessions`) kaydi kurar ve sentetik `student_id` dondurur.

    `session_to_sinav_sonucu` -> `get_session_data` ONCE `active_sessions`'a
    bakar (core/osym_exam_engine.py:1074-1076), bulunca Redis'e HIC gitmez.
    Buraya konan nesneler GERCEK dataclass'lar (mock DEGIL).

    `student_id` sentetiktir: `get_student_exams` Redis'i de tarar ve baska
    kosumlardan kalmis ayni ogrenciye ait oturumlar sonucu kirletebilirdi.
    """
    from core.osym_exam_engine import (
        ExamPerformanceMetrics,
        ExamSessionData,
        ExamStatus,
        ExamType,
        OSYMExamConfig,
        osym_exam_engine,
    )

    ogrenci_id = f"pytest-ogr-{uuid.uuid4()}"
    baslangic = datetime.now() - timedelta(minutes=40)
    osym_exam_engine.active_sessions[session_id] = ExamSessionData(
        session_id=session_id,
        student_id=ogrenci_id,
        exam_config=OSYMExamConfig(
            exam_type=ExamType.TYT,
            total_questions=toplam,
            duration_minutes=40,
            subject_distribution={DERS: toplam},
        ),
        status=ExamStatus.COMPLETED,
        started_at=baslangic,
        completed_at=datetime.now(),
        performance_metrics=ExamPerformanceMetrics(
            total_questions=toplam,
            answered_questions=toplam,
            correct_answers=dogru,
            wrong_answers=yanlis,
            empty_answers=0,
            net_score=dogru - yanlis / 4,
            raw_score=float(dogru),
        ),
    )
    return ogrenci_id


@pytest_asyncio.fixture
async def tuketici_sinavi(geri_alinan_oturum):
    """5 KONU x 3 soru; 3 konu %100 dogru, 2 konu %100 yanlis.

    Basari yuzdeleri bilerek ucta tutulur: `zayif` (<50) ve `guclu` (>=70)
    listelerinin IKISI DE dolu olur, boylece T2'nin ayriklik iddiasi
    olculebilir hale gelir (bos kumede kendiliginden gecmez).
    """
    db = geri_alinan_oturum
    havuz = await _konu_havuzu(db, asgari=3)
    if len(havuz) < 5:
        pytest.skip(
            f"Kapida {DERS} dersinde >=3 soruluk 5 konu yok (bulunan={len(havuz)}). "
            "mv_safe_for_beta icerigi degismis olabilir."
        )

    kovalar = []
    for sira, kod in enumerate(sorted(havuz)[:5]):
        kovalar.append(
            {
                "topic_code": kod,
                "topic_name": havuz[kod]["topic_name"],
                "question_ids": havuz[kod]["question_ids"][:3],
                "dogru": sira % 2 == 0,
            }
        )

    veri = await _sinav_kur(db, kovalar)
    try:
        yield veri
    finally:
        from core.osym_exam_engine import osym_exam_engine

        osym_exam_engine.active_sessions.pop(veri["session_id"], None)


async def _sonucu_getir(session_id: str):
    from core.osym_exam_engine import session_to_sinav_sonucu

    return await session_to_sinav_sonucu(session_id)


def _bos_sonuc_uyarisi(veri: dict) -> str:
    return (
        "session_to_sinav_sonucu None dondu. Ya `get_session_data` L1 kaydini "
        "bulamadi ya da `get_subject_performance` icindeki ciplak "
        "`except Exception` (core/osym_exam_engine.py:1462) gercek hatayi yutup "
        f"`return []` yapti. session_id={veri['session_id']}, "
        f"kurulan soru={veri['toplam_soru']}"
    )


# ---------------------------------------------------------------------------
# T1 — konu etiketleri ayirt edilebilir olmali
# ---------------------------------------------------------------------------
async def test_konu_performanslari_ayirt_edilebilir_etiket_tasir(tuketici_sinavi):
    """Her `KonuPerformansi` kovasi AYIRT EDILEBILIR bir `konu` etiketi tasir.

    BUGUN KIRMIZI: core/osym_exam_engine.py:2171 `konu=sp.subject` — 5 kovanin
    5'i de 'matematik' etiketiyle donuyor. Kova sayisi 1 iken bu YAPISAL OLARAK
    mumkun degildi; ders->konu gocu bu kusuru URETTI.

    Kullanici karari (uygulanacak): `konu = sp.topic_name or sp.subject`.
    """
    veri = tuketici_sinavi
    sonuc = await _sonucu_getir(veri["session_id"])

    assert sonuc is not None, _bos_sonuc_uyarisi(veri)
    kovalar = sonuc.konu_performanslari
    assert kovalar, _bos_sonuc_uyarisi(veri)

    etiketler = [kp.konu for kp in kovalar]
    assert len(set(etiketler)) == len(kovalar), (
        f"{len(kovalar)} kova var ama yalnizca {len(set(etiketler))} farkli "
        f"etiket donuyor. Etiketler={etiketler}. "
        f"DB'de bu oturumda {len(veri['kovalar'])} farkli konu var: "
        f"{[k['topic_name'] for k in veri['kovalar']]}"
    )

    # KARSI-OLCUM: benzersizlik tek basina yanlis-pozitif verebilir (motor
    # kova basina 'matematik-1', 'matematik-2' uretse de gecerdi). Etiket
    # kumesi DB'deki konu ADLARIYLA birebir esit olmali.
    assert set(etiketler) == {k["topic_name"] for k in veri["kovalar"]}, (
        f"Etiket kumesi DB konu adlariyla eslesmiyor. "
        f"API={sorted(set(etiketler))}, DB={sorted(k['topic_name'] for k in veri['kovalar'])}"
    )


# ---------------------------------------------------------------------------
# T2 — zayif ve guclu listeleri AYRIK olmali
# ---------------------------------------------------------------------------
async def test_zayif_ve_guclu_konular_ayriktir(tuketici_sinavi):
    """MANTIKSAL INVARYANT: bir konu ayni anda hem zayif hem guclu OLAMAZ.

    BUGUN KIRMIZI: zayif/guclu listeleri `kp.konu` degerinden turuyor ve
    `kp.konu` her kovada 'matematik' oldugu icin kesisim {'matematik'}.
    Canli olcum: zayif ['matematik']x11, guclu ['matematik']x1.
    """
    veri = tuketici_sinavi
    sonuc = await _sonucu_getir(veri["session_id"])

    assert sonuc is not None, _bos_sonuc_uyarisi(veri)

    # Iddia olculebilir mi? Iki liste de dolu OLMALI (bos kumenin kesisimi
    # zaten bostur — S238: bos kumede bekciler XPASS verdi).
    assert sonuc.zayif_konular, (
        "Zayif liste bos — ayriklik iddiasi olculemez. "
        f"kova basarilari={[(kp.konu, kp.basari_yuzdesi) for kp in sonuc.konu_performanslari]}"
    )
    assert sonuc.guclu_konular, (
        "Guclu liste bos — ayriklik iddiasi olculemez. "
        f"kova basarilari={[(kp.konu, kp.basari_yuzdesi) for kp in sonuc.konu_performanslari]}"
    )

    kesisim = set(sonuc.zayif_konular) & set(sonuc.guclu_konular)
    assert kesisim == set(), (
        f"AYNI etiket hem zayif hem guclu: {sorted(kesisim)}. "
        f"zayif={sonuc.zayif_konular}, guclu={sonuc.guclu_konular}"
    )


# ---------------------------------------------------------------------------
# T3 — tek sinav TEK sinav sayilir
# ---------------------------------------------------------------------------
async def test_ogretmen_analizinde_tek_sinav_tek_sayilir(tuketici_sinavi):
    """`ogretmen_service.py:210` `sinav_sayisi` sismesi bekcisi.

    ONCE gercek `OgretmenServisi.ogrenci_detay_performans` KOSULUR (mock yok;
    `kullanici_servisi` ve `sinif_ogrenci_iliskileri` gercek in-memory
    nesnelerle doldurulur).

    OLCUM NOTU (yeniden kurulan tek satir): `sinav_sayisi` fonksiyonun
    DONUS SOZLUGUNDE YOK — yalnizca yerel `konu_performanslari` dict'inde
    yasiyor (services/ogretmen_service.py:196-210). Bu yuzden degeri
    `Counter(kp.konu for kp in sonuc.konu_performanslari)` ile yeniden
    kuruyorum; bu, :210'daki `sinav_sayisi += 1` satirinin TEK sinav icin
    birebir esdegeridir (dongu her `konu_perf` icin bir kez artiriyor).
    Ikinci (yeniden kurulmayan) assert donus sozlugunun `konu_performanslari`
    anahtar sayisini olcer — ayni kok nedenin gercek gozlemlenebiliri.

    BUGUN KIRMIZI: 5 kovanin 5'i 'matematik' -> sinav_sayisi=5, tek anahtar.
    """
    from models import KullaniciRolu, SinavTipi
    from models.user import Kullanici, OgrenciProfili
    from services.ogretmen_service import OgretmenServisi
    from services.user_service import kullanici_servisi

    veri = tuketici_sinavi
    sonuc = await _sonucu_getir(veri["session_id"])
    assert sonuc is not None, _bos_sonuc_uyarisi(veri)

    ogrenci_id = sonuc.ogrenci_id
    kullanici_id = f"pytest-kul-{uuid.uuid4()}"
    ogretmen_id = f"pytest-ogt-{uuid.uuid4()}"

    kullanici_servisi.kullanicilar[kullanici_id] = Kullanici(
        id=kullanici_id,
        email="b3.bekci@example.com",
        ad_soyad="B3 Bekci",
        rol=KullaniciRolu.OGRENCI,
    )
    kullanici_servisi.ogrenci_profilleri[ogrenci_id] = OgrenciProfili(
        ogrenci_id=ogrenci_id,
        kullanici_id=kullanici_id,
        sinif_seviyesi=12,
        hedef_sinav=SinavTipi.TYT,
    )
    servis = OgretmenServisi()
    servis.sinif_ogrenci_iliskileri[ogretmen_id] = [ogrenci_id]

    try:
        analiz = await servis.ogrenci_detay_performans(ogretmen_id, ogrenci_id)
    finally:
        kullanici_servisi.kullanicilar.pop(kullanici_id, None)
        kullanici_servisi.ogrenci_profilleri.pop(ogrenci_id, None)

    assert analiz["genel_istatistikler"]["toplam_sinav"] == 1, (
        "Fikstur TEK sinav kurdu ama servis "
        f"{analiz['genel_istatistikler']['toplam_sinav']} sinav gordu — "
        "olcum aleti arizali (Redis'ten sizan oturum?)."
    )

    sinav_sayilari = Counter(kp.konu for kp in sonuc.konu_performanslari)
    sismis = {konu: n for konu, n in sinav_sayilari.items() if n != 1}
    assert sismis == {}, (
        "TEK sinav birden cok kez sayiliyor (ogretmen_service.py:210 "
        f"`sinav_sayisi += 1`): {sismis}. Kova sayisi={len(sonuc.konu_performanslari)}, "
        f"etiketler={[kp.konu for kp in sonuc.konu_performanslari]}"
    )

    assert len(analiz["konu_performanslari"]) == len(veri["kovalar"]), (
        f"Ogretmen analizi {len(analiz['konu_performanslari'])} konu anahtari "
        f"donduruyor, DB'de {len(veri['kovalar'])} konu var. "
        f"anahtarlar={sorted(analiz['konu_performanslari'])}"
    )


# ---------------------------------------------------------------------------
# T4 — siralama bekcisi (mutasyon M2'yi oldurur)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def ters_sirali_sinav(geri_alinan_oturum):
    """Kovalari BEKLENEN CIKTININ TAM TERSI sirada ekler + BERABERLIK icerir.

    NEDEN boyle kuruluyor: Faz 1'de `subject_performances.sort(...)` blogu
    (core/osym_exam_engine.py:1463-1465) tamamen SILINDIGINDE 631 test
    **0 fail** verdi. Sebep, mevcut fiksturun tesaduefen zaten azalan sirada
    olmasiydi. Bu fikstur o tesaduefu ORTADAN KALDIRIR: siralama satiri
    silinirse cikti kesinlikle artan sirali olur.

    Kova buyuklukleri: 3, 3, 2, 2, 1 -> iki BERABERLIK ciftinde tie-break
    (`topic_name`) yuk tasir; tie-break kaldirilirsa stabil siralama
    ekleme sirasini korur ve beklenen sira TUTMAZ.
    """
    db = geri_alinan_oturum
    havuz = await _konu_havuzu(db, asgari=3)
    if len(havuz) < 5:
        pytest.skip(
            f"Kapida {DERS} dersinde >=3 soruluk 5 konu yok (bulunan={len(havuz)})."
        )

    # Adlara gore (Unicode kod-noktasi) sirali 5 konu: n0 < n1 < n2 < n3 < n4
    secilen = sorted(havuz)[:5]
    ada_gore = sorted(secilen, key=lambda kod: havuz[kod]["topic_name"])
    n0, n1, n2, n3, n4 = ada_gore

    # Beklenen cikti: (-total_questions, topic_name)
    #   3'luk cift {n0, n2} -> n0, n2   |   2'lik cift {n1, n3} -> n1, n3   |   n4
    beklenen = [(n0, 3), (n2, 3), (n1, 2), (n3, 2), (n4, 1)]
    ekleme_sirasi = list(reversed(beklenen))  # n4, n3, n1, n2, n0

    kovalar = [
        {
            "topic_code": kod,
            "topic_name": havuz[kod]["topic_name"],
            "question_ids": havuz[kod]["question_ids"][:adet],
            "dogru": True,
        }
        for kod, adet in ekleme_sirasi
    ]

    veri = await _sinav_kur(db, kovalar)
    veri["beklenen_sira"] = [(havuz[kod]["topic_name"], adet) for kod, adet in beklenen]
    try:
        yield veri
    finally:
        from core.osym_exam_engine import osym_exam_engine

        osym_exam_engine.active_sessions.pop(veri["session_id"], None)


async def _performansi_getir(session_id: str):
    from core.osym_exam_engine import OSYMExamEngine

    return await OSYMExamEngine().get_subject_performance(session_id)


async def test_kovalar_azalan_sirali_ve_tie_break_deterministik(ters_sirali_sinav):
    """Kovalar `total_questions` AZALAN, esitlikte `topic_name` artan sirali.

    TIE-BREAK NOTU (olculdu, faz 1 curutucusu): sira Turkce alfabetik DEGIL,
    Python'un varsayilan **Unicode kod-noktasi** siralamasidir — 'C' (U+00C7)
    ve 'U' (U+00DC) TUM ASCII harflerden SONRA gelir, yani "Carpanlara Ayirma"
    Turkce alfabede basta olmasina ragmen bu siralamada SONA duser. Test
    GERCEK davranisa gore yazildi (`sorted(...)` ile ayni anahtar), tasarim
    tercihine gore degil.

    Bu test `subject_performances.sort(...)` blogunu OLDURMEK icin var:
    ekleme sirasi beklenen ciktinin tam tersidir (bkz. fikstur).
    """
    veri = ters_sirali_sinav
    perf = await _performansi_getir(veri["session_id"])

    assert perf, (
        "Motor bos liste dondu — siralama iddiasi olculemez. "
        f"session_id={veri['session_id']}"
    )
    assert (
        len(perf) >= 2
    ), f"Siralama iddiasi olculemez: {len(perf)} kova donuyor (>=2 gerekli)."

    gercek = [(p.topic_name, p.total_questions) for p in perf]
    assert gercek == veri["beklenen_sira"], (
        "Kovalar (-total_questions, topic_name) sirasinda DEGIL.\n"
        f"  beklenen : {veri['beklenen_sira']}\n"
        f"  gercek   : {gercek}\n"
        "Not: ekleme sirasi beklenenin TERSI kuruldu; siralama satiri "
        "silinirse bu assert dusmek ZORUNDA."
    )

    # Beraberlik gercekten var mi? (yoksa tie-break iddiasi bos kumede geciyor)
    sayilar = [adet for _, adet in gercek]
    assert len(sayilar) != len(
        set(sayilar)
    ), f"Beraberlik yok — tie-break iddiasi olculmedi. sayilar={sayilar}"

    # DETERMINIZM: ayni girdi iki kez islenince ayni sira gelmeli.
    ikinci = await _performansi_getir(veri["session_id"])
    assert [(p.topic_name, p.total_questions) for p in ikinci] == gercek, (
        "Ayni oturum iki kez islenince FARKLI sira dondu (tie-break "
        f"deterministik degil). 1={gercek}, 2={[(p.topic_name, p.total_questions) for p in ikinci]}"
    )


# ---------------------------------------------------------------------------
# T5 — "Konu atanmamis" dali (mutasyon M4'u oldurur)
# ---------------------------------------------------------------------------
KONUSUZ_TOPIC_INSERT_SQL = text(
    """
    INSERT INTO topic_hierarchy
        (id, level, code, name_tr, osym_relevance, osym_frequency,
         total_questions, average_difficulty, is_active, subject_area)
    VALUES (:tid, 2, :kod, '', 0.5, 0, 0, 0.5, true, :ders)
    """
)


@pytest_asyncio.fixture
async def adsiz_konulu_sinav(geri_alinan_oturum, canli_maker):  # noqa: F811
    """Bir soruyu, `name_tr` degeri FALSY olan bir konuya baglar (islem icinde).

    ------------------------------------------------------------------
    SECILEN YAKLASIM: (b)'nin tek uygulanabilir varyanti — islem icinde
    yaz, ROLLBACK et. Uc secenegin UCU DE olculdu:
    ------------------------------------------------------------------
    (a) Saf yardimciya besle — YAPILAMAZ. Gruplama/etiketleme mantigi
        `get_subject_performance` govdesinde SATIR ICI
        (core/osym_exam_engine.py:1393-1402); disaridan cagrilabilir bir
        yardimci YOK ve bu gorevde uretim koduna dokunmak yasak.

    (c) `topic_hierarchy`'de karsiligi olmayan `primary_topic_id` — IMKANSIZ:
        `question_bank_primary_topic_id_fkey FOREIGN KEY (primary_topic_id)
        REFERENCES topic_hierarchy(id)`, `convalidated = t` (pg_constraint).

    (b) `primary_topic_id = NULL` — **BU DA IMKANSIZ**, ilk kosumda olculdu:
            asyncpg.exceptions.NotNullViolationError: null value in column
            "primary_topic_id" of relation "question_bank"
        `information_schema.columns.is_nullable = 'NO'`.

    ------------------------------------------------------------------
    OLCUMUN SONUCU: `topic_name IS NULL` dali SEMA ITIBARIYLA ERISILEMEZ
    ------------------------------------------------------------------
    Uretimdeki yorum "Konu satiri yoksa" diyor ama outerjoin'in kacirmasi
    icin ya `question_bank.primary_topic_id` NULL olmali (NOT NULL) ya da
    sarkan olmali (FK). Ikisi de yasak. `topic_hierarchy.name_tr` de
    NOT NULL (`topic_hierarchy_name_tr_not_null`).

    Geriye `or` operatorunun korudugu falsy sinifin ERISILEBILIR tek uyesi
    kaliyor: **bos dize**. `name_tr = ''` uzerinde CHECK kisiti YOK
    (pg_constraint'te yalniz `check_osym_relevance` ve `check_topic_level`),
    yani bu deger bugun bu semaya girebilir. Dal `'' or "Konu atanmamis"`
    ile GERCEKTEN uyarilir; M4 mutasyonu (`topic_name or subject`) altinda
    ayni girdi 'matematik' uretir ve test duser.

    KALICI YAZIM YOK: bu dosyanin tum fiksturleri tek, commit edilmemis
    islemde calisir ve testin sonunda ROLLBACK edilir. Test geri alimi
    BAGIMSIZ bir baglantiyla dogrular — "geri aldim" bir iddiadir
    (.claude/rules/verification.md).
    """
    db = geri_alinan_oturum
    havuz = await _konu_havuzu(db, asgari=3)
    if len(havuz) < 2:
        pytest.skip(f"Kapida {DERS} dersinde >=3 soruluk 2 konu yok ({len(havuz)}).")

    kovalar = [
        {
            "topic_code": kod,
            "topic_name": havuz[kod]["topic_name"],
            "question_ids": havuz[kod]["question_ids"][:3],
            "dogru": True,
        }
        for kod in sorted(havuz)[:2]
    ]
    veri = await _sinav_kur(db, kovalar)

    adsiz_tid = f"pytest-topic-{uuid.uuid4()}"
    adsiz_kod = f"PYTEST.ADSIZ.{uuid.uuid4().hex[:8]}"
    await db.execute(
        KONUSUZ_TOPIC_INSERT_SQL,
        {"tid": adsiz_tid, "kod": adsiz_kod, "ders": DERS},
    )

    hedef_qid = kovalar[0]["question_ids"][0]
    onceki = (
        await db.execute(
            text("SELECT primary_topic_id FROM question_bank WHERE id = :qid"),
            {"qid": hedef_qid},
        )
    ).scalar_one()
    await db.execute(
        text("UPDATE question_bank SET primary_topic_id = :tid WHERE id = :qid"),
        {"tid": adsiz_tid, "qid": hedef_qid},
    )
    # Ham SQL UPDATE ORM kimlik haritasini gecersiz KILMAZ; sonraki
    # select(Question) bayat nesne dondurebilirdi.
    db.expunge_all()

    veri.update(
        {
            "hedef_qid": hedef_qid,
            "onceki_topic_id": onceki,
            "adsiz_tid": adsiz_tid,
            "adsiz_kod": adsiz_kod,
            "canli_maker": canli_maker,
        }
    )
    try:
        yield veri
    finally:
        from core.osym_exam_engine import osym_exam_engine

        osym_exam_engine.active_sessions.pop(veri["session_id"], None)


async def test_adsiz_konu_gorunur_konu_atanmamis_kovasinda(
    adsiz_konulu_sinav, geri_alinan_oturum
):
    """Falsy `topic_name` -> gorunur "Konu atanmamis"; DERS ADINA DUSULMEZ.

    Faz 1'de bu dalin bekcisi HER KOSUMDA SKIPPED idi
    (tests/integration/test_osym_exam_konu_kirilimi.py:398): DB'de
    `primary_topic_id IS NULL` satiri 0 idi ve — sonradan olculdu — o sutun
    zaten NOT NULL oldugu icin O SAYI HICBIR ZAMAN ARTAMAZ. SKIP kapsam
    DEGILDIR; bu test dali gercekten uyarir.

    Mutasyon M4 (`topic_name or "Konu atanmamis"` -> `topic_name or subject`,
    core/osym_exam_engine.py:1400) faz 1'de 31 passed / 1 skipped / 0 fail
    vermisti. Bu assert onu oldurur: mutasyonla etiket 'matematik' olur.
    """
    veri = adsiz_konulu_sinav
    perf = await _performansi_getir(veri["session_id"])

    assert perf, f"Motor bos liste dondu. session_id={veri['session_id']}"

    adsiz = [p for p in perf if p.topic_code == veri["adsiz_kod"]]
    assert len(adsiz) == 1, (
        "Adi bos olan konu icin TAM 1 gorunur kova bekleniyordu, "
        f"{len(adsiz)} bulundu. kovalar="
        f"{[(p.subject, p.topic_code, p.topic_name, p.total_questions) for p in perf]}"
    )
    kova = adsiz[0]
    assert kova.topic_name == "Konu atanmamis", (
        "Adi cozulemeyen kovanin etiketi 'Konu atanmamis' olmali; sessiz "
        f"varsayilan (ders adi) YASAK. Bulunan={kova.topic_name!r}, "
        f"subject={kova.subject!r}"
    )
    assert (
        kova.total_questions == 1
    ), f"Adsiz konulu kovada 1 soru bekleniyordu, {kova.total_questions} var."

    # Soru DUSMEDI: toplam korunur (outerjoin invaryanti).
    assert sum(p.total_questions for p in perf) == veri["toplam_soru"], (
        f"Kova toplamlari {sum(p.total_questions for p in perf)}, "
        f"oturumun soru sayisi {veri['toplam_soru']}."
    )

    # GERI ALIM BIR IDDIADIR — bagimsiz baglantiyla dogrula.
    await geri_alinan_oturum.rollback()
    async with veri["canli_maker"]() as taze:
        simdiki = (
            await taze.execute(
                text("SELECT primary_topic_id FROM question_bank WHERE id = :qid"),
                {"qid": veri["hedef_qid"]},
            )
        ).scalar_one()
        sentetik_konu = (
            await taze.execute(
                text("SELECT count(*) FROM topic_hierarchy WHERE id = :tid"),
                {"tid": veri["adsiz_tid"]},
            )
        ).scalar_one()

    assert simdiki == veri["onceki_topic_id"], (
        "ROLLBACK sonrasi question_bank satiri ESKI HALINE DONMEDI! "
        f"qid={veri['hedef_qid']}, once={veri['onceki_topic_id']}, simdi={simdiki}"
    )
    assert sentetik_konu == 0, (
        "ROLLBACK sonrasi sentetik topic_hierarchy satiri DB'de KALDI: "
        f"{veri['adsiz_tid']}"
    )


# --------------------------------------------------------------------------
# T6 — B3 FAZ 3: uretici ders kimligini de tasir
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_konu_performanslari_ders_kimligi_de_tasir(tuketici_sinavi):
    """`konu` KONU adi, `ders` DERS kimligi -- ikisi ayri alanda.

    FAZ 2 `konu`yu konu adina cevirdi ama ders kimligi HICBIR yerde
    tasinmiyordu; tuketiciler dizeyi ders sanmak zorunda kaldi. Bu test
    kimligin uretici katmaninda gercekten dolduruldugunu civiler.
    """
    sonuc = await _sonucu_getir(tuketici_sinavi["session_id"])
    assert sonuc is not None, _bos_sonuc_uyarisi(tuketici_sinavi)

    kovalar = sonuc.konu_performanslari
    assert kovalar, "kova yok -- fikstur kurulmamis"

    # Her kova ders kimligi tasir ve hepsi AYNI ders (fikstur tek ders kurar).
    dersler = {kp.ders for kp in kovalar}
    assert dersler == {
        DERS.lower()
    }, f"ders kimligi eksik/yanlis: {dersler} (beklenen {{'{DERS.lower()}'}})"

    # Konu kodu dolu ve BENZERSIZ -- ayirt edici anahtar budur.
    kodlar = [kp.konu_kodu for kp in kovalar]
    assert all(kodlar), f"konu_kodu bos olan kova var: {kodlar}"
    assert len(set(kodlar)) == len(kodlar), f"konu_kodu tekrar ediyor: {kodlar}"

    # Kimlik `konu` dizesinden BAGIMSIZ olmali. Onceki bicim
    # (`assert kp.ders is not None`) onceki iki assert tarafindan zaten
    # KAPSANIYORDU -- tek basina hicbir mutasyonu olduremezdi. Yerine
    # ayirt edici invaryant konuldu: `konu` DEGISKEN, `ders` SABIT.
    # `ders=sp.topic_name` gibi bir yanlis kablolama bu assert'i dusurur,
    # eskisini dusurmezdi.
    assert len({kp.konu for kp in kovalar}) > 1, (
        f"konu tek degerli -- fikstur cok konulu kurulmamis: "
        f"{[kp.konu for kp in kovalar]}"
    )
    assert len({kp.ders for kp in kovalar}) == 1, (
        f"ders degisken -- konu alanina kablolanmis olabilir: "
        f"{[(kp.konu, kp.ders) for kp in kovalar]}"
    )
