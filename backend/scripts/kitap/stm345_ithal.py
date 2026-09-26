"""345 2025 Start Matematik -- PASIF ithal.

KAYNAK VE TAVANI
----------------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri; sayfa karti (589, 43) -
(1331, 1020) = 742x977. 320 PNG; basili sayfa = dosya - 1.

KAPSAM
------
Yalniz 'SINAVA GECIS' test sayfalari (45 test x 2 sayfa = 90 sayfa, 371
soru). Isindirma Kosesi ve acik uclu alistirmalar kapsam disi (sahip
karari, 25 Eyl).

BIRIM = TEST, KONU = UNITE
-------------------------
Her test iki ardisik sayfa; test bandi unite adini basar. Kitap uniteyi
alt konuya bolmedigi icin sorular UNITE dugumune baglanir (0057, MAT
kokunun altinda MAT-345S25-Unn; `konu_eslesme_duzeyi` = 'unite').

CEVAP KAYNAGI: SAYFA ALTI CEVAP SERIDI
--------------------------------------
Anahtar kitabin KENDI basili seridinden iki bagimsiz gorsel okumayla
(A 5x sirali, B 7x ters sirali) okundu, 371/371 ayni; ucuncu kanal piksel
glif en-yakin-komsu (LOO 358/359), kapsam disi ve tereddutlu girdiler goz
ile (10x). Hicbir soru cozulmedi.

METIN
-----
10 grupta ayri okuyucularla kirpimdan; TAM ikinci okuma (on kayitli) ve
soluk '+' piksel taramasi. Render edilmemis isaretler `[??]` (6 soru,
`okunamaz_isaret` bayragi; 0039 dislama kurali aktiflestirmede disarida
birakir).

ORTME: ITHAL EDILIR, ISARETLENIR
--------------------------------
Okuyucu diskinin kenar halkasinda kitap murekkebi olculen 6 soru
`okuyucu_diski_ortme` bayragi tasir.

MUKERRER
--------
345_2025_start_matematik_mukerrer_adaylari.json (formulu koruyan 3-gram):
GUCLU aday 0, kitap ici tekrar 0. Bayrak yalniz GUCLU adaya konur.

ESKI HAT
--------
Ayni kaynak adini tasiyan 3 eski satir kitapta yok; 0058 ile pasif. Bu
ithal onlara DOKUNMAZ (id'leri farkli; `ayristir` yabanci korumasi).

BILINEN BORC
------------
  * Cozumler kitapta soru sayfasinda YOK; `explanation` bos.

Detay: veriseti/zkitap/cikti/STM_345_YONTEM.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz
from scripts.kitap.metin_olcum import (
    bloom_belirle,
    kelime_istatistik,
    morfoloji_karmasikligi,
    okunabilirlik,
    sik_bayraklari,
    soru_hash,
)

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
CIKTI = "veriseti/zkitap/cikti"
ONEK_DOSYA = f"{CIKTI}/345_2025_start_matematik"
VARSAYILAN_VERI = f"{ONEK_DOSYA}_metin.json"
VARSAYILAN_HARITA = f"{ONEK_DOSYA}_konu_haritasi.json"
VARSAYILAN_KUTULAR = f"{ONEK_DOSYA}_kirpim_kutulari.json"
VARSAYILAN_ANAHTAR = f"{ONEK_DOSYA}_cevap_anahtari.json"
VARSAYILAN_ORTME = f"{ONEK_DOSYA}_ortme_olcumu.json"
VARSAYILAN_MUKERRER = f"{ONEK_DOSYA}_mukerrer_adaylari.json"
KAYNAK_ADI = "345 2025 Start Matematik"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
MAT_KOK_KODU = "MAT"
KOD_ONEKI = "MAT-345S25"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/stm345_ithal.py"
CROP_ONEK = "STM345"
TELIF_NOTU = (
    "345 (UcDortBes) Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar KITABIN sayfa "
    "alti cevap seridinden iki bagimsiz gorsel okumayla alindi (371/371 ayni; "
    "piksel glif en-yakin-komsu ucuncu kanal; kapsam disi/tereddutlu girdiler "
    "goz ile). Sorular cozulmedi. Kirpim kutulari basili soru numarasindan "
    "(371/371). Transkripsiyon 10 grupta ayri okuyucularla kirpimdan; TAM "
    "ikinci okuma + soluk '+' taramasi; anahtar gosterilmedi. Detay: "
    "veriseti/zkitap/cikti/STM_345_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "sayfa_alti_serit_iki_okuma_371_371_ayni__piksel_nn_loo_358_359__"
    "kapsam_disi_12_tereddut_12_goz_10x__"
    "girdi_sayisi_esittir_basili_numara__test_iki_ardisik_sayfa"
)
CEVAP_KAYNAGI = "sayfa_alti_cevap_seridi"
CEVAP_KANALLARI = (
    "iki_okuma+piksel",
    "iki_okuma+piksel+tereddut(numara_surekliligi)",
    "iki_okuma+goz(10x)",
    "iki_okuma+goz(10x)+tereddut(numara_surekliligi)",
)
KIRPIM_SISTEMI = "sayfa_karti_589_43_1331_1020_sutun_ara_cizgisinden"
BEKLENEN_SORU = 371
BEKLENEN_TEST = 45
BEKLENEN_UNITE = 16
GORSEL_SIK = "(g\u00f6rsel \u015f\u0131k)"
OKUNAMAZ = "[??]"


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("sikler_gorsel"):
        b.append("sikler_gorsel")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_kusuru")
    if r.get("ortme"):
        b.append("okuyucu_diski_ortme")
    if r.get("mukerrer"):
        b.append("mukerrer_aday")
    if OKUNAMAZ in r["govde"] + "".join(sec.values()):
        b.append("okunamaz_isaret")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r["sikler"][h] for h in "ABCDE"}
    h = soru_hash(r["govde"], sec)
    n, u, ort = kelime_istatistik(r["govde"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["govde"], sec)
    kutu = r["kirpim_kutusu"]
    basili_sayfa = int(r["sayfa"]) - 1
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["govde"],
        "secenekler": sec,
        "correct_answer": r["cevap"],
        # GORSEL ADI: kirpim script'inin urettigi ad (BIRIM_SS.png).
        "question_image_url": f"/static/crops/{CROP_ONEK}/{r['dosya']}.png",
        "explanation": None,
        "source_page": basili_sayfa,
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["govde"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["govde"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": None,
        "osym_format_compliant": False,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "konu_eslesme_duzeyi": "unite",
            "konu_kaynagi": "unite_ayraci_ve_icindekiler_ve_test_baslik_bandi",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": basili_sayfa,
            "sutun": r["sutun"],
            "serit_sira": r["serit_sira"],
            "soru_no_basili": r["basili_no"],
            "birim_kodu": r["birim"],
            "birim_ici_sira": r["soru"],
            "test_adi": r["test_adi"],
            "kaynak_gorseli": f"{r['dosya']}.png",
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "cevap_okuma_kanali": r["cevap_kanali"],
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "cikmis_soru": False,
            "sekil_var": bool(r.get("sekil_var")),
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kaynak_kusuru": r.get("kaynak_kusuru") or None,
            "okuyucu_diski_ortme": r.get("ortme"),
            "mukerrer_aday": r.get("mukerrer"),
            "kirpim_kutusu": kutu,
            "kirpim_capa_kanali": r["capa_kanali"],
            "kirpim_koordinat_sistemi": KIRPIM_SISTEMI,
            "gorsel_kaynagi": "tam_soru_kirpimi",
            "metin_kaynagi": f"soru_kirpimi_gorsel_okuma_{r['okuma']}_tam_ikinci_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_742x977",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": ITHAL_ARACI,
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(konu_id)s, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
"""
_QC = """
INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, explanation, question_image_url, image_width, image_height)
VALUES (%(id)s, %(question_text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(e)s, %(correct_answer)s,
    NULL, %(question_image_url)s, %(image_width)s, %(image_height)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'MATEMATIK', %(grade_level)s,
    %(osym_format_compliant)s, %(osym_year)s, %(source_book)s,
    %(source_page)s, %(pipeline_metadata)s::json, %(morphology_complexity)s, %(word_count)s,
    %(unique_word_count)s, %(average_word_length)s, %(readability_score)s, 'PENDING')
"""
_QS = """
INSERT INTO question_statistics (id, difficulty_level, irt_based_difficulty, student_success_rate,
    difficulty_update_count, irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
    is_calibrated, calibration_sample_size, calibration_quality_score, times_asked, times_correct,
    times_wrong, times_skipped, average_response_time, median_response_time, exposure_rate,
    quality_score, quality_review_status)
VALUES (%(id)s, 'MEDIUM', 'medium', 0.5, 0, 1.0, 0.0, 0.2, 1.0, FALSE, 0, 0.0, 0, 0, 0, 0, 0.0, 0.0, 0.0,
    100.0, 'pending')
"""


