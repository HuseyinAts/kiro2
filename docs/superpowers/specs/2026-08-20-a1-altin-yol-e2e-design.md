# A1 Altın Yol — uçtan uca ölçüm ve düzeltme (tasarım)

**Tarih:** 20 Ağustos 2026 · **Oturum:** S241 · **Dal:** `feature/self-evolution-optimization`
**Taban commit:** `d488ecb7d`

---

## 1. Neden şimdi

KIRO2'nin tek kabul kriteri (CLAUDE.md, A1):

> Yeni bir öğrenci kayıt olur → e-postasını doğrular → 40 soruluk bir TYT Matematik
> testi çözer → netini ve konu kırılımını görür.

Bu zincir **bugüne kadar hiç uçtan uca koşulamadı**, çünkü öğrenci kapısı
(`mv_safe_for_beta`) ya boştu ya da içindeki içerik servis edilemezdi:

| Tarih | Kapı | Örneklem okuması |
|---|---|---|
| S231 (19 Ağu) | 27.073 | **0/40** servis edilebilir |
| S238 (20 Ağu) | 0 | (36.967 sentetik satır silindi) |
| S239 (20 Ağu) | 3.560 | **12/12** gerçek, kitap kaynaklı |

20 Ağustos 2026 canlı ölçümü (`psql`, port 5434, db `kiro2`):

```
question_bank      3.922
mv_safe_for_beta   3.560
  └─ MAT dilimi      353   (14 farklı konu kodu)
  └─ KIM dilimi    3.207
```

353 ≥ 40 → **A1'in içerik engeli ilk kez kalktı.** Zincirin kalanı (kayıt,
doğrulama, sınav üretimi, puanlama, yüzey) hiç ölçülmedi.

İkinci gerekçe: oturum banner'ı önceki turda **37 commit / 0 kullanıcı-görünür
çıktı** raporladı (E3 uyarısı). Devir notunun "Sonraki Adımlar" listesindeki beş
kalemin beşi de altyapı işi; hiçbiri A1'i ilerletmiyor.

## 2. Tasarımın merkezî kararı: önce ölç, sonra kır

Bu oturumun ilk 20 dakikasında **kendi ölçüm aletim iki kez yanıldı**:

1. `WHERE primary_topic_id LIKE 'MAT%'` → **0** döndü. Kolon UUID; `MAT.*` kodu
   `topic_hierarchy.code`'da yaşıyor. Yanlış katman.
2. `information_schema.columns WHERE table_name='mv_safe_for_beta'` → **boş**
   döndü. Materialized view orada değil, `pg_attribute`'da.

İkisi de "bulgu" değil **alet arızası**ydı ve ikisi de yeşil/sıfır görünüyordu.
Bu, S239'un kayıtlı dersinin (*"0 bulundu" her seferinde önce ALET ARIZASI
varsayılmalı*) birebir tekrarı.

Sonuç: tasarım, ölçümü düzeltmeden **ayırır** ve her bulguyu bağımsız bir
şüpheciye çürüttürür. Varsayılan yargı **ÇÜRÜTÜLDÜ**'dür; bir bulgu ancak ham
çıktıyla ayakta kalırsa engelleyici sayılır.

## 3. Kapsam — A1'in dört ayağı

| Ayak | Ölçülecek soru | Kabul edilen kanıt |
|---|---|---|
| **L1 Kayıt** | `POST /api/v1/auth/kayit` yeni öğrenciyle ne dönüyor; `users` + `student_profiles` satırı düşüyor mu; `role` ve `is_verified` hangi değeri alıyor | HTTP kodu + ham gövde + `psql` satırı |
| **L2 Doğrulama** | `users.is_verified`'ı **hangi kod yolu** set ediyor; `/auth/giris` doğrulanmamış hesabı blokluyor mu; `magic-link/send` + `/verify` zinciri çalışıyor mu; e-posta gönderimi tam olarak nerede düşüyor | `dosya:satır` ankrajı + canlı HTTP + container log satırı |
| **L3 Sınav üretimi** | `POST /api/v1/exams/generate-mock` **40 TYT MAT** sorusu dönüyor mu; sorular **kapıdan** mı geliyor; beş şık tam mı; **`correct_answer` istemciye sızıyor mu** | ham JSON gövdesi (kesilmemiş) |
| **L4 Puanlama** | `POST /{id}/answer` + `POST /{id}/submit` çalışıyor mu; net formülü (D − Y/4) doğru mu; **konu kırılımı** doğru konulara mı yazıyor | bilinen cevap seti → beklenen net vs dönen net |
| **L5 Yüzey** | `/exam/start` → `/exam/:id` → `/exam/:id/results` gerçekten render ediyor mu; konsol hatası var mı; sonuç ekranında net + konu kırılımı görünüyor mu | Playwright ekran görüntüsü + konsol dökümü |

**L2 kasıtlı olarak açık uçlu.** Canlı OpenAPI'de `/auth/verify-email` yok;
`users.is_verified` kolonu var ama onu set eden kullanıcı-yolu görünmüyor.
Uç inşa edilip edilmeyeceği **ölçümden sonra** karara bağlanır — kullanıcının
açık tercihi bu yönde. Yanlış varsayımla uç inşa etmek bu tasarımın önlemek
istediği şeydir.

