"""zkitap viewer screenshot'larindan sayfa disi alani kirp + OCR'a hazirla.

Girdi : veriseti/zkitap/screenshots/<kitap>/*.png  (1920x1080 PDF viewer ekran goruntusu)
Cikti : <kitap>/temiz <kitap>/            -> tam sayfa, 2x LANCZOS
        <kitap>/temiz <kitap>/sutun/      -> sol/sag sutun, Claude'un KUCULTMEDIGI boyutta

Neden iki cikti:
  Claude gorseli uzun kenar 1568 px ve ~1.15 MP butcesine indiriyor. Tam sayfa
  (752x968 ham) bu butcede ~1.26x'e sikisiyor -> metin satiri ~11 px kaliyor,
  W4r dersinin esigi olan 12 px'in ALTINDA. Sutun kirpiginda kucultme hic
  devreye girmiyor -> ~15 px. OCR sutunla yapilir, dogrulama/sayfa eslemesi
  tam sayfayla.

Sayfa kutusu OLCULUR, sabit varsayilmaz: crop_preprocessor.py'nin L1 sabiti
(595,45,1325,1020) bu kitaplarda sayfanin sol/sag kenarindan 11'er px yiyor.

Kullanim:
    python sayfa_kirp_zkitap.py --kitap "345 2025 Tyt Biyoloji Soru Bankası"
    python sayfa_kirp_zkitap.py --kitap "..." --sadece tam      # sutun uretme
    python sayfa_kirp_zkitap.py --kitap "..." --force --limit 5 # pilot
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image

if isinstance(sys.stdout, io.TextIOWrapper):  # cp1254 konsolda Turkce cokmesin
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")

BEKLENEN_BOYUT = (1920, 1080)
# Arama penceresi: ust sekme, alt arac cubugu, yan oklar ve sag yayinevi widget'i
# disarida kalmali. x1=1500 -> widget'i 1650'de olan kitap da (TYT Biyoloji),
# 1730'da olan da (AYT Biyoloji) guvende.
PENCERE = (120, 46, 1500, 1016)
TOLERANS = 3  # olculen kutu modal kutudan bu kadar sapabilir
ORNEK_SAYISI = 16  # modal kutuyu belirlemek icin

TAM_OLCEK = 2  # tam sayfa 2x LANCZOS

# Claude gorsel sinirlari (API spesifikasyonu): uzun kenar <=1568 px ve <=~1.15 MP.
# Sutun kirpigi bu sinirlarin ALTINDA kalacak sekilde buyutulur -> kucultme yok.
UZUN_KENAR_SINIR = 1568
PIKSEL_BUTCESI = 1_150_000

# Sutun bolme (sayfa ICINDE, ham sayfa genisligine oranli).
# Olculen oluk: x=382..417 / 752 genislik -> merkez ~%53. Kesme riskine karsi
# iki yana 30 px bindirme birakiliyor.
OLUK_SOL = 430  # sol sutun bu x'e kadar (bindirmeli)
OLUK_SAG = 370  # sag sutun bu x'ten itibaren (bindirmeli)


# Viewer her sorunun soluna bir buyutec ikonu basiyor. Glif rengi TAM olarak
# RGB(69,39,160) ve anti-aliasing yuzunden ~29 saf piksel, 1-5'lik parcalara
# dagilmis halde. Genisletip birlestirince sayfa basina soru sayisi DETERMINISTIK
# olarak sayilabiliyor -> LLM ciktisini curutecek ikinci sinyal (tek-sinyal yasak).
IKON_RENK = (69, 39, 160)
IKON_TOLERANS = 6
IKON_MIN_PIKSEL = 12
# Sayfa ustunde SORU OLMAYAN ikonlar var (tum kitapta olculdu, 7 adet):
#   y=8   -> 0009,0041,0053,0063: ust dekoratif bantta bosta duran, yarim kesik ikon
#   y~50  -> 0103,0153,0189: "Sinavda Bu Tarz Sorular" basliginin yanindaki ikon
# Buna karsilik y~100-139'daki ikonlar GERCEK sorulardir (basliksiz OSYM sayfalari;
# 0016 ve 0020 bagimsiz cikarimla dogrulandi). Esik ikisinin arasina konuldu.
IKON_MIN_Y = 60
# Ikonun hangi SUTUNA ait oldugunu belirleyen esik. Kirpma sinirini (OLUK_SAG=370)
# kullanmak HATALIYDI: olculen dagilim sol kume x=39..57, sag kume x=232..380 ->
# 370'lik esik sag kumenin ICINDEN geciyor ve 360..369 arasindaki 14 ikonu sola
# yaziyordu. Esik iki kumenin arasina konuldu (bos bolge: 57..232).
IKON_SUTUN_ESIGI = 200

# Cevap anahtari satiri ('1.A 2.D 3.D') sayfa altinda, her sutunun kendi altinda.
# Olculdu: y=896..902 (h=6 px), 5 sayfada birebir ayni. Bu 6 px'lik satir tam
# sayfa gorselinde okunamaz boyutta -> ayri ve YUKSEK zoom'la kirpilir.
CEVAP_ARAMA = (880, 920)  # sayfa-ici y arama araligi
CEVAP_PAY = 8  # bulunan bandin altina/ustune birakilan pay

# Bolum kapaklarinda viylewer bazen TEK basibos ikon birakiyor (orn. sayfa_0017,
# BOLUM 02 kapagi) ve kapak basligi da cevap bandina denk gelip serit sanilabiliyor.
# Olculen dagilim: gercek soru sayfalari 3-7 ikon; hicbir sayfada 2 yok.
# Esik 2 -> tek basibos ikon soru sayilmaz, o sayfaya cevap seridi de uretilmez.
SORU_ESIGI = 2


class OlcumHatasiError(RuntimeError):
    """Tespit penceresine degiyor -> olculen kutu kirpilmis, guvenilmez."""


def sayfa_bbox_olc(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Viewer arka planindan renkce ayrisan en dis dikdortgen."""
    a = np.asarray(img.crop(PENCERE).convert("RGB"), dtype=np.int16)
    bg = np.median(a[:, 0:60].reshape(-1, 3), axis=0)  # sol serit = saf arka plan
    ys, xs = np.nonzero(np.abs(a - bg).max(axis=2) > 8)
    if len(xs) == 0:
        return None
    return (
        int(xs.min()) + PENCERE[0],
        int(ys.min()) + PENCERE[1],
        int(xs.max()) + PENCERE[0] + 1,
        int(ys.max()) + PENCERE[1] + 1,
    )


