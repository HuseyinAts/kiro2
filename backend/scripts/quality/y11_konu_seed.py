#!/usr/bin/env python
"""Canli `topic_hierarchy`'ye eksik MATEMATIK alt konularini ekler (varsayilan GERI ALIR).

NEDEN GEREKLI (20 Agu 2026 olcumu)
----------------------------------
Canli `topic_hierarchy` **26 satir** ve `subject_area='MATEMATIK'` olan **tek**
satiri var (`MAT.TRV`). `kiro2_temp`'in temiz MAT/TYT havuzu (5.420 soru) ise
43 ayri koda dagiliyor. Goc araci `y11_goc._canli_topic_id()` bilinmeyen kodda
`ValueError` firlatip DURUYOR (sessiz varsayilan yok, dogru davranis) -- yani
bu satirlar eklenmeden MAT/TYT gocunun buyuk kismi REDDEDILIR.

KAPSAM: yalniz **level-2 `MAT.*`** kodlari (ebeveyn `MAT`, canlida ZATEN VAR).
Olculdu: 20 aday, 1'i (MAT.TRV) zaten canlida -> **19 satir** eklenir ve temiz
havuzun kapsamasi %13,2 (718) -> **%92,9 (5.034/5.420)** olur; kazanc +4.316 soru.
Kalan 16 `TYT-MAT-*`/`AYT-MAT-*` kodu KAPSAM DISI: ebeveynsiz, `level` degerleri
tutarsiz (Istatistik level 5, Sayilar level 1) ve toplam 386 soru tasiyorlar --
ayri bir karar konusu, sessizce dahil edilmiyor.

UUID DRIFT -- OLCULDU
---------------------
Kod ayni, id farkli: canli `MAT` = 259066bd-... , temp `MAT` = c3261158-...
Yani `parent_id`'yi kaynaktan OLDUGU GIBI kopyalayan bir seed FK ihlali verir.
Emsal: canli `MAT.TRV`'nin **id'si temp'inkiyle birebir ayni**, `parent_id`'si
canli `MAT`'a yeniden yazilmis. Bu script ayni deseni izler:
    id       -> kaynaktan AYNEN (gelecekteki surukleme azalir; cakisma 0 olculdu)
    parent_id-> CANLI `MAT`'in id'si

`total_questions` = **0** yazilir, kaynaktaki sayi kopyalanmaz: o sayi temp
korpusunun sayimidir ve canli icin YANLIS olur. Denormalize onbellek; goc
ilerledikce yeniden sayilir. (Kural: ucucu sayiyi otorite gibi yazma.)

DERS-AGNOSTIK (7 Eyl 2026, TURKCE gocu)
---------------------------------------
Varsayilanlar MAT davranisini BIREBIR korur. TURKCE icin olculen yapi farkli:
temp'te `TUR.*` level-2 kodlarinin `parent_id`'si NULL ve `TYT-TR-01/02/03`
kodlari ebeveynsiz + level'lari tutarsiz (1, 1, 3). Bu yuzden iki ek parametre:
`--kod-deseni` birden cok LIKE deseni alir, `--yaz-level` verilirse level
kaynaktan kopyalanmaz, sabitlenir (TUR altinda hepsi 2). `--kaynak-level`
verilmezse level suzgeci uygulanmaz (MAT varsayilani 2'dir).

Kullanim:
    python backend/scripts/quality/y11_konu_seed.py            # PROVA (geri alir), MAT
    python backend/scripts/quality/y11_konu_seed.py --kalici   # KALICI, MAT
    python backend/scripts/quality/y11_konu_seed.py --ders TURKCE --ebeveyn TUR \\
        --kod-deseni "TUR.%" --kod-deseni "TYT-TR-%" --yaz-level 2 [--kalici]
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import asyncpg

_yeniden_ayarla = getattr(sys.stdout, "reconfigure", None)
if _yeniden_ayarla and (sys.stdout.encoding or "").lower().startswith("cp"):
    _yeniden_ayarla(encoding="utf-8", errors="replace")

KOK = "postgresql://postgres@localhost:5434"
EBEVEYN_KOD = "MAT"

# Temiz havuzun kullandigi konu kodlari. Liste burada SABIT degil -- kaynaktan
# cekilir; bu yalniz KAPSAM suzgecidir. $1 = ders (subject_area), $2 = LIKE
# desenleri, $3 = kaynak level suzgeci (NULL = suzme).
KAPSAM_SQL = """
WITH temiz AS (
    SELECT primary_topic_id FROM question_bank
    WHERE exam_type = 'TYT' AND subject_area = $1
      AND quality_review_status = 'auto_judged_high' AND is_active
      AND question_image_url ~ '_q[0-9]+\\.png$'
      AND correct_answer IN ('A','B','C','D','E')
      AND option_e IS NOT NULL AND btrim(option_e) <> ''
)
SELECT th.id, th.code, th.name_tr, th.name_en, th.level,
       th.osym_relevance, th.osym_frequency, th.average_difficulty,
       th.difficulty_level, th.subject_area, count(*) AS temiz_soru
