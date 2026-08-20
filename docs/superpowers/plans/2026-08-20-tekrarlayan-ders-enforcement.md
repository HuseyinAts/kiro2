# Tekrarlayan Kayıtlı Derslere Enforcement — Uygulama Planı (S240)

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: `superpowers:subagent-driven-development`
> (önerilen) veya `superpowers:executing-plans`. Adımlar `- [ ]` kutucuğuyla izlenir.

**Hedef:** Bir oturumda 4 kez tekrar eden kayıtlı dersi, **ihlal edildiği anda**
görünür kılmak — commit anında değil, yazma/komut anında.

**Mimari:** Yeni hook YAZILMIYOR. İki mevcut hook zaten doğru noktada duruyor ve
kör: `post-edit-format.py` (PostToolUse, Edit/Write) ve `pre-commit-check.py`
(PreToolUse, Bash). Saf dedektör fonksiyonları ayrı bir modüle konur, iki hook
onları çağırır. Dedektörler DB'siz/IO'suz olduğu için pytest ile çivilenebilir.

**Tech Stack:** Python 3.13 · pytest · ruff (yerel **0.14.13**, kapı **0.7.1** —
farklı sürümler) · Claude Code hook sözleşmesi

---

## Neden bu plan var — ÖLÇÜLDÜ (20 Ağu 2026)

Projenin kendi doktrini (`.claude/rules/verification.md`):

> 1. kez: Fix + not al · 2. kez: ROOT CAUSE çöz + enforcement ekle ·
> **3. kez: ASLA olmasın — CI/CD'de blokla**

Tek oturumda tekrar edenler:

| Ders | Bu oturumda | Toplam | Kayıt |
|---|---|---|---|
| N802 — BÜYÜK harfli test adı | **2** | **8** | `L-s233-ayni-linter-iki-config` / Y13 |
| `git commit -m` içinde ters tırnak | 1 | ≥2 | `L-s231-ters-tirnak-komut-calistirir` |
| `/tmp` ad-alanı (bash MSYS ≠ Python `C:\tmp`) | 1 | ≥5 | S237'de 4 kez |
| CRLF çok satırlı ankraj | 1 | ≥2 | `audit-methodology.md` |

### Kök nedenler — üçü de "eksik kontrol" DEĞİL

**1. N802 — kontrol VAR, susturulmuş.**
`.claude/hooks/post-edit-format.py:48` şunu koşuyor:

```python
subprocess.run(["ruff", "check", "--fix", "--quiet", file_path], ...)
```

N802 (fonksiyon adı küçük harf olmalı) **auto-fixable değil** — yeniden
adlandırma güvenli otomatik düzeltme sayılmaz. `--fix` onu düzeltemez, `--quiet`
raporu yutar. Yani ruff her yazımda ihlali **görüyor ve susuyor**; sinyal ancak
commit anında, kapının farklı ruff sürümüyle geliyor.

**2. Ters tırnak — hook doğru yerde, bakmıyor.**
`pre-commit-check.py` PreToolUse/Bash'te ve komut dizesinin TAMAMINI görüyor
(`is_git_commit_or_add()` zaten `git commit` ile başlıyor mu diye bakıyor). Ama
dize içinde ters tırnak arayan hiçbir kontrol yok. `d03674d9d`'de bash ters
tırnak içindeki defter kimliğini komut olarak çalıştırdı, kimlik mesajdan
**silindi**, commit EXIT=0 verdi ve push geçti — sessiz kayıp.

**3. `/tmp` — aynı hook, aynı körlük.**
Git Bash'te `/tmp` = `%LOCALAPPDATA%\Temp`; Python'da `/tmp` = `C:\tmp`. Bir
adımda yazıp diğerinde okumak "dosya yok" veriyor. Bu oturumda gate listesi
boş kaldı ve pytest **tüm depoyu** toplamaya kalkıp 2 dk'da zaman aşımına uğradı.

### Kapsam dışı (bilerek)