def pencereye_degiyor(bbox: tuple[int, int, int, int]) -> bool:
    """Kutu arama penceresinin kenarina yapismissa olcum KIRPILMIS demektir.

    Bu bekci gercek bir hatadan dogdu: TYT Biyoloji'de yayinevi widget'i x~1650'de
    basliyor; pencere 1700 iken widget kutuya dahil olup sag kenari 1700'e
    civiliyordu. Yanlis kutu sessizce sayfanin yarisini fazladan kirpardi.

    UST kenar bilerek DISARIDA: sayfanin ustu (y=46) viewer icerik alaninin
    baslangiciyla cakisiyor, yani orada temas NORMAL. Pencere yukari acilamiyor
    cunku ust sekme cipi sayfanin x araliginda duruyor ve kutuya karisir.
    Ust kenar ayrica ust_kenar_dogrula() ile denetleniyor.
    """
    return bbox[0] <= PENCERE[0] or bbox[2] >= PENCERE[2] or bbox[3] >= PENCERE[3]


def ust_kenar_dogrula(bbox: tuple[int, int, int, int]) -> None:
    """Sayfa ustu viewer icerik ustunde olmali; asagi kaymissa olcum suphelidir."""
    if bbox[1] != PENCERE[1]:
        print(f"  NOT: sayfa ust kenari {bbox[1]} (beklenen {PENCERE[1]})")


