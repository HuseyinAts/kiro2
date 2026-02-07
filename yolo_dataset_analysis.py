#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 YOLO Dataset Comprehensive Analysis
==========================================
Bu script YOLO veri setini detaylı analiz eder ve JSON raporu oluşturur.
"""

import os
import json
from collections import defaultdict
from pathlib import Path
import re

# Sınıf eşlemesi (data.yaml'dan)
CLASS_NAMES = {
    0: 'soru',      # Soru
    1: 'konu',      # Konu başlığı
    2: 'cevaplar',  # Cevaplar
    3: 'test_no',   # Test numarası
    4: 'sayfa',     # Sayfa göstergesi
    5: 'cozum',     # Çözüm
    6: 'kitap'      # Kitap tanımlayıcı
}

# Yayınevi eşleştirmesi
PUBLISHER_MAPPING = {
    'Acil': 'Acil Yayınları',
    'ACİL': 'Acil Yayınları',
    'Apotemi': 'Apotemi',
    '345': '345 Yayınları',
    'Aktif': 'Aktif Öğrenme',
    'Aromat': 'Aromat',
    'Bilgi': 'Bilgi Sarmalı',
    'C1CELL': 'C1CELL',
    'Cap': 'Çap Yayınları',
    'Deneme': 'Deneme Deposu',
    'Edebiyat': 'Edebiyat Denizi',
    'Esen': 'Esen Yayınları',
    'Fizipedia': 'Fizipedia',
    'Full': 'Full Matematik',
    'Krallar': 'Krallar Karması',
    'krallar': 'Krallar Karması',
    'Mikro': 'Mikro Orijinal',
    'Neofizik': 'Neofizik',
    'Orijinal': 'Orijinal',
    'Pes': 'Pes Yayınları',
    'Sure': 'Sure Yayınları',
    'Vaf': 'Vaf Yayınları'
}

def parse_yolo_label(filepath):
    """YOLO label dosyasını oku ve annotation'ları döndür"""
    annotations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    annotations.append({
                        'class_id': class_id,
                        'class_name': CLASS_NAMES.get(class_id, f'unknown_{class_id}'),
                        'x_center': x_center,
                        'y_center': y_center,
                        'width': width,
                        'height': height,
                        'area': width * height
                    })
    except Exception as e:
        print(f"Hata: {filepath}: {e}")
    return annotations

def extract_book_info(filename):
    """Dosya adından kitap bilgilerini çıkar"""
    name = filename.replace('.txt', '')
    parts = name.rsplit('_', 1)
    
    book_name = parts[0] if len(parts) > 1 else name
    page_num = parts[1] if len(parts) > 1 else '0'
    
    # Yıl çıkar
    year = None
    for y in ['2019', '2020', '2021', '2022', '2023', '2024', '2025']:
        if y in book_name:
            year = y
            break
    
    # Yayınevi çıkar
    publisher = 'Bilinmeyen'
    for key, val in PUBLISHER_MAPPING.items():
        if book_name.startswith(key) or key in book_name:
            publisher = val
            break
    
    # Sınav türü
    exam_type = None
    book_lower = book_name.lower()
    if 'tyt' in book_lower:
        exam_type = 'TYT'
    elif 'ayt' in book_lower:
        exam_type = 'AYT'
    elif 'ydt' in book_lower:
        exam_type = 'YDT'
    
    # Ders
    subject = None
    subjects = {
        'matematik': 'Matematik', 'matem': 'Matematik', 'mat': 'Matematik',
        'fizik': 'Fizik', 'fiz': 'Fizik',
        'kimya': 'Kimya', 'kim': 'Kimya',
        'biyoloji': 'Biyoloji', 'biyoloj': 'Biyoloji', 'biyo': 'Biyoloji',
        'türkçe': 'Türkçe', 'turkce': 'Türkçe', 'turk': 'Türkçe',
        'edebiyat': 'Edebiyat', 'edeb': 'Edebiyat',
        'tarih': 'Tarih', 'tar': 'Tarih',
        'coğrafya': 'Coğrafya', 'cografya': 'Coğrafya', 'cog': 'Coğrafya',
        'paragraf': 'Paragraf', 'para': 'Paragraf',
        'geometri': 'Geometri', 'geo': 'Geometri',
        'problem': 'Problem',
        'anlat': 'Anlatım',
        'dil': 'Dil ve Anlatım'
    }
    
    for key, val in subjects.items():
        if key in book_lower:
            subject = val
            break
    
    return {
        'book_name': book_name,
        'page_num': page_num,
        'publisher': publisher,
        'year': year,
        'exam_type': exam_type,
        'subject': subject
    }

