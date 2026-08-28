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

Kullanim:
    python backend/scripts/quality/y11_konu_seed.py            # PROVA (geri alir)
    python backend/scripts/quality/y11_konu_seed.py --kalici   # KALICI
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

# Temiz MAT/TYT havuzunun kullandigi level-2 MAT.* kodlari.
# Liste burada SABIT degil -- kaynaktan cekilir; bu yalniz KAPSAM suzgecidir.
KAPSAM_SQL = """
WITH temiz AS (
    SELECT primary_topic_id FROM question_bank
    WHERE exam_type = 'TYT' AND subject_area = 'MATEMATIK'
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
WHERE th.code LIKE 'MAT.%' AND th.level = 2
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


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Canli topic_hierarchy MATEMATIK seed")
    ap.add_argument(
        "--kalici",
        action="store_true",
        help="KALICI YAZ. Verilmezse transaction GERI ALINIR (prova).",
    )
    a = ap.parse_args(argv)

    kaynak = await asyncpg.connect(f"{KOK}/kiro2_temp")
    hedef = await asyncpg.connect(f"{KOK}/kiro2")
    try:
        adaylar = await kaynak.fetch(KAPSAM_SQL)
        if not adaylar:
            raise SystemExit(
                "HATA: 0 aday -- yanlis-sifir, kapsam sorgusunu kontrol et."
            )

        ebeveyn = await hedef.fetchval(
            "SELECT id FROM topic_hierarchy WHERE code = $1", EBEVEYN_KOD
        )
        if not ebeveyn:
            raise SystemExit(
                f"HATA: canli '{EBEVEYN_KOD}' YOK -- ebeveyn zinciri kirik."
            )
        print(f"canli ebeveyn {EBEVEYN_KOD} = {ebeveyn}")

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
                    r["level"],
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
            mat = await hedef.fetchval(
                "SELECT count(*) FROM topic_hierarchy WHERE code LIKE 'MAT.%'"
            )
            yetim = await hedef.fetchval(
                "SELECT count(*) FROM topic_hierarchy c "
                "LEFT JOIN topic_hierarchy p ON p.id = c.parent_id "
                "WHERE c.parent_id IS NOT NULL AND p.id IS NULL"
            )
            yanlis_ebeveyn = await hedef.fetchval(
                "SELECT count(*) FROM topic_hierarchy WHERE code LIKE 'MAT.%' "
                "AND parent_id IS DISTINCT FROM $1",
                ebeveyn,
            )
            print("\nDOGRULAMA (transaction icinde)")
            print(f"  topic_hierarchy toplam : {toplam}")
            print(f"  MAT.* satir            : {mat}")
            print(f"  FK yetimi              : {yetim}   (0 olmali)")
            print(f"  yanlis ebeveynli MAT.* : {yanlis_ebeveyn}   (0 olmali)")
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
