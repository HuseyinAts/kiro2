"""Ortak yardimcilar: profil yukleme, dosya yollari, sayfa karti, okuyucu glifi."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[4]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
EKRAN = KOK / "veriseti" / "zkitap" / "screenshots"
VERAFILM = Path(r"C:\Users\husey\VeraFilm")
BEKLENEN_BOYUT = (1920, 1080)
GLIF_RENK = (69, 39, 160)


def profil(kod: str) -> ModuleType:
    return importlib.import_module(f"scripts.kitap.kitap_hat.profiller.{kod.lower()}")


def yol(p: ModuleType, ad: str) -> Path:
    """veriseti/zkitap/cikti/<CIKTI_ONEK>_<ad>.json"""
    return CIKTI / f"{p.CIKTI_ONEK}_{ad}.json"


def oku(p: ModuleType, ad: str) -> Any:
    return json.loads(yol(p, ad).read_text("utf-8"))


def yaz(p: ModuleType, ad: str, veri: Any, *, girinti: int | None = 0) -> Path:
    y = yol(p, ad)
    y.write_text(
        json.dumps(veri, ensure_ascii=True, indent=girinti) + "\n",
        encoding="ascii",
        newline="\n",
    )
    return y


def kaynak_dizin(p: ModuleType) -> Path:
    d = EKRAN / p.KLASOR
    n = len(list(d.glob("sayfa_*.png")))
    if n != p.BEKLENEN_SAYFA:
        raise SystemExit(f"kaynak sayfa sayisi {n} != {p.BEKLENEN_SAYFA}")
    return Path(d)


def kart(p: ModuleType, d: Path, n: int) -> np.ndarray:
    img = Image.open(d / f"sayfa_{n:04d}.png").convert("RGB")
    if img.size != BEKLENEN_BOYUT:
        raise SystemExit(f"BOYUT UYUSMAZLIGI s{n}: {img.size}")
    return np.asarray(img.crop(p.KART)).astype(int)


def birim_kodu(p: ModuleType, test: int) -> str:
    return f"{p.KOD}-T{test:03d}"


def dosya_adi(birim: str, soru: int) -> str:
    return f"{birim}_{soru:02d}"


def glifler(p: ModuleType, a: np.ndarray) -> list[list[int]]:
    """Okuyucu simgesi (mor glif) sol-ust koseleri [y, x], yukaridan asagi."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (
        (abs(r - GLIF_RENK[0]) < 35)
        & (abs(g - GLIF_RENK[1]) < 35)
        & (abs(b - GLIF_RENK[2]) < 40)
    )
    if getattr(p, "GLIF_GENISLET", False):
        m = ndimage.binary_dilation(m, np.ones((3, 3), bool))
    lab, _ = ndimage.label(m)
    h0, h1, w0, w1 = p.GLIF_BOY
    out = []
    for s in ndimage.find_objects(lab):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        if h0 <= h <= h1 and w0 <= w <= w1:
            out.append([s[0].start, s[1].start])
    return sorted(out)


def kirmizi(a: np.ndarray) -> np.ndarray:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (r > 170) & (g < 100) & (b < 110)
    return m
