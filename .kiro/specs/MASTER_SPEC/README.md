# 📚 MASTER SPEC - Platform Gereksinim ve Tasarım Dokümanları

**Oluşturulma**: 18 Ekim 2025  
**Versiyon**: 1.0  
**Durum**: Aktif

---

## 📋 İçindekiler

Bu klasör, tüm bireysel speclerin birleştirilmiş master dokümanlarını içerir.

### Dosyalar

1. **[requirements.md](./requirements.md)** (594 satır)
   - 47 ana gereksinim
   - 200+ kabul kriteri
   - 4 bölüm: Sınav, İçerik, Kaynak Kalitesi, Sağlık Denetimi

2. **[design.md](./design.md)**
   - Sistem mimarisi
   - Teknoloji stack
   - API tasarımı
   - Güvenlik ve performans

3. **[tasks.md](./tasks.md)**
   - Tamamlanmış görevler (%97)
   - Devam eden görevler (%3)
   - Öncelik sıralaması

4. **[README.md](./README.md)** (bu dosya)
   - Genel bakış
   - Kullanım kılavuzu

---

## 🎯 Amaç

Bu master spec, 8 farklı spec klasöründeki dağınık gereksinimleri **tek bir tutarlı dokümantasyon setinde** birleştirmek için oluşturulmuştur.

### Birleştirilen Specler

| Spec Adı | Durum | Satır | Bölüm |
|----------|-------|-------|-------|
| turkiye-universite-sinav-hazirlik-platformu | ✅ Tam | 4,422 | 1 (Sınav Sistemi) |
| project-health-audit | ✅ Tam | 2,613 | 4 (Sağlık Denetimi) |
| content-management-system | ✅ Tam | 749 | 2 (İçerik Yönetimi) |
| learning-path-resource-quality | ✅ Tam | 1,026 | 3 (Kaynak Kalitesi) |
| shared-components | ⚠️ Eksik | - | (Referans) |
| combined-learning-platform | ❌ Boş | - | (Arşivlenecek) |
| performans-optimizasyonu | ❌ Boş | - | (Arşivlenecek) |
| project-analysis | ❌ Boş | - | (Arşivlenecek) |

---

## 🚀 Nasıl Kullanılır?

### Yeni Geliştirici İçin
1. **İlk okuma**: requirements.md → design.md → tasks.md sırasıyla
2. **Detay için**: Bireysel spec klasörlerine bakın
3. **Kod yazarken**: tasks.md'deki önceliklere göre ilerleyin

### Proje Yöneticisi İçin
1. **İlerleme takibi**: tasks.md (% completion metrikleri)
2. **Gereksinim doğrulama**: requirements.md (kabul kriterleri)
3. **Teknik değerlendirme**: design.md (mimari kararlar)

### QA Mühendisi İçin
1. **Test planı**: requirements.md (her REQ için test yazılabilir)
2. **Kabul testleri**: Kabul kriterlerini test senaryolarına çevirin
3. **Entegrasyon testleri**: design.md'deki API endpoint'leri test edin

---

## 📊 İstatistikler

| Metrik | Değer |
|--------|-------|
| **Toplam Gereksinim** | 47 |
| **Kabul Kriteri** | 200+ |
| **Tamamlanmış Görev** | %97 |
| **Kalan İş** | %3 (security, monitoring) |
| **Öncelik P0** | 5 gereksinim |
| **Öncelik P1** | 8 gereksinim |
| **Öncelik P2** | 11 gereksinim |
| **Öncelik P3** | 23 gereksinim |

---

## ⚠️ Önemli Notlar

### Bireysel Specler Hala Geçerli
Master spec, bireysel speclerin **yerini almaz**. Sadece bunları birleştirir ve özet sunar. Detaylı bilgi için orijinal spec dosyalarına bakın.

### Versiyon Kontrolü
- Master spec versiyonu: **1.0**
- Her değişiklik için versiyon numarası artırılmalı
- Değişiklikler CHANGELOG.md'de takip edilmeli

### Güncellemeler
Master spec'i güncellerken:
1. Orijinal spec'i güncelle
2. Master spec'i senkronize et
3. Versiyon numarasını artır
4. CHANGELOG.md'e ekle

---

## 🔗 Referanslar

### İlgili Dokümantasyon
- [Ana Platform Spec](../turkiye-universite-sinav-hazirlik-platformu/)
- [Sağlık Denetimi Spec](../project-health-audit/)
- [İçerik Yönetimi Spec](../content-management-system/)
- [Kaynak Kalitesi Spec](../learning-path-resource-quality/)

### Geliştirme Kaynakları
- Backend: `c:/Users/husey/kiro2/backend/`
- Frontend: `c:/Users/husey/kiro2/frontend/`
- Tests: `c:/Users/husey/kiro2/backend/tests/`

---

## 📞 İletişim

Sorularınız için:
- **Spec güncellemeleri**: Git commit ile önerilerinizi paylaşın
- **Teknik sorular**: Backend/Frontend ekipleriyle iletişime geçin
- **Gereksinim değişiklikleri**: Product Owner onayı gereklidir

---

**Son Güncelleme**: 18 Ekim 2025  
**Güncelleyen**: Claude AI (Spec Consolidation)
