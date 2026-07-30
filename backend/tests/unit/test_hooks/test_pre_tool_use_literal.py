"""PreToolUse hook'u fixture string'ini gerçek kod sanmamalı (#452).

`.claude/hooks/pre-tool-use.py` **BLOKLAYICI** bir hook: exit 2 döndüğünde Write/Edit
hiç gerçekleşmez, dosya diske yazılmaz. Bu yüzden yanlış-pozitifi pahalıdır —
geliştirici meşru bir dosyayı kaydedemez ve tek çıkış yolu hook'u devre dışı
bırakmaktır.

30 TEM 2026 ÖLÇÜMÜ (hook'a gerçek JSON verildi, exit kodu okundu):

    | girdi                                   | exit | karar  |
    | gerçek kodda fake assertion             |  2   | DOĞRU  |
    | ÜÇLÜ TIRNAK fixture içinde aynı satır   |  2   | YANLIŞ |

İkincisi test VERİSİDİR, çalıştırılabilir kod değil. Backend bekçisindeki aynı kusur
30 Tem'de `literal_spans.py` ile kapatılmıştı (#448); bu hook aynı hatayı taşıyor.

CANLI KANIT: bu dosyanın ilk sürümü, yukarıdaki tabloyu gerçek kod satırı olarak
yazdığı için hook TARAFINDAN BLOKLANDI ("Reward hacking: 'assert True'"). Yani
kusur, kendisini belgeleyen testin yazılmasını engelledi. Tablo bu yüzden düz
metne çevrildi.

KAPSAM ÖLÇÜLDÜ — yalnız ÜÇLÜ TIRNAK fixture'ları tetikliyor. Kaçışlı biçim tek
fiziksel satır olduğu için satır-sonu çapalı desene uymuyor. Bu dosyadaki
fixture'ların kaçışlı yazılmasının sebebi budur.

FAIL-OPEN: içerik sözcüksel olarak çözümlenemezse (Edit'in `new_string`'i çoğu zaman
bir PARÇA'dır, tek başına geçerli Python olmayabilir) bastırma yapılmaz, yani hook
bloklamaya devam eder. Belirsizlikte bekçi kör değil AÇIK kalır — `literal_spans.py`
ile aynı politika.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

KOK = Path(__file__).resolve().parents[4]
HOOK = KOK / ".claude" / "hooks" / "pre-tool-use.py"

# Fixture'lar KACISLI yazildi (bkz modul docstring'i): degerleri gercek satir
# sonu icerir ama BU DOSYANIN metninde tek fiziksel satirdir.
_FAKE = "assert True"
GERCEK_IHLAL = f"def test_x():\n    {_FAKE}\n"
UCLU_FIXTURE = f'SAHTE = """\ndef test_x():\n    {_FAKE}\n"""\n\n\ndef test_gercek():\n    assert 1 + 1 == 2\n'
FIXTURE_ARTI_GERCEK = (
    f'SAHTE = """\ndef test_x():\n    {_FAKE}\n"""\n\n\ndef test_kotu():\n    {_FAKE}\n'
)
BOS_TEST_FIXTURE = 'SAHTE = """\ndef test_bos():\n    pass\n"""\n\n\ndef test_gercek():\n    assert 1 + 1 == 2\n'
BOS_TEST_GERCEK = "def test_bos():\n    pass\n"


def _hook(
    icerik: str, *, arac: str = "Write", yol: str = "backend/tests/test_x.py"
) -> int:
    """Hook'u GERCEK arayuzuyle kosar: stdin'den JSON, sozlesme cikis kodudur."""
    anahtar = "content" if arac == "Write" else "new_string"
    girdi = json.dumps(
        {"tool_name": arac, "tool_input": {"file_path": yol, anahtar: icerik}}
    )
    sonuc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=girdi,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return sonuc.returncode


def test_gercek_fake_assertion_bloklanir():
    """MUTASYON GÜVENCESİ: gerçek fake assertion her koşulda bloklanmalı."""
    assert _hook(GERCEK_IHLAL) == 2


def test_uclu_tirnak_fixture_bloklanmaz():
    """Üçlü tırnak içindeki fake assertion TEST VERİSİDİR — yazma engellenmemeli."""
    assert _hook(UCLU_FIXTURE) == 0


def test_fixture_yaninda_gercek_ihlal_varsa_yine_bloklanir():
    """KÖRLEŞME GÜVENCESİ: bastırma toptan değil KARAKTER düzeyinde olmalı.

    Aynı içerikte hem fixture string'i hem GERÇEK ihlal varsa hook bloklamaya
    devam etmeli. "dosyada üçlü tırnak varsa hiç bakma" gibi kaba bir çözüm
    seçilirse bu test kırmızıya döner.
    """
    assert _hook(FIXTURE_ARTI_GERCEK) == 2


def test_bos_test_govdesi_fixture_icindeyse_bloklanmaz():
    """Aynı kusur `check_empty_test` yolunda da var — fixture'daki boş test."""
    assert _hook(BOS_TEST_FIXTURE) == 0


def test_gercek_bos_test_govdesi_bloklanir():
    """MUTASYON GÜVENCESİ: gerçek boş test gövdesi bloklanmaya devam etmeli."""
    assert _hook(BOS_TEST_GERCEK) == 2


def test_cozumlenemeyen_parca_fail_open_kalir():
    """Edit parçası sözcüksel olarak geçersizse bastırma YAPILMAZ (fail-open).

    Girintiyle başlayan tek satırlık bir parça geçerli Python değildir; tokenize
    düşer. O durumda bekçi AÇIK kalmalı — belirsizlikte engelleme yönünde.
    """
    assert _hook(f"    {_FAKE}\n", arac="Edit") == 2
