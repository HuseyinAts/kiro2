"""
Pool-growth pilot prep (Phase 0) — Top-1 (garble ön-eleme) + pilot extraction.

1. coherent=true (pipeline_metadata) üzerinde char-trigram garble LM eğit.
2. unverified+pending havuzdan reproducible stratified pilot çek (seed 42).
3. Pilot'u garble skorla; readable (skor < EŞİK) alt-kümeyi ayır.
4. readable JSONL emit et (workflow çift-blind solve için).

ÇIKTI: /tmp/pool_pilot_readable.jsonl  +  /tmp/pool_pilot_garbled.jsonl
correct_answer JSONL'de VAR ama solver prompt'una GİRMEYECEK (script karşılaştırır).
Reproducible. DB read-only.
"""

import asyncio
import json
import math
import random
import re
from collections import Counter, defaultdict

from sqlalchemy import text

from core.database import db_manager

SEED = 42
PILOT_N = 120  # stratified pilot size
GARBLE_THRESHOLD = 4.5  # memory: >=4.5 garble tail (popülasyonda ~0, çoğu yabancı-dil)
TR = "abcçdefgğhıijklmnoöprsştuüvyz"


def norm(t: str) -> str:
    return t.replace("I", "ı").replace("İ", "i").lower()


def tokens(t: str) -> list[str]:
    return [w for w in re.findall(r"[a-zçğıöşü]+", norm(t or "")) if len(w) >= 3]


# ---- char-trigram model ----
TRI: dict = defaultdict(Counter)
CTX: Counter = Counter()
V = len(TR) + 2


def add_word(w: str) -> None:
    s = "^^" + w + "$"
    for i in range(2, len(s)):
        ctx = s[i - 2 : i]
        TRI[ctx][s[i]] += 1
        CTX[ctx] += 1


def word_surprisal(w: str) -> tuple[float, int]:
    s = "^^" + w + "$"
    bits, n = 0.0, 0
    for i in range(2, len(s)):
        ctx, ch = s[i - 2 : i], s[i]
        num = TRI[ctx][ch] + 0.1
        den = CTX[ctx] + 0.1 * V
        bits += -math.log2(num / den)
        n += 1
    return bits, n


def text_score(tks: list[str]):
    tb, tn = 0.0, 0
    for w in tks:
        b, n = word_surprisal(w)
        tb += b
        tn += n
    if tn < 12:
        return None
    return tb / tn


async def main() -> None:
    async with db_manager.get_session() as s:
        # 1. train set
        rows = (
            await s.execute(
                text(
                    "SELECT question_text FROM question_bank "
                    "WHERE pipeline_metadata->>'student_coherent'='true'"
                )
            )
        ).all()
        for (qt,) in rows:
            for w in tokens(qt):
                add_word(w)
        print(
            f"garble LM eğitildi: {len(rows)} coherent soru, {len(TRI)} trigram bağlam"
        )

        # 2. stratified pilot — her subject'ten orantılı, reproducible
        pool = (
            await s.execute(
                text(
                    """SELECT id::text, subject_area, exam_type, question_text,
                              option_a, option_b, option_c, option_d, option_e,
                              correct_answer, quality_review_status
                       FROM question_bank
                       WHERE quality_review_status IN ('unverified','pending')
                         AND is_active=true
                         AND question_text IS NOT NULL"""
                )
            )
        ).all()
        by_subj: dict = defaultdict(list)
        for r in pool:
            by_subj[r[1] or "(null)"].append(r)
        rng = random.Random(SEED)
        # orantılı kota
        total = len(pool)
        pilot = []
        for subj, items in sorted(by_subj.items(), key=lambda x: -len(x[1])):
            quota = max(1, round(PILOT_N * len(items) / total))
            rng.shuffle(items)
            pilot.extend(items[:quota])
        rng.shuffle(pilot)
        pilot = pilot[:PILOT_N]
        print(f"pilot çekildi: {len(pilot)} soru ({len(by_subj)} subject)")

        # 3. garble skor + readable ayrımı
        readable, garbled = [], []
        for r in pilot:
            (qid, subj, exam, qt, a, b, c, d, e, ca, st) = r
            sc = text_score(tokens(qt))
            rec = {
                "id": qid,
                "subject_area": subj,
                "exam_type": exam,
                "question_text": qt,
                "options": {"A": a, "B": b, "C": c, "D": d, "E": e},
                "correct_answer": ca,
                "status": st,
                "garble_score": round(sc, 2) if sc is not None else None,
            }
            if sc is not None and sc >= GARBLE_THRESHOLD:
                garbled.append(rec)
            else:
                readable.append(rec)

        with open("/tmp/pool_pilot_readable.jsonl", "w", encoding="utf-8") as f:
            for rec in readable:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open("/tmp/pool_pilot_garbled.jsonl", "w", encoding="utf-8") as f:
            for rec in garbled:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(
            f"readable: {len(readable)}  garbled(>= {GARBLE_THRESHOLD}): {len(garbled)}"
        )
        # subject dağılımı
        dist: Counter = Counter(r["subject_area"] for r in readable)
        print("readable subject dağılımı:", dict(dist.most_common()))


if __name__ == "__main__":
    asyncio.run(main())
