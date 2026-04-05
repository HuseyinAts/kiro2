"""
_analyze_performance() icine is_correct ve times_asked geri yazma ekle.
Dosyayi geri almak icin: git diff backend/core/osym_exam_engine.py
"""

path = r"C:\Users\husey\kiro2\backend\core\osym_exam_engine.py"

with open(path, encoding="utf-8") as f:
    content = f.read()

# ---------- PATCH 1: for dongusunu is_correct takibi yapacak sekilde guncelle ----------
OLD_LOOP = '''                for question_id, student_answer in session_data.answers.items():
                    correct_answer = correct_answers_map.get(question_id)

                    if (
                        correct_answer
                        and student_answer
                        and correct_answer.strip().upper()
                        == student_answer.strip().upper()
                    ):
                        correct_answers += 1
                    else:
                        wrong_answers += 1'''

NEW_LOOP = '''                # is_correct takibi: (question_id, bool) listesi
                is_correct_results: list[tuple[str, bool]] = []

                for question_id, student_answer in session_data.answers.items():
                    correct_answer = correct_answers_map.get(question_id)
                    is_corr = bool(
                        correct_answer
                        and student_answer
                        and correct_answer.strip().upper()
                        == student_answer.strip().upper()
                    )
                    if is_corr:
                        correct_answers += 1
                    else:
                        wrong_answers += 1
                    is_correct_results.append((question_id, is_corr))

                # --- BUG FIX: is_correct geri yaz (student_answers tablosu) ---
                if is_correct_results:
                    for q_id, is_corr in is_correct_results:
                        await db_session.execute(
                            update(StudentAnswer)
                            .where(
                                and_(
                                    StudentAnswer.exam_session_id == session_data.session_id,
                                    StudentAnswer.question_id == q_id,
                                )
                            )
                            .values(is_correct=is_corr)
                        )

                    # --- BUG FIX: times_asked / times_correct batch update ---
                    all_answered_ids = list(session_data.answers.keys())
                    correct_ids = [q for q, ok in is_correct_results if ok]

                    if all_answered_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(all_answered_ids))
                            .values(times_asked=Question.times_asked + 1)
                        )
                    if correct_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(correct_ids))
                            .values(times_correct=Question.times_correct + 1)
                        )

                    await db_session.commit()
                    logger.info(
                        f"is_correct + times_asked guncellendi: "
                        f"{len(is_correct_results)} cevap, {len(correct_ids)} dogru",
                        extra_data={"session_id": session_data.session_id},
                    )'''

if OLD_LOOP not in content:
    print("HATA: Degistirilecek kod bulunamadi!")
    print("Muhtemelen dosya farkli versiyon. Ilk 10 satirini kontrol et:")
    idx = content.find("for question_id, student_answer in session_data.answers")
    print(repr(content[idx:idx+300]))
else:
    new_content = content.replace(OLD_LOOP, NEW_LOOP, 1)
    assert new_content != content, "Degisiklik yapilmadi!"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"OK: _analyze_performance() guncellendi")
    print(f"  Eski: {content.count(chr(10))+1} satir")
    print(f"  Yeni: {new_content.count(chr(10))+1} satir")
    print(f"  Fark: +{new_content.count(chr(10)) - content.count(chr(10))} satir")
