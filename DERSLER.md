# KIRO2 — Dersler ve Çalışma Prensipleri

**Kaynak:** 20 Nisan 2026 diary_api pilot oturumu (3 tur öz-eleştiri dahil)
**Kurumlaştırma tarihi:** 20 Nisan 2026
**Tamamlayıcı:** `.cursor/rules/99-meta-pilot-protocol.mdc` (operasyonel kurallar)

Bu doküman KIRO2'de Claude ve Composer 2 ile nasıl çalıştığımızın hikayesidir. Operasyonel kurallar `.mdc` dosyasındadır; bunlar **neden böyle olması gerektiği**.

---

## 📖 Kısa Tarihçe — 20 Nisan 2026

Kullanıcı (Hüseyin) Cursor Pro aldı. Composer 2'nin KIRO2'de nerelerde kullanılacağını sordu. Claude ilk yanıtta 5 alan önerdi, içinde CursorBench 61.3 gibi benchmark sayıları yazdı, audit raporlarını okumadan iş önerdi.

Kullanıcı "gözden geçir" dedi. Claude 8 hatasını kabul etti. Öneri 2 alana indi, sonra tek pilota: `diary_api` aktivasyonu.

Pilot 3 dosya üretti: plan + ADIM 0 state + RESULT. Aşama B çıktı (tablolar var, Alembic drift var), smoke test geçti. Sonra 12 router için batch ADIM 0 yapıldı. Briefing v12'den v13'e güncellendi. Yeni çalışma düzeni kurumlaştırıldı.

Bu dokümana düşen işin **meta**'sıdır: ne yaptık, neden yaptık, nasıl tekrar ederiz.

---

## 🎯 Bölüm 1 — Claude'un Tekrar Etmemesi Gereken 8 Hata

### 1. Audit Raporlarını Okumadan Öneri Üretmek

İlk yanıtta 5 alan önerdim. `FRONTEND_AUDIT.md`, `INFRA_TEST_AUDIT.md`, `AI_PIPELINE_AUDIT.md`, `AUDIT_PLAN.md`, `BACKEND_AUDIT.md`, `REPO_MAP.md`, `AUTH_CANONICAL_PATH.md` + 4 tane daha auth audit dosyasının varlığından habersizdim. Kullanıcı düzeltti.

**Ders:** Yeni sohbette öneri üretmeden önce `ls *.md` benzeri bir tarama yap. Proje kökünde 15+ `.md` dosyası var, hepsi kanıt kaynağı. Önce okuyup sonra konuş.

### 2. Ezberden Benchmark Sayıları Kullanmak

"CursorBench 61.3", "SWE-Bench Multilingual 73.7", "Terminal-Bench 61.7" yazdım. Kaynak olarak `.cursor/commands/best-of-n.md` gösterdim — ki o dosyayı ben daha önceki bir sohbette yazmıştım. **Döngüsel referans.**

**Ders:** Benchmark sayısı, fiyat, süre gibi somut rakamlar için:
- Kaynak doğrulanabilir mi? (Cursor resmi blog, Anthropic API dokümantasyonu gibi)
- Değilse "bu sayıyı doğrulayamıyorum" de, çıkarma
- Kendi yazdığım dosyayı kaynak diye gösterme

### 3. "EN Parlak Noktası" Abartısı

"Bu Composer 2'nin EN iyi yaptığı iş" dedim. Gerçek: birçok LLM aynı işi yapabilir. Composer 2 tercih nedeni genelde **maliyet** (Pro havuz) veya **ergonomi** (terminal integration), "EN iyi" değil.

**Ders:** "Yeterli ve ekonomik" ile "en iyi" farklı. Abartma. Bir iş için "bu Composer 2'ye uygun" demek yeterli, "en parlak noktası" demek değerlendirmeyi bozar.

### 4. "Pro Havuzda ≈$0" İddiası

Cursor Pro'da Composer 2 cömert havuzda denilmiş ama sınırsız değil. "Pratik olarak sınırsız" gibi kaçamak ifade de yanıltıcı — quota gerçek.

**Ders:** "Quota dahil" de, rakam uydurma. Kullanıcı bütçe kararı verirken yanıltıcı olur.

### 5. Git Log Kontrol Etmeden İş Önerme

Briefing 6 Nisan tarihliydi. 20 Nisan'da iş önerirken son 2 haftanın commit'lerini hiç bakmadım. Belki auth konsolidasyon başlamış, belki XSS işi yapılmış. Kontrol edilmeden "şunu yapalım" önerisi körlemesine.

