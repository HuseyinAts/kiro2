# Hook System Quick Reference

**1 Sayfa - Hızlı Başvuru**

---

## 🔧 Komutlar

### Test Et
```bash
bash .claude/hooks/test_hooks.sh          # Tüm hook'ları otomatik test et
bash .claude/hooks/user-prompt-submit.sh "rapor"  # Tek hook test
```

### Facts Topla
```bash
bash .claude/hooks/pre-report-write.sh    # Tüm facts'leri topla
```

### Rapor Doğrula
```bash
bash .claude/hooks/post-report-write.sh RAPOR.md  # Manuel doğrulama
```

### Durum Kontrol
```bash
bash .claude/hooks/check_hooks_status.sh  # Tüm hook durumları
```

---

## 📋 5 Hook Özeti

| Hook | Tip | Ne Zaman | Etkinlik |
|------|-----|----------|----------|
| **user-prompt-submit** | Auto | Kullanıcı "rapor" deyince | 60% |
| **tool-call (PreToolUse)** | Auto | Rapor yazılmadan önce | 40% |
| **post-tool-use (PostToolUse)** | Auto | Rapor yazıldıktan sonra | 70% |
| **pre-report-write** | Manuel | İsteğe bağlı | 30% |
| **post-report-write** | Core | post-tool-use'dan çağrılır | 30% |

**Toplam Etkinlik:** 80%

---

## 🚫 Yasaklı İfadeler (7)

1. ❌ `production-ready` → ✅ `production readiness: 20%`
2. ❌ `100% complete` → ✅ `Phase 1 complete (20%)`
3. ❌ `fully functional` → ✅ `Core features implemented`
4. ❌ `10,000+ sorular` → ✅ `Database has 0 rows`
5. ❌ `all tests passing` → ✅ `15/20 tests pass`
6. ❌ `world-class` → ✅ (Nesnel ifade kullan)
7. ❌ `revolutionary` → ✅ (Nesnel ifade kullan)

---

## 📊 Verification Score

**Hedef:** ≥75/100

**Nasıl Hesaplanır:**
- Evidence blocks (+25)
- No forbidden phrases (+25)
- Mentions database facts (+25)
- Mentions issues/gaps (+25)

---

## 🔍 Gerçek Sayılar (2025-11-09)

```
Database:   0 rows, 5 tables
Mock Data:  2,454 occurrences
Backend:    Not running
Etkinlik:   ~20%
```

**NOT:** Raporda bu sayıları kullan, tahmin etme!

---

## ⚡ Hızlı Sorun Giderme

### Hook çalışmıyor?
```bash
chmod +x .claude/hooks/*.sh              # Executable yap
python -m json.tool .claude/settings.local.json  # JSON geçerli mi?
```

### Python bulunamıyor?
- Hook'lar gracefully fallback yapar
- Default değerler kullanılır
- Tam doğrulama için Python kur

### Verification score düşük?
- Evidence blocks ekle (+25)
- Forbidden phrase sil (+25)
- Database facts ekle (+25)
- Issues/gaps say (+25)

---

## 📁 Dosya Konumları

```
.claude/
├── hooks/
│   ├── user-prompt-submit.sh    # Auto reminder
│   ├── tool-call.sh              # Pre-write warning
│   ├── post-tool-use.sh          # Post-write verify
│   ├── pre-report-write.sh       # Manual facts
│   ├── post-report-write.sh      # Core engine
│   └── test_hooks.sh             # Test suite
├── settings.local.json           # Hook config (CRITICAL!)
├── facts/latest.json             # Current facts
└── scripts/
    ├── check_database.py         # DB checker
    └── check_mocks.sh            # Mock counter
```

---

## 🎯 Rapor Yazarken Checklist

**ÖNCE:**
- [ ] `bash .claude/hooks/pre-report-write.sh` çalıştır
- [ ] Facts file'ı oku (`.claude/facts/latest.json`)
- [ ] Gerçek sayıları kullan

**YAZARKEN:**
- [ ] Evidence blocks ekle
- [ ] Yasaklı ifadeler kullanma
- [ ] Database facts belirt
- [ ] Issues/gaps say

**SONRA:**
- [ ] `bash .claude/hooks/post-report-write.sh RAPOR.md` çalıştır
- [ ] Verification score ≥75 kontrol et
- [ ] Uyarıları oku ve düzelt

---

## 📞 Yardım

**Dokümantasyon:**
- [README.md](README.md) - Detaylı kullanım
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 10 yaygın sorun
- [END_TO_END_TEST_RESULTS.md](END_TO_END_TEST_RESULTS.md) - Test sonuçları

**Test:**
```bash
bash .claude/hooks/test_hooks.sh  # Tam test
```

**Sıfırla:**
```bash
bash .claude/hooks/backup_hooks.sh   # Önce backup al
bash .claude/hooks/restore_hooks.sh  # Sonra geri yükle
```

---

**Versiyon:** 1.0 | **Güncelleme:** 2025-11-09 | **Etkinlik:** 80%
