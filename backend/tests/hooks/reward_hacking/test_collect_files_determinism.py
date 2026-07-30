"""`collect_files` çıktısı DETERMİNİSTİK olmalı (#457).

30 TEM 2026 ÖLÇÜMÜ — aynı korpus, aynı komut, üç koşum:

    python -m hooks.reward_hacking.cli tests --json --max-files 250
    -> toplam 742 · 742 · 744      bulgulu dosya 170 · 170 · 171
    -> analiz edilen dosya kümesinin imzası 7af76a388b45  vs  dfb6592842c8

KÖK NEDEN (ölçüldü): `collect_files()` `for ext in HookManager.SUPPORTED_EXTENSIONS`
ile dönüyor ve `SUPPORTED_EXTENSIONS` bir **set**. `str` hash'i süreçler arası
randomize edildiği için set iterasyon sırası her süreçte farklı olabiliyor;
dosyalar uzantı GRUPLARI hâlinde eklendiğinden liste sırası değişiyor.
`run_hooks` ise `valid_files[:max_files]` diyor — yani kap devreye girdiğinde
her koşum FARKLI bir alt kümeyi analiz ediyor.

`backend/tests` altında ölçülen uzantı dağılımı: `.py` 688, **`.js` 2, `.sh` 1**
— yani birden fazla grup var, koşul gerçekleşiyor.

ETKİSİ: pre-push'ta düşük (`pass_filenames: true`, staged dosyalar genelde
kaptan az) AMA bir dizin verildiğinde (CI, elle tarama) bekçi sessizce farklı
alt küme tarar; ayrıca CLI üzerinden yapılan HER korpus ölçümü geçersizdir —
bu oturumda bir A/B'yi fiilen bozdu.

NOT: bu kusur TEK SÜREÇTE görünmez (aynı süreçte set sırası sabittir). Bu yüzden
aşağıda iki farklı test var: (1) sıralılık invaryantı, (2) gerçek çok-süreç
özelliği `PYTHONHASHSEED` ile.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from hooks.reward_hacking.cli import collect_files

pytestmark = [pytest.mark.unit]

BACKEND = Path(__file__).resolve().parents[3]


@pytest.fixture
def karisik_dizin(tmp_path: Path) -> Path:
    """Birden fazla desteklenen uzantı — grup sırası ancak böyle gözlenebilir."""
    (tmp_path / "a_once.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b_sonra.js").write_text("const x = 1;\n", encoding="utf-8")
    (tmp_path / "c_ucuncu.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "d_dorduncu.sh").write_text("echo x\n", encoding="utf-8")
    (tmp_path / "e_besinci.yml").write_text("k: v\n", encoding="utf-8")
    return tmp_path


def test_cikti_sirali_yani_uzanti_gruplarina_bolunmus_degil(karisik_dizin):
    """Çıktı sıralı olmalı — uzantıya göre gruplanmış liste sıralı DEĞİLDİR.

    Bu, kusurun tek süreçte gözlenebilen izdüşümü: eski kod `.py`leri, sonra
    `.js`leri, sonra `.sh`leri ekliyordu; hangi grubun önce geldiği ise set
    sırasına bağlıydı. Sıralı çıktı bu bağımlılığı tamamen ortadan kaldırır.
    """
    sonuc = collect_files([str(karisik_dizin)])
    beklenen = sorted(sonuc)
    mesaj = f"cikti sirali degil:\n  gelen   ={sonuc}\n  beklenen={beklenen}"
    assert sonuc == beklenen, mesaj


def test_bes_dosyanin_tamami_toplaniyor(karisik_dizin):
    """KÖRLEŞME GÜVENCESİ: sıralamak dosya KAYBETTİRMEMELİ.

    `sorted()` yerine yanlışlıkla `sorted(set(...))[:n]` gibi bir şey yazılırsa
    ya da bir uzantı grubu düşerse bu test kırmızıya döner.
    """
    adlar = sorted(Path(p).name for p in collect_files([str(karisik_dizin)]))
    assert adlar == [
        "a_once.py",
        "b_sonra.js",
        "c_ucuncu.py",
        "d_dorduncu.sh",
        "e_besinci.yml",
    ]


def _alt_surecte_topla(dizin: Path, seed: str) -> str:
    """collect_files'i AYRI bir süreçte, verilen hash seed'i ile koşar."""
    kod = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from hooks.reward_hacking.cli import collect_files;"
        "print('|'.join(collect_files([sys.argv[2]])))"
    )
    cikti = subprocess.run(
        [sys.executable, "-c", kod, str(BACKEND), str(dizin)],
        capture_output=True,
        text=True,
        check=True,
        env={"PYTHONHASHSEED": seed, "SYSTEMROOT": "C:\\Windows", "PATH": ""},
    )
    return cikti.stdout.strip()


def test_farkli_hash_seedlerinde_ayni_sira(karisik_dizin):
    """ASIL ÖZELLİK: sıra `PYTHONHASHSEED`'e bağlı OLMAMALI.

    Tek süreç içinde set iterasyonu sabittir, dolayısıyla kusur in-process
    görülemez. Burada altı ayrı süreç açılıyor; hepsi aynı listeyi vermeli.
    Fix öncesi seed'ler set sırasını değiştirdiği için çıktılar ayrışır.
    """
    ciktilar = {_alt_surecte_topla(karisik_dizin, str(s)) for s in (1, 2, 3, 4, 5, 6)}
    mesaj = f"{len(ciktilar)} farkli sira uretildi (1 olmali):\n" + "\n".join(
        sorted(ciktilar)
    )
    assert len(ciktilar) == 1, mesaj


# ---------------------------------------------------------------------------
# `--json` STDOUT'U KİRLETİLMEMELİ
#
# Yukarıdaki sıralama düzeltmesi bu kusuru DETERMİNİSTİK hale getirdi: BOM'lu
# `tests/integration/test_end_to_end_platform.py` artık her koşumda ilk-250
# diliminin içinde ve AST parse hatası veriyor. `cli.py` kendi uyarılarını
# `file=sys.stderr` ile basıyor, AMA dedektörler ve hook_manager'daki 8 uyarı
# stdout'a gidiyordu — yani `--json` çıktısı HİÇ ayrıştırılamıyordu:
#     json.decoder.JSONDecodeError: Expecting value: line 1 column 1
# Bir ölçüm aracının çıktısını kendi tanı mesajlarıyla kirletmesi, #457'nin
# amacını (güvenilir ölçüm) doğrudan çürütür.
# ---------------------------------------------------------------------------


def test_json_ciktisi_ast_parse_hatasina_ragmen_gecerli_kalir(tmp_path, capsys):
    """Parse edilemeyen bir dosya varken bile `--json` stdout'u geçerli JSON olmalı."""
    import json

    from hooks.reward_hacking.cli import main

    # BOM: ast.parse "invalid non-printable character U+FEFF" ile duser
    (tmp_path / "test_bomlu.py").write_bytes(
        b"\xef\xbb\xbfdef test_x():\n    m = MagicMock()\n    assert m\n"
    )
    (tmp_path / "test_saglam.py").write_text(
        "def test_y():\n    assert True\n", encoding="utf-8"
    )

    main([str(tmp_path), "--json"])
    yakalanan = capsys.readouterr()

    try:
        veri = json.loads(yakalanan.out)
    except json.JSONDecodeError as hata:
        pytest.fail(
            f"stdout gecerli JSON degil ({hata}); ilk 120 karakter:\n"
            f"{yakalanan.out[:120]!r}"
        )
    assert "total_detections" in veri
    # Tani mesaji kaybolmamali, sadece dogru akisa gitmeli
    assert "AST parse" in yakalanan.err, "uyari stderr'e de basilmali (susturma degil)"