def satirlari_bagla(
    veri: dict,
    harita: dict,
    kutular: dict,
    anahtar: dict,
    *,
    ortme: dict,
    mukerrer: dict,
) -> list[dict[str, Any]]:
    """Metin, unite haritasi, kirpim kutusu, cevap anahtari, ortme ve mukerrer adaylarini birlestirir.

    Birlestirme anahtari (test kodu, test ici sira). BASILI numaranin test ici
    siraya esitligi AYRICA dogrulanir (bu kitapta 371/371 kutu numara capali).
    """
    test = {t["birim"]: t for t in harita["testler"]}
    unite = {u["kod"] for u in harita["uniteler"]}
    kutu = {(k["birim"], k["soru"]): k for k in kutular["kutular"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    ortulen: dict[tuple[str, int], list] = {}
    for o in ortme["ortme"]:
        ortulen.setdefault((o["birim"], o["soru"]), []).append(o["simge"])
    guclu = {
        a["dosya"]: {
            k: a[k] for k in ("db_id", "db_kaynak", "govde_3gram", "ayni_sik_sayisi")
        }
        for a in mukerrer["adaylar"]
        if a["guclu"]
    }
    satir = []
    for s in veri["sorular"]:
        kod, sira = s["dosya"].rsplit("_", 1)
        sira_i = int(sira)
        k = kutu[(kod, sira_i)]
        if s["basili_no"] != sira_i:
            raise ValueError(f"{s['dosya']}: basili {s['basili_no']} != sira {sira_i}")
        t = test[kod]
        if t["unite"] not in unite:
            raise ValueError(f"{kod}: unite {t['unite']} haritada yok")
        c = cevap[(kod, sira_i)]
        if (k["dosya"], k["sutun"], k["serit_sira"]) != (
            c["dosya"],
            c["sutun"],
            c["serit_sira"],
        ):
            raise ValueError(
                f"{s['dosya']}: kutu ile cevap anahtari ayni soruyu gostermiyor"
            )
        if k["dosya"] not in t["sayfalar"]:
            raise ValueError(
                f"{s['dosya']}: sayfa {k['dosya']} testin sayfalarinda degil"
            )
        satir.append(
            {
                **s,
                "birim": kod,
                "soru": sira_i,
                "sayfa": k["dosya"],
                "sutun": k["sutun"],
                "serit_sira": k["serit_sira"],
                "test_adi": t["test_adi"],
                "konu_kodu": t["unite"],
                "cevap": c["cevap"],
                "cevap_kanali": c["kaynak"],
                "sikler_gorsel": all(v == GORSEL_SIK for v in s["sikler"].values()),
                "kirpim_kutusu": k["kutu"],
                "capa_kanali": k["capa_kanali"],
                "ortme": ortulen.get((kod, sira_i)),
                "mukerrer": guclu.get(s["dosya"]),
            }
        )
    return satir


def sekil_ikizleri(kayitlar: list[dict[str, Any]]) -> int:
    """Ayni metin + ayni bes sik, FARKLI sekil: kimligi kirpimla ayristirir.

    soru_hash formulu (metin + sikler) ortak altyapi oldugu icin DEGISTIRILMEZ;
    yalniz bu grupta id = uuid5(hash | sekil | kirpim adi) olur (mat345tyt /
    acil25_geo_ithal ile ayni kural). Grup uyelerinden biri sekilsizse
    ayristirma YAPILMAZ; on kontrol 'ayni hash iki kez' ile durur.
    """
    grup: dict[str, list[dict[str, Any]]] = {}
    for k in kayitlar:
        grup.setdefault(k["soru_hash"], []).append(k)
    n = 0
    for h, g in grup.items():
        if len(g) < 2 or not all(k["pipeline_metadata"]["sekil_var"] for k in g):
            continue
        n += 1
        adlar = [k["pipeline_metadata"]["kaynak_gorseli"] for k in g]
        for k in g:
            ad = k["pipeline_metadata"]["kaynak_gorseli"]
            k["id"] = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{h}|sekil|{ad}"))
            k["pipeline_metadata"]["sekil_ikizi_ile"] = [a for a in adlar if a != ad]
            k["pipeline_metadata"]["bayraklar"].append("sekil_ikizi")
    return n


def _yapisal_kapilar(
    veri: dict, harita: dict, kutular: dict, anahtar: dict
) -> list[str]:
    """Bu kitabin tasiyici sayimlari -- sessizce kayan bir satir olmasin."""
    hata = []
    sorular = veri["sorular"]
    if len(sorular) != BEKLENEN_SORU:
        hata.append(f"soru sayisi {len(sorular)} != {BEKLENEN_SORU}")
    if len(harita["testler"]) != BEKLENEN_TEST:
        hata.append(f"test sayisi {len(harita['testler'])} != {BEKLENEN_TEST}")
    if len(harita["uniteler"]) != BEKLENEN_UNITE:
        hata.append(f"unite sayisi {len(harita['uniteler'])} != {BEKLENEN_UNITE}")
    if sum(t["soru_sayisi"] for t in harita["testler"]) != BEKLENEN_SORU:
        hata.append(f"harita soru toplami {BEKLENEN_SORU} degil")
    if len(anahtar["cevaplar"]) != BEKLENEN_SORU:
        hata.append(f"anahtar sayisi {len(anahtar['cevaplar'])} != {BEKLENEN_SORU}")
    if len(kutular["kutular"]) != BEKLENEN_SORU:
        hata.append(f"kutu sayisi {len(kutular['kutular'])} != {BEKLENEN_SORU}")
    if len({s["dosya"] for s in sorular}) != len(sorular):
        hata.append("ayni kirpim iki kez okunmus")
    # Transkripsiyon anahtardan BAGIMSIZ kanal olmali.
    sizan = [s for s in sorular if {"cevap", "correct_answer"} & set(s)]
    if sizan:
        hata.append(f"{len(sizan)} metin satirinda cevap alani var -- kanal kirlendi")
    # Kapsam: cikmis soru kutusu bu kitapta yok; etiket gelirse bicim kurulmamistir.
    etiketli = [s["dosya"] for s in sorular if s.get("etiket")]
    if etiketli:
        hata.append(
            f"{len(etiketli)} soruda etiket var -- cikmis soru bicimi kurulmadi"
        )
    return hata


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:
    """Ithal oncesi ic tutarlilik -- bir tanesi bile varsa ithal baslamaz."""
    hata = []
    gorulen: set[str] = set()
    for k in kayitlar:
        sec = k["secenekler"]
        if len(sec) != 5 or any(h not in sec for h in "ABCDE"):
            hata.append(f"{k['id']}: 5 sik degil ({sorted(sec)})")
        if k["correct_answer"] not in set("ABCDE"):
            hata.append(f"{k['id']}: cevap {k['correct_answer']!r} A-E degil")
        elif not (sec.get(k["correct_answer"]) or "").strip():
            hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        if not (k["konu_kodu"] or "").startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {k['konu_kodu']!r} {KOD_ONEKI}* degil")
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if pm["cevap_okuma_kanali"] not in CEVAP_KANALLARI:
            hata.append(
                f"{k['id']}: taninmayan cevap okuma kanali {pm['cevap_okuma_kanali']!r}"
            )
        if not pm["kirpim_kutusu"] or not k["question_image_url"]:
            hata.append(f"{k['id']}: kirpim yok -- bu kitapta her sorunun kutusu var")
        if pm["soru_no_basili"] != pm["birim_ici_sira"]:
            hata.append(f"{k['id']}: basili numara test ici siraya esit degil")
        if pm["basili_sayfa"] != pm["sayfa_dosya_no"] - 1:
            hata.append(f"{k['id']}: basili sayfa != dosya - 1")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur."""
    kok = conn.execute(
        "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (MAT_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{MAT_KOK_KODU} kok konusu yok"
    kodlar = sorted({k["konu_kodu"] for k in kayitlar})
    konular: dict[str, str] = dict(
        conn.execute(
            "SELECT code, id FROM topic_hierarchy WHERE code = ANY(%s)", (kodlar,)
        ).fetchall()
    )
    eksik = set(kodlar) - set(konular)
    if eksik:
        return (
            f"{len(eksik)} unite kodu agacta yok: {sorted(eksik)[:5]}. "
            "0057_stm345_konu_agaci kosmadi mi? Kok dugume dusurup "
            "sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    print("unite dagilimi:")
    for kod, adet in sorted(sayac.items()):
        print(f"  {adet:5d}  {kod}")
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print(
        "cevap kanali      :",
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)),
    )
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}")


def _hazirla(yollar: dict[str, Path]) -> list[dict[str, Any]] | None:
    """Dosyalari okur, kapilardan gecirir, kayitlari uretir (None = DURDU)."""
    oku = {ad: json.loads(p.read_text(encoding="utf-8")) for ad, p in yollar.items()}
    yapisal = _yapisal_kapilar(
        oku["veri"], oku["harita"], oku["kutular"], oku["anahtar"]
    )
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun buldu; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(
        f"yapisal kapi: {BEKLENEN_SORU} soru + {BEKLENEN_TEST} test + {BEKLENEN_UNITE} unite + "
        f"{BEKLENEN_SORU} anahtar + {BEKLENEN_SORU} kutu + cevap sizintisi yok -- TEMIZ"
    )
    satirlar = satirlari_bagla(
        oku["veri"],
        oku["harita"],
        oku["kutular"],
        oku["anahtar"],
        ortme=oku["ortme"],
        mukerrer=oku["mukerrer"],
    )
    print(f"veri setinde {len(satirlar)} soru")
    kayitlar = [kayit_uret(r) for r in satirlar]
    ikiz = sekil_ikizleri(kayitlar)
    if ikiz:
        print(f"sekil ikizi: {ikiz} grup (ayni metin + ayni sikler, farkli sekil)")
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return None
    print(
        "on kontrol: 5 sik + A-E cevap + dolu anahtar sikki + dolu metin "
        f"+ {KOD_ONEKI} unite kodu + serit kaynagi + kutu/gorsel + basili no "
        "+ basili sayfa + benzersiz hash -- TEMIZ"
    )
    return kayitlar


def ithal(yollar: dict[str, Path], dsn: str, yaz: bool) -> int:
    kayitlar = _hazirla(yollar)
    if kayitlar is None:
        return 2
    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2
        yeni, _bizim, yabanci = ayristir(conn, kayitlar, KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)
        _ozet(yeni or kayitlar)
        if not yaz:
            print("(--yaz verilmedi; hicbir sey yazilmadi)")
            return 0
        with conn.transaction():
            for k in yeni:
                s = k["secenekler"]
                kutu = k["pipeline_metadata"]["kirpim_kutusu"]
                conn.execute(_QB, k)
                conn.execute(
                    _QC,
                    {
                        "id": k["id"],
                        "question_text": k["question_text"],
                        "a": s["A"],
                        "b": s["B"],
                        "c": s["C"],
                        "d": s["D"],
                        "e": s["E"],
                        "correct_answer": k["correct_answer"],
                        "question_image_url": k["question_image_url"],
                        "image_width": kutu[2] - kutu[0],
                        "image_height": kutu[3] - kutu[1],
                    },
                )
                conn.execute(
                    _QM,
                    {
                        **k,
                        "grade_level": SINIF_DUZEYI,
                        "source_book": KAYNAK_ADI,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})
        satir = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s AND m.pipeline_metadata->>'ithal_araci' = %s""",
            (KAYNAK_ADI, ITHAL_ARACI),
        ).fetchone()
        if satir is None:  # pragma: no cover  # count(*) hep satir dondurur
            raise RuntimeError("dogrulama sorgusu satir dondurmedi")
        n, aktif, kapida = satir
        print(f"YAZILDI: {len(yeni)} yeni satir")
        print(
            f"DB'de bu ithalin satirlari: toplam {n}, is_active {aktif}, kapidan gecen {kapida}"
        )
        if aktif or kapida:
            print("HATA: pasif ithal sozlesmesi bozuldu")
            return 3
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument("--harita", default=VARSAYILAN_HARITA)
    p.add_argument("--kutular", default=VARSAYILAN_KUTULAR)
    p.add_argument("--anahtar", default=VARSAYILAN_ANAHTAR)
    p.add_argument("--ortme", default=VARSAYILAN_ORTME)
    p.add_argument("--mukerrer", default=VARSAYILAN_MUKERRER)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    p.add_argument(
        "--kuru", action="store_true", help="DB'ye hic baglanma, yalniz kapilari kos"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    yollar = {
        "veri": Path(args.veri),
        "harita": Path(args.harita),
        "kutular": Path(args.kutular),
        "anahtar": Path(args.anahtar),
        "ortme": Path(args.ortme),
        "mukerrer": Path(args.mukerrer),
    }
    if args.kuru:
        kayitlar = _hazirla(yollar)
        if kayitlar is None:
            return 2
        _ozet(kayitlar)
        print("(--kuru: DB'ye baglanilmadi)")
        return 0
    return ithal(yollar, args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