- **CRLF çok satırlı ankraj**: Edit aracının `old_string` eşleşmesiyle ilgili;
  hook'tan görünmüyor (araç girdisi hook'a gelmiyor, dosya içeriği gelmiyor).
  Enforcement noktası yok → bu turda ele alınmıyor, defterde `zorlayici: null`
  kalır ve **boşluk görünür bırakılır** (`L-s230`'un yaptığı gibi).
- Kalan ~3.500 MAT sorusu ve `MAT.IST` dengesizliği — **ayrı iş**, içerik hattı.
  Bu plan süreç hattı; ikisini karıştırmak iki işi de yavaşlatır.

---

## Dosya yapısı

| Dosya | Sorumluluk | Durum |
|---|---|---|
| `.claude/hooks/ders_dedektorleri.py` | Saf dedektör fonksiyonları (IO yok, subprocess yok) | **YENİ** |
| `backend/tests/unit/test_hooks/test_ders_dedektorleri.py` | Dedektör bekçisi | **YENİ** |
| `.claude/hooks/post-edit-format.py` | ruff'ın DÜZELTEMEDİĞİ bulguları stderr'e bas | **DEĞİŞİR** |
| `.claude/hooks/pre-commit-check.py` | ters tırnak + `/tmp` uyarısı ekle | **DEĞİŞİR** |
| `.claude/lessons/ders_kaydi.yaml` | 3 dersin `zorlayici` alanı doldurulur | **DEĞİŞİR** |

Dedektörler **ayrı modülde** çünkü: (a) iki hook da kullanacak, (b) hook'ların
kendisi subprocess/stdin'e bağlı ve test edilmesi pahalı, (c) saf fonksiyon
mutasyonla çivilenebilir.

---

### Task 1: Saf dedektör modülü

**Dosyalar:**
- Oluştur: `.claude/hooks/ders_dedektorleri.py`
- Test: `backend/tests/unit/test_hooks/test_ders_dedektorleri.py`

- [ ] **Adım 1: Düşen testi yaz**

`backend/tests/unit/test_hooks/test_ders_dedektorleri.py`:

```python
"""Tekrarlayan kayitli derslerin dedektorleri — saf, IO'suz.

NEDEN: bu uc ders bir oturumda 4 kez tekrar etti (N802 sekizinci kez).
Doktrin (.claude/rules/verification.md): "3. kez: ASLA olmasin".
Dedektorler saf tutuldu ki hook kosmadan da civilenebilsinler.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".claude" / "hooks"))

from ders_dedektorleri import (  # noqa: E402
    duzeltilemeyen_bulgular,
    ters_tirnak_riski,
    tmp_ad_alani_riski,
)

TT = chr(96)  # ters tirnak — kaynak dosyada CIPLAK yazilmaz, kendisi tuzak


@pytest.mark.parametrize(
    "komut",
    [
        f'git commit -m "bkz {TT}L-s230-ast{TT}"',
        f"git commit -m 'a' -m \"b {TT}x{TT} c\"",
        f'git commit -am "fix {TT}foo{TT}"',
    ],
)
def test_ters_tirnak_git_commit_m_icinde_yakalanir(komut: str) -> None:
    """`d03674d9d`: bash ters tirnagi KOMUT olarak calistirdi, mesaj yutuldu."""
    assert ters_tirnak_riski(komut) is not None


@pytest.mark.parametrize(
    "komut",
    [
        "git commit -F mesaj.txt",
        f'echo "{TT}date{TT}"',
        "git add backend/",
        'git commit -m "duz mesaj, ters tirnak yok"',
    ],
)
def test_ters_tirnak_yanlis_pozitif_uretmez(komut: str) -> None:
    """-F guvenli yol; git disi komutlar bu dedektorun isi DEGIL.

    `echo` satiri bilerek listede: dedektor YALNIZ `git commit -m`e bakar,
    genel bir ters-tirnak polisi degildir. Genel olsaydi her kabuk komutunda
    oterdi ve UYARI KORLUGU yaratirdi — susturulan kontrol olu kontroldur.
    """
    assert ters_tirnak_riski(komut) is None


def test_ters_tirnak_mesaji_cozumu_soyler() -> None:
    """Uyari 'ne yapmali' demezse aliskanliga donusmez."""
    mesaj = ters_tirnak_riski(f'git commit -m "x {TT}y{TT}"')
    assert mesaj is not None
    assert "-F" in mesaj, "cozum (-F ile dosyadan ver) mesajda YOK"


@pytest.mark.parametrize(
    "komut",
    [
        "python -c \"open('/tmp/x.txt','w')\"",
        "docker cp /tmp/liste.txt kap:/tmp/liste.txt",
        "cat /tmp/gate.txt",
    ],
)
def test_tmp_ad_alani_yakalanir(komut: str) -> None:
    """bash /tmp = AppData\\Local\\Temp, Python /tmp = C:\\tmp — AYRI."""
    assert tmp_ad_alani_riski(komut) is not None


@pytest.mark.parametrize(
    "komut",
    [
        "pytest backend/tests -q",
        "echo merhaba",
        "docker exec kap python -c \"open('/tmp/x')\"",
    ],
)
def test_tmp_yanlis_pozitif_uretmez(komut: str) -> None:
    """`docker exec` icindeki /tmp KONTEYNER yolu — host ad-alani sorunu yok."""
    assert tmp_ad_alani_riski(komut) is None


def test_duzeltilemeyen_bulgu_n802_yakalanir() -> None:
    """ASIL KUSUR: ruff N802'yi GORUYOR ama --fix duzeltemiyor, --quiet yutuyor."""
    cikti = (
        "backend/tests/x.py:12:5: N802 Function name should be lowercase\n"
        "Found 1 error.\n"
    )
    bulgular = duzeltilemeyen_bulgular(cikti)
    assert len(bulgular) == 1
    assert "N802" in bulgular[0]


def test_duzeltilemeyen_bulgu_temiz_ciktida_bos() -> None:
    """Kontrol kolu: temiz cikti 0 bulgu vermeli, yoksa dedektor gurultu uretir."""
    assert duzeltilemeyen_bulgular("All checks passed!\n") == []
    assert duzeltilemeyen_bulgular("") == []


def test_duzeltilemeyen_bulgu_birden_fazla_satiri_korur() -> None:
    """Tek bulgu bildirmek kalanini gizler — sekiz turdur olan tam buydu."""
    cikti = (
        "a.py:1:1: N802 Function name should be lowercase\n"
        "b.py:2:2: S608 Possible SQL injection\n"
        "Found 2 errors.\n"
    )
    assert len(duzeltilemeyen_bulgular(cikti)) == 2


def test_duzeltilemeyen_bulgu_TAM_satiri_dondurur() -> None:
    """Yalniz on ek donerse mesaj kural KODUNU tasimaz ve ise yaramaz."""
    cikti = "a.py:1:1: N802 Function name should be lowercase\n"
    assert duzeltilemeyen_bulgular(cikti)[0].endswith("lowercase")
```

- [ ] **Adım 2: Testi koştur, DÜŞTÜĞÜNÜ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_hooks/test_ders_dedektorleri.py -q --no-header -p no:cacheprovider
```
Beklenen: `ModuleNotFoundError: No module named 'ders_dedektorleri'` (collection error).

- [ ] **Adım 3: Uygula**

`.claude/hooks/ders_dedektorleri.py`:

```python
#!/usr/bin/env python
"""Tekrarlayan kayitli derslerin SAF dedektorleri.

NEDEN AYRI MODUL: iki hook da kullaniyor (`post-edit-format.py`,
`pre-commit-check.py`) ve hook'larin kendisi stdin/subprocess'e bagli oldugu
icin pahali test ediliyor. Buradaki fonksiyonlar IO'suz -> pytest ile ve
mutasyonla civilenebilir.

Bekci: backend/tests/unit/test_hooks/test_ders_dedektorleri.py
"""

from __future__ import annotations

import re

TERS_TIRNAK = chr(96)

# `git commit` + (-m veya -am). `-F` KASITLI olarak disarida: cozum o.
_COMMIT_M = re.compile(r"\bgit\s+commit\b[^\n]*?(?<!\w)-(?:m|am|ma)\b")


def ters_tirnak_riski(komut: str) -> str | None:
    """`git commit -m` mesajinda ters tirnak varsa uyari dizesi dondurur.

    Olculdu (`d03674d9d`, 20 Agu 2026): bash cift tirnak icindeki ters tirnagi
    KOMUT olarak calistirdi; defter kimligi mesajdan silindi, commit EXIT=0
    verdi, push gecti. Sessiz kayip.

    YALNIZ `git commit -m`e bakar. Genel bir ters-tirnak polisi OLMAK ISTEMEZ:
    oyle olsaydi her kabuk komutunda oterdi ve uyari korlugu yaratirdi.
    Susturulan kontrol, olu kontroldur.
    """
    if TERS_TIRNAK not in komut or not _COMMIT_M.search(komut):
        return None
    return (
        "TERS TIRNAK: git commit -m mesajinda ters tirnak var. Bash onu KOMUT "
        "olarak calistirir ve mesajdan sessizce siler (olculdu: d03674d9d). "
        "COZUM: mesaji dosyaya yaz ve `git commit -F <dosya>` ile ver."
    )


# Host kabugundan gecen /tmp. `docker exec`/`docker run` icindekiler KONTEYNER
# yolu — ayri ad alani sorunu yok, onlar disarida.
_TMP = re.compile(r"(?<![\w/])/tmp/")
_KONTEYNER = re.compile(r"\bdocker\s+(?:exec|run)\b")


def tmp_ad_alani_riski(komut: str) -> str | None:
    """Host komutunda `/tmp/` gecerse uyarir.

    Git Bash `/tmp` = `%LOCALAPPDATA%\\Temp`; Python `/tmp` = `C:\\tmp`. Bir
    adimda yazip digerinde okumak "dosya yok" verir. Bu oturumda gate listesi
    bos kaldi ve pytest TUM depoyu toplamaya kalkip zaman asimina ugradi.
    """
    if not _TMP.search(komut) or _KONTEYNER.search(komut):
        return None
    return (
        "/tmp AD-ALANI: bash /tmp = AppData\\Local\\Temp, Python /tmp = C:\\tmp "
        "— AYRI iki yer. Bir adimda yazip digerinde okursan 'dosya yok' alirsin. "
        "COZUM: ara dosyayi DEPO ICINDE tut."
    )


# ruff metinsel cikti satiri: yol:satir:sutun: KOD mesaj
_BULGU = re.compile(r"^\S+:\d+:\d+:\s+[A-Z]+\d+\s")


def duzeltilemeyen_bulgular(ruff_ciktisi: str) -> list[str]:
    """`ruff check` (--fix'siz) ciktisindan bulgu satirlarini ayiklar.

    ASIL KUSUR BURADA: `post-edit-format.py` `ruff check --fix --quiet`
    kosuyordu. N802 auto-fixable DEGIL (yeniden adlandirma guvenli otomatik
    duzeltme sayilmaz), `--quiet` de raporu yutuyordu. Yani ruff ihlali HER
    yazimda goruyor ve SUSUYORDU; sinyal ancak commit aninda geliyordu.
    Sekiz tekrarin sebebi bu.

    TAM SATIR dondurulur — yalniz on ek donerse mesaj kural KODUNU tasimaz.
    """
    return [
        satir.strip()
        for satir in ruff_ciktisi.splitlines()
        if _BULGU.match(satir)
    ]
```

- [ ] **Adım 4: Testleri koştur, GEÇTİĞİNİ doğrula**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_hooks/test_ders_dedektorleri.py -q --no-header -p no:cacheprovider
```
Beklenen: `16 passed`.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run --files .claude/hooks/ders_dedektorleri.py backend/tests/unit/test_hooks/test_ders_dedektorleri.py
cat > backend/_m.txt <<'MSG'
feat(hook): tekrarlayan uc dersin saf dedektorleri

N802 (8. tekrar), git commit -m ters tirnak, /tmp ad-alani. Saf/IO'suz ->
mutasyonla civilenebilir. Bekci: 16 test.
MSG
git add .claude/hooks/ders_dedektorleri.py backend/tests/unit/test_hooks/test_ders_dedektorleri.py
git commit -F backend/_m.txt      # -m KULLANMA (dersin ta kendisi)
rm -f backend/_m.txt
git show --stat HEAD | tail -4
```

---

### Task 2: `post-edit-format.py` — susturulmuş raporu aç

**Dosyalar:**
- Değiştir: `.claude/hooks/post-edit-format.py:45-59`

- [ ] **Adım 1: Mevcut davranışı ÖLÇ (kontrol kolu)**

Prova dosyası yaz ve hook'un sustuğunu kanıtla. Dosya **assertion içermez** —
N802 fonksiyon ADINA bakar, gövdeye değil:

```bash
cd C:/Users/husey/kiro2
cat > backend/scripts/quality/_n802_prova.py <<'PY'
def Buyuk_Harfli_Ad():
    return 1
PY
ruff check --fix --quiet backend/scripts/quality/_n802_prova.py; echo "quiet EXIT=$?"
ruff check backend/scripts/quality/_n802_prova.py | head -3
```
Beklenen: `--quiet` **hiçbir şey basmaz**; ikinci komut `N802` bulur.
Bu, kusurun kanıtıdır: bulgu var, rapor yok.

- [ ] **Adım 2: Uygula**

`.claude/hooks/post-edit-format.py` içinde `ruff format` çağrısından SONRA
(satır ~53'ten sonra) şunu ekle:

```python
        # `--fix` DUZELTEMEDIGI kurallari (orn. N802 yeniden adlandirma)
        # sessizce birakiyor, `--quiet` de raporu yutuyordu. Ikinci gecis
        # bayraksiz kosar ve KALAN bulgulari stderr'e basar. PostToolUse
        # BLOKLAYAMAZ (Claude Code sozlesmesi) — amac blok degil, sinyali
        # commit aninda degil YAZMA aninda vermek.
        kalan = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=20,
        )
        for bulgu in duzeltilemeyen_bulgular(kalan.stdout):
            print(f"[lint] {bulgu}", file=sys.stderr)
