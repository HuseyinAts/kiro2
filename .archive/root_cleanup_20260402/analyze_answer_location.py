#!/usr/bin/env python3
"""
Cevap Anahtarı Konum Analizi
12 farklı kitabın ilk 25 ve son 25 sayfasını incele
"""

from PIL import Image
import numpy as np
import os
import json
from pathlib import Path
from collections import defaultdict
import easyocr

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v4")

print("=" * 70)
print("CEVAP ANAHTARI KONUM ANALİZİ")
print("12 Kitap x (İlk 25 + Son 25 Sayfa)")
print("=" * 70)

# EasyOCR yükle
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır\n")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tüm kitapları al ve 12 farklı kitap seç (çeşitli yayınlar)
all_books = sorted([d for d in os.listdir(CROPS_DIR) if (CROPS_DIR / d).is_dir()])
print(f"Toplam kitap: {len(all_books)}")

# Farklı yayınlardan seçim yap
selected_books = []
publishers = ['Acil', 'Apotemi', 'Esen', '345', 'Karekök', 'Palme', 'Limit', 'Okyanus', 'Bilgi', 'Hız', 'Delta', '3D']

for pub in publishers:
    for book in all_books:
        if pub.lower() in book.lower() and book not in selected_books:
            selected_books.append(book)
            break

# 12'ye tamamla
if len(selected_books) < 12:
    for book in all_books:
        if book not in selected_books:
            selected_books.append(book)
        if len(selected_books) >= 12:
            break

selected_books = selected_books[:12]
print(f"\nSeçilen 12 kitap:")
for i, book in enumerate(selected_books, 1):
    print(f"  {i:2d}. {book[:50]}")

# Sonuçları topla
results = {
    "ilk_25": defaultdict(list),  # İlk 25 sayfa
    "son_25": defaultdict(list),  # Son 25 sayfa
    "cevap_pattern": defaultdict(int),  # Cevap pattern'leri
}

print("\n" + "=" * 70)
print("ANALİZ BAŞLIYOR...")
print("=" * 70)

for book_idx, book_name in enumerate(selected_books):
    book_path = CROPS_DIR / book_name

    # Tüm PNG'leri al ve sayfa numarasına göre sırala
    try:
        all_pngs = sorted([f for f in os.listdir(book_path) if f.endswith('.png')])
    except:
        continue

    if not all_pngs:
        continue

    # Sayfa numaralarını çıkar
    def get_page_num(filename):
        import re
        match = re.search(r'sayfa_(\d+)', filename)
        return int(match.group(1)) if match else 0

    all_pngs_sorted = sorted(all_pngs, key=get_page_num)

    # İlk 25 ve son 25
    ilk_25 = all_pngs_sorted[:25]
    son_25 = all_pngs_sorted[-25:] if len(all_pngs_sorted) > 25 else []

    print(f"\n{'─'*70}")
    print(f"📚 [{book_idx+1}/12] {book_name[:55]}")
    print(f"   Toplam crop: {len(all_pngs)}, İlk 25: {len(ilk_25)}, Son 25: {len(son_25)}")

    # İLK 25 SAYFA
    print(f"\n   📖 İLK 25 SAYFA:")
    ilk_25_ocr = []
    for png in ilk_25[:10]:  # İlk 10'u detaylı göster
        try:
            img = Image.open(book_path / png)
            img_array = np.array(img)
            result = reader.readtext(img_array, detail=0)
            text = ' '.join(result).upper()
            ilk_25_ocr.append({"file": png, "text": text, "size": img.size})

            # Cevap pattern kontrolü
            has_answer = any(c in text for c in ['1.A', '1-A', '1)A', '1 A', '2.B', '3.C', 'CEVAP'])
            status = "✅ CEVAP?" if has_answer else "📝"
            print(f"      {status} {png}: '{text[:50]}...' " if len(text) > 50 else f"      {status} {png}: '{text}'")

            if has_answer:
                results["cevap_pattern"]["ilk_25"] += 1
        except Exception as e:
            pass

    # SON 25 SAYFA
    if son_25:
        print(f"\n   📖 SON 25 SAYFA:")
        son_25_ocr = []
        for png in son_25[-10:]:  # Son 10'u detaylı göster
            try:
                img = Image.open(book_path / png)
                img_array = np.array(img)
                result = reader.readtext(img_array, detail=0)
                text = ' '.join(result).upper()
                son_25_ocr.append({"file": png, "text": text, "size": img.size})

                # Cevap pattern kontrolü - daha geniş
                import re
                has_answer = bool(re.search(r'\d+\s*[.\-)\s:]\s*[A-E]', text)) or 'CEVAP' in text
                status = "✅ CEVAP?" if has_answer else "📝"
                print(f"      {status} {png}: '{text[:50]}...' " if len(text) > 50 else f"      {status} {png}: '{text}'")

                if has_answer:
                    results["cevap_pattern"]["son_25"] += 1
            except Exception as e:
                pass

        results["son_25"][book_name] = son_25_ocr

    results["ilk_25"][book_name] = ilk_25_ocr

# ÖZET
print("\n" + "=" * 70)
print("ÖZET ANALİZ")
print("=" * 70)
print(f"\nCevap Pattern Dağılımı:")
print(f"  İlk 25 sayfada: {results['cevap_pattern']['ilk_25']} adet")
print(f"  Son 25 sayfada: {results['cevap_pattern']['son_25']} adet")

# Detaylı analiz için JSON kaydet
summary_file = OUTPUT_DIR / "sayfa_analiz_ozet.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump({
        "ilk_25_count": results["cevap_pattern"]["ilk_25"],
        "son_25_count": results["cevap_pattern"]["son_25"],
        "books_analyzed": selected_books
    }, f, ensure_ascii=False, indent=2)

print(f"\nÖzet kaydedildi: {summary_file}")
