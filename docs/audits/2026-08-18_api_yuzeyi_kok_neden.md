# API Yüzeyi Kök-Neden Raporu — "326 vs 1.224" Çelişkisi

**Tarih:** 18 Ağustos 2026 · **Oturum:** S229 · **Dal:** `feature/self-evolution-optimization`
**Tetikleyici:** Aynı gün yayınlanan durum tespitinde "API yüzeyinin ~%73'ü kayıp" iddiası
**Sonuç:** İddia **ÇÜRÜTÜLDÜ**. Kod sağlam; sorun **bayat container imajı**.

---

## 1. Yönetici Özeti

| # | Bulgu | Ölçüm |
|---|---|---|
| 1 | **Kod tabanında kayıp YOK.** `ROUTER_MAPPING`'in 150 girdisinin 150'si diskte var, 150'si sorunsuz import ediliyor. | `MAPPING=150 DOSYA_YOK=0 IMPORT_OK=150 HATA=0 TOPLAM_ROUTE=1206` |
| 2 | **MEMORY'nin 1.224 rakamı doğruydu.** Bugün 1.206 route — küçük, açıklanabilir sapma. | aynı ölçüm |
| 3 | **Canlı yüzeyin 326 olmasının sebebi bayat imaj.** `kiro2-backend` imajı **2026-08-06** tarihli; ~106 modül dosyası imajda **fiziksel olarak yok**. | `docker inspect` + dosya varlık testi |
| 4 | **YENİ BULGU: host ↔ container framework uçurumu.** Host `fastapi 0.103.2 / starlette 0.27.0`, container `fastapi 0.141.1 / starlette 1.4.1`. | `python -c "import fastapi,starlette"` her iki tarafta |
| 5 | **Test paketinin kök nedeni de sürüm.** Host `starlette 0.27 + httpx 0.28.1` → `TypeError: Client.__init__() got an unexpected keyword argument 'app'`. | birebir üretildi |

**Karar:** Sorun **(a) bayat/eksik imaj** + **(b) sürüm matrisi kaosu**. **Eksik kod DEĞİL.**
"Yanlış ölçülmüş rakam" payı: %100 — benim raporladığım teşhis baştan sona hatalıydı.

---

## 2. Merkezî Ölçüm (belirleyici kanıt)

`backend/` dizininden, `sys.path`'e `backend` eklenmiş halde, `ROUTER_MAPPING`'in her girdisi
tek tek denendi. `BaseException` yakalandı (yani `SystemExit` bile kaçmaz):

```
MAPPING=150 DISABLED=0
{'DOSYA_YOK': 0, 'IMPORT_OK_ROUTER': 150, 'IMPORT_OK_ROUTERSIZ': 0, 'HATA': 0}
TOPLAM_ROUTE=1206
```

Yani: **dosyası olmayan modül 0**, **import hatası 0**, **router'ı olmayan modül 0**.

Bu ölçüm bağımsız olarak iki kez üretildi: bir Gemini oturumu (AST 1.204 + runtime 1.206)
ve bu oturum (runtime 1.206). **İki bağımsız araç aynı sayıyı verdi.**

---

## 3. Benim Hatamın Anatomisi (3 ayrı alet arızası, hepsi aynı sınıf)

Yayınlanan yanlış iddia: *"106 modül git geçmişinde hiç var olmamış, host'ta da yok,
yüzeyin %73'ü kayıp."* Üç ölçüm de geçersizdi ve **üçü de aynı kök nedene** dayanıyor:
**kabuk `cwd`'si ile yol/isim-alanı uyumsuzluğu.**

| Ölçüm | Ne yaptım | Neden geçersiz | Doğrusu |
|---|---|---|---|
| Git arkeolojisi | `git log --diff-filter=A -- "backend/api/x.py"` | cwd zaten `backend/` idi → pathspec `backend/backend/api/...`'ya çözüldü → **boş sonuç** "hiç var olmamış" sanıldı | `-- "api/x.py"` → **2 eklenme kaydı**, 0 silinme |
| Dosya varlığı | `ls backend/api/x.py` | Aynı cwd hatası → "host'ta da yok" | `[ -f /c/Users/husey/kiro2/backend/api/x.py ]` → **VAR** |
| Probe çıktısı | Python `open("/tmp/out.txt")`, bash `cat /tmp/out.txt` | **bash `/tmp` = MSYS temp, Python `/tmp` = `C:\tmp`** — iki ayrı isim alanı. Dosya yazıldı, ben yanlış yere baktım → "sonuç yok" | `cat /c/tmp/out.txt` → **sonuçlar orada** |