```

Sonra — **kullanımı yazdıktan SONRA** — import'u ekle ve varlığını doğrula
(biçimlendirici kullanılmayan import'u siler, `L-s212-bicimlendirici-import-siler`):

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ders_dedektorleri import duzeltilemeyen_bulgular
```

```bash
cd C:/Users/husey/kiro2
grep -c "duzeltilemeyen_bulgular" .claude/hooks/post-edit-format.py
```
Beklenen: **2** (import + kullanım). `1` ise biçimlendirici import'u silmiştir.

- [ ] **Adım 3: Hook'u gerçek dosyayla koştur**

```bash
cd C:/Users/husey/kiro2
echo '{"tool_input":{"file_path":"backend/scripts/quality/_n802_prova.py"}}' \
  | python .claude/hooks/post-edit-format.py 2>&1 | grep -E "lint|format"
```
Beklenen: `[lint] backend/scripts/quality/_n802_prova.py:1:5: N802 ...` görünür.
**Önce görünmüyordu — fark budur.**

- [ ] **Adım 4: Prova dosyasını sil ve geri alımı DOĞRULA**

```bash
cd C:/Users/husey/kiro2
rm -f backend/scripts/quality/_n802_prova.py
git status --porcelain --untracked-files=no backend/scripts/quality/   # BOS olmali
```

