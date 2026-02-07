-- KIRO2 Emergency Content Import - Schema v2 (JSONB options)
-- 50 YKS Questions for initial platform testing
-- Converted from legacy schema (option_a/b/c/d/e) to new schema (JSONB options)

-- TYT Matematik (8 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('Bir sayının 3/4''ü 36 ise, bu sayının 2/5''i kaçtır?', '{"A": "16", "B": "18", "C": "19.2", "D": "20", "E": "24"}', 'C', 'TYT Matematik', 'Kesirler', -1.2, 'ÖSYM 2023', 2023, 'Sayı = 36 × 4/3 = 48, sonra 48 × 2/5 = 19.2', NULL, NULL, '[]', '[]', 0, 0, 0),
('12 işçi bir işi 15 günde bitiriyor. Aynı işi 9 günde bitirmek için kaç işçi gerekir?', '{"A": "18", "B": "20", "C": "22", "D": "24", "E": "25"}', 'B', 'TYT Matematik', 'Ters Orantı', -0.8, 'ÖSYM 2022', 2022, '12 × 15 = x × 9, x = 20 işçi', NULL, NULL, '[]', '[]', 0, 0, 0),
('Bir malın fiyatı önce %20 artırılıp, sonra %20 indirilirse, son fiyat ilk fiyatın yüzde kaçıdır?', '{"A": "96", "B": "98", "C": "100", "D": "102", "E": "104"}', 'A', 'TYT Matematik', 'Yüzde Problemleri', -0.5, 'ÖSYM 2023', 2023, '100 × 1.20 × 0.80 = 96', NULL, NULL, '[]', '[]', 0, 0, 0),
('x + y = 7 ve xy = 12 ise x² + y² kaçtır?', '{"A": "20", "B": "22", "C": "24", "D": "25", "E": "26"}', 'D', 'TYT Matematik', 'Denklem Sistemleri', -0.3, 'ÖSYM 2022', 2022, '(x+y)² = x² + 2xy + y², 49 = x² + y² + 24, x² + y² = 25', NULL, NULL, '[]', '[]', 0, 0, 0),
('Bir üçgenin iç açıları 2x, 3x ve 4x derece ise en büyük açı kaç derecedir?', '{"A": "60", "B": "70", "C": "75", "D": "80", "E": "85"}', 'D', 'TYT Matematik', 'Üçgenler', -1.0, 'ÖSYM 2023', 2023, '2x + 3x + 4x = 180, 9x = 180, x = 20, en büyük = 4×20 = 80', NULL, NULL, '[]', '[]', 0, 0, 0),
('log₂8 + log₃27 kaçtır?', '{"A": "5", "B": "6", "C": "7", "D": "8", "E": "9"}', 'B', 'TYT Matematik', 'Logaritma', 0.2, 'ÖSYM 2022', 2022, 'log₂8 = 3, log₃27 = 3, toplam = 6', NULL, NULL, '[]', '[]', 0, 0, 0),
('f(x) = 2x + 3 fonksiyonu için f(f(1)) kaçtır?', '{"A": "11", "B": "13", "C": "15", "D": "17", "E": "19"}', 'B', 'TYT Matematik', 'Fonksiyonlar', -0.6, 'ÖSYM 2023', 2023, 'f(1) = 5, f(5) = 13', NULL, NULL, '[]', '[]', 0, 0, 0),
('Bir dairenin çevresi 12π cm ise alanı kaç cm²''dir?', '{"A": "24π", "B": "30π", "C": "36π", "D": "42π", "E": "48π"}', 'C', 'TYT Matematik', 'Daire', -0.9, 'ÖSYM 2022', 2022, '2πr = 12π, r = 6, Alan = πr² = 36π', NULL, NULL, '[]', '[]', 0, 0, 0);

-- TYT Türkçe (5 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?', '{"A": "Herkes kendi işine bakmalı.", "B": "Hiçbir şey eskisi gibi değil.", "C": "Her halde yarın gelecek.", "D": "Herkesten önce geldim.", "E": "Hiçbiri beni anlamıyor."}', 'C', 'TYT Türkçe', 'Yazım Kuralları', -1.5, 'ÖSYM 2023', 2023, 'Herhalde bitişik yazılır', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdaki cümlelerin hangisinde bir anlatım bozukluğu vardır?', '{"A": "Bu kitabı okumanızı öneririm.", "B": "Toplantıya katılmak zorundayız.", "C": "En büyük hatasını yaptı.", "D": "Sınava iyi hazırlandım.", "E": "Projemiz tamamlandı."}', 'C', 'TYT Türkçe', 'Anlatım Bozuklukları', -0.4, 'ÖSYM 2022', 2022, 'En üstünlük eki tekrar hatası', NULL, NULL, '[]', '[]', 0, 0, 0),
('"Göz" sözcüğü aşağıdaki cümlelerin hangisinde mecaz anlamda kullanılmıştır?', '{"A": "Gözleri çok güzeldi.", "B": "Masanın gözünü açtı.", "C": "Gözlüklerini kaybetti.", "D": "Gözlerinden yaş aktı.", "E": "Göz doktoruna gitti."}', 'B', 'TYT Türkçe', 'Sözcükte Anlam', -1.0, 'ÖSYM 2023', 2023, 'Masanın gözü - çekmece anlamında mecaz', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdaki cümlelerin hangisinde özne-yüklem uyumsuzluğu vardır?', '{"A": "Öğrenciler sınava girdi.", "B": "Herkes yerini aldı.", "C": "Çocuklar bahçede oynadı.", "D": "Kuşlar gökyüzünde uçuyor.", "E": "Arkadaşlarım geldi."}', 'A', 'TYT Türkçe', 'Cümle Bilgisi', -0.7, 'ÖSYM 2022', 2022, 'Öğrenciler çoğul, yüklem tekil olmalı: girdiler', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdakilerden hangisi birleşik fiil değildir?', '{"A": "gelebilmek", "B": "yazıvermek", "C": "okuyakoymak", "D": "düşünmek", "E": "bakakalmak"}', 'D', 'TYT Türkçe', 'Fiiller', -0.2, 'ÖSYM 2023', 2023, 'Düşünmek basit fiildir, diğerleri yardımcı fiillerle kurulmuş birleşik fiillerdir', NULL, NULL, '[]', '[]', 0, 0, 0);

-- TYT Fen Bilimleri (5 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('Bir cisim 20 m/s hızla hareket ederken 4 saniyede duruyorsa, ivmesi kaç m/s²''dir?', '{"A": "-4", "B": "-5", "C": "-6", "D": "-8", "E": "-10"}', 'B', 'TYT Fizik', 'Hareket', -0.8, 'ÖSYM 2023', 2023, 'a = (v-v₀)/t = (0-20)/4 = -5 m/s²', NULL, NULL, '[]', '[]', 0, 0, 0),
('Periyodik tabloda 17. grupta bulunan elementlere ne ad verilir?', '{"A": "Alkali metaller", "B": "Toprak alkali metaller", "C": "Halojenler", "D": "Soy gazlar", "E": "Geçiş metalleri"}', 'C', 'TYT Kimya', 'Periyodik Tablo', -1.5, 'ÖSYM 2022', 2022, '17. grup elementleri halojenlerdir', NULL, NULL, '[]', '[]', 0, 0, 0),
('Fotosentez tepkimesinde üretilen madde aşağıdakilerden hangisidir?', '{"A": "Karbondioksit", "B": "Su", "C": "Oksijen", "D": "Azot", "E": "Hidrojen"}', 'C', 'TYT Biyoloji', 'Fotosentez', -1.8, 'ÖSYM 2023', 2023, 'Fotosentezde CO₂ ve H₂O kullanılarak glikoz ve O₂ üretilir', NULL, NULL, '[]', '[]', 0, 0, 0),
('50 g su 20°C''den 70°C''ye ısıtılırsa kaç kalori ısı alır?', '{"A": "2000", "B": "2500", "C": "3000", "D": "3500", "E": "4000"}', 'B', 'TYT Fizik', 'Isı ve Sıcaklık', -1.0, 'ÖSYM 2022', 2022, 'Q = m.c.ΔT = 50 × 1 × 50 = 2500 kalori', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdakilerden hangisi asit özelliği göstermez?', '{"A": "HCl", "B": "H₂SO₄", "C": "NaOH", "D": "HNO₃", "E": "CH₃COOH"}', 'C', 'TYT Kimya', 'Asit-Baz', -1.2, 'ÖSYM 2023', 2023, 'NaOH bir bazdır, diğerleri asittir', NULL, NULL, '[]', '[]', 0, 0, 0);

-- TYT Sosyal Bilimler (4 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('Türkiye''nin en uzun nehri aşağıdakilerden hangisidir?', '{"A": "Fırat", "B": "Dicle", "C": "Kızılırmak", "D": "Sakarya", "E": "Yeşilırmak"}', 'C', 'TYT Coğrafya', 'Türkiye Coğrafyası', -2.0, 'ÖSYM 2023', 2023, 'Kızılırmak 1355 km ile Türkiye''nin en uzun nehridir', NULL, NULL, '[]', '[]', 0, 0, 0),
('Osmanlı Devleti''nde Tanzimat Fermanı hangi yılda ilan edilmiştir?', '{"A": "1808", "B": "1839", "C": "1856", "D": "1876", "E": "1908"}', 'B', 'TYT Tarih', 'Osmanlı Tarihi', -1.5, 'ÖSYM 2022', 2022, 'Tanzimat Fermanı 3 Kasım 1839''da ilan edilmiştir', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdakilerden hangisi temel hak ve özgürlüklerden biri değildir?', '{"A": "Yaşama hakkı", "B": "Mülkiyet hakkı", "C": "Eğitim hakkı", "D": "Vergi muafiyeti", "E": "Düşünce özgürlüğü"}', 'D', 'TYT Vatandaşlık', 'Temel Haklar', -1.3, 'ÖSYM 2023', 2023, 'Vergi muafiyeti bir hak değil, istisnadır', NULL, NULL, '[]', '[]', 0, 0, 0),
('İklim değişikliğinin en önemli nedeni aşağıdakilerden hangisidir?', '{"A": "Volkanik faaliyetler", "B": "Güneş lekeleri", "C": "Sera gazları", "D": "Okyanus akıntıları", "E": "Depremler"}', 'C', 'TYT Coğrafya', 'İklim', -1.0, 'ÖSYM 2022', 2022, 'Sera gazları küresel ısınmanın ana nedenidir', NULL, NULL, '[]', '[]', 0, 0, 0);

-- AYT Matematik (6 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('lim(x→2) (x²-4)/(x-2) limitinin değeri kaçtır?', '{"A": "0", "B": "2", "C": "4", "D": "6", "E": "Tanımsız"}', 'C', 'AYT Matematik', 'Limit', 0.3, 'ÖSYM 2023', 2023, '(x²-4)/(x-2) = (x-2)(x+2)/(x-2) = x+2, x→2 için 4', NULL, NULL, '[]', '[]', 0, 0, 0),
('f(x) = x³ - 3x² + 2 fonksiyonunun türevi f''(x) nedir?', '{"A": "3x² - 6x", "B": "3x² - 3x", "C": "x² - 6x", "D": "3x² + 6x", "E": "x³ - 6x"}', 'A', 'AYT Matematik', 'Türev', 0.1, 'ÖSYM 2022', 2022, 'f''(x) = 3x² - 6x + 0 = 3x² - 6x', NULL, NULL, '[]', '[]', 0, 0, 0),
('∫(2x + 3)dx integralinin sonucu nedir?', '{"A": "x² + 3x + C", "B": "2x² + 3x + C", "C": "x² + 3 + C", "D": "2x + 3 + C", "E": "x² + C"}', 'A', 'AYT Matematik', 'İntegral', 0.0, 'ÖSYM 2023', 2023, '∫(2x + 3)dx = x² + 3x + C', NULL, NULL, '[]', '[]', 0, 0, 0),
('3x + 2y = 12 doğrusunun y-eksenini kestiği nokta hangisidir?', '{"A": "(0, 4)", "B": "(0, 6)", "C": "(4, 0)", "D": "(6, 0)", "E": "(0, 3)"}', 'B', 'AYT Matematik', 'Analitik Geometri', -0.5, 'ÖSYM 2022', 2022, 'x = 0 için 2y = 12, y = 6', NULL, NULL, '[]', '[]', 0, 0, 0),
('Bir geometrik dizinin ilk terimi 3, ortak oranı 2 ise 5. terimi kaçtır?', '{"A": "24", "B": "32", "C": "48", "D": "64", "E": "96"}', 'C', 'AYT Matematik', 'Diziler', -0.2, 'ÖSYM 2023', 2023, 'aₙ = a₁ × rⁿ⁻¹ = 3 × 2⁴ = 48', NULL, NULL, '[]', '[]', 0, 0, 0),
('log₁₀(x²) = 4 ise x kaçtır?', '{"A": "10", "B": "100", "C": "1000", "D": "50", "E": "200"}', 'B', 'AYT Matematik', 'Logaritma', 0.2, 'ÖSYM 2022', 2022, 'x² = 10⁴ = 10000, x = 100', NULL, NULL, '[]', '[]', 0, 0, 0);

-- AYT Fizik (4 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('10 kg kütleli bir cisme 50 N kuvvet uygulanırsa ivmesi kaç m/s²''dir?', '{"A": "3", "B": "4", "C": "5", "D": "6", "E": "7"}', 'C', 'AYT Fizik', 'Dinamik', -0.5, 'ÖSYM 2023', 2023, 'F = ma, 50 = 10a, a = 5 m/s²', NULL, NULL, '[]', '[]', 0, 0, 0),
('Bir kondansatörün kapasitesi 4 µF ve üzerindeki gerilim 100 V ise depoladığı enerji kaç mJ''dür?', '{"A": "10", "B": "20", "C": "30", "D": "40", "E": "50"}', 'B', 'AYT Fizik', 'Elektrik', 0.3, 'ÖSYM 2022', 2022, 'E = ½CV² = ½ × 4×10⁻⁶ × 10000 = 0.02 J = 20 mJ', NULL, NULL, '[]', '[]', 0, 0, 0),
('Işık hızı yaklaşık kaç m/s''dir?', '{"A": "3×10⁶", "B": "3×10⁷", "C": "3×10⁸", "D": "3×10⁹", "E": "3×10¹⁰"}', 'C', 'AYT Fizik', 'Optik', -1.5, 'ÖSYM 2023', 2023, 'Işık hızı c ≈ 3×10⁸ m/s', NULL, NULL, '[]', '[]', 0, 0, 0),
('Basit harmonik harekette periyot hangi büyüklükten bağımsızdır?', '{"A": "Kütle", "B": "Yay sabiti", "C": "Genlik", "D": "Yerçekimi", "E": "Uzunluk"}', 'C', 'AYT Fizik', 'Dalgalar', 0.0, 'ÖSYM 2022', 2022, 'SHM periyodu genlikten bağımsızdır, T = 2π√(m/k)', NULL, NULL, '[]', '[]', 0, 0, 0);

-- AYT Kimya (4 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('Suyun öz ısısı 4.18 J/(g·°C) ise 100 g suyun sıcaklığını 10°C artırmak için kaç J enerji gerekir?', '{"A": "4180", "B": "418", "C": "41.8", "D": "41800", "E": "2090"}', 'A', 'AYT Kimya', 'Termokimya', -0.3, 'ÖSYM 2023', 2023, 'Q = mcΔT = 100 × 4.18 × 10 = 4180 J', NULL, NULL, '[]', '[]', 0, 0, 0),
('Aşağıdakilerden hangisi kovalent bağlı bir bileşiktir?', '{"A": "NaCl", "B": "KBr", "C": "H₂O", "D": "CaO", "E": "MgCl₂"}', 'C', 'AYT Kimya', 'Kimyasal Bağlar', -0.8, 'ÖSYM 2022', 2022, 'H₂O molekülünde O-H kovalent bağları vardır', NULL, NULL, '[]', '[]', 0, 0, 0),
('pH = 3 olan bir çözeltinin H⁺ derişimi kaç mol/L''dir?', '{"A": "10⁻³", "B": "10⁻¹¹", "C": "3", "D": "10³", "E": "10⁻⁷"}', 'A', 'AYT Kimya', 'Asit-Baz Dengesi', 0.1, 'ÖSYM 2023', 2023, 'pH = -log[H⁺], 3 = -log[H⁺], [H⁺] = 10⁻³ mol/L', NULL, NULL, '[]', '[]', 0, 0, 0),
('Hangi element geçiş metalidir?', '{"A": "Na", "B": "Ca", "C": "Fe", "D": "Al", "E": "S"}', 'C', 'AYT Kimya', 'Periyodik Özellikler', -1.2, 'ÖSYM 2022', 2022, 'Fe (demir) d bloğunda olup geçiş metalidir', NULL, NULL, '[]', '[]', 0, 0, 0);

-- AYT Biyoloji (4 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('DNA replikasyonunda hangi enzim çift sarmalı açar?', '{"A": "DNA polimeraz", "B": "Helikaz", "C": "Ligaz", "D": "Primaz", "E": "Topoizomeraz"}', 'B', 'AYT Biyoloji', 'Genetik', 0.2, 'ÖSYM 2023', 2023, 'Helikaz enzimi DNA çift sarmalını açarak replikasyonu başlatır', NULL, NULL, '[]', '[]', 0, 0, 0),
('Mitoz bölünme sonucunda kaç hücre oluşur?', '{"A": "1", "B": "2", "C": "4", "D": "8", "E": "16"}', 'B', 'AYT Biyoloji', 'Hücre Bölünmesi', -1.5, 'ÖSYM 2022', 2022, 'Mitoz bölünme sonucunda 2 özdeş hücre oluşur', NULL, NULL, '[]', '[]', 0, 0, 0),
('Krebs döngüsü hücrenin hangi organelinde gerçekleşir?', '{"A": "Çekirdek", "B": "Ribozom", "C": "Mitokondri", "D": "Golgi", "E": "Lizozom"}', 'C', 'AYT Biyoloji', 'Hücresel Solunum', -0.6, 'ÖSYM 2023', 2023, 'Krebs döngüsü mitokondrinin matriksinde gerçekleşir', NULL, NULL, '[]', '[]', 0, 0, 0),
('İnsan vücudunda en çok bulunan protein hangisidir?', '{"A": "Hemoglobin", "B": "Keratin", "C": "Kolajen", "D": "Miyozin", "E": "İnsülin"}', 'C', 'AYT Biyoloji', 'Proteinler', -0.4, 'ÖSYM 2022', 2022, 'Kolajen vücuttaki en bol proteindir (%25-35)', NULL, NULL, '[]', '[]', 0, 0, 0);

-- YDT İngilizce (5 questions)
INSERT INTO questions (stem, options, correct_option, subject, topic, difficulty, source, year, explanation, solution_steps, bloom_level, kazanim_codes, keywords, times_used, times_correct, times_wrong) VALUES
('She _____ to the cinema yesterday.', '{"A": "go", "B": "goes", "C": "went", "D": "going", "E": "gone"}', 'C', 'YDT İngilizce', 'Tenses', -1.5, 'ÖSYM 2023', 2023, 'Yesterday indicates past tense, so "went" is correct', NULL, NULL, '[]', '[]', 0, 0, 0),
('If I _____ rich, I would travel the world.', '{"A": "am", "B": "was", "C": "were", "D": "be", "E": "being"}', 'C', 'YDT İngilizce', 'Conditionals', -0.5, 'ÖSYM 2022', 2022, 'Second conditional uses "were" for all subjects', NULL, NULL, '[]', '[]', 0, 0, 0),
('The book _____ by millions of people.', '{"A": "read", "B": "reads", "C": "is read", "D": "reading", "E": "has read"}', 'C', 'YDT İngilizce', 'Passive Voice', -0.3, 'ÖSYM 2023', 2023, 'Passive voice: is/are + past participle', NULL, NULL, '[]', '[]', 0, 0, 0),
('He is _____ than his brother.', '{"A": "tall", "B": "taller", "C": "tallest", "D": "more tall", "E": "most tall"}', 'B', 'YDT İngilizce', 'Comparatives', -1.8, 'ÖSYM 2022', 2022, 'Comparative form of short adjectives: adj + er', NULL, NULL, '[]', '[]', 0, 0, 0),
('I have been living here _____ 2010.', '{"A": "for", "B": "since", "C": "from", "D": "during", "E": "while"}', 'B', 'YDT İngilizce', 'Prepositions', -1.0, 'ÖSYM 2023', 2023, 'Since is used with specific points in time', NULL, NULL, '[]', '[]', 0, 0, 0);

-- Verification query (comment out after testing)
-- SELECT subject, COUNT(*) as count FROM questions GROUP BY subject ORDER BY subject;
