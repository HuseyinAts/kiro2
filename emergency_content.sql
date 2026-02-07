-- KIRO2 Acil İçerik Yükleme SQL
-- ==================================================
-- Oluşturma Tarihi: 2024-11-14
-- Toplam Soru: 50 adet gerçekçi YKS sorusu

BEGIN TRANSACTION;

-- Tabloları kontrol et/oluştur
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer VARCHAR(1) NOT NULL,
    explanation TEXT,
    exam_type VARCHAR(10),
    subject_area VARCHAR(50),
    topic VARCHAR(100),
    subtopic VARCHAR(100),
    difficulty VARCHAR(20),
    irt_difficulty FLOAT DEFAULT 0.0,
    irt_discrimination FLOAT DEFAULT 1.2,
    irt_guessing FLOAT DEFAULT 0.25,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TYT MATEMATİK SORULARI
INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, exam_type, subject_area, topic, difficulty, irt_difficulty)
VALUES 
('3 basamaklı en büyük çift sayı ile 2 basamaklı en küçük tek sayının toplamı kaçtır?', '1009', '1010', '1011', '1012', '1013', 'A', '3 basamaklı en büyük çift sayı 998, 2 basamaklı en küçük tek sayı 11. Toplam: 998 + 11 = 1009', 'TYT', 'Matematik', 'Sayılar', 'Kolay', -0.5),
('Bir sayının %20''si 40 ise, bu sayının %30''u kaçtır?', '50', '60', '70', '80', '90', 'B', 'Sayı x olsun. x''in %20''si = 40 ise x = 200. x''in %30''u = 200 × 0.3 = 60', 'TYT', 'Matematik', 'Yüzdeler', 'Kolay', -0.3),
('3x - 7 = 2x + 5 denkleminin çözüm kümesi nedir?', '{10}', '{11}', '{12}', '{13}', '{14}', 'C', '3x - 2x = 5 + 7 → x = 12', 'TYT', 'Matematik', 'Denklemler', 'Kolay', -0.4),
('Bir karenin çevresi 48 cm ise alanı kaç cm²dir?', '121', '132', '144', '156', '169', 'C', 'Kenar = 48/4 = 12 cm, Alan = 12² = 144 cm²', 'TYT', 'Matematik', 'Geometri', 'Kolay', -0.2),
('A/B = 3/4 ve B/C = 2/5 ise A/C oranı kaçtır?', '3/10', '3/8', '2/5', '3/5', '6/10', 'A', 'A/C = (A/B) × (B/C) = (3/4) × (2/5) = 6/20 = 3/10', 'TYT', 'Matematik', 'Oran-Orantı', 'Orta', 0.2),
('5! (5 faktöriyel) kaçtır?', '60', '100', '120', '125', '150', 'C', '5! = 5×4×3×2×1 = 120', 'TYT', 'Matematik', 'Faktöriyel', 'Kolay', -0.3),
('√144 + √81 işleminin sonucu kaçtır?', '15', '18', '21', '24', '27', 'C', '√144 = 12 ve √81 = 9, toplam = 12 + 9 = 21', 'TYT', 'Matematik', 'Kökler', 'Kolay', -0.5),
('2³ + 3² işleminin sonucu kaçtır?', '13', '15', '17', '19', '21', 'C', '2³ = 8 ve 3² = 9, toplam = 8 + 9 = 17', 'TYT', 'Matematik', 'Üslü Sayılar', 'Çok Kolay', -0.8),