- [ ] **Adım 5: Hook bekçisini koştur (gerileme)**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_hooks/ -q --no-header -p no:cacheprovider
```
Beklenen: mevcut hook testleri hâlâ yeşil (S237'de 7/7 idi), yeni kırık 0.

- [ ] **Adım 6: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run --files .claude/hooks/post-edit-format.py
cat > backend/_m2.txt <<'MSG'
fix(hook): ruff'in duzeltemedigi bulgular artik YAZMA aninda goruluyor

`ruff check --fix --quiet` N802'yi goruyor ama duzeltemiyor ve --quiet raporu
yutuyordu. Sinyal ancak commit aninda, kapinin farkli ruff surumuyle geliyordu.
Sekiz tekrarin sebebi buydu. Ikinci gecis bayraksiz kosuyor, kalan bulgular
stderr'e basiliyor. PostToolUse bloklayamaz; amac blok degil ERKEN SINYAL.
MSG
git add .claude/hooks/post-edit-format.py
git commit -F backend/_m2.txt
rm -f backend/_m2.txt
git show --stat HEAD | tail -4
```

---

### Task 3: `pre-commit-check.py` — ters tırnak + `/tmp`

**Dosyalar:**
- Değiştir: `.claude/hooks/pre-commit-check.py` (`main()` içindeki uyarı toplama)

