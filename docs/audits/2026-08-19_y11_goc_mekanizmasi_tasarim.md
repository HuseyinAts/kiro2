# Y11 ④ — Göç mekanizması tasarımı (ölçüme dayalı, uygulama BAŞLAMADI)

**Tarih:** 19 Ağustos 2026 · **Oturum:** S232-F
**Durum:** Ön ölçüm TAMAM · kod YAZILMADI · hiçbir veri değiştirilmedi (salt okunur)
**Alet:** `backend/scripts/quality/y11_goc_sema_farki.sql` · `y11_goc_riskleri.sql`

---

## Neden bu belge var

Göç, `kiro2_temp` (pre-split, 78 kolonlu tek tablo) → canlı `kiro2` (4-tablo split)
dönüşümüdür. Bir kopyalama değil. S225'te aynı sınıftaki `toplu_soru_ekle`
**4 seri kusurla %100 düşmüştü** ve uç `HTTP 201 + success:true + "0/3 eklendi"`
dönüyordu. Bu yüzden kod yazılmadan önce kapılar ölçüldü.

---

## Ölçüm 1 — Zorunlu kolonlar (NOT NULL + defaultsuz)

| Hedef tablo | Kolon | NOT NULL | **ZORUNLU** |
|---|---|---|---|
| `question_bank` | 12 | 10 | **4** |
| `question_content` | 19 | 7 | **7** |
| `question_metadata` | 21 | 13 | **12** |
| `question_statistics` | 34 | 24 | **21** |
| **Toplam** | | | **44** |

**44/44'ünün karşılığı kaynakta VAR** (kaynak 78 kolon). Sentez gerekmiyor.

## Ölçüm 2 — "Kolon var" ≠ "Kolon dolu"

Kabul edilen **3.666 KIMYA** satırında 41 zorunlu kolonun NULL sayımı yapıldı.
Kontrol kolu: sorgu 42 satır döndürmeli (1 kontrol + 41 kolon) — döndürdü.

    NULL > 0 olan kolon : 0 / 41
    NULL = 0 olan kolon : 41 / 41

Yani göç saf kolon eşlemesi + dağıtım. Varsayılan üretmeye gerek yok.

---

## Ölçüm 3 — Dört risk (S225'in düşürdüğü sınıflar)

| # | Risk | Ölçüm | Durum |
|---|---|---|---|
| **R1** | `difficulty_level` enum casing | Kaynak `VERY_EASY/EASY/MEDIUM/HARD/VERY_HARD` · canlı enum **birebir aynı** | ✅ temiz |
| **R2** | `primary_topic_id` FK | Kaynakta **17** konu · canlıda **12** · **ortüşme 0** | 🔴 **ENGEL** |
| **R3** | `soru_hash` çarpışma | 4.419 satır / 4.419 distinct / 0 NULL · canlıyla kesişim **0** | ✅ temiz |
| **R4** | `id` çarpışma | Kaynak **4.419/4.419 UUIDv5** · canlı tamamı **v4** | ✅ temiz |

⚠️ **R1 bir sürpriz:** S225'in kusuru `'medium'` (küçük harf) idi. Burada kaynak
zaten büyük harf. Ama bu **KIMYA için ölçüldü** — diğer derslerde tekrar ölçülmeli.

### R2 çözülebilir — kaynakta konu tablosu VAR

    kiro2_temp.topic_hierarchy : 141 satir
    kolon kumeleri IKI TARAFTA DA AYNI (18 kolon, yalniz sira farkli)
    KIMYA'nin 17 konusunun 17'si de kaynakta TANIMLI

Kaynak konular gerçek granülerlik taşıyor — canlının tek `Genel` konusuna karşı:

| kod | ad | soru |
|---|---|---|
| `KIM.DEN` | Kimyasal Denge | 1.361 |
| `KIM.ASI` | Asitler ve Bazlar | 507 |
| `KIM.ORG` | Organik Kimya | 416 |
| `TYT-KIM-02` | Periyodik | 391 |
| `TYT-KIM-01` | Atom Yapısı | 304 |
| `TYT-KIM-04` | Reaksiyonlar | 304 |
| … | (+11 konu) | |

⚠️ 3'ü **ders etiketi yanlış** olan sorulara ait (`FIZ` 12, `MAT.TRV` 1, `FEN` 1) —
göçte ayrı ele alınmalı, konuyu kopyalamak yeterli değil.

---

