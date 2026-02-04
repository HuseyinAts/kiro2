# Soru Bankası Servisi

## Genel Bakış

Soru Bankası Servisi, Türkiye Üniversite Sınavları Hazırlık Platformu'nun temel bileşenlerinden biridir. Bu servis, ÖSYM standartlarına uygun soru yönetimi, IRT (Item Response Theory) parametreli adaptif soru seçimi ve Türkçe morfolojik analiz özelliklerini sunar.

## Özellikler

### 🎯 Temel CRUD Operasyonları
- Soru ekleme, güncelleme, silme (soft delete)
- Filtreleme ve arama işlemleri
- Toplu soru ekleme desteği

### 🧠 IRT Parametreli Soru Seçimi
- **3PL IRT Modeli**: Zorluk (b), Ayırıcılık (a), Şans (c) parametreleri
- **Fisher Information**: Optimal bilgi değeri hesaplama
- **Adaptif Seçim**: Öğrenci yetenek seviyesine göre soru seçimi
- **Performans Takibi**: Gerçek zamanlı IRT parametresi güncelleme

### 🇹🇷 Türkçe Morfolojik Analiz
- **Karmaşıklık Hesaplama**: Kelime yapısı analizi
- **Okunabilirlik Skoru**: Türkçe'ye özel hesaplama
- **Hece Sayma**: Otomatik hece analizi
- **Zemberek Entegrasyonu**: Gelişmiş morfolojik işleme (hazır)

### 📊 İstatistik ve Raporlama
- Soru bankası genel istatistikleri
- Konu ve zorluk dağılımları
- IRT parametresi analizleri
- Kalite metrikleri

## Kullanım

### Servis Başlatma

```python
from services.soru_bankasi_service import soru_bankasi_servisi

# Servis hazır kullanıma hazır (singleton pattern)
```

### Soru Ekleme

```python
soru_data = {
    "soru_metni": "2x + 3 = 11 denkleminin çözümü nedir?",
    "secenekler": ["A) 2", "B) 3", "C) 4", "D) 5"],
    "dogru_cevap": "C",
    "konu": "Matematik",
    "alt_konu": "Birinci Dereceden Denklemler",
    "zorluk_seviyesi": "kolay",
    "sinav_tipi": "TYT",
    "cozum_aciklamasi": "2x + 3 = 11 → 2x = 8 → x = 4"
}

yeni_soru = await soru_bankasi_servisi.soru_ekle(soru_data)
```

### Rastgele Soru Seçimi

```python
# Basit rastgele seçim
sorular = await soru_bankasi_servisi.rastgele_sorular_sec(
    sinav_tipi="TYT",
    soru_sayisi=20
)

# Konu dağılımlı seçim
konu_dagilimi = {
    "Matematik": 10,
    "Türkçe": 10,
    "Fen": 5,
    "Sosyal": 5
}

sorular = await soru_bankasi_servisi.rastgele_sorular_sec(
    sinav_tipi="TYT",
    soru_sayisi=30,
    konu_dagilimi=konu_dagilimi
)
```

### IRT Parametreli Adaptif Seçim

```python
# Öğrenci yetenek seviyesine göre optimal sorular
adaptif_sorular = await soru_bankasi_servisi.irt_parametreli_soru_sec(
    ogrenci_yetenek=0.5,  # -3.0 ile +3.0 arası
    sinav_tipi="TYT",
    soru_sayisi=20,
    hedef_bilgi=1.0
)
```

### Zorluk Seviyesi Filtreleme

```python
# Yetenek seviyesine uygun sorular
uygun_sorular = await soru_bankasi_servisi.zorluk_seviyesi_filtrele(
    ogrenci_yetenek=0.0,
    sinav_tipi="TYT",
    tolerans=1.0  # ±1.0 zorluk toleransı
)
```

## API Endpoint'leri

### GET /api/v1/soru-bankasi/sorular
Filtrelere göre soru listesi getir

**Parametreler:**
- `sinav_tipi`: Sınav türü (TYT, AYT, YDT)
- `konu`: Konu filtresi
- `zorluk_seviyesi`: Zorluk seviyesi (easy, medium, hard)
- `limit`: Maksimum soru sayısı (1-500)
- `offset`: Sayfalama offset'i

### GET /api/v1/soru-bankasi/soru/{soru_id}
Belirli bir sorunun detaylarını getir

### POST /api/v1/soru-bankasi/rastgele-sorular
Rastgele soru seçimi yap

**Body:**
```json
{
  "sinav_tipi": "TYT",
  "soru_sayisi": 20,
  "konu_dagilimi": {
    "Matematik": 10,
    "Türkçe": 10
  }
}
```

### POST /api/v1/soru-bankasi/irt-parametreli-sorular
IRT parametreli adaptif soru seçimi