def modal_bbox(dosyalar: list[Path]) -> tuple[int, int, int, int]:
    """Orneklemden en sik gorulen sayfa kutusu (kanonik)."""
    sayac: dict[tuple[int, int, int, int], int] = {}
    idx = np.linspace(0, len(dosyalar) - 1, min(ORNEK_SAYISI, len(dosyalar)))
    for i in idx.astype(int):
        with Image.open(dosyalar[i]) as im:
            if im.size != BEKLENEN_BOYUT:
                continue
            bb = sayfa_bbox_olc(im)
        if bb is None:
            continue
        if pencereye_degiyor(bb):
            raise OlcumHatasiError(
                f"{dosyalar[i].name}: olculen kutu {bb} arama penceresine "
                f"{PENCERE} degiyor -> olcum kirpilmis. PENCERE'yi daralt."
            )
        sayac[bb] = sayac.get(bb, 0) + 1
    if not sayac:
        raise OlcumHatasiError("Orneklemde hicbir sayfa kutusu olculemedi")
    return max(sayac.items(), key=lambda kv: kv[1])[0]


def cevap_bandi(
    img: Image.Image, bbox: tuple[int, int, int, int]
) -> tuple[int, int] | None:
    """Sayfa altindaki cevap anahtari satirinin y araligi (sayfa-ici koordinat).

    Olculdu (5 sayfa, birebir ayni): y=896..902, h=6 px. Bolum kapaklarinda YOK.
    Sabit yazmak yerine her sayfada aranir; bulunamazsa o sayfada cevap seridi
    uretilmez (sessizce bos gorsel yazmak yerine).
    """
    a = np.asarray(img.crop(bbox).convert("L"), dtype=np.uint8)
    y0, y1 = CEVAP_ARAMA
    dolu = (a[y0:y1] < 120).sum(axis=1) > 0
    if not dolu.any():
        return None
    ys = np.nonzero(dolu)[0]
    return (y0 + int(ys.min()) - CEVAP_PAY, y0 + int(ys.max()) + 1 + CEVAP_PAY)


def soru_ikonlari(img: Image.Image, bbox: tuple[int, int, int, int]) -> list[int]:
    """Sayfadaki buyutec ikonlarinin x konumlari (sayfa-ici koordinat).

    Sayi = o sayfada BEKLENEN soru sayisi. OCR ciktisi bununla capraz kontrol
    edilir; tutmuyorsa model soru atlamis veya uydurmus demektir.

    DIKKAT: viewer BAZI sayfalarda cevap anahtari satirinin soluna da ayni ikonu
    basiyor (orn. sayfa_0020) -> o ikon soru DEGIL. Cevap bandi ve altinda kalan
    ikonlar elenir. Bu kusur ilk surumde vardi ve kontrol sayfasi (sayfa_0032)
    tesadufen o ikonu tasimayan sayfalardan biri oldugu icin fark edilmedi.
    """
    from scipy import ndimage  # yalniz manifest modunda gerekli

    a = np.asarray(img.crop(bbox).convert("RGB"), dtype=np.int16)
    maske = np.all(np.abs(a - np.array(IKON_RENK)) <= IKON_TOLERANS, axis=2)
    if not maske.any():
        return []
    genis = ndimage.binary_dilation(maske, np.ones((7, 7), bool))
    etiket, n = ndimage.label(genis)
    boyut = ndimage.sum(maske, etiket, range(1, n + 1))
    merkez = ndimage.center_of_mass(maske, etiket, range(1, n + 1))
    return sorted(
        int(c[1])
        for s, c in zip(boyut, merkez, strict=True)
        if s >= IKON_MIN_PIKSEL and IKON_MIN_Y <= c[0] < CEVAP_ARAMA[0]
    )


def ocr_olcegi(genislik: int, yukseklik: int) -> float:
    """Claude'un KUCULTMEYECEGI en buyuk olcek (sadece buyutur, kucultmez)."""
    k = min(
        UZUN_KENAR_SINIR / max(genislik, yukseklik),
        (PIKSEL_BUTCESI / (genislik * yukseklik)) ** 0.5,
    )
    return float(max(1.0, k))


def buyut(img: Image.Image, k: float) -> Image.Image:
    return img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)


class SayfaYollari(NamedTuple):
    """Bir kaynak PNG'nin uretecegi tum cikti yollari."""

    tam: Path
    sol: Path
    sag: Path
    cevap_sol: Path
    cevap_sag: Path


def _guncel(cikti: Path, kaynak: Path) -> bool:
    """Cikti kaynaktan yeni mi (yeniden uretmeye gerek var mi)."""
    return cikti.exists() and cikti.stat().st_mtime >= kaynak.stat().st_mtime