- [ ] **Adım 1: Mevcut körlüğü ÖLÇ (kontrol kolu)**

```bash
cd C:/Users/husey/kiro2
python - <<'PY' | python .claude/hooks/pre-commit-check.py
import json
tt = chr(96)
print(json.dumps({"tool_input": {"command": f'git commit -m "bkz {tt}L-s230{tt}"'}}))
PY
```
Beklenen: **hiçbir uyarı yok** — kusurun kanıtı.

- [ ] **Adım 2: Uygula**

`.claude/hooks/pre-commit-check.py` `main()` içinde, mevcut uyarılar
toplandıktan SONRA ekle:

```python
    # Bu iki kontrol `is_git_commit_or_add` kapisinin DISINDA: `/tmp` her bash
    # komutunda gecerli, ters tirnak ise yalniz `git commit -m`de anlamli ve
    # daraltmayi dedektorun kendisi yapiyor.
    for dedektor in (ters_tirnak_riski, tmp_ad_alani_riski):
        uyari = dedektor(command)
        if uyari:
            warnings.append(uyari)
```

Sonra import'u ekle ve varlığını doğrula:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ders_dedektorleri import ters_tirnak_riski, tmp_ad_alani_riski
```

```bash
cd C:/Users/husey/kiro2
grep -c "ters_tirnak_riski" .claude/hooks/pre-commit-check.py
```
Beklenen: **2** (import + kullanım).

- [ ] **Adım 3: İkisini de gerçek girdiyle koştur**

```bash
cd C:/Users/husey/kiro2
python - <<'PY' | python .claude/hooks/pre-commit-check.py 2>&1 | grep -i "ters tirnak"
import json
tt = chr(96)
print(json.dumps({"tool_input": {"command": f'git commit -m "bkz {tt}L-s230{tt}"'}}))
PY
echo '{"tool_input":{"command":"cat /tmp/gate.txt"}}' \
  | python .claude/hooks/pre-commit-check.py 2>&1 | grep -i "ad-alani"
