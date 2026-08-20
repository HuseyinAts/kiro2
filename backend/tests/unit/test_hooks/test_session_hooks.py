"""Session hook'larinin OLCTUKLERI seyi gercekten olctugunu civileyen testler.

Kok neden (20 Agu 2026, olculdu):
  * `_check_bash()` `timeout=3` ile `bash --version` cagiriyordu; bu makinede
    SOGUK bash spawn **7,11 sn**. SessionStart/Stop hook'lari daima soguk kosar
    -> `_BASH_AVAILABLE=False` -> `run_cmd` turevi HER alan bos dondu.
    Kanit: `.claude/session_state.json` icinde `branch=""`, `services=DOWN`,
    `uncommitted_count=0` (hepsi run_cmd turevi) ama `question_count=77336`,
    `migrations.count=2` (hepsi saf-Python turevi) DOLU idi.
  * `git status --porcelain` bu depoda **>60 sn** suruyor (3.400 takipsiz dosya +
    `d-dataset/output/crops` altinda 528.651 PNG). `--untracked-files=no` ile
    **0,09 sn**. Yani 10 sn'lik run_cmd timeout'u bu cagriyi asla tamamlayamaz.

Bu testler yapisal davranisi civiler, ortam sansini degil: bash SICAKKEN de
gecmemeleri gerekir. (S219 dersi: "test paketi de bir dilim olcer".)
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[4] / ".claude" / "hooks"


def _yukle(dosya_adi: str):
    """`.claude/hooks/<dosya>.py` bir paket degil — dosya yolundan yukle."""
    yol = HOOKS_DIR / dosya_adi
    if not yol.exists():  # pragma: no cover - ortam kusuru, testin konusu degil
        pytest.skip(f"hook bulunamadi: {yol}")
    spec = importlib.util.spec_from_file_location(f"_hook_{yol.stem}", yol)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modul
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def save_hook():
    return _yukle("session-save.py")


def _casus_kur(monkeypatch, modul) -> list[list[str]]:
    """`subprocess.run` cagrilarini kaydeden casus tak; cagri listesini dondur.

    Uc testte de ayni sey gerekiyordu; kopyalamak yerine tek yerde.
    """
    cagrilar: list[list[str]] = []
    gercek_run = subprocess.run

    def casus(args, **kw):
        if isinstance(args, list | tuple):
            cagrilar.append(list(args))
        return gercek_run(args, **kw)

    monkeypatch.setattr(modul.subprocess, "run", casus)
    return cagrilar


def _gercek_dal() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(HOOKS_DIR.parent.parent),
        check=False,
    ).stdout.strip()


# --------------------------------------------------------------------------
# 1) Yapisal: hook `bash` dolayimini HIC kullanmamali
# --------------------------------------------------------------------------


def test_git_durumu_bash_uzerinden_cagrilmaz(save_hook, monkeypatch):
    """bash dolayimi kaldirilmali — soguk spawn 7,11 sn ve hook'u komple susturuyor.

    Bu test bash SICAKKEN de dusmeli: iddia "sonuc dogru mu" degil,
    "cagri bash uzerinden mi gidiyor" — yani kusurun kendisi.
    """
    cagrilar = _casus_kur(monkeypatch, save_hook)
    save_hook.get_git_state()

    bash_cagrilari = [c for c in cagrilar if c and "bash" in str(c[0]).lower()]
    assert bash_cagrilari == [], (
        f"git durumu hala bash uzerinden cagriliyor: {bash_cagrilari}. "
        "Soguk bash spawn 7,11 sn olculdu; dogrudan git.exe 0,06 sn."
    )


def test_servis_kontrolu_bash_uzerinden_cagrilmaz(save_hook, monkeypatch):
    """`curl` de bash uzerinden cagriliyordu; urllib ile bagimsiz olmali."""
    cagrilar = _casus_kur(monkeypatch, save_hook)
    save_hook.get_services_state()

    bash_cagrilari = [c for c in cagrilar if c and "bash" in str(c[0]).lower()]
    assert (
        bash_cagrilari == []
    ), f"servis kontrolu hala bash uzerinden: {bash_cagrilari}"


# --------------------------------------------------------------------------
# 2) Yapisal: `git status` takipsiz dosya TARAMAMALI (bu depoda >60 sn)
# --------------------------------------------------------------------------


def test_git_status_takipsiz_dosya_taramaz(save_hook, monkeypatch):
    """`-u` taramasi 528.651 crop PNG yuzunden 60 sn'de bitmiyor; -uno 0,09 sn."""
    cagrilar = _casus_kur(monkeypatch, save_hook)
    save_hook.get_git_state()

    status_cagrilari = [c for c in cagrilar if "status" in " ".join(map(str, c))]
    assert status_cagrilari, "hic `git status` cagrisi yok — testin ankraji kaymis"
    for c in status_cagrilari:
        birlesik = " ".join(map(str, c))
        assert ("--untracked-files=no" in birlesik) or (
            " -uno" in birlesik
        ), f"git status takipsiz dosya tariyor: {birlesik}"