def analyze_page_type(annotations):
    """Sayfa türünü analiz et"""
    class_counts = defaultdict(int)
    for ann in annotations:
        class_counts[ann['class_name']] += 1
    
    num_questions = class_counts['soru']
    num_answers = class_counts['cevaplar']
    num_solutions = class_counts['cozum']
    
    # Sayfa türü belirleme
    if num_answers > 10 and num_questions == 0:
        return 'cevap_anahtari'  # Sadece cevap anahtarı sayfası
    elif num_solutions > 0:
        return 'cozumlu_sayfa'   # Çözümlü sayfa
    elif num_questions > 0 and num_answers > 0:
        return 'soru_cevap'      # Soru + inline cevap
    elif num_questions > 0:
        return 'sadece_soru'     # Sadece soru
    elif num_answers > 0:
        return 'sadece_cevap'    # Sadece cevap
    else:
        return 'diger'           # Diğer

def analyze_layout(annotations):
    """Sayfa düzenini analiz et"""
    questions = [a for a in annotations if a['class_name'] == 'soru']
    answers = [a for a in annotations if a['class_name'] == 'cevaplar']
    
    layout = {
        'num_questions': len(questions),
        'num_answers': len(answers),
        'has_topic': any(a['class_name'] == 'konu' for a in annotations),
        'has_test_no': any(a['class_name'] == 'test_no' for a in annotations),
        'has_page': any(a['class_name'] == 'sayfa' for a in annotations),
        'has_solution': any(a['class_name'] == 'cozum' for a in annotations),
        'layout_type': '1-column',
        'answer_position': None
    }
    
    # Kolon düzeni analizi
    if questions:
        left_q = sum(1 for q in questions if q['x_center'] < 0.5)
        right_q = sum(1 for q in questions if q['x_center'] >= 0.5)
        if left_q > 0 and right_q > 0:
            layout['layout_type'] = '2-column'
    
    # Cevap pozisyonu analizi
    if answers:
        avg_y = sum(a['y_center'] for a in answers) / len(answers)
        if avg_y < 0.15:
            layout['answer_position'] = 'top'
        elif avg_y > 0.85:
            layout['answer_position'] = 'bottom'
        elif 0.4 < avg_y < 0.6:
            layout['answer_position'] = 'middle'
        else:
            layout['answer_position'] = 'distributed'
    
    return layout

