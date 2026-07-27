"""Sır tarama bekçisinin bekçisi.

27 TEM 2026 — NEDEN VAR
-----------------------
11 anahtar (10 Google + 1 HuggingFace) depoya sızdı. Kök neden tek değil,
ÜST ÜSTE BİNMİŞ DÖRT SESSİZ KUSURDU; her biri tek başına taramayı etkisiz
kılıyordu ve hiçbiri hata vermiyordu:

  1. `core.hooksPath = nul` (Windows NUL aygıtı) -> HİÇBİR git hook'u
     çalışmıyordu. Canlı deneyle ölçüldü: koşulsuz `exit 1` yapan bir
     pre-commit hook'u bile commit'i BLOKLAMADI.
  2. Kurulu hook `backend/.pre-commit-config.yaml`'ı çağırıyordu — o config'de
     sır taraması HİÇ YOK (ne detect-secrets ne özel dedektör).
  3. Kök config `default_language_version: python3.11` pin'liyordu; o
     yorumlayıcı makinede yok -> config'i kullanan her koşum
     "failed to find interpreter" ile çöküyordu.
  4. Özel dedektör `types: [python]` ile kısıtlıydı (.env/.json/.yml/.md/.sh
     kapsam dışı), `stages: [commit]` pre-commit 4.x'te geçersiz bir ad, ve
     dedektörün kendisi YORUM SATIRLARINI ATLIYORDU — yani
     `# GEMINI_API_KEY=AIza...` taramadan geçiyordu.

Ders (.claude/rules/testing.md #15): dersi yazmak yetmez, ENFORCE et.
Bu dosya 1, 3 ve 4'ü test edilebilir kılar. Kaynak: backend/hooks/secret_detector.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DETECTOR = REPO_ROOT / "backend" / "hooks" / "secret_detector.py"

# Sentetik — hiçbir sağlayıcıda geçerli değil. Uzunluklar desenle eşleşsin diye
# programatik üretiliyor; elle yazılan sabitler kolayca yanlış uzunlukta olur
# (bu testi yazarken ilk denemede 38 karakter üretip yanlış negatif aldık).
FAKE_GOOGLE = "AIza" + ("Sy_KIRO2_TEST_ANAHTARI" + "0" * 35)[:35]
FAKE_HF = "hf_" + "K" * 34
FAKE_GITHUB = "ghp_" + "A" * 36


def _run(tmp_path: Path, filename: str, content: str) -> subprocess.CompletedProcess:
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    # S603: argümanlar sabit; sys.executable ve DETECTOR modül seviyesinde
    # türetiliyor, kullanıcı girdisi yok. Dedektörü ALT SÜREÇ olarak koşmak
    # kasıtlı: testin ölçtüğü şey ÇIKIŞ KODU (2 = blokla), import edilebilir
    # bir fonksiyonun dönüş değeri değil — pre-commit de onu böyle görür.
    return subprocess.run(  # noqa: S603
        [sys.executable, str(DETECTOR), str(p)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("kod.py", f'GEMINI_API_KEY = "{FAKE_GOOGLE}"'),
        # Yorum satırı: eski dedektör bunu ATLIYORDU. Sızıntının en yaygın
        # biçimlerinden biri — anahtar yine git geçmişine yazılır.
        ("yorum.py", f'# GEMINI_API_KEY = "{FAKE_GOOGLE}"'),
        ("yorum.js", f'// const k = "{FAKE_GOOGLE}";'),
        # .py DIŞI türler: eski config `types: [python]` ile bunları hiç
        # taramıyordu.
        ("cfg.env", f"#GEMINI_API_KEY={FAKE_GOOGLE}"),
        ("cfg.yml", f"gemini_key: {FAKE_GOOGLE}"),
        ("notlar.md", f"Anahtar: {FAKE_GOOGLE}"),
        ("kur.sh", f"export GEMINI_API_KEY={FAKE_GOOGLE}"),
        ("hf.py", f'TOKEN = "{FAKE_HF}"'),
        ("gh.sh", f"export T={FAKE_GITHUB}"),
    ],
)
def test_blocks_provider_formatted_keys(tmp_path, filename, content):
    """Sağlayıcı-formatlı anahtar HER dosya türünde ve yorumda bloklanmalı."""
    r = _run(tmp_path, filename, content + "\n")
    assert r.returncode == 2, (
        f"{filename} bloklanmadı (rc={r.returncode}). Sır taraması etkisiz.\n"
        f"stdout: {r.stdout[:400]}"
    )


def test_allowlist_marker_permits_documentation_example(tmp_path):
    """Meşru doküman örneği satır-içi işaretle geçebilmeli."""
    r = _run(tmp_path, "ornek.py", f'K = "{FAKE_GOOGLE}"  # pragma: allowlist secret\n')
    assert r.returncode == 0, f"pragma işaretli satır bloklandı: {r.stdout[:300]}"


def test_generic_password_heuristic_warns_but_does_not_block(tmp_path):
    """Sezgisel desen commit'i DURDURMAMALI.

    Depoda 99 jenerik `password = "..."` eşleşmesi var (test fixture'ı, yerel
    DSN). Bunları bloklatmak bekçiyi güvenilmez yapar ve kapatılmasına yol
    açar — bu depo tam olarak öyle olmuştu.
    """
    r = _run(tmp_path, "t.py", 'password = "supersecret123"\n')
    assert r.returncode == 0, "sezgisel desen bloklamamalı"
    assert "WARN" in r.stdout, "sezgisel eşleşme en azından uyarmalı"


def test_detector_output_never_contains_the_secret(tmp_path):
    """Sır tarayıcısının ÇIKTISI sırrı içeremez.

    Eski `preview` satırın ilk 60 karakterini basıyordu — yani dedektör sırrı
    stdout'a, CI log'una ve terminal geçmişine sızdırıyordu.
    """
    r = _run(tmp_path, "leak.py", f'K = "{FAKE_GOOGLE}"\n')
    assert r.returncode == 2
    assert FAKE_GOOGLE not in r.stdout, "Dedektör sırrı log'a yazdı — maskeleme bozuk."
    assert "len=39" in r.stdout, "maskeli önizleme beklenen biçimde değil"


def test_git_hooks_are_not_disabled():
    """`core.hooksPath` hook'ları etkisiz bir yola yönlendirmemeli.

    `nul` (Windows) veya `/dev/null` ayarlandığında git hiçbir hook bulamaz ve
    SESSİZCE devam eder — hata yok, uyarı yok. 11 anahtarın sızmasının
    birincil sebebi buydu.
    """
    r = subprocess.run(  # noqa: S603
        ["git", "config", "--get", "core.hooksPath"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    value = r.stdout.strip()
    if not value:
        return  # ayarsız = varsayılan .git/hooks = doğru
    assert value.lower() not in {"nul", "/dev/null", "nul:", "con"}, (
        f"core.hooksPath = {value!r} — git hook'ları ETKİSİZ. "
        f"`git config --unset core.hooksPath` ile düzelt."
    )
    assert (
        REPO_ROOT / value
    ).is_dir(), f"core.hooksPath = {value!r} bir dizin değil; hook'lar çalışmaz."


def test_installed_hook_points_at_root_config():
    """Kurulu pre-commit hook'u sır taraması OLAN kök config'i çağırmalı.

    `backend/.pre-commit-config.yaml`'da sır taraması yok. Hook oraya
    yönlendirilirse tarama sessizce devre dışı kalır.
    """
    hook = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    if not hook.exists():
        pytest.skip(
            "pre-commit hook kurulu değil (`pre-commit install -c .pre-commit-config.yaml`)"
        )
    body = hook.read_text(encoding="utf-8", errors="ignore")
    if "pre_commit" not in body and "pre-commit" not in body:
        pytest.skip("hook pre-commit framework'ünü kullanmıyor")
    assert "backend\\.pre-commit-config.yaml" not in body, (
        "Hook backend/.pre-commit-config.yaml'ı çağırıyor — o config'de sır "
        "taraması YOK. `pre-commit install -c .pre-commit-config.yaml --overwrite`"
    )
    assert (
        "backend/.pre-commit-config.yaml" not in body
    ), "Hook backend/.pre-commit-config.yaml'ı çağırıyor — sır taraması yok."
