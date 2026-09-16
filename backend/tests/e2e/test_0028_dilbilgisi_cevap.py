"""0028_dilbilgisi_cevap migration'inin koruma testleri.

Canli DB istemez; migration modulunu okur, yani CI'da da kosar.

1. ZINCIR ve ASCII.
2. KAPSAM: tam iki satir, ikisi de eski hattin satiri (yeni ithal
   satirlari DOKUNULMAZ), id'ler ve hash'ler bicim olarak gecerli.
3. UC KATLI KORUMA: sorgu id VE soru_hash ile secer, upgrade mevcut
   cevabi beklenen ESKI degerle karsilastirir ve tutmazsa ATLAR.
   MUTASYON KARSILIGI: korumayi kaldiran bir surum testi dusurur.
4. GERI ALINABILIRLIK: gunluk kurulur, downgrade onceki cevabi geri
   koyar, eklenen metadata anahtarini siler, gunlugu dusurur.
5. DURUSTLUK: metadata'ya soru_cozulmedi=true yazilir; migration
   question_bank/question_metadata'nin baska hicbir alanina dokunmaz.
6. VERI TUTARLILIGI: eski ve yeni cevap farklidir, ikisi de A-E'dir.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

GOC_YOLU = KOK / "alembic" / "versions" / "0028_dilbilgisi_cevap_duzeltme.py"


def _modul():
    spec = importlib.util.spec_from_file_location("goc_0028", GOC_YOLU)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def goc():
    return _modul()


@pytest.fixture(scope="module")
def kaynak_metni() -> str:
    return GOC_YOLU.read_text(encoding="utf-8")


# --- 1. ZINCIR ---------------------------------------------------------


def test_revizyon_zinciri(goc) -> None:
    assert goc.revision == "0028_dilbilgisi_cevap"
    assert goc.down_revision == "0027_dilbilgisi_beta"


def test_revizyon_adi_sinirlarin_icinde(goc) -> None:
    assert len(goc.revision) <= 32
    assert len(goc.GUNLUK) <= 63


def test_dosya_ascii() -> None:
    ham = GOC_YOLU.read_bytes()
    kusurlu = [i for i, b in enumerate(ham) if b > 127]
    assert not kusurlu, f"ASCII disi bayt: {kusurlu[:5]}"


# --- 2. KAPSAM ---------------------------------------------------------


def test_tam_iki_satir_hedefleniyor(goc) -> None:
    assert len(goc.DUZELTMELER) == 2
    idler = [d[0] for d in goc.DUZELTMELER]
    assert len(set(idler)) == 2


def test_idler_ve_hashler_bicimsel_olarak_gecerli(goc) -> None:
    for sid, shash, _, _, _ in goc.DUZELTMELER:
        uuid.UUID(sid)  # bicim bozuksa burada patlar
        assert re.fullmatch(r"[0-9a-f]{32}", shash), shash


def test_serit_kaynaklari_sayfa_ve_soru_belirtiyor(goc) -> None:
    kaynaklar = [d[4] for d in goc.DUZELTMELER]
    assert all(k.startswith("basili_cevap_seridi_s") for k in kaynaklar)
    assert all(re.search(r"_soru\d+$", k) for k in kaynaklar)
    assert len(set(kaynaklar)) == 2


# --- 3. UC KATLI KORUMA (mutasyon karsiligi) ---------------------------


def test_secim_sorgusu_hem_id_hem_hash_ariyor(goc) -> None:
    sql = goc._SEC_SQL
    assert "qc.id = :id" in sql
    assert "qb.soru_hash = :hash" in sql


def _koruma_var_mi(kod: str) -> bool:
    """upgrade() mevcut cevabi beklenenle karsilastirip atliyor mu?"""
    return "if mevcut != eski:" in kod and "continue" in kod


def test_upgrade_beklenmeyen_cevabi_atliyor(kaynak_metni: str) -> None:
    ust = kaynak_metni.split("def upgrade")[1].split("def downgrade")[0]
    assert _koruma_var_mi(ust)
    assert "mevcut is None" in ust


def test_mutasyon_korumasiz_surum_testi_dusurur() -> None:
    bozuk = (
        "    for sid, shash, eski, yeni, kaynak in DUZELTMELER:\n"
        "        b.execute(...)\n"
    )
    assert _koruma_var_mi(bozuk) is False


# --- 4. GERI ALINABILIRLIK ---------------------------------------------


def test_gunluk_kuruluyor_ve_dusuruluyor(kaynak_metni: str) -> None:
    assert "op.create_table(" in kaynak_metni
    alt = kaynak_metni.split("def downgrade")[1]
    assert "op.drop_table(GUNLUK)" in alt
    assert "onceki_cevap" in alt


def test_downgrade_metadata_anahtarini_siliyor(kaynak_metni: str) -> None:
    alt = kaynak_metni.split("def downgrade")[1]
    assert "pipeline_metadata::jsonb - :a" in alt
    assert "META_ANAHTARI" in alt


def test_meta_anahtari_revizyonla_ayni_numarayi_tasiyor(goc) -> None:
    assert goc.META_ANAHTARI.endswith("0028")


# --- 5. DURUSTLUK ------------------------------------------------------


def test_soru_cozulmedi_isareti_yaziliyor(goc) -> None:
    metin = str(goc._META_EKLE)
    assert "'soru_cozulmedi', true" in metin
    assert "'okuma_sayisi', 3" in metin


def test_yalniz_correct_answer_degisiyor(kaynak_metni: str) -> None:
    """question_content'te baska bir sutuna, question_bank'e hic dokunulmaz."""
    kod = kaynak_metni.split('"""', 2)[2]
    guncellemeler = re.findall(r"UPDATE (\w+) SET (\w+)", kod)
    assert set(guncellemeler) <= {
        ("question_content", "correct_answer"),
        ("question_metadata", "pipeline_metadata"),
    }, guncellemeler
    assert "is_active" not in kod
    assert "is_public" not in kod
    assert "review_status" not in kod


# --- 6. VERI TUTARLILIGI -----------------------------------------------


def test_eski_ve_yeni_cevaplar_farkli_ve_gecerli(goc) -> None:
    for sid, _, eski, yeni, _ in goc.DUZELTMELER:
        assert eski in "ABCDE", sid
        assert yeni in "ABCDE", sid
        assert eski != yeni, sid


def test_bilinen_iki_duzeltme_aynen_duruyor(goc) -> None:
    """Olcum sonucu capa olarak yazilir; sessizce degistirilemez."""
    ozet = {(d[0][:8], d[2], d[3]) for d in goc.DUZELTMELER}
    assert ozet == {("58238cd6", "A", "B"), ("e0afeff6", "C", "E")}
