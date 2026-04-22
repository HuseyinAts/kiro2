---
dosya_adi: 30_DERSLER.md
amac: Yaşayan dersler — Claude hataları + doğru pattern'ler + kullanıcı tercihleri + tuzaklar
ne_zaman_oku: Yeni pilot planı yazarken; sapma şüphesinde; Claude yanlış yaptığında düzeltme için
versiyon: v4 (2026-04-22)
guncellendi: 2026-04-22
durum: aktif — yaşayan doküman, her yeni ders eklenir
ilgili_dosyalar: [00_INDEX, 10_BRIEFING, 20_PILOT_PROTOCOL, 40_OPEN_DEBTS]
kaynak: Repo `DERSLER.md` (20 Nisan) + 21-24 Nisan sohbet kazanımları + 22 Nisan Borç #6 Round 2 + Files rewrite oturumu
---

# KIRO2 Dersler ve Çalışma Prensipleri

Bu doküman KIRO2'de Claude Desktop, Composer 2 ve Cursor'un diğer ajanlarıyla
(Agent mode, Background Agent) nasıl çalışıldığının hikayesidir. Operasyonel
kurallar `20_PILOT_PROTOCOL` + `.cursor/rules/*.mdc`'dedir; bu dosya **neden
böyle olması gerektiği**.

## Kısa Tarihçe — 20 Nisan 2026'dan Bu Yana

Hüseyin Cursor Pro aldı, ardından bir Nightly kanalına geçti. 20 Nisan'da Claude
Desktop ile pilot-based workflow kuruldu: Claude plan yazar, Composer 2 uygular,
Hüseyin karar verir ve geri dönüşsüz eylemleri (push, alembic upgrade) yapar.
İlk pilot `diary_api` aktivasyonu, Aşama B çıktı, smoke geçti. Repo'da
`DERSLER.md` dosyası doğdu (bu Files'taki 30_DERSLER'in alt kaynağı).

21 Nisan'da iki paralel iş: (a) `offline_sync_api` pilotu başladı, 4 kod borcu
tespit edildi; (b) autopilot background agent başlatıldı,
`autopilot/student-ready-20260421` dalında 9 commit üretti. Autopilot F1
(ChromaDB altyapı) başlangıcı yaptı.

22 Nisan gündüzü Borç #4 kapandı (`ff06119`, `q.options` ORM uyumsuz).

23 Nisan Borç #2 pilot'u Round 1'de smoke FAIL oldu — **deploy drift (D-12)**.
Composer 2 "PASS" raporu vermişti, kod container'a `docker cp` edilmemişti.
"Migration ≠ Deploy" dersi (Lesson 11) bu olaydan doğdu.

24 Nisan Round 2 PASS oldu (S1-S6 gerçek backend üzerinde). Sonra hijyen 5'li
push yapılırken **yeni bir sapma doğdu** — D-13: Composer 2 "13 commit bekleniyor"
talimatını "13 olmalı" komutu olarak yorumladı, sayıyı tutturmak için autopilot
branch'inden 3 commit cherry-pick'ledi. Borç #6 açıldı. **§1.10 dersi** (sayım
talimatı semantiği) bu olaydan çıktı.

Aynı gün akşam Files 7 dosyalık sistemi **çoklu Cursor aracı** desteğiyle
yeniden tasarlanırken Claude Desktop kendi sohbetinin compaction özetine
dayanarak Files'ı yazmaya başladı — **§1.9 dersi** (Files transkript varsayımı)
bu sohbetin o anında doğdu. Hüseyin "gözden geçir" dedi, hata yakalandı,
Files yeniden yazıldı. Aynı oturumun geç turunda **§1.11 dersi** (plan yazarken
stack literal'lerini ezberden yazma) şekillendi.

22 Nisan akşam oturumu Borç #6 Round 2 planını yazarken üç yapısal hata
tek bir kök nedenden kaynaklandı: plan yazarken **iddia → kanıt arama** akışı
uygulanmadı. §1.11 literal'ler için bunu söylüyordu; **§1.12 dersi** (Plan
Yazımı Pre-Flight) prensibi genelleştirdi. Aynı sohbette git HEAD bizzat
doğrulanırken local'in origin'den ileri olduğu keşfedildi (handoff'un
bilmediği bir commit) — **§1.16 Paralel Aktör Gerçekliği** dersinin canlı
kanıtı. Files rewrite + hijyen push + v4 formalize zincirinde §1.13-§1.18
altı yeni ders birlikte yerleşti.

