# B3 FAZ 3 Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `KonuPerformansi`'ye ders kimliği taşıt, `advanced_reports`'un üç sessiz kusurunu kapat, `POST /complete` sözleşmesini çivile ve backend imajını git ile hizala.

**Architecture:** Kök neden modelde: `KonuPerformansi` yalnız `konu: str` taşıyor. İki varsayılanlı alan (`ders`, `konu_kodu`) eklenir, üretici doldurur, üç tüketici dize eşleşmesi yerine alan okur. ZPD ortalaması soru-ağırlıklı yapılır — kova sayısından **bağımsız** hale gelir. Her adım TDD (RED önce gösterilir), her adım ayrı commit.

**Tech Stack:** Python 3.13 · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · pytest + pytest-asyncio · PostgreSQL 18 (port 5434) · Docker Compose

**Spec:** `docs/superpowers/specs/2026-08-21-b3-faz3-design.md`

---

## 🔴 Plan yazarken ölçülen — SPEC'İ DÜZELTEN bulgu

`backend/config/mock_endpoint_flags.json` okundu (21 Ağu 2026): **tüm
`advanced_reports.*` bayrakları `false`** — yani canlıda koşan `_real` değil
**`_mock`** yollar.

| Kusur | REAL yol | MOCK yol | **CANLI olan** |
|---|---|---|---|
| (a) IRT | `:474`, `:1167` | mock IRT sabit değer döner, agregasyon **çağırmaz** | **hiçbiri — uykuda** |
| (b) ZPD | `:761` | `:869/873` | **mock** ✅ düzeltiliyor |
| (c) ders dalı | `:934` | `:1051` | **mock** ✅ düzeltiliyor |

**Severity dürüstlüğü:** (a) IRT kusuru **bayrakla kapalı bir yolda**. Gerçek bir
kusurdur (operatör bayrağı çevirir çevirmez sessizce yanlış dersin verisini
döndürür) ama *"bugün öğrenciyi bozuyor"* demek **aşırı iddia** olurdu. Spec bunu
liveness iddiası olarak yazmamıştı; denetim dokümanına açıkça geçirilir.

**Ölçüm sonucu:** Task 6'daki canlı ÖNCE/SONRA için `/irt-morfoloji` ucu **yetmez**
(mock döner). (a)'nın kanıtı **doğrudan fonksiyon çağrısıyla** üretilir (Task 4
Step 8) — uç üzerinden değil.

---

## Ortam kuralları (her görevde geçerli)

```bash
# Tüm komutlar depo kökünden: C:\Users\husey\kiro2
# pytest backend/ dizininden koşar:
cd /c/Users/husey/kiro2/backend && python -m pytest ...

# docker exec / container yolu iceren komutlarda ZORUNLU:
export MSYS_NO_PATHCONV=1
# ...ama `git commit -F <yol>` bu bayrak ACIKKEN MSYS yolunu cevirmez.
# Commit mesaj dosyasi DAIMA Windows bicimli ve DEPO DISINDA olmali:
#   MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
# (depo icinde olursa pre-commit takipsiz dosyayi stash'ler ve git okuyamaz)

# Boru hattinda `$?` SON HALKAYI olcer. Cikis kodu DAIMA ayri degiskene:
#   git commit -F "$MSGFILE" > /tmp/out.txt 2>&1
#   RC=$?
#   echo "exit=$RC"; git log --oneline -1   # hash DEGISTI mi?
```

**Yasak:** Bu planın tamamı bitene kadar `docker compose up -d` (bileşik, servis adı vermeden) **çalıştırılmaz** — container'daki `docker cp`'li B3 FAZ 2 fix'ini geri alır. Yalnız `docker compose up -d --no-deps backend` kullanılır.

---

## Dosya yapısı

| Dosya | Sorumluluk | İşlem |
|---|---|---|
| `backend/models/exam.py` | `KonuPerformansi` şeması | Modify (2 alan ekle) |
| `backend/core/osym_exam_engine.py` | Üretici (`session_to_sinav_sonucu`) | Modify (2 kwarg) |
| `backend/api/advanced_reports.py` | 3 tüketici + yeni IRT yardımcısı + ağırlıklı ortalama yardımcısı | Modify |
| `backend/tests/unit/test_konu_kimligi.py` | Model + saf yardımcı birim testleri | **Create** |
| `backend/tests/fast/test_irt_aggregate_topic_split.py` | Yeni IRT sorgusunun split bekçisi | **Create** |
| `backend/tests/integration/test_osym_exam_konu_tuketiciler.py` | Üretici + `POST /complete` sözleşmesi (gerçek Postgres) | Modify (T6, T7 ekle) |
| `docs/audits/2026-08-21_b3_konu_kirilimi.md` | FAZ 3 bölümü | Modify |

---

## Task 0: REBUILD-1 — sigorta turu

**Neden:** İmaj 18 Ağu tarihli, git 21 Ağu. Derleme kırıksa bunu #512 kodunu yazdıktan **sonra** keşfetmek iki sorunu karıştırır. Bu adım `#511`'i **kapatmaz** (sonra kod değişecek), riski düşürür.

**Files:** yok (yalnız ops)

- [ ] **Step 1: Taban ölçümü — imaj git'ten geride mi?**

```bash
export MSYS_NO_PATHCONV=1
cd /c/Users/husey/kiro2
echo "--- GIT ---"
grep -c "topic_code" backend/application/commands/sinav.py backend/core/osym_exam_engine.py
echo "--- TEMIZ IMAJ ---"
docker run --rm --entrypoint sh kiro2-backend:latest -c \
  'grep -c "topic_code" /app/application/commands/sinav.py; grep -c "topic_code" /app/core/osym_exam_engine.py'
```