**Parametreler:**
- `ogrenci_yetenek`: Öğrenci yetenek parametresi (-3.0 ile +3.0)
- `sinav_tipi`: Sınav türü
- `soru_sayisi`: Seçilecek soru sayısı
- `hedef_bilgi`: Hedef bilgi fonksiyonu değeri

### GET /api/v1/soru-bankasi/konular
Mevcut konuları listele

### GET /api/v1/soru-bankasi/istatistikler
Soru bankası istatistiklerini getir

### POST /api/v1/soru-bankasi/soru-performans-guncelle
Soru performans istatistiklerini güncelle

## IRT (Item Response Theory) Modeli

### 3PL Model Formülü
```
P(θ) = c + (1-c) * [1 / (1 + e^(-a(θ-b)))]
```

**Parametreler:**
- **θ (theta)**: Öğrenci yetenek seviyesi
- **a**: Ayırıcılık parametresi (0.5-2.5)
- **b**: Zorluk parametresi (-3.0 ile +3.0)
- **c**: Şans parametresi (genellikle 0.25)

### Fisher Information Fonksiyonu
```
I(θ) = a² * [(P(θ)(1-P(θ))) / (1-c)²] * [(1-c) / (P(θ)-c)]²
```

## Türkçe Morfolojik Analiz

### Karmaşıklık Faktörleri
- **Ek Sayısı**: Kelime başına ek sayısı
- **Türetim Derinliği**: Morfolojik türetim seviyesi
- **Birleşik Kelime**: Birleşik yapı karmaşıklığı
- **Ses Değişimleri**: Fonetik değişim sayısı
- **Anlam Belirsizliği**: Çok anlamlılık faktörü

### Okunabilirlik Hesaplama
Türkçe'ye uyarlanmış Flesch-Kincaid formülü:
```
Okunabilirlik = 206.835 - (1.015 * (kelime/cümle)) - (84.6 * (hece/kelime))
```

## Konfigürasyon

### Varsayılan IRT Parametreleri
```python
default_irt_params = {
    "difficulty_range": (-3.0, 3.0),
    "discrimination_range": (0.5, 2.5),
    "guessing_parameter": 0.25,
    "target_information": 1.0
}
```

### Konu Dağılım Şablonları
```python
konu_dagilim_sablonlari = {
    SinavTipi.TYT: {
        "Matematik": 40,
        "Türkçe": 40, 
        "Fen": 20,
        "Sosyal": 20
    },
    SinavTipi.AYT: {
        "Matematik": 40,
        "Fizik": 14,
        "Kimya": 13,
        "Biyoloji": 13
    },
    SinavTipi.YDT: {
        "İngilizce": 80
    }
}
```

## Test Edilmiş Özellikler

✅ **Enum Dönüştürücü**: String'den SQLAlchemy enum'larına dönüştürme  
✅ **IRT Parametresi Hesaplama**: Zorluk ve konu bazlı parametre üretimi  
✅ **Morfolojik Karmaşıklık**: Türkçe kelime analizi  
✅ **Okunabilirlik Skoru**: Metin zorluk değerlendirmesi  
✅ **Hece Sayma**: Otomatik hece analizi  
✅ **Bilgi Fonksiyonu**: Fisher Information hesaplama  
✅ **Olasılık Hesaplama**: 3PL IRT model implementasyonu  
✅ **Database Entegrasyonu**: Async SQLAlchemy operasyonları  
✅ **API Endpoint'leri**: RESTful API tasarımı  
✅ **Error Handling**: Kapsamlı hata yönetimi  

## Performans Optimizasyonları

- **Connection Pooling**: Database bağlantı havuzu
- **Async Operations**: Tüm I/O işlemleri asenkron
- **Caching Strategy**: Redis entegrasyonu hazır
- **Batch Operations**: Toplu işlem desteği
- **Index Optimization**: Database indeks stratejisi

## Güvenlik

- **Input Validation**: Pydantic model validasyonu
- **SQL Injection**: SQLAlchemy ORM koruması
- **Rate Limiting**: API endpoint koruması
- **Authentication**: JWT token entegrasyonu
- **Authorization**: Rol tabanlı erişim kontrolü

## Monitoring ve Logging

- **Performance Metrics**: Yanıt süresi takibi
- **Error Tracking**: Detaylı hata loglama
- **Usage Analytics**: API kullanım istatistikleri
- **Health Checks**: Sistem durumu kontrolü

## Gelecek Geliştirmeler

🔄 **Zemberek-NLP Entegrasyonu**: Gelişmiş Türkçe morfoloji  
🔄 **Machine Learning**: Otomatik IRT kalibrasyonu  
🔄 **Real-time Analytics**: Canlı performans takibi  
🔄 **A/B Testing**: Soru seçim algoritması optimizasyonu  
🔄 **Multi-language**: Çoklu dil desteği  

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## Lisans

Bu proje Teknofest 2025 Eğitim Teknolojileri yarışması kapsamında geliştirilmiştir.