```
Beklenen: her iki komut da ilgili uyarıyı basar.

- [ ] **Adım 4: Yanlış-pozitif kontrol kolu**

```bash
cd C:/Users/husey/kiro2
echo '{"tool_input":{"command":"git commit -F mesaj.txt"}}' \
  | python .claude/hooks/pre-commit-check.py 2>&1 | grep -ci "ters tirnak"
echo '{"tool_input":{"command":"docker exec kap ls /tmp/x"}}' \
  | python .claude/hooks/pre-commit-check.py 2>&1 | grep -ci "ad-alani"
```
Beklenen: **her ikisi de `0`**. Yanlış-pozitif uyarı körlüğü üretir; dedektör
ötüyorsa susturulur ve kontrol yine ölür.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
pre-commit run --files .claude/hooks/pre-commit-check.py
cat > backend/_m3.txt <<'MSG'
feat(hook): ters tirnak + /tmp ad-alani uyarilari PreToolUse/Bash'e baglandi

Hook zaten dogru noktadaydi (komut dizesinin tamamini goruyor) ama ikisine de
bakmiyordu. d03674d9d'de bash ters tirnak icindeki defter kimligini calistirdi;
kimlik mesajdan silindi, commit EXIT=0, push gecti -> sessiz kayip.
MSG
git add .claude/hooks/pre-commit-check.py
git commit -F backend/_m3.txt
rm -f backend/_m3.txt
git show --stat HEAD | tail -4
```

