# MAT/TYT Göçü — REVİZE Uygulama Planı (S239)

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: `superpowers:subagent-driven-development`
> (önerilen) veya `superpowers:executing-plans`. Adımlar `- [ ]` kutucuğuyla izlenir.

**Hedef:** ~600 MAT/TYT sorusunu canlı `kiro2`'ye göçürmek; **her crop kör okunmuş**,
sızdıran **silinmiş** olacak. A1 kabul kriterinin içerik ayağını ilk kez gerçek
veriyle koşulabilir yapmak.

**Mimari:** Y11 hattının üç saf katmanı korunuyor — dönüşüm (`y11_goc.py`, DB'siz),
yazma (`y11_yukleyici.py`, tek transaction), aday seçimi. İlk ikisi KIMYA'da
kanıtlandı (3.616 satır, `44cb08a04`). Bu plan yalnız **aday seçiciyi** ekler ve
sızıntıyı **kitap katmanında değil crop katmanında** ele alır.

**Teknoloji:** Python 3.13 · asyncpg · PostgreSQL 18.1 (5434, `postgres` trust) ·
pytest · pre-commit (kapı ruff **0.7.1**, yerel 0.14.13 — farklı sürümler)

---

## ⚠️ Bu plan, öncekinin (2026-08-20-mat-tyt-goc.md) İKİ TASK'INI İPTAL EDER

| Eski | Durum | Gerekçe |
|---|---|---|
| **T2** `SIZINTILI_KITAPLAR` frozenset | 🔴 **İPTAL** | MAT-T1 ölçtü: 59 kitap / 354 crop kör okundu → 9 sızıntı (**%2,54**). Kitap sinyali **yok**: hepsi aynı orandaysa ≥1 görülen kitap beklentisi 8,4, gözlenen 9 → örneklem gürültüsü. Eşik (`>=2/6`) yapısal olarak sıfır üretiyordu (olasılık %0,91). **Kitap kümesi yanlış katman.** |
| **T1** kitap-başı örneklem | ✅ kapandı | `496` |

**Doğru katman crop-başı.** OCR yok ve kurulmayacak (kullanıcı kararı, 20 Ağu:
*"ocr yok çok vakit kaybı oluyor"*). OCR'siz istatistiksel dedektör de **kör**
ölçüldü (KÖTÜ medyan 0,0690 < İYİ 0,0829, fark −0,0139). Geriye tek geçerli
yöntem kalıyor: **crop'u gözle oku.** O yüzden dilim, okunabilir bir boyuta
indiriliyor — 5.420 değil **600**.

**Sızdıran kurtarılmaz, ATILIR** (kullanıcı kararı). Kırpma/yeniden üretme yok.

---

## Ölçülmüş başlangıç durumu (20 Ağu 2026, S238 silmesi SONRASI)

| | Değer | Not |
|---|---|---|
| Canlı `question_bank` | **3.616** ×4 | S238'de 36.967 sentetik satır silindi |
| Canlı kapı `mv_safe_for_beta` | **0** | kasıtlı; yeni parti de `pending` girecek |
| Canlı `topic_hierarchy` | **45** kod (`MAT.*` = 21) | `f74a09bf5` seed'i |
| MAT/TYT temiz dilim (`kiro2_temp`) | **5.420** / 99 kitap / 43 kod | süzgeç aşağıda |
| → canlı konuda **karşılığı VAR** | **4.549** | göç edilebilir taban |
| → kapsam **DIŞI** | **871** | ⚠️ eski plan **386** diyordu — **BAYAT**. Önceden elenmezse yükleyici `ValueError` ile **tümden durur** |
| ≥60 soruluk kapsanan konu | **19** | 12 konu × 50 = 600 rahat karşılanıyor |
| SIKI kimlik (gövde+şık) fazlalık | **0** | KIMYA'daki 16'nın karşılığı yok |
| Çapraz-DB çakışma (#504) | **0** | canlı saf KIMYA, aday saf MAT |
| Crop sızıntı oranı | **%2,54** (9/354) | MAT-T1, kör okuma |

**Temiz dilim süzgeci** (plan boyunca değişmez):

```sql
exam_type = 'TYT' AND subject_area = 'MATEMATIK'
AND quality_review_status = 'auto_judged_high' AND is_active
AND question_image_url ~ '_q[0-9]+\.png$'     -- _PAGE crop'lari DISARIDA
AND correct_answer IN ('A','B','C','D','E')
AND option_e IS NOT NULL AND btrim(option_e) <> ''
```

`_PAGE` süzgeci **zorunlu**: MAT/TYT görsellerinin %40-45'i tam sayfa crop ve
komşu soruları + basılı cevap anahtarını sızdırıyor (B4'te ölçüldü). Bu süzgeç
sızıntının **büyük** kısmını zaten kesiyor; kalan %2,54 onun ARTIĞI.

---

## Dosya yapısı

| Dosya | Sorumluluk | Durum |
|---|---|---|
| `backend/scripts/quality/y11_aday_uret.py` | SQL diliminden aday id kümesi + konu süzgeci + dedup | **T1'de YENİ** |
| `backend/tests/fast/test_y11_aday_uret.py` | Seçici bekçisi (DB'siz, saf) | **T1'de YENİ** |
| `backend/scripts/quality/y11_crop_liste.py` | Aday id → (id, kitap, host crop yolu) TSV | **T2'de YENİ** |
| `backend/scripts/quality/_mat_sizdiran.txt` | Kör okumadan çıkan sızdıran id listesi | **T3'te YENİ (veri)** |
| `backend/scripts/quality/y11_mat_kumesi.txt` | Nihai göç id kümesi | **T3'te YENİ (veri)** |
| `docs/audits/2026-08-20_mat_crop_kor_okuma.md` | Kör okuma kanıt kütüğü | **T3'te YENİ** |
| `y11_goc.py` / `y11_yukleyici.py` / `y11_dedup.py` | dönüşüm + yazma + kimlik | **DEĞİŞMEZ** |

`y11_goc.py`'ye **dokunulmuyor**: `SIZINTILI_KITAP` tek dizesi KIMYA için doğru
kalıyor ve MAT dilimi o kitabı içermiyor (`subject_area='MATEMATIK'`). Eski T2'nin
genelleştirmesi iptal edildiği için değişiklik gereksiz. **Çalışan koda dokunma.**

---

### Task 1: Ders-agnostik aday seçici

**Dosyalar:**
- Oluştur: `backend/scripts/quality/y11_aday_uret.py`
- Test: `backend/tests/fast/test_y11_aday_uret.py`

- [ ] **Adım 1: Düşen testi yaz**

`backend/tests/fast/test_y11_aday_uret.py`:

```python
"""Aday secicinin KIMYA'ya degil verilen SQL dilimine bagli oldugunu civiler."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "quality"))

from y11_aday_uret import (  # noqa: E402
    DILIMLER,
    KONU_BASI_TAVAN,
    haric_kumesi,
    konu_dengeli_sec,
)


def test_dilim_sql_parametre_olarak_gelir() -> None:
    """Ders/kitap adi modulde SABIT olmamali; KIMYA yolu ayri durmali."""
    assert set(DILIMLER) == {"mat_tyt"}, "beklenmeyen dilim -- sessiz genisletme"
    assert all(isinstance(v, str) for v in DILIMLER.values())
    kimya = (
        Path(__file__).resolve().parents[2]
        / "scripts" / "quality" / "y11_goc_kumesi_uret.py"
    )
    assert kimya.exists(), "KIMYA yolu silinmis -- gerileme"


def test_mat_dilimi_page_croplarini_disliyor() -> None:
    """_PAGE crop'lari basili cevap anahtari sizdiriyor (B4'te olculdu)."""
    sql = DILIMLER["mat_tyt"]
    assert "_q[0-9]+" in sql, "soru-bazli crop suzgeci YOK -- _PAGE sizar"
    assert "auto_judged_high" in sql, "kalite suzgeci YOK"
    assert "option_e IS NOT NULL" in sql, "bos sik suzgeci YOK"


def test_haric_kumesi_birlesim_kullanir_cikarma_degil() -> None:
    """set-ici mukerrer ile capraz-DB ORTUSEBILIR; cikarma yanlis sayi verir."""
    assert haric_kumesi({"a", "b"}, {"b", "c"}) == {"a", "b", "c"}


def test_konu_dengeli_sec_tavani_asmaz() -> None:
    """Tek konu havuzu domine etmemeli -- A1 'konu kirilimi' vaat ediyor."""
    adaylar = [(f"id{i}", "K1") for i in range(200)] + [
        (f"j{i}", "K2") for i in range(10)
    ]
    secilen = konu_dengeli_sec(adaylar, tavan=50)
    k1 = [x for x in secilen if x[1] == "K1"]
    k2 = [x for x in secilen if x[1] == "K2"]
    assert len(k1) == 50, f"K1 tavani asti: {len(k1)}"
    assert len(k2) == 10, "tavanin ALTINDAKI konu kirpilmamali"


def test_konu_dengeli_sec_DETERMINISTIK() -> None:
    """Iki kosum birebir ayni kumeyi vermeli -- `random` YOK."""
    adaylar = [(f"id{i}", "K1") for i in range(200)]
    assert konu_dengeli_sec(adaylar, tavan=50) == konu_dengeli_sec(adaylar, tavan=50)


def test_konu_basi_tavan_makul() -> None:
    """600 hedefi 12 konu x 50'den geliyor; sabit belgelenmis olmali."""
    assert KONU_BASI_TAVAN == 50
```

- [ ] **Adım 2: Testi koştur, DÜŞTÜĞÜNÜ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_aday_uret.py -q --no-header -p no:cacheprovider
```
Beklenen: `ModuleNotFoundError: No module named 'y11_aday_uret'` (collection error).

- [ ] **Adım 3: Uygula**

`backend/scripts/quality/y11_aday_uret.py`:

```python
#!/usr/bin/env python
"""MAT/TYT aday secici — SQL dilimi parametre, KIMYA'ya bagimli DEGIL.

KIMYA adaylari verdikt TSV'sinden gelir ve `y11_goc_kumesi_uret.py`'de durur;
oraya DOKUNULMAZ. `dict[str, str]` icine `None` koymak tip kirliligi olurdu.

KONU SUZGECI ZORUNLU: `y11_goc._canli_topic_id()` bilinmeyen kodda `ValueError`
firlatir. 20 Agu olcumu: dilimin 5.420 satirindan **871'inin** primary_topic_id
canli `topic_hierarchy`'de YOK. Onceden elenmezse yukleyici TUMDEN durur.
(Eski plan bu sayiyi 386 diyordu — BAYAT.)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# 12 konu x 50 = 600 aday. Sinir KOR OKUMA kapasitesi: her crop tek tek goz ile
# okunacak (OCR yok, kullanici karari). MAT-T1 bir turda 354 crop okudu.
KONU_BASI_TAVAN = 50

DILIMLER: dict[str, str] = {
    "mat_tyt": """
        SELECT id::text AS id, primary_topic_id::text AS konu
        FROM question_bank
        WHERE exam_type = 'TYT' AND subject_area = 'MATEMATIK'
          AND quality_review_status = 'auto_judged_high' AND is_active
          AND question_image_url ~ '_q[0-9]+\\.png$'
          AND correct_answer IN ('A','B','C','D','E')
          AND option_e IS NOT NULL AND btrim(option_e) <> ''
    """,
}


def haric_kumesi(set_ici: set[str], capraz: set[str]) -> set[str]:
    """BIRLESIM — cikarma DEGIL. Iki kume ortusebilir."""
    return set_ici | capraz


def konu_dengeli_sec(
    adaylar: Iterable[tuple[str, str]], *, tavan: int = KONU_BASI_TAVAN
) -> list[tuple[str, str]]:
    """Konu basina en fazla `tavan` aday — DETERMINISTIK (`md5(id)` sirasi).

    `random` KULLANILMAZ: iki kosum birebir ayni kumeyi vermeli, yoksa PROVA'da
    olculen kume ile KALICI'da yazilan kume ayrisir.
    """
    kovalar: dict[str, list[tuple[str, str]]] = {}
    for id_, konu in adaylar:
        kovalar.setdefault(konu, []).append((id_, konu))
    secilen: list[tuple[str, str]] = []
    for konu in sorted(kovalar):
        sirali = sorted(
            kovalar[konu], key=lambda x: hashlib.md5(x[0].encode()).hexdigest()
        )
        secilen.extend(sirali[:tavan])
    return sorted(secilen, key=lambda x: hashlib.md5(x[0].encode()).hexdigest())


def dsn_coz(veritabani: str) -> str:
    """DSN'i ortamdan cozer. Parola KODA YAZILMAZ."""
    if dsn := os.environ.get(f"KIRO2_DSN_{veritabani.upper()}"):
        return dsn
    kullanici = os.environ.get("PGUSER", "postgres")
    parola = os.environ.get("PGPASSWORD", "")
    sunucu = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5434")
    kimlik = f"{kullanici}:{parola}@" if parola else f"{kullanici}@"
    return f"postgresql://{kimlik}{sunucu}:{port}/{veritabani}"


async def _main(argv: Sequence[str] | None = None) -> int:
    import asyncpg

    ap = argparse.ArgumentParser(description="MAT/TYT aday secici")
    ap.add_argument("--dilim", required=True, choices=sorted(DILIMLER))
    ap.add_argument("--cikti", required=True, type=Path)
    ap.add_argument("--tavan", type=int, default=KONU_BASI_TAVAN)
    a = ap.parse_args(argv)

    kaynak = await asyncpg.connect(dsn_coz("kiro2_temp"))
    hedef = await asyncpg.connect(dsn_coz("kiro2"))
    try:
        ham = [(r["id"], r["konu"]) for r in await kaynak.fetch(DILIMLER[a.dilim])]
        canli_konu = {r["id"] for r in await hedef.fetch(
            "SELECT id::text AS id FROM topic_hierarchy")}
        canli_hash = {r["h"] for r in await hedef.fetch(
            "SELECT soru_hash AS h FROM question_bank WHERE soru_hash IS NOT NULL")}
        kaynak_hash = {
            r["id"]: r["h"]
            for r in await kaynak.fetch(
                "SELECT id::text AS id, soru_hash AS h FROM question_bank"
            )
        }
    finally:
        await kaynak.close()
        await hedef.close()

    kapsanan = [(i, k) for i, k in ham if k in canli_konu]
    elenen_konu = len(ham) - len(kapsanan)
    capraz = {i for i, _ in kapsanan if kaynak_hash.get(i) in canli_hash}
    kalan = [(i, k) for i, k in kapsanan if i not in haric_kumesi(set(), capraz)]
    secilen = konu_dengeli_sec(kalan, tavan=a.tavan)

    a.cikti.write_text("\n".join(i for i, _ in secilen), encoding="utf-8")
    konular = {k for _, k in secilen}
    # SESSIZ ELEME YOK — her dusen sayi yazdirilir.
    print(f"ham aday                  : {len(ham)}")
    print(f"konu kapsami disi elenen  : {elenen_konu}")
    print(f"capraz-DB elenen          : {len(capraz)}")
    print(f"konu tavani sonrasi       : {len(secilen)}  ({len(konular)} konu)")
    print(f"cikti                     : {a.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
```

- [ ] **Adım 4: Testleri koştur, GEÇTİĞİNİ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_aday_uret.py -q --no-header -p no:cacheprovider
```
Beklenen: `6 passed`.

- [ ] **Adım 5: Seçiciyi koştur + determinizmi ölç**

```bash
cd C:/Users/husey/kiro2/backend
PGUSER=postgres PGHOST=localhost PGPORT=5434 python scripts/quality/y11_aday_uret.py \
  --dilim mat_tyt --cikti scripts/quality/y11_mat_aday.txt
PGUSER=postgres PGHOST=localhost PGPORT=5434 python scripts/quality/y11_aday_uret.py \
  --dilim mat_tyt --cikti scripts/quality/_ikinci.txt
python -c "
import pathlib,hashlib
a=pathlib.Path('scripts/quality/y11_mat_aday.txt').read_bytes()
b=pathlib.Path('scripts/quality/_ikinci.txt').read_bytes()
print('DETERMINIZM:', 'BIREBIR' if a==b else 'FARKLI')
print('satir:', len(a.splitlines()), 'sha:', hashlib.sha256(a).hexdigest()[:16])
"
rm -f scripts/quality/_ikinci.txt
```
Beklenen: `konu kapsami disi elenen : 871` · `DETERMINIZM: BIREBIR` ·
satır **~600** (19 konu × 50 tavanı, konu sayısına göre 600-950 arası).

- [ ] **Adım 6: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run --files backend/scripts/quality/y11_aday_uret.py backend/tests/fast/test_y11_aday_uret.py
git add backend/scripts/quality/y11_aday_uret.py backend/tests/fast/test_y11_aday_uret.py
git commit -F <mesaj-dosyasi>    # -m KULLANMA: ters tirnak komut calistirir
git show --stat HEAD | tail -4   # exit 0 + yeni hash YETMEZ, NE girdigini oku
```

---

### Task 2: Crop yol listesi

**Dosyalar:**
- Oluştur: `backend/scripts/quality/y11_crop_liste.py`

- [ ] **Adım 1: Uygula**

```python
#!/usr/bin/env python
"""Aday id listesi -> (id, kitap, container yolu, host yolu) TSV.

Kor okuma ajanlari bu TSV'yi okur. Yol donusumu TEK yerde: iki ayri ajanin
kendi basina yol kurmasi, S237'de 4 kez isiran `/tmp` ve NFC-NFD tuzaklarini
tekrar uretirdi.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from y11_aday_uret import dsn_coz  # noqa: E402

HOST_KOK = "C:/Users/husey/kiro2/d-dataset/output/crops"
ONEK = "/static/crops/"


async def _main(argv: list[str] | None = None) -> int:
    import asyncpg

    ap = argparse.ArgumentParser()
    ap.add_argument("--idler", required=True, type=Path)
    ap.add_argument("--cikti", required=True, type=Path)
    a = ap.parse_args(argv)

    idler = [s for s in a.idler.read_text(encoding="utf-8").split() if s]
    baglanti = await asyncpg.connect(dsn_coz("kiro2_temp"))
    try:
        satirlar = await baglanti.fetch(
            "SELECT id::text AS id, source_book AS kitap, question_image_url AS url "
            "FROM question_bank WHERE id::text = ANY($1::text[])",
            idler,
        )
    finally:
        await baglanti.close()

    with a.cikti.open("w", encoding="utf-8", newline="\n") as f:
        for r in satirlar:
            url = r["url"] or ""
            gorece = url[len(ONEK):] if url.startswith(ONEK) else url.lstrip("/")
            f.write(f"{r['id']}\t{r['kitap']}\t/app/static/crops/{gorece}\t{HOST_KOK}/{gorece}\n")
    print(f"yazilan: {len(satirlar)} / istenen: {len(idler)} -> {a.cikti}")
    return 0 if len(satirlar) == len(idler) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
```

- [ ] **Adım 2: Koştur ve dosya varlığını CONTAINER'dan doğrula**

```bash
cd C:/Users/husey/kiro2/backend
PGUSER=postgres PGHOST=localhost PGPORT=5434 python scripts/quality/y11_crop_liste.py \
  --idler scripts/quality/y11_mat_aday.txt --cikti scripts/quality/y11_mat_crop.tsv
wc -l < scripts/quality/y11_mat_crop.tsv
```

⚠️ Dosya varlığını bash `[ -f ]` ile **SORMA** — NTFS'te Türkçe `İ/ı/ğ` NFC-NFD
farkı var olan dosyaya "yok" dedirtir (S237'de 8/8 yanlış-negatif ölçüldü).
Container'dan sor:

```bash
cut -f3 scripts/quality/y11_mat_crop.tsv > scripts/quality/_yollar.txt
docker cp scripts/quality/_yollar.txt kiro2-backend:/tmp/_yollar.txt
docker exec kiro2-backend python -c "
import io,os
y=[l.strip() for l in io.open('/tmp/_yollar.txt',encoding='utf-8') if l.strip()]
v=sum(1 for p in y if os.path.isfile(p))
print(f'container: {v}/{len(y)} dosya VAR')
"
```
Beklenen: `container: N/N dosya VAR`. Eksik varsa o id'ler aday kümesinden
çıkarılır (sessizce göç ettirilmez).

- [ ] **Adım 3: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run --files backend/scripts/quality/y11_crop_liste.py
git add backend/scripts/quality/y11_crop_liste.py
git commit -F <mesaj-dosyasi>
```

---

### Task 3: HER crop kör okunur — sızdıran SİLİNİR

Bu planın çekirdeği. Kitap katmanı çürütüldü, OCR yok → tek geçerli yöntem
**gözle okuma**. Aday sayısı (600) tam olarak bunun için seçildi.

**Dosyalar:**
- Oluştur: `backend/scripts/quality/_mat_sizdiran.txt`
- Oluştur: `backend/scripts/quality/y11_mat_kumesi.txt`
- Oluştur: `docs/audits/2026-08-20_mat_crop_kor_okuma.md`

- [ ] **Adım 1: Paralel görme ajanlarını dağıt**

`superpowers:dispatching-parallel-agents` kullan. TSV'yi **15 dilime** böl
(~40 crop/ajan). Her ajana verilecek görev:

> Sana `y11_mat_crop.tsv` dosyasından bir satır aralığı verilecek. Her satırın
> 4. alanı bir PNG'nin HOST yoludur. **Her PNG'yi `Read` ile aç** ve tek soruya
> cevap ver: **bu görselde sorunun cevap anahtarı görünüyor mu?**
> Sızıntı sayılan: kenar/alt/üst şeritte basılı anahtar (`1.A 2.C 3.E …`),
> komşu sorunun çözümü, ya da doğru şıkkı işaretleyen herhangi bir iz.
> Sızıntı SAYILMAYAN: sorunun kendi şekli/grafiği/tablosu.
> Kararsızsan **sızdırıyor** de (yanlış-pozitif ucuz, yanlış-negatif öğrenciye gider).
> Çıktı: her satır için `id<TAB>EVET|HAYIR<TAB>kanit_cumlesi`.

- [ ] **Adım 2: Sızdıranları topla**

```bash
cd C:/Users/husey/kiro2/backend
# ajan ciktilari birlestirildikten sonra:
awk -F'\t' '$2=="EVET"{print $1}' scripts/quality/_kor_okuma_ham.tsv \
  | sort -u > scripts/quality/_mat_sizdiran.txt
echo "sizdiran: $(wc -l < scripts/quality/_mat_sizdiran.txt)"
```
Beklenen: **%2,54 civarı** (600'de ~15). Çok sapıyorsa (`>%10` veya `0`)
**DUR** — ya örneklem katmanı yanlış ya ajanlar ölçmüyor; MAT-T1'in oranıyla
karşılaştır.

- [ ] **Adım 3: Nihai kümeyi üret — sızdıran ATILIR**

```bash
cd C:/Users/husey/kiro2/backend
python - <<'PY'
import io, pathlib
aday = [s for s in pathlib.Path("scripts/quality/y11_mat_aday.txt").read_text(
    encoding="utf-8").split() if s]
sizdiran = {s for s in pathlib.Path("scripts/quality/_mat_sizdiran.txt").read_text(
    encoding="utf-8").split() if s}
kalan = [i for i in aday if i not in sizdiran]
io.open("scripts/quality/y11_mat_kumesi.txt", "w", encoding="utf-8",
        newline="\n").write("\n".join(kalan))
print(f"aday {len(aday)} - sizdiran {len(sizdiran)} = goc {len(kalan)}")
assert len(kalan) == len(aday) - len(sizdiran & set(aday)), "kume aritmetigi tutmadi"
assert len(kalan) >= 300, f"kalan {len(kalan)} < 300 -- A1 icin marj yetersiz, DUR"
PY
```

- [ ] **Adım 4: Kanıt kütüğünü yaz**

`docs/audits/2026-08-20_mat_crop_kor_okuma.md`: Methodology (örneklem = **evrenin
TAMAMI**, truncation yok, ajan başına dilim, karar ölçütü) + sızdıran tablo +
oranın MAT-T1'in %2,54'üyle karşılaştırması + kalan küme boyutu.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/scripts/quality/y11_mat_kumesi.txt \
        backend/scripts/quality/_mat_sizdiran.txt \
        docs/audits/2026-08-20_mat_crop_kor_okuma.md
git commit -F <mesaj-dosyasi>
```

---

### Task 4: Tam ölçekte PROVA (geri alınır)

- [ ] **Adım 1: Yazım öncesi tabanı ölç**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -F' | ' -c \
"SELECT (SELECT count(*) FROM question_bank),(SELECT count(*) FROM question_content),(SELECT count(*) FROM question_metadata),(SELECT count(*) FROM question_statistics),(SELECT count(*) FROM mv_safe_for_beta);"
```
Beklenen: `3616 | 3616 | 3616 | 3616 | 0`

- [ ] **Adım 2: Provayı koştur (`--kalici` YOK = geri alır)**

```bash
cd C:/Users/husey/kiro2/backend
PGUSER=postgres PGHOST=localhost PGPORT=5434 python scripts/quality/y11_yukleyici.py \
  --idler scripts/quality/y11_mat_kumesi.txt --damga y11_mat_tyt_20260820
```

Kabul — raporun **hepsi** tutmalı: `yazilan` dört tabloda eşit · `yetim: 0` ·
`damgali` = satır sayısı · `icerik_sadakati.sapma: []` · `kural_sayimi` içinde
`is_active_true` = `review_status_approved` = `quality_pending` = satır sayısı.

- [ ] **Adım 3: Rollback'i doğrula**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -c \
"SELECT count(*) FROM question_metadata WHERE pipeline_metadata->>'y11_batch'='y11_mat_tyt_20260820';"
```
Beklenen: `0`.

- [ ] **Adım 4: Örneklem OKU — sayıya güvenme**

Nihai kümeden 10 soruyu metin + 5 şık + anahtar olarak çek ve **tek tek çöz**.
Kabul: **≥8/10 servis edilebilir ve anahtarı doğru**. Altındaysa **DUR** —
dilim süzgeci yetersiz, Task 1'e dön. (`L-s231-hacim-vekil-olcum-icerik-degil`)

---

### Task 5: KALICI yazım

- [ ] **Adım 1: Kalıcı yaz**

```bash
cd C:/Users/husey/kiro2/backend
PGUSER=postgres PGHOST=localhost PGPORT=5434 python scripts/quality/y11_yukleyici.py \
  --idler scripts/quality/y11_mat_kumesi.txt --damga y11_mat_tyt_20260820 --kalici
```

- [ ] **Adım 2: Transaction DIŞINDAN bağımsız doğrula**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -F' | ' -c \
"SELECT (SELECT count(*) FROM question_bank),
        (SELECT count(*) FROM question_metadata WHERE pipeline_metadata->>'y11_batch'='y11_mat_tyt_20260820'),
        (SELECT count(*) FROM question_bank b LEFT JOIN question_content c ON c.id=b.id WHERE c.id IS NULL),
        (SELECT count(*) FROM mv_safe_for_beta);"
```
Beklenen: `3616+N | N | 0 | 0` — kapı **değişmemeli** (yeni parti `pending`).

- [ ] **Adım 3: Görsel hattını container'dan doğrula**

Yeni partiden 40 `question_image_url` çek, container'da `os.path.isfile` ile sor.
Beklenen **40/40**. ⚠️ Bash `[ -f ]` KULLANMA (NFC-NFD). ⚠️ Ara dosyayı **depo
içinde** tut — bash `/tmp` (MSYS) ile Python `/tmp` (`C:\tmp`) ayrı ad alanları.

- [ ] **Adım 4: İdempotensi doğrula**

Seçiciyi tekrar koştur. Göç edilenler artık canlıda olduğu için `capraz-DB
elenen` **≥ göç edilen sayı** olmalı. Çift göç yapısal olarak engellenmeli.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/scripts/quality/y11_mat_kumesi.txt
git commit -F <mesaj-dosyasi>
git show --stat HEAD | tail -4
```

---

### Task 6: A1 KABUL TESTİ — asıl ölçüm

Buraya kadar her şey vasıta. Kriter: *"40 soruluk bir TYT Matematik testi çözer →
netini ve konu kırılımını görür."*

- [ ] **Adım 1: 40 soruluk test kurulabiliyor mu**

```sql
SELECT th.code, th.name_tr, count(*) AS soru
FROM question_bank qb
JOIN question_metadata qm ON qm.id = qb.id
JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
WHERE qm.pipeline_metadata->>'y11_batch' = 'y11_mat_tyt_20260820'
GROUP BY 1,2 ORDER BY 3 DESC;
```
Kabul: **≥5 farklı konu kodu** ve toplam **≥40 soru**.
⚠️ Konu kırılımında **Türev/İntegral** görünürse **DUR** — `exam_type`
güvenilmez (B4'te ölçüldü), AYT sorusu TYT dilimine sızmış demektir.

- [ ] **Adım 2: Kapının değişmediğini ölç**

```sql
SELECT count(*) FROM mv_safe_for_beta;   -- 0 olmali
```
Yeni parti `pending`, yani kapının **dışında** — **kasıtlı**. Terfi
(`pending → auto_judged_high` + `REFRESH`) **ayrı onay** ister.

- [ ] **Adım 3: Devir notunu yaz**

`.claude/sessions/latest.md`'ye yeni oturum bloğu: ölçülen sayılar, düşen
testler, engelleyiciler, kararlar, sonraki adımlar (maks 5).
⚠️ Dosya **son 3 oturum** tutuyor; en eskisini `.claude/sessions/arsiv/`'e
**birebir** taşı, silme.

---

## Riskler ve önleyici ölçümler

| Risk | Sessizce nasıl gider | Önleyici ölçüm |
|---|---|---|
| Kapsam dışı **871** soru | Yükleyici tümden `ValueError` ile durur | **T1** — konu süzgeci + elenen sayı yazdırılır |
| Crop sızıntısı (%2,54) | Basılı anahtar öğrenciye gider | **T3** — evrenin TAMAMI kör okunur, sızdıran atılır |
| Crop dosyası diskte yok | `question_image_url` kırık link | **T2 Adım 2** — container'dan `os.path.isfile` |
| `exam_type` güvenilmez | AYT sorusu TYT testine girer | **T6 Adım 1** — Türev/İntegral görünürse DUR |
| Aday kümesi çift göç eder | Mükerrer içerik | **T5 Adım 4** — idempotens |
| Seçici nondeterministik | PROVA'daki küme ≠ KALICI'daki | **T1 Adım 5** — iki koşum sha256 karşılaştırması |
| Commit yarım gider | İş kaybolur | Her commit sonrası `git show --stat HEAD` |

## Kapsam dışı (bilerek)

- `pending → auto_judged_high` terfisi + `REFRESH` — **ayrı onay**.
- Kalan ~3.900 kapsanan MAT sorusu — kör okunamadığı için göçürülmez.
  Ölçek istenirse kör okuma kapasitesi artırılarak ayrı turda yapılır.
- 871 kapsam dışı soru (`TYT-MAT-*`/`AYT-MAT-*` ebeveynsiz kodlar) — ayrı karar.
- Canlıdaki 3.616 KIMYA satırının crop sızıntısı **hiç ölçülmedi** (~1.426 görsel,
  %2,54 varsayarsa ~36 sızdıran). **Açık iş** — bu planın kapsamı değil.
- `y11_goc.py` genelleştirmesi (eski T2) — **iptal**, kitap katmanı çürütüldü.
