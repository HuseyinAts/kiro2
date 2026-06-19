# Fallback Re-tag — RESULT (2026-06-20)

## Hedef
2.058 fallback-vp soru (3-sinyal doğrulanmış: key+blind+readability, yalnız güvenilir
topic eksik) → primary_topic re-tag + status promote → v_safe.

## Yapılan (DB canlı, reversible)
- **v_safe 7.812 → 8.337 (+525).** 525 CLEAN soru re-tag'lendi.
- Apply: primary_topic_id güncel + quality_review_status='auto_judged_high' +
  pipeline_metadata.ai_extras.topic_match_quality='llm_retag_verified' (fallback temizlendi) +
  flag fallback_retag_run='2026-06-20'. **correct_answer/is_active DOKUNULMADI.**
- 525/525 v_safe'e girdi (diğer kapılar zaten temizdi). Spot-check 8/8 + pilot 5/5 doğru.
- Backup: question_bank_fallback_retag_backup_20260620 (2.058 satır snapshot, reversible).

## Sınıflandırma kapsamı (rate-limit nedeniyle kısmi)
- 603/2.058 işlendi → 525 CLEAN (subject_ok ∧ conf≥0.80 ∧ topic-çözülür) apply.
- 78 covered-ama-clean-değil: subject_ok=N (yanlış-ders/taksonomi-gap) veya conf<0.80 → fallback'te kaldı.
- **1.455 KALDI** (FIZIK kuyruğu + GEOMETRI + KIMYA + MATEMATIK + SOSYAL + TARIH + TURKCE batch'leri rate-limit yedi).

## Rate-limit gerçeği
Batch'leme çağrıyı 20× azalttı (2058→106) AMA hesabın anlık RPM tavanı o kadar düşük ki
106 batch çağrısı bile ~33'ten sonra 529 yedi. Bkz [[reference_workflow-rate-limit-batching]].
KALAN İÇİN: ya çok-büyük batch (70-100/agent → ~15-21 çağrı) + uzun cooldown, ya da
TAZE SESSION (RPM resetlenir). Batch dosyaları + manifest + missing_ids.json hazır.

## CLEAN dağılımı (uygulanan 525)
BIYOLOJI 331, FIZIK 116, EDEBIYAT 32, COGRAFYA 29, MATEMATIK 6, KIMYA 5, TURKCE 4, GEOMETRI 2.

## Taksonomi boşlukları (re-tag sırasında keşfedildi)
- KIMYA: "Çözeltiler/Karışımlar" ve "bilim tarihi" topic'i YOK → çözünürlük/simya soruları subject_ok=N.
- Bazı subject_area gerçekten yanlış: "su kaynakları büyüklüğü" KIMYA etiketli ama coğrafya.

---
## FINAL (20 Haz, big-batch tamamlandı)
- **v_safe 7.812 -> 9.448 (+1.636).** Toplam re-tag: 525 (ilk run) + 1.111 (big-batch) = 1.636.
- Kapsam TAM: 2.050/2.058 islendi. CLEAN 1.636 apply, 422 dislandi (subject_ok=N + conf<0.80 + 2 unresolved) -> fallback'te kaldi.
- **Big-batch cozumu rate-limit'i KESIN cozdu:** 80 soru/agent, WAVE=3, 120sn cooldown -> 22 agent, 0 hata.
- retag_in_vsafe=1.636/1.636 (hepsi v_safe'e girdi). correct_answer/is_active DOKUNULMADI.
- backup question_bank_fallback_retag_backup_20260620 (2.058 reversible).