def _gereken_isler(
    kaynak: Path,
    yol: SayfaYollari,
    *,
    tam: bool,
    sutun: bool,
    cevap: bool,
    force: bool,
) -> list[str]:
    isler = []
    if tam and (force or not _guncel(yol.tam, kaynak)):
        isler.append("tam")
    if sutun and (force or not (_guncel(yol.sol, kaynak) and _guncel(yol.sag, kaynak))):
        isler.append("sutun")
    if cevap and (
        force or not (_guncel(yol.cevap_sol, kaynak) and _guncel(yol.cevap_sag, kaynak))
    ):
        isler.append("cevap")
    return isler


def _kutu_sec(
    img: Image.Image,
    kanonik: tuple[int, int, int, int],
    ad: str,
    sapanlar: list[str],
    tespit_yok: list[str],
) -> tuple[int, int, int, int]:
    """Olculen kutu; guvenilmezse kanonige duser ve sebebi kaydeder."""
    bbox = sayfa_bbox_olc(img)
    if bbox is None:
        tespit_yok.append(ad)
        return kanonik
    if (
        pencereye_degiyor(bbox)
        or max(abs(a - b) for a, b in zip(bbox, kanonik, strict=True)) > TOLERANS
    ):
        sapanlar.append(f"{ad} olculen={bbox}")
        return kanonik
    return bbox


def _cevap_seridi_yaz(
    img: Image.Image,
    sayfa: Image.Image,
    bbox: tuple[int, int, int, int],
    yol: SayfaYollari,
) -> int:
    """Cevap seridini yazar, yazilan dosya sayisini doner (0 = uretilmedi).

    Soru sayfasi degilse eski uretilmis seritleri TEMIZLER: kapak basligi
    cevap bandina denk gelip serit sanilabiliyor.
    """
    if len(soru_ikonlari(img, bbox)) < SORU_ESIGI:
        yol.cevap_sol.unlink(missing_ok=True)
        yol.cevap_sag.unlink(missing_ok=True)
        return 0
    band = cevap_bandi(img, bbox)
    if band is None:
        return 0
    cy0, cy1 = band
    for kutu, hedef_yol in (
        ((0, cy0, OLUK_SOL, cy1), yol.cevap_sol),
        ((OLUK_SAG, cy0, sayfa.width, cy1), yol.cevap_sag),
    ):
        serit = sayfa.crop(kutu)
        buyut(serit, ocr_olcegi(serit.width, serit.height)).save(
            hedef_yol, format="PNG", optimize=True
        )
    return 2


def _ciktilari_yaz(
    img: Image.Image,
    bbox: tuple[int, int, int, int],
    yol: SayfaYollari,
    gerekli: list[str],
) -> tuple[int, int, int]:
    """Istenen ciktilari yazar. Donus: (tam, sutun, cevap) yazilan dosya sayilari."""
    sayfa = img.crop(bbox)
    tam = sutun = cevap = 0

    if "tam" in gerekli:
        buyut(sayfa, TAM_OLCEK).save(yol.tam, format="PNG", optimize=True)
        tam = 1

    if "sutun" in gerekli:
        sol = sayfa.crop((0, 0, OLUK_SOL, sayfa.height))
        sag = sayfa.crop((OLUK_SAG, 0, sayfa.width, sayfa.height))
        buyut(sol, ocr_olcegi(sol.width, sol.height)).save(
            yol.sol, format="PNG", optimize=True
        )
        buyut(sag, ocr_olcegi(sag.width, sag.height)).save(
            yol.sag, format="PNG", optimize=True
        )
        sutun = 2

    if "cevap" in gerekli:
        cevap = _cevap_seridi_yaz(img, sayfa, bbox, yol)

    return tam, sutun, cevap


def _duzeltmeleri_oku(hedef: Path) -> dict[str, tuple[int, int, int]]:
    """Insan tarafindan DOGRULANMIS manifest duzeltmeleri (ikon sayacini EZER).

    Ikon sayaci bir ALT SINIRDIR: viewer bazi sorulara ikon BASMIYOR. Olculdu:
    sayfa_0106 s.4 ve sayfa_0111'de sorunun govdesi, 5 sikki, kaynak etiketi ve
    cevap seridi kaydi var ama ikonu yok. Bu sayfalar bagimsiz kanitla
    dogrulanip buraya yazilir; gerekce sutunu kanitin ozetidir.
    """
    yol = hedef / "manifest_duzeltme.csv"
    if not yol.exists():
        return {}
    with yol.open(encoding="utf-8") as fh:
        return {
            r["dosya"]: (
                int(r["beklenen_soru"]),
                int(r["sol_sutun"]),
                int(r["sag_sutun"]),
            )
            for r in csv.DictReader(fh)
        }


