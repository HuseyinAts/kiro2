# KIRO2 Claude Code Cheat Sheet

## 🎯 PROJE
- **Konum:** C:\Users\husey\kiro2
- **PostgreSQL:** PORT 5434 (5432 DEĞİL!)
- **Stack:** Python 3.11, FastAPI, React 18, LangGraph

---

## ⚡ GÖREV PROTOKOLÜ

```
1. PLAN   → Kompleks görevde önce plan yap (Shift+Tab x2)
2. OKU    → Önce dosyaları oku, sonra değiştir
3. MİNİMAL → Sadece gerekeni değiştir
4. DOĞRULA → Her değişikliği test et
```

---

## 🔴 ASLA YAPMA

```
❌ PostgreSQL port 5432 kullanma (5434!)
❌ API key hardcode etme
❌ Test dosyasını "geçmesi için" değiştirme
❌ assert True, echo Success, exit 0 hack'leri
❌ Type hints olmadan fonksiyon yazma
❌ try/except: pass (sessiz hata yutma)
❌ Tüm dosyayı silip yeniden yazma
```

---

## ✅ HER ZAMAN YAP

```
✅ Önce oku, sonra yaz
✅ Type hints + docstrings
✅ UTF-8 + Türkçe karakter desteği
✅ Parametrized SQL query
✅ Her değişiklik sonrası: ruff check + pytest
✅ Hata varsa KODU düzelt, TESTİ değil
```

---

## 📋 KOD KONTROL LİSTESİ

### Yazmadan Önce
- [ ] Görevi anladım
- [ ] İlgili dosyaları okudum
- [ ] Mevcut testleri inceledim

### Yazarken
- [ ] Type hints var
- [ ] Docstring var
- [ ] Hata yönetimi var

### Yazdıktan Sonra
- [ ] `ruff check .` geçiyor
- [ ] `pytest` geçiyor
- [ ] Gereksiz değişiklik yok

---

## 📁 SORU FORMATI

```json
{
  "question_id": "MAT-AYT-LIMIT-001",
  "question_text": "...",
  "options": {"A":"..","B":"..","C":"..","D":"..","E":".."},
  "correct_answer": "B",
  "difficulty_level": 1-5,
  "explanation": "...",
  "solution_steps": ["..."]
}
```

### Soru Kontrol
- [ ] JSON geçerli
- [ ] 5 seçenek var (A-E)
- [ ] LaTeX syntax doğru ($...$)
- [ ] Türkçe karakterler OK
- [ ] Zorluk uygun (1-5)

---

## 🔧 CONTEXT YÖNETİMİ

| Durum | Komut |
|-------|-------|
| Yeni görev | `/clear` |
| Uzun görev devam | `/compact` |
| Context %75+ | Progress kaydet → `/clear` |

---

## 🤖 SUBAGENT

```
Task: [görev]
Task code-reviewer: Review this module
Task test-runner: Fix failing tests
```

**Mevcut:** code-reviewer, debugger, test-runner, python-pro, kiro2-backend, kiro2-frontend, kiro2-content

---

## 🆘 HIZLI ÇÖZÜMLER

| Sorun | Çözüm |
|-------|-------|
| DB bağlantı hatası | Port 5434 mü kontrol et |
| Import hatası | `pip install -e .` |
| Test başarısız | Kodu düzelt, testi DEĞİL |
| Context doldu | Progress kaydet → `/clear` |

---

## 📊 HEDEFLER

| Metrik | Hedef |
|--------|-------|
| Test coverage | >80% |
| Lint errors | 0 |
| Soru validation | 100% |
| Response time | <2s |

---

## 🔗 DOSYALAR

```
orchestrator/  → AI orchestrator
backend/       → FastAPI API
frontend/      → React UI
d-dataset/     → Sorular
tests/         → Testler
docs/rapor-v3/ → Detaylı rapor (18 bölüm)
```

---

**Golden Rule:** Önce oku, sonra yaz. Her değişikliği doğrula.
