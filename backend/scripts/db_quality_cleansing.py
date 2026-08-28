#!/usr/bin/env python3
"""
KIRO2 - Veritabanı Kalite ve Arındırma (Cleansing) Betiği
SRE Mimarisi: Sıfır-Kesinti (Zero-Downtime) Karantina Motoru

Bu betik:
1. Mükerrer soruları saptar, geçmiş çözüm verilerini canonical soruya aktarır
   ve kopyaları soft-delete (is_active=False) ile karantinaya alır.
2. Çöp metinleri (15 karakterden kısa) soft-delete ile karantinaya alır.
3. --dry-run (simülasyon) seçeneği ile verileri bozmadan rapor sunar.

KULLANIM:
python db_quality_cleansing.py --dry-run
python db_quality_cleansing.py --execute
"""

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_quality_cleansing")

async def main():
    parser = argparse.ArgumentParser(description="KIRO2 Veritabanı Kalite ve Karantina Arındırma Betiği")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Değişiklikleri kaydetmeden simülasyon modunda çalıştır.")
    group.add_argument("--execute", action="store_true", help="Değişiklikleri veritabanına uygula.")
    args = parser.parse_args()

    # Load DATABASE_URL from environment or .env.mvp
    db_url = None
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.mvp")
    if not os.path.exists(env_path):
        env_path = ".env.mvp"

    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("DATABASE_URL="):
                    db_url = line.strip().split("DATABASE_URL=", 1)[1]
                    break

    if not db_url:
        db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2")

    # Replace docker host with local loopback for external script execution
    if "host.docker.internal" in db_url:
        db_url = db_url.replace("host.docker.internal", "127.0.0.1")
    if "postgresql://" in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    logger.info("Veritabanına bağlanılıyor...")
    engine = create_async_engine(
        db_url,
        connect_args={
            "server_settings": {
                "statement_timeout": "10000"  # 10s statement timeout
            }
        }
    )

    try:
        async with engine.connect() as conn:
            # Set statement timeout
            await conn.execute(text("SET statement_timeout = '10s';"))

            if args.dry_run:
                logger.info("=== SİMÜLASYON MODU (DRY RUN) ETKİN - HİÇBİR VERİ DEĞİŞTİRİLMEYECEK ===")
            else:
                logger.warning("!!! UYGULAMA MODU (EXECUTE) ETKİN - DEĞİŞİKLİKLER KAYDEDİLECEK !!!")

            # ---------------------------------------------------------
            # 1. Aşama: Mükerrer Soruların Tespiti ve Temizliği
            # ---------------------------------------------------------
            logger.info("Mükerrer soru hash grupları sorgulanıyor...")

            dup_hashes_query = text("""
                SELECT soru_hash, COUNT(*) as cnt 
                FROM question_bank 
                GROUP BY soru_hash 
                HAVING COUNT(*) > 1;
            """)
            dup_hashes_res = await conn.execute(dup_hashes_query)
            dup_groups = dup_hashes_res.fetchall()

            logger.info(f"Toplam {len(dup_groups)} farklı mükerrer hash grubu bulundu.")

            total_duplicates_processed = 0
            total_answers_migrated = 0
            total_calibration_history_migrated = 0
            total_exam_questions_migrated = 0

            for group in dup_groups:
                hash_val, count = group

                # Fetch all questions sharing this hash
                # We sort by is_active DESC, times_asked DESC, created_at ASC to find the canonical item
                q_list_query = text("""
                    SELECT id, is_active, times_asked, created_at 
                    FROM question_bank 
                    WHERE soru_hash = :hash_val 
                    ORDER BY is_active DESC, times_asked DESC, created_at ASC;
                """)
                q_res = await conn.execute(q_list_query, {"hash_val": hash_val})
                questions = q_res.fetchall()

                if not questions or len(questions) < 2:
                    continue

                canonical = questions[0]
                duplicates = questions[1:]

                canonical_id = canonical[0]
                logger.info(f"Hash {hash_val}: Canonical Soru={canonical_id} seçildi. Kopyaları: {[d[0] for d in duplicates]}")

                for dup in duplicates:
                    dup_id = dup[0]
                    total_duplicates_processed += 1

                    if args.dry_run:
                        # Dry run reporting
                        # Get answer count
                        ans_count_res = await conn.execute(
                            text("SELECT COUNT(*) FROM student_answers WHERE question_id = :dup_id;"),
                            {"dup_id": dup_id}
                        )
                        ans_count = ans_count_res.scalar()

                        # Get calibration history count
                        cal_count_res = await conn.execute(
                            text("SELECT COUNT(*) FROM irt_calibration_history WHERE question_id = :dup_id;"),
                            {"dup_id": dup_id}
                        )
                        cal_count = cal_count_res.scalar()

                        # Get exam question association count
                        eq_count_res = await conn.execute(
                            text("SELECT COUNT(*) FROM exam_questions WHERE question_id = :dup_id;"),
                            {"dup_id": dup_id}
                        )
                        eq_count = eq_count_res.scalar()

                        logger.info(
                            f"[DRY-RUN SIMULATION] Soru ID {dup_id} soft-delete yapılacak.\n"
                            f"  -> {ans_count} öğrenci cevabı Soru {canonical_id}'ye aktarılacak.\n"
                            f"  -> {cal_count} kalibrasyon kaydı Soru {canonical_id}'ye aktarılacak.\n"
                            f"  -> {eq_count} sınav soru ataması Soru {canonical_id}'ye aktarılacak."
                        )

                        total_answers_migrated += ans_count
                        total_calibration_history_migrated += cal_count
                        total_exam_questions_migrated += eq_count
                    else:
                        # Execute mode with explicit transaction isolation
                        logger.info(f"Soru ID {dup_id} verileri Soru ID {canonical_id}'ye taşınıyor...")

                        # Use nested transactions for row-by-row updates to safely ignore IntegrityErrors
                        from sqlalchemy.exc import IntegrityError

                        # A. Transfer student answers row-by-row
                        ans_select = text("SELECT id FROM student_answers WHERE question_id = :dup_id;")
                        ans_rows = (await conn.execute(ans_select, {"dup_id": dup_id})).fetchall()

                        answers_moved = 0
                        for ans_row in ans_rows:
                            ans_row_id = ans_row[0]
                            try:
                                async with conn.begin_nested() as sp_row:
                                    update_ans_row = text("""
                                        UPDATE student_answers 
                                        SET question_id = :canonical_id 
                                        WHERE id = :ans_row_id;
                                    """)
                                    await conn.execute(update_ans_row, {"canonical_id": canonical_id, "ans_row_id": ans_row_id})
                                    answers_moved += 1
                            except IntegrityError:
                                # Conflict exists: student answered both. Safe to delete the duplicate answer record.
                                await conn.execute(
                                    text("DELETE FROM student_answers WHERE id = :ans_row_id;"),
                                    {"ans_row_id": ans_row_id}
                                )
                        total_answers_migrated += answers_moved

                        # B. Transfer calibration histories row-by-row
                        cal_select = text("SELECT id FROM irt_calibration_history WHERE question_id = :dup_id;")
                        cal_rows = (await conn.execute(cal_select, {"dup_id": dup_id})).fetchall()
                        for cal_row in cal_rows:
                            cal_row_id = cal_row[0]
                            try:
                                async with conn.begin_nested() as sp_row:
                                    await conn.execute(
                                        text("UPDATE irt_calibration_history SET question_id = :canonical_id WHERE id = :cal_row_id;"),
                                        {"canonical_id": canonical_id, "cal_row_id": cal_row_id}
                                    )
                                    total_calibration_history_migrated += 1
                            except IntegrityError:
                                await conn.execute(
                                    text("DELETE FROM irt_calibration_history WHERE id = :cal_row_id;"),
                                    {"cal_row_id": cal_row_id}
                                )

                        # C. Transfer exam questions row-by-row
                        eq_select = text("SELECT id FROM exam_questions WHERE question_id = :dup_id;")
                        eq_rows = (await conn.execute(eq_select, {"dup_id": dup_id})).fetchall()
                        for eq_row in eq_rows:
                            eq_row_id = eq_row[0]
                            try:
                                async with conn.begin_nested() as sp_row:
                                    await conn.execute(
                                        text("UPDATE exam_questions SET question_id = :canonical_id WHERE id = :eq_row_id;"),
                                        {"canonical_id": canonical_id, "eq_row_id": eq_row_id}
                                    )
                                    total_exam_questions_migrated += 1
                            except IntegrityError:
                                await conn.execute(
                                    text("DELETE FROM exam_questions WHERE id = :eq_row_id;"),
                                    {"eq_row_id": eq_row_id}
                                )

                        # D. Set duplicate question as inactive (Karantina)
                        deactivate_query = text("""
                            UPDATE question_bank 
                            SET is_active = false 
                            WHERE id = :dup_id;
                        """)
                        await conn.execute(deactivate_query, {"dup_id": dup_id})

                        logger.info(f"Soru ID {dup_id} karantinaya alındı. {answers_moved} adet cevap başarıyla kanonik kayda devredildi.")

            # ---------------------------------------------------------
            # 2. Aşama: Çöp Metinlerin (Short Text) Temizliği
            # ---------------------------------------------------------
            logger.info("15 karakterden kısa çöp sorular sorgulanıyor...")
            trash_query = text("SELECT id, question_text FROM question_bank WHERE LENGTH(question_text) < 15 AND is_active = true;")
            trash_res = await conn.execute(trash_query)
            trash_rows = trash_res.fetchall()

            logger.info(f"Toplam {len(trash_rows)} adet aktif çöp soru bulundu.")

            for row in trash_rows:
                q_id, q_text = row
                if args.dry_run:
                    logger.info(f"[DRY-RUN SIMULATION] Çöp soru karantinaya alınacak: ID={q_id}, Metin='{q_text}'")
                else:
                    deactivate_trash_query = text("UPDATE question_bank SET is_active = false WHERE id = :q_id;")
                    await conn.execute(deactivate_trash_query, {"q_id": q_id})
                    logger.info(f"Çöp soru karantinaya alındı: ID={q_id}")

            # Commit the transaction if executing
            if not args.dry_run:
                # Engine connect transaction commits automatically if using connection.begin()
                # or manually if we run on connection block. Let's make sure transaction is committed.
                await conn.execute(text("COMMIT;"))
                logger.info("Tüm değişiklikler başarıyla uygulandı ve COMMIT edildi!")

            # ---------------------------------------------------------
            # Raporlama ve Özet
            # ---------------------------------------------------------
            print("\n" + "="*60)
            print("                VERİ KALİTESİ ARINDIRMA RAPORU")
            print("="*60)
            print(f"Betiğin Çalışma Modu: {'SİMÜLASYON (Dry-run)' if args.dry_run else 'UYGULAMA (Execute)'}")
            print(f"Karantinaya Alınan Mükerrer Sayısı: {total_duplicates_processed}")
            print(f"Devredilen Öğrenci Cevap Sayısı: {total_answers_migrated}")
            print(f"Devredilen IRT Kalibrasyon Sayısı: {total_calibration_history_migrated}")
            print(f"Devredilen Sınav Sorusu Sayısı: {total_exam_questions_migrated}")
            print(f"Karantinaya Alınan Çöp Soru Sayısı: {len(trash_rows)}")
            print("="*60 + "\n")

    except Exception as e:
        logger.critical(f"ARINDIRMA SÜRECİNDE BEKLENMEDİK HATA: {e!s}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
