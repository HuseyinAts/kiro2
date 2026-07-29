# 12 Oturum Gözden Geçirmesi — 21-29 Tem 2026

**Kapsam:** 141 commit, 33 handoff, 21-29 Tem (öncesinde commit boşluğu var, temiz sınır).
**Yöntem:** 15 ajan (7 dilim incelemesi + 7 skeptik çürütme turu + sentez), ardından en ağır
iddiaların elle yeniden ölçümü. Stack inceleme günü yeniden derlendi (29 Tem 13:30 UTC), bu
yüzden canlı ölçüm ilk kez anlamlıydı.

## Methodology

- Her dilim ajanı kendi `git log <aralık>`'ını çekti, canlı uçlara vurdu, DB'yi sorguladı.
- "SAGLAM" ilan edilen her iş ayrı bir skeptik ajana çürütülmek üzere verildi.
- Sentez sonrası **en ağır 6 iddia elle yeniden ölçüldü** (aşağıda ✓ ile işaretli).
- Read-only: hiçbir ajan dosya değiştirmedi, migration/build çalıştırmadı.
- Reproducible: workflow script `.claude/.../workflows/scripts/son-12-oturum-*.js`

## Karne

| Yargı | Sayı |
|---|---|
| SAĞLAM | 27 |
| SAĞLAM denip skeptik turda ÇÜRÜDÜ | 9 |
| EKSİK (iddia doğru, kapsam yanlış) | 39 |
| FANTOM | 6 |
| YENİ RİSK (düzeltme delik açtı) | 12 |
| ÖLÇÜLEMEDİ | 2 |

Sağlamlık **%28**. Daha kritik gösterge: "sağlam" denen 36 işin 9'u (%25) **tek bir skeptik
tura dayanmadı** — yani ilk ölçüm turu da yanılıyor. Bu, tek turlu doğrulamanın yetmediğinin
sayısal kanıtı.

## Elle yeniden ölçülenler (✓ = bu doküman yazarken doğrulandı)

| İddia | Ölçüm | Sonuç |
|---|---|---|
| `user_item_fsrs` tablosu yok | `information_schema` → 0 | ✓ DOĞRU |
| `getMe()` var olmayan yolu çağırıyor | `/api/v1/me` → 404, openapi'de yok; `api-client.ts:182` `live('/me')`; 31 dosya kullanıyor | ✓ DOĞRU |
| `c555a10f4b93` hâlâ zincirde | dosya var, **145 DROP TABLE** | ✓ DOĞRU |
| ES kapıyı tanımıyor | mv 25.127 · aktif 110.858 · ES **64.270 doküman** | ✓ DOĞRU |
| Kayıt formunda Admin kartı | `App.tsx:226` ModernRegisterPage canlıda, `:223` `value:'admin'` | ✓ DOĞRU |
| `send_email` "koşulsuz True" | `email_util.py:38-40` SMTP yokken **False** dönüyor | ✗ **AJAN YANILDI** |
| 13 kapısız uç | kaynakta sayıldı: 15 uçtan 2'sinde kapı, **7 yazma ucu** kapısız | ✓ DÜZELTİLDİ (sayı 13 değil 7) |

## 6 Fantom

1. `1cc5106c9` FSRS stres adaptasyonu — `getattr(ctx,'stress_level',0.0)`, dataclass'ta alan yok, dal asla çalışmaz; sınıfın importer'ı da yok.
2. `1cc5106c9` hybrid_llm_service Redis semantic cache ("aylık binlerce dolar tasarruf") — 10 grep isabetinin 10'u kendi dosyasında, Redis'te 0 anahtar.
3. `1cc5106c9` chat.tsx AI yasal uyarısı — dosyanın importer'ı yok, canlı bundle'da metin yok.
4. `ac4936f8b` FSRS mercy'yi koruyan 3 unit test — servis tamamen mock; metot **hiç yokken de** 65 test yeşildi.
5. `30aa4ac0e` Düello "CANLI PASS" — matchmake 200 ama aynı `Promise.all`'daki `getMe()` 404 → kullanıcı hata ekranı görüyor. O gün bu ekran "rakip yok, doğru davranış" diye okunmuş.
6. `590eafdfc` G3 Parent KPI "shipped" — veli `/parent/dashboard`'a iniyor, orası 656 satır sabit veri; gerçek `VeliPaneliPage` `/veli`'de yetim.

## Tekrar eden desen

