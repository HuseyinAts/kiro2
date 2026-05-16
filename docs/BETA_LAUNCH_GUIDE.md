# KIRO2 Beta Soft Launch — Manual Mode

**Tarih:** 17 May 2026 (Faz 7.1)
**Kapsam:** 10 öğrenci × 1 hafta canlı test
**Beta pool:** 22,325 sample (v_safe_for_beta, Faz 5+6 rule-based filter)
**Manuel feedback:** Telegram/email/issue (Faz 7.2 endpoint yok)

---

## 1. Davetiye Mesaj Template

### Kısa (WhatsApp/Telegram)

```
Merhaba 👋

KIRO2 (Turkish EdTech YKS prep platformu) beta test'e davetlisin.

🔗 Link: http://localhost:3000  (veya açık adres)
👤 Kullanıcı adın: beta0X@kiro2.com (X = 1-10 arası)
🔑 Şifre: Beta0X!Kiro2026 (X yerine kullanıcı numarası, örn: Beta03!Kiro2026)

İşin: 1 hafta günlük 10-20 soru çöz. Hatalı veya tuhaf soru görürsen:
- Screenshot al
- WhatsApp/Telegram'a gönder ("ID, sayfa, sorun")

Teşekkürler! 🚀
```

### Detaylı (email)

```
Konu: KIRO2 YKS prep beta — 1 hafta test

Merhaba [İsim],

KIRO2 platformuna 1 haftalık beta erişimin açıldı. YKS hazırlanan
öğrenciler için Türkçe AI-destekli adaptif soru çözüm platformu.

GİRİŞ:
  URL: http://localhost:3000
  E-posta: beta0X@kiro2.com  (X = 1-10)
  Şifre: Beta0X!Kiro2026

YAPACAĞIN İŞ (1 HAFTA):
  - Günlük 10-20 soru çöz (matematik/fizik/kimya/Türkçe vb.)
  - Beğendiğin/sevmediğin özellikleri not al
  - Hatalı/tuhaf soru görürsen rapor et (ekran görüntüsü + ID)

HATA RAPORLAMA:
  - Screenshot al
  - Telegram: @kiro2_beta (veya kişisel)
  - E-posta: beta@kiro2.com
  - GitHub issue: huseyinats/kiro2/issues

DİKKAT EDİLECEKLER:
  - Bazı sorular "AROMAT MODELI" işaretli ama içerik farklı → bu pipeline
    bug'ı, sorudan değil etiketleme hatasından
  - Bazı sorularda çözüm anahtarı sayfada görünüyor olabilir → rapor et
  - Matematik sorularında cevap yanlış olabilir (DB pipeline kalıntısı)

Teşekkürler! Geri bildirimlerin platformun gelişimi için kritik.

— KIRO2 Team
```

---

## 2. Beta Tracking SQL

### Günlük cevap sayımı

```sql
-- Beta kullanıcıların günlük aktivitesi
SELECT
    u.email,
    DATE(ua.attempted_at) AS gun,
    COUNT(*) AS toplam_cevap,
    COUNT(*) FILTER (WHERE ua.is_correct = TRUE) AS dogru,
    COUNT(*) FILTER (WHERE ua.is_correct = FALSE) AS yanlis,
    ROUND(100.0 * COUNT(*) FILTER (WHERE ua.is_correct = TRUE) / NULLIF(COUNT(*), 0), 1) AS pass_pct
FROM users u
LEFT JOIN user_question_attempts ua ON ua.user_id = u.id
WHERE u.email LIKE 'beta%@kiro2.com'
  AND (ua.attempted_at IS NULL OR ua.attempted_at >= NOW() - INTERVAL '7 days')
GROUP BY u.email, DATE(ua.attempted_at)
ORDER BY u.email, gun DESC;
```

### Beta-eligible pool kullanımı

```sql
-- Beta kullanıcıların gördüğü soru pool oranları
SELECT
    q.quality_review_status,
    COUNT(DISTINCT ua.question_id) AS unique_sorular_sunulan,
    COUNT(*) AS toplam_attempt
FROM user_question_attempts ua
JOIN question_bank q ON q.id = ua.question_id
JOIN users u ON u.id = ua.user_id
WHERE u.email LIKE 'beta%@kiro2.com'
GROUP BY q.quality_review_status
ORDER BY toplam_attempt DESC;
```

### Manuel feedback log (telegram/email içeriden)

```bash
# Markdown'da topla, weekly summary'de incele
docs/beta_feedback/2026-W20-feedback.md
docs/beta_feedback/2026-W21-feedback.md
...
```

---

## 3. Pre-Launch Checklist

- [x] Docker stack healthy (`docker ps`)
- [x] Backend /health 200
- [x] Frontend 3000 OK
- [x] Login E2E (test@kiro2.com + beta01@kiro2.com)
- [x] 10 beta user oluşturuldu (`beta_create_users.py --apply`)
- [x] v_safe_for_beta = 22,325 sample (Faz 5+6 rule-based)
- [ ] Davetiye gönderildi (5-10 öğrenci)
- [ ] Beta tracking SQL haftalık çalıştırıldı
- [ ] Feedback toplandı (telegram/email)

---

## 4. 1 Hafta Sonra Audit (Faz 7.3 retrospective)

Sonra:
1. SQL ile aktivite çek (toplam attempt, pass rate, error type)
2. Manuel feedback'leri kategorize et (wrong_answer / wrong_topic / missing_diagram / OCR / UI bug / vb.)
3. Plan v1 hipotezleri vs gerçek hata oranı karşılaştır
4. Faz 7.4 (Curator quota) ve Faz 7.5 (Judge re-calibration) için input

---

## 5. Reject/Manual Queue Hatırlatma

Beta user'lar bu sample'ları **görmeyecek** (rule-based filter sayesinde):
- 21,329 rejected (legacy_v3 + Aromat)
- 197 Edebiyat Sokagi Dil Bilgisi (manual queue)

Yani şikayetlerin çoğu **kaliteli pool içinde** yaşanan hatalar olmalı — bu Faz 6.2 audit etkisini gösterir.

---

## 6. Beta User Listesi

| Email | Şifre | İsim |
|---|---|---|
| beta01@kiro2.com | Beta01!Kiro2026 | Beta User 01 |
| beta02@kiro2.com | Beta02!Kiro2026 | Beta User 02 |
| beta03@kiro2.com | Beta03!Kiro2026 | Beta User 03 |
| beta04@kiro2.com | Beta04!Kiro2026 | Beta User 04 |
| beta05@kiro2.com | Beta05!Kiro2026 | Beta User 05 |
| beta06@kiro2.com | Beta06!Kiro2026 | Beta User 06 |
| beta07@kiro2.com | Beta07!Kiro2026 | Beta User 07 |
| beta08@kiro2.com | Beta08!Kiro2026 | Beta User 08 |
| beta09@kiro2.com | Beta09!Kiro2026 | Beta User 09 |
| beta10@kiro2.com | Beta10!Kiro2026 | Beta User 10 |

---

*Generated: 17 May 2026, Faz 7.1 Manual Beta launch artifacts.*
