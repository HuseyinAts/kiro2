#!/usr/bin/env python
"""
Cursor beforeShellExecution hook — tehlikeli komutları blokar.

Cursor docs'a göre beforeShellExecution input:
  {
    "command": "<full terminal command>",
    "cwd": "...",
    "sandbox": false,
    ...
  }

Output (block için):
  {"permission": "deny", "user_message": "...", "agent_message": "..."}

.claude/rules/security.md'deki YASAK KOMUTLAR listesinden esinlenilmiştir.
"""
import json
import re
import sys


# Windows cp1254 fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DANGEROUS_PATTERNS = [
    # Dosya sistemi yıkımı
    (r"rm\s+-rf\s+/", "Kök dizini silmeye çalışıyor"),
    (r"rm\s+-rf\s+\*", "Wildcard ile toplu silme"),
    (r"rm\s+-rf\s+~", "Home silinmeye çalışılıyor"),
    (r"rm\s+-rf\s+\.", "Mevcut dizini silmeye çalışıyor"),

    # DB yıkımı (DROP TABLE production-like)
    (r"DROP\s+TABLE", "DROP TABLE yasak — Alembic migration kullan"),
    (r"DROP\s+DATABASE", "DROP DATABASE yasak"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE yasak — Alembic data migration kullan"),

    # Git tehlikeli
    (r"git\s+push\s+(--force|-f)\s+.*\s+(main|master)", "Main/master'a force push"),
    (r"git\s+reset\s+--hard\s+HEAD~", "Reset hard yasak — önce stash veya branch"),

    # Secrets açıklama
    (r"cat\s+\.env(\s|$)", "cat .env yasak — secret sızar"),
    (r"echo\s+\$API_KEY", "API_KEY echo yasak"),
    (r"echo\s+\$PASSWORD", "PASSWORD echo yasak"),

    # Production DB connection (KIRO2 özel)
    (r"psql.*production", "Production DB bağlantısı yasak"),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        # Parse edemezsek fail-open — agent devam etsin
        print(json.dumps({"permission": "allow"}))
        return 0

    cmd = payload.get("command", "")

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            response = {
                "permission": "deny",
                "user_message": f"Tehlikeli komut bloklandı: {reason}",
                "agent_message": (
                    f"Komut güvenlik hook'u tarafından engellendi. "
                    f"Sebep: {reason}. Bu komut KIRO2 güvenlik politikasına "
                    f"aykırı. Farklı bir yaklaşım dene veya kullanıcıdan "
                    f"açık onay iste."
                ),
            }
            print(json.dumps(response))
            return 0

    # Güvenli → allow
    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Fail-open: hook crash olursa komut geçsin (agent kilitlenmesin)
        print(f"[WARN] guard-shell: {e}", file=sys.stderr)
        print(json.dumps({"permission": "allow"}))
        sys.exit(0)
