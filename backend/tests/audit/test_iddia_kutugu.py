"""İddia kütüğü bekçisi — denetim disiplinini ZORLAYICI yapar.

NEDEN VAR
---------
`.claude/rules/audit-methodology.md` ve `docs/research/2026-08-12_claude_code_
opus5_arastirma_raporu.md` §D.1/#4 aynı şeyi söylüyor:

    "CLAUDE.md tavsiyedir; hook/test zorlamadır."

`docs/audits/2026-08-12_25uzman/iddialar.yaml` bir kural seti beyan ediyor
(durum != beklemede -> kanıt ZORUNLU, uygulandi -> commit + test ZORUNLU).
Bu dosya olmadan o beyan yalnızca yorum satırıdır ve sessizce ihlal edilir.

Bu testler tam olarak §C.1.12'deki `think` aracı gibi çalışır: hiçbir şey
"yapmazlar", yalnız yapısal bir boşluğu kapatırlar — kanıtsız durum değişikliği
merge edilemez.

MUTASYONLA ÇİVİLENDİ (12 Ağu 2026):
  M1: bir kaydın `kanit`ini null yap + durum=dogrulandi -> test_kanitsiz_durum FAIL ✓
  M2: `severity_iddia`yı "P9" yap                      -> test_severity_gecerli FAIL ✓
  M3: iki kayda aynı id ver                            -> test_id_benzersiz FAIL ✓
  M4: durum="uygulandi" + commit=null                  -> test_uygulandi_commit FAIL ✓
  M5: stakes cümlesini değiştir                        -> test_stakes_sabit FAIL ✓
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML yok")

KUTUK = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "audits"
    / "2026-08-12_25uzman"
    / "iddialar.yaml"
)

GECERLI_DURUM = {"beklemede", "dogrulandi", "fantom", "abartili", "uygulandi"}
GECERLI_SEVERITY = {"P0", "P1", "P2", "P3", "yok"}

# Rapor §C.6.1: yargıç promptundaki "stakes" bir ÖLÇÜM DEĞİŞKENİDİR.
# Aynı transkript, yalnız bu cümle değişince %85,6 <-> %16,7 yanlış etiketlendi.
# Bu yüzden cümle sabittir ve testle çivilenmiştir.
STAKES_CEKIRDEK = "kimse cezalandırılmaz"


def _yukle() -> tuple[dict, list[dict]]:
    if not KUTUK.exists():
        pytest.skip(f"kütük yok: {KUTUK}")
    ham = yaml.safe_load(KUTUK.read_text(encoding="utf-8"))
    assert isinstance(ham, dict), "kütük kökü mapping olmalı (meta + iddialar)"
    meta = ham.get("meta") or {}
    kayitlar = ham.get("iddialar") or []
    assert isinstance(kayitlar, list), "iddialar bir liste olmalı"
    for oge in kayitlar:
        assert isinstance(oge, dict), f"iddia dict değil: {oge!r}"
    return meta, kayitlar


@pytest.fixture(scope="module")
def kutuk():
    return _yukle()


def test_kutuk_ayristirilabilir(kutuk):
    meta, kayitlar = kutuk
    assert kayitlar, "kütükte hiç iddia yok"
    assert meta, "meta bloğu yok"


def test_id_benzersiz(kutuk):
    _, kayitlar = kutuk
    idler = [k["id"] for k in kayitlar]
    tekrar = {i for i in idler if idler.count(i) > 1}
    assert not tekrar, f"tekrarlanan id: {sorted(tekrar)}"


def test_zorunlu_alanlar(kutuk):
    _, kayitlar = kutuk
    zorunlu = ("id", "uzman", "ankraj", "iddia", "severity_iddia", "durum")
    eksikler = [
        (k.get("id", "<idsiz>"), a) for k in kayitlar for a in zorunlu if a not in k
    ]
    assert not eksikler, f"eksik zorunlu alan: {eksikler}"


def test_durum_gecerli(kutuk):
    _, kayitlar = kutuk
    hatali = [
        (k["id"], k["durum"]) for k in kayitlar if k["durum"] not in GECERLI_DURUM
    ]
    assert not hatali, f"geçersiz durum: {hatali} (izinli: {sorted(GECERLI_DURUM)})"


def test_severity_gecerli(kutuk):
    _, kayitlar = kutuk
    hatali = [
        (k["id"], k["severity_iddia"])
        for k in kayitlar
        if k["severity_iddia"] not in GECERLI_SEVERITY
    ]
    assert not hatali, f"geçersiz severity_iddia: {hatali}"

    hatali_olculen = [
        (k["id"], k["severity_olculen"])
        for k in kayitlar
        if k.get("severity_olculen") is not None
        and k["severity_olculen"] not in GECERLI_SEVERITY
    ]
    assert not hatali_olculen, f"geçersiz severity_olculen: {hatali_olculen}"


def test_kanitsiz_durum_yasak(kutuk):
    """ASIL BEKÇİ: 'beklemede' dışına çıkan her iddia KANIT taşımalı.

    Bu, 23 May 2026 meta-denetiminde 18 P0'ın %87'sinin fantom çıkmasının
    yapısal panzehiridir. Kanıtsız 'dogrulandi' yazmak artık merge edilemez.
    """
    _, kayitlar = kutuk
    ihlal = [
        k["id"]
        for k in kayitlar
        if k["durum"] != "beklemede" and not (k.get("kanit") or "").strip()
    ]
    assert not ihlal, (
        f"durum != beklemede ama kanit BOŞ: {ihlal}. "
        "audit-methodology.md: 'Varsayım ≠ Ölçüm'. Kanıt yapıştırılmadan durum değişmez."
    )


def test_uygulandi_commit_ve_test_ister(kutuk):
    """'uygulandi' demek: commit VAR ve o fix'i koruyan test VAR."""
    _, kayitlar = kutuk
    ihlal = [
        k["id"]
        for k in kayitlar
        if k["durum"] == "uygulandi"
        and (
            not (k.get("commit") or "").strip()
            or not (k.get("zorlayici_test") or "").strip()
        )
    ]
    assert not ihlal, (
        f"durum=uygulandi ama commit/zorlayici_test eksik: {ihlal}. "
        "Fix'i koruyan test yoksa fix regresyona açıktır."
    )