# --------------------------------------------------------------------------
# 3) Islevsel: dogru VE hizli (ikisi birlikte — tek basina hicbiri yetmez)
# --------------------------------------------------------------------------


def test_git_durumu_hem_dogru_hem_5_saniyeden_hizli(save_hook):
    """Iki kusurun ikisini birden yakalar.

    * bash yolu calisirsa: `git status --short` >60 sn -> SURE dusurur.
    * bash yolu susarsa:   branch "" doner            -> DOGRULUK dusurur.
    Yani mevcut kodda hangi dal kosarsa kossun bu test KIRMIZI.
    """
    beklenen = _gercek_dal()
    assert beklenen, "kontrol kolu bozuk: gercek dal olculemedi"

    basla = time.perf_counter()
    durum = save_hook.get_git_state()
    gecen = time.perf_counter() - basla

    assert (
        durum["branch"] == beklenen
    ), f"dal yanlis/bos: {durum['branch']!r} != {beklenen!r}"
    assert durum["last_commits"], "son commit listesi bos"
    assert gecen < 5.0, f"git durumu {gecen:.1f} sn surdu (esik 5 sn)"


def test_backend_ayaktayken_down_raporlanmaz(save_hook):
    """Canli backend'i 'DOWN' diye raporlamak yanlis teshis uretiyordu."""
    try:
        import urllib.request

        with urllib.request.urlopen("http://localhost:8000/health", timeout=3) as yanit:
            canli = yanit.status == 200
    except Exception:
        canli = False
    if not canli:
        pytest.skip("backend ayakta degil — bu testin kontrol kolu yok")

    assert save_hook.get_services_state()["backend"] == "200"


# --------------------------------------------------------------------------
# 4) Etiket durustlugu: JSONL satir sayisi "Production" DEGILDIR
# --------------------------------------------------------------------------


def test_uretim_sayisi_jsonl_satiri_olarak_raporlanmaz(save_hook):
    """`d-dataset/eslesmis_sorucevap.jsonl` satir sayisi (77.336) canli DB degil.

    Olculdu (20 Agu 2026): question_bank=36.967, mv_safe_for_beta=27.073.
    Hook bu farki 'Production: 77,336 questions' diye raporluyordu — vekil olcum.
    """
    durum = save_hook.get_production_state()
    assert "question_count" not in durum, (
        "belirsiz 'question_count' anahtari duruyor — kaynagi adlandiran anahtar kullan "
        "(orn. jsonl_rows / db_question_bank)"
    )
    assert "jsonl_rows" in durum, "JSONL satir sayisi kendi adiyla raporlanmali"
    assert "db_question_bank" in durum, "canli DB sayimi (veya None) raporlanmali"


# --------------------------------------------------------------------------
# 5) session-init.py: saglik yolu
# --------------------------------------------------------------------------


def test_session_init_dogru_saglik_yolunu_kullanir():
    """`/api/v1/health` -> 404, `/health` -> 200 (verification.md, 1 Agu 2026'da olculdu).

    Yanlis yol saglikli backend'i 'erisilemez' diye raporlatiyordu.
    """
    kaynak = (HOOKS_DIR / "session-init.py").read_text(encoding="utf-8")

    # YORUMLARI AT. Aksi halde dedektor, yolun neden yanlis oldugunu ANLATAN
    # yorumu kusur sanar — bu deponun kayitli `mojibake-fixture` tuzaginin aynisi:
    # bozuk-gorunen bir dizeyi kusur saymadan once TUKETICISINE bak.
    kod = "\n".join(satir.split("#", 1)[0] for satir in kaynak.splitlines())

    # Kaynagi assert MESAJINA koyma: 250+ satirlik dosya pytest ciktisini boguyor.
    yanlis_yol_var = "/api/v1/health" in kod
    dogru_yol_var = "localhost:8000/health" in kod
    assert (
        not yanlis_yol_var
    ), "session-init.py hala /api/v1/health kullaniyor — o yol 404 donuyor"
    assert dogru_yol_var, "saglik kontrolu /health'e vurmali"