**Ders:** Yeni sohbette ilk adımlardan biri: `git log --since='2 weeks ago' --oneline`. Briefing ile gerçek arası delta var mı?

### 6. 5-10 Alternatif Menü Çıkarma Tuzağı

İlk yanıtımda 5 alan önerdim: "Seç, hangisini istersin?" Bu karar yükünü kullanıcıya atar. Kullanıcı uzman değil benim uzman olduğum konuda değil, benim pozisyon almam bekleniyor.

**Ders:** Tek net öneri + gerekçe. "Ama alternatif istersen X, Y" şeklinde değil. Alternatif ancak kullanıcı "başka seçenek var mı?" derse sunulur.

### 7. Risk Analizi Yokluğu

Plan önerirken "ne ters gidebilir" demedim. Alembic upgrade geri dönüşsüz. Migration yanlış yazılırsa IRT kolonları gidebilir. Production DB'ye sızarsa kullanıcı verisi kaybolabilir. Bunların hiçbirinden bahsetmedim ilk turda.

**Ders:** Her pilot planında Risk Matrisi bölümü zorunlu. En az 3-5 risk + azaltma. Düşük/orta/yüksek sınıflandırmasıyla.

### 8. Composer 2'ye TDD Coverage İşi Önerme

"services/ %35 → %80 coverage" önerdim. Kullanıcı daha önce **138 fake test silmiş** (`assert x is not None or x is None` gibi pattern'ler). Composer 2'ye "test yaz" demek otomatik fake test fabrikası açmak demek — prompt'ta "YASAK" yazsam bile LLM unutur.

**Ders:** Test coverage işini Composer 2'ye verme. Ya insan tek tek review eder, ya da önce CI gate'i yaz (`ruff` veya `semgrep` rule ile `is not None` pattern'ini yasakla), sonra ver. Kullanıcının geçmiş çalışmalarını sayma; bir kez fake test silmiş ise bir daha istemiyor.

---

## ✨ Bölüm 2 — Doğru Yaptıklarımız (Koruma Altına Alınmalı)

### 1. Pilot 3-Dosya Pattern'i

Plan → State → Result. Her biri farklı aşamada farklı yazar (Claude/Composer 2), ama dosya türü sabit. Bu yapı:
- Prior knowledge birikimini sağlar (`backend/_pilots/` arşiv)
- Tekrarlanabilirlik getirir (yeni pilot aynı iskeleti kullanır)
- İnsan review noktalarını netleştirir (plan ortada, result sonda)

**Korunması için:** Her yeni pilotta 3 dosya üret. Eksik bırakma. Tek dosya "hepsini toplayan" versiyona kaçma — bölmek değerli.

### 2. ADIM 0 — Gerçek Durum Tespiti

Kod yazmaya başlamadan önce psql + docker logs + alembic current ile **mevcut durumu kanıtla**. Diary pilotunda briefing'le 3 çelişki çıkardı: token alanı, disabled router sayısı, Alembic head. Bu çelişkiler bulunmasa migration yanlış yazılacaktı.

**Korunması için:** Her pilot plan'ı 6-7 adımdan fazla olsa da ADIM 0 her zaman 1 numara. Atlama.

### 3. Aşama A/B/C/D/E Sınıflandırması

Batch ADIM 0'da 12 router'ı 5 aşamaya ayırdık. Bu sınıflandırma artık **karar ağacı**: Aşama B ise pilota uygun, Aşama D ise altyapı kararı önce, Aşama E ise manuel review önce.

**Korunması için:** Yeni router'lar geldiğinde aynı 5 aşamayla sınıflandır. Yeni aşama ekleme — 5 yeter.

### 4. Prior Knowledge Pattern

Composer 2 prompt'una `backend/_pilots/*_state.md` okutmak. Aynı `users.id` VARCHAR kontrolünü 10 pilotta tekrarlamak zaman israfı. Önceki bulguları öğret.

**Korunması için:** Her yeni pilot prompt'unda "Prior Knowledge" bölümü zorunlu.

### 5. Hook'suz Amend Tekniği

`git -c core.hooksPath=.git/hooks-empty commit --amend` — Cursor'un "Made-with" footer'ını atlatır. Kullanıcı bunu istiyor çünkü commit mesajı proje kaydı, Cursor reklamı değil.

**Korunması için:** Her commit'ten sonra `git log -1` bak. Footer varsa amend et. Bu artık standard.

### 6. "Durma Noktaları" Mekanizması

Her plan'da 5-7 "bana sor, sonra devam et" tetikleyicisi. Beklenmedik tablolar, UUID FK, birden fazla head, vs. Bu mekanizma Composer 2'nin körlemesine ilerlemesini engelliyor.

**Korunması için:** Her plan'da bu bölüm olmalı. "Composer 2 kapsamı genişletebilir" diye düşünüp önceden engelle.

### 7. Artifact'lere Commit Hijyeni

Her pilot commit'i tek mantıksal grup, hook'suz, net mesaj. Git log okunabilir. `ede451a` → `ab6c8b8` → `83421cc` her biri bir iş.

**Korunması için:** Bir commit'te 5 farklı iş birleştirme. "Bunu da eklerim" dürtüsüne direnç göster.

---

## 👤 Bölüm 3 — Kullanıcı Tercihleri Kataloğu

Bu sohbette gözlemlenmiş Hüseyin tercihleri. Bunları bir kere öğren, her sohbette uygula.

### Dil ve Ton

- **Türkçe öncelikli.** Teknik terimler İngilizce (`commit`, `router`, `migration`, `endpoint`) ama açıklama Türkçe
- **Kısa yazışmalar tolere eder.** "ADIM 1", "A", "COMM" gibi tek kelime mesajlar gelebilir — bağlamdan çıkar, "bunu mu demek istediniz?" sormaya gerek yok (çoğunlukla)
- **Resmi değil ama seviyeli.** "Abicim" tonunu değil, "meslektaşlar konuşuyor" tonunu tutturur
- **Emoji az ama stratejik.** Sen de öyle yap — başlıklarda emoji tamam, paragraflarda aşırıya kaçma

### Öz-Eleştiri Beklentisi

- "Gözden geçir" dediğinde beklenti: kendi yanıtındaki 5-10 problemi açıkça listele
- Problemi kabul ettikten sonra yeniden yapma; tekrarlarsan güven kaybı
- Savunmaya geçme, "o zaman iyi niyetliydim" deme. Hata hatadır

### Karar Mekanizması

- Alternatif menüsünden hoşlanmaz
- Tek net öneri + gerekçe ister
- Ama kararı kendisi verir. "Bunu yapacağız" demekle "bunu yap" demek arasındaki sınırı tutar
- Risk görünür olduğunda bekler; görünmediğinde ilerler

### Çalışma Ritmi

- Pilot odaklı. 2-4 saatlik bölümler halinde ilerler
- Backup + ADIM 0 + smoke test zinciri sapmaz
- Alembic upgrade, git push gibi geri dönüşsüz işleri kendi yapar; Composer 2 veya Claude'a vermez
- Her pilot sonunda doğal duraklama kabul eder; zorlamaya gerek yok

### Ezbere Karşı Hassasiyet

- "Bizzat gör, ezberden konuşma" — bu sohbetin baş sloganı
- Benchmark sayısı, token miktarı, tablo sayısı için kanıt ister
- Briefing alıntılamak yetmez — canlı gözlem lazım
- "Muhtemelen", "genelde" gibi ifadeleri kanıtla destekle

### Commit Detayı

- Hook'suz (`core.hooksPath=.git/hooks-empty`)
- Subject + boş satır + gövde
- Çoklu `-m` yerine tek uzun mesaj daha iyi
- Push'u kendisi yapar

---

## 🧭 Bölüm 4 — Meta-Prensipler (Her Pilot için Geçerli)

### Prensip 1: Gerçek Kaynak Canlı Kod + DB

Briefing eskiye kalır. Audit raporları zamana yenilir. **Anlık doğrulama** için:

| Soru | Gerçek Kaynak |
|---|---|
| Hangi router'lar disabled? | `backend/routers/loader.py` `DISABLED_ROUTERS` set'i |
| Hangi tablolar var? | `information_schema.tables` |
| Alembic nerede? | `alembic current` + `alembic heads` |
| Auth şeması? | `/api/v1/auth/giris` gerçek response |
| FK tipleri? | `information_schema.columns.data_type` |

Briefing bu bilgileri tekrarlar ama **otoritatif değildir**. Çelişki varsa canlı kazanır.

### Prensip 2: Composer 2'nin Yeri Mekanik, İnsanın Yeri Karar

Composer 2 çok iyi bir **uygulayıcı** ama zayıf bir **karar verici**. Bu ayrım bilinçli tutulmalı:

- Pattern'i uygula → Composer 2
- Pattern'i tasarla → Claude (planlar)
- Pattern arasında seç → İnsan (aşama kararı)
- Geri dönüşsüz eylem → İnsan

Bu üçgeni bozma. Composer 2'ye "hangi aşama?" sorma — bilmez, tahmin eder, yanılır.

### Prensip 3: Rollback Yolu Olmayan İş Yasaktır

Backup + plan'da rollback bölümü + düşük kapsam commit = geri dönüş güvencesi. Bu üçlüyü kuramıyorsan pilot başlatma, başka zaman yap.

Rollback yolu örnekleri:
- Alembic: `alembic downgrade -1`
- Kod: `git revert <commit>`
- DB veri: `pg_restore` backup'tan
- Migration halâ `.disabled`: arşive taşıma ters çevrilebilir

### Prensip 4: Artifact Biriktirmek Değerlidir

Her pilot üç dosya bırakır. Zaman içinde `backend/_pilots/` dizini proje tarihçesini taşır. 6 ay sonra "neden bu migrationu yaptık?" sorusunun cevabı orada olur.

Bu birikim **Composer 2'nin prior knowledge kaynağı** olarak da değerli — hatırlanmaya mahkum değil, yazılı.

### Prensip 5: Dokümantasyon Drift'i Gerçektir

Briefing haftada yenilenmezse günceliğini kaybeder. v12 6 Nisan'da yazıldı, 20 Nisan'da 3 noktada yanlıştı. Bu normal — kod değişir, doküman geç kalır.

**Uygulama:** Her pilot sonunda briefing güncellemesi var mı kontrol et. Küçük değişiklikler de olsa (auth token alanı gibi) işaretle.

---

## 🔄 Bölüm 5 — Yeni Sohbetler için Checklist

Yeni Claude sohbeti açıldığında (bu dosyayı okuduktan sonra) ilk adımlar:

**Adım A — Bağlam edin (5 dakika)**

- [ ] `KIRO2_SESSION_BRIEFING.md` (v13+) oku
- [ ] `NEXT_SESSION_HANDOFF.md` varsa oku, yoksa git log'dan son 2 hafta özet çıkar
- [ ] `backend/_pilots/*_state.md` dosyalarını listele (hangi pilotlar yapıldı?)
- [ ] `git status` + `git log --oneline -15` (son durumu gör)

**Adım B — Pozisyon al (2 dakika)**

- [ ] "Şu an şu 3 açık iş var" şeklinde kullanıcıya sun
- [ ] Her biri için: süre, risk, aşama önerisi
- [ ] Menü değil, öncelik sırası ver

**Adım C — Kullanıcı seçtikten sonra (her pilot başlangıcında)**

- [ ] Plan dosyası `.cursor/plans/YYYYMMDD_<iş>.md` yaz
- [ ] Plan'da ADIM 0 + Risk Matrix + Durma Noktaları var
- [ ] Composer 2 prompt'u prior knowledge referansıyla hazırla
- [ ] İnsan backup aldığını doğrula
- [ ] Pilot başlar

**Adım D — Pilot sonunda (her pilot kapanışında)**

- [ ] `backend/_pilots/*_state.md` Composer 2 yazdı mı?
- [ ] `.cursor/plans/*_RESULT.md` yazıldı mı?
- [ ] Briefing değişikliği gerekli mi? (çelişki varsa listele)
- [ ] Commit hook'suz amend ile temiz mi?
- [ ] Sonraki pilot önerisi net mi?

---

## ⚠️ Bölüm 6 — Kaçınılması Gereken Tuzaklar

### Tuzak 1: "Hepsini Temizleyelim" Dürtüsü

12 disabled router var. Hepsini bir günde aktifleştirme dürtüsü gelir. **Direnç göster.** Diary pilotunda 4 saat geçti; 12 × 4 = 48 saat, hiçbir insanın hiçbir günde kaldıramayacağı kapsam. Hepsi birbirine bağımlı değil, tek tek gitmek doğru.

### Tuzak 2: "Bunu da Ekleyelim" Kapsam Genişlemesi

Diary pilotunda Alembic drift çıktı. "O zaman genel drift stratejisini de çözelim" demek pilotu 4 saatten 1 haftaya uzatır. Drift stratejisi ayrı pilot. Dar kapsam = bitebilir pilot.

### Tuzak 3: "Composer 2 Anlar" İyimserliği

Prompt ne kadar net yazsan da Composer 2 bazen kapsamı genişletir. Her komut onayında **ne yaptığını oku**. `git commit` ve `alembic upgrade` niyetleri özellikle kontrol.

### Tuzak 4: "Staging Yok Önemi Yok" Fantezisi

Dev DB = tek DB. Yanlış migration tüm 77K soruyu kaybettirir, tüm IRT kalibrasyonu siler. `pg_dump` zorunlu, opsiyonel değil.

### Tuzak 5: "Briefing Söylüyor" Güveni

Briefing hipotez. ADIM 0 kanıt. Briefing söyleseydi de tablolar DB'de olacak garantisi yok. Her pilot öncesi canlı doğrula.

### Tuzak 6: "İkinci Opinyonu Atlayayım" Aceleciliği

Plan yazıp direkt "şimdi çalıştır" demek. Kullanıcı review etmeli. Onun gözü farklı görür; senin kaçırdığın şey onun "dur bir saniye"sinde yakalanır.

---

## 🛠️ Bölüm 7 — Bu Dokümanın Bakımı

Bu dosya **kalıcı** — ama **donmuş** değil. Yeni ders çıktıkça eklenmeli.

### Ne Zaman Güncellenir

- Yeni bir pilot tekrar eden bir hata ortaya çıkarırsa → Bölüm 1'e ekle
- Yeni bir başarılı pattern ortaya çıkarsa → Bölüm 2'ye ekle
- Kullanıcı yeni bir tercih sinyali verirse → Bölüm 3'e ekle
- Yeni bir meta-prensip yerleşirse → Bölüm 4'e ekle
- Yeni bir tuzak yaşanırsa → Bölüm 6'ya ekle

### Nasıl Güncellenir

- Dosya sonuna yeni "Oturum Ekleri" bölümü aç (tarihli)
- Ana bölümleri (1-6) sadece tam kanıtlı dersler için güncelle
- `.cursor/rules/99-meta-pilot-protocol.mdc`'yi de senkronize et (operasyonel kısım)

### Bu Dokümanı Silme Koşulları

Hiçbir koşulda. Proje tarihçesi — değerli. Kullanışsız hissederse yeni bölüm ekle, ama silme.

---

## 📎 Referans Haritası

```
KIRO2 Proje Kökü
├── DERSLER.md ← BURADASIN
├── KIRO2_SESSION_BRIEFING.md (v13+)
├── NEXT_SESSION_HANDOFF.md (her sohbet sonu güncellenir)
├── AUDIT_PLAN.md, BACKEND_AUDIT.md, FRONTEND_AUDIT.md, INFRA_TEST_AUDIT.md
├── AUTH_*.md (5 dosya)
├── REPO_MAP.md
├── CLAUDE.md, CLAUDE.local.md
│
├── .cursor/
│   ├── rules/
│   │   ├── 00-core.mdc        ← Altın kurallar
│   │   ├── 10-backend.mdc
│   │   ├── 20-frontend.mdc
│   │   ├── 30-migrations.mdc
│   │   ├── 40-algorithms.mdc
│   │   └── 99-meta-pilot-protocol.mdc ← Bu dersin operasyonel kısmı
│   ├── commands/ (19 slash komutu)
│   ├── skills/
│   └── plans/YYYYMMDD_<iş>.md + _RESULT.md
│
└── backend/_pilots/
    ├── README.md
    └── YYYYMMDD_<iş>_state.md
```

---

## 🎭 Son Söz

Bu doküman bir proje değil — bir **çalışma alışkanlığı**. Uygulanması için disiplin gerekli ama disipline girince ritmi kolay.

Kullanıcı (Hüseyin) bu düzeni kurdu; Claude ve Composer 2 onu uygulamakla yükümlü. Bir sonraki Claude sohbeti bu dosyayı okursa, aynı hataları yapmaktan değil, aynı **iyi işleri** tekrarlamaktan çıkar.

En önemli satır, bu dokümanın hiçbir yerinde değil, kullanıcının bir mesajında:

> **"ezbere tahmin hareket etme bizzat görerek tespit et ona göre adım adım düşünerek karar ver"**

Bu cümle dersin tamamı. Gerisi detay.

---

*Oluşturma: 2026-04-20. Bu dosya yaşayan belgedir; her oturumdan sonra gerekiyorsa güncellenir.*