---

### Task 4: Defteri bağla — enforcement listesi büyüsün

**Dosyalar:**
- Değiştir: `.claude/lessons/ders_kaydi.yaml`

- [ ] **Adım 1: İlgili kayıtları GREP ile bul (ezberden yazma)**

```bash
cd C:/Users/husey/kiro2
grep -n "ters-tirnak\|tmp\|N802\|iki-config" .claude/lessons/ders_kaydi.yaml | head -10
```

- [ ] **Adım 2: Üç dersin `zorlayici` alanını doldur**

Bulunan kayıtlarda `zorlayici: null` satırını şununla değiştir:

```yaml
  zorlayici: backend/tests/unit/test_hooks/test_ders_dedektorleri.py
```

- [ ] **Adım 3: Defter bekçisini koştur**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_ders_kaydi.py -q --no-header -p no:cacheprovider
```
Beklenen: `10 passed`. (`aktif` durumdaki her ders kanıt taşımalı.)

- [ ] **Adım 4: Zorlayıcı liste büyüdü mü ÖLÇ**

```bash
cd C:/Users/husey/kiro2
python -c "
import io,re
s=io.open('.claude/lessons/ders_kaydi.yaml',encoding='utf-8').read()
y=sorted({p for p in re.findall(r'zorlayici:\s*[\"\']?([^\s\"\'\n]+\.py)[^\s\"\'\n]*', s) if p.lower()!='null'})
print(len(y),'zorlayici dosya')
"
```
Beklenen: **24** (S239 sonunda 23 idi).

- [ ] **Adım 5: Tam kapıyı koştur**

⚠️ Ara dosya `backend/` içinde — `/tmp` DEĞİL (dersin kendisi).

```bash
cd C:/Users/husey/kiro2
python -c "
import io,re
s=io.open('.claude/lessons/ders_kaydi.yaml',encoding='utf-8').read()
y=sorted({p for p in re.findall(r'zorlayici:\s*[\"\']?([^\s\"\'\n]+\.py)[^\s\"\'\n]*', s) if p.lower()!='null'})
io.open('backend/_gl.txt','w',encoding='utf-8',newline='\n').write('\n'.join(y))
"
cd backend && FILES=$(sed 's|^backend/||' _gl.txt | tr '\n' ' ')
ELASTICSEARCH_URL='http://localhost:9200' KVKK_VERIFY_DSN='postgresql://postgres@localhost:5434/kiro2' \
  python -m pytest $FILES -q --no-header -p no:cacheprovider
rm -f _gl.txt
```
Beklenen: **0 failed**, passed sayısı S239'un 226'sından ~16 fazla.

- [ ] **Adım 6: Commit**

```bash
cd C:/Users/husey/kiro2
cat > backend/_m4.txt <<'MSG'
chore(defter): uc tekrarlayan derse zorlayici baglandi (23 -> 24 dosya)
MSG
git add .claude/lessons/ders_kaydi.yaml
git commit -F backend/_m4.txt
rm -f backend/_m4.txt
git show --stat HEAD | tail -4
```

---

### Task 5: Mutasyonla çivile — dedektörler gerçekten ölçüyor mu

Yeşil test, testin yük taşıdığını KANITLAMAZ. Dedektörler saf olduğu için
mutasyona uygun. **Commit SONRASI** koşulur (commit'siz iş mutasyona sokulmaz —
geri alım onu siler, `L-s233`).

- [ ] **Adım 1: Üç mutasyonu sırayla uygula ve öldüğünü ölç**

```bash
cd C:/Users/husey/kiro2
python - <<'PY'
import pathlib, subprocess
p = pathlib.Path(".claude/hooks/ders_dedektorleri.py")
yedek = p.read_bytes()
mutasyonlar = [
    (b"if TERS_TIRNAK not in komut or not _COMMIT_M.search(komut):", b"if False:"),
    (b"if not _TMP.search(komut) or _KONTEYNER.search(komut):",
     b"if not _TMP.search(komut):"),
    (b"if _BULGU.match(satir)", b"if satir"),
]
try:
    for i, (eski, yeni) in enumerate(mutasyonlar, 1):
        assert eski in yedek, f"M{i} ANKRAJ YOK"
        p.write_bytes(yedek.replace(eski, yeni, 1))
        r = subprocess.run(
            ["python", "-m", "pytest",
             "tests/unit/test_hooks/test_ders_dedektorleri.py",
             "-q", "--no-header", "-p", "no:cacheprovider"],
            capture_output=True, text=True, cwd="backend",
        )
        gecersiz = " error" in r.stdout
        oldu = " failed" in r.stdout and not gecersiz
        print(f"M{i}: {'GECERSIZ (sozdizimi)' if gecersiz else ('OLDU' if oldu else 'KACTI -- test degersiz')}")
        p.write_bytes(yedek)