Beklenen: GIT `1` ve `5`; TEMIZ IMAJ `0` ve `0`. (Bu fark #511'in kanıtıdır.)

- [ ] **Step 2: İmajı yeniden kur**

```bash
export MSYS_NO_PATHCONV=1
cd /c/Users/husey/kiro2
docker compose build backend 2>&1 | tail -20
echo "build exit gorunur olsun:"; echo $?
```

Beklenen: `Successfully tagged` veya `naming to ... done`. Hata varsa **DUR** ve kullanıcıya bildir.

- [ ] **Step 3: Yalnız backend'i yeniden başlat (bileşik `up -d` DEĞİL)**

```bash
export MSYS_NO_PATHCONV=1
cd /c/Users/husey/kiro2
docker compose up -d --no-deps backend
sleep 90    # 22 DEGIL: 150 router yukleniyor, acilis ~60-85 sn
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health
```

Beklenen: `200`. `000` görürsen 30 sn daha bekle ve tekrar dene (2 kez); hâlâ `000` ise `docker logs kiro2-backend --tail 50` oku.

- [ ] **Step 4: Yeni imajda B3 FAZ 2 fix'i var mı**

```bash
export MSYS_NO_PATHCONV=1
docker run --rm --entrypoint sh kiro2-backend:latest -c \
  'grep -c "topic_code" /app/application/commands/sinav.py; grep -c "topic_code" /app/core/osym_exam_engine.py'
```

Beklenen: `1` ve `5` (Step 1'de `0`/`0` idi).

- [ ] **Step 5: E2E taban — sınav zinciri hâlâ çalışıyor mu**

```bash
cd /c/Users/husey/kiro2
python backend/.verify_p0_examtype_live.py 2>&1 | tail -20 || \
  echo "script yok — asagidaki manuel zinciri kullan"
```

Script yoksa manuel: `POST /api/v1/auth/login` → `POST /api/v1/osym-exam/create` → `/start` → `/answer` → `/complete` → `/subject-performance`. Beklenen: hepsi `200`, `subject-performance` **≥5 farklı `topic_code`**.

- [ ] **Step 6: Commit yok — ölçüm devir notuna yazılır**

Bu görev kod üretmez. Step 1 ve Step 4 çıktılarını sonraki görevlerde denetim dokümanına yazmak üzere sakla.

---

## Task 1: Model kimlik alanları + üretici

**Files:**
- Create: `backend/tests/unit/test_konu_kimligi.py`
- Modify: `backend/models/exam.py:83-95`
- Modify: `backend/core/osym_exam_engine.py:2180-2188`
- Modify: `backend/tests/integration/test_osym_exam_konu_tuketiciler.py` (T6 ekle)

- [ ] **Step 1: Failing test yaz — model alanları**

`backend/tests/unit/test_konu_kimligi.py` (YENİ dosya):

```python
"""B3 FAZ 3 — `KonuPerformansi` ders kimligi + kovalama-degismez ortalama.

NEDEN BU DOSYA VAR (olculdu, 21 Agu 2026):
`KonuPerformansi` yalniz `konu: str` tasiyordu. B3 `konu`yu ders adindan konu
adina cevirince, ders kimligine ihtiyaci olan her tuketici diziyi ders sanmak
zorunda kaldi:
  advanced_reports.py:474/1167  _get_subject_irt_aggregate(kp.konu)
      "Kimyasal Denge" -> "KIMYASAL DENGE" -> 0 satir   (gercek 1262)
      "Kimya"          -> "KIMYA"          -> 3531 satir (gercek 263)
  advanced_reports.py:761/869   Sigma / len(kova) -- kova sayisina BAGIMLI
  advanced_reports.py:934/1051  "matematik" in normalize_tr(kp.konu) -> olu dal
"""

from __future__ import annotations

import pytest

from models import KonuPerformansi


def _kp(**ek) -> KonuPerformansi:
    """Varsayilan gecerli KonuPerformansi; `ek` ile alan ezilir."""
    alanlar = {
        "konu": "Fonksiyonlar",
        "toplam_soru": 3,
        "dogru_sayisi": 2,
        "yanlis_sayisi": 1,
        "bos_sayisi": 0,
        "basari_yuzdesi": 66.7,
    }
    alanlar.update(ek)
    return KonuPerformansi(**alanlar)


class TestKimlikAlanlari:
    def test_ders_ve_konu_kodu_alanlari_var(self):
        """Ders kimligi ARTIK ayri alanda -- `konu` dizesinden cikarilmaz."""
        kp = _kp(ders="matematik", konu_kodu="MAT.FON")
        assert kp.ders == "matematik"
        assert kp.konu_kodu == "MAT.FON"

    def test_alanlar_varsayilanli_geriye_uyumlu(self):
        """Eski cagri yerleri (6 test dosyasi) kirilmamali."""
        kp = _kp()
        assert kp.ders is None
        assert kp.konu_kodu is None

    def test_konu_ile_ders_ayri_kimliklerdir(self):
        """Level-1 konu adi ders adiyla CAKISABILIR (olculdu: KIM|Kimya)."""
        kp = _kp(konu="Kimya", ders="kimya", konu_kodu="KIM")
        assert kp.konu == "Kimya"
        assert kp.ders == "kimya"
        # Ayirt edici anahtar konu KODUDUR, konu ADI degil.
        assert kp.konu_kodu == "KIM"
```

- [ ] **Step 2: Testi koştur, FAIL doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py -v --tb=short 2>&1 | tail -25
```

Beklenen: `TestKimlikAlanlari::test_ders_ve_konu_kodu_alanlari_var` **FAIL** — Pydantic v2 bilinmeyen alanı yok sayar veya `AttributeError: 'KonuPerformansi' object has no attribute 'ders'`. `test_alanlar_varsayilanli_geriye_uyumlu` de FAIL (aynı sebep).

- [ ] **Step 3: Modele iki alan ekle**

`backend/models/exam.py`, `class KonuPerformansi` gövdesinin **SONUNA** (satır 94'ten sonra):

```python
    # B3 FAZ 3 — kimlik alanlari SONA + varsayilanli.
    # `SubjectPerformance`'taki ayni disiplin (osym_exam_engine.py:113-117):
    # basa/ortaya eklenen alan pozisyonel cagriyi sessizce yanlis alana baglar.
    # Varsayilanli olmalari mevcut 6 test cagri yerini geriye uyumlu birakir.
    #
    # `konu` ARTIK ders adi degil KONU adi tasiyor (B3, da59ef871). Ders
    # kimligine ihtiyaci olan tuketici bu alani okur -- `konu` dizesini
    # ders SANMAZ. Olculdu: level-1 konu adi ders adiyla cakisiyor
    # (topic_hierarchy: KIM|Kimya|level 1), yani dize esitligi kimlik DEGIL.
    ders: str | None = Field(
        None, description="Ders kimligi (motorun urettigi bicim: kucuk harf)"
    )
    konu_kodu: str | None = Field(
        None, description="topic_hierarchy.code -- ayirt edici anahtar"
    )
```

- [ ] **Step 4: Testi koştur, PASS doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py -v --tb=short 2>&1 | tail -15
```

Beklenen: `3 passed`.

- [ ] **Step 5: Üretici için gerçek-veri testi yaz (RED)**

`backend/tests/integration/test_osym_exam_konu_tuketiciler.py` **SONUNA** ekle:

```python
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
    assert dersler == {DERS.lower()}, (
        f"ders kimligi eksik/yanlis: {dersler} (beklenen {{'{DERS.lower()}'}})"
    )

    # Konu kodu dolu ve BENZERSIZ -- ayirt edici anahtar budur.
    kodlar = [kp.konu_kodu for kp in kovalar]
    assert all(kodlar), f"konu_kodu bos olan kova var: {kodlar}"
    assert len(set(kodlar)) == len(kodlar), f"konu_kodu tekrar ediyor: {kodlar}"

    # Kimlik `konu` dizesinden BAGIMSIZ: ders adi konu adina esit olsa bile
    # iki alan ayri ayri okunabilir.
    for kp in kovalar:
        assert kp.ders is not None and kp.konu_kodu is not None
```

- [ ] **Step 6: T6'yı koştur, FAIL doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/integration/test_osym_exam_konu_tuketiciler.py::test_konu_performanslari_ders_kimligi_de_tasir -v --tb=short 2>&1 | tail -25
```

Beklenen: **FAIL** — `ders kimligi eksik/yanlis: {None}`. `SKIPPED` görürsen Postgres/fixture sorunu var: `pg_isready -p 5434` ve `mv_safe_for_beta` içeriğini kontrol et, **testi zayıflatma**.

- [ ] **Step 7: Üreticiyi doldur**

`backend/core/osym_exam_engine.py`, `session_to_sinav_sonucu` içindeki `KonuPerformansi(...)` çağrısına iki kwarg ekle (mevcut `ortalama_sure=sp.average_response_time,` satırından sonra):

```python
            ortalama_sure=sp.average_response_time,
            # B3 FAZ 3: kimlik alanlari. `konu` KONU adi tasidigi icin ders
            # kimligi ayrica tasinmali -- tuketici dizeyi ders SANMASIN.
            # `topic_hierarchy.subject_area` KULLANILAMAZ: olculdu, NULL
            # (MAT|Matematik||1). Ders kimligi yalniz question_metadata
            # uzerinden gelir, o da motorda `sp.subject`tir (kucuk harf).
            ders=sp.subject,
            konu_kodu=sp.topic_code,
```

- [ ] **Step 8: T6 + tüm dosyayı koştur, PASS doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/integration/test_osym_exam_konu_tuketiciler.py -v --tb=short 2>&1 | tail -20
```

Beklenen: tüm testler `passed` (T1-T5 + T6), `0 failed`.

- [ ] **Step 9: Regresyon — modeli tüketen mevcut testler**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_exam_curriculum_models.py tests/unit/test_advanced_reports_schema_parity.py tests/unit/test_api_coverage_final.py -q --tb=short 2>&1 | tail -12
```

Beklenen: `0 failed`.

- [ ] **Step 10: Lint**

```bash
cd /c/Users/husey/kiro2/backend
python -m ruff check models/exam.py core/osym_exam_engine.py tests/unit/test_konu_kimligi.py tests/integration/test_osym_exam_konu_tuketiciler.py --output-format=concise
```

Beklenen: `All checks passed!` veya yalnız önceden var olan bulgular.

- [ ] **Step 11: Commit**

```bash
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
feat(exam): KonuPerformansi ders kimligi tasir -- B3 FAZ 3 adim 1/5

`konu` B3'te ders adindan konu adina cevrildi ama ders kimligi hicbir yerde
tasinmiyordu; tuketiciler dizeyi ders sanmak zorunda kaldi.

Iki varsayilanli alan SONA eklendi (pozisyonel cagriyi kaydirmasin):
  ders      : motorun urettigi bicim (kucuk harf 'matematik')
  konu_kodu : topic_hierarchy.code -- ayirt edici anahtar

topic_hierarchy.subject_area KULLANILMADI: olculdu, NULL (MAT|Matematik||1).

Bekci: tests/unit/test_konu_kimligi.py (3) + T6 gercek Postgres (mock YOK).
T6 fix ONCESI FAIL veriyordu: "ders kimligi eksik/yanlis: {None}".
EOF
git add backend/models/exam.py backend/core/osym_exam_engine.py \
        backend/tests/unit/test_konu_kimligi.py \
        backend/tests/integration/test_osym_exam_konu_tuketiciler.py
git commit -F "$MSGFILE" > /tmp/c1.txt 2>&1
RC=$?
rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c1.txt; git log --oneline -1; git show --stat HEAD | tail -6
```

Beklenen: `exit=0`, HEAD hash **değişti**, 4 dosya.

---

## Task 2: (c) ders dalı — dize eşleşmesi yerine alan

**Files:**
- Modify: `backend/api/advanced_reports.py:22` (import), `:931-944`, `:1049-1062`
- Modify: `backend/tests/unit/test_konu_kimligi.py` (sınıf ekle)

- [ ] **Step 1: Failing test yaz**

`backend/tests/unit/test_konu_kimligi.py` **SONUNA** ekle:

```python
class TestDersDali:
    """`advanced_reports` ogrenme-stili uyumu ders bazli dallanir.

    OLCULDU (21 Agu 2026): kanon subject_area kumesi {KIMYA, MATEMATIK} --
    ASCII, yani Turkce ders adi 'TURKCE' bicimindedir. Mevcut kodda
    `elif "turkce" in ...` yerine `"turkce"` (Turkce harfli) yaziyordu ve
    kanon degerle HICBIR ZAMAN eslesemezdi.

    Canli DB'de TURKCE satiri YOK -- bu dal E2E ile dogrulanamaz, bu yuzden
    sentetik veriyle civilenir. Sinir denetim dokumanina yazildi.
    """

    @pytest.mark.parametrize(
        "ders_girdi",
        ["matematik", "MATEMATIK", "Matematik", "  matematik  "],
    )
    def test_matematik_dali_bicimden_bagimsiz_secilir(self, ders_girdi):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.8, "reading": 0.2, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        skor = _ders_uyum_skoru(ders_girdi, vark, felder)
        beklenen = (vark["visual"] + abs(felder["sequential_global"])) / 2
        assert skor == pytest.approx(beklenen), (
            f"matematik dali secilmedi (girdi={ders_girdi!r})"
        )

    def test_turkce_dali_ascii_kanon_degerle_secilir(self):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.1, "reading": 0.9, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        skor = _ders_uyum_skoru("TURKCE", vark, felder)
        beklenen = (vark["reading"] + abs(felder["visual_verbal"])) / 2
        assert skor == pytest.approx(beklenen), "TURKCE dali secilmedi"

    def test_bilinmeyen_ders_ortalama_dala_duser(self):
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.4, "reading": 0.4, "auditory": 0.4, "kinesthetic": 0.4}
        felder = {"sequential_global": -0.4, "visual_verbal": 0.3}

        assert _ders_uyum_skoru("KIMYA", vark, felder) == pytest.approx(0.4)
        assert _ders_uyum_skoru(None, vark, felder) == pytest.approx(0.4)

    def test_konu_adi_ders_dalini_SECMEZ(self):
        """Regresyon civisi: dal `konu` degil `ders` okur.

        'Matematik' adli bir KONU (level-1, topic_hierarchy'de var) ders
        dalini tetiklememelidir -- ders kimligi ayri alandan gelir.
        """
        from api.advanced_reports import _ders_uyum_skoru

        vark = {"visual": 0.9, "reading": 0.1, "auditory": 0.1, "kinesthetic": 0.1}
        felder = {"sequential_global": -0.9, "visual_verbal": 0.3}

        # ders=None (kimlik yok) -> matematik dali SECILMEZ, ortalamaya duser
        ortalama = sum(vark.values()) / 4
        assert _ders_uyum_skoru(None, vark, felder) == pytest.approx(ortalama)
```

- [ ] **Step 2: Testi koştur, FAIL doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py::TestDersDali -v --tb=short 2>&1 | tail -20
```

Beklenen: **FAIL** — `ImportError: cannot import name '_ders_uyum_skoru' from 'api.advanced_reports'`.

- [ ] **Step 3: Yardımcıyı yaz + iki çağrı yerini bağla**

`backend/api/advanced_reports.py` satır 22'deki import'u genişlet:

```python
from core.turkish_nlp_utils import normalize_tr, subject_key
```

`_get_onerilen_ogrenme_yontemi` fonksiyonundan **ÖNCE** (satır ~1407 civarı, modül düzeyi) ekle:

```python
def _ders_uyum_skoru(ders: str | None, vark: dict, felder: dict) -> float:
    """Ogrenme stili uyum skoru -- DERS kimligine gore dallanir.

    B3 FAZ 3: onceki bicim `if "matematik" in normalize_tr(kp.konu)` idi ve
    iki sebeple kirilgandi:
      1) `konu` B3'ten sonra KONU adi tasiyor -> dal hic girilmiyordu (olu).
      2) `normalize_tr` bir SUBJECT IDENTIFIER'a uygulanmamali: Turkce locale
         I->i donusumu yapar (`.claude/rules/case-convention.md` yasagi).
    Kimlik artik `ders` alanindan gelir ve `subject_key` ile kanonlanir.

    Kanon kume OLCULDU (21 Agu 2026): {KIMYA, MATEMATIK} -- ASCII. Turkce
    dersi kanonda 'TURKCE' bicimindedir; eski koddaki Turkce harfli dize
    hicbir zaman eslesemezdi.
    """
    anahtar = subject_key(ders)
    if anahtar == "matematik":
        return (vark["visual"] + abs(felder["sequential_global"])) / 2
    if anahtar == "turkce":
        return (vark["reading"] + abs(felder["visual_verbal"])) / 2
    return sum(vark.values()) / 4
```

`:931-944` (`_get_hibrit_ogrenme_stili_analizi_real`) — `for konu_perf in ...` gövdesindeki `konu_norm = ...` + `if/elif/else` bloğunu şununla değiştir:

```python
    performans_uyumu = []
    for konu_perf in temel_sonuc.konu_performanslari:
        uyum_skoru = _ders_uyum_skoru(
            konu_perf.ders, vark_profili, felder_silverman_profili
        )
```

`:1049-1062` (`_get_hibrit_ogrenme_stili_analizi_mock`) — aynı biçimde:

```python
        for konu_performansi in temel_sonuc.konu_performanslari:
            # Ders kimligine gore ogrenme stili uyumu (B3 FAZ 3)
            uyum_skoru = _ders_uyum_skoru(
                konu_performansi.ders, vark_profili, felder_silverman_profili
            )
```

- [ ] **Step 4: Testi koştur, PASS doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py -v --tb=short 2>&1 | tail -18
```

Beklenen: `10 passed` (3 + 7).

- [ ] **Step 5: Mutasyon — dal gerçekten yük taşıyor mu**

```bash
cd /c/Users/husey/kiro2/backend
cp api/advanced_reports.py /c/Users/husey/kiro2/.mut_backup.py
python - << 'PY'
from pathlib import Path
p = Path("api/advanced_reports.py")
s = p.read_bytes().decode("utf-8")
# M-C: matematik dalini olduren mutasyon
s = s.replace('    if anahtar == "matematik":', '    if False:  # MUTASYON')
p.write_bytes(s.encode("utf-8"))
print("mutasyon uygulandi")
PY
grep -c "if False:  # MUTASYON" api/advanced_reports.py   # 1 dondurmeli
python -m pytest tests/unit/test_konu_kimligi.py::TestDersDali -q --tb=line 2>&1 | tail -6
```

Beklenen: mutasyon `1` kez uygulandı **ve** en az 1 test **FAIL**. `0 failed` görürsen test yük taşımıyor — testi güçlendir.

- [ ] **Step 6: Mutasyonu geri al + DOĞRULA**

```bash
cd /c/Users/husey/kiro2
git checkout HEAD -- backend/api/advanced_reports.py 2>/dev/null || \
  cp .mut_backup.py backend/api/advanced_reports.py
rm -f .mut_backup.py
grep -c "MUTASYON" backend/api/advanced_reports.py || echo "mutasyon YOK (dogru)"
```

⚠️ `git checkout HEAD --` bu dosyada **Task 2 değişikliklerini de siler** (henüz commit edilmedi). Bu yüzden **`cp .mut_backup.py` yolu kullanılır**. Geri alım sonrası:

```bash
cd /c/Users/husey/kiro2/backend
grep -c "_ders_uyum_skoru" api/advanced_reports.py   # >=3 olmali (tanim + 2 cagri)
python -m pytest tests/unit/test_konu_kimligi.py -q 2>&1 | tail -3
```

Beklenen: `10 passed`.

- [ ] **Step 7: Lint + commit**

```bash
cd /c/Users/husey/kiro2/backend
python -m ruff check api/advanced_reports.py tests/unit/test_konu_kimligi.py --output-format=concise
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
fix(reports): ders dali dize eslesmesi degil KIMLIK okur -- B3 FAZ 3 adim 2/5

`if "matematik" in normalize_tr(kp.konu)` iki sebeple kirilgandi:
  1) `konu` B3'ten sonra KONU adi tasiyor -> dal OLU (13 kovanin 13'u else)
  2) normalize_tr bir SUBJECT IDENTIFIER'a uygulanmamali (case-convention.md)

