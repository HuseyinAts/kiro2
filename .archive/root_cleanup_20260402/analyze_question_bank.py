#!/usr/bin/env python3
"""KIRO2 Soru Bankası Detaylı Analiz Raporu"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from typing import Dict, List, Any

def connect_db():
    """PostgreSQL veritabanına bağlan"""
    return psycopg2.connect(
        host="localhost",
        port=5434,
        database="kiro2",
        user="postgres",
        cursor_factory=RealDictCursor
    )

def get_total_questions(conn) -> Dict[str, Any]:
    """Toplam soru sayısı ve genel durum"""
    with conn.cursor() as cur:
        # Toplam soru sayısı
        cur.execute("SELECT COUNT(*) as total FROM questions")
        total = cur.fetchone()['total']
        
        # Aktif/Pasif durumu (aktif sütunu kullanılıyor)
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE aktif = true) as active_count,
                COUNT(*) FILTER (WHERE aktif = false) as inactive_count,
                COUNT(*) FILTER (WHERE aktif IS NULL) as null_status
            FROM questions
        """)
        status = cur.fetchone()
        
        # Son eklenen sorular
        cur.execute("""
            SELECT 
                MIN(created_at) as first_question,
                MAX(created_at) as last_question
            FROM questions
            WHERE created_at IS NOT NULL
        """)
        dates = cur.fetchone()
        
        return {
            'total': total,
            'active': status['active_count'] if status else 0,
            'inactive': status['inactive_count'] if status else 0,
            'null_status': status['null_status'] if status else 0,
            'first_added': dates['first_question'] if dates else None,
            'last_added': dates['last_question'] if dates else None
        }

def get_exam_type_distribution(conn) -> List[Dict]:
    """Sınav tiplerine göre dağılım"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COALESCE(exam_type, 'Belirtilmemiş') as exam_type,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM questions), 0), 2) as percentage
            FROM questions
            GROUP BY exam_type
            ORDER BY count DESC
        """)
        return cur.fetchall()

def get_subject_distribution(conn) -> List[Dict]:
    """Derslere göre dağılım"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COALESCE(subject_area, 'Belirtilmemiş') as subject,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM questions), 0), 2) as percentage
            FROM questions
            GROUP BY subject_area
            ORDER BY count DESC
        """)
        return cur.fetchall()

def get_difficulty_distribution(conn) -> List[Dict]:
    """Zorluk seviyelerine göre dağılım"""
    with conn.cursor() as cur:
        # Basit bir yaklaşım kullanalım
        cur.execute("""
            SELECT 
                difficulty,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM questions), 0), 2) as percentage
            FROM questions
            GROUP BY difficulty
            ORDER BY difficulty
        """)
        return cur.fetchall()

def get_irt_parameters(conn) -> Dict[str, Any]:
    """IRT parametreleri analizi"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE irt_discrimination IS NOT NULL) as has_discrimination,
                COUNT(*) FILTER (WHERE irt_difficulty IS NOT NULL) as has_difficulty,
                COUNT(*) FILTER (WHERE irt_guessing IS NOT NULL) as has_guessing,
                AVG(irt_discrimination) as avg_discrimination,
                AVG(irt_difficulty) as avg_difficulty,
                AVG(irt_guessing) as avg_guessing,
                MIN(irt_discrimination) as min_discrimination,
                MAX(irt_discrimination) as max_discrimination
            FROM questions
        """)
        return cur.fetchone()

def get_recent_questions(conn, limit=10) -> List[Dict]:
    """Son eklenen sorular"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                id,
                question_text,
                exam_type,
                subject_area,
                difficulty,
                created_at,
                CASE 
                    WHEN LENGTH(question_text) > 100 
                    THEN SUBSTRING(question_text, 1, 100) || '...'
                    ELSE question_text
                END as question_preview
            FROM questions
            WHERE created_at IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()

def get_content_quality(conn) -> Dict[str, Any]:
    """İçerik kalitesi analizi"""
    with conn.cursor() as cur:
        # Boş veya eksik içerik kontrolü
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE question_text IS NULL OR question_text = '') as empty_questions,
                COUNT(*) FILTER (WHERE LENGTH(question_text) < 10) as too_short,
                COUNT(*) FILTER (WHERE correct_answer IS NULL OR correct_answer = '') as no_correct_answer,
                COUNT(*) FILTER (WHERE option_a IS NULL OR option_a = '') as no_option_a,
                COUNT(*) FILTER (WHERE option_b IS NULL OR option_b = '') as no_option_b,
                COUNT(*) FILTER (WHERE explanation IS NULL OR explanation = '') as no_explanation,
                COUNT(*) FILTER (WHERE subject_area IS NULL OR subject_area = '') as no_subject,
                COUNT(*) FILTER (WHERE exam_type IS NULL OR exam_type = '') as no_exam_type
            FROM questions
        """)
        return cur.fetchone()