def _manifest_yaz(
    hedef: Path, dosyalar: list[Path], kanonik: tuple[int, int, int, int]
) -> None:
    """Sayfa basina beklenen soru sayisi (ikon sayaci + dogrulanmis duzeltmeler).

    ATOMIK: once .tmp'ye yazilir, sonra os.replace ile yerine konur. Dogrudan
    "w" ile acmak dosyayi ANINDA sifirliyordu ve 235 PNG taranirken (1-2 dk)
    manifest BOS kaliyordu; o pencerede okuyan tuketici sessizce bos veri
    aliyor. Gercekten yasandi: paralel bir OCR ajani manifest'i 0 bayt gordu
    (15 Eyl 2026).
    """
    yol = hedef / "manifest.csv"
    gecici = hedef / "manifest.csv.tmp"
    duzeltme = _duzeltmeleri_oku(hedef)
    toplam = sifir = duzeltilen = 0
    with gecici.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["dosya", "beklenen_soru", "sol_sutun", "sag_sutun", "sayfa_tipi", "kaynak"]
        )
        for f in dosyalar:
            with Image.open(f) as im:
                if im.size != BEKLENEN_BOYUT:
                    continue
                xler = soru_ikonlari(im, kanonik)
            soru = len(xler) >= SORU_ESIGI
            n = len(xler) if soru else 0
            sol = sum(1 for x in xler if x < IKON_SUTUN_ESIGI) if soru else 0
            sag = n - sol
            kaynak = "ikon"
            if f.name in duzeltme:
                n, sol, sag = duzeltme[f.name]
                soru = n >= SORU_ESIGI
                kaynak = "duzeltme"
                duzeltilen += 1
            toplam += n
            sifir += 0 if soru else 1
            w.writerow(
                [f.name, n, sol, sag, "soru" if soru else "kapak_veya_anlatim", kaynak]
            )
    gecici.replace(yol)  # atomik: tuketici yarim dosya gormez
    print(
        f"manifest: {yol.name} | beklenen toplam soru={toplam} | "
        f"soru sayfasi={len(dosyalar) - sifir} | sorusuz sayfa={sifir} | "
        f"dogrulanmis duzeltme={duzeltilen}"
    )


