#!/usr/bin/env python3
"""
20 Farklı Yayınevinden Kitap Analizi
İlk 30 ve Son 30 Sayfaları OCR ile Tara
Cevap Anahtarlarını Bul
"""

from PIL import Image, ImageEnhance
import numpy as np
import os
import re
from pathlib import Path
from collections import defaultdict
import easyocr
import json

# Kaynak klasör - ham sayfalar
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v5")

print("=" * 70)
print("20 FARKLI YAYINEVİ - İLK 30 & SON 30 SAYFA ANALİZİ")
print("=" * 70)

# Kaynak kontrolü
if not SOURCE_DIR.exists():
    # Alternatif konumları ara
    alternatives = [
        Path(r"C:\Users\husey\kiro2\veriseti"),
        Path(r"C:\Users\husey\d-dataset"),
    ]
    for alt in alternatives:
        if alt.exists():
            print(f"\n📁 {alt} içeriği:")
            for item in sorted(alt.iterdir())[:20]:
                if item.is_dir():
                    sub = len(list(item.iterdir()))
                    print(f"   {item.name}: {sub} öğe")
    print(f"\n❌ Kaynak bulunamadı: {SOURCE_DIR}")
    print("Lütfen doğru yolu belirtin.")
    exit(1)

print(f"\n✅ Kaynak: {SOURCE_DIR}")

# Tüm kitapları listele
all_books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
print(f"   Toplam kitap: {len(all_books)}")

# Farklı yayınevlerinden kitap seç
PUBLISHERS = [
    'ACİL', 'Acil', 'ACIL',
    'Apotemi', 'APOTEMI',
    '345',
    'Esen', 'ESEN',
    'Palme', 'PALME',
    'Karekök', 'KAREKÖK', 'Karekok',
    'Limit', 'LİMİT',
    'Okyanus', 'OKYANUS',
    'Bilgi', 'BİLGİ',
    'Hız', 'HIZ',
    'Çap', 'CAP', 'ÇAP',
    'Paraf', 'PARAF',
    'Sonuç', 'SONUC', 'SONUÇ',
    'Ankara', 'ANKARA',
    'Pegem', 'PEGEM',
    'Kırmızı', 'KIRMIZI',
    'Birey', 'BİREY',
    'Üç Dört Beş', 'Üçdörtbeş',
    'FDD', 'Fdd',
    'Yayın', 'YAYIN',
]

selected_books = []
used_publishers = set()

# Her yayınevinden bir kitap seç
for book in all_books:
    book_name = book.name
    for pub in PUBLISHERS:
        if pub.lower() in book_name.lower() and pub.lower() not in used_publishers:
            selected_books.append(book)
            used_publishers.add(pub.lower())
            break
    if len(selected_books) >= 20:
        break

# 20'ye tamamla
if len(selected_books) < 20:
    for book in all_books:
        if book not in selected_books:
            selected_books.append(book)
        if len(selected_books) >= 20:
            break

print(f"\n📚 SEÇİLEN 20 KİTAP:")
for i, book in enumerate(selected_books, 1):
    pages = list(book.glob("*.png")) + list(book.glob("*.jpg"))
    print(f"   {i:2d}. {book.name[:50]}... ({len(pages)} sayfa)")

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def preprocess_page(img):
    """Sayfa görüntüsünü OCR için hazırla"""
    w, h = img.size
    # Çok büyükse küçült (hız için)
    if max(w, h) > 1500:
        scale = 1500 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    return img

def extract_answers(text):
    """Metinden cevap anahtarı çıkar"""
    answers = {}
    text_upper = text.upper()

    # Pattern'ler
    patterns = [
        r'(\d{1,3})\s*[.\-:)]\s*([A-E])\b',   # 1.A, 1-A, 1:A, 1)A
        r'(\d{1,3})\s+([A-E])\b',              # 1 A
        r'\b([A-E])\s*(\d{1,3})\b',            # A1 (ters format)
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if pattern == r'\b([A-E])\s*(\d{1,3})\b':
                a, q = match
            else:
                q, a = match
            try:
                q = int(q)
                if 1 <= q <= 200:
                    answers[q] = a
            except:
                pass

    return answers

def is_answer_key_page(text, answers):
    """Bu sayfa cevap anahtarı sayfası mı?"""
    text_upper = text.upper()

    # Cevap anahtarı ipuçları
    keywords = ['CEVAP', 'YANITLAR', 'ANSWER', 'ÇÖZÜM', 'COZUM', 'ANAHTARI', 'ANAHTAR']
    has_keyword = any(kw in text_upper for kw in keywords)

    # En az 5 cevap ve ardışık numaralar
    if len(answers) >= 5:
        nums = sorted(answers.keys())
        # Ardışık kontrol
        consecutive = sum(1 for i in range(len(nums)-1) if nums[i+1] - nums[i] <= 2)
        if consecutive >= 3:
            return True

    if has_keyword and len(answers) >= 3:
        return True

    return False

def analyze_book(book_path, book_idx, total):
    """Bir kitabın ilk 30 ve son 30 sayfasını analiz et"""
    book_name = book_path.name

    # Sayfa dosyalarını al
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)

    if len(pages) < 10:
        return None

    result = {
        'book': book_name,
        'total_pages': len(pages),
        'first_30': {'pages_analyzed': 0, 'answer_pages': [], 'total_answers': 0},
        'last_30': {'pages_analyzed': 0, 'answer_pages': [], 'total_answers': 0},
    }

    # İLK 30 SAYFA
    first_pages = pages[:30]
    for page_path in first_pages:
        try:
            img = Image.open(page_path)
            img = preprocess_page(img)

            ocr_result = reader.readtext(np.array(img), detail=0)
            text = ' '.join(ocr_result)

            answers = extract_answers(text)

            result['first_30']['pages_analyzed'] += 1

            if is_answer_key_page(text, answers):
                result['first_30']['answer_pages'].append({
                    'page': page_path.name,
                    'answer_count': len(answers),
                    'sample': list(answers.items())[:10],
                    'text_preview': text[:100]
                })
                result['first_30']['total_answers'] += len(answers)
        except Exception as e:
            pass

    # SON 30 SAYFA
    last_pages = pages[-30:] if len(pages) > 30 else []
    for page_path in last_pages:
        try:
            img = Image.open(page_path)
            img = preprocess_page(img)

            ocr_result = reader.readtext(np.array(img), detail=0)
            text = ' '.join(ocr_result)

            answers = extract_answers(text)

            result['last_30']['pages_analyzed'] += 1

            if is_answer_key_page(text, answers):
                result['last_30']['answer_pages'].append({
                    'page': page_path.name,
                    'answer_count': len(answers),
                    'sample': list(answers.items())[:10],
                    'text_preview': text[:100]
                })
                result['last_30']['total_answers'] += len(answers)
        except Exception as e:
            pass

    return result