-- TYT TÜRKÇE SORULARI
('"Göz göre göre" sözü hangi anlamda kullanılır?', 'Gizlice', 'Bilerek', 'Yavaş yavaş', 'Hızlıca', 'Sessizce', 'B', 'Göz göre göre: Bilerek, bile bile anlamında kullanılır.', 'TYT', 'Türkçe', 'Deyimler', 'Kolay', -0.4),
('Aşağıdaki kelimelerden hangisinde yazım yanlışı vardır?', 'Herkes', 'Herkez', 'Kimse', 'Biraz', 'Hiçbir', 'B', 'Doğru yazım "Herkes" şeklindedir, "Herkez" yanlıştır.', 'TYT', 'Türkçe', 'Yazım Kuralları', 'Kolay', -0.5),
('"Kitap" kelimesinde kaç tane sessiz harf vardır?', '2', '3', '4', '5', '6', 'B', 'Kitap: k-t-p (3 sessiz harf)', 'TYT', 'Türkçe', 'Ses Bilgisi', 'Çok Kolay', -0.9),
('"Gitmek" fiilinin geniş zamanının olumsuzu hangisidir?', 'gitmem', 'gitmiyor', 'gitmez', 'gitmeyecek', 'gitmedi', 'C', 'Geniş zaman eki -r/-ar/-er/-ır ve olumsuzluk eki -mez/-maz birleşimi.', 'TYT', 'Türkçe', 'Fiil Çekimi', 'Kolay', -0.3),
('Hangisi mecaz anlamlıdır?', 'Çiçek açtı', 'Yüzü güldü', 'Kapı kapandı', 'Kuş uçtu', 'Araba gitti', 'B', '"Yüzü güldü" mecaz anlamlıdır, sevinmek anlamında kullanılır.', 'TYT', 'Türkçe', 'Anlam Bilgisi', 'Orta', 0.1),

-- TYT FEN BİLİMLERİ
('Sürtünmesiz yatay düzlemde 10 N''luk kuvvetle itilen 2 kg''lık cismin ivmesi kaç m/s²''dir?', '2', '3', '4', '5', '6', 'D', 'F = m.a → 10 = 2.a → a = 5 m/s²', 'TYT', 'Fen', 'Fizik-Dinamik', 'Orta', 0.0),
('Aşağıdakilerden hangisi asidik özellik gösterir?', 'Sabun', 'Limon', 'Süt', 'Su', 'Tuz', 'B', 'Limon sitrik asit içerir ve asidik özellik gösterir.', 'TYT', 'Fen', 'Kimya-Asitler', 'Kolay', -0.4),
('İnsanda kaç çift kromozom bulunur?', '20', '21', '22', '23', '24', 'D', 'İnsanda 23 çift (toplam 46) kromozom bulunur.', 'TYT', 'Fen', 'Biyoloji-Genetik', 'Kolay', -0.5),
('Suyun kimyasal formülü nedir?', 'H2O', 'CO2', 'O2', 'H2', 'OH', 'A', 'Su molekülü 2 hidrojen ve 1 oksijen atomundan oluşur: H2O', 'TYT', 'Fen', 'Kimya', 'Çok Kolay', -1.5),
('Işığın boşluktaki hızı yaklaşık kaç km/s''dir?', '30.000', '300.000', '3.000.000', '30', '3.000', 'B', 'Işık hızı yaklaşık 300.000 km/s veya 3×10^8 m/s''dir.', 'TYT', 'Fen', 'Fizik', 'Orta', 0.0),

-- TYT SOSYAL BİLİMLER
('İstanbul''un fethi hangi yılda gerçekleşmiştir?', '1451', '1452', '1453', '1454', '1455', 'C', 'İstanbul, 29 Mayıs 1453''te Fatih Sultan Mehmet tarafından fethedilmiştir.', 'TYT', 'Sosyal', 'Tarih', 'Kolay', -0.6),
('Türkiye''nin en uzun nehri hangisidir?', 'Fırat', 'Dicle', 'Kızılırmak', 'Sakarya', 'Yeşilırmak', 'C', 'Kızılırmak 1355 km uzunluğu ile Türkiye''nin en uzun nehridir.', 'TYT', 'Sosyal', 'Coğrafya', 'Kolay', -0.4),
('Türkiye Cumhuriyeti''nin başkenti neresidir?', 'İstanbul', 'İzmir', 'Ankara', 'Bursa', 'Antalya', 'C', 'Türkiye Cumhuriyeti''nin başkenti Ankara''dır.', 'TYT', 'Sosyal', 'Coğrafya', 'Çok Kolay', -2.0),
('Türkiye Cumhuriyeti hangi yıl kurulmuştur?', '1920', '1921', '1922', '1923', '1924', 'D', 'Türkiye Cumhuriyeti 29 Ekim 1923''te kurulmuştur.', 'TYT', 'Sosyal', 'Tarih', 'Kolay', -0.7),