def _ozet_yaz(
    *,
    sayilar: tuple[int, int, int, int],
    cevap_yok: list[str] | None,
    sapanlar: list[str],
    tespit_yok: list[str],
    boyut_disi: list[str],
) -> None:
    """Tur sonu ozeti. Sessiz basari yok: her sapma sayiyla raporlanir."""
    tam, sutun, cevap, atlandi = sayilar
    print(f"yazildi: tam={tam} sutun={sutun} cevap={cevap} | atlandi={atlandi}")
    if cevap_yok is not None:
        print(f"cevap seridi bulunamayan sayfa: {len(cevap_yok)} -> {cevap_yok[:12]}")
    print(f"kanonige dusulen (sapma>{TOLERANS}px veya pencere temasi): {len(sapanlar)}")
    for s in sapanlar[:20]:
        print(f"  SAPMA {s}")
    if tespit_yok:
        print(
            f"tespit basarisiz (kanonik kullanildi): {len(tespit_yok)} -> {tespit_yok[:10]}"
        )
    if boyut_disi:
        print(
            f"{BEKLENEN_BOYUT} DEGIL (islenmedi): {len(boyut_disi)} -> {boyut_disi[:10]}"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kitap", required=True, help="screenshots altindaki klasor adi")
    ap.add_argument(
        "--sadece",
        choices=["tam", "sutun", "ikisi"],
        default="ikisi",
        help="hangi cikti uretilsin (varsayilan: ikisi)",
    )
    ap.add_argument(
        "--manifest",
        action="store_true",
        help="manifest.csv uret: sayfa basina beklenen soru sayisi + sutun dagilimi",
    )
    ap.add_argument(
        "--cevap",
        action="store_true",
        help="cevap/ altina sayfa alti cevap anahtari seridini yuksek zoom'la kirp",
    )
    ap.add_argument(
        "--force", action="store_true", help="mevcut ciktilari yeniden uret"
    )
    ap.add_argument("--limit", type=int, default=0, help="ilk N dosya (pilot)")
    args = ap.parse_args()

    kaynak = KOK / args.kitap
    if not kaynak.is_dir():
        print(f"HATA: klasor yok -> {kaynak}")
        return 2
    hedef = kaynak / f"temiz {args.kitap}"
    hedef_sutun = hedef / "sutun"
    hedef_cevap = hedef / "cevap"

    dosyalar = sorted(kaynak.glob("*.png"))
    if args.limit:
        dosyalar = dosyalar[: args.limit]
    if not dosyalar:
        print(f"HATA: PNG yok -> {kaynak}")
        return 2
    print(f"kaynak png: {len(dosyalar)}  ({dosyalar[0].name} .. {dosyalar[-1].name})")

    try:
        kanonik = modal_bbox(dosyalar)
    except OlcumHatasiError as e:
        print(f"OLCUM HATASI: {e}")
        return 2
    ust_kenar_dogrula(kanonik)
    kw, kh = kanonik[2] - kanonik[0], kanonik[3] - kanonik[1]
    print(f"kanonik sayfa kutusu: {kanonik}  ({kw}x{kh})")

    tam_yap = args.sadece in ("tam", "ikisi")
    sutun_yap = args.sadece in ("sutun", "ikisi")
    hedef.mkdir(exist_ok=True)
    if sutun_yap:
        hedef_sutun.mkdir(exist_ok=True)
        k_sol = ocr_olcegi(OLUK_SOL, kh)
        k_sag = ocr_olcegi(kw - OLUK_SAG, kh)
        print(
            f"sutun olcegi: sol x{k_sol:.2f} -> {round(OLUK_SOL * k_sol)}x{round(kh * k_sol)} | "
            f"sag x{k_sag:.2f} -> {round((kw - OLUK_SAG) * k_sag)}x{round(kh * k_sag)}"
        )

    if args.cevap:
        hedef_cevap.mkdir(exist_ok=True)

    yazildi_tam = yazildi_sutun = yazildi_cevap = atlandi = 0
    cevap_yok: list[str] = []
    sapanlar: list[str] = []
    boyut_disi: list[str] = []
    tespit_yok: list[str] = []

    for f in dosyalar:
        yol = SayfaYollari(
            tam=hedef / f.name,
            sol=hedef_sutun / f"{f.stem}_sol.png",
            sag=hedef_sutun / f"{f.stem}_sag.png",
            cevap_sol=hedef_cevap / f"{f.stem}_cevap_sol.png",
            cevap_sag=hedef_cevap / f"{f.stem}_cevap_sag.png",
        )
        gerekli = _gereken_isler(
            f,
            yol,
            tam=tam_yap,
            sutun=sutun_yap,
            cevap=args.cevap,
            force=args.force,
        )
        if not gerekli:
            atlandi += 1
            continue

        img = Image.open(f)
        if img.size != BEKLENEN_BOYUT:
            boyut_disi.append(f"{f.name} ({img.size[0]}x{img.size[1]})")
            continue

        bbox = _kutu_sec(img, kanonik, f.name, sapanlar, tespit_yok)
        t, s, c = _ciktilari_yaz(img, bbox, yol, gerekli)
        yazildi_tam += t
        yazildi_sutun += s
        yazildi_cevap += c
        if "cevap" in gerekli and c == 0:
            cevap_yok.append(f.name)

    if args.manifest:
        _manifest_yaz(hedef, dosyalar, kanonik)

    _ozet_yaz(
        sayilar=(yazildi_tam, yazildi_sutun, yazildi_cevap, atlandi),
        cevap_yok=cevap_yok if args.cevap else None,
        sapanlar=sapanlar,
        tespit_yok=tespit_yok,
        boyut_disi=boyut_disi,
    )
    return 1 if (boyut_disi or tespit_yok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
