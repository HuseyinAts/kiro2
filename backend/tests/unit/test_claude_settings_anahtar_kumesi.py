"""X05 bekçisi — `.claude/settings.json` belgelenmemiş anahtar taşımamalı.

NEDEN VAR
---------
22 Ağu 2026, `iddialar.yaml` X05: `excludePatterns` ve `contextManagement`
anahtarları aylarca dosyada durdu ve **hiçbir şey yapmadı**. Ölçüldü:

  rg -a -o -F "excludePatterns:"   claude.exe (337MB) -> 0
  rg -a -o -F "contextManagement:" claude.exe          -> 0
  KONTROL KOLU: cleanupPeriodDays:=1 · enabledPlugins:=17 · outputStyle:=24

Claude Code ayar şeması `.strict()` TAŞIMIYOR ve proje ayarları `safeParse`
ile ayrıştırılıyor → şemada olmayan anahtar **sessizce düşürülüyor, uyarı
üretilmiyor**. Yani yanlış yazılmış veya uydurulmuş bir ayar, dosyada
"yapılandırılmış" gibi durur ama ölüdür.

ÖLÇÜLEBİLİR ZARAR (yalnız hijyen değil): `docs/rapor-v3/19-master-kontrol-
listesi.md:193` operatöre *"%70 dolulukta /clear (settings.json
clearThreshold)"* diyordu — var olmayan bir mekanizmaya dayanan canlı bir
kontrol listesi maddesi.

Bu bekçi tekrarı engeller: yeni bir belgelenmemiş anahtar eklenirse KIRMIZI.
Anahtarın gerçekten geçerli olduğunu ölçtüysen `BELGELENMIS`e ekle — ama
ölçümü commit mesajına yaz.

MUTASYONLA ÇİVİLENDİ (22 Ağu 2026):
  M1: `excludePatterns` geri eklendi     -> test_belgelenmemis_anahtar_yok FAIL ✓
  M2: `hooks` silindi                    -> test_kritik_anahtarlar_duruyor FAIL ✓
  (M2 kontrol koludur: "dosyayı boşalt" çözümü M1'i geçerdi.)

BU BEKÇİ İLK YAZILIŞINDA ÖLÜYDÜ — mutasyon adımı yakaladı (22 Ağu 2026).
`parents[2]` = `backend/` idi → `backend/.claude/settings.json` aranıyordu,
dosya yoktu, fixture `pytest.skip` ediyordu: **`3 skipped`** ve üç mutasyonun
üçü de "hayatta kaldı" — çünkü test hiç koşmadı. Bu, aynı gün kapatılan
X10'un (`2e7c11d53`) birebir aynı sınıfıdır: *sessiz skip = yapısal olarak
alarm veremeyen bekçi*. Düzeltme: `parents[3]` (depo kökü) + dosya yoksa
**skip DEĞİL FAIL** (ayar dosyası bu depoda her zaman vardır; yokluğu
altyapı arızası değil, gerçek bir kusurdur).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# parents[3] = depo kökü (bu dosya: <kök>/backend/tests/unit/…)
AYARLAR = Path(__file__).resolve().parents[3] / ".claude" / "settings.json"

# Claude Code'un ayar şemasında GERÇEKTEN bulunan üst anahtarlar.
# Ekleme yapmadan önce binary'de ölç: rg -a -o -F "<anahtar>:" <claude.exe>
BELGELENMIS = {
    "$schema",
    "apiKeyHelper",
    "cleanupPeriodDays",
    "enabledPlugins",
    "enableAllProjectMcpServers",
    "env",
    "forceLoginMethod",
    "hooks",
    "includeCoAuthoredBy",
    "model",
    "outputStyle",
    "permissions",
    "statusLine",
}

# Bu proje bunlara DAYANIYOR; biri kaybolursa oturum davranışı sessizce değişir.
KRITIK = {"env", "permissions", "model", "hooks"}


@pytest.fixture(scope="module")
def ayarlar() -> dict:
    # SKIP DEĞİL FAIL: bu dosya depoda her zaman vardır. Yokluğu "ölçülemedi"
    # değil, "yol yanlış veya dosya kayboldu" demektir — ikisi de kusurdur.
    # (Bu bekçi ilk yazılışında tam da burada sessizce skip ediyordu.)
    assert AYARLAR.exists(), (
        f"ayar dosyası bulunamadı: {AYARLAR}. Bekçi ölçüm yapamıyor — "
        "skip edilseydi sessizce yeşil kalırdı (X10 sınıfı)."
    )
    return json.loads(AYARLAR.read_text(encoding="utf-8"))


def test_alet_dogrulamasi_dosya_gercek_bir_yapilandirma(ayarlar: dict) -> None:
    """Premis kontrolü: ölçtüğümüz şey boş/bozuk bir dosya değil.

    Bu düşerse aşağıdaki iki test anlamsızdır — ölçülecek yapılandırma yok.
    """
    assert isinstance(ayarlar, dict) and ayarlar, "ayar dosyası boş"
    assert len(ayarlar) >= 3, f"yalnız {len(ayarlar)} üst anahtar — dosya güdük"


def test_belgelenmemis_anahtar_yok(ayarlar: dict) -> None:
    """Şemada olmayan anahtar SESSİZCE düşürülür — dosyada durması yanıltır."""
    kacak = sorted(set(ayarlar) - BELGELENMIS)
    assert not kacak, (
        f"belgelenmemiş ayar anahtar(lar)ı: {kacak}. Claude Code şeması "
        "`.strict()` değil; bunlar SESSİZCE düşürülür ve hiçbir şey yapmaz. "
        "Gerçekten geçerliyse binary'de ölç (rg -a -o -F '<anahtar>:') ve "
        "BELGELENMIS kümesine ölçümüyle birlikte ekle."
    )


def test_kritik_anahtarlar_duruyor(ayarlar: dict) -> None:
    """KONTROL KOLU: temizlik, işe yarayan ayarları silmeye dönüşmemeli.

    Bu assert olmadan `{}` yazan bir "fix" yukarıdaki testi geçerdi.
    """
    eksik = sorted(KRITIK - set(ayarlar))
    assert not eksik, f"kritik ayar anahtarı kaybolmuş: {eksik}"
