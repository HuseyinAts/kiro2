"""ES senkron sorgusunun SPLIT sonrasi semaya vurdugunu civiler (#433).

NEDEN VAR
---------
`core/es_index_schema.SORGU` S210'un 69-alan split'inden (`0fd9b8413`) ONCEKI
semayi varsayiyordu:

    SELECT q.question_text, q.option_a, ... FROM question_bank q

Split sonrasi `question_bank`ta 12 kolon var; digerleri yavru tablolara tasindi.
Sonuc: senkron HER kosumda `asyncpg.UndefinedColumnError` ile dusuyordu ve canli
index **0 dokuman** kaldi. 20 Agu 2026'da olculdu:

    turkiye_sinav_platform_v20260731        0 dokuman   <- alias BURAYA bakiyor
    turkiye_sinav_platform_yedek_20260731  64.270 dok   <- bayat, correct_answer ICERIYOR

NEDEN AST TARAYICISI GOREMEDI
-----------------------------
`scripts/scan_split_accesses.py` AST tabanli; kolon adlari burada bir STRING
LITERAL icinde (f-string ile kuruluyor) ve string icinde `Attribute` dugumu
yoktur. `test_split_migration_cat_session.py` ayni sinifi belgeliyor.
Bu yuzden bekci SORGUYU KOSTURUR — metnini okumakla yetinmez.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.asyncio

# Her ALANLAR uyesinin HANGI tabloda yasadigi. Split sonrasi canli
# `information_schema` ile dogrulandi (20 Agu 2026).
ALAN_TABLO = {
    "id": "question_bank",
    "primary_topic_id": "question_bank",
    "question_text": "question_content",
    "option_a": "question_content",
    "option_b": "question_content",
    "option_c": "question_content",
    "option_d": "question_content",
    "option_e": "question_content",
    "subject_area": "question_metadata",
    "exam_type": "question_metadata",
    "grade_level": "question_metadata",
    "osym_year": "question_metadata",
    "source_book": "question_metadata",
    "bloom_level": "question_metadata",
    "word_count": "question_metadata",
    "difficulty_level": "question_statistics",
    "irt_difficulty": "question_statistics",
    "quality_score": "question_statistics",
}


def test_alan_tablo_haritasi_alanlari_tam_kapsar() -> None:
    """Harita ile `ALANLAR` ayrisirsa bu bekci sessizce eksik olcer."""
    from core.es_index_schema import ALANLAR

    assert set(ALANLAR) == set(ALAN_TABLO), (
        f"ALANLAR ile harita ayrismis: fazla={set(ALANLAR) - set(ALAN_TABLO)} "
        f"eksik={set(ALAN_TABLO) - set(ALANLAR)}"
    )


async def test_sorgu_canli_semaya_karsi_kosuyor(live_db) -> None:
    """ASIL BEKCI: sorgu metnini okumak yetmez, KOSTUR.

    Split kacagi tam olarak burada yakalanir; metinsel kontrol
    `q.question_text` gorup "var" derdi.
    """
    from core.es_index_schema import SORGU

    satirlar = (await live_db.execute(text(SORGU))).mappings().all()
    kapi = (
        await live_db.execute(text("SELECT count(*) FROM mv_safe_for_beta"))
    ).scalar_one()
    assert len(satirlar) == kapi, (
        f"sorgu {len(satirlar)} satir dondurdu, kapida {kapi} var — "
        "JOIN kaybi veya fazlasi"
    )


async def test_sorgu_yasakli_alan_secmiyor(live_db) -> None:
    """`correct_answer`/`explanation`/`is_active` ES'e SIZAMAZ.

    `_belge_kur` bunu ayrica kontrol ediyor ama kontrol VERIYE bakiyor;
    burada SORGUNUN kendisi olculuyor — iki katman.
    """
    from core.es_index_schema import SORGU, YASAKLI_ALANLAR

    satirlar = (await live_db.execute(text(SORGU))).mappings().all()
    if not satirlar:
        pytest.skip("Kapi BOS — bu bekci hicbir sey olcemez (alet arizasi)")
    sizan = YASAKLI_ALANLAR & set(satirlar[0].keys())
    assert not sizan, f"Yasakli alan sorguda: {sorted(sizan)}"


async def test_belge_kur_gercek_satirla_calisiyor(live_db) -> None:
    """Saf donusum GERCEK satirla; sentetik sozlukle test yaniltici olurdu."""
    from core.es_index_schema import SORGU, _belge_kur

    satirlar = (await live_db.execute(text(SORGU))).mappings().all()
    if not satirlar:
        pytest.skip("Kapi BOS — bu bekci hicbir sey olcemez (alet arizasi)")
    doc_id, belge = _belge_kur(dict(satirlar[0]))
    assert doc_id, "bos doc_id — ES otomatik id uretir, cop dokuman birikir"
    assert belge.get("question_text"), "question_text BOS — JOIN kopmus olabilir"


@pytest.mark.skipif(
    not os.environ.get("KIRO2_ES_URL") and not os.environ.get("ELASTICSEARCH_URL"),
    reason="ES adresi verilmedi",
)
async def test_bayat_yedek_index_correct_answer_tasimiyor() -> None:
    """Bayat `_yedek_` index'i silinene kadar bu bekci KIRMIZI kalir.

    64.270 dokuman `correct_answer` iceriyor ve silinen satirlara ait.
    ES 127.0.0.1'e bagli (olculdu) — LAN'a acik degil, ama yine de artik.
    """
    import httpx

    url = os.environ.get("KIRO2_ES_URL") or os.environ["ELASTICSEARCH_URL"]
    # ALET ONARIMI (28 Agu 2026): bu bekci ES'e KIMLIK GONDERMIYORDU.
    # ES 401 + `{"error": {...}}` donuyor, kod `[i["index"] for i in r.json()]`
    # yaziyor ve sozlukte gezinip `TypeError: string indices must be integers`
    # veriyordu. Yani bekci 'bayat index yok' DEMIYOR, HICBIR SEY OLCMUYORDU --
    # ve push kapisini bu ANLASILMAZ hatayla blokluyordu.
    kullanici = os.environ.get("ELASTICSEARCH_USER")
    parola = os.environ.get("ELASTICSEARCH_PASSWORD")
    kimlik = (kullanici, parola) if kullanici and parola else None

    async with httpx.AsyncClient(timeout=10, auth=kimlik) as c:
        r = await c.get(f"{url}/_cat/indices?h=index&format=json")

    if r.status_code in (401, 403):
        # OLCEMEDIM != TEMIZ. Kimlik test ortaminda yok (backend/.env yalniz
        # URL tasiyor; kullanici/parola konteyner env'inde). Skip bunu GORUNUR
        # kilar; 'gecti' demek yalan olurdu.
        pytest.skip(
            f"ES kimlik dogrulamasi gerekiyor (HTTP {r.status_code}) ve "
            "ELASTICSEARCH_USER/ELASTICSEARCH_PASSWORD test ortaminda YOK -> "
            "bayat index OLCULEMEDI. Konteynerden olcum (28 Agu 2026): "
            "5 index, 'yedek' iceren YOK."
        )

    assert r.status_code == 200, (
        f"ES _cat/indices {r.status_code}: {r.text[:200]}. Bu bir BULGU degil "
        "ALET ARIZASI -- bekci olcum yapamadi."
    )
    govde = r.json()
    assert isinstance(govde, list), (
        f"_cat/indices liste bekleniyordu, {type(govde).__name__} geldi: "
        f"{str(govde)[:200]}"
    )
    adlar = [i["index"] for i in govde]
    bayat = [a for a in adlar if "yedek" in a.lower()]
    assert not bayat, f"Bayat index hala duruyor (cevap anahtari tasiyor): {bayat}"
