"""Ortak yardimcilar: profil yukleme, dosya yollari, sayfa karti, okuyucu glifi."""

from __future__ import annotations

import importlib
import json
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[4]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
EKRAN = KOK / "veriseti" / "zkitap" / "screenshots"
VERAFILM = Path(r"C:\Users\husey\VeraFilm")
BEKLENEN_BOYUT = (1920, 1080)
GLIF_RENK = (69, 39, 160)
T = TypeVar("T")
R = TypeVar("R")


def profil(kod: str) -> ModuleType:
    return importlib.import_module(f"scripts.kitap.kitap_hat.profiller.{kod.lower()}")


def profil_kodu(p: ModuleType) -> str:
    """profil(kod) ile yeniden yuklenebilir ad (surec havuzu isine modul gecmez)."""
    return p.__name__.rsplit(".", 1)[-1]


def paralel(fn: Callable[[T], R], isler: list[T], en_az: int = 8) -> list[R]:
    """Sayfa basina bagimsiz isler icin surec havuzu; sonuc SIRASI girdiyle ayni.

    Is sayisi azsa ya da KITAP_TEK_CEKIRDEK=1 ise sirali (test / hata ayiklama).
    Windows spawn: fn modul duzeyinde tanimli olmali, cagiran `__main__` korumali."""
    if len(isler) < en_az or os.environ.get("KITAP_TEK_CEKIRDEK") == "1":
        return [fn(x) for x in isler]
    n = max(1, min(12, (os.cpu_count() or 2) - 2))
    with ProcessPoolExecutor(n) as ex:
        return list(ex.map(fn, isler, chunksize=max(1, len(isler) // (n * 4))))


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


def parite(p: ModuleType, n: int) -> int:
    """Yerlesim paritesi (SIMGE_X / SUTUNLAR anahtari): dosya n % 2; profilin
    PARITE_TERS kumesindeki dosyalarda ters (yakalama boslugundan sonra dosya
    ile basili sayfa paritesi kayan kitaplar)."""
    return (n + (n in getattr(p, "PARITE_TERS", ()))) % 2


def birim_kodu(p: ModuleType, test: int) -> str:
    return f"{p.KOD}-T{test:03d}"


def dosya_adi(birim: str, soru: int) -> str:
    return f"{birim}_{soru:02d}"


def yakalanan(p: ModuleType, test: int, hucreler: list) -> list:
    """Anahtar hucrelerinden sorusu YAKALANMAMIS olanlari cikarir.

    YAKALANMAYAN_SORU {test: (basili no, ...)}: anahtar (kitap sonu tablo) soruyu
    listeler ama sorunun sayfasi ekran goruntusu setinde yok (gozle: yerine baska
    sayfanin kopyasi gelmis). Capa eslemesi kalan hucrelerle yapilir; numaralar
    basili numaradir (atlanan soru numarasi yeniden kullanilmaz)."""
    yok = set(getattr(p, "YAKALANMAYAN_SORU", {}).get(test, ()))
    return [h for h in hucreler if h[0] not in yok]


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


def mavi(a: np.ndarray) -> np.ndarray:
    """MOZ duzeni mavi numara (64,96,160); okuyucu glifi (69,39,160) g < r -> disarida."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (b > 130) & (b - r > 50) & (g > r + 10)
    return m


def camgobegi(a: np.ndarray) -> np.ndarray:
    """'Matematigin Ilaci' camgobegi numara (0,160,224)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (b > 180) & (b - r > 80) & (g > r + 60)
    return m


def siyah(a: np.ndarray) -> np.ndarray:
    """Siyah kalin numara (Sayilar-1): koyu ve notr."""
    m: np.ndarray = (a.max(axis=2) < 100) & (a.max(axis=2) - a.min(axis=2) < 40)
    return m


# Basili numara rengi on ayarlari: profil `numara_maskesi = ortak.NUMARA_MASKELERI["mavi"]`
# diyebilir; kesif.py yeni kitapta hangisinin tuttugunu olcer.
NUMARA_MASKELERI = {
    "kirmizi": kirmizi,
    "mavi": mavi,
    "camgobegi": camgobegi,
    "siyah": siyah,
}
