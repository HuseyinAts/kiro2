# Weekly Audit — Windows Task Scheduler Setup

**Faz:** 2.5 (Plan v1)
**Trigger:** Pazar 09:00, weekly
**Job:** `run_weekly_audit.ps1` → `weekly_audit.py` → RAW + SCORING TSV otomatik üret

---

## Kurulum (Tek Komut)

PowerShell **as Administrator** aç, çalıştır:

```powershell
schtasks /create `
  /tn "KIRO2 Weekly Quality Audit" `
  /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\husey\kiro2\backend\scripts\quality\run_weekly_audit.ps1" `
  /sc weekly `
  /d SUN `
  /st 09:00 `
  /rl HIGHEST `
  /f
```

**Açıklama:**
- `/tn` task name (Türkçe karakter yok, schtasks limit)
- `/tr` çalıştırılacak komut
- `/sc weekly /d SUN /st 09:00` — Her Pazar 09:00
- `/rl HIGHEST` — Yönetici hakkı (DB bağlantısı için gerekebilir)
- `/f` — Aynı isimle task varsa üzerine yaz

---

## Doğrulama

```powershell
# Task var mı?
schtasks /query /tn "KIRO2 Weekly Quality Audit"

# Hemen manuel çalıştır (test):
schtasks /run /tn "KIRO2 Weekly Quality Audit"

# Çıktıyı izle:
Get-Content "C:\Users\husey\kiro2\backend\_pilots\scheduler_logs\weekly_audit_*.log" -Tail 30
```

---

## Log Dosyaları

`backend/_pilots/scheduler_logs/weekly_audit_YYYYMMDD_HHMMSS.log`

Her run kendi log dosyasını yazar. Manuel temizleme:

```powershell
# 30+ günden eski logları sil
Get-ChildItem "C:\Users\husey\kiro2\backend\_pilots\scheduler_logs\*.log" |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  Remove-Item
```

---

## İş Akışı (haftalık)

```
Pazar 09:00  → schtasks tetikler run_weekly_audit.ps1
             → weekly_audit.py: 30 random sample, deterministic seed=ISO year+week
             → RAW.tsv yazılır
             → scoring_template --prepare otomatik çağrılır
             → SCORING.tsv hazır (3 boş kolon)

Pazartesi    → Hüseyin SCORING.tsv açar, doldurur (~45 dk, 30 satır)

Salı/Çar.    → manuel: drift_dashboard ile multi-hafta birleşik rapor
             → ma_tracker.py ile 30-gün MA + alarm
```

---

## Manuel Tetikleme (Scheduler olmadan)

PowerShell:
```powershell
cd C:\Users\husey\kiro2
.\backend\scripts\quality\run_weekly_audit.ps1
```

Git Bash / direct Python:
```bash
cd /c/Users/husey/kiro2
python -m backend.scripts.quality.weekly_audit
```

---

## Troubleshooting

| Sorun | Çözüm |
|---|---|
| Task çalışmıyor (Task Scheduler History boş) | `/rl HIGHEST` flag eksik olabilir, admin olarak yeniden kur |
| `psycopg2 connection refused` | PostgreSQL port 5434 servis çalışıyor mu? `pg_isready -p 5434` |
| `ModuleNotFoundError: backend.scripts.quality` | PROJECT_ROOT yanlış, `Set-Location` path'i kontrol et |
| Log boş | `ExecutionPolicy Bypass` flag'i unutuldu, schtasks komutuna `-ExecutionPolicy Bypass` ekle |
| Türkçe karakter bozuk log'ta | PowerShell console UTF-8: `$OutputEncoding = [System.Text.UTF8Encoding]::new()` |

---

## Devre Dışı Bırakma

```powershell
# Geçici dur:
schtasks /change /tn "KIRO2 Weekly Quality Audit" /disable

# Kalıcı sil:
schtasks /delete /tn "KIRO2 Weekly Quality Audit" /f
```

---

## Faz 2.5 Implementation Notes

- Plan v1 satır 82: "Pazar 09:00 audit otomatik"
- Faz 2.6 (İlk 4 hafta baseline) bu scheduler aktifken oluşur
- Faz 2.4 (MA tracker) bu scheduler çıktısını input alır
- Auto-chain: weekly_audit → scoring_template --prepare (subprocess) tek runda biter

**Kurulum onayı kullanıcıdan istenmelidir** — schtasks system-wide task ekler, kullanıcı izni gerekli.