FROM temiz t
JOIN topic_hierarchy th ON th.id = t.primary_topic_id
WHERE th.code LIKE ANY($2::text[])
  AND ($3::int IS NULL OR th.level = $3::int)
GROUP BY th.id, th.code, th.name_tr, th.name_en, th.level, th.osym_relevance,
         th.osym_frequency, th.average_difficulty, th.difficulty_level,
         th.subject_area
ORDER BY count(*) DESC
"""

EKLE = """
INSERT INTO topic_hierarchy
    (id, level, parent_id, code, name_tr, name_en, osym_relevance,
     osym_frequency, total_questions, average_difficulty, difficulty_level,
     subject_area, is_active)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0, $9, $10, $11, TRUE)
"""


def ebeveyn_belirle(kok: bool, ebeveyn_kod: str, bulunan_id: object) -> object:
    """Yazilacak `parent_id`: kok modunda NULL, degilse canli ebeveyn ZORUNLU.

    NEDEN KOK MODU (SOS olcumu, 7 Eyl 2026): kaynakta `SOS`/`SOC0*` kodlari
    EBEVEYNSIZ (kok) duruyor ve canlida hic yok. Canlinin kendisi de karisik:
    `TYT-KIM-01`, `KIM.ASI` gibi satirlar kok olarak duruyor. Yani kok yazmak
    uydurma bir hiyerarsi degil, mevcut sekli izlemek. Uydurma ebeveyn takmak
    (ornegin SOS'u TAR'in altina) konu agacini YANLIS yapardi.
    """
    if kok:
        return None
    if not bulunan_id:
        raise SystemExit(f"HATA: canli '{ebeveyn_kod}' YOK -- ebeveyn zinciri kirik.")
    return bulunan_id


def yanlis_ebeveyn_sorgusu(ebeveyn: object, desenler: list[str]) -> tuple[str, list]:
    """Ebeveyn invaryanti sorgusu; kok modunda "parent_id NULL olmali" olur.

    Kok modunda eski sorgu (`parent_id IS DISTINCT FROM NULL`) her satiri
    yanlis sayardi -- yani kontrol sessizce ters doner ve seed hic yazamazdi.
    """
    if ebeveyn is None:
        return (
            "SELECT count(*) FROM topic_hierarchy "
            "WHERE code LIKE ANY($1::text[]) AND parent_id IS NOT NULL",
            [desenler],
        )
    return (
        "SELECT count(*) FROM topic_hierarchy "
        "WHERE code LIKE ANY($2::text[]) AND parent_id IS DISTINCT FROM $1",
        [ebeveyn, desenler],
    )


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Canli topic_hierarchy konu seed")
    ap.add_argument(
        "--kalici",
        action="store_true",
        help="KALICI YAZ. Verilmezse transaction GERI ALINIR (prova).",
    )
    ap.add_argument("--ders", default="MATEMATIK", help="kaynak subject_area")
    ap.add_argument("--ebeveyn", default=EBEVEYN_KOD, help="canli ebeveyn kodu")
    ap.add_argument(
        "--kod-deseni",
        action="append",
        default=None,
        help="konu kodu LIKE deseni (tekrarlanabilir). Varsayilan: '<ebeveyn>.%%'",
    )
    ap.add_argument(
        "--kaynak-level",
        type=int,
        default=None,
        help="kaynakta bu level'daki kodlari al (MAT varsayilani 2; verilmezse suzme)",
    )
    ap.add_argument(
        "--yaz-level",
        type=int,
        default=None,
        help="canliya bu level ile yaz (verilmezse kaynaktan kopyalanir)",
    )
    ap.add_argument(
        "--kok",
        action="store_true",
        help="KOK olarak yaz (parent_id NULL); --ebeveyn aranmaz. Kaynakta "
        "ebeveyni olmayan kodlar icin (ornek: SOS, SOC0*).",
    )
    a = ap.parse_args(argv)
    ebeveyn_kod: str = a.ebeveyn
    desenler: list[str] = a.kod_deseni or [f"{ebeveyn_kod}.%"]
    kaynak_level = a.kaynak_level
    if kaynak_level is None and a.ders == "MATEMATIK" and a.kod_deseni is None:
        kaynak_level = 2  # MAT varsayilani birebir korunur

    kaynak = await asyncpg.connect(f"{KOK}/kiro2_temp")
    hedef = await asyncpg.connect(f"{KOK}/kiro2")
    try:
        adaylar = await kaynak.fetch(KAPSAM_SQL, a.ders, desenler, kaynak_level)
        if not adaylar:
            raise SystemExit(
                "HATA: 0 aday -- yanlis-sifir, kapsam sorgusunu kontrol et."
            )

        bulunan = (
            None
            if a.kok
            else await hedef.fetchval(
                "SELECT id FROM topic_hierarchy WHERE code = $1", ebeveyn_kod
            )
        )
        ebeveyn = ebeveyn_belirle(a.kok, ebeveyn_kod, bulunan)
        nere = (
            "KOK (parent_id NULL)"
            if a.kok
            else f"canli ebeveyn {ebeveyn_kod} = {ebeveyn}"
        )
        print(f"ders {a.ders} | desen {desenler} | {nere}")

        mevcut = {
            r["code"] for r in await hedef.fetch("SELECT code FROM topic_hierarchy")
        }
        mevcut_id = {
            r["id"] for r in await hedef.fetch("SELECT id FROM topic_hierarchy")
        }

        eklenecek = [r for r in adaylar if r["code"] not in mevcut]
        atlanan = [r["code"] for r in adaylar if r["code"] in mevcut]
        cakisan_id = [r["code"] for r in eklenecek if r["id"] in mevcut_id]
        if cakisan_id:
            raise SystemExit(
                f"HATA: id cakismasi {cakisan_id} -- sessizce devam edilmez."
            )

        print(
            f"aday {len(adaylar)} | zaten canlida {len(atlanan)} {atlanan} "
            f"| EKLENECEK {len(eklenecek)}"
        )
        acilan = sum(r["temiz_soru"] for r in eklenecek)
        print(f"bu kodlarin actigi temiz soru: {acilan}")

        tx = hedef.transaction()
        await tx.start()
        kalici_yaz = False
        try:
            for r in eklenecek:
                await hedef.execute(
                    EKLE,
                    r["id"],
                    a.yaz_level if a.yaz_level is not None else r["level"],
                    ebeveyn,
                    r["code"],
                    r["name_tr"],
                    r["name_en"],
                    r["osym_relevance"],
                    r["osym_frequency"],
                    r["average_difficulty"],
                    r["difficulty_level"],
                    r["subject_area"],
                )

            # --- transaction ICINDE dogrula ---
            toplam = await hedef.fetchval("SELECT count(*) FROM topic_hierarchy")
            desen_satir = await hedef.fetchval(
                "SELECT count(*) FROM topic_hierarchy WHERE code LIKE ANY($1::text[])",
                desenler,
            )
            yetim = await hedef.fetchval(
                "SELECT count(*) FROM topic_hierarchy c "
                "LEFT JOIN topic_hierarchy p ON p.id = c.parent_id "
                "WHERE c.parent_id IS NOT NULL AND p.id IS NULL"
            )
            sorgu, parametreler = yanlis_ebeveyn_sorgusu(ebeveyn, desenler)
            yanlis_ebeveyn = await hedef.fetchval(sorgu, *parametreler)
            print("\nDOGRULAMA (transaction icinde)")
            print(f"  topic_hierarchy toplam : {toplam}")
            print(f"  desene uyan satir      : {desen_satir}")
            print(f"  FK yetimi              : {yetim}   (0 olmali)")
            print(f"  yanlis ebeveynli satir : {yanlis_ebeveyn}   (0 olmali)")
            if yetim or yanlis_ebeveyn:
                raise SystemExit("HATA: invaryant ihlali -- transaction geri alinacak.")

            kalici_yaz = bool(a.kalici)
        finally:
            # TEK cikis noktasi: istisna olsa da olmasa da transaction KAPANIR.
            # (Kontrol akisi icin istisna kullanmak N818'i tetikliyordu ve
            #  "hata degil sinyal" olan bir sinifa Error soneki takmak yanlis
            #  olurdu -- bastirmak yerine yapiyi duzelttik.)
            if kalici_yaz:
                await tx.commit()
                print("\nKALICI YAZILDI.")
            else:
                await tx.rollback()
                print(
                    "\nPROVA -- transaction GERI ALINDI (kalici yazim icin --kalici)."
                )
    finally:
        await kaynak.close()
        await hedef.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
