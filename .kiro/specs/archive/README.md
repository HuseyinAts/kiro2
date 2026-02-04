# 📦 Arşivlenmiş Spec Dosyaları

**Arşivleme Tarihi**: 18 Ekim 2025  
**Sebep**: 8 dağınık spec → 1 master spec konsolidasyonu

---

## ⚠️ ÖNEMLİ UYARI

Bu klasördeki specler **ARŞİVLENMİŞTİR** ve aktif geliştirme için kullanılmamalıdır.

**Aktif Spec**: `../MASTER_SPEC/`

---

## 📂 Arşivlenen Dosyalar

### ✅ Tam ve Aktif Specler (MASTER_SPEC'e entegre edildi)

| Spec | Boyut | Durum | Master Spec Bölüm |
|------|-------|-------|-------------------|
| turkiye-universite-sinav-hazirlik-platformu | 172KB | ✅ Tam | Bölüm 1 (REQ-1 to REQ-12) |
| project-health-audit | 124KB | ✅ Tam | Bölüm 4 (REQ-26 to REQ-47) |
| content-management-system | 32KB | ✅ Tam | Bölüm 2 (REQ-13 to REQ-20) |
| learning-path-resource-quality | 44KB | ✅ Tam | Bölüm 3 (REQ-21 to REQ-25) |

### ⚠️ Eksik Specler

| Spec | Boyut | Durum | Notlar |
|------|-------|-------|--------|
| shared-components | 3KB | ⚠️ Eksik | requirements.md, tasks.md eksik |

### ❌ Boş Klasörler

| Spec | Boyut | Durum | Notlar |
|------|-------|-------|--------|
| combined-learning-platform | 0KB | ❌ Boş | Hiç içerik yok |
| performans-optimizasyonu | 0KB | ❌ Boş | Hiç içerik yok |
| project-analysis | 0KB | ❌ Boş | Hiç içerik yok |

---

## 🔍 Ne Zaman Kullanılır?

Bu arşiv dosyaları şu durumlarda faydalıdır:

1. **Detaylı Tasarım Referansı**: Master spec'te olmayan detaylar için
2. **Geçmiş Analizi**: Spec evrimini incelemek için
3. **Migration Doğrulama**: MASTER_SPEC'in doğru oluşturulduğunu doğrulamak için

---

## 📖 Nasıl Okunur?

### Örnek: Sınav sistemi detayları

```bash
# MASTER_SPEC'te özet var
cat ../MASTER_SPEC/requirements.md  # REQ-1: ÖSYM Sınav Sistemi

# Detay için arşive bak
cat turkiye-universite-sinav-hazirlik-platformu/design.md  # Detaylı mimari
```

---

## ⚡ Hızlı Referans

### REQ ID → Arşiv Eşleştirme

| REQ Range | Orijinal Spec | Arşiv Yolu |
|-----------|---------------|------------|
| REQ-1 to REQ-12 | turkiye-universite... | `archive/turkiye-universite.../` |
| REQ-13 to REQ-20 | content-management | `archive/content-management-system/` |
| REQ-21 to REQ-25 | learning-path | `archive/learning-path-resource-quality/` |
| REQ-26 to REQ-47 | health-audit | `archive/project-health-audit/` |

---

## 🚫 Yapılmaması Gerekenler

❌ **Bu arşivi yeni geliştirme için kullanmayın**  
❌ **Spec güncellemelerini buraya yapmayın**  
❌ **Yeni gereksinimleri buraya eklemeyin**

✅ **Bunun yerine**: `../MASTER_SPEC/` kullanın

---

## 📞 Sorular?

- **Migration ile ilgili**: `../MASTER_SPEC/MIGRATION_GUIDE.md`
- **Master Spec kullanımı**: `../MASTER_SPEC/README.md`
- **Teknik sorular**: Team lead'e danışın

---

**Arşiv Oluşturan**: Claude AI  
**Arşiv Tarihi**: 18 Ekim 2025  
**Toplam Arşiv Boyutu**: ~375KB
