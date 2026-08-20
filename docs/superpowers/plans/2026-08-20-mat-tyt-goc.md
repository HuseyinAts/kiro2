# MAT/TYT Göçü — Uygulama Planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: bu planı task-task uygulamak için
> `superpowers:subagent-driven-development` (önerilen) veya
> `superpowers:executing-plans` kullan. Adımlar `- [ ]` kutucuk sözdizimiyle izlenir.

**Hedef:** Temiz MAT/TYT dilimini `kiro2_temp`'ten canlı `kiro2`'ye göç ettirip
A1 kabul kriterinin içerik ayağını ilk kez gerçek veriyle koşulabilir yapmak.

**Mimari:** Y11 hattı üç saf katmandan oluşuyor — dönüşüm (`y11_goc.py`, DB'siz),
yazma (`y11_yukleyici.py`, tek transaction), aday seçimi. İlk ikisi KIMYA göçünde
kanıtlandı (3.616 satır kalıcı yazıldı, `44cb08a04`). Bu plan üçüncüsünü ders-agnostik
yapar ve dönüşümdeki tek KIMYA-özgü sabiti genelleştirir. Yeni motor yazılmaz.

**Teknoloji:** Python 3.13 · asyncpg · PostgreSQL 18.1 (port 5434, `postgres` trust) ·
pytest · pre-commit (kapı ruff **0.7.1**, yerel 0.14.13 — farklı sürümler)

---

## Ölçülmüş başlangıç durumu

| | Değer | Kanıt |
|---|---|---|
| Temiz MAT/TYT havuzu | **5.420** soru / 99 kitap / 43 kod | süzgeç aşağıda |
| Konu kapsaması | **5.034 (%92,9)** | `f74a09bf5` seed'i sonrası ölçüldü |
| Kapsanmayan | 386 soru / 18 kod (`TYT-MAT-*`, `AYT-MAT-*`) | kapsam dışı, ayrı karar |
| Canlı DB | `question_bank` 40.583 ×4 · kapı 27.073 · görsel 1.426 | `44cb08a04` sonrası |
| Örneklem okuması | 8 sorunun **7'si** metinden, **8'i** görselden servis edilebilir | B4 turu |

**Temiz dilim süzgeci** (bu plan boyunca değişmez):

```sql
exam_type = 'TYT' AND subject_area = 'MATEMATIK'
AND quality_review_status = 'auto_judged_high' AND is_active
AND question_image_url ~ '_q[0-9]+\.png$'     -- _PAGE crop'ları DIŞARIDA
AND correct_answer IN ('A','B','C','D','E')
AND option_e IS NOT NULL AND btrim(option_e) <> ''
```

`_PAGE` süzgeci **zorunlu**: MAT/TYT görsellerinin %40-45'i tam sayfa crop ve
komşu soruları + **basılı cevap anahtarını** sızdırıyor (B4'te ölçüldü).

---

## Dosya yapısı

| Dosya | Sorumluluk | Durum |
|---|---|---|
| `backend/scripts/quality/y11_goc.py` | Saf dönüşüm (DB'siz) | **T2'de değişir** — `:72` tek dize → küme |
| `backend/scripts/quality/y11_aday_uret.py` | SQL'den aday id kümesi + dedup | **T3'te YENİ** |
| `backend/scripts/quality/y11_yukleyici.py` | Yazma katmanı | değişmez |
| `backend/scripts/quality/y11_dedup.py` | Kimlik + mükerrer gruplama | değişmez |
| `backend/tests/fast/test_y11_goc.py` | 242 vaka | **T2'de +test** |
| `backend/tests/fast/test_y11_aday_uret.py` | Aday seçici testleri | **T3'te YENİ** |
| `docs/audits/2026-08-20_mat_sizinti_olcumu.md` | T1 kanıt kütüğü | **T1'de YENİ** |

---

### Task 1: MATEMATIK'te sızıntılı kitap ÖLÇÜMÜ

`SIZINTILI_KITAP = "Apotemi 2024 Ayt Kimya Soru Bankasi"` KIMYA turunda **ölçülerek**
bulundu (112 crop sızdırıyordu). MATEMATIK için karşılığı **bilinmiyor**. KIMYA'nın
kuralını devralmak da, "sızıntı yok" varsaymak da ölçüm değil.

**Dosyalar:**
- Oluştur: `docs/audits/2026-08-20_mat_sizinti_olcumu.md`

- [ ] **Adım 1: Kitap başına örneklem URL'lerini çıkar**

```bash
cd C:/Users/husey/kiro2/backend
cat > scripts/quality/_sizinti_ornek.sql <<'SQL'
\encoding UTF8
\pset format unaligned
\pset fieldsep '|'
\pset tuples_only on
WITH temiz AS (
  SELECT source_book, question_image_url,
         row_number() OVER (PARTITION BY source_book ORDER BY md5(id::text)) AS sira,
         count(*)     OVER (PARTITION BY source_book) AS kitap_n
  FROM question_bank
  WHERE exam_type='TYT' AND subject_area='MATEMATIK'
    AND quality_review_status='auto_judged_high' AND is_active
    AND question_image_url ~ '_q[0-9]+\.png$'
    AND correct_answer IN ('A','B','C','D','E')
    AND option_e IS NOT NULL AND btrim(option_e) <> ''
)
SELECT source_book, question_image_url FROM temiz
WHERE sira <= 6 AND kitap_n >= 20 ORDER BY source_book, sira;
SQL
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2_temp \
  -f scripts/quality/_sizinti_ornek.sql > scripts/quality/_sizinti_ornek.txt
wc -l < scripts/quality/_sizinti_ornek.txt
```

Beklenen: her biri `kitap|/static/crops/...png` biçiminde ~100-200 satır
(20+ soruluk kitaplar × 6 örnek).

- [ ] **Adım 2: Görselleri KÖR oku — paralel ajanlarla**

`superpowers:dispatching-parallel-agents` kullan. Kitapları ~8 ajana böl.
Her ajana verilecek görev metni:

> Sana bir kitap adı ve 6 crop yolu verilecek. Her PNG'yi **Read** ile aç ve
> yalnız şunu yanıtla: **görselde o sorunun cevap anahtarı görünüyor mu?**
> (kenar/alt/üst şeritte "1.A 2.C 3.E …" gibi basılı anahtar, ya da komşu sorunun
> çözümü). Dosya yolu container'da `/app` + URL; hostta
> `C:/Users/husey/kiro2/d-dataset/output/crops/` + URL'nin `/static/crops/` sonrası.
> ⚠️ Git Bash `[ -f ]` Türkçe `İ/ı/ğ` içeren yolda YANLIŞ "yok" der — dosya
> varlığını `docker exec kiro2-backend python -c "import os;print(os.path.isfile(...))"`
> ile sor. Çıktı: `kitap | sizdiran_crop_sayisi/6 | kanit_cumlesi`.

- [ ] **Adım 3: Kararı yaz**

`docs/audits/2026-08-20_mat_sizinti_olcumu.md` içine: Methodology (SQL, örneklem
boyutu, seçim = `md5(id)` deterministik, truncation yok) + kitap başına tablo +
sonuç. Karar ölçütü: **6/6'da 2 veya daha fazla sızıntı → o kitap sızıntılı.**

**Sonuca göre dallan — üç durum, üçü de farklı iş:**

| T1 sonucu | Anlamı | Karar |
|---|---|---|
| **0 sızıntılı kitap** | `_PAGE` süzgeci tek başına yetiyor | T2'yi yine yap (küme yapısı MAT için boş kalır, KIMYA korunur), göç dilimi **5.034** |
| **1-5 kitap** | KIMYA'nın deseni, beklenen | Kümeye ekle; dilim daralır, **yeni boyutu ölç ve yaz** |
| **>15 kitap (%15+)** | Sızıntı **kitap-özgü değil sistemik** | **DUR.** Kitap kümesi yanlış katman; crop üretim hattı incelenmeli. Planı burada kes, bulguyu ayrı iş olarak kaydet |

Üçüncü durumda göçe devam etmek, ölçülmüş bir riski "kitap listesi" kılığında
gizlemek olur — S233'te görsellerin %57,8'inin basılı anahtar sızdırdığı ölçülmüştü.

- [ ] **Adım 4: Commit**

```bash
cd C:/Users/husey/kiro2
git add docs/audits/2026-08-20_mat_sizinti_olcumu.md
git commit -m "docs(Y11/T1): MATEMATIK sizinti olcumu -- N kitap tarandi, M sizintili"
```

---

### Task 2: `SIZINTILI_KITAP` → ders-agnostik küme

**Dosyalar:**
- Değiştir: `backend/scripts/quality/y11_goc.py:72` ve `:239`
- Test: `backend/tests/fast/test_y11_goc.py`

- [ ] **Adım 1: Düşen testi yaz**

`backend/tests/fast/test_y11_goc.py` sonuna ekle:

```python
def test_sizintili_kitap_kumesi_birden_fazla_kitabi_kapsar():
    """Tek dize KIMYA'ya kilitliydi; MATEMATIK'in kendi sizintili kitaplari var.

    T1'de olculdu (docs/audits/2026-08-20_mat_sizinti_olcumu.md).
    """
    from y11_goc import SIZINTILI_KITAPLAR

    assert isinstance(SIZINTILI_KITAPLAR, frozenset)
    assert "Apotemi 2024 Ayt Kimya Soru Bankasi" in SIZINTILI_KITAPLAR, (
        "KIMYA'nin olculmus sizintili kitabi kumede kalmali -- gerileme olur"
    )


@pytest.mark.parametrize(
    "kitap,beklenen",
    [
        ("Apotemi 2024 Ayt Kimya Soru Bankasi", None),
        ("Temiz Kitap", "/static/crops/x/x_p0001_q01.png"),
    ],
)
def test_gorsel_kurali_kume_uzerinden_calisir(kitap, beklenen):
    from y11_goc import _gorsel_url

    satir = {
        "question_image_url": "/static/crops/x/x_p0001_q01.png",
        "source_book": kitap,
    }
    assert _gorsel_url(satir) == beklenen
```

- [ ] **Adım 2: Testi koştur, DÜŞTÜĞÜNÜ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_goc.py -k sizintili -q --no-header -p no:cacheprovider
```
Beklenen: `ImportError: cannot import name 'SIZINTILI_KITAPLAR'` (2 failed).

- [ ] **Adım 3: Uygula**

`y11_goc.py:72`'yi değiştir:

```python
# T1'de OLCULDU (docs/audits/2026-08-20_mat_sizinti_olcumu.md). Bu bir KUME:
# her ders kendi sizintili kitaplarini getirir, KIMYA'ninki silinmez.
# Karar olcutu: 6 crop orneklemin >=2'sinde basili cevap anahtari gorunuyorsa.
SIZINTILI_KITAPLAR: frozenset[str] = frozenset(
    {
        "Apotemi 2024 Ayt Kimya Soru Bankasi",  # KIMYA turu, 112 crop
        # <T1 ciktisindan MATEMATIK kitaplari buraya>
    }
)
```

`:239`'u değiştir:

```python
    if kitap in SIZINTILI_KITAPLAR:
        return None
```

- [ ] **Adım 4: Testleri koştur, GEÇTİĞİNİ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_goc.py -q --no-header -p no:cacheprovider
```
Beklenen: `245 passed` (242 önceki + 3 yeni vaka), 0 failed.

- [ ] **Adım 5: Mutasyonla çivile**

```bash
cd C:/Users/husey/kiro2/backend
python - <<'PY'
import pathlib
p = pathlib.Path("scripts/quality/y11_goc.py")
yedek = p.read_bytes()
try:
    s = yedek.decode("utf-8").replace("if kitap in SIZINTILI_KITAPLAR:", "if False:", 1)
    p.write_bytes(s.encode("utf-8"))
    import subprocess
    r = subprocess.run(["python", "-m", "pytest", "tests/fast/test_y11_goc.py",
                        "-q", "--no-header", "-p", "no:cacheprovider"],
                       capture_output=True, text=True)
    print("MUTASYON:", "OLDU" if " failed" in r.stdout else "KACTI -- test degersiz")
finally:
    p.write_bytes(yedek)
PY
git status --short scripts/quality/y11_goc.py    # BOS olmali (geri alim dogrulandi)
```
Beklenen: `MUTASYON: OLDU` ve `git status` boş.

- [ ] **Adım 6: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run ruff --files backend/scripts/quality/y11_goc.py backend/tests/fast/test_y11_goc.py
pre-commit run ruff-format --files backend/scripts/quality/y11_goc.py backend/tests/fast/test_y11_goc.py
git add backend/scripts/quality/y11_goc.py backend/tests/fast/test_y11_goc.py
git commit -m "feat(Y11/T2): SIZINTILI_KITAP -> ders-agnostik SIZINTILI_KITAPLAR kumesi"
git show --stat HEAD | tail -4      # NE GIRDI -- exit 0 + yeni hash yetmez
```

---

### Task 3: Ders-agnostik aday seçici

`y11_goc_kumesi_uret.py` KIMYA verdikt TSV'sine bağlı. MAT dilimi TSV'den değil
**SQL süzgecinden** geliyor (yargı zaten `quality_review_status`'ta kayıtlı).

**Dosyalar:**
- Oluştur: `backend/scripts/quality/y11_aday_uret.py`
- Test: `backend/tests/fast/test_y11_aday_uret.py`

- [ ] **Adım 1: Düşen testi yaz**

`backend/tests/fast/test_y11_aday_uret.py`:

```python
"""Aday secicinin KIMYA'ya degil, verilen SQL'e bagli oldugunu civiler."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "quality"))


def test_dilim_sql_parametre_olarak_gelir():
    """Ders adi/kitap adi modulde SABIT olmamali.

    KIMYA'yi buraya `None` degeriyle koymak TIP KIRLILIGI olurdu (`dict[str, str]`
    icinde `None`); KIMYA yolu `y11_goc_kumesi_uret.py`'de TSV uzerinden duruyor
    ve oraya dokunulmuyor. Gerileme korumasi o dosyanin VARLIGINI olcer.
    """
    from y11_aday_uret import DILIMLER

    assert set(DILIMLER) == {"mat_tyt"}, "beklenmeyen dilim -- sessiz genisletme"
    assert all(isinstance(v, str) for v in DILIMLER.values()), "deger str olmali"
    kimya_yolu = Path(__file__).resolve().parents[2] / "scripts" / "quality" / "y11_goc_kumesi_uret.py"
    assert kimya_yolu.exists(), "KIMYA yolu silinmis -- gerileme"


def test_mat_tyt_dilimi_PAGE_croplarini_disliyor():
    """_PAGE crop'lari basili cevap anahtari sizdiriyor (B4'te olculdu)."""
    from y11_aday_uret import DILIMLER

    sql = DILIMLER["mat_tyt"]
    assert "_q[0-9]+" in sql, "soru-bazli crop suzgeci YOK -- _PAGE sizar"
    assert "auto_judged_high" in sql, "kalite suzgeci YOK"


def test_haric_kumesi_birlesim_kullanir_cikarma_degil():
    """set-ici mukerrer ile capraz-DB ORTUSEBILIR; cikarma yanlis sayi verir."""
    from y11_aday_uret import haric_kumesi

    set_ici = {"a", "b"}
    capraz = {"b", "c"}
    assert haric_kumesi(set_ici, capraz) == {"a", "b", "c"}
    assert len(haric_kumesi(set_ici, capraz)) == 3, "birlesim 3, cikarma 1 verirdi"
```

- [ ] **Adım 2: Testi koştur, DÜŞTÜĞÜNÜ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_aday_uret.py -q --no-header -p no:cacheprovider
```
Beklenen: `ModuleNotFoundError: No module named 'y11_aday_uret'` (3 error).

- [ ] **Adım 3: Uygula**

`backend/scripts/quality/y11_aday_uret.py` oluştur. Çekirdek:

```python
DILIMLER: dict[str, str] = {
    "mat_tyt": """
        SELECT id::text AS id, question_text, option_a, option_b, option_c,
               option_d, option_e, correct_answer
        FROM question_bank
        WHERE exam_type = 'TYT' AND subject_area = 'MATEMATIK'
          AND quality_review_status = 'auto_judged_high' AND is_active
          AND question_image_url ~ '_q[0-9]+\\.png$'
          AND correct_answer IN ('A','B','C','D','E')
          AND option_e IS NOT NULL AND btrim(option_e) <> ''
    """,
}
# KIMYA BURAYA EKLENMEZ: onun adaylari verdikt TSV'sinden geliyor ve
# `y11_goc_kumesi_uret.py`'de calisiyor. `dict[str, str]` icine `None` koymak
# tip kirliligi olurdu; iki yol ayri kalir.


def haric_kumesi(set_ici: set[str], capraz: set[str]) -> set[str]:
    """BIRLESIM -- cikarma DEGIL.

    Iki kume ortusebilir. KIMYA'da KESISIM=0 olctu ve naif cikarma tesadufen
    dogru cikti; MAT'ta ayni sansi varsayma.
    """
    return set_ici | capraz
```

Geri kalanı `y11_goc_kumesi_uret.py`'nin yapısını izler: adayları çek →
`mukerrer_gruplar` ile set-içi fazlalık → canlı kimlik kümesiyle çapraz-DB →
`haric_kumesi` → dosyaya yaz. `--dilim` ve `--cikti` argümanları.

- [ ] **Adım 4: Testleri koştur, GEÇTİĞİNİ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/fast/test_y11_aday_uret.py -q --no-header -p no:cacheprovider
```
Beklenen: `3 passed`.

- [ ] **Adım 5: Determinizmi ölç**

```bash
cd C:/Users/husey/kiro2/backend
python scripts/quality/y11_aday_uret.py --dilim mat_tyt --cikti scripts/quality/y11_mat_kumesi.txt
python scripts/quality/y11_aday_uret.py --dilim mat_tyt --cikti scripts/quality/_ikinci.txt
python -c "
import pathlib,hashlib
a=pathlib.Path('scripts/quality/y11_mat_kumesi.txt').read_bytes()
b=pathlib.Path('scripts/quality/_ikinci.txt').read_bytes()
print('DETERMINIZM:', 'BIREBIR' if a==b else 'FARKLI', hashlib.sha256(a).hexdigest()[:16])
print('satir:', len(a.splitlines()))
"
rm -f scripts/quality/_ikinci.txt
```
Beklenen: `DETERMINIZM: BIREBIR`, satır sayısı **~5.034 veya altı** (konu
kapsaması dışı kalanlar `y11_goc` tarafından reddedilecek — Adım 6 bunu ölçer).

- [ ] **Adım 6: Kapsanmayan kodları ÖNCEDEN ele**

`y11_goc._canli_topic_id()` bilinmeyen kodda `ValueError` fırlatır. Aday
kümesinde canlıda karşılığı olmayan 386 soru varsa yükleyici **tümden** durur.
Seçiciye canlı `topic_hierarchy` kodlarıyla kesişim süzgeci ekle ve elenen
sayıyı **yazdır** (sessiz eleme yok).

Beklenen çıktı satırı: `konu kapsami disi elenen: 386`

- [ ] **Adım 7: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run ruff --files backend/scripts/quality/y11_aday_uret.py backend/tests/fast/test_y11_aday_uret.py
pre-commit run ruff-format --files backend/scripts/quality/y11_aday_uret.py backend/tests/fast/test_y11_aday_uret.py
git add backend/scripts/quality/y11_aday_uret.py backend/tests/fast/test_y11_aday_uret.py backend/scripts/quality/y11_mat_kumesi.txt
git commit -m "feat(Y11/T3): ders-agnostik aday secici -- SQL dilimi parametre"
git show --stat HEAD | tail -4
```

---

### Task 4: Tam ölçekte PROVA (geri alınır)

- [ ] **Adım 1: Yazım öncesi tabanı ölç**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -F' | ' -c \
"SELECT (SELECT count(*) FROM question_bank),(SELECT count(*) FROM question_content),(SELECT count(*) FROM question_metadata),(SELECT count(*) FROM question_statistics),(SELECT count(*) FROM mv_safe_for_beta);"
```
Beklenen: `40583 | 40583 | 40583 | 40583 | 27073`

- [ ] **Adım 2: Provayı koştur (`--kalici` YOK = geri alır)**

```bash
cd C:/Users/husey/kiro2/backend
python scripts/quality/y11_yukleyici.py \
  --idler scripts/quality/y11_mat_kumesi.txt --damga y11_mat_tyt_20260820
```

Kabul kriteri — raporun **hepsi** tutmalı:
`yazilan` dört tabloda eşit · `yetim: 0` · `damgali` = satır sayısı ·
`icerik_sadakati.sapma: []` · `kural_sayimi` içinde `is_active_true` =
`review_status_approved` = `quality_pending` = satır sayısı.

- [ ] **Adım 3: Rollback'i doğrula**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -c \
"SELECT count(*) FROM question_metadata WHERE pipeline_metadata->>'y11_batch'='y11_mat_tyt_20260820';"
```
Beklenen: `0` (damga kalıntısı yok).

- [ ] **Adım 4: Örneklem OKU — sayıya güvenme**

Aday kümesinden 10 soruyu metin + 5 şık + anahtar olarak çek ve **tek tek çöz**.
Kabul: **≥8/10 servis edilebilir ve anahtarı doğru**. Altındaysa **DUR** —
dilim süzgeci yetersiz demektir, Task 1'e geri dön.

---

### Task 5: KALICI yazım

- [ ] **Adım 1: Kalıcı yaz**

```bash
cd C:/Users/husey/kiro2/backend
python scripts/quality/y11_yukleyici.py \
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
Beklenen: `40583+N | N | 0 | 27073` (kapı **değişmemeli** — yeni parti `pending`).

- [ ] **Adım 3: Görsel hattını container'dan doğrula**

Yeni partiden 40 `question_image_url` çek, container'da `os.path.isfile` ile sor.
Beklenen: **40/40**. ⚠️ Bash `[ -f ]` kullanma — Türkçe `İ/ı/ğ` NFC-NFD yüzünden
yanlış "yok" der (bu oturumda 8/8 yanlış-negatif ölçüldü).
⚠️ Ara dosyayı **depo içinde** tut — bash `/tmp` (MSYS) ile Python `/tmp` (`C:\tmp`)
ayrı ad alanları (bu oturumda 4 kez ısırdı).

- [ ] **Adım 4: İdempotensi doğrula**

Seçiciyi tekrar koştur. Beklenen: göç edilen id'ler artık canlıda olduğu için
aday kümesi **0** veya sadece yeni eklenenler. Çift göç yapısal olarak engellenmeli.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/scripts/quality/y11_mat_kumesi.txt
git commit -F <mesaj-dosyasi>     # ters tirnak komut calistirir; -m KULLANMA
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
JOIN question_statistics qs ON qs.id = qb.id
JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
WHERE qm.pipeline_metadata->>'y11_batch' = 'y11_mat_tyt_20260820'
GROUP BY 1,2 ORDER BY 3 DESC;
```
Kabul: **≥5 farklı konu kodu** ve toplam **≥40 soru** — "konu kırılımı" vaadi
tek kovadan (`MAT`) karşılanamaz.

- [ ] **Adım 2: Motor gerçekten seçebiliyor mu**

Yeni parti `quality_review_status='pending'`, yani `mv_safe_for_beta` kapısının
**dışında** — sınav motoru onu göremez. Bu **kasıtlı**. Terfi (`pending` →
`auto_judged_high` + `REFRESH MATERIALIZED VIEW`) **ayrı onay** ister; bu planın
kapsamı değil. Bu adımda yalnız şunu ölç ve raporla:

```sql
SELECT count(*) FROM mv_safe_for_beta;   -- degismemis olmali
```

- [ ] **Adım 3: Devir notunu yaz**

`.claude/sessions/latest.md` başına yeni oturum bloğu: ölçülen sayılar, düşen
testler, engelleyiciler, kararlar, sonraki adımlar (maks 5).
⚠️ Dosya artık **son 3 oturum** tutuyor; en eskisini
`.claude/sessions/arsiv/`'e **birebir** taşı, silme.

---

## Riskler ve önleyici ölçümler

| Risk | Sessizce nasıl gider | Önleyici ölçüm |
|---|---|---|
| MAT'ta sızıntılı kitap var, ölçmedik | Basılı anahtar öğrenciye gider | **T1** — kör görsel okuma, 6/6 örneklem |
| Konu kapsamı dışı 386 soru | Yükleyici tümden `ValueError` ile durur | **T3 Adım 6** — önceden ele, sayıyı yazdır |
| `exam_type` güvenilmez (B4'te ölçüldü) | AYT sorusu TYT testine girer | **T6 Adım 1** — konu kırılımında Türev/İntegral görünürse DUR |
| Aday kümesi çift göç eder | Mükerrer içerik | **T5 Adım 4** — idempotens |
| Commit yarım gider | İş kaybolur | Her commit'ten sonra `git show --stat HEAD` |

## Kapsam dışı (bilerek)

- `pending → auto_judged_high` terfisi ve `REFRESH MATERIALIZED VIEW` — ayrı onay.
- 386 soruluk `TYT-MAT-*`/`AYT-MAT-*` kod ailesi — ebeveynsiz, `level` tutarsız.
- 65K MATEMATIK'in tamamı — A1 40 soru istiyor, bu dilim 100+ katı karşılıyor
  (B5'te ölçüldü: ölçeklendirmek A1 için gereksiz).
- `#485` JOIN göçü — A3'te donduruldu.
