#!/usr/bin/env python3
"""
KIRO2 Custom Secret Detector
Pre-commit hook for detecting hardcoded secrets

Exit Codes (Daisy Stanton Standards):
- 0: Success (no secrets found)
- 2: Blocking error (secrets detected - must fix before commit)

Usage:
    python backend/hooks/secret_detector.py [file1] [file2] ...

Or via pre-commit:
    - repo: local
      hooks:
        - id: kiro2-secret-detector
          name: KIRO2 Secret Detector
          entry: python backend/hooks/secret_detector.py
          language: system
          types: [python]
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# İKİ KATMANLI DESEN SETİ (27 Tem 2026)
#
# NEDEN AYRIM: Bu depoda `core.hooksPath = nul` ayarlıydı ve HİÇBİR git hook'u
# çalışmıyordu (koşulsuz `exit 1` yapan bir hook bile commit'i bloklamadı —
# canlı deneyle ölçüldü). Bir bekçinin kapatılmasının en yaygın sebebi yanlış
# alarmdır. Bu yüzden bloklayan katmanda KESİNLİK, kapsamdan önce gelir.
#
# ÖLÇÜM (depodaki tüm izlenen dosyalar, sertleştirilmiş dedektör):
#   toplam 110 bulgu
#     99  jenerik `password = "..."`   <- test fixture'ı / yerel DSN, GÜRÜLTÜ
#      4  KIRO2 DB parolası (literal)
#      3  Google API anahtarı          <- ...XX/YY/ZZ ile biten doküman örneği
#      2  jenerik api_key
#      1  KIRO2 JWT secret
#      1  OpenAI anahtarı              <- sk-abc...78, örnek
# Sızan 11 anahtarın ikisi de KESİN FORMATLI (AIza…, hf_…). Jenerik parola
# sezgiselinin o sınıfa katkısı SIFIR, gürültüsü 99. Bloklatmak, bekçiyi
# yeniden kapattırmanın en kısa yolu olurdu.
# ---------------------------------------------------------------------------

# BLOKLAYAN (exit 2): sağlayıcıya özgü, düşük yanlış-pozitif formatlar.
BLOCKING_PATTERNS: list[tuple[str, str]] = [
    (r"sk-ant-api\d+-[A-Za-z0-9_-]{20,}", "Anthropic API Key"),
    (r"sk-proj-[A-Za-z0-9_-]{20,}", "OpenAI Project Key"),
    (r"sk-[A-Za-z0-9]{48,}", "OpenAI API Key"),
    (r"hf_[A-Za-z0-9]{34,}", "HuggingFace Token"),
    (r"AIza[A-Za-z0-9_-]{35}", "Google API Key"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub Token"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack Token"),
    # KIRO2'ye özgü, geçmişte GERÇEKTEN sızmış literaller
    (r"TeknoFest\d+SecurePass", "KIRO2 Database Password"),
    (r"teknofest-\d+-super-secret[A-Za-z0-9_-]*", "KIRO2 JWT Secret"),
]

# UYARAN (exit 0): yüksek yanlış-pozitifli sezgiseller. Rapor edilir ama
# commit'i durdurmaz. Bunları bloklayıcı yapmak isteyen önce depodaki 99
# bulguyu temizlemeli — aksi halde bekçi güvenilirliğini kaybeder.
WARNING_PATTERNS: list[tuple[str, str]] = [
    (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Password (heuristic)"),
    (r'api_key\s*=\s*["\']sk-[^"\']+["\']', "Hardcoded API Key (heuristic)"),
]

# Geriye dönük uyumluluk: dış çağıranlar bu adı bekliyor olabilir.
SECRET_PATTERNS: list[tuple[str, str]] = BLOCKING_PATTERNS + WARNING_PATTERNS

# Satır-içi izin işareti. detect-secrets ile aynı sözdizimi, böylece iki araç
# tek bir işareti paylaşır. Meşru ÖRNEK/dokümantasyon satırları için:
#     api_key = "AIza..."  # pragma: allowlist secret
# Dosya bazlı beyaz liste yerine bunu kullan: bir dosyayı topluca muaf tutmak,
# o dosyaya sonradan giren GERÇEK anahtarı da muaf tutar.
ALLOWLIST_MARKER = "pragma: allowlist secret"

# Dosya bazlı muafiyet — MÜMKÜN OLDUĞUNCA DAR TUT.
# 27 Tem 2026: 'CLAUDE.md' buradan ÇIKARILDI. Ölçüldü: beyaz listedeyken
# CLAUDE.md içine konmuş sentetik bir Google anahtarı dedektörden GEÇİYORDU.
# Dokümantasyon örnekleri artık ALLOWLIST_MARKER ile işaretlenir.
ALLOWED_FILES = [
    ".secrets.baseline",  # detect-secrets'in kendi kayıt dosyası
    "secret_detector.py",  # bu dosya (desenlerin kendisi burada)
]

# Directories to skip
SKIP_DIRS = [
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
]


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    # Skip allowed files
    if filepath.name in ALLOWED_FILES:
        return True

    # Skip directories
    return any(skip_dir in filepath.parts for skip_dir in SKIP_DIRS)


def _mask(secret: str) -> str:
    """Sırrı log'a yazmadan tanınabilir kıl.

    27 Tem 2026 — GÜVENLİK KUSURU DÜZELTİLDİ. Eski `preview` satırın ilk 60
    karakterini olduğu gibi basıyordu, yani dedektörün KENDİSİ sırrı stdout'a
    (ve CI log'una, ve terminal geçmişine) sızdırıyordu. Bir sır tarayıcısının
    çıktısı sırrı içeremez.
    """
    if len(secret) <= 10:
        return "*" * len(secret)
    return f"{secret[:4]}…{secret[-2:]} (len={len(secret)})"


def scan_file(filepath: Path) -> list[tuple[int, str, str, bool]]:
    """
    Scan file for secrets.

    Returns:
        List of (line_number, secret_type, masked_preview, is_blocking)
    """
    if should_skip_file(filepath):
        return []

    findings = []

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # 27 Tem 2026 — YORUM ATLAMA KALDIRILDI.
            # Eskiden `if stripped.startswith("#"): continue` vardı, yani
            #     # GEMINI_API_KEY = "AIza..."
            # satırı dedektörden GEÇİYORDU (sentetik test ile ölçüldü). Oysa
            # yorumlanmış config satırı sızıntının en yaygın biçimlerinden
            # biridir — anahtar yine git geçmişine yazılır, yorum olması onu
            # gizlemez, yalnız insan gözünden kaçırır.
            # Meşru dokümantasyon örnekleri için satır-içi işaret kullanılır.
            if ALLOWLIST_MARKER in line:
                continue

            matched = False
            for pattern, secret_type in BLOCKING_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    findings.append((line_num, secret_type, _mask(m.group(0)), True))
                    matched = True
                    break  # One finding per line is enough
            if matched:
                continue
            for pattern, secret_type in WARNING_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    findings.append((line_num, secret_type, _mask(m.group(0)), False))
                    break

    except Exception:
        # Silently skip files that can't be read
        pass

    return findings


def main() -> int:
    """Main entry point."""
    files = sys.argv[1:]

    if not files:
        print("Usage: python secret_detector.py <file1> [file2] ...")
        return 0

    blocking = 0
    warnings = 0

    for filepath_str in files:
        filepath = Path(filepath_str)

        if not filepath.exists():
            continue

        for line_num, secret_type, masked, is_blocking in scan_file(filepath):
            tag = "SECRET DETECTED" if is_blocking else "SECRET WARNING"
            print(f"\n[{tag}] {filepath}:{line_num}")
            print(f"  Type: {secret_type}")
            print(f"  Match: {masked}")
            if is_blocking:
                blocking += 1
            else:
                warnings += 1

    if warnings:
        print(f"\n[WARN] {warnings} olası sır (sezgisel) — commit BLOKLANMADI.")
        print("       Yanlış pozitifse yok say; gerçekse .env'e taşı.")

    if blocking:
        print("\n" + "=" * 60)
        print(f"[ERROR] {blocking} hardcoded secret(s) detected!")
        print("=" * 60)
        print("\nFix instructions:")
        print("1. Move secrets to .env file")
        print("2. Use os.getenv() or Settings class")
        print("3. Never commit secrets to git")
        print("\nExample:")
        print('  # BAD:  api_key = "sk-ant-api03-..."')
        print('  # GOOD: api_key = os.getenv("ANTHROPIC_API_KEY")')
        print("\nMeşru dokümantasyon örneği ise satır sonuna ekle:")
        print("  # pragma: allowlist secret")
        print("\nSee: docs/SECRETS_MANAGEMENT.md")
        return 2  # Exit code 2 = blocking error

    return 0


if __name__ == "__main__":
    sys.exit(main())