`_ders_uyum_skoru(ders, vark, felder)` cikarildi; iki cagri yeri (real +
mock) tek yardimciyi paylasiyor.

KARDES SESSIZ KUSUR de kapandi: kanon kume OLCULDU = {KIMYA, MATEMATIK},
ASCII. Eski koddaki Turkce harfli 'turkce' dizesi kanonla HICBIR ZAMAN
eslesemezdi. Canli DB'de TURKCE satiri YOK -> dal E2E ile dogrulanamaz,
sentetik birim testle civilendi (sinir denetime yazildi).

Mutasyon: `if anahtar == "matematik"` -> `if False` ile TestDersDali FAIL.
EOF
git add backend/api/advanced_reports.py backend/tests/unit/test_konu_kimligi.py
git commit -F "$MSGFILE" > /tmp/c2.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c2.txt; git log --oneline -1
```

Beklenen: `exit=0`, hash değişti.

---

## Task 3: (b) ZPD ortalaması — kovalama-değişmez

**Files:**
- Modify: `backend/api/advanced_reports.py` (yardımcı + `:699-783` + `:801-880`)
- Modify: `backend/tests/unit/test_konu_kimligi.py` (sınıf ekle)

- [ ] **Step 1: Failing test yaz — ASIL bekçi kovalama-değişmezliktir**

`backend/tests/unit/test_konu_kimligi.py` **SONUNA** ekle:

```python
class TestAgirlikliOrtalama:
    """ZPD genel profili kova SAYISINDAN bagimsiz olmali.

    Eski bicim `Sigma / len(kova)` idi: kardinalite 1 -> 13 olunca ortalama
    sessizce kaydi (olculdu: +9,91 puan). Soru-agirlikli bicim ayni veriyi
    hangi kovalamayla verirsen ver AYNI sonucu uretir -- yani bir sonraki
    kardinalite degisiminde de kaymaz. Bu testin tasidigi iddia budur.
    """

    def test_agirlikli_ortalama_temel(self):
        from api.advanced_reports import _agirlikli_ortalama

        kayitlar = [
            {"deger": 10.0, "agirlik": 1},
            {"deger": 0.0, "agirlik": 3},
        ]
        # (10*1 + 0*3) / 4 = 2.5   (agirliksiz olsa 5.0 olurdu)
        assert _agirlikli_ortalama(kayitlar, "deger") == pytest.approx(2.5)

    def test_KOVALAMA_DEGISMEZ(self):
        """AYNI 40 soru, iki farkli kovalama -> AYNI ortalama.

        Bu, B3'un kirdigi invaryantin ta kendisidir.
        """
        from api.advanced_reports import _agirlikli_ortalama

        # 2 DERS kovasi: matematik 10 soru @ %80, kimya 30 soru @ %40
        iki_kova = [
            {"deger": 8.0, "agirlik": 10},
            {"deger": 4.0, "agirlik": 30},
        ]
        # AYNI ogrenci, 4 KONU kovasi olarak: ayni sorular, ayni basarilar
        dort_kova = [
            {"deger": 8.0, "agirlik": 4},
            {"deger": 8.0, "agirlik": 6},
            {"deger": 4.0, "agirlik": 12},
            {"deger": 4.0, "agirlik": 18},
        ]
        assert _agirlikli_ortalama(iki_kova, "deger") == pytest.approx(
            _agirlikli_ortalama(dort_kova, "deger")
        ), "ortalama kovalamaya BAGIMLI -- invaryant kirik"

    def test_agirliksiz_bicim_bu_testi_GECEMEZ(self):
        """Kontrol kolu: eski `Sigma/len` bicimi iki kovalamada FARKLI verir.

        Bu assert olmadan yukaridaki test 'her zaman gecer' sanilabilirdi.
        """
        iki = [8.0, 4.0]
        dort = [8.0, 8.0, 4.0, 4.0]
        assert sum(iki) / len(iki) == pytest.approx(6.0)
        assert sum(dort) / len(dort) == pytest.approx(6.0)
        # Esit ciktilar rastlanti; asimetrik dagilimda ayrisir:
        iki_asim = [8.0, 4.0]
        uc_asim = [8.0, 4.0, 4.0]
        assert sum(iki_asim) / 2 != pytest.approx(sum(uc_asim) / 3)

    def test_sifir_agirlik_sifira_bolmez(self):
        from api.advanced_reports import _agirlikli_ortalama

        assert _agirlikli_ortalama([], "deger") == 0.0
        assert _agirlikli_ortalama([{"deger": 5.0, "agirlik": 0}], "deger") == 0.0
