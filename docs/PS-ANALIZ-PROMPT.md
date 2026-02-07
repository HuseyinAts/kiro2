# PowerShell Çıktı Analizi & Çözüm Prompt'u

> **Kullanım:** Bu prompt'u Claude'a yapıştır, ardından PowerShell çıktını ekle.

---

## PROMPT

```
Sen PowerShell ve Windows sistem uzmanısın. Aşağıdaki PowerShell çıktısını analiz et ve doğrudan çalıştırabileceğim kodu üret.

## 1️⃣ TARAMA

| 🔴 KRİTİK | 🟡 UYARI | 🟢 BAŞARI |
|-----------|----------|-----------|
| Error, Exception, Failed, Access Denied, Cannot, Unable | Warning, Deprecated, Timeout, Skipped | Success, OK, Completed, True |

Tespit edilen sorunları listele.

---

## 2️⃣ KÖK NEDEN

> 🎯 **Sorun:** [Tek cümlede açıkla]

**5 Neden Zinciri:**
[HATA] → Neden? → [Cevap] → Neden? → ... → 🎯 KÖK NEDEN

---

## 3️⃣ ÇÖZÜM KODU

### Şimdi Çalıştır:
```powershell
# Bunu kopyala ve PowerShell'e yapıştır
```

### Alternatif (hata devam ederse):
```powershell
# Yedek çözüm
```

---

## 4️⃣ DOĞRULAMA

```powershell
# Test komutu
```

✅ **Beklenen:** [Başarılı çıktı açıklaması]

---

## 5️⃣ SONUÇ

- ✓ Çalıştı → Tamam
- ✗ Yeni hata → Çıktıyı yapıştır, devam edelim

---

# ÇIKTI:
```
[BURAYA YAPIŞTIR]
```
```

---

## HIZLI KULLANIM

Her seferinde sadece şunu yapıştır:

```
PowerShell çıktısını analiz et, çalıştıracağım kodu ver:

```
[ÇIKTIYI BURAYA YAPIŞTIR]
```
```

---

## İŞ AKIŞI

```
┌─────────────────────────────────────────────┐
│  1. PowerShell'de kod çalıştır              │
│                 ↓                           │
│  2. Çıktıyı kopyala (Ctrl+A, Ctrl+C)        │
│                 ↓                           │
│  3. Claude'a yapıştır                       │
│                 ↓                           │
│  4. Verilen kodu PowerShell'e yapıştır      │
│                 ↓                           │
│  5. Çözüldü mü?                             │
│       ├── Evet → Bitti ✓                    │
│       └── Hayır → Yeni çıktıyı yapıştır     │
└─────────────────────────────────────────────┘
```

---

## ÖRNEK KULLANIM

**Senaryo:** Servis başlatma hatası

**Giriş:**
```
PowerShell çıktısını analiz et, çalıştıracağım kodu ver:

```
Start-Service : Service 'PostgreSQL' cannot be started due to the following error: 
Cannot open PostgreSQL service on computer '.'.
At line:1 char:1
+ Start-Service PostgreSQL
+ ~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : OpenError: (System.ServiceProcess.ServiceController:ServiceController) [Start-Service], ServiceCommandException
    + FullyQualifiedErrorId : CouldNotStartService,Microsoft.PowerShell.Commands.StartServiceCommand
```
```

**Beklenen Yanıt:**
```
## 1️⃣ TARAMA
| 🔴 KRİTİK |
| Cannot be started, Cannot open service |

## 2️⃣ KÖK NEDEN
> 🎯 **Sorun:** PostgreSQL servisi yönetici yetkisi olmadan başlatılamıyor.

## 3️⃣ ÇÖZÜM KODU

### Şimdi Çalıştır:
```powershell
# Admin olarak PowerShell aç, sonra:
Start-Service -Name 'postgresql-x64-14'
```

### Alternatif:
```powershell
# Servis adını doğrula
Get-Service *postgres* | Select-Object Name, Status, StartType
```

## 4️⃣ DOĞRULAMA
```powershell
Get-Service *postgres* | Where-Object {$_.Status -eq 'Running'}
```
✅ **Beklenen:** Status = Running

## 5️⃣ SONUÇ
- Çalıştı mı? → Yeni çıktıyı paylaş
```

---

## NOTLAR

- Bu prompt iteratif çalışır - her hata için döngüye devam et
- Admin gerektiren komutlar için `# Admin olarak çalıştır` notu eklenir
- Encoding sorunları için UTF-8 uyarısı verilir
- Türkçe karakter sorunları için `-Encoding UTF8` önerilir