# Ana analiz
print("\n" + "=" * 70)
print("ANALİZ BAŞLIYOR...")
print("=" * 70)

all_results = []

for idx, book in enumerate(selected_books):
    print(f"\n[{idx+1}/20] 📖 {book.name[:50]}...")

    result = analyze_book(book, idx, len(selected_books))

    if result:
        all_results.append(result)

        first_ans = len(result['first_30']['answer_pages'])
        last_ans = len(result['last_30']['answer_pages'])
        first_total = result['first_30']['total_answers']
        last_total = result['last_30']['total_answers']

        print(f"   📄 Toplam sayfa: {result['total_pages']}")
        print(f"   🔹 İLK 30: {first_ans} cevap sayfası, {first_total} cevap")
        print(f"   🔸 SON 30: {last_ans} cevap sayfası, {last_total} cevap")

        # Örnek göster
        if result['first_30']['answer_pages']:
            sample = result['first_30']['answer_pages'][0]
            print(f"      İlk örnek: {sample['page']} - {sample['sample'][:3]}")
        if result['last_30']['answer_pages']:
            sample = result['last_30']['answer_pages'][0]
            print(f"      Son örnek: {sample['page']} - {sample['sample'][:3]}")

# ÖZET RAPOR
print("\n" + "=" * 70)
print("ÖZET RAPOR")
print("=" * 70)

total_first = sum(len(r['first_30']['answer_pages']) for r in all_results)
total_last = sum(len(r['last_30']['answer_pages']) for r in all_results)
total_first_answers = sum(r['first_30']['total_answers'] for r in all_results)
total_last_answers = sum(r['last_30']['total_answers'] for r in all_results)

books_with_first = sum(1 for r in all_results if r['first_30']['answer_pages'])
books_with_last = sum(1 for r in all_results if r['last_30']['answer_pages'])

print(f"\n📊 CEVAP ANAHTARI KONUMU:")
print(f"   ┌─────────────────┬──────────────┬──────────────┬──────────────┐")
print(f"   │ Konum           │ Sayfa Sayısı │ Toplam Cevap │ Kitap Sayısı │")
print(f"   ├─────────────────┼──────────────┼──────────────┼──────────────┤")
print(f"   │ İLK 30 SAYFA    │ {total_first:12d} │ {total_first_answers:12d} │ {books_with_first:12d} │")
print(f"   │ SON 30 SAYFA    │ {total_last:12d} │ {total_last_answers:12d} │ {books_with_last:12d} │")
print(f"   └─────────────────┴──────────────┴──────────────┴──────────────┘")

if total_last_answers > total_first_answers:
    print(f"\n   💡 SONUÇ: Cevap anahtarları KİTAP SONUNDA!")
    print(f"      Son 30 sayfada {total_last_answers} cevap vs İlk 30 sayfada {total_first_answers} cevap")
elif total_first_answers > total_last_answers:
    print(f"\n   💡 SONUÇ: Cevap anahtarları KİTAP BAŞINDA!")
    print(f"      İlk 30 sayfada {total_first_answers} cevap vs Son 30 sayfada {total_last_answers} cevap")
else:
    print(f"\n   ⚠️ SONUÇ: Dağılım eşit veya belirsiz")

# Detaylı sonuçları kaydet
output_file = OUTPUT_DIR / "analysis_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    # Convert tuples to lists for JSON
    for r in all_results:
        for section in ['first_30', 'last_30']:
            for page in r[section]['answer_pages']:
                page['sample'] = [[k, v] for k, v in page['sample']]
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\n   📁 Detaylı sonuçlar: {output_file}")

# Cevap bulunan kitapların listesi
print("\n" + "-" * 70)
print("CEVAP BULUNAN KİTAPLAR:")
print("-" * 70)
for r in all_results:
    if r['first_30']['total_answers'] > 0 or r['last_30']['total_answers'] > 0:
        print(f"\n   📚 {r['book'][:50]}")
        if r['first_30']['total_answers'] > 0:
            print(f"      İLK 30: {r['first_30']['total_answers']} cevap")
            for p in r['first_30']['answer_pages'][:2]:
                print(f"         - {p['page']}: {p['answer_count']} cevap")
        if r['last_30']['total_answers'] > 0:
            print(f"      SON 30: {r['last_30']['total_answers']} cevap")
            for p in r['last_30']['answer_pages'][:2]:
                print(f"         - {p['page']}: {p['answer_count']} cevap")

print("\n" + "=" * 70)
print("ANALİZ TAMAMLANDI")
print("=" * 70)
