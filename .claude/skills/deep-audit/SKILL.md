---
name: deep-audit
description: Paralel sub-agent'larla sistematik codebase audit. 5+ dosyayi etkileyen audit/review/tarama isteklerinde otomatik yukle.
---

# Deep Audit — Paralel Sub-Agent Sistematik Tarama

## Ne Zaman Kullan
- 5+ dosyayi etkileyen audit, review, tarama istekleri
- Security, model, endpoint, frontend topluca inceleme
- "Deep analysis", "kapsamli tarama", "tum dosyalari kontrol et" gibi istekler

## Ne Zaman KULLANMA
- Tek dosya analizi → `/analyze`
- Bilinen bug fix → `/debug-bug`
- 3'ten az dosya → direkt Read + Grep yeterli

## Adimlari

### 1. Kapsam Belirle
Kullaniciya sor veya istekten cikar:
- Hangi dizinler? (backend/app/, frontend/src/, orchestrator/)
- Hangi concern'ler? (security, models, endpoints, frontend, performance, tests)

### 2. Concern'leri Ayir (max 4 paralel)
Her concern icin AYRI bir Agent tool dispatch et. TUM Agent cagrilarini AYNI YANIT'ta yap (paralel).

| Concern | Hedef Dizin | Odak |
|---------|-------------|------|
| Security | backend/app/api/ + backend/app/core/ | IDOR, auth bypass, injection, hardcoded secrets |
| Models | backend/app/models/ + backend/app/schemas/ | Wrong table, missing is_active, relationship |
| Endpoints | backend/app/api/ | Error handling, missing validation, wrong status code |
| Frontend | frontend/src/ | Type errors, unused imports, dead code |
| Performance | backend/app/services/ | N+1 query, missing index, cache miss |

### 3. Agent Prompt Sablonu

Her Agent'a su prompt'u ver (concern'e gore doldur):

```
Sen bir {CONCERN} analisti olarak {DIZIN} dizinini tara.

Read ve Grep araclariyla dosyalari oku. Root dizin TARAMA (timeout riski).

Her bulgu icin su formatta yaz:
- [dosya:satir] [P0/P1/P2] aciklama — fix onerisi

Severity:
- P0: Security hole, data loss, crash
- P1: Bug, wrong behavior, missing validation
- P2: Code smell, performance, maintainability

Max 10 bulgu, severity sirasinda. 250 kelime limit.
Somut ol — "performans sorunu olabilir" gibi genel ifade YASAK.
"X dosyasinda Y satirdaki Z fonksiyonu W sebebiyle kirilir" formatinda yaz.
```

### 4. Sentezle

Tum agent sonuclari geldikten sonra:

1. **P0 listesi**: Hemen fix edilmesi gereken (security, crash)
2. **P1 listesi**: Bu sprint icinde fix
3. **P2 listesi**: Teknik borc olarak kaydet
4. **Konsensus**: 2+ agent'in ayni sorunu isaretlemesi = yuksek guvenilirlik
5. **Catisma**: Agent'lar farkli gorusteyse hangisi hakli ve neden

### 5. Rapor Kaydet

```bash
# docs/audits/{YYYY-MM-DD}_{konu}.md formatinda kaydet
```

Rapor formati:
```markdown
# Audit: {KONU}
Tarih: {TARIH} | Concern'ler: {LISTE} | Agent sayisi: {N}

## P0 (Hemen Fix)
1. [dosya:satir] aciklama — fix onerisi

## P1 (Sprint Icinde)
...

## P2 (Teknik Borc)
...

## Konsensus
{2+ agent'in hemfikir oldugu noktalar}
```

### 6. P0 Fix (Opsiyonel)

Kullanici onaylarsa P0 bulgularini hemen fix et — TDD loop ile:
1. Fail eden test yaz
2. Fix uygula
3. Test PASS dogrula

## Kurallar
- Root dizin (`C:\Users\husey\kiro2`) ASLA taranmaz (30dk timeout!)
- Her agent max 1 dizin hedefler
- Max 4 paralel agent (maliyet kontrolu)
- Agent'lar dosya ICERIGI degil dosya YOLU alir — kendileri Read ile okur
