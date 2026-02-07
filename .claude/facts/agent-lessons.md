# Agent Lessons Learned (Hatalardan Ogrenilenler)

Bu dosya agent'larin yaptigi hatalardan ogrenilenlerini icerir.
Her hata bir ders olarak kaydedilir ve gelecek calismalarda referans alinir.

---

## 2026-01-22: TypeScript Unused Fix Hatalari

### Hata 1: Kullanilan Import'u Silme
- **Dosya:** `BatchOperationsPage.tsx`
- **Hata:** `TableRow` import'u "unused" olarak isaretlendi ve silindi
- **Gercek:** `TableRow` dosyada 10+ yerde kullaniliyordu
- **Sebep:** Agent sadece import satirina bakti, dosyanin geri kalanini kontrol etmedi

**DERS:** Import silmeden once MUTLAKA `grep -c "ImportName" dosya.tsx` calistir.
Eger sonuc > 1 ise, import KULLANILIYOR demektir, SILME!

### Hata 2: Kullanilan Import'u Silme (recharts)
- **Dosya:** `PerformanceChart.tsx`
- **Hata:** `Line` import'u silindi
- **Gercek:** `<Line />` componenti JSX'te kullaniliyordu
- **Sebep:** Agent sadece TypeScript hatasina odaklandi

**DERS:** JSX icinde kullanim da kontrol edilmeli: `grep -c "<ImportName" dosya.tsx`

### Hata 3: Kullanilan Degiskeni Rename Etme
- **Dosya:** `BatchOperationsPage.tsx`
- **Hata:** `topics` -> `_topics` yapildi
- **Gercek:** `topics` degiskeni baska satirlarda kullaniliyordu
- **Sebep:** Sadece declaration satiri kontrol edildi

**DERS:** Degisken rename oncesi TUM referanslari kontrol et:
```bash
grep -n "variableName" dosya.tsx
```
Eger declaration disinda kullanim varsa, RENAME YAPMA!

---

## Genel Kurallar (Tum Agent'lar Icin)

### Import/Export Islemleri
1. Silmeden once `grep -c` ile kullanim sayisini kontrol et
2. JSX kullanimi icin `<ComponentName` pattern'i de ara
3. Her dosya degisikliginden sonra `tsc --noEmit` calistir

### Degisken Islemleri
1. Rename oncesi tum dosyayi tara
2. Sadece declaration'da geciyorsa (1 kullanim) rename yap
3. Baska yerlerde kullaniliyorsa DOKUNMA

### Dogrulama Adimlari
```bash
# Her degisiklikten sonra
cd frontend && npx tsc --noEmit src/path/to/file.tsx

# Hata cikarsa GERİ AL
git checkout -- src/path/to/file.tsx
```

---

## Hata Ekleme Sablonu

Yeni hata eklerken su formati kullan:

```markdown
### Hata X: [Kisa Baslik]
- **Dosya:** `dosya.tsx`
- **Hata:** [Ne yapildi]
- **Gercek:** [Gercekte ne olmasi gerekiyordu]
- **Sebep:** [Neden oldu]

**DERS:** [Ogrenilenler ve kural]
```
