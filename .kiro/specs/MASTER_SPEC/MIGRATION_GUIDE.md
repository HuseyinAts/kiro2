# 🔄 Spec Migration Guide
## From Individual Specs → Master Spec

**Date**: 18 Ekim 2025  
**Reason**: 8 spec klasörü kafa karıştırıcıydı - tek master spec'e konsolide edildi

---

## 📋 Ne Değişti?

### Önceki Durum (8 Spec)
```
.kiro/specs/
├── turkiye-universite-sinav-hazirlik-platformu/
├── project-health-audit/
├── content-management-system/
├── learning-path-resource-quality/
├── shared-components/           (eksik)
├── combined-learning-platform/  (boş)
├── performans-optimizasyonu/    (boş)
└── project-analysis/            (boş)
```

### Yeni Durum (1 Master + Archive)
```
.kiro/specs/
├── MASTER_SPEC/                 (YENİ - TEK KAYNAK)
│   ├── README.md
│   ├── requirements.md (47 req, 200+ criteria)
│   ├── design.md
│   ├── tasks.md
│   └── MIGRATION_GUIDE.md (bu dosya)
└── archive/                     (ARŞIV)
    ├── turkiye-universite-sinav-hazirlik-platformu/
    ├── project-health-audit/
    ├── content-management-system/
    ├── learning-path-resource-quality/
    ├── shared-components/
    ├── combined-learning-platform/
    ├── performans-optimizasyonu/
    └── project-analysis/
```

---

## 🎯 Master Spec Eşleştirmeleri

### REQ ID Mapping

| Eski Spec | Master Spec Bölüm | REQ ID Range |
|-----------|-------------------|--------------|
| turkiye-universite... | Bölüm 1: Sınav Sistemi | REQ-1 to REQ-12 |
| content-management... | Bölüm 2: İçerik Yönetimi | REQ-13 to REQ-20 |
| learning-path-resource... | Bölüm 3: Kaynak Kalitesi | REQ-21 to REQ-25 |
| project-health-audit | Bölüm 4: Sağlık Denetimi | REQ-26 to REQ-47 |

### Örnek Eşleştirmeler

**Eski**:
- `turkiye-universite.../requirements.md` → Gereksinim 1
- `content-management.../requirements.md` → Gereksinim 1

**Yeni**:
- `MASTER_SPEC/requirements.md` → REQ-1 (ÖSYM Sınav)
- `MASTER_SPEC/requirements.md` → REQ-13 (Makale İçerik)

---

## 🛠️ Geliştiriciler İçin Değişiklikler

### Kod Referansları Güncelleme

#### Python Backend
```python
# ESKI
# Spec: turkiye-universite.../requirements.md Gereksinim 1.1

# YENİ  
# Spec: REQ-1.1 - ÖSYM TYT Sınav Formatı
```

#### Test Dosyaları
```python
# ESKI
"""
Test: content-management-system/requirements.md Gereksinim 1
"""

# YENİ
"""
Test: REQ-13 - Makale İçerik Yönetimi
Acceptance Criteria: REQ-13.1 to REQ-13.7
"""
```

#### Commit Messages
```bash
# ESKI
git commit -m "feat: implement video search (learning-path spec req 2)"

# YENİ
git commit -m "feat: implement video search (REQ-22 konu uygunluğu)"
```

---

## 📂 Arşivleme Detayları

### Arşivlenen Specler

#### ✅ Tam ve Aktif (Referans için saklandı)
1. **turkiye-universite-sinav-hazirlik-platformu**
   - Reason: Master spec'e tam entegre edildi
   - Archive path: `archive/turkiye-universite.../`
   - Use case: Detaylı tasarım referansı

2. **project-health-audit**
   - Reason: Master spec'e tam entegre edildi
   - Archive path: `archive/project-health-audit/`
   - Use case: 47 kontrol kriteri detayları

3. **content-management-system**
   - Reason: Master spec'e tam entegre edildi
   - Archive path: `archive/content-management-system/`

4. **learning-path-resource-quality**
   - Reason: Master spec'e tam entegre edildi
   - Archive path: `archive/learning-path-resource-quality/`

#### ⚠️ Eksik/Tamamlanmamış (Arşivlendi)
5. **shared-components**
   - Reason: Eksik requirements.md, design.md, tasks.md
   - Action: Arşivlendi, gelecekte gerekirse tamamlanabilir

#### ❌ Boş Klasörler (Silindi/Arşivlendi)
6. **combined-learning-platform** - Hiç içerik yok
7. **performans-optimizasyonu** - Hiç içerik yok
8. **project-analysis** - Hiç içerik yok

---

## ✅ Migration Checklist

### Geliştirici İçin
- [ ] Master spec'i oku (requirements.md)
- [ ] REQ ID'lerini öğren (REQ-1 to REQ-47)
- [ ] Kodlarında spec referanslarını güncelle
- [ ] Yeni commit message formatını kullan

### QA İçin
- [ ] Test planlarını yeni REQ ID'lere göre güncelle
- [ ] Kabul kriterlerini REQ-X.Y formatına çevir
- [ ] Test coverage raporlarını yeni ID'lerle eşleştir

### Proje Yöneticisi İçin
- [ ] tasks.md'deki % completion'ı takip et
- [ ] Yeni gereksinim eklemelerini master spec'e yap
- [ ] Sprint planlarını REQ önceliklerine göre düzenle

---

## 🔍 Sık Sorulan Sorular

### Q: Eski spec dosyalarını silebilir miyiz?
**A**: Hayır. Arşivlendi ama silinmedi. Detaylı referans için hala gerekli.

### Q: Yeni gereksinim eklenecekse nereye?
**A**: `MASTER_SPEC/requirements.md`'ye ekle, REQ-48 olarak başlat.

### Q: Bireysel spec'i güncellemek gerekirse?
**A**: Master spec'i güncelle, arşivdeki orijinali read-only olarak sakla.

### Q: Master spec çok mu büyük?
**A**: Evet (594 satır), ama tek kaynak. Bölümler halinde organize edilmiş.

### Q: Hangi spec'i okuyacağım?
**A**: Her zaman **MASTER_SPEC** önce, detay için arşivdeki orijinallere bak.

---

## 📞 Destek

Migration sorunları için:
- **Git history**: `git log --follow .kiro/specs/MASTER_SPEC/`
- **Sorular**: Team lead'e ulaşın
- **Spec güncellemeleri**: PR açın

---

**Migration Date**: 18 Ekim 2025  
**Migration By**: Claude AI  
**Status**: ✅ Complete