```

- [ ] **Step 2: Testi koştur, FAIL doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py::TestAgirlikliOrtalama -v --tb=short 2>&1 | tail -18
```

Beklenen: **FAIL** — `ImportError: cannot import name '_agirlikli_ortalama'`.

- [ ] **Step 3: Yardımcıyı yaz**

`backend/api/advanced_reports.py`, `_ders_uyum_skoru`'nun **hemen ÜSTÜNE** ekle:

```python
def _agirlikli_ortalama(kayitlar: list[dict], alan: str) -> float:
    """Soru-agirlikli ortalama -- kova SAYISINDAN bagimsiz.

    B3 FAZ 3: onceki bicim `sum(...) / len(kayitlar)` idi. Kova kardinalitesi
    1 -> 13 olunca ortalama sessizce kaydi (olculdu: +9,91 puan). Agirlikli
    bicim ayni veriyi hangi kovalamayla verirsen ver AYNI sonucu uretir --
    yani bir SONRAKI kardinalite degisiminde de kaymaz.

    `agirlik` = o kovadaki soru sayisi. Toplam agirlik 0 ise 0.0 (sifira
    bolme ayri bir kaynaktir: `len(kayitlar) > 0` iken de olusabilir).
    """
    toplam_agirlik = sum(k.get("agirlik", 0) for k in kayitlar)
    if not toplam_agirlik:
        return 0.0
    return sum(k[alan] * k.get("agirlik", 0) for k in kayitlar) / toplam_agirlik
```

- [ ] **Step 4: Testi koştur, PASS doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py::TestAgirlikliOrtalama -v --tb=short 2>&1 | tail -12
```

Beklenen: `4 passed`.

- [ ] **Step 5: REAL yolu bağla (`_get_zpd_analizi_real`)**

`:707-721` — `konu_zpd_analizleri.append({...})` sözlüğüne `agirlik` ekle (`"konu": konu_perf.konu,` satırından sonra):

```python
                "konu": konu_perf.konu,
                # B3 FAZ 3: agirlik = kovadaki soru sayisi. Genel profil
                # ortalamasi bununla kovalama-DEGISMEZ hale gelir.
                "agirlik": konu_perf.toplam_soru,