def main():
    # Dizin yolları
    base_dir = Path(r"C:\Users\husey\kiro2\veriseti\kiro2_yolo_dataset")
    train_labels = base_dir / "train" / "labels"
    val_labels = base_dir / "val" / "labels"
    
    # İstatistikler
    stats = {
        'total_files': 0,
        'total_annotations': 0,
        'train_files': 0,
        'val_files': 0,
        'class_distribution': defaultdict(int),
        'publishers': defaultdict(lambda: {'files': 0, 'questions': 0, 'answers': 0}),
        'years': defaultdict(int),
        'exam_types': defaultdict(int),
        'subjects': defaultdict(int),
        'books': defaultdict(lambda: {'pages': 0, 'questions': 0, 'answers': 0, 'solutions': 0}),
        'page_types': defaultdict(int),
        'layout_types': defaultdict(int),
        'answer_positions': defaultdict(int),
        'questions_per_page': defaultdict(int),
        'answers_per_page': defaultdict(int),
        'bbox_stats': {
            'question_areas': [],
            'answer_areas': [],
            'question_heights': [],
            'question_widths': []
        }
    }
    
    # Tüm label dosyalarını işle
    all_label_files = []
    
    if train_labels.exists():
        train_files = list(train_labels.glob("*.txt"))
        all_label_files.extend([(f, 'train') for f in train_files])
        stats['train_files'] = len(train_files)
        print(f"Train labels: {len(train_files)} dosya")
    
    if val_labels.exists():
        val_files = list(val_labels.glob("*.txt"))
        all_label_files.extend([(f, 'val') for f in val_files])
        stats['val_files'] = len(val_files)
        print(f"Val labels: {len(val_files)} dosya")
    
    stats['total_files'] = len(all_label_files)
    print(f"\nToplam: {stats['total_files']} dosya analiz ediliyor...\n")
    
    # Her dosyayı analiz et
    for idx, (label_file, split) in enumerate(all_label_files):
        if idx % 200 == 0:
            print(f"İşleniyor: {idx}/{len(all_label_files)}")
        
        filename = label_file.name
        annotations = parse_yolo_label(label_file)
        book_info = extract_book_info(filename)
        layout = analyze_layout(annotations)
        page_type = analyze_page_type(annotations)
        
        # Temel istatistikler
        stats['total_annotations'] += len(annotations)
        
        # Sınıf dağılımı
        for ann in annotations:
            stats['class_distribution'][ann['class_name']] += 1
            
            # BBox istatistikleri
            if ann['class_name'] == 'soru':
                stats['bbox_stats']['question_areas'].append(ann['area'])
                stats['bbox_stats']['question_heights'].append(ann['height'])
                stats['bbox_stats']['question_widths'].append(ann['width'])
            elif ann['class_name'] == 'cevaplar':
                stats['bbox_stats']['answer_areas'].append(ann['area'])
        
        # Yayınevi
        pub = book_info['publisher']
        stats['publishers'][pub]['files'] += 1
        stats['publishers'][pub]['questions'] += layout['num_questions']
        stats['publishers'][pub]['answers'] += layout['num_answers']
        
        # Yıl
        if book_info['year']:
            stats['years'][book_info['year']] += 1
        
        # Sınav türü
        if book_info['exam_type']:
            stats['exam_types'][book_info['exam_type']] += 1
        
        # Ders
        if book_info['subject']:
            stats['subjects'][book_info['subject']] += 1
        
        # Kitap
        book = book_info['book_name']
        stats['books'][book]['pages'] += 1
        stats['books'][book]['questions'] += layout['num_questions']
        stats['books'][book]['answers'] += layout['num_answers']
        if layout['has_solution']:
            stats['books'][book]['solutions'] += 1
        
        # Sayfa türü
        stats['page_types'][page_type] += 1
        
        # Düzen türü
        stats['layout_types'][layout['layout_type']] += 1
        
        # Cevap pozisyonu
        if layout['answer_position']:
            stats['answer_positions'][layout['answer_position']] += 1
        
        # Sayfa başına soru/cevap
        stats['questions_per_page'][layout['num_questions']] += 1
        stats['answers_per_page'][layout['num_answers']] += 1
    
    # BBox istatistiklerini hesapla
    def calc_stats(values):
        if not values:
            return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
        sorted_vals = sorted(values)
        return {
            'min': round(min(values), 4),
            'max': round(max(values), 4),
            'avg': round(sum(values) / len(values), 4),
            'median': round(sorted_vals[len(sorted_vals)//2], 4)
        }
    
    bbox_summary = {
        'question_area': calc_stats(stats['bbox_stats']['question_areas']),
        'answer_area': calc_stats(stats['bbox_stats']['answer_areas']),
        'question_height': calc_stats(stats['bbox_stats']['question_heights']),
        'question_width': calc_stats(stats['bbox_stats']['question_widths'])
    }
    
    # Sonuçları düzenle
    result = {
        'genel_ozet': {
            'toplam_dosya': stats['total_files'],
            'train_dosya': stats['train_files'],
            'val_dosya': stats['val_files'],
            'toplam_annotation': stats['total_annotations'],
            'benzersiz_kitap': len(stats['books']),
            'benzersiz_yayinevi': len(stats['publishers'])
        },
        'sinif_dagilimi': dict(stats['class_distribution']),
        'yayinevleri': {k: dict(v) for k, v in sorted(stats['publishers'].items(), key=lambda x: -x[1]['files'])},
        'yillar': dict(sorted(stats['years'].items())),
        'sinav_turleri': dict(stats['exam_types']),
        'dersler': dict(sorted(stats['subjects'].items(), key=lambda x: -x[1])),
        'sayfa_turleri': dict(stats['page_types']),
        'duzen_turleri': dict(stats['layout_types']),
        'cevap_pozisyonlari': dict(stats['answer_positions']),
        'sayfa_basina_soru_dagilimi': {str(k): v for k, v in sorted(stats['questions_per_page'].items()) if k <= 20},
        'sayfa_basina_cevap_dagilimi': {str(k): v for k, v in sorted(stats['answers_per_page'].items()) if k <= 30},
        'bbox_istatistikleri': bbox_summary,
        'kitaplar': {k: dict(v) for k, v in sorted(stats['books'].items(), key=lambda x: -x[1]['questions'])[:50]}
    }
    
    # JSON olarak kaydet
    output_file = base_dir / "dataset_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print("YOLO VERİ SETİ ANALİZ SONUÇLARI")
    print('='*70)
    
    print(f"\n📊 GENEL ÖZET:")
    print(f"   Toplam etiketli sayfa: {result['genel_ozet']['toplam_dosya']:,}")
    print(f"   Toplam annotation: {result['genel_ozet']['toplam_annotation']:,}")
    print(f"   Train/Val oranı: {result['genel_ozet']['train_dosya']}/{result['genel_ozet']['val_dosya']}")
    print(f"   Benzersiz kitap serisi: {result['genel_ozet']['benzersiz_kitap']}")
    print(f"   Benzersiz yayınevi: {result['genel_ozet']['benzersiz_yayinevi']}")
    
    print(f"\n📦 SINIF DAĞILIMI:")
    for cls, count in sorted(result['sinif_dagilimi'].items(), key=lambda x: -x[1]):
        print(f"   {cls:12}: {count:,}")
    
    print(f"\n📚 YAYINEVLERİ (en çok sayfa):")
    for pub, data in list(result['yayinevleri'].items())[:10]:
        print(f"   {pub:20}: {data['files']:4} sayfa, {data['questions']:5} soru")
    
    print(f"\n📅 YILLAR:")
    for year, count in result['yillar'].items():
        print(f"   {year}: {count} kitap")
    
    print(f"\n🎯 SINAV TÜRLERİ:")
    for exam, count in result['sinav_turleri'].items():
        print(f"   {exam}: {count} sayfa")
    
    print(f"\n📖 DERSLER:")
    for subj, count in list(result['dersler'].items())[:10]:
        print(f"   {subj:15}: {count} sayfa")
    
    print(f"\n📄 SAYFA TÜRLERİ:")
    for ptype, count in result['sayfa_turleri'].items():
        print(f"   {ptype:20}: {count}")
    
    print(f"\n📐 DÜZEN TÜRLERİ:")
    for ltype, count in result['duzen_turleri'].items():
        print(f"   {ltype:12}: {count}")
    
    print(f"\n📍 CEVAP POZİSYONLARI:")
    for pos, count in result['cevap_pozisyonlari'].items():
        print(f"   {pos:12}: {count}")
    
    print(f"\n📏 BBOX İSTATİSTİKLERİ:")
    print(f"   Soru alanı (avg): {bbox_summary['question_area']['avg']:.4f}")
    print(f"   Soru yüksekliği (avg): {bbox_summary['question_height']['avg']:.4f}")
    print(f"   Soru genişliği (avg): {bbox_summary['question_width']['avg']:.4f}")
    print(f"   Cevap alanı (avg): {bbox_summary['answer_area']['avg']:.4f}")
    
    print(f"\n✅ Analiz tamamlandı!")
    print(f"   Sonuç dosyası: {output_file}")
    
    return result

if __name__ == "__main__":
    main()
