# Requirements Document

## Introduction

Bu özellik, http://localhost:3001/learning-path sayfasındaki "Size Özel Kaynaklar" bölümünde gösterilen video kaynaklarının kalitesini ve uygunluğunu artırmayı amaçlamaktadır. Mevcut sistemde üç kritik sorun tespit edilmiştir:

1. Önerilen kaynakların Türkçe olmaması
2. Önerilen kaynakların ders ve konu ile tam uyumlu olmaması
3. Önerilen videoların çalışmaması (kırık linkler, erişim sorunları)

## Glossary

- **LearningPathSystem**: Öğrencilere kişiselleştirilmiş öğrenme yolu oluşturan sistem
- **ResourceRecommendationEngine**: Öğrenme kaynaklarını öneren motor
- **YouTubeIntegrationService**: YouTube API ile entegrasyon servisi
- **VideoQualityValidator**: Video kaynaklarının kalitesini ve erişilebilirliğini doğrulayan servis
- **TurkishContentFilter**: Türkçe içerik filtreleme servisi
- **SubjectRelevanceScorer**: Konu uygunluğu skorlama servisi
- **SemanticMatcher**: Semantik eşleştirme yapan servis

## Requirements

### Requirement 1: Türkçe İçerik Garantisi

**User Story:** Öğrenci olarak, öğrenme yolumda önerilen tüm videoların Türkçe olmasını istiyorum, böylece içeriği tam olarak anlayabilirim.

#### Acceptance Criteria

1. WHEN ResourceRecommendationEngine bir video önerisi oluşturduğunda, THE TurkishContentFilter SHALL video başlığını ve açıklamasını Türkçe dil kontrolünden geçirir
2. WHEN TurkishContentFilter bir videoyu analiz ettiğinde, THE TurkishContentFilter SHALL video kanalının Türkçe eğitim kanalları listesinde olup olmadığını kontrol eder
3. WHEN bir video Türkçe olmadığı tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır
4. WHEN TurkishContentFilter Türkçe skorunu hesapladığında, THE TurkishContentFilter SHALL minimum %70 Türkçe skoru olan videoları kabul eder
5. WHEN öğrenci "Size Özel Kaynaklar" bölümünü görüntülediğinde, THE LearningPathSystem SHALL sadece Türkçe onaylı videoları gösterir

### Requirement 2: Konu Uygunluğu Doğrulaması

**User Story:** Öğrenci olarak, önerilen videoların çalıştığım ders ve konuyla tam uyumlu olmasını istiyorum, böylece zamanımı boşa harcamam.

#### Acceptance Criteria

1. WHEN SubjectRelevanceScorer bir videoyu değerlendirdiğinde, THE SubjectRelevanceScorer SHALL video başlığı ve açıklamasını öğrenci profilindeki ders ve konu ile karşılaştırır
2. WHEN SemanticMatcher konu uygunluğunu hesapladığında, THE SemanticMatcher SHALL embedding tabanlı semantik benzerlik skoru hesaplar
3. WHEN bir videonun konu uygunluk skoru %60'ın altında olduğunda, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır
4. WHEN ResourceRecommendationEngine video sıralaması yaptığında, THE ResourceRecommendationEngine SHALL konu uygunluk skorunu öncelikli sıralama kriteri olarak kullanır
5. WHEN öğrenci bir modül için video önerileri aldığında, THE LearningPathSystem SHALL modülün konusu ile %80 üzeri uyumlu videoları önceliklendirir

### Requirement 3: Video Erişilebilirlik Kontrolü

**User Story:** Öğrenci olarak, önerilen videoların çalışır durumda olmasını istiyorum, böylece kırık linklerle zaman kaybetmem.

#### Acceptance Criteria

1. WHEN VideoQualityValidator bir video önerisi aldığında, THE VideoQualityValidator SHALL videonun YouTube'da erişilebilir olup olmadığını kontrol eder
2. WHEN bir video erişilemez durumda tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır ve alternatif video arar
3. WHEN YouTubeIntegrationService video metadata'sını çektiğinde, THE YouTubeIntegrationService SHALL videonun gömülebilir (embeddable) olup olmadığını doğrular
4. WHEN VideoQualityValidator video kalitesini değerlendirdiğinde, THE VideoQualityValidator SHALL videonun yayın durumunu (public/private/unlisted) kontrol eder
5. WHEN öğrenci bir videoyu oynatmaya çalıştığında, THE LearningPathSystem SHALL sadece erişilebilir ve gömülebilir videoları gösterir

### Requirement 4: Öneri Kalite Metrikleri

**User Story:** Öğrenci olarak, en kaliteli ve güvenilir eğitim videolarını görmek istiyorum, böylece doğru bilgi edinebilirim.

#### Acceptance Criteria

1. WHEN ResourceRecommendationEngine video skorlaması yaptığında, THE ResourceRecommendationEngine SHALL kanal güvenilirliği, görüntülenme sayısı ve beğeni oranını hesaba katar
2. WHEN bir video güvenilir eğitim kanallarından birinden geldiğinde, THE ResourceRecommendationEngine SHALL bu videoya %20 bonus skor ekler
3. WHEN VideoQualityValidator video süresini kontrol ettiğinde, THE VideoQualityValidator SHALL 5-60 dakika arası videoları ideal olarak değerlendirir
4. WHEN bir videonun altyazı desteği olduğu tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoya %10 bonus skor ekler
5. WHEN öğrenci video önerilerini görüntülediğinde, THE LearningPathSystem SHALL videoları toplam kalite skoruna göre sıralı olarak gösterir

### Requirement 5: Gerçek Zamanlı Doğrulama

**User Story:** Öğrenci olarak, öğrenme yolum her yüklendiğinde güncel ve çalışan videoların gösterilmesini istiyorum.

#### Acceptance Criteria

1. WHEN öğrenci learning path sayfasını açtığında, THE LearningPathSystem SHALL video önerilerini gerçek zamanlı olarak doğrular
2. WHEN VideoQualityValidator toplu video kontrolü yaptığında, THE VideoQualityValidator SHALL maksimum 5 saniye içinde sonuç döner
3. WHEN bir video doğrulama başarısız olduğunda, THE ResourceRecommendationEngine SHALL önbellekten (cache) alternatif video önerir
4. WHEN YouTubeIntegrationService API limitine ulaştığında, THE YouTubeIntegrationService SHALL fallback mekanizmasını devreye sokar
5. WHEN sistem video önerilerini güncellerken, THE LearningPathSystem SHALL kullanıcıya yükleme göstergesi gösterir