finally:
    p.write_bytes(yedek)
PY
git status --short .claude/hooks/ders_dedektorleri.py   # BOS olmali
```
Beklenen: `M1: OLDU`, `M2: OLDU`, `M3: OLDU` ve `git status` **boş**.
`KACTI` çıkarsa o dedektörün testi yük taşımıyordur — testi güçlendir,
mutasyonu tekrarla. `GECERSIZ` çıkarsa ölçüm yapılmamıştır
(`L-s202-mutasyon-error-gecersiz`).

- [ ] **Adım 2: Devir notunu yaz**

`.claude/sessions/latest.md` sonuna S240 bloğu: ölçülen sayılar (kapı
passed/failed, zorlayıcı dosya 23→24, mutasyon 3/3), yapılmayanlar
(CRLF ankrajı — enforcement noktası yok, boşluk görünür bırakıldı;
kalan ~3.500 MAT — ayrı iş).

---

## Riskler ve önleyici ölçümler

| Risk | Sessizce nasıl gider | Önleyici ölçüm |
|---|---|---|
| Dedektör yanlış-pozitif üretir → uyarı körlüğü | Uyarı susturulur, kontrol yine ölür | **T3 Adım 4** — `-F` ve `docker exec` kontrol kolu, beklenen `0` |
| `post-edit-format` yavaşlar | Hook timeout'a düşer, sessizce boş döner | `timeout=20` + ikinci geçiş yalnız **tek dosyada** |
| Biçimlendirici yeni import'u siler | `NameError` | **T2/T3** — `grep -c` ile import varlığı ölçülür, beklenen 2 |
| Defter kimliğini ezberden yazma | Yanlış kayda `zorlayici` bağlanır | **T4 Adım 1** — grep ile bul |
| Mutasyon `error` verir, `failed` sanılır | Ölçüm geçersizken "çivili" denir | **T5** — `gecersiz` ayrı raporlanır |
| Ara dosya `/tmp`'de | Bash yazar, Python okuyamaz | Tüm adımlarda ara dosya `backend/` içinde |
| Test kaynağında ÇIPLAK ters tırnak | Kendi tuzağına düşer | `TT = chr(96)` — kaynakta çıplak yazılmaz |

## Kapsam dışı (bilerek)

- **CRLF çok satırlı ankraj** — Edit aracının `old_string` eşleşmesi hook'tan
  görünmüyor; enforcement noktası YOK. Defterde `zorlayici: null` kalır ve
  boşluk **görünür** bırakılır (`L-s230`'un yaptığı gibi; o boşluk sonradan
  ısırdı ve kapatıldı — bu da ısırırsa kapatılır).
- **Kalan ~3.500 MAT sorusu** ve `MAT.IST` dengesizliği — içerik hattı, ayrı iş.
- Kapının ruff **0.7.1** ↔ yerel **0.14.13** sürüm farkı — bu plan farkı
  kapatmıyor, yalnız yerel bulguyu **erken görünür** kılıyor. Sürüm birleştirme
  ayrı ve daha riskli bir iş.