Bu doküman o yolculuğun meta kaydıdır.

---

## Bölüm 1 — Claude'un Tekrar Etmemesi Gereken 18 Hata

### 1. Audit Raporlarını Okumadan Öneri Üretmek

İlk sohbette 5 alan önerdim. `FRONTEND_AUDIT.md`, `INFRA_TEST_AUDIT.md`,
`AI_PIPELINE_AUDIT.md`, `AUDIT_PLAN.md`, `BACKEND_AUDIT.md`, `REPO_MAP.md`,
`AUTH_CANONICAL_PATH.md` + 4 auth audit dosyasının varlığından habersizdim.

**Ders**: Yeni sohbette öneri üretmeden önce `ls *.md` benzeri tarama + komşu
belgeler (00_INDEX'te listeli) dolaş. Proje kökünde 15+ `.md` dosyası kanıt
kaynağı. Önce oku, sonra konuş.

### 2. Ezberden Benchmark Sayıları Kullanmak

"CursorBench 61.3", "SWE-Bench Multilingual 73.7", "Terminal-Bench 61.7" yazdım.
Kaynak olarak `.cursor/commands/best-of-n.md` gösterdim — ki o dosyayı ben
daha önce bir sohbette yazmıştım. **Döngüsel referans.**

**Ders**: Benchmark sayısı, fiyat, süre gibi somut rakamlar için:
- Kaynak doğrulanabilir mi? (Cursor resmi blog, Anthropic API dokümantasyonu gibi)
- Değilse "bu sayıyı doğrulayamıyorum" de, çıkarma
- Kendi yazdığım dosyayı kaynak diye gösterme

### 3. "EN Parlak Noktası" Abartısı

"Bu Composer 2'nin EN iyi yaptığı iş" dedim. Gerçek: birçok ajan aynı işi
yapabilir. Cursor'da Composer 2 tercih nedeni genelde **maliyet** (Pro havuz)
veya **ergonomi** (multi-file edit coordinasyonu), "EN iyi" değil.

**Ders**: "Yeterli ve ekonomik" ile "en iyi" farklı. Bir iş için "bu Composer 2'ye
uygun" demek yeterli; "en parlak noktası" demek değerlendirmeyi bozar. Cursor
Agent mode, Background Agent, skills/rules/hooks de araç havuzunun parçası —
mono-araç düşüncesi yanlış.

### 4. "Pro Havuzda ≈$0" İddiası

Cursor Pro'da Composer 2 cömert havuzda denilmiş ama sınırsız değil. "Pratik
olarak sınırsız" gibi kaçamak ifade de yanıltıcı — quota gerçek.

**Ders**: "Quota dahil" de, rakam uydurma. Hüseyin bütçe kararı verirken
yanıltıcı olur.

### 5. Git Log Kontrol Etmeden İş Önerme

Briefing 6 Nisan tarihliydi. 20 Nisan'da iş önerirken son 2 haftanın commit'lerine
hiç bakmadım. Belki auth konsolidasyon başlamış, belki XSS işi yapılmış.
Kontrol edilmeden "şunu yapalım" önerisi körlemesine.

**Ders**: Yeni sohbette ilk adımlardan biri: `git log --since='2 weeks ago'
--oneline`. Briefing ile gerçek arası delta var mı? Claude Desktop filesystem
MCP + `.git/refs/heads/master` + `.git/logs/HEAD` okuyarak teyit edebilir.

### 6. 5-10 Alternatif Menü Çıkarma Tuzağı

İlk yanıtımda 5 alan önerdim: "Seç, hangisini istersin?" Bu karar yükünü
Hüseyin'e atar. Benden uzmanın pozisyon alması bekleniyor.

**Ders**: Tek net öneri + gerekçe. "Ama alternatif istersen X, Y" şeklinde
değil. Alternatif ancak Hüseyin "başka seçenek var mı?" derse sunulur.

### 7. Risk Analizi Yokluğu

Plan önerirken "ne ters gidebilir" demedim. Alembic upgrade geri dönüşsüz.
Migration yanlış yazılırsa IRT kolonları gidebilir. Production DB'ye sızarsa
kullanıcı verisi kaybolabilir. Bunların hiçbirinden bahsetmedim ilk turda.

**Ders**: Her pilot planında Risk Matrisi bölümü zorunlu. En az 3-5 risk +
azaltma. Düşük/orta/yüksek sınıflandırmasıyla.

### 8. Composer 2'ye TDD Coverage İşi Önerme

"services/ %35 → %80 coverage" önerdim. Hüseyin daha önce **138 fake test
silmiş** (`assert x is not None or x is None` gibi pattern'ler). Composer 2'ye
"test yaz" demek otomatik fake test fabrikası açmak demek — prompt'ta "YASAK"
yazsam bile LLM unutur.

**Ders**: Test coverage işini Composer 2'ye doğrudan verme. Ya insan tek tek
review eder, ya da önce CI gate'i yaz (`ruff` veya `semgrep` rule ile `is not
None` pattern'ini yasakla), sonra ver. Hüseyin'in geçmiş çalışmalarını sayma;
bir kez fake test silmiş ise bir daha istemiyor.

### 9. Files Dosyalarını Yazarken Transkript Özetine Dayanma (24 Nisan)

Claude Desktop, Files 7 dosyasını yeniden yazarken bir kez **transkript
compaction özetine** dayandı. Özet "Round 2 bekliyor" diyordu, gerçekte RESULT
dosyasına Round 2 PASS zaten append edilmişti. Claude repo'daki RESULT
dosyasını bizzat okumadan 6 Files dosyasını yanlış zemin üzerine yazdı.
Hüseyin "gözden geçir" dedi, hata yakalandı.

İroni: Aynı turda §Bölüm 6'ya "Tuzak 9: Files Dosyaları Güncel Varsayımı"
dersi eklenmişti. Kendi yazdığım dersi ihlal ettim.

**Ders**: Files veya başka dinamik dosya yazmadan önce, referansladığı
canlı kaynakları (RESULT, state.md, git log, autopilot_log) **bizzat aç oku**.
Round N sayısını gör, status matrisini taramadan yazma. Compaction özeti
hızlıdır ama kesin değildir.

### 10. Sayım Talimatının Semantiği (24 Nisan)

Claude plan yazarken "13 commit bekleniyor, değilse DUR + raporla" dedi.
Composer 2 (Cursor Agent mode'da hijyen yaparken) "eksikse tamamla" olarak
yorumladı. Autopilot branch'inden 3 commit cherry-pick'ledi, push'ladı. D-13
sapma örüntüsü bu olaydan doğdu. Ayrıca Claude'un sayımı kendisi de yanlıştı —
"10 commit üretti" demişti, gerçek 9. Çifte sayım hatası: hem sayım ifadesi
ambigü hem sayının kendisi yanlış.

**Ders**: Sayım talimatını **komut + yasaklama** formatında yaz, asla sayı
değil. LLM komut + yasaklama seti görür, "eksik doldurma" niyetini yok sayar.
Ayrıca sayı söylemeden önce **sen de bizzat say**.

### 11. Plan Yazarken Stack Literal'lerini Ezberden Yazmak (22 Nisan)

Plan yazarken literal değerleri (port, kolon adı, DB adı, host, endpoint path,
dosya yolu, container adı, enum değeri, docker komut hedefi) ezberden yazma.
Her literal için 10_BRIEFING'in ilgili bölümünü bizzat aç, kaynağı cümle
içinde göster. Kaynak gösteremediğin değer = ezber, plana koyma, ADIM 0'da
placeholder bırak.

**Canlı kanıt (22 Nisan Borç #6 Round 2 planı)**: Plan'da
`docker exec kiro2_postgres psql -d DB_ADI` placeholder'ı yazıldı. Backend
aslında `host.docker.internal:5434/kiro2` (native Windows PostgreSQL) ile
konuşuyor, `kiro2_postgres` konteyneri farklı bir instance. 10_BRIEFING
§Stack Özeti "port 5434" diyor, okunmadı.

**Ders**: Docker komutu yazarken "bu komut hangi makinede, hangi DB'ye
bağlanıyor" tek cümleyle açıkla — stack topolojisi default değil, her plan
için yeniden teyit. §1.12 bu dersi üç-boyutlu kanıt akışıyla genişletir.

### 12. Plan Yazımı Pre-Flight — Kanıtsız İddia Yasağı (22 Nisan)

Plan yazımı ilk taslak değil; **iddia → kanıt arama** akışıdır. §1.11 literal'ler
için bunu söylüyordu; §1.12 prensibi genelleştirir.

**Üç kural:**

**A. Literal Envanteri**: Plan'da geçecek tüm somut değerleri listele. Her biri
için canonical kaynak göster. Kaynak gösteremediğin her değer = placeholder,
ADIM 0'da teyit.

**B. Sorgu Failure-Mode**: Plan'daki her SQL/grep/endpoint çağrısı için: beklenen
çıktı şekli, boş/dengesiz veri durumu, DUR koşulu. Zihinsel test: "Eğer veri
1000 X + 0 Y ise sorgu ne döner?"

**C. Sınıflandırma Boyutluluğu**: Kategori listesi varsa: hangi boyut, tek
boyutlu mu çok boyutlu mu, karma durum (rol A için i, rol B için iii) plan
formatında gösterilebiliyor mu?

**Uygulama**: Her plan başında `<Pre-Flight>` bloğu. Bloğun yokluğu = §1.12
ihlali, plan Composer 2'ye verilmez.

### 13. Kurallar Canlı — Ders Yazıldı Diye Sorun Çözülmüş Değil (22 Nisan)

Bir ders yazıldığında kapsamı dar kalabilir. Aynı kategoriden ikinci ihlal =
kuralı genişlet, yenisini yaz.

**Canlı kanıt**: §1.11 yazıldı, aynı sohbette iki yapısal hata daha çıktı
(sorgu failure-mode, sınıflandırma boyutu) — §1.12 bu üçünü birleştirmek için
doğdu.

**Ders**: Her ihlal gözden geçirmesinden sonra "bu kural yeterince geniş mi?"
sorusu sor.

### 14. Sinyal ≠ Sonuç (22 Nisan)

Kod içindeki gözlemler (normalize çağrıları, docstring, değişken isimleri,
default değerler) sinyaldir, sonuç değil. Her sinyal bağımsız doğrulama
gerektirir.

**Canlı kanıt**: `require_role` içinde `.lower()` görünce "DB küçük harf"
varsayımı yaptım — yanlış. `.lower()` input hoşgörüsü içindi, DB enum BÜYÜK
HARF saklıyordu (DISTINCT sorgu teyit: STUDENT/TEACHER/ADMIN/PARENT).

**Ders**: Sinyali sonuç yerine kullanmak §1.11-§1.12 ile aynı kökten:
kanıtsız iddia.

### 15. Canonical Görünen ≠ Doğrulanmış (22 Nisan)

Sistem tarihi, Files frontmatter'ı, 10_BRIEFING iddiaları, compaction özeti —
hiçbiri otomatik güvenilir değil. §1.9'un genelleştirilmiş hali.

**Canlı kanıt**: Handoff "v3 base Files'a yüklenmeli" dedi, v3 bulunamadı.
`30_DERSLER.md.txt` Downloads'ta v2.1 çıktı, frontmatter yanıltıcı şekilde
"v2" yazıyordu.

**Ders**: Taze kaynaklar (repo günlük damgalar, canlı runtime sorguları, git
log) etiketli canonical dosyalardan daha güvenilir. "Versiyon: vN" yazısı kanıt
değil — içerikle doğrulanır.

### 16. Paralel Aktör Gerçekliği (22 Nisan)

Repo kapalı kutu değil — başka aktörler (Composer 2, insan, başka Claude
instance'ları, background agent) aynı anda değiştiriyor olabilir.

**Canlı kanıt**: Handoff `b5fab34` beklerken local master `81aa2e2` çıktı —
`chore(alembic): add diary_drift_recovery_20260422` commit'i paralel atılmıştı.

**Ders**: Plan başında "Round 1 zaten yapılmış olabilir", "commit benim
yokluğumda atılmış olabilir" olasılıkları kontrol edilmeli. Her "durumu özetle"
talebinde Prensip 6 aktif.

### 17. Compaction Sonrası Ders Kaybı (22 Nisan)

Uzun sohbetlerde compaction yaşandığında derslerin bir kısmı transkript özetine
dayanarak taşınır — kayıplı taşıma.

**Canlı kanıt**: 24 Nisan sohbetinin ilk bölümündeki §1.10 compaction sonrası
neredeyse hiç konuşulmadı ve sohbetin 2. yarısında 3 kez ihlal edildi.

**Ders**: Compaction sonrası kendi ders özetini çıkar, transkript özetine tek
başına güvenme.

### 18. Ders Listesi Boyut Ayrımı (22 Nisan)

Ders listesi yazarken kategori ayrımı yap: **ders** (soyut kural), **kanıt**
(somut örnek), **gözlem** (pattern tanımı), **rapor** (uygulama özeti).

**Canlı kanıt**: 22 Nisan akşam "bu sohbette alınan dersler" sorusuna 11
maddelik liste yazdım — aslında 4-5 gerçek ders + 6 kanıt/rapor içeriyordu.

**Ders**: "10 madde" ≠ "10 ders". §1.18 bu dokümanın kendi bakım disiplini
olarak da geçerli.

---

## Bölüm 2 — Doğru Yaptıklarımız (Koruma Altına Alınmalı)

### 1. Pilot 3-Dosya Pattern'i

Plan → State → Result. Her biri farklı aşamada farklı yazar, ama dosya türü
sabit. Prior knowledge birikimini sağlar, tekrarlanabilirlik getirir, insan
review noktalarını netleştirir.

**Korunması için**: Her yeni pilotta 3 dosya üret. Eksik bırakma.

### 2. ADIM 0 — Gerçek Durum Tespiti

Kod yazmaya başlamadan önce psql + docker logs + alembic current ile mevcut
durumu kanıtla. Diary pilotunda briefing'le 3 çelişki çıkardı.

**Korunması için**: ADIM 0 her zaman 1 numara. Atlama.

### 3. Aşama A/B/D/E Sınıflandırması

Batch ADIM 0'da 12 router'ı 4 aşamaya ayırdık. Aşama B → pilota uygun, Aşama D
→ altyapı kararı önce, Aşama E → manuel review önce.

### 4. Prior Knowledge Pattern

Composer 2 prompt'una `backend/_pilots/*_state.md` okutmak. Her yeni pilot
prompt'unda Prior Knowledge bölümü zorunlu.

### 5. Hook'suz Amend Tekniği

`git -c core.hooksPath=.git/hooks-empty commit --amend` — Cursor footer'ını
atlatır. Her commit'ten sonra `git log -1 --format='%H%n%s%n---%n%b'` bak.

### 6. "Durma Noktaları" Mekanizması

Her plan'da 5-7 "bana sor, sonra devam et" tetikleyicisi. Composer 2'nin
körlemesine ilerlemesini engeller.

### 7. Artifact'lere Commit Hijyeni

Her pilot commit'i tek mantıksal grup, hook'suz, net mesaj. Seçici `git add
<dosya>`, `git add -A` yasak.

### 8. Round N Smoke Pattern'i (24 Nisan)

RESULT dosyası single-shot değil. FAIL turu silinmez, yeni tur append edilir.
Hem sapma hem düzeltme süreci arşivde kalır.

### 9. Autopilot Branch İzolasyonu (24 Nisan)

Background Agent kendi dalına commit atar; master'a Hüseyin onayı ile merge.
D-13 drift tuzağı: Composer 2 izolasyonu bozdu, cherry-pick'ledi.

**Korunması için**: Hijyen planlarında "başka branch'ten cherry-pick YASAK".

### 10. Cursor Çoklu Araç Havuzu (24 Nisan)

KIRO2'de Cursor bir havuz: Composer 2, Agent mode, Background Agent, Slash
Commands, Skills, Rules, Hooks, MCP, `@Past Chats`. Her aracın pilot akışında
yeri farklı. Her pilot planında "Cursor Araç Seçimi" tablosu zorunlu.

---

## Bölüm 3 — Kullanıcı Tercihleri Kataloğu

### Dil ve Ton

- Türkçe öncelikli. Teknik terimler İngilizce kalır.
- Kısa yazışmalar tolere eder. "ADIM 1", "A", "devam" gibi tek kelime mesajlar
  gelebilir — bağlamdan çıkar.
- Resmi değil ama seviyeli. Emoji az ama stratejik.

### Öz-Eleştiri Beklentisi

- "Gözden geçir" dediğinde: kendi yanıtındaki sorunları açıkça listele.
- Savunmaya geçme. Hata hatadır.

### Karar Mekanizması

- Alternatif menüsünden hoşlanmaz. Tek net öneri + gerekçe ister.
- Kararı kendisi verir. Risk görünür olduğunda bekler.
- "Adım adım düşünerek" ifadesini sıkça kullanır — mantık zinciri bekler.

### Workflow (Kritik)

- Claude Desktop plan yazar, çalıştırmaz.
- Cursor tarafı (Composer 2, Agent mode, Background Agent) uygulayıcı.
- Hüseyin PowerShell'e doğrudan girmiyor — shell komutları Cursor tarafında
  çalışır.
- Git push / alembic upgrade / docker restart — Hüseyin yapar.

### Ezbere Karşı Hassasiyet

- "Bizzat gör, ezberden konuşma" — bu sohbet serisinin baş sloganı.
- Benchmark sayısı, token miktarı, tablo sayısı için kanıt ister.

---

## Bölüm 4 — Meta-Prensipler (Her Pilot için Geçerli)

### Prensip 1: Gerçek Kaynak Canlı Kod + DB

| Soru | Gerçek Kaynak |
|---|---|
| Hangi router'lar disabled? | `backend/routers/loader.py` `DISABLED_ROUTERS` set'i |
| Hangi tablolar var? | postgres MCP `\d+ tablo` |
| Alembic nerede? | `alembic current` + `alembic heads` |
| Git durumu? | `.git/refs/heads/master` + `.git/logs/HEAD` |
| Container durumu? | `docker ps` |

Briefing otoritatif değildir. Çelişki varsa canlı kazanır.

### Prensip 2: Cursor Ajanlarının Yeri Mekanik, İnsanın Yeri Karar

- Pattern'i uygula → Composer 2 veya Agent mode
- Pattern'i tasarla → Claude Desktop
- Pattern arasında seç → Hüseyin
- Geri dönüşsüz eylem → Hüseyin

### Prensip 3: Rollback Yolu Olmayan İş Yasaktır

Backup + rollback bölümü + düşük kapsam commit = geri dönüş güvencesi.

### Prensip 4: Artifact Biriktirmek Değerlidir

Her pilot 3 dosya bırakır. `backend/_pilots/` + `.cursor/plans/` proje
tarihçesini taşır. Cursor ajanları için prior knowledge kaynağı.

### Prensip 5: Dokümantasyon Drift'i Gerçektir

Briefing haftada yenilenmezse günceliğini kaybeder. Her pilot sonunda Files
güncellemesi kontrol et.

### Prensip 6: Repo'yu Bizzat Oku (§1.9 + §1.15 + §1.16 prensip hali)

Her "durumu özetle" talebinde:
1. Files dinamik dosyaları oku
2. Filesystem MCP ile canlı teyit: HEAD SHA, logs/HEAD, RESULT
3. Handoff "X yapılmadı" diyorsa da doğrula — paralel aktör olabilir

### Prensip 7: Süreç Kusuru ≠ Teknik İş Eksikliği (24 Nisan)

Borcun teknik kriteri tam karşılandıysa KAPANDI. Süreç şikayeti ayrı kanalda
(yeni borç + sapma örüntüsü) takip.

### Prensip 8: Plan Yazımı Bir Doğrulama Sürecidir (22 Nisan)

Plan yazımı ilk taslak değil; iddia → kanıt arama akışıdır. Her plan başında
`<Pre-Flight>` bloğu (§1.12). Bloğun yokluğu = plan eksik.

---

## Bölüm 5 — Yeni Sohbetler için Checklist

**Adım A — Bağlam edin**

- [ ] `00_INDEX.md` oku
- [ ] `60_NEXT_HANDOFF.md` ile açılış aksiyonunu gör
- [ ] `50_CHAT_SUMMARY_LATEST.md` ile son sohbeti özümse
- [ ] `40_OPEN_DEBTS.md` ile açık borçları gör
- [ ] Filesystem MCP ile canlı teyit (§1.16 dahil): HEAD SHA, docker ps,
      handoff'taki spesifik kontroller

**Adım B — Pozisyon al**

- [ ] Açık işleri öncelik sırasıyla sun (menü değil)
- [ ] Her biri için süre, risk, öneri + gerekçe

**Adım C — Pilot başlangıcında**

- [ ] Plan dosyası `.cursor/plans/YYYYMMDD_<iş>.md` yaz
- [ ] Plan'da: Pre-Flight (§1.12) + ADIM 0 + Risk Matrix + Durma Noktaları +
      YASAK listesi + Cursor Araç Seçimi tablosu
- [ ] Hüseyin backup aldığını doğrular

**Adım D — Pilot sonunda**

- [ ] state.md yazıldı mı? RESULT yazıldı mı?
- [ ] Commit hook'suz, footer temiz mi?
- [ ] Briefing değişikliği gerekli mi?
- [ ] Files dinamik dosyalar güncellendi mi?

---

## Bölüm 6 — Kaçınılması Gereken Tuzaklar

### Tuzak 1: "Hepsini Temizleyelim" Dürtüsü

12 disabled router'ı bir günde aktifleştirme. Dar kapsam = bitebilir pilot.

### Tuzak 2: "Bunu da Ekleyelim" Kapsam Genişlemesi

Drift çıktığında "genel drift stratejisini de çözelim" demek. Ayrı pilot.

### Tuzak 3: "Composer 2 Anlar" İyimserliği

Prompt ne kadar net olsa da Composer 2 kapsamı genişletebilir. Her komut
onayında ne yaptığını oku. D-8..D-13 sapma örüntülerini bil.

### Tuzak 4: "Staging Yok Önemi Yok" Fantezisi

Dev DB = tek DB. `pg_dump` zorunlu, opsiyonel değil.

### Tuzak 5: "Briefing Söylüyor" Güveni

Briefing hipotez. ADIM 0 kanıt.

### Tuzak 6: "İkinci Opinyonu Atlayayım" Aceleciliği

Hüseyin review etmeli. Onun gözü farklı görür.

### Tuzak 7: Cursor Aracı Monokültürü (24 Nisan)

"Cursor = Composer 2" yanlış. Her pilot planında Cursor Araç Seçimi tablosu.

### Tuzak 8: Sayım Talimatının Semantiği (24 Nisan)

Sayı değil liste. "Liste dışı commit üretme, cherry-pick yasak, eksikse tamamla
yorumu yasak."

### Tuzak 9: Files Dosyaları Güncel Varsayımı (24 Nisan)

Dinamik dosyaları yazarken canlı kaynakları bizzat aç. §1.9 dersi.

### Tuzak 10: Handoff Metni Eksiksiz Varsayımı (22 Nisan)

Handoff "X yapılmadı" diyorsa da repo bizzat teyit et. §1.16 canlı kanıt:
handoff `b5fab34` beklerken local `81aa2e2` çıktı.

---

## Bölüm 7 — Bu Dokümanın Bakımı

Yeni ders → §1.N+1 olarak Bölüm 1'e. Kanıt zorunlu. §1.18 kategori ayrımı
zorunlu (ders / kanıt / gözlem / rapor). Bu doküman hiçbir koşulda silinmez.

---

## Son Söz

Bu doküman bir proje değil — bir **çalışma alışkanlığı**.

> **"ezbere tahmin hareket etme bizzat görerek tespit et ona göre adım adım
> düşünerek karar ver"**

Bu cümle dersin tamamı. Gerisi detay.

---

## Versiyon Notu

- **v4 (2026-04-22)**: §1.11-§1.18 formalize. Bölüm 1 "18 Hata" güncellendi.
  §1.11 stack literal ezber yasağı. §1.12 Pre-Flight 3 kural (patch entegre).
  §1.13 kurallar canlı. §1.14 sinyal≠sonuç. §1.15 canonical≠doğrulanmış.
  §1.16 paralel aktör. §1.17 compaction ders kaybı. §1.18 boyut ayrımı.
  Prensip 8 + Tuzak 10 eklendi. Frontmatter v2→v4 (v3 atlanmış sayılır).

- **v2.1 (2026-04-24)**: §1.10'a "aynı sohbette 3 kez ihlal" canlı kanıt.

- **v2 (2026-04-24)**: Files'a taşıma + §1.9 + §1.10 + Bölüm 2'ye 3 yeni
  pattern + Prensip 6 + Prensip 7 + Tuzak 7/8/9.

- **v1 (2026-04-20)**: İlk kurumlaşma. 8 hata, 7 pattern, 6 tuzak.