**Ağırlaştırıcı sebep:** bu üç dersin **hepsi bu depoda zaten yazılıydı**
(`L-s229-cd-kalici-sifir-collected` ve `verification.md`'deki `/tmp` iki-isim-alanı dersi).
Dersi aynı oturumda yazıp aynı oturumda ihlal ettim. Ders yazmak, dersi uygulamak değildir.

**Yapısal sonuç:** "0 bulundu / 0 collected / boş döndü" bir **bulgu değil**, alet arızası
adayıdır. Kontrol kolu tek komut: `pwd` + bilinen-var bir örneğin aynı yöntemle bulunması.

---

## 4. Gerçek Kök Neden: Bayat ve Eksik Container İmajı

```
docker inspect kiro2-backend  →  Container: 2026-08-06T00:12:01Z
                                 İmaj:      2026-08-06T00:09:33Z
Son 4 günde depoya giren commit sayısı: 91
```

İmaj **6 Ağustos** tarihli. Sonrasındaki hiçbir değişiklik container'da yok.

### 4.1 Eksik dosya mı, sürüm uyumsuzluğu mu? (ayırt edici test)

Container içinde, önce dosya varlığı sonra gerçek import:

| Modül | `/app/...` dosya | Container'da import |
|---|---|---|
| `api.rag` | **VAR** | **IMPORT_OK** |
| `api.agents` | **VAR** | **IMPORT_OK** |
| `api.analytics` | YOK | `ModuleNotFoundError` |
| `api.diary_api` | YOK | `ModuleNotFoundError` |
| `api.duel_api` | YOK | `ModuleNotFoundError` |
| `api.curator` | YOK | `ModuleNotFoundError` |
| `api.kvkk_consent_api` | YOK | `ModuleNotFoundError` |

**Sonuç: sebep saf dosya eksikliği.** Dosyası olan modüller container'da da yükleniyor.

### 4.2 Gemini'nin bir maddesi de çürüdü

Gemini raporu, container'daki hataları *"`langchain_community`/ChromaDB/PyTorch gibi ağır
opsiyonel bağımlılıklar"*'a bağlıyordu ve örnek olarak **`api/rag.py`**'yi gösteriyordu.
Ölçüm bunu desteklemiyor: **`api.rag` container'da sorunsuz import ediliyor.**
Yani ağır-bağımlılık hipotezi bu vakada geçerli değil; tek mekanizma eksik dosya.

*(Bu, çift yönlü doğrulamanın değeri: Gemini benim iki büyük hatamı yakaladı, ben onun bir
açıklama hatasını yakaladım. Hiçbir raporu ölçmeden kabul etmemek işe yaradı.)*

### 4.3 Mekanizmanın neden sessiz olduğu

`routers/loader.py:292-299` her modülü `try/except ImportError` ile sarıyor ve hatayı
**yalnızca `logger.warning`** ile bildiriyor. Yükleme devam ediyor, uygulama sağlıklı
başlıyor, `/health` 200 dönüyor. Yani **106 eksik router hiçbir kırmızı sinyal üretmiyor** —
sadece başlangıç logunda 106 uyarı satırı olarak akıyor ve kimse okumuyor.

---

## 5. YENİ BULGU: Host ↔ Container Sürüm Uçurumu

| | fastapi | starlette | httpx |
|---|---|---|---|
| **Host (geliştirme + testler)** | 0.103.2 | **0.27.0** | 0.28.1 |
| **Container (çalışan servis)** | **0.141.1** | **1.4.1** | 0.28.1 |

Bu, tek bir bayatlık değil **iki yönlü sapma**: container ileride (fastapi 0.141 / starlette
1.4 — major atlama), host geride. İki sonucu var:

1. **Test ↔ üretim eşdeğerliği yok.** Host'ta geçen bir test, container'da farklı bir
   framework sürümüyle koşan kodu doğrulamıyor. Bu deponun "yeşil test doğruluk kanıtı
   değil" dersinin altyapı düzeyindeki hali.
2. **Rebuild riski.** İmajı yeniden kurmak 106 router'ı geri getirir ama kodu
   **starlette 1.4 / fastapi 0.141** altında çalıştırır. Kod 0.103 döneminde yazıldı;
   uyumsuzluk çıkması beklenmelidir. **Rebuild'i ölçümsüz yapma.**

---

## 6. Test Paketi Kök Nedeni (ayrı ama aynı aileden)

97 test hatasının tamamı `ERROR at setup of` idi (bu oturumda 97/97 ölçüldü). Kök neden:

```
starlette 0.27.0 → TestClient.__init__ içinde super().__init__(app=self.app) çağırıyor
httpx     0.28.1 → Client.__init__(app=...) parametresini KALDIRDI
```

Birebir üretildi:

```
>>> TestClient(FastAPI())
TypeError: Client.__init__() got an unexpected keyword argument 'app'
```

**Fix seçenekleri:** (a) `httpx<0.28` sabitle, (b) `starlette`/`fastapi` yükselt
(dikkat: container zaten 1.4.1'de — bu seçenek iki tarafı da hizalar), (c) `conftest.py`'ye
`ASGITransport` shim'i. **(b) en tutarlı yol** çünkü sürüm uçurumunu da kapatır.

---

## 7. Risk Tablosu (bayat container'ın sessiz sonuçları)

| Risk | Mekanizma | Belirti |
|---|---|---|
| **Sessiz eksik özellik** | 106 router mount edilmiyor | Frontend 404; kullanıcı "çalışmıyor" der, log temiz |
| **Yanlış "hazır" değerlendirmesi** | Yüzey ölçümü canlıdan alınırsa 326 görünür | Yol haritası eksik kapsam üzerine kurulur |
| **Migration ↔ kod tutarsızlığı** | DB'ye `0002` uygulandı, container o migration dosyasını bilmiyor | Alembic durumu container'dan sorgulanırsa yanıltıcı |
| **Elle `docker cp` yamaları** | Bu oturumda 3 dosya elle kopyalandı | Rebuild bu yamaları **siler**; kalıcı olduğu sanılıyorsa regresyon |
| **Test-üretim ayrışması** | Farklı framework sürümleri | "Host'ta geçti" üretim garantisi değil |

---

## 8. Aksiyon Planı (her adımda doğrulanabilir kabul kriteri)

| # | Adım | Kabul kriteri (ÖLÇÜM) |
|---|---|---|
| **A1** | Sürüm matrisini sabitle: `requirements*.txt` içinde fastapi/starlette/httpx üçlüsünü pin'le. Host ve container **aynı** üçlüyü kursun. | Her iki tarafta `python -c "import fastapi,starlette,httpx; print(...)"` **birebir aynı** çıktı |
| **A2** | `conftest.py` TestClient uyumu (A1 ile birlikte çözülebilir) | `pytest tests/unit/test_admin_api.py` → `ERROR at setup` sayısı **0** (şu an 97) |
| **A3** | `docker compose build backend && up -d --no-deps backend` | Rebuild ÖNCESİ/SONRASI `curl /openapi.json` yol sayısı: **326 → ~1.206**. Başlangıç logunda `Failed to import` sayısı: **106 → 0** |
| **A4** | Rebuild sonrası duman testi | Golden Flow paketi + bu oturumun 12 entegrasyon testi: rebuild sonrası **hâlâ yeşil** |
| **A5** | `docker cp` yamalarının kalıcılığı | Rebuild sonrası container'da `grep -c "question_content qc ON qc.id = qb.id" /app/api/admin.py` → **≥1** (yoksa yama kayboldu, commit'ten gelmiyor demektir) |
| **A6** | Loader'ın sessizliğini bitir | `Failed to import` sayısı bir eşiği aşarsa **başlangıçta hata ver** (veya `/health` degraded dönsün). Bekçi testi: kasıtlı bozuk mapping → uygulama uyarı değil **hata** üretmeli |
| **A7** | Frontend 404 envanteri | Rebuild sonrası frontend fetch yolları ile `/openapi.json` kesişimi; eşleşmeyen kritik yol sayısı raporlanır |

**Sıra kritik:** A1 → A2 → A3. A3'ü A1'den önce yapmak sürüm uçurumunu üretime taşır.

---

## 9. Ölçülemeyenler (dürüst boşluk listesi)

- **1.206 route rebuild sonrası gerçekten mount olacak mı** — ölçülmedi. Starlette 1.4
  altında bazı router'lar kırılabilir. A3'ün kabul kriteri bunu ölçmek için var.
- **106 eksik dosyanın TAM listesi** — bu raporda 7 modül örneklendi; tam envanter paralel
  araştırmada üretiliyor (bu rapor onunla güncellenecek).
- **İmajın neden eksik dosyalarla kurulduğu** — hipotez: 5-6 Ağu içerik-kaybı penceresinde
  build alındı (MEMORY: 14-15 Ağu'da "22 dosya restore"). **Doğrulanmadı.**
- **Frontend'in kaç çağrısının şu an 404 aldığı** — sayısal olarak ölçülmedi.
- **MEMORY'deki 1.224 ile bugünkü 1.206 arasındaki 18 route farkı** — açıklanmadı
  (muhtemelen normal kod değişimi, ama ölçülmedi).

---

## 10. Bu Vakadan Çıkan Yöntem Dersi

Bu raporun konusu bir kod kusuru değil, **bir ölçüm zinciri kusuru**:

1. Canlı sistemden alınan sayı (326) doğruydu.
2. Ondan çıkarılan **teşhis** (kod kayboldu) yanlıştı.
3. Yanlış teşhis, üç ayrı alet arızasının **aynı yöne** işaret etmesiyle inandırıcı oldu.
4. Üç arıza da **tek kök nedene** dayanıyordu: yol/isim-alanı uyumsuzluğu.
5. Hatayı **başka bir araç** (Gemini) yakaladı — çünkü farklı bir çalışma dizini ve farklı
   bir yöntem (AST) kullanıyordu.

**Kural:** bir sistem iddiası ("X kayboldu") üretirken, o iddiayı **iki farklı yöntemle**
ve tercihen **iki farklı araçla** ölç. Aynı aracın iki koşumu aynı arızayı taşır.

---

*Kaynak ölçümler bu oturumun transkriptinde; her tablo satırı bir komut çıktısına dayanır.
Paralel araştırma (`wf_2d726569-ebd`) tamamlandığında bu rapor tam envanter + frontend etki
analizi ile güncellenecektir.*

---

# EK: PLANIN UYGULANMASI (aynı gün, S229 devamı)

Yukarıdaki A1–A5 planı **uygulandı**. Aşağıdaki her satır canlı ölçümdür.

## A1 — Sürüm matrisi sabitlendi ✅

Plan "hangi yöne hizalayalım" diye açık uçluydu; **ölçüm kararı verdi**: repo zaten
cevabı yazmıştı.

```
requirements.txt : fastapi==0.141.1  starlette==1.4.1  httpx==0.28.1
CONTAINER        : 0.141.1 / 1.4.1 / 0.28.1   ← requirements ile UYUMLU
HOST (önce)      : 0.103.2 / 0.27.0 / 0.28.1  ← kendi requirements'ına AYKIRI
```

Yani bu bir tasarım kararı değil, **sapma onarımı**ydı. Host yükseltildi.

**İkinci kusur (planda yoktu, ölçümde çıktı):** `Dockerfile.minimal`,
`requirements-minimal.txt` kuruyor ve o dosya `fastapi>=0.104.1` diyordu,
**starlette pin'i hiç yoktu** → her build farklı sürüm çekebilirdi. Üçü de kesin
sürüme pin'lendi (commit `1dd12579d`).

| Kabul kriteri | Sonuç |
|---|---|
| host == container sürümleri | `HOST 0.141.1 1.4.1 0.28.1` / `CONT 0.141.1 1.4.1 0.28.1` ✅ |
| regresyon (test_admin_api.py) | 46 passed → **46 passed** ✅ |
| TestClient probe | `TypeError` → **SORUN YOK** (kontrol kolu ile: önce de koşuldu, düştü) |

**Açık kalan:** `schemathesis 3.36.3` metadata'sı `starlette<1` istiyor, artık ihlal.
Sözleşme testi bugün 10/10 geçiyor — yani **ihlal edilmiş kısıt altında ölçülen bir
başarı**, garanti değil. Ayrı iş. `requirements-test.txt` de bu matrise pin'li değil.

## A2 — Kod yazılmadı, gerek kalmadı ✅

Plan `conftest.py:1186`'ya shim yazmayı öngörüyordu. **A1'den sonra ölçüldü:**

| 4 dosyalık set | A1 öncesi | A1 sonrası |
|---|---|---|
| error | **97** | **0** ✅ |
| passed | 1 | **73** |

`conftest.py` semptomdu; kök neden sürüm sapmasıydı. Shim yazmak, ölçülmemiş bir
soruna kod eklemek olurdu — yazılmadı.

## A3 — Rebuild: yüzey geri geldi ✅

```
Eski imaj: b7b4b866d1fa (2026-08-06)   ← geri dönüş için, artık dangling
Yeni imaj: 2a445de6397d (2026-08-18)   ← build 10 dk 02 sn, exit 0
```

| Kabul kriteri | ÖNCE | SONRA |
|---|---|---|
| `Failed to import` (benzersiz) | **111** | **0** ✅ |
| Yüklenen router | 40 | **150** ✅ |
| openapi **yol** | 326 | **1119** |
| openapi **operasyon** | 349 | **1184** |
| şema | 212 | **793** |
| başlangıçta ERROR/CRITICAL | — | **0** |

Nokta kontrol: `analytics · diary_api · duel_api · curator · kvkk_consent_api · org_api`
→ rebuild öncesi **6/6 YOK**, sonrası **6/6 VAR** ve uçları canlı (duel 12 yol, diary 40,
curator 4, kvkk 17, org 9, analytics 28).

**Birim uyarısı korundu:** 1.206 sayısı *route* (router.routes toplamı); openapi *yol*
1119. İkisi aynı şey değil — aynı yolun birden çok metodu tek yol sayılır, WS/mount
route'ları openapi'ye girmez. "1206 yol bekle" kriteri kurulsaydı doğru rebuild'de bile
"başarısız" görünürdü.

## A5 riski ÇÜRÜDÜ (Gemini haklıydı)

Bu raporun ilk sürümü *"rebuild `docker cp` yamalarını siler"* diyordu. **Yanlış.**
3 dosyanın 3'ü de commit'liydi, rebuild onları git'ten aldı — imajda doğrulandı:
`admin.py` JOIN **3**, `question_bank.py` `default=True, server_default` **1**,
alembic `0002` migration **1**. Elle kopyalamaya gerek kalmadı.

## YENİ BULGU — açılış süresi 3 katına çıktı

40 router yerine 150 yüklendiği için uygulama açılışı **~25 sn → ~60-85 sn**.
Compose healthcheck `start_period: 60s` artık **sınırda**; ilk `curl` boş yanıt (000) döndü.

⚠️ **CLAUDE.md'deki kanonik deploy döngüsü `Start-Sleep 22` diyor — bu imaj için
YETERSİZ.** Deploy script'leri ve o kural güncellenmeli, aksi halde her deploy'da
"backend çöktü" yanlış teşhisi üretilir.

## Kalan (bu ek yazılırken ölçülüyordu)

- **A4** rebuild sonrası regresyon (12 entegrasyon testi + Golden Flow + canlı uç kontrolü)
- **A5** IRT cold-start ön ölçümü: `irt_difficulty`'yi CAT/ZPD/BKT/sınav motoru gerçekten
  okuyor mu? (FSRS için ölçüldü: **hayır** — 0 referans)