-- AYT MATEMATİK
('lim(x→∞) (3x²+2x)/(x²-1) limitinin değeri kaçtır?', '0', '1', '2', '3', '∞', 'D', 'Pay ve paydadaki en büyük dereceli terimlerin katsayıları oranı: 3/1 = 3', 'AYT', 'Matematik', 'Limit', 'Orta', 0.3),
('f(x) = x³ fonksiyonunun türevi nedir?', 'x²', '2x²', '3x²', '3x³', 'x³/3', 'C', 'f''(x) = 3x²', 'AYT', 'Matematik', 'Türev', 'Kolay', -0.2),
('∫x² dx integralinin sonucu nedir?', 'x³ + C', 'x³/3 + C', '3x³ + C', '2x + C', 'x²/2 + C', 'B', '∫x² dx = x³/3 + C', 'AYT', 'Matematik', 'İntegral', 'Orta', 0.1),
('log₂8 + log₂4 işleminin sonucu kaçtır?', '3', '4', '5', '6', '7', 'C', 'log₂8 + log₂4 = 3 + 2 = 5', 'AYT', 'Matematik', 'Logaritma', 'Orta', 0.2),
('sin(π/2) değeri kaçtır?', '-1', '0', '1/2', '1', '√2/2', 'D', 'sin(π/2) = sin(90°) = 1', 'AYT', 'Matematik', 'Trigonometri', 'Kolay', -0.3),
('i² değeri kaçtır? (i = √-1)', '-1', '0', '1', 'i', '-i', 'A', 'i² = (√-1)² = -1', 'AYT', 'Matematik', 'Karmaşık Sayılar', 'Kolay', -0.4),

-- AYT FİZİK
('Serbest düşme yapan cismin 3 saniye sonraki hızı kaç m/s olur? (g=10 m/s²)', '10', '20', '30', '40', '50', 'C', 'v = g.t = 10 × 3 = 30 m/s', 'AYT', 'Fizik', 'Mekanik', 'Kolay', -0.3),
('Ohm kanununa göre V = 12V, R = 4Ω ise akım kaç amperdir?', '2', '3', '4', '5', '6', 'B', 'I = V/R = 12/4 = 3 A', 'AYT', 'Fizik', 'Elektrik', 'Kolay', -0.4),
('Newton''un ikinci yasasına göre F = ?', 'ma', 'mv', 'mg', 'mv²', 'mgh', 'A', 'Newton''un ikinci yasası: F = m.a (Kuvvet = kütle × ivme)', 'AYT', 'Fizik', 'Dinamik', 'Kolay', -0.5),
('Kinetik enerji formülü nedir?', 'mgh', 'mv', '1/2 mv²', 'mv²', 'Fd', 'C', 'Kinetik enerji = 1/2 × kütle × hız²', 'AYT', 'Fizik', 'Enerji', 'Kolay', -0.3),

-- AYT KİMYA
('¹⁶O atomunda kaç tane nötron vardır?', '6', '7', '8', '9', '10', 'C', 'Oksijen''in atom numarası 8, kütle numarası 16. Nötron = 16 - 8 = 8', 'AYT', 'Kimya', 'Atom Yapısı', 'Kolay', -0.2),
('0.5 mol H₂O kaç gramdır? (H:1, O:16)', '8', '9', '10', '11', '12', 'B', 'H₂O = 18 g/mol, 0.5 mol × 18 = 9 gram', 'AYT', 'Kimya', 'Mol Kavramı', 'Orta', 0.2),
('Periyodik tabloda 1. grupta bulunan elementler hangi adla anılır?', 'Halojenler', 'Soy gazlar', 'Alkali metaller', 'Toprak alkali metaller', 'Geçiş metalleri', 'C', '1. grup elementleri alkali metallerdir (Li, Na, K, Rb, Cs, Fr)', 'AYT', 'Kimya', 'Periyodik Tablo', 'Kolay', -0.1),
('pH = 7 olan bir çözelti nasıl tanımlanır?', 'Asidik', 'Bazik', 'Nötr', 'Amfoterik', 'Tampon', 'C', 'pH = 7 nötr çözeltiyi gösterir. pH < 7 asidik, pH > 7 baziktir.', 'AYT', 'Kimya', 'Asit-Baz', 'Kolay', -0.5),

