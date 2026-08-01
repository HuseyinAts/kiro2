# Ders Kaydı — denetle / değiştir / sil

`ders_kaydi.yaml` bu deponun **tek ders defteri**. Uzun anlatım hâlâ
`.claude/rules/*.md` içinde; bu defter onların üstünde bir **yaşam döngüsü**
katmanı. Bekçi: `backend/tests/unit/test_ders_kaydi.py`.

## Neden var

Dersler 13 dosyada, 2203 satır prose içinde dağılmıştı: kimliği, durumu, kanıtı
ve zorlayıcısı yoktu. `testing.md` #15 zaten şunu yazıyor —

> "Ders çıkarılması YETMEZ. 3 adım gerekli: (1) testing.md'ye yaz **(YAPILIYOR)**,
> (2) pre-commit hook veya lint rule ekle **(YAPILMIYOR)**, (3) CI/CD'de kontrol
> et **(YAPILMIYOR)**"

Bu defter (2) ve (3)'ü mümkün kılar: bir ders artık *hangi testin* koruduğunu
söyler ve o test silinirse bekçi kırmızıya döner.

## Şema

| Alan | Anlamı |
|---|---|
| `id` | Kalıcı kimlik. Değişmez — ankraj bozulur. |
| `baslik` | Tek cümle, emir kipi tercih edilir. |
| `kaynak` | `dosya.md#bölüm` — uzun anlatımın yeri. **Dosya var olmalı.** |
| `sinif` | `olcum` · `test` · `sema` · `alet` · `tekrarlayan` |
| `durum` | `aktif` · `dogrulanmadi` · `curutuldu` · `devredildi` |
| `zorlayici` | Dersi koruyan test/hook yolu (yoksa `null`). **Varsa dosya var olmalı.** |
| `kanit` | Commit hash / ölçüm. `aktif` ve `curutuldu` için **zorunlu**. |

## Durum ne demek

- **`aktif`** — ÖLÇÜLDÜ ve hâlâ geçerli. Kanıtsız `aktif` olamaz; bekçi düşürür.
- **`dogrulanmadi`** — Defterde var ama bu turda doğrulanmadı. Göç edilen 47
  dersin çoğu burada. Bu **dürüst** varsayılan: "yazılmış" ≠ "hâlâ doğru".
- **`curutuldu`** — Ölçüm dersi yanlışladı. `kanit` alanına **neyin çürüttüğü**
  yazılır. Bu depoda emsali var: "61K garble" varsayımı ölçülünce çürüdü.
- **`devredildi`** — Yerini başka bir ders aldı; `kanit`'e yeni `id` yazılır.

## Üç işlem

### Denetle
```bash
cd backend && pytest tests/unit/test_ders_kaydi.py -v
```
Bekçi şunları arar: yetim `kaynak`, silinmiş `zorlayici`, kanıtsız `aktif`,
gerekçesiz `curutuldu`, tekrarlayan `id`, taban altına düşen ders sayısı.

`dogrulanmadi` sayısını azaltmak **denetimin kendisidir**: bir dersi elden
geçir, hâlâ geçerliyse kanıt ekleyip `aktif` yap.

### Değiştir
`durum` + `kanit` alanlarını düzenle. `id` ve `baslik`'e dokunma — ankraj ve
arama onlara dayanıyor. Başlık gerçekten yanlışsa: eskisini `devredildi` yap,
yenisini yeni `id` ile ekle.

### Sil
**Sessiz silme yok.** Doğru yol `durum: curutuldu` + `kanit`. Fiziksel silme
git diff'inde görünür ve bekçinin taban sayısı (`DERS_TABANI`) toplu silmenin
fark edilmeden geçmesini engeller — sayı düşerse bilinçli karar gerekir.

## Yeni ders ekleme

Bir oturumda ölçümle bir şey öğrenildiyse:

1. Uzun anlatımı ilgili `.claude/rules/*.md` dosyasına yaz (varsa).
2. Deftere satır ekle: `durum: aktif` + `kanit: <commit veya ölçüm>`.
3. Dersi koruyan bir test/hook yazdıysan `zorlayici` alanına yolunu koy.
   Yazmadıysan `null` bırak — **yalan söyleme**, bu boşluk görünür kalsın.

## Bilinen sınır

Bu bekçi dersin **doğruluğunu** değil, defterin **bütünlüğünü** ölçer:
ankrajlar çözülüyor mu, kanıt var mı, zorlayıcı duruyor mu. Bir dersin hâlâ
geçerli olup olmadığı ancak o dersin kendi ölçümü tekrarlanarak anlaşılır —
`dogrulanmadi` durumu tam olarak bunu görünür kılmak için var.
