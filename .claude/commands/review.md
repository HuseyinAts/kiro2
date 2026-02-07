---
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
description: Son kod değişikliklerini incele
---

## Context
- Recent changes: !`git diff HEAD~3 --stat`

## Task
Kod değişikliklerini incele ve geri bildirim ver.

## İnceleme Kriterleri

### 1. Güvenlik
- SQL injection riski
- XSS açıkları
- Hardcoded credentials
- JWT/auth bypass

### 2. Performans
- N+1 query problemi
- Memory leak
- Gereksiz re-render (React)
- Cache kullanımı

### 3. Kod Kalitesi
- Type hints (Python)
- TypeScript strict mode
- DRY prensibi
- SOLID principles

### 4. KIRO2 Özel Kurallar
- ❌ `useAuth.ts` → ✅ `authStore.ts`
- ❌ Mock data → ✅ Gerçek API
- ✅ Türkçe için UTF-8
- ✅ Docstring (Google style)

## Çıktı Formatı

```markdown
### 🔴 KRİTİK (Merge öncesi düzelt)
- [dosya:satır] Sorun açıklaması

### 🟡 UYARI (Düzeltilmeli)
- [dosya:satır] Sorun açıklaması

### 🟢 ÖNERİ (İyileştirme)
- [dosya:satır] Öneri
```
