---
allowed-tools: Read, Grep, Glob, Task
argument-hint: [plan veya fikir açıklaması]
description: Bir planı 3 paralel eleştirmenle stres-testine tabi tut. Hızlı, dosya yazmaz. Stratejik beyin fırtınası için /brainstorm kullan.
---

## Bağlam (ön-işleme)

- Proje öncelikleri: !`head -30 CLAUDE.md 2>/dev/null || echo "CLAUDE.md yok"`

## Görev

$ARGUMENTS planını stres-testine tabi tut.

Önce `Grep`/`Glob` ile planla ilgili mevcut dosyaları bul. Yollarını not et.

Sonra **3 Task çağrısını aynı yanıtında** (paralel) yap:

**Task 1 — Pessimist Mühendis:**
```
Bir pessimist mühendis olarak düşün.

Şu dosyaları Read ile oku: {BULUNAN_DOSYA_YOLLARI}

Plan: $ARGUMENTS

Görev:
1. Bu plan nerede kırılır? 3 somut kırılma senaryosu yaz
2. Mevcut kodda bu planla çelişen kısımlar var mı? (dosyalardan kontrol et)
3. Gözden kaçan edge case?

"Riskli olabilir" gibi genel cevap YASAK. "X olduğunda Y kırılır çünkü Z" formatında yaz.
Max 200 kelime.
```

**Task 2 — Rakip Analisti:**
```
Bir rakip analisti olarak düşün.

CLAUDE.md dosyasını Read ile oku — rakip bilgileri ve proje durumu orada.

Plan: $ARGUMENTS

Görev:
1. Türk EdTech rakipleri bu sorunu nasıl çözdü veya çözerdi?
2. KIRO2'nun yaklaşımı neden daha iyi veya daha kötü?
3. YKS öğrencisi (16-18 yaş) bu plandan memnun olur mu?

Max 200 kelime.
```

**Task 3 — Pragmatist:**
```
Bir pragmatist olarak düşün.

CLAUDE.md dosyasını Read ile oku — mevcut öncelikleri ve darboğazları öğren.

Plan: $ARGUMENTS

Görev:
1. Bu kaç gün sürer? (iyimser / gerçekçi / kötümser tahmin)
2. %80 değeri %20 eforla veren daha basit alternatif?
3. Mevcut önceliklere göre doğru zamanlama mı?

Max 200 kelime.
```

## Doğrulama (max 1 retry)

Her subagent en az 2 somut bulgu üretmiş mi? "Riskli olabilir" gibi boş cevap varsa → 1 kez yeniden fırlat. İkincide de boşsa devam et, sentezde "yetersiz analiz" olarak belirt.

## Çıktı (sadece terminal)

```
⚠️ KRİTİK (hepsi hemfikir):
1. {somut senaryo}

🤔 TARTIŞMALI:
1. {konu} — Pessimist: {görüş} / Pragmatist: {görüş}

✅ GÜVENLİ (eleştiri yok):
1. {alan}

💡 ALTERNATİF: {Pragmatist'in basit alternatifi}

⏱️ SÜRE TAHMİNİ: {iyimser} / {gerçekçi} / {kötümser} gün
```