## Tasarım — sıralı, geri alınabilir

    ADIM 0  yedek : canli 4 tabloya `_y11_oncesi` son ekli backup tablolari
    ADIM 1  konu  : eksik topic_hierarchy satirlarini kaynaktan kopyala
                    (SEMA AYNI -> duz INSERT; FK ebeveyni oldugu icin ONCE)
                    ⚠️ parent_id zinciri: level>1 konularin ebeveyni de gelmeli
    ADIM 2  pilot : 50 KABUL satiri, 4 tabloya dagit, DOGRULA, GERI AL
    ADIM 3  tam   : 3.666 KIMYA KABUL satiri, parti parti (1000'lik)
    ADIM 4  kapi  : mv_safe_for_beta REFRESH + Y12 bekcisi kosulur

### Kapılar (her adımda, atlanamaz)
- `git status` ile geri alınabilirlik doğrulanır
- Her adımda **satır sayısı invaryantı**: kaynak N → hedef 4×N (yetim 0)
- ADIM 2 sonrası **5/5 nokta-kontrol**: 4 tablodan JOIN'le okunan soru,
  kaynaktakiyle birebir aynı mı
- ADIM 4 sonrası **Y12 bekçisi** koşulur ve `xfail` işaretleri kaldırılır
  (içerik düzeldiği için XPASS vermeliler — mekanizma S232'de mutasyonla çivilendi)

---

## 🔴 Tasarımı DEĞİŞTİREN ölçüm — insan tek karar mercii OLMAYACAK

S232'de uyuşmazlık çözücü kalibre edilirken **kontrol kolu olarak Claude'un elle
verdiği 24 yargı** kullanıldı ve **kontrol kolu düştü**: mekanizma 5 kalemde
Claude'u düzeltti (hepsinde mekanizma haklıydı). Hata deseni tekti — *çözmeden
yargılamak*.

Bu yüzden göç kapısında "insan onayı" **tek başına güvence sayılmayacak**.
Kurulacak yapı: **iki bağımsız çerçeve + insan tahkimi**. İnsan, mekanizmanın
üstünde değil, mekanizmayla birlikte karar verir.

---

## ③ bu adıma gömülü

- **Tekilleştirme:** 153 gerçek mükerrer satır (gövde+şık aynı, anahtar çelişkisi 0).
  ⚠️ Önceki "669 mükerrer" ölçümü YANLIŞTI — yalnız gövdeye bakıyordu, 516 meşru
  soru silinecekti. Bkz. `L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir`.
- **Anahtar düzeltme:** ~%1,4 soru "yargıç doğru, kitap anahtarı bozuk"
  (uyuşmazlıkların %87,5'i). `correct_answer` **yerinde değiştirilmez**; göç
  sırasında yeni satıra gerekçesiyle yazılır, kaynak dokunulmadan kalır.

---

## Bu belgenin sınırı

Ölçümler **yalnız KIMYA** için yapıldı (4.419 soru). MATEMATIK/GEOMETRI/FIZIK
göçünden önce R1-R4 **her ders için tekrar ölçülmeli** — özellikle R1 (enum
casing) ve R2 (konu sayısı), çünkü ikisi de ders-bağımlı.

Kod **yazılmadı**. Bu belge ADIM 0-4'ün girdisidir, çıktısı değil.

---

## ADIM 0 — YAPILDI ve DOĞRULANDI (19 Ağu 2026)

`kiro2_app`'in `public` şemasında **CREATE TABLE yetkisi YOK**
(`permission denied for schema public`). `.claude/rules/database.md` zaten
"postgres for migrations/DDL" diyormuş. Tablo-yedek yerine **dosya-yedek** seçildi —
`pg_dump` yalnız okur, DDL istemez, canlıyı şişirmez, deponun mevcut yolu.

    backups/kiro2_20260819_y11_oncesi.dump   6,6 MB

**Doğrulandı** (yedek bir iddiadır, dump'ın içi sayıldı):

| tablo | dump içindeki satır | canlı |
|---|---|---|
| question_bank | 36.967 | 36.967 |
| question_content | 36.967 | 36.967 |
| question_metadata | 36.967 | 36.967 |
| question_statistics | 36.967 | 36.967 |
| topic_hierarchy | 12 | 12 |
| **toplam** | **147.880** | ✅ |

---

## ADIM 1 — TAM ÖLÇÜLDÜ, kod YAZILMADI

### Yetki
`topic_hierarchy`'ye **INSERT yetkisi VAR**. Test işlemi yetki reddiyle değil,
`osym_relevance` NOT NULL kısıtıyla düştü → alt küme değil **tam kolon** INSERT gerekli.
ROLLBACK doğrulandı (0 test satırı, 12 konu).

### Zincir
17 taban konu + **1 ebeveyn** (`MAT.TRV` → `MAT`) = **18 konu**.
En derin zincir **1 adım**, **yetim ebeveyn referansı 0**. INSERT sırası = `level`.

### Kaynak bütünlüğü
Canlının **9 zorunlu kolonu** (`id, code, name_tr, level, is_active, osym_relevance,
osym_frequency, total_questions, average_difficulty`) kaynakta 18/18 satırda **DOLU**
(NULL 0/9).

### 🔴 KOD ÇAKIŞMASI — ADIM 1 "kopyala" değil "kopyala + EŞLE"
`code` **UNIQUE** (`topic_hierarchy_code_key`). Kaynaktaki 18 kodun **4'ü** canlıda var:

| kod | canlı id | etkilenen KIMYA sorusu |
|---|---|---|
| `KIM` | `72e79276-4795-424c-a262-0edf9a77a23f` | **852** |
| `FIZ` | `c6c72669-267e-47ce-a3d2-8392de050bc7` | 12 |
| `GEN` | `9928457b-b653-46d4-8bc1-a0937b1d9836` | 1 |
| `MAT` | `259066bd-71fb-420e-85e3-a4e3ad9811fe` | 0 (yalnız `MAT.TRV`'nin ebeveyni) |

→ **14 konu kopyalanır · 4 konu EŞLENİR · 865 sorunun `primary_topic_id`'si
göç sırasında YENİDEN HARİTALANIR.**

⚠️ Bu kopyalanmış olsaydı UNIQUE kısıtı **kısmi INSERT sonrası** düşerdi — gürültülü
ama yarım durumda. Eşleme tablosu ADIM 2'nin girdisidir.

### Kalan
ADIM 2 (50 satırlık pilot + geri alma) ve sonrası **başlamadı**. İlk kalıcı veri
yazımı orada; taze bağlamda yapılmalı.
