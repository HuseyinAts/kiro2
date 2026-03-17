---
name: debugging-first
description: Bug fix oncesi ZORUNLU kok neden dogrulama protokolu
trigger: always
priority: high
---

# Debugging-First Protocol

> 46 wrong_approach friction event (77 session'da). #1 zaman kaybi.

## BUG FIX BASLAMADAN ONCE 3 KONTROL

### 1. Endpoint Dogrulama
- Hangi endpoint hata donuyor? `curl` ile dogrula
- Error response'u oku — gercek hata mesaji ne?
- Sessiz basarisizlik var mi? (200 donup bos data)

### 2. Veri Kaynak Dogrulama
- Sorgulanan tablo DOLU mu? (`SELECT COUNT(*) FROM table_name`)
- `question_bank` = 77K production, `questions` = BOS legacy
- `is_active = TRUE` filtresi var mi?

### 3. Altyapi Kontrolu
503/500 → %75 altyapi sorunu.
Komutlar icin bkz: verification.md > INFRA-FIRST bolumu.

## FIX STRATEJISI

YANLIS: Hemen koda dal, tahminle fix yaz
DOGRU:
1. Hatayi reproduce et (curl/test)
2. Root cause'u dogrula (log/trace/debug)
3. Tek dosyada minimal fix
4. Test ile dogrula

## TEKRARLAYAN HATALAR

Bu pattern'lerden birini gordugunde UYARI ver:
- Bos tablo sorgulama (questions vs question_bank)
- Yanlis endpoint fix etme (path collision, route siralama)
- Silent exception handler maskeleme (bare except, pass)
- Mock uyumsuzlugu (eski mock, yeni API)
- Pydantic dict-style access (obj["field"] yerine obj.field)
- get_async_session context manager olarak kullanma (generator!)
