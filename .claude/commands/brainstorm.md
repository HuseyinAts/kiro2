---
allowed-tools: Bash, Read, Grep, Glob, Task, Write
argument-hint: [konu veya dosya yolu]
description: 3-4 paralel subagent ile farklı perspektiflerden beyin fırtınası. Mimari, özellik, içerik, strateji kararları için. Tek dosya kod analizi için /analyze kullan.
---

## Ne zaman KULLANMA

- Tek dosya kod analizi → `/analyze`
- Mevcut planı sorgula → `/challenge`
- 3 adımdan az iş veya basit soru → Direkt cevapla
- Aynı konuda zaten brainstorm yapıldıysa → `docs/brainstorms/` kontrol et

## Bağlam (ön-işleme)

- Proje durumu: !`head -60 CLAUDE.md 2>/dev/null || echo "CLAUDE.md bulunamadı"`
- Son brainstormlar: !`ls docs/brainstorms/ 2>/dev/null | tail -5 || echo "Henüz yok"`

## Adım 1: Bağlam topla

$ARGUMENTS konusunu analiz et.

Dosya yolu içeriyorsa → `Read` ile oku, yolunu not et.
Genel konu ise → `Grep` ve `Glob` ile ilgili max 5 dosyayı bul, yollarını not et.

Bu dosya yollarını DOSYA_YOLLARI olarak tut — subagent'lara vereceksin.

## Adım 2: Domain ve perspektif seç

| Domain | Tetikleyici | Perspektif sayısı |
|--------|------------|-------------------|
| **feature** | Yeni özellik, UX, kullanıcı hikayesi | 4 (aşağıdaki personalar) |
| **architecture** | Altyapı, DB, cache, API tasarımı | 3: Performans · Bakım · Maliyet |
| **content** | OCR, pipeline, veri işleme | 3: Kalite · Hız · Hata toleransı |
| **strategy** | TÜBİTAK, pazar, rekabet, büyüme | 3: Hakem · Rakip · Fizibilite |

Karar veremiyorsan kullanıcıya sor.

### Feature personaları (sadece feature domain'de kullan)

**Öğrenci Ahmet (11. sınıf):** Ankara, YKS'ye 10 ay, günde 3 saat, telefondan çalışır, motivasyonu düşük. "2 dakikada anlar mıyım? Arkadaşlarıma gösterir miyim? Bir yük daha mı?"

**Sistem Mimarı:** 100K eşzamanlı kullanıcı. FastAPI + PostgreSQL + Redis + React 18. "Yeni tablo/endpoint? Cache? 100K darboğaz? IRT/FSRS/ZPD entegrasyonu?"

**Ürün Stratejisti:** "Rakipler bunu yapıyor mu? TÜBİTAK katkısı? Freemium/premium sınırı? MVP'de neler OLMAMALI?"

**Eğitim Bilimci:** SR, ZPD, IRT, Bloom, Yerkes-Dodson. "Hangi teori? Metacognition? Sınav kaygısı? Optimal zorluk?"

## Adım 3: Paralel dispatch

⚠️ Maliyet: 3-4 subagent ≈ 25-40K token, 2-4 dakika.

Aşağıdaki kurallara HARFIYEN uy:

1. Her perspektif için **bir Task tool çağrısı** yap
2. Tüm Task çağrılarını **aynı yanıtında** yap (sıralı DEĞİL, paralel)
3. Subagent'a dosya **yolunu** ver — içeriğini yapıştırma, kendisi `Read` ile okusun
4. Sadece Stratejist ve Eğitim Bilimci'ye "CLAUDE.md'yi oku" de (diğerleri gereksiz)

Her Task prompt'u şu yapıda olsun:

```
Sen bir {ROL} olarak düşünüyorsun.

{SADECE Stratejist/Bilimci İÇİN: Proje bağlamı için CLAUDE.md dosyasını Read ile oku.}
{DOSYA_YOLLARI varsa: Şu dosyaları Read ile oku: [yollar]}

Konu: {KONU}

Görev:
1. SADECE kendi perspektifinden 3 somut öneri üret
2. Her öneri: bir cümle açıklama + etki(1-5) + zorluk(kolay/orta/zor) + en büyük risk
3. 1 kör nokta (diğer perspektifler kaçırır)
4. 1 uyarı (bunu yapMAyın)

ZORUNLU: Read tool ile dosya oku, varsayımla konuşma. Max 250 kelime.
```

## Adım 4: Sentez ve doğrulama

Subagent sonuçlarını topla. Sentezle:

1. **Konsensüs**: 2+ perspektifin hemfikir olduğu noktalar
2. **Çatışma**: Ters düşen noktalar — hangisi neden haklı
3. **Kör noktalar**: Birleşik liste
4. **Top 5 aksiyon**: Etki × fizibilite sıralaması

**Doğrulama (max 1 retry per subagent):**
- 3'ten az öneri → 1 kez yeniden fırlat, yine başarısızsa "yetersiz çıktı" olarak not et
- "Performansı artırın" gibi genel cevap → 1 kez yeniden fırlat
- İkinci başarısızlıkta devam et, sentezde belirt

## Adım 5: Çıktı

Terminale: TL;DR (3 cümle) + Top 5 aksiyon

Tam raporu `Write` ile `docs/brainstorms/{YYYY-MM-DD}_{SLUG}.md` olarak kaydet:

```markdown
# Brainstorm: {KONU}
Tarih: {TARIH} | Domain: {DOMAIN} | Perspektifler: {LİSTE}

## TL;DR
{en güçlü 2 öneri + en kritik risk — 3 cümle}

## Top 5 Aksiyon
1. **{aksiyon}** — Etki: X/5 · Zorluk: Y · Kaynak: {perspektif}

## Konsensüs
{2+ perspektifin desteklediği noktalar}

## Çatışmalar
| Konu | Taraf A | Taraf B | Önerilen karar |

## Perspektif Detayları
### {Perspektif 1}
{Subagent çıktısı}

## Kör Noktalar & Uyarılar
{Birleşik liste}
```