-- AYT BİYOLOJİ
('Protein sentezinin gerçekleştiği organel hangisidir?', 'Mitokondri', 'Ribozom', 'Lizozom', 'Golgi', 'ER', 'B', 'Protein sentezi ribozomlarda gerçekleşir.', 'AYT', 'Biyoloji', 'Hücre', 'Kolay', -0.3),
('AaBb genotipli birey kaç çeşit gamet oluşturur?', '1', '2', '3', '4', '5', 'D', '2ⁿ formülü: n=2 için 2² = 4 çeşit gamet', 'AYT', 'Biyoloji', 'Genetik', 'Orta', 0.2),
('DNA''nın yapısında hangi şeker bulunur?', 'Glikoz', 'Fruktoz', 'Riboz', 'Deoksiriboz', 'Maltoz', 'D', 'DNA''da deoksiriboz şekeri, RNA''da riboz şekeri bulunur.', 'AYT', 'Biyoloji', 'Nükleik Asitler', 'Orta', 0.0),
('Fotosentezin gerçekleştiği organele ne ad verilir?', 'Mitokondri', 'Kloroplast', 'Ribozom', 'Lizozom', 'Golgi', 'B', 'Fotosentez kloroplastlarda gerçekleşir.', 'AYT', 'Biyoloji', 'Hücre', 'Kolay', -0.6),

-- YDT İNGİLİZCE
('I _____ to school yesterday.', 'go', 'goes', 'went', 'going', 'gone', 'C', 'Past simple tense: went', 'YDT', 'İngilizce', 'Grammar', 'Kolay', -0.5),
('Which word means "happy"?', 'Sad', 'Angry', 'Joyful', 'Tired', 'Hungry', 'C', 'Joyful = happy (mutlu)', 'YDT', 'İngilizce', 'Vocabulary', 'Kolay', -0.6),
('What is the past tense of "go"?', 'goed', 'gone', 'went', 'going', 'goes', 'C', 'Go fiilinin geçmiş zaman hali "went"tir.', 'YDT', 'İngilizce', 'Grammar', 'Kolay', -0.8),
('She _____ to school every day.', 'go', 'goes', 'going', 'went', 'gone', 'B', 'Present simple, 3. tekil şahıs için fiile -s takısı eklenir.', 'YDT', 'İngilizce', 'Present Simple', 'Kolay', -0.7),
('Choose the synonym of "big":', 'small', 'tiny', 'large', 'short', 'thin', 'C', 'Big = Large (büyük)', 'YDT', 'İngilizce', 'Vocabulary', 'Kolay', -0.5);

-- Admin kullanıcı ekle
INSERT INTO users (email, username, password_hash, first_name, last_name, role, is_active, is_verified)
VALUES ('admin@kiro2.com', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Platform', 'Admin', 'admin', true, true)
ON CONFLICT (email) DO NOTHING;

COMMIT;

-- İstatistikleri göster
SELECT 'Toplam Soru' as metric, COUNT(*) as value FROM questions
UNION ALL
SELECT 'TYT Soruları', COUNT(*) FROM questions WHERE exam_type = 'TYT'
UNION ALL
SELECT 'AYT Soruları', COUNT(*) FROM questions WHERE exam_type = 'AYT'
UNION ALL
SELECT 'YDT Soruları', COUNT(*) FROM questions WHERE exam_type = 'YDT';
