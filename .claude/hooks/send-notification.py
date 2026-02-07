#!/usr/bin/env python3
"""
Notification Hook - Claude Code 2026
Claude bildirim gönderdiğinde çalışır.

Görevler:
1. Terminal bildirimi
2. Sistem bildirimi (opsiyonel)
3. Slack/Discord webhook (opsiyonel)
4. Log kaydı
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess


def get_notification_content() -> dict:
    """Bildirim içeriğini al."""
    content = os.environ.get("NOTIFICATION_CONTENT", "")
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"message": content}
    return {"message": "Unknown notification"}


def terminal_notify(title: str, message: str) -> None:
    """Terminal'e bildirim yaz."""
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"🔔 {title}")
    print(separator)
    print(message)
    print(f"{separator}\n")


def system_notify(title: str, message: str) -> None:
    """Sistem bildirimi gönder (Windows/macOS/Linux)."""
    try:
        if sys.platform == "win32":
            # Windows toast notification (PowerShell)
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
            $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
            $text = $xml.GetElementsByTagName("text")
            $text[0].AppendChild($xml.CreateTextNode("{title}")) | Out-Null
            $text[1].AppendChild($xml.CreateTextNode("{message[:200]}")) | Out-Null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code")
            $notifier.Show($toast)
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        elif sys.platform == "darwin":
            # macOS notification
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message[:200]}" with title "{title}"'
            ], capture_output=True)
        else:
            # Linux notification (notify-send)
            subprocess.run([
                "notify-send", title, message[:200]
            ], capture_output=True)
    except Exception as e:
        print(f"[Notification] System notify failed: {e}")


def webhook_notify(title: str, message: str, notification_type: str) -> None:
    """Webhook'a bildirim gönder (Slack/Discord)."""
    webhook_url = os.environ.get("CLAUDE_NOTIFICATION_WEBHOOK")
    if not webhook_url:
        return

    try:
        import urllib.request

        # Slack-style payload
        payload = {
            "text": f"*{title}*\n{message}",
            "attachments": [
                {
                    "color": "#36a64f" if notification_type == "success" else "#ff0000",
                    "fields": [
                        {"title": "Type", "value": notification_type, "short": True},
                        {"title": "Time", "value": datetime.now().strftime("%H:%M:%S"), "short": True},
                    ]
                }
            ]
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        print("[Notification] Webhook sent successfully")
    except Exception as e:
        print(f"[Notification] Webhook failed: {e}")


def log_notification(title: str, message: str, notification_type: str) -> None:
    """Bildirimi logla."""
    log_dir = Path.home() / ".claude" / "logs" / "notifications"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.jsonl"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "title": title,
        "message": message[:500],  # Truncate
        "type": notification_type,
        "session_id": os.environ.get("CLAUDE_SESSION_ID"),
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def main() -> int:
    """Ana fonksiyon."""
    content = get_notification_content()

    title = content.get("title", "Claude Code Notification")
    message = content.get("message", "")
    notification_type = content.get("type", "info")

    # Emoji prefix
    emoji_map = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "task_complete": "🎉",
        "task_blocked": "🚫",
    }
    emoji = emoji_map.get(notification_type, "🔔")

    full_title = f"{emoji} {title}"

    # Terminal bildirim (her zaman)
    terminal_notify(full_title, message)

    # Sistem bildirimi (CLAUDE_SYSTEM_NOTIFY=1 ise)
    if os.environ.get("CLAUDE_SYSTEM_NOTIFY") == "1":
        system_notify(title, message)

    # Webhook (CLAUDE_NOTIFICATION_WEBHOOK varsa)
    webhook_notify(title, message, notification_type)

    # Log
    log_notification(title, message, notification_type)

    # Her zaman success dön (non-blocking hook)
    return 0


if __name__ == "__main__":
    sys.exit(main())