```

`:761-772` — `n = len(...)` satırını **SİL** ve `genel_zpd_profili` bloğunu değiştir:

```python
    return {
        "konu_zpd_analizleri": konu_zpd_analizleri,
        "genel_zpd_profili": {
            "ortalama_mevcut_seviye": _agirlikli_ortalama(
                konu_zpd_analizleri, "mevcut_seviye"
            ),
            "ortalama_optimal_zorluk": _agirlikli_ortalama(
                konu_zpd_analizleri, "optimal_zorluk"
            ),
            "kulturel_uyum_seviyesi": "yuksek",
            "maarif_degerleri_uyumu": "iyi",
        },
```

- [ ] **Step 6: MOCK yolu bağla (`_get_zpd_analizi_mock`)**

`:805-820` — `zpd_araligi` sözlüğüne `"konu": konu_performansi.konu,` satırından sonra ekle:

```python
                "konu": konu_performansi.konu,
                # B3 FAZ 3: real yolla ayni sozlesme (schema parity).
                "agirlik": konu_performansi.toplam_soru,
```

`:865-874` — `genel_zpd_profili` bloğunu değiştir:

```python
            "genel_zpd_profili": {
                "ortalama_mevcut_seviye": _agirlikli_ortalama(
                    konu_zpd_analizleri, "mevcut_seviye"
                ),
                "ortalama_optimal_zorluk": _agirlikli_ortalama(
                    konu_zpd_analizleri, "optimal_zorluk"
                ),
                "kulturel_uyum_seviyesi": "yuksek",
                "maarif_degerleri_uyumu": "iyi",
            },
```

- [ ] **Step 7: `len()` kalıntısı kalmadığını doğrula**

```bash
cd /c/Users/husey/kiro2/backend
grep -n "len(konu_zpd_analizleri)" api/advanced_reports.py
```

Beklenen: **çıktı yok** (`grep` exit 1). Çıktı varsa o satır atlandı.

- [ ] **Step 8: Regresyon + şema uyumu**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py tests/unit/test_advanced_reports_schema_parity.py -v --tb=short 2>&1 | tail -20
```

Beklenen: `0 failed`. Şema uyumu testi `agirlik` yüzünden düşerse: yeni anahtar **eklemeli** olduğu için test güncellenir (anahtar kaldırılmadı), gerekçe test docstring'ine yazılır.

- [ ] **Step 9: Lint + commit**

```bash
cd /c/Users/husey/kiro2/backend
python -m ruff check api/advanced_reports.py tests/unit/test_konu_kimligi.py --output-format=concise
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
fix(reports): ZPD ortalamasi kovalama-DEGISMEZ oldu -- B3 FAZ 3 adim 3/5

`Sigma / len(kova)` kova SAYISINA bagimliydi: kardinalite 1 -> 13 olunca
ortalama sessizce kaydi (olculdu: +9,91 puan). `_agirlikli_ortalama` soru
sayisiyla agirliklandirir; ayni veri hangi kovalamayla verilirse verilsin
AYNI sonucu uretir.

Asil kazanc bugunku sapmanin duzelmesi DEGIL: bir SONRAKI kardinalite
degisiminde (konu -> alt-konu) de kaymayacak olmasi. S243'un deftere
yazdigi dersin yapisal panzehiri budur.

Iki yol da baglandi (real + mock, schema parity korunur). `agirlik`
EKLEMELI bir anahtar -- hicbiri kaldirilmadi.

Bekci: TestAgirlikliOrtalama::test_KOVALAMA_DEGISMEZ + kontrol kolu testi
(agirliksiz bicimin asimetrik dagilimda ayristigini gosteren).
EOF
git add backend/api/advanced_reports.py backend/tests/unit/test_konu_kimligi.py \
        backend/tests/unit/test_advanced_reports_schema_parity.py
git commit -F "$MSGFILE" > /tmp/c3.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c3.txt; git log --oneline -1
```

---

## Task 4: (a) IRT agregasyonu — konu bazlı + split bekçisi

**Files:**
- Modify: `backend/api/advanced_reports.py` (yeni `_get_irt_aggregate` + `:474` + `:1167`)
- Create: `backend/tests/fast/test_irt_aggregate_topic_split.py`

- [ ] **Step 1: Split bekçisi testini yaz (RED)**

`backend/tests/fast/test_irt_aggregate_topic_split.py` (YENİ dosya):

```python
"""Yeni konu-bazli IRT toplam sorgusunun split (#485) bekcisi.

NEDEN AYRI DOSYA: `tests/fast/test_advanced_reports_split.py` YALNIZ
`_get_subject_irt_aggregate`'i civiliyor. `_get_irt_aggregate` YENI bir
sorgudur ve o bekcinin kapsami DISINDADIR -- ayni sinifta bir split kacagi
burada tekrar edebilir (bkz. `L-s230-ast-sayaci-ham-sql-goremez` ve ES sema
kacagi vakasi: sorgu S210 split'inden once yazilmisti, senkron AYLARDIR
UndefinedColumnError ile dusuyordu).

Testler GERCEK `models.question_bank` modeline karsi kosar; sahte
`sys.modules` stub'i kirik kodda da yesil kalirdi.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


class _CaptureSession:
    def __init__(self, row):
        self.row = row
        self.stmt = None

    async def execute(self, stmt):
        self.stmt = stmt
        result = MagicMock()
        result.one.return_value = self.row
        return result


@pytest.fixture
def wired(monkeypatch):
    """Cache bosa alinir, DB oturumu yakalayiciya yonlendirilir."""
    import core.cache
    import core.database

    session = _CaptureSession(
        MagicMock(
            avg_difficulty=0.4, avg_discrimination=1.2, avg_guessing=0.2, sample_size=7
        )
    )

    @asynccontextmanager
    async def fake_ctx():
        yield session

    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    monkeypatch.setattr(core.database, "get_db_session_context", fake_ctx)
    monkeypatch.setattr(core.cache, "cache_manager", cache)
    return session, cache


class TestKonuBazliSorgu:
    @pytest.mark.asyncio
    async def test_konu_kodu_varsa_topic_hierarchy_join_edilir(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")

        assert session.stmt is not None, "session.execute hic cagrilmadi"
        sql = _compiled_sql(session.stmt)
        assert "JOIN topic_hierarchy" in sql, f"topic_hierarchy JOIN yok:\n{sql}"
        assert "topic_hierarchy.code = 'MAT.FON'" in sql, sql
        # Split (#485): irt_* QuestionStatistics'te
        assert "avg(question_statistics.irt_difficulty)" in sql, sql
        assert "avg(question_statistics.irt_discrimination)" in sql, sql
        assert "avg(question_statistics.irt_guessing)" in sql, sql

    @pytest.mark.asyncio
    async def test_tek_from_kartezyen_yok(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")
        froms = session.stmt.get_final_froms()
        assert len(froms) == 1, f"kartezyen carpim: {len(froms)} ayri FROM"

    @pytest.mark.asyncio
    async def test_konu_kodu_yoksa_DERSE_duser(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code=None, ders="matematik")
        sql = _compiled_sql(session.stmt)
        assert "question_metadata.subject_area = 'MATEMATIK'" in sql, sql
        assert "topic_hierarchy" not in sql, f"gereksiz JOIN:\n{sql}"

    @pytest.mark.asyncio
    async def test_is_active_filtresi_ZORUNLU(self, wired):
        """Soru sorgusunda `is_active` atlanamaz (.claude/rules/database.md)."""
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")
        sql = _compiled_sql(session.stmt)
        assert "question_bank.is_active IS true" in sql, sql


class TestCacheAnahtariAyrisir:
    @pytest.mark.asyncio
    async def test_konu_ve_ders_anahtarlari_CAKISMAZ(self, wired):
        """Ayni anahtar altinda iki farkli semantik veri tutulamaz.

        Olculdu: 'Kimya' hem level-1 KONU adi hem DERS adi. Tek anahtar
        semasi ikisini birbirine karistirirdi.
        """
        from api.advanced_reports import _get_irt_aggregate

        _, cache = wired
        await _get_irt_aggregate(topic_code="KIM", ders="kimya")
        await _get_irt_aggregate(topic_code=None, ders="kimya")

        anahtarlar = [c.args[0] for c in cache.set.call_args_list]
        assert len(set(anahtarlar)) == 2, f"cache anahtarlari cakisti: {anahtarlar}"
        assert any(a.startswith("irt_aggregate:topic:") for a in anahtarlar), anahtarlar
        assert any(
            a.startswith("irt_aggregate:subject:") for a in anahtarlar
        ), anahtarlar
```

- [ ] **Step 2: Testi koştur, FAIL doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/fast/test_irt_aggregate_topic_split.py -v --tb=short 2>&1 | tail -20
```

Beklenen: **FAIL** — `ImportError: cannot import name '_get_irt_aggregate'`.

- [ ] **Step 3: Yeni agregasyon fonksiyonunu yaz**

`backend/api/advanced_reports.py`, mevcut `_get_subject_irt_aggregate` fonksiyonunun **hemen ALTINA** ekle:

```python
async def _get_irt_aggregate(
    *, topic_code: str | None, ders: str | None
) -> dict[str, float | int]:
    """IRT toplami -- konu kodu varsa KONU bazli, yoksa DERSE duser.

    B3 FAZ 3 kok nedeni: `_get_subject_irt_aggregate` yalniz DERS adi kabul
    eder ve iceride `.upper()` yapar. Konu adi gecirilince iki sessiz kusur
    olusur (ikisi de 21 Agu 2026'da canli DB'de olculdu):
      "Kimyasal Denge" -> "KIMYASAL DENGE" -> 0 satir     (gercek 1262)
      "Kimya"          -> "KIMYA"          -> 3531 satir  (gercek 263)
    Ikincisi TEHLIKELI olan: sifir donmek gurultulu, YANLIS dersin verisini
    donmek sessizdir. Sebep `topic_hierarchy`de level-1 KONU adinin DERS
    adiyla cakismasi (KIM|Kimya, MAT|Matematik).

    `topic_hierarchy.code` ASCII ve cakismasizdir -- ayirt edici anahtar odur.

    Eski fonksiyon SILINMEDI: `tests/fast/test_advanced_reports_split.py`
    12 yerde onu cagirip #485 split JOIN yapisini civiliyor.
    """
    from core.cache import cache_manager
    from core.database import get_db_session_context
    from models.question_bank import (
        QuestionBankItem,
        QuestionMetadata,
        QuestionStatistics,
        TopicHierarchy,
    )

    if topic_code:
        cache_key = f"irt_aggregate:topic:{topic_code}"
    else:
        cache_key = f"irt_aggregate:subject:{subject_db(ders) or ''}"

    cached: dict[str, float | int] | None = await cache_manager.get(cache_key)
    if cached is not None:
        return cached

    async with get_db_session_context() as session:
        # #485 split: irt_* QuestionStatistics'te, subject_area
        # QuestionMetadata'da. SELECT listesinde yalniz QuestionStatistics
        # kolonlari oldugu icin explicit select_from ZORUNLU -- yoksa
        # SQLAlchemy sol tarafi o tablo sanip kendisine JOIN etmeye calisir
        # ve sorgu CALISMA aninda degil KURULURKEN patlar.
        stmt = (
            select(
                func.avg(QuestionStatistics.irt_difficulty).label("avg_difficulty"),
                func.avg(QuestionStatistics.irt_discrimination).label(
                    "avg_discrimination"
                ),
                func.avg(QuestionStatistics.irt_guessing).label("avg_guessing"),
                func.count().label("sample_size"),
            )
            .select_from(QuestionBankItem)
            .join(QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id)
            .where(QuestionBankItem.is_active.is_(True))
        )
        if topic_code:
            stmt = stmt.join(
                TopicHierarchy,
                TopicHierarchy.id == QuestionBankItem.primary_topic_id,
            ).where(TopicHierarchy.code == topic_code)
        else:
            stmt = stmt.join(
                QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id
            ).where(QuestionMetadata.subject_area == subject_db(ders))
        row = (await session.execute(stmt)).one()

    result = {
        "avg_difficulty": float(row.avg_difficulty or 0.0),
        "avg_discrimination": float(row.avg_discrimination or 1.0),
        "avg_guessing": float(row.avg_guessing or 0.2),
        "sample_size": int(row.sample_size or 0),
    }
    # 1h TTL — IRT parametreleri yalniz Curator guncellemesinde degisir.
    await cache_manager.set(cache_key, result, ttl=3600)
    return result
```

`backend/api/advanced_reports.py` satır 22 import'una `subject_db` de ekle:

```python
from core.turkish_nlp_utils import normalize_tr, subject_db, subject_key
```

- [ ] **Step 4: Testi koştur, PASS doğrula**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/fast/test_irt_aggregate_topic_split.py -v --tb=short 2>&1 | tail -18
```

Beklenen: `6 passed`.

- [ ] **Step 5: İki çağrı yerini bağla**

`:474` (`_get_irt_morfoloji_analizi_real`):

```python
    for konu_perf in konu_perfs:
        # B3 FAZ 3: anahtar KONU KODU. `konu_perf.konu` gecirmek "Kimya"
        # ornegindeki gibi YANLIS dersin 3531 satirini dondururdu.
        agg = await _get_irt_aggregate(
            topic_code=konu_perf.konu_kodu, ders=konu_perf.ders
        )
        sample_n = agg["sample_size"]
```

`:1167` (`_get_osym_ets_karsilastirmasi_real`):

```python
        for kp in konu_perfs:
            agg = await _get_irt_aggregate(topic_code=kp.konu_kodu, ders=kp.ders)
            w = max(1, kp.toplam_soru)  # weight by # of questions in this konu
```

- [ ] **Step 6: Eski fonksiyonun üretim tüketicisi kalmadığını doğrula**

```bash
cd /c/Users/husey/kiro2/backend
grep -n "_get_subject_irt_aggregate" api/advanced_reports.py
```

Beklenen: **yalnız 1 satır** — `async def _get_subject_irt_aggregate(...)` tanımı. Çağrı yeri kalmamalı. Fonksiyon **silinmez** (split bekçisi onu çağırıyor).

- [ ] **Step 7: Eski split bekçisi hâlâ yeşil mi**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/fast/test_advanced_reports_split.py tests/fast/test_irt_aggregate_topic_split.py tests/unit/test_konu_kimligi.py tests/unit/test_advanced_reports_schema_parity.py -q --tb=short 2>&1 | tail -12
```

Beklenen: `0 failed`.

- [ ] **Step 8: Canlı çakışma ölçümü — iddia gerçek mi**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -F'|' -c \
"SELECT 'DERS-yolu(Kimya adiyla)' AS yol, count(*) FROM question_bank qb
   JOIN question_metadata qm ON qm.id=qb.id
  WHERE qb.is_active AND qm.subject_area='KIMYA'
 UNION ALL
 SELECT 'KONU-yolu(KIM kodu)', count(*) FROM question_bank qb
   JOIN topic_hierarchy th ON th.id=qb.primary_topic_id
  WHERE qb.is_active AND th.code='KIM';"
```

Beklenen: `DERS-yolu|3531` ve `KONU-yolu|263`. Bu iki sayı fix'in **ÖNCE/SONRA** farkıdır; denetim dokümanına yazılır.

- [ ] **Step 9: Lint + commit**

```bash
cd /c/Users/husey/kiro2/backend
python -m ruff check api/advanced_reports.py tests/fast/test_irt_aggregate_topic_split.py --output-format=concise
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
fix(reports): IRT toplami KONU KODU ile anahtarlanir -- B3 FAZ 3 adim 4/5

`_get_subject_irt_aggregate(kp.konu)` konu adini ders adi saniyordu.
Canli olcum (21 Agu 2026):
  "Kimyasal Denge" -> "KIMYASAL DENGE" -> 0 satir     (gercek 1262)
  "Kimya"          -> "KIMYA"          -> 3531 satir  (gercek 263)
Ikincisi TEHLIKELI olan: sifir donmek gurultulu, YANLIS dersin verisini
donmek sessizdir. Sebep level-1 KONU adinin DERS adiyla cakismasi
(topic_hierarchy: KIM|Kimya, MAT|Matematik).

`_get_irt_aggregate(topic_code=..., ders=...)` eklendi: kod varsa
topic_hierarchy JOIN, yoksa derse duser. Cache anahtari AYRISIR
(irt_aggregate:topic:* / :subject:*) -- tek sema ikisini karistirirdi.

Eski fonksiyon SILINMEDI: test_advanced_reports_split.py 12 yerde onu
cagirip #485 split JOIN yapisini civiliyor.

YENI KOR NOKTA KAPATILDI: yeni sorgu o bekcinin kapsami disindaydi.
tests/fast/test_irt_aggregate_topic_split.py (6 test) eklendi -- ayni
sinifta bir split kacagi ES senkronunda AYLARDIR sessizce dusmustu
(L-s230-ast-sayaci-ham-sql-goremez).
EOF
git add backend/api/advanced_reports.py backend/tests/fast/test_irt_aggregate_topic_split.py
git commit -F "$MSGFILE" > /tmp/c4.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c4.txt; git log --oneline -1
```

---

## Task 5: #510 — `POST /complete` sözleşme bekçisi (M6'yı öldür)

**Files:**
- Modify: `backend/tests/integration/test_osym_exam_konu_tuketiciler.py` (T7 ekle)

- [ ] **Step 1: Sözleşme testini yaz (RED)**

`backend/tests/integration/test_osym_exam_konu_tuketiciler.py` **SONUNA** ekle:

```python
# --------------------------------------------------------------------------
# T7 — #510: POST /complete donus sozlesmesi (M6 bekcisi)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_complete_konu_data_topic_alanlarini_tasir(tuketici_sinavi):
    """`application/commands/sinav.py:841-844` mapping'i sozlesmeyi tasir.

    NEDEN: FAZ 2'de mapping'e `topic_code`/`topic_name` eklendi ama BEKCISI
    YOKTU. M6 mutasyonu (iki alani mapping'den sil) 2069 testte DELTA=0
    verdi -- yani o iki satiri hicbir test tasimiyor. Bu test onu civiler.

    `CompleteExamCommandHandler` dogrudan cagrilir: HTTP katmani
    (kimlik/rate-limit) bu iddianin parcasi degil, mapping'in kendisi.

    `student_id` fikstur oturumunun KENDI sahibinden okunur -- handler
    `sinav.py:791` sahiplik kontrolu yapiyor (esitlemezsek 403 alirdik ve
    test yanlis sebeple kirmizi olurdu).
    """
    from application.commands.sinav import (
        CompleteExamCommand,
        CompleteExamCommandHandler,
    )
    from core.osym_exam_engine import osym_exam_engine

    session_id = tuketici_sinavi["session_id"]
    sahip = osym_exam_engine.active_sessions[session_id].student_id

    handler = CompleteExamCommandHandler()
    sonuc = await handler.handle(
        CompleteExamCommand(student_id=str(sahip), session_id=session_id)
    )

    kovalar = sonuc["konu_performanslari"]
    assert kovalar, f"konu_performanslari bos: {sonuc!r}"

    # Sozlesme: FAZ 2 oncesi 8 alan + FAZ 2'nin ekledigi 2 alan.
    zorunlu = {
        "subject",
        "total_questions",
        "correct_answers",
        "wrong_answers",
        "empty_answers",
        "success_rate",
        "average_response_time",
        "difficulty_level",
        "topic_code",
        "topic_name",
    }
    for kova in kovalar:
        eksik = zorunlu - set(kova)
        assert not eksik, f"sozlesme alani eksik: {eksik} — kova={kova!r}"

    # Ayirt edicilik: None OLMAYAN topic_code'lar BENZERSIZ olmali.
    # None'lar DISLANIR ki bekci bos kumede kendiliginden gecmesin
    # (olculdu: primary_topic_id IS NULL = 0/3922, yani None dali bugun
    # ulasilamaz; disllamazsak assert bilgi tasimaz).
    kodlar = [k["topic_code"] for k in kovalar if k["topic_code"] is not None]
    assert kodlar, "hicbir kova topic_code tasimiyor -- mapping dusmus olabilir"
    assert len(set(kodlar)) == len(kodlar), f"topic_code tekrar ediyor: {kodlar}"
    assert len(kodlar) == len(kovalar), (
        f"bazi kovalarda topic_code None: {[k['topic_code'] for k in kovalar]}"
    )
```

- [ ] **Step 2: Testi koştur — GEÇMELİ (fix zaten var)**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/integration/test_osym_exam_konu_tuketiciler.py::test_complete_konu_data_topic_alanlarini_tasir -v --tb=short 2>&1 | tail -25
```

Beklenen: `1 passed`.

⚠️ **İki tuzak:**
1. Bu test **yeşil doğar** (kod zaten doğru). RED kanıtı **mutasyonla** üretilir — Step 3.
2. `complete_exam` motorda oturumu **tüketir/siler**. Test bir kez `handle` çağırır; aynı fikstür üstünde ikinci çağrı 404 verir. Fikstür test başına yeniden kurulduğu için sorun yok — ama testi bölmeye/çoğaltmaya kalkma.

`ImportError` alırsan (sınıf adları taşınmış olabilir) gerçek adları bul:

```bash
grep -n "class CompleteExam" application/commands/sinav.py
```

- [ ] **Step 3: M6 mutasyonu — test gerçekten yük taşıyor mu**

```bash
cd /c/Users/husey/kiro2/backend
cp application/commands/sinav.py /c/Users/husey/kiro2/.mut_sinav.py
python - << 'PY'
from pathlib import Path
p = Path("application/commands/sinav.py")
s = p.read_bytes().decode("utf-8")
onceki = s
s = s.replace('                    "topic_code": p.topic_code,\n', "")
s = s.replace('                    "topic_name": p.topic_name,\n', "")
assert s != onceki, "MUTASYON UYGULANMADI -- ankraj eslesmedi (CRLF/girinti?)"
p.write_bytes(s.encode("utf-8"))
print("M6 uygulandi")
PY
grep -c "topic_code" application/commands/sinav.py    # 0 dondurmeli
```

Beklenen: `M6 uygulandi` **ve** `grep -c` → `0`. `AssertionError` alırsan mutasyon uygulanmadı — ölçüm **geçersizdir**, ankrajı düzelt.

- [ ] **Step 4: Mutasyonlu koşum — T7 TEK BAŞINA ölmeli**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/integration/test_osym_exam_konu_tuketiciler.py::test_complete_konu_data_topic_alanlarini_tasir -q --tb=line 2>&1 | tail -6
```

Beklenen: **1 failed** — `sozlesme alani eksik: {'topic_code', 'topic_name'}`. `passed` görürsen test yük taşımıyor, güçlendir.

- [ ] **Step 5: Mutasyonu geri al + DOĞRULA**

```bash
cd /c/Users/husey/kiro2
git checkout HEAD -- backend/application/commands/sinav.py
git status --short backend/application/commands/sinav.py
grep -c "topic_code" backend/application/commands/sinav.py
rm -f .mut_sinav.py
```

Beklenen: `git status --short` çıktısı **BOŞ**, `grep -c` → `1`.
(Bu dosya Task 5'te değiştirilmedi, bu yüzden `git checkout HEAD --` güvenlidir.)

- [ ] **Step 6: Tam dosya + kapı koşumu**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/integration/test_osym_exam_konu_tuketiciler.py -v --tb=short 2>&1 | tail -18
```

Beklenen: T1-T7 hepsi `passed`, `0 failed`.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
test(exam): POST /complete sozlesme bekcisi -- M6 OLDU (B3 FAZ 3 adim 5/5)

FAZ 2 `sinav.py:841-844` mapping'ine topic_code/topic_name ekledi ama
BEKCISI YOKTU: M6 mutasyonu 2069 testte DELTA=0 veriyordu -- o iki satiri
hicbir test tasimiyordu.

T7 eklendi: gercek Postgres, AsyncMock YOK (FAZ 2'nin kok nedeni mock
korluguydu). Handler dogrudan cagrilir; 10 alanli sozlesme + None-olmayan
topic_code'larin BENZERSIZLIGI assert edilir.

None'lar assert'ten DISLANDI: olculdu primary_topic_id IS NULL = 0/3922,
yani None dali bugun ulasilamaz. Dislamasak assert bos kumede
kendiliginden gecerdi (S238'de iki bekci tam bu yuzden XPASS vermisti).

Test YESIL DOGAR (kod zaten dogru), bu yuzden RED kaniti mutasyonla
uretildi: iki alan mapping'den silinince T7 TEK BASINA FAIL veriyor.
Geri alim `git status --short` ile BOS dogrulandi.
EOF
git add backend/tests/integration/test_osym_exam_konu_tuketiciler.py
git commit -F "$MSGFILE" > /tmp/c5.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c5.txt; git log --oneline -1
```

---

## Task 6: REBUILD-2 (#511 kapanış) + canlı ÖNCE/SONRA + denetim

**Files:**
- Modify: `docs/audits/2026-08-21_b3_konu_kirilimi.md` (FAZ 3 bölümü)

- [ ] **Step 1: Bayrak durumunu DOĞRULA (plan yazılırken ölçüldü, değişmiş olabilir)**

```bash
cd /c/Users/husey/kiro2
python -c "
import json
f = json.load(open('backend/config/mock_endpoint_flags.json', encoding='utf-8'))
for k, v in f.items():
    if k.startswith('advanced_reports'):
        print(f'{k:50s} {v}')
"
```

Beklenen (21 Ağu 2026 ölçümü): **5 satırın 5'i de `False`** → canlıda `_mock` yollar koşuyor.

Bu **değişmişse** (biri `True` olmuşsa) Step 5'teki ÖNCE/SONRA beklentisi değişir — o ucun artık gerçek veriyle yanıt vereceğini nota yaz. Bayrağı **bu turda çevirme**: kapsam dışı, ayrı bir operatör kararı.

- [ ] **Step 2: Tam kapı koşumu (commit ÖNCESİ son kontrol)**

```bash
cd /c/Users/husey/kiro2/backend
python -m pytest tests/unit/test_konu_kimligi.py \
  tests/fast/test_irt_aggregate_topic_split.py \
  tests/fast/test_advanced_reports_split.py \
  tests/unit/test_advanced_reports_schema_parity.py \
  tests/unit/test_exam_curriculum_models.py \
  tests/integration/test_osym_exam_konu_tuketiciler.py \
  tests/integration/test_osym_exam_konu_kirilimi.py \
  -v --tb=short 2>&1 | tail -20
echo "EXIT=$?"
```

Beklenen: `0 failed`. Fail varsa **DUR**, düzelt.

- [ ] **Step 3: İmajı yeniden kur — #511'in GERÇEK kapanışı**

```bash
export MSYS_NO_PATHCONV=1
cd /c/Users/husey/kiro2
docker compose build backend 2>&1 | tail -15
docker compose up -d --no-deps backend
sleep 90
curl -s -o /dev/null -w "health=%{http_code}\n" http://localhost:8000/health
```

Beklenen: `health=200`.

- [ ] **Step 4: `git == imaj` invaryantını ölç (#511 kabul kriteri)**

```bash
export MSYS_NO_PATHCONV=1
cd /c/Users/husey/kiro2
for f in application/commands/sinav.py core/osym_exam_engine.py api/advanced_reports.py models/exam.py; do
  G=$(md5sum "backend/$f" | cut -d' ' -f1)
  I=$(docker run --rm --entrypoint sh kiro2-backend:latest -c "md5sum /app/$f" | cut -d' ' -f1)
  [ "$G" = "$I" ] && echo "OK   $f" || echo "FARK $f  git=$G imaj=$I"
done
```

Beklenen: **4 satırın 4'ü de `OK`**. Bu #511'in kabul kanıtıdır.

- [ ] **Step 5: Canlı E2E — sınav zinciri + konu kırılımı**

E2E'yi tek bir Python betiğiyle koştur (bash + curl + JSON Windows'ta kırılgan). Betiği `$CLAUDE_JOB_DIR/tmp/` altına yaz — depo içine **değil** (pre-commit takipsiz dosyayı stash'ler).

```bash
cd /c/Users/husey/kiro2
cat > "$CLAUDE_JOB_DIR/tmp/e2e_faz3.py" << 'PY'
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000"

def cagir(yol, veri=None, token=None):
    istek = urllib.request.Request(BASE + yol, method="POST" if veri is not None else "GET")
    istek.add_header("Content-Type", "application/json")
    if token:
        istek.add_header("Authorization", f"Bearer {token}")
    govde = json.dumps(veri).encode() if veri is not None else None
    try:
        with urllib.request.urlopen(istek, govde, timeout=60) as y:
            return y.status, json.loads(y.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"_hata": e.read().decode(errors="replace")[:300]}

EPOSTA, PAROLA = sys.argv[1], sys.argv[2]
kod, giris = cagir("/api/v1/auth/login", {"email": EPOSTA, "password": PAROLA})
assert kod == 200, f"login {kod}: {giris}"
tok = giris.get("access_token") or giris.get("token")

kod, sinav = cagir("/api/v1/osym-exam/create",
                   {"exam_type": "TYT", "subject_distribution": {"MATEMATIK": 10}}, tok)
print(f"create      {kod}")
assert kod == 200, sinav
sid = sinav.get("session_id") or sinav.get("id")

print(f"start       {cagir(f'/api/v1/osym-exam/{sid}/start', {}, tok)[0]}")
kod, tamam = cagir(f"/api/v1/osym-exam/{sid}/complete", {}, tok)
print(f"complete    {kod}")

kovalar = tamam.get("konu_performanslari", [])
kodlar = [k.get("topic_code") for k in kovalar]
print(f"  kova={len(kovalar)}  topic_code dolu={sum(1 for k in kodlar if k)}"
      f"  benzersiz={len(set(kodlar))}")

kod, sp = cagir(f"/api/v1/osym-exam/{sid}/subject-performance", None, tok)
sp_kod = {s.get("topic_code") for s in (sp if isinstance(sp, list) else sp.get("items", []))}
print(f"subject-perf {kod}  farkli topic_code={len(sp_kod)}")

for yol in (f"/api/v1/reports/{sid}/zpd-recommendations",
            f"/api/v1/reports/{sid}/irt-morfoloji"):
    k, g = cagir(yol, None, tok)
    print(f"{yol.split('/')[-1]:22s} {k}")
    if "genel_zpd_profili" in json.dumps(g):
        print("   ", json.dumps(g.get("genel_zpd_profili", {}), ensure_ascii=False)[:200])
PY
python "$CLAUDE_JOB_DIR/tmp/e2e_faz3.py" <ogrenci-eposta> <parola>
```

Öğrenci hesabı yoksa listele: `psql ... -c "SELECT email FROM users WHERE role='STUDENT' LIMIT 5;"`
Rapor uçlarının gerçek yolları farklıysa `curl -s localhost:8000/openapi.json | python -c "import json,sys; [print(p) for p in json.load(sys.stdin)['paths'] if 'reports' in p]"` ile bul.

Kaydedilecek ölçümler:

| Ölçüm | Beklenen |
|---|---|
| `/complete` her kovada `topic_code` dolu | `topic_code dolu == kova` ve `benzersiz == kova` |
| `/subject-performance` farklı `topic_code` | **≥5** |
| `/zpd-recommendations` `genel_zpd_profili` | ağırlıklı değer (mock yol — sözleşme korunmuş olmalı) |
| `/irt-morfoloji` | **mock döner** — `sample_size` değişmez. (a)'nın kanıtı Task 4 Step 8'deki SQL'dir |
| hiçbir uç | `500` **değil** |

- [ ] **Step 6: Denetim dokümanına FAZ 3 bölümünü yaz**

`docs/audits/2026-08-21_b3_konu_kirilimi.md` **sonuna** `## FAZ 3` bölümü ekle. İçermeli:

- Task 0 Step 1 vs Step 4 çıktısı (imaj `0/0` → `1/5`)
- Task 4 Step 8 SQL çıktısı (`DERS-yolu 3531` vs `KONU-yolu 263`)
- Task 6 Step 4 md5 tablosu (4/4 OK)
- Task 6 Step 5 canlı E2E tablosu
- **Dürüst sınırlar:**
  - `TURKCE` dalı canlı DB'de doğrulanamadı (0 satır) — sentetik birim testle çivili
  - `sample_size` konu bazında **küçüldü**; CI yarı-genişliği `0.5/√n` ile büyüdü. **Gerileme değil**, dürüst ölçüm
  - Tasarım turunda kurulan *"(c) dalı B3 öncesi de ölüydü"* hipotezi ölçümle **çürüdü**

- [ ] **Step 7: Kapı — pre-commit depo KÖKÜNDEN**

```bash
cd /c/Users/husey/kiro2
pre-commit run --files backend/models/exam.py backend/core/osym_exam_engine.py \
  backend/api/advanced_reports.py backend/tests/unit/test_konu_kimligi.py \
  backend/tests/fast/test_irt_aggregate_topic_split.py \
  backend/tests/integration/test_osym_exam_konu_tuketiciler.py \
  docs/audits/2026-08-21_b3_konu_kirilimi.md 2>&1 | tail -25
```

Bulgu çıkarsa **kontrol kolu ZORUNLU** — SKIP etmeden önce:

```bash
git stash push -- <dosya>          # pathspec'siz stash KULLANMA
pre-commit run --files <dosya> 2>&1 | tail -10   # HEAD surumunde de var mi?
git stash pop
```

Önceden var olansa: SKIP edilir **ve ayrı açık iş olarak kaydedilir** (#509'a eklenir). Benim hunk'ımdaysa: **düzeltilir**.

- [ ] **Step 8: Commit**

```bash
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
docs(audit): B3 FAZ 3 kanitlari + #511 imaj hizalamasi KAPANDI

#511 kabul kriteri OLCULDU: git == imaj, 4 dosyanin 4'unde md5 esit.
Once: imajda topic_code 0/0, git'te 1/5 (docker compose up -d fix'i geri
alirdi). Sonra: 4/4 OK.

Canli ONCE/SONRA (IRT anahtar degisimi):
  DERS-yolu ('Kimya' adiyla)  -> 3531 satir
  KONU-yolu ('KIM' koduyla)   ->  263 satir
Fark 3268 satir: 'Kimya' level-1 KONUSU dersin TAMAMINI yiyordu.

DURUST SINIRLAR denetime yazildi:
  - TURKCE dali canli DB'de dogrulanamadi (0 satir) -- sentetik birim test
  - sample_size konu bazinda KUCULDU, CI 0.5/sqrt(n) ile buyudu.
    GERILEME DEGIL, durust olcum.
  - Tasarim turundaki "(c) dali B3 oncesi de oluydu" hipotezi CURUDU:
    osym_exam_engine.py:1387 subject_area.lower() uretiyordu.
EOF
git add docs/audits/2026-08-21_b3_konu_kirilimi.md
git commit -F "$MSGFILE" > /tmp/c6.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; tail -3 /tmp/c6.txt; git log --oneline -1
```

---

## Task 7: Kapanış — devir notu + görev kütüğü

**Files:**
- Modify: `.claude/sessions/latest.md`
- Modify: `.claude/lessons/ders_kaydi.yaml` (yeni ders)

- [ ] **Step 1: Deftere ders ekle**

`.claude/lessons/ders_kaydi.yaml`'a yeni kayıt (mevcut şemayı birebir izle):

```yaml
  - kimlik: L-s244-kovalama-degismez-metrik
    ozet: >
      Kova sayisina bagli ortalama (Sigma/len) kardinalite degisiminde
      SESSIZCE kayar. Agirlikli bicim kovalamadan BAGIMSIZDIR -- bugunku
      sapmayi duzeltmekle kalmaz, SONRAKI kardinalite degisiminde de kaymaz.
    kaynak: docs/audits/2026-08-21_b3_konu_kirilimi.md
    durum: aktif
    kanit: >
      ZPD ortalamasi kova 1->13 olunca +9,91 puan kaydi (S243 olcumu).
      Agirlikli bicim ayni veriyi 2-kova ve 4-kova olarak alinca AYNI
      sonucu uretiyor (test_KOVALAMA_DEGISMEZ).
    zorlayici: backend/tests/unit/test_konu_kimligi.py
```

- [ ] **Step 2: Görev kütüğünü güncelle**

`TaskUpdate` ile: #510, #511, #512 → `completed`. Açık kalan: #509 (kapı borcu, varsa yeni bulgu eklenir), #513, #441.

- [ ] **Step 3: Devir notu**

`.claude/sessions/latest.md` başına yeni handoff bloğu ekle (en eskisi arşive iner, dosya **son 3** oturumu tutar). İçermeli: Ölçülen · Fail eden testler · Engelleyiciler · Sonraki adımlar (maks 5) · Kararlar · Dürüst kayıt.

- [ ] **Step 4: Commit + push**

```bash
cd /c/Users/husey/kiro2
MSGFILE="C:/Users/husey/.kiro2_commitmsg.txt"
cat > "$MSGFILE" << 'EOF'
chore: S244 kapanis -- B3 FAZ 3 (#510/#511/#512) + yeni ders

Defter: L-s244-kovalama-degismez-metrik (aktif, zorlayici dolu).
EOF
git add .claude/sessions/latest.md .claude/lessons/ders_kaydi.yaml
git commit -F "$MSGFILE" > /tmp/c7.txt 2>&1
RC=$?; rm -f "$MSGFILE"
echo "exit=$RC"; git log --oneline -1
git push 2>&1 | tail -5
```

- [ ] **Step 5: Ağaç temizliği**

```bash
cd /c/Users/husey/kiro2
git status --untracked-files=no --short
```

Beklenen: yalnız devralınan `backend/semantic_cache.pkl` (bu işe ait değil, commit'lenmez). `.mut_*.py` artıkları kalmışsa sil.

---

## Kabul kriterleri (plan bitti sayılmak için hepsi ölçülmeli)

| # | Kriter | Kanıt |
|---|---|---|
| 1 | `KonuPerformansi.ders` + `.konu_kodu` üretici tarafından dolduruluyor | T6 gerçek Postgres'te `passed` |
| 2 | IRT satır başına dürüst `sample_size` | `KIM` kodu **263** döner, 3531 değil |
| 3 | ZPD ortalaması kovalama-değişmez | `test_KOVALAMA_DEGISMEZ` `passed` + kontrol kolu testi |
| 4 | Ders dalı canlı | `TestDersDali` 4/4 `passed` + mutasyon FAIL üretti |
| 5 | M6 öldü | mutasyonlu koşumda T7 **tek başına** FAIL |
| 6 | Yeni sorgu split kör noktası kapandı | `test_irt_aggregate_topic_split.py` 6/6 `passed` |
| 7 | `git == imaj` | 4 dosyada md5 eşit |
| 8 | Canlı zincir sağlam | create/start/answer/complete/subject-performance/zpd/irt hepsi **<500** |
| 9 | Dürüst sınırlar yazıldı | denetim dokümanında 3 madde (TURKCE · sample_size · çürüyen hipotez) |
