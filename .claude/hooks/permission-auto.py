#!/usr/bin/env python3
"""
PermissionRequest Hook - Claude Code 2026
İzin dialogunda çalışır.

Görevler:
1. Güvenli işlemleri otomatik onaylama
2. Tehlikeli işlemleri engelleme
3. İzin geçmişi tutma
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Otomatik onaylanacak pattern'ler
AUTO_APPROVE_PATTERNS = [
    # Read operations
    r"^Read\s+.*",
    r"^Glob\s+.*",
    r"^Grep\s+.*",

    # Safe bash commands
    r"^Bash\s+(ruff|mypy|pytest|npm\s+test|npm\s+run\s+lint|git\s+status|git\s+diff|git\s+log|ls|pwd|echo)\b",

    # Edit in allowed directories
    r"^Edit\s+.*/(backend|frontend|\.claude)/.*",
    r"^Write\s+.*/(backend|frontend|\.claude)/.*",
]

# Otomatik reddedilecek pattern'ler (GÜVENLİK)
AUTO_DENY_PATTERNS = [
    # Dangerous bash commands
    r"^Bash\s+.*(rm\s+-rf|DROP\s+|DELETE\s+FROM|TRUNCATE|sudo|chmod\s+777)",

    # Sensitive files
    r"^(Edit|Write|Read)\s+.*\.env($|[^.])",
    r"^(Edit|Write|Read)\s+.*/\.ssh/",
    r"^(Edit|Write|Read)\s+.*/\.aws/",
    r"^(Edit|Write|Read)\s+.*credentials",
    r"^(Edit|Write|Read)\s+.*secrets",

    # System directories
    r"^(Edit|Write)\s+/etc/",
    r"^(Edit|Write)\s+/usr/",
    r"^(Edit|Write)\s+C:\\Windows",
    r"^(Edit|Write)\s+C:\\Program Files",

    # Git dangerous
    r"^Bash\s+git\s+(push\s+--force|reset\s+--hard|clean\s+-f)",
]


def get_permission_request() -> dict:
    """İzin isteğini al."""
    request = os.environ.get("PERMISSION_REQUEST", "")
    if request:
        try:
            return json.loads(request)
        except json.JSONDecodeError:
            return {"action": request}
    return {"action": "unknown"}


def check_patterns(action: str, patterns: list[str]) -> bool:
    """Action'ın pattern'lerle eşleşip eşleşmediğini kontrol et."""
    for pattern in patterns:
        if re.search(pattern, action, re.IGNORECASE):
            return True
    return False


def log_permission(action: str, decision: str, reason: str) -> None:
    """İzin kararını logla."""
    log_dir = Path.home() / ".claude" / "logs" / "permissions"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.jsonl"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action[:500],  # Truncate
        "decision": decision,
        "reason": reason,
        "session_id": os.environ.get("CLAUDE_SESSION_ID"),
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def main() -> int:
    """Ana fonksiyon.

    Returns:
        0: Kullanıcıya sor (default)
        1: Otomatik onayla
        2: Otomatik reddet
    """
    request = get_permission_request()
    action = request.get("action", "")

    if not action:
        return 0  # Kullanıcıya sor

    # Önce tehlikeli pattern'leri kontrol et
    if check_patterns(action, AUTO_DENY_PATTERNS):
        log_permission(action, "denied", "Dangerous pattern detected")
        print(f"[Permission] ❌ AUTO-DENIED: {action[:100]}...")
        return 2  # Engelle

    # Sonra güvenli pattern'leri kontrol et
    if check_patterns(action, AUTO_APPROVE_PATTERNS):
        log_permission(action, "approved", "Safe pattern matched")
        print(f"[Permission] ✅ AUTO-APPROVED: {action[:100]}...")
        return 1  # Onayla

    # Bilinmeyen pattern - kullanıcıya sor
    log_permission(action, "ask_user", "Unknown pattern")
    return 0


if __name__ == "__main__":
    sys.exit(main())