## 4. Faz akışı

```
FAZ 0  (elle)        tek test hesabı aç + token al; kanıtı yakala; workflow'a args ile geç
FAZ 1  (5 ölçücü)    L1-kod · L2 · L3 · L4 · L5 — PARALEL, salt-okunur
FAZ 2  (5 çürütücü)  her ayağın bulguları ayrı şüpheciye: "gerçek kusur mu, alet arızası mı?"
FAZ 3  (1 eleştirmen) "hangi ayak / hata modu hiç ölçülmedi?"
FAZ 4  (elle)        doğrulanmış engelleyici listesi → kullanıcı onayı → TDD düzeltme
```

FAZ 0'ın elle yapılmasının nedeni yapısal: L2–L5 ölçümlerinin hepsi aynı
kimlik doğrulanmış oturuma bağımlı. Hesabı ajanlara açtırmak beş ajanın beş
ayrı hesap yaratmasına ve ölçümlerin farklı özneler üzerinde koşmasına yol açar.

## 5. Sert kısıtlar

- **FAZ 1–3 salt-okunur.** Hiçbir ajan `Edit` / `Write` çağırmaz, DB'ye yazmaz,
  container yeniden başlatmaz. Tek yazma istisnası FAZ 0'daki damgalı test hesabı.
- **`question_bank`, `question_content`, `mv_safe_for_beta` okunur, YAZILMAZ.**
  `correct_answer` ve `is_active` bu oturumda hiçbir yolla değişmez.
- **Kanıtsız bulgu geçersiz.** "Endpoint 500 dönüyor" bir iddiadır; kabul edilen
  şey `curl` gövdesidir. FAZ 2 kanıtsız bulguyu düşürür.
- **Metin kesilmez.** Ham gövde uzunsa örneklem küçültülür, `…[TRUNCATED]`
  işaretlenmeden kesilmez (audit-methodology.md).
- **Düzeltme yalnız FAZ 4'te**, kullanıcı onayıyla, TDD ile (önce kırmızı test),
  düzeltme başına en fazla 3 dosya.

## 6. Başarı kriteri

Bu oturum ancak şu iki şart birlikte sağlanınca "bitti" sayılır:

1. **Dört ayağın her biri** için üç yargıdan biri, kanıtla:
   `ÇALIŞIYOR (ham çıktı)` · `KIRIK (ham çıktı + kök neden `dosya:satır`)` ·
   `YOK (kod ankrajı)`. Tahmin, "muhtemelen", "büyük ihtimalle" kabul edilmez.
2. **En az bir doğrulanmış kırık ayak düzeltilmiş** ve düzeltme
   `backend/api` · `backend/services` · `backend/algorithms` · `frontend/src`
   yollarından birine düşmüş olmalı (E3 kullanıcı-görünür çıktı ölçütü).

Eğer dört ayak da çalışıyor çıkarsa (beklenmiyor ama mümkün), 2. şart
**A1 kabul testinin kendisini kalıcı bir bekçiye dönüştürmekle** karşılanır —
yani zincir bir daha sessizce kırılamaz.

## 7. Yapılmayacaklar (YAGNI)

- Kalan ~3.500 MAT sorusunun kör okunması — A1 eşiği (≥40) 353 ile zaten 8 kat aşılı.
- `MAT.IST` (12 soru) konu dengesizliğinin düzeltilmesi — A1'i etkilemiyor.
- `#495` boş exception handler'ları, CRLF ankraj enforcement'ı, yedek tabloların
  düşürülmesi — kullanıcı-görünür çıktı üretmez, E3 uyarısını ikinci kez tetikler.
- Gerçek SMTP teslimi — operatör/kimlik-bilgisi işi, kod işi değil.
- İlgisiz refactor. Dokunulan her satır A1 zincirine izlenebilir olmalı.

## 8. İlişkili

`CLAUDE.md` (A1 + E3) · `.claude/rules/audit-methodology.md` (alet doğrulama,
örneklem, kesme yasağı) · `.claude/rules/verification.md` (infra-first, TDD) ·
`.claude/sessions/latest.md` (S238–S240 devir notları) ·
`.claude/lessons/ders_kaydi.yaml` (`L-s232-bulguyu-degil-aleti-sina`)

> **Öz-denetimde çıkan yan bulgu (kapsam dışı, açık iş olarak kaydedildi):** bu
> spec ilk yazımda `L-s239-sifir-once-alet-arizasi` diye bir dersi ankraj
> gösteriyordu — **böyle bir ders yok.** Defter `L-s233-*` ile bitiyor; S238,
> S239 ve S240 devir notlarının "yeni ders adayı" dediği dersler
> (*boş küme üzerinde geçen bekçi = yeşil alet arızası*, *"0 bulundu" önce alet
> arızası varsayılmalı*, *oran dersten derse değişir*) **deftere hiç girmemiş.**
> Devir notunda ders ilan etmek onu kaydetmek değildir.