| Desen | Kez |
|---|---|
| **Backend/kod düzeldi ama kullanıcıya ulaşmıyor** | **13** |
| Test yeşil ama üretim yolunu koşmuyor | 12 |
| Bekçi eklendi ama mutasyona dayanmıyor / hiç koşmuyor | 9 |
| Bir düzeltme ikinci kod yolunu açık bırakıyor | 6 |
| Sessiz yutma | 5 |
| Tamamlandı işaretlendi ama koşmadı | 4 |

Hepsi tek kök nedene çıkıyor: **kapanış kriteri "kod commit'lendi", "kullanıcı yolu ölçüldü"
değil.** Destekleyen sayılar: 43 kiro ekranının 6'sı mount'lu; kiro istemcisindeki 53 yoldan
28'i backend'de yok.

### Önerilen mekanizma (yeni kural değil, çalışan kapı)

`scripts/route_contract_check.py` → pre-push hook'una.
Mount edilmiş ekranların çağırdığı `live()` yollarını canlı `openapi.json` ile karşılaştırır;
eşleşmeyen varsa exit 1. Mount edilmemiş ekranlar kapsam dışı (bilinen WIP).
Bugün koşsa yakalayacakları: `/me`, `/assignments`, `/subjects`, `/streak`, `/notifications`.
521 testlik frontend kapısı bunları yakalayamıyor — `setup.ts:334` tüm testleri global mock'a
sabitliyor.

**Uyarı:** `if kontrol_edilen == 0: exit 1` koy. `push_secret_guard.py` bu hatayı yaptı ve
geçersiz git aralığında "0 satır tarandı, sır yok" deyip yeşil döndü.

## Bu gözden geçirmeden çıkan ve AYNI GÜN kapatılan işler

| Commit | İş | Doğrulama |
|---|---|---|
| `cfe3e54c4` | Celery rotasız görevler (6 sınıf hiç koşmuyordu, 3.369 mesaj tıkalı) | RED 7 → GREEN 16/16; canlıda worker teslimatı kanıtlandı |
| `25784449d` | Öğretmen/veli kaydolamıyordu (`str(enum)` Py3.11+) | RED 6 → GREEN 11/11; mutasyon 3/3 |
| `d7f80175b` | 7 kapısız yazma ucu + kayıt formundaki ölü Admin kartı | RED 7 → GREEN 21/21 + kapsam bekçisi |

## Açık kalanlar

| # | İş | Büyüklük | Kim |
|---|---|---|---|
| 447 | `GET /api/v1/me` agregasyon ucu (karar verildi, spec hazır) | 0.5-1 gün | Claude |
| — | `user_item_fsrs` restore + `c555a10f4b93` silahsızlandır | 1-2 gün | Claude |
| 433 | ES bypass — reindex / yanıt süzme / tetikleyici kararı | 1 gün | karar + Claude |
| 446 | reward-hacking bekçisi advisory'yi bloke ediyor (2. kusur) | 2-4 saat | Claude |
| 441 | SMTP kimlik bilgisi (3 compose dosyasında da yok) | 1-2 saat | operatör |
| 445 | 73 STUDENT hesap triyajı (istenen rol hiç saklanmamış) | — | operatör |

## İyi olan ne

1. **Skeptik/mutasyon turu** — en değerli 9 bulgu ilk turda değil ikinci turda çıktı. Bir
   bekçi eklerken korumayı söküp kırmızıya döndüğünü GÖR; yoksa bekçi değil dekor.
2. **Kapsamını dürüstçe daraltan commit mesajları** — `05e6cf04a` "2. oyuncu gerektirir →
   yapılmadı", `8a3028c8b` "(stub, TODO'lu)". Bu gözden geçirme onlar sayesinde mümkün oldu.
   Ama aynı iş akışı ertesi gün aynı kanıt sınıfını "CANLI PASS"a terfi ettirdi — standart
   24 saatte kaydı.
3. **Kök nedeni canlı ortamda ölçmek** — `str(enum)` hatası konteynerin kendi Python
   3.11.15'inde çalıştırılarak doğrulandı, tahminle değil.

## İlişkili kurallar

- `.claude/rules/audit-methodology.md` — Severity de bir ölçümdür
- `.claude/rules/verification.md` — tekrarlayan sorun 2. kezde kök neden
- `.claude/rules/testing.md` #31 — status yargısı ≠ servis dışı

---

*Oluşturulma: 29 Tem 2026. Ölçümler o günün canlı sistemine aittir; yeniden kullanmadan önce
tazele — bu dokümanın kendi dersi tam olarak budur.*
