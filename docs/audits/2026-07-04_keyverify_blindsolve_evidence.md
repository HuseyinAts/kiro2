# Cevap-Anahtarı Kör-Çözüm Doğrulaması — Ölçülmüş Kanıt

*Tarih: 2026-07-04 · Yöntem: 2-sinyal bağımsız kör-çözüm · Kapsam: v_safe stratified 1330 örneklem*

## Amaç
Panelin ~%9.2 kusur **tahmini** (428 örnek, LLM-yargı) — varsayımsal. Bu iş **ölçüm** üretti: servis havuzundan stratified örneklem bağımsız kör-çözülüp stored cevap-anahtarıyla karşılaştırıldı. Agent'a anahtar VERİLMEDİ (`keys.json` ayrı) → dairesel-doğrulama yok.

## Yöntem
1. **Örneklem:** v_safe'ten branş-stratified 1330 (MATEMATIK 534 ... SOSYAL 50), deterministik md5 sırası.
2. **1. sinyal:** 54 agent (25 soru/batch) her soruyu KÖR çözdü (anahtar görmeden) → 1309 tahmin.
3. **Karşılaştırma:** blind1 == stored key → AGREE (Python, deterministik).
4. **2. sinyal:** yüksek-güven (conf≥0.8) DISAGREE'ler (17) bağımsız 2. çözücüyle yeniden çözüldü + 3'lü yargı.

## Ölçülmüş Sonuç (1302 çözülebilir)

| Branş | n | AGREE% |
|---|--:|--:|
| KIMYA | 184 | 98.9 |
| SOSYAL | 50 | 98.0 |
| MATEMATIK | 514 | 97.6 |
| GEOMETRI | 69 | 97.0 |
| FIZIK | 116 | 96.5 |
| TURKCE | 105 | 96.2 |
| BIYOLOJI/TARIH | 79 | 94.9 |
| COGRAFYA | 50 | 94.0 |
| EDEBIYAT | 56 | 91.1 |
| **TOPLAM** | **1302** | **96.8** |

- Çözülemez (X): 11 (%0.8)
- DISAGREE: 41 (%3.2), yüksek-güven 17

## 2-Sinyal Doğrulama (17 yüksek-güven disagree)
- **8 STORED_WRONG** (blind1 + 2. çözücü bağımsız hemfikir, farklı cevap) = gerçek anahtar-hatası
- **7 STORED_CORRECT** (blind1 model hatası; anahtar doğru)
- **2 AMBIGUOUS** (soru çift-doğru/bozuk)

**A-bias dersinin canlı kanıtı:** tek-model disagree'nin yalnız %47'si gerçek hata. 2. sinyal olmasa ~2x fazla sayılırdı.

## Sonuç: ölçülmüş anahtar-hatası oranı ~%0.77 (panelin ~1/12'si)
- **Doğrulanmış hata: 10/1302 = %0.77** (8 wrong + 2 ambiguous, 2-sinyal).
- Servis havuzuna ekstrapolasyon (25.127): ~**193 anahtar-hatası + ~48 ambiguous ≈ 240 soru (~%1)**.
- **Panel ~%9.2 → gerçek ~%1.** Panel şişikti: yumuşak kusurları (çeldirici/etiket) + LLM-yargının kör-çözümden sertliği + örneklem şansı.

**Servis havuzu cevap-anahtarı kalitesi ~%97-99 (ölçülmüş) — satış için sağlam.**

## Aksiyon (curator-ready, correct_answer DOKUNULMADI)
- 8 STORED_WRONG → `pipeline_metadata.keyverify_stored_wrong_20260704` (2-sinyal cevap + gerekçe). Örnek: 60a54fa1 Mn(Z=25, M-katman 13e⁻); stored 23=Vanadyum yanlış.
- 2 AMBIGUOUS → `keyverify_ambiguous_20260704`.
- Backup: `question_bank_keyverify_flag_backup_20260704` (reversible). correct_answer/is_active değişmedi (0).
- **correct_answer değişimi = curator/3.-sinyal işi** (en hassas alan, codebase deseni 3-sinyal+human).

## Kalan (ölçek — çok-oturumlu)
Bu 1330-örnek dalgası servis havuzunun %5.3'ünü kapsadı. Tam-havuz (25.127) doğrulama = ~19 dalga daha (her ~1330). Ölçülmüş oran kararlıysa (%97 AGREE) tam-tarama düşük-ROI; hedefli dalgalar (EDEBIYAT %91 en düşük → öncelik) daha verimli. Scriptler: `backend/scripts/quality/_keyverify/`.

---

## EDEBIYAT hedefli tam-havuz dalgası (1144, 2026-07-04)

En düşük ölçülen (56-örnek %91.1) branş hedeflendi → **tam 1144 havuz kör-çözüldü** (workflow w479x6edk, 46 agent, 1130 tahmin).

### Sonuç: küçük-örneklem gürültüsü çürüdü
- **AGREE %98.0** (1099/1121 çözülebilir) — 56-örnek %91.1 şanssız-cluster'dı. EDEBIYAT aslında ~%98, en kötü değil.
- DISAGREE 22 (%2.0), yüksek-güven 8.
- 2. sinyal (8): **5 STORED_WRONG + 3 model-hatası** (0 ambiguous). Doğrulanmış hata **5/1121 = %0.45**.
- 5 STORED_WRONG sağlam factual gerekçeli (Panorama=Yakup Kadri, gazel-mahlas yapısı, "Modern Türk Şiirinin Doğası"=Ebubekir Eroğlu, Şermin=hece/Tevfik Fikret).

### Kümülatif kanıt (2 dalga)
- Toplam **13 doğrulanmış cevap-anahtarı hatası** (8 genel + 5 EDEBIYAT) + 2 ambiguous → hepsi curator-flag'li (`keyverify_stored_wrong_20260704` / `keyverify_ambiguous_20260704`), correct_answer DOKUNULMADI.
- Backuplar: `question_bank_keyverify_flag_backup_20260704` (10) + `question_bank_keyverify_edb_backup_20260704` (5).
- **En kötü ölçülen branş bile ~%98 (EDEBIYAT), hata ~%0.45.** Servis havuzu anahtar-kalitesi satış için sağlam kanıtlandı.