def get_combined_distribution(conn) -> List[Dict]:
    """Sınav tipi ve ders kombinasyonu dağılımı"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COALESCE(exam_type, 'Belirtilmemiş') as exam_type,
                COALESCE(subject_area, 'Belirtilmemiş') as subject,
                COUNT(*) as count
            FROM questions
            GROUP BY exam_type, subject_area
            HAVING COUNT(*) > 0
            ORDER BY exam_type, count DESC
        """)
        return cur.fetchall()

def generate_report(data: Dict[str, Any]) -> str:
    """Markdown formatında rapor oluştur"""
    report = []
    
    report.append("# KIRO2 Soru Bankası Detaylı Analiz Raporu")
    report.append(f"\n📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    report.append("\n---\n")
    
    # 1. Genel Durum
    total = data['total_stats']
    report.append("## 📊 1. Genel Durum")
    report.append(f"\n### Toplam Soru Sayısı: **{total['total']:,}**")
    
    if total['total'] == 0:
        report.append("\n⚠️ **KRİTİK DURUM:** Veritabanında hiç soru bulunmamaktadır!")
        report.append("\nPlatformun çalışması için ACİL olarak soru yüklenmesi gerekmektedir.")
    else:
        report.append(f"- ✅ Aktif: {total['active']:,} soru")
        report.append(f"- ❌ Pasif: {total['inactive']:,} soru")
        if total['null_status'] > 0:
            report.append(f"- ⚠️ Durumu belirsiz: {total['null_status']:,} soru")
        
        if total['first_added']:
            report.append(f"\n📆 İlk soru: {total['first_added'].strftime('%d.%m.%Y') if total['first_added'] else 'Bilinmiyor'}")
        if total['last_added']:
            report.append(f"📆 Son soru: {total['last_added'].strftime('%d.%m.%Y %H:%M') if total['last_added'] else 'Bilinmiyor'}")
    
    # 2. Sınav Tipi Dağılımı
    report.append("\n## 🎯 2. Sınav Tiplerine Göre Dağılım")
    
    if data['exam_types']:
        report.append("\n| Sınav Tipi | Soru Sayısı | Yüzde |")
        report.append("|------------|-------------|--------|")
        for exam in data['exam_types']:
            report.append(f"| {exam['exam_type']} | {exam['count']:,} | %{exam['percentage']} |")
    else:
        report.append("\n⚠️ Sınav tipi dağılımı bulunamadı.")
    
    # 3. Ders Dağılımı
    report.append("\n## 📚 3. Derslere Göre Dağılım")
    
    if data['subjects']:
        report.append("\n| Ders | Soru Sayısı | Yüzde |")
        report.append("|------|-------------|--------|")
        for subject in data['subjects'][:15]:  # İlk 15 ders
            report.append(f"| {subject['subject']} | {subject['count']:,} | %{subject['percentage']} |")
        
        if len(data['subjects']) > 15:
            report.append(f"\n*Ve {len(data['subjects']) - 15} ders daha...*")
    else:
        report.append("\n⚠️ Ders dağılımı bulunamadı.")
    
    # 4. Zorluk Seviyesi Dağılımı
    report.append("\n## 📈 4. Zorluk Seviyeleri")
    
    if data['difficulties']:
        report.append("\n| Zorluk | Soru Sayısı | Yüzde |")
        report.append("|--------|-------------|--------|")
        for diff in data['difficulties'][:20]:  # İlk 20 değer
            difficulty_val = diff['difficulty'] if diff['difficulty'] else 'Belirtilmemiş'
            report.append(f"| {difficulty_val} | {diff['count']:,} | %{diff['percentage']} |")
        
        if len(data['difficulties']) > 20:
            report.append(f"\n*Ve {len(data['difficulties']) - 20} zorluk değeri daha...*")
    else:
        report.append("\n⚠️ Zorluk seviyesi dağılımı bulunamadı.")
    
    # 5. IRT Parametreleri
    report.append("\n## 🔬 5. IRT Parametreleri Analizi")
    
    irt = data['irt_params']
    if irt and total['total'] > 0:
        report.append(f"\n- **Discrimination parametresi olan:** {irt['has_discrimination']:,} soru ({irt['has_discrimination']*100//total['total']}%)")
        report.append(f"- **Difficulty parametresi olan:** {irt['has_difficulty']:,} soru ({irt['has_difficulty']*100//total['total']}%)")
        report.append(f"- **Guessing parametresi olan:** {irt['has_guessing']:,} soru ({irt['has_guessing']*100//total['total']}%)")
        
        if irt['avg_discrimination']:
            report.append(f"\n### Ortalama Değerler:")
            report.append(f"- Discrimination: {irt['avg_discrimination']:.3f}")
            report.append(f"- Difficulty: {irt['avg_difficulty']:.3f}" if irt['avg_difficulty'] else "- Difficulty: N/A")
            report.append(f"- Guessing: {irt['avg_guessing']:.3f}" if irt['avg_guessing'] else "- Guessing: N/A")
    else:
        report.append("\n⚠️ IRT parametreleri henüz ayarlanmamış.")
    
    # 6. İçerik Kalitesi
    report.append("\n## 🔍 6. İçerik Kalitesi Analizi")
    
    quality = data['content_quality']
    if quality and total['total'] > 0:
        problems = []
        if quality['empty_questions'] > 0:
            problems.append(f"- 🚫 Boş soru metni: {quality['empty_questions']:,} soru")
        if quality['too_short'] > 0:
            problems.append(f"- ⚠️ Çok kısa soru metni (<10 karakter): {quality['too_short']:,} soru")
        if quality['no_correct_answer'] > 0:
            problems.append(f"- ❌ Doğru cevap eksik: {quality['no_correct_answer']:,} soru")
        if quality['no_option_a'] > 0:
            problems.append(f"- ❌ A seçeneği eksik: {quality['no_option_a']:,} soru")
        if quality['no_option_b'] > 0:
            problems.append(f"- ❌ B seçeneği eksik: {quality['no_option_b']:,} soru")
        if quality['no_explanation'] > 0:
            problems.append(f"- 📝 Açıklama eksik: {quality['no_explanation']:,} soru")
        if quality['no_subject'] > 0:
            problems.append(f"- 📚 Ders bilgisi eksik: {quality['no_subject']:,} soru")
        if quality['no_exam_type'] > 0:
            problems.append(f"- 🎯 Sınav tipi eksik: {quality['no_exam_type']:,} soru")
        
        if problems:
            report.append("\n### Eksiklikler:")
            report.extend(problems)
        else:
            report.append("\n✅ Tüm sorular tam ve eksiksiz görünüyor.")
    
    # 7. Son Eklenen Sorular
    if data['recent_questions']:
        report.append("\n## 📝 7. Son Eklenen Sorular")
        report.append("\n| Tarih | Sınav | Ders | Zorluk | Soru Önizleme |")
        report.append("|-------|-------|------|--------|---------------|")
        
        for q in data['recent_questions'][:5]:
            date = q['created_at'].strftime('%d.%m.%Y') if q['created_at'] else 'N/A'
            exam = q['exam_type'] or 'N/A'
            subj = q['subject_area'] or 'N/A'
            diff = f"{q['difficulty']}" if q['difficulty'] else 'N/A'
            preview = q['question_preview'].replace('\n', ' ').replace('|', '\\|') if q['question_preview'] else 'N/A'
            report.append(f"| {date} | {exam} | {subj} | {diff} | {preview[:50]}... |")
    
    # 8. Kombinasyon Analizi
    report.append("\n## 🔄 8. Sınav-Ders Kombinasyon Dağılımı")
    
    combined = data['combined_dist']
    if combined:
        # Sınav tipine göre grupla
        exam_groups = {}
        for item in combined:
            if item['exam_type'] not in exam_groups:
                exam_groups[item['exam_type']] = []
            exam_groups[item['exam_type']].append(item)
        
        for exam_type, items in list(exam_groups.items())[:3]:  # İlk 3 sınav tipi
            report.append(f"\n### {exam_type}")
            report.append("| Ders | Soru Sayısı |")
            report.append("|------|-------------|")
            for item in items[:5]:  # Her sınav tipi için ilk 5 ders
                report.append(f"| {item['subject']} | {item['count']:,} |")
    
    # 9. Problemler ve Öneriler
    report.append("\n## ⚠️ 9. Tespit Edilen Problemler")
    
    problems = []
    
    if total['total'] < 50:
        problems.append("🔴 **KRİTİK:** Toplam soru sayısı 50'nin altında! Platform kullanılamaz durumda.")
    elif total['total'] < 500:
        problems.append("🟠 **UYARI:** Soru sayısı yetersiz (500'ün altında). Daha fazla soru eklenmeli.")
    elif total['total'] < 2500:
        problems.append("🟡 **BİLGİ:** Hedef soru sayısına (2500+) ulaşmak için daha fazla içerik gerekli.")
    
    # Sınav tipi eksiklikleri
    if data['exam_types']:
        for exam in ['TYT', 'AYT', 'YDT']:
            exam_data = next((e for e in data['exam_types'] if e['exam_type'] == exam), None)
            if not exam_data or exam_data['count'] < 100:
                problems.append(f"📚 {exam} soru sayısı yetersiz")
    
    # IRT parametreleri eksikliği
    if irt and irt['has_discrimination'] < total['total'] * 0.5:
        problems.append("📊 IRT parametreleri çoğu soru için eksik")
    
    # Zorluk dağılımı kontrolü kaldırıldı (şu an farklı formatta)
    
    if problems:
        for problem in problems:
            report.append(f"- {problem}")
    else:
        report.append("\n✅ Önemli bir problem tespit edilmedi.")
    
    # 10. Öneriler
    report.append("\n## 💡 10. Öneriler ve Eylem Planı")
    
    if total['total'] < 50:
        report.append("\n### 🚨 ACİL EYLEM GEREKLİ:")
        report.append("1. **Hemen 50+ soru yükle** - `emergency_content.sql` veya `load_questions.py` kullan")
        report.append("2. **OSYM PDF'lerini işle** - `/osym` klasöründeki PDF'leri OCR ile tara")
        report.append("3. **Hazır veri setlerini kullan** - Mevcut JSON/CSV dosyalarını içe aktar")
        report.append("4. **Manuel soru girişi** - Admin panelinden hızlı soru ekleme")
    elif total['total'] < 500:
        report.append("\n### 📋 Öncelikli Görevler:")
        report.append("1. **Eksik sınav tiplerini tamamla** - Özellikle az olan sınav tiplerini")
        report.append("2. **Ders çeşitliliğini artır** - Tüm YKS derslerini kapsa")
        report.append("3. **Zorluk dengesi kur** - Her seviyeden soru ekle")
        report.append("4. **IRT kalibrasyonu yap** - Parametreleri hesapla")
    else:
        report.append("\n### 🎯 İyileştirme Önerileri:")
        report.append("1. **Kalite kontrolü** - Eksik açıklamaları tamamla")
        report.append("2. **IRT optimizasyonu** - Tüm sorular için parametre hesapla")
        report.append("3. **İçerik zenginleştirme** - Görsel ve formül desteği ekle")
        report.append("4. **Performans analizi** - Öğrenci başarı verilerini değerlendir")
    
    report.append("\n---")
    report.append(f"\n*Rapor {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} tarihinde oluşturuldu.*")
    
    return "\n".join(report)

def main():
    """Ana fonksiyon"""
    import sys
    import io
    
    # Windows terminal encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    try:
        print("KIRO2 veritabanına bağlanılıyor...")
        conn = connect_db()
        
        print("Veriler toplanıyor...")
        data = {
            'total_stats': get_total_questions(conn),
            'exam_types': get_exam_type_distribution(conn),
            'subjects': get_subject_distribution(conn),
            'difficulties': get_difficulty_distribution(conn),
            'irt_params': get_irt_parameters(conn),
            'content_quality': get_content_quality(conn),
            'recent_questions': get_recent_questions(conn),
            'combined_dist': get_combined_distribution(conn)
        }
        
        # Rapor oluştur
        print("Rapor hazırlanıyor...")
        report = generate_report(data)
        
        # Raporu dosyaya kaydet
        report_file = f"KIRO2_SORU_BANKASI_RAPOR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Konsola da yazdır
        print("\n" + "="*80)
        print(report)
        print("="*80)
        
        print(f"\nRapor başarıyla oluşturuldu: {report_file}")
        
        conn.close()
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()