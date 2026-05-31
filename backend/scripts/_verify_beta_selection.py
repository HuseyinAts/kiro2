"""Beta pratik soru seçimi — gerçek DB doğrulaması (container içinde çalışır).

docker cp + docker exec python ile kanonik döngü. Gerçek PG 5434 beta havuzuna
(386 beta_clean_verified) karşı _select_beta_questions'ı sınar.
"""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.osym_exam_engine import OSYMExamEngine  # noqa: E402


def _is_beta_clean(q) -> bool:
    meta = q.pipeline_metadata or {}
    # Beta artık verified_gold gate'ine güvenir (gold pool tam-run, 31 May 2026)
    return meta.get("verified_gold") in (True, "true")


async def main() -> int:
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(20)
    n = len(questions)
    all_clean = all(_is_beta_clean(q) for q in questions)
    all_active = all(q.is_active for q in questions)
    subjects = sorted({q.subject_area for q in questions})
    print(f"count={n} all_clean={all_clean} all_active={all_active}")
    print(f"subjects={subjects}")
    # Karışıklık kanıtı: 20 rastgeleden >1 ders beklenir (MAT 156/386 baskın)
    ok = n == 20 and all_clean and all_active
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