def test_severity_farki_gerekce_ister(kutuk):
    """severity_olculen != severity_iddia ise NEDEN yazılmalı.

    audit-methodology.md 28 Tem 2026: 'SEVERITY DE BİR ÖLÇÜMDÜR.'
    Sessizce severity düşürmek, bulguyu gömmenin kolay yoludur.
    """
    _, kayitlar = kutuk
    ihlal = []
    for k in kayitlar:
        olculen = k.get("severity_olculen")
        if olculen is None or olculen == k["severity_iddia"]:
            continue
        gerekce = " ".join(
            str(k.get(a) or "")
            for a in ("kanit", "degerlendirme", "on_bulgu", "curutme_sorusu")
        )
        if len(gerekce.strip()) < 40:
            ihlal.append(k["id"])
    assert not ihlal, f"severity değişti ama gerekçe yok/kısa: {ihlal}"


def test_stakes_sabit(kutuk):
    """Yargıç stakes dili değiştirilemez — o bir ölçüm değişkenidir (§C.6.1)."""
    meta, _ = kutuk
    metin = str(meta.get("yargic_stakes_dili", ""))
    assert STAKES_CEKIRDEK in metin, (
        "meta.yargic_stakes_dili değişmiş. Rapor §C.6.1: aynı transkript, yalnız "
        "sonuç dili değişince %85,6 <-> %16,7 yanlış etiketlendi. Bu cümle SABİTTİR."
    )


def test_ankraj_dosyalari_var(kutuk):
    """Ankraj dosyası yoksa iddia zaten fantomdur — ilk ucuz filtre."""
    # KUTUK = <depo>/docs/audits/<tarih>/iddialar.yaml  ->  parents[3] = <depo>
    depo = KUTUK.resolve().parents[3]
    assert (depo / ".claude").is_dir(), f"depo koku yanlis cozuldu: {depo}"

    kayip = []
    for k in kutuk[1]:
        for parca in str(k["ankraj"]).replace("+", " ").split():
            yol = parca.split(":")[0].strip("(),")
            if "{" in yol:  # brace expansion -> tek dosya degil, atla
                continue
            if "/" not in yol or not yol.endswith(
                (".py", ".ts", ".tsx", ".css", ".json", ".yaml", ".yml")
            ):
                continue
            if not (depo / yol).exists():
                kayip.append((k["id"], yol))
    assert not kayip, (
        f"ankraj dosyası bulunamadı: {kayip}. Dosya yoksa iddia FANTOM'dur — "
        "durumu 'fantom' yap ve kanıta bu listeyi yaz."
    )
