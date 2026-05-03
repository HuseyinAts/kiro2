"""
KIRO2 - Crop Preprocessor (Layer 1 + Layer 2 yayinevi-bazli)

Pilot 500p extract_page'i CALL etmeden once PNG'yi crop'lar:
- Layer 1: 1920x1080 viewer UI'sini cikarir (sabit x:595-1325, y:45-1020)
- Layer 2: yayinevi-bazli icerik kenar boslugu trim (kitap_crop_coords.json)

Cache: cropped PNG'yi <orjinal_klasor>/.cropped/ icine yazar.
Tekrar islenmek istenirse direkt cache'i kullanir.
Cache invalidation: orijinal PNG mtime > cropped mtime ise yeniden uretilir.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image

CROP_COORDS_PATH = Path(__file__).parent / "kitap_crop_coords.json"
CACHE_DIR_NAME = ".cropped"


def _normalize_yayinevi(folder_name: str) -> str:
    """calibrate_yayinevleri.py ile birebir ayni mantik."""
    tr_map = str.maketrans('İıĞğŞşÇçÖöÜü', 'IiGgSsCcOoUu')
    n = folder_name.translate(tr_map).lower().strip()
    n = re.sub(r'^(?:201\d-201\d|202\d-202\d)[\s\-]+', '', n)
    n = re.sub(r'^(?:201\d|202\d)[\s\-]+', '', n)

    if n.startswith('345') or n[:5].strip().startswith('345'): return '345'
    if 'apotemi' in n: return 'APOTEMI'
    if 'aktif og' in n or 'aktif öğ' in n: return 'AKTIF_OGRENME'
    if 'altyap' in n: return 'ALTYAPI'
    if 'aromat' in n or 'aramot' in n: return 'AROMAT'
    if 'aydın' in n or 'aydin' in n: return 'AYDIN'
    if 'bilgi sarmal' in n: return 'BS'
    if 'c1cell' in n: return 'C1CELL'
    if n.startswith('cap ') or n.startswith('cap-'): return 'CAP'
    if 'deneme deposu' in n or n.startswith('dd-'): return 'DD'
    if 'edebiyat denizi' in n: return 'EDEBIYAT_DENIZI'
    if 'edebiyat sokagi' in n or 'edebiyat sohagi' in n: return 'EDEBIYAT_SOKAGI'
    if 'egsersiz' in n: return 'EGSERSIZ'
    if n.startswith('esen') or n.startswith('esen-'): return 'ESEN'
    if 'fizipedia' in n: return 'FIZIPEDIA'
    if n.startswith('full'): return 'FULL'
    if 'krallar' in n: return 'KRALLAR'
    if n.startswith('mikro'): return 'MIKRO'
    if 'neofizik' in n: return 'NEOFIZIK'
    if n.startswith('orijinal'): return 'ORIJINAL'
    if n[:4] == 'pes ' or n.startswith('pes-'): return 'PES'
    if n.startswith('sure '): return 'SURE'
    if n.startswith('vaf '): return 'VAF'
    if n.startswith('viral'): return 'VIRAL'
    if 'acil' in n: return 'ACIL'
    return None  # Bilinmeyen yayinevi -> Layer 2 atlanir


@lru_cache(maxsize=1)
def _load_coords() -> dict:
    """JSON'i bir kez yukle. Yoksa None doner -> kalibrasyon yok, sadece L1."""
    if not CROP_COORDS_PATH.exists():
        return {}
    return json.loads(CROP_COORDS_PATH.read_text(encoding='utf-8'))


def get_crop_box(book_dir_name: str) -> tuple[int, int, int, int]:
    """Yayinevi-bazli mutlak crop box (1920x1080 koordinatlari).

    Layer 1 (sabit) + Layer 2 (yayinevi). Kalibrasyon yoksa sadece L1.
    """
    coords = _load_coords()
    if not coords:
        # Fallback: sadece L1 default
        return (595, 45, 1325, 1020)

    L1 = tuple(coords['layer1_viewer_crop']['bbox'])  # (x_l, y_t, x_r, y_b)

    ye = _normalize_yayinevi(book_dir_name)
    if ye is None or ye not in coords.get('yayinevleri', {}):
        return L1  # Bilinmeyen yayinevi -> sadece L1

    L2 = coords['yayinevleri'][ye]['recommended_layer2_crop']
    # L2 koordinatlari L1 ICINDE relative -> mutlak'a cevir
    return (
        L1[0] + L2[0],
        L1[1] + L2[1],
        L1[0] + L2[2],
        L1[1] + L2[3],
    )


def preprocess_page(png_path: Path) -> Path:
    """PNG'yi crop'la, cache'e yaz, cropped path'i don.

    Cache: <orijinal_klasor>/.cropped/<dosya_adi>
    Invalidation: orijinal mtime > cropped mtime -> yeniden uret
    1920x1080 disindaki goruntuler ham donulur (smoke1f gibi onceden hazirlanmis).
    """
    book_dir = png_path.parent

    # Cache dizini orijinal kitap klasorunde, gizli
    cache_dir = book_dir / CACHE_DIR_NAME
    cropped_path = cache_dir / png_path.name

    # Cache hit?
    if cropped_path.exists():
        if cropped_path.stat().st_mtime >= png_path.stat().st_mtime:
            return cropped_path

    # Read + check size
    img = Image.open(png_path)
    if img.size != (1920, 1080):
        # Onceden hazirlanmis (sol/sag yari) veya farkli format -> ham don
        return png_path

    # Crop
    box = get_crop_box(book_dir.name)
    cropped = img.crop(box)

    # Write to cache
    cache_dir.mkdir(exist_ok=True)
    cropped.save(cropped_path, format='PNG', optimize=True)

    return cropped_path
