---
name: iddia-dogrula
description: Denetim kütüğündeki (docs/audits/*/iddialar.yaml) bir iddiayı canlı kodda ölçerek doğrular veya fantom olduğunu kanıtlar. Bir panel/denetim bulgusunun gerçek olup olmadığı sorulduğunda, "bu P0 gerçek mi", "şu bulguyu doğrula", "fantom mu" denildiğinde kullan. Ana bağlamı kirletmez.
argument-hint: "<iddia-id> (örn. U13) veya 'hepsi'"
context: fork
agent: iddia-dogrulayici
model: sonnet
allowed-tools: Read, Grep, Glob, Bash
---

# İddia Doğrulama

Kütük: `docs/audits/2026-08-12_25uzman/iddialar.yaml`
Hedef iddia: **$ARGUMENTS**

Bu bir envanter doğrulamasıdır. Bulgun ne olursa olsun kimse cezalandırılmaz ve
hiçbir şey silinmez; yalnızca kütüğe yazılır.

## Bugünün canlı durumu

Dal: !`git rev-parse --abbrev-ref HEAD`
Son commit: !`git log --oneline -1`
Commit'siz dosya: !`git status --short | wc -l`

## Adımlar

1. **Kütüğü oku.** `docs/audits/2026-08-12_25uzman/iddialar.yaml` içinde
   `id: $ARGUMENTS` olan girdiyi bul. `ankraj`, `iddia`, `curutme_sorusu`,
   `dogrulama` ve varsa `on_bulgu` alanlarını al.

2. **`on_bulgu` varsa önce ONU sına.** Ön bulgu bir hipotezdir, kanıt değildir.

3. **`dogrulama` listesindeki komutları koştur.** Hepsini. Çıktıyı sakla.

4. **`curutme_sorusu`nu ciddiye al.** O soru, iddiayı düşürmek için yazıldı.
   Cevabı "hayır, yine de sorun var" ise bunu kanıtla göster.

5. **Dört çürütme yolunu uygula** (subagent tanımında): zaten kapalı mı ·
   yanlış ad mı · başka katmanda mı · semantik yanlış mı.

6. **Severity'yi ayrıca ölç.** `severity_iddia` ile aynı çıkmak zorunda değil.

7. **Fix'in değerini sor.** Bu düzeltilirse ölçülebilir ne değişir? Cevap
   "hiçbir şey" veya "bilinmiyor" ise bunu yaz — düzeltme kararını bu belirler.

## Bitiş kriteri

Şu blok üretilmeden bitirme:

```
IDDIA: <id>
YARGI: dogrulandi | fantom | abartili | olculemedi
SEVERITY_OLCULEN: P0|P1|P2|P3|yok
KANIT:            <komut + gerçek çıktı>
CURUTME_DENEMELERI: <4 yol, her biri sonuçlu>
GEREKCE:          <2-4 cümle>
FIX_DEGERI:       <ölçülebilir etki veya "bilinmiyor">
KUTUK_YAMASI:     <iddialar.yaml'a yazılacak durum/kanit/severity_olculen alanları>
```

`KUTUK_YAMASI` olmadan iş bitmemiştir — kütük mekanik kuyruktur, "bitti" demek
diskteki dosyanın güncellenmesi demektir.

## Yasak

- Düzeltme yapma. Bu skill yalnız **yargılar**.
- "Muhtemelen/görünüyor/olabilir" ile yargı verme → `olculemedi` yaz.
- Kontrol kolu beklenen sonucu vermediyse yargı **her zaman** `olculemedi`.
