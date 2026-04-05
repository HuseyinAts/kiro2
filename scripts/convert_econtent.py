# -*- coding: utf-8 -*-
import re, json, uuid, sys

TOPIC_MAP = {
    ("TYT Matematik", "Kesirler"):       "b311c03c-9a43-54e3-a9ca-bb9e1ab23fdd",
    ("TYT Matematik", "Ters Orant"):     "b311c03c-9a43-54e3-a9ca-bb9e1ab23fdd",
    ("TYT Matematik", "Yüzde"):          "b311c03c-9a43-54e3-a9ca-bb9e1ab23fdd",
    ("TYT Matematik", "Denklem"):        "b28b6dc5-6ebf-5a35-aad3-9c3cd8cb7625",
    ("TYT Matematik", "Üçgenler"):       "1c0fea32-d7ea-53fc-9b30-853f15f736b2",
    ("TYT Matematik", "Logaritma"):      "1a3dc570-605c-5fe3-8936-f465d35ef46c",
    ("TYT Matematik", "Fonksiyonlar"):   "bc97a7b8-3c6f-5e97-b18d-a25c6ed097f1",
    ("TYT Matematik", "Daire"):          "f60d9926-8463-5773-9e89-42905d1f2b7e",
    ("TYT Türkçe",    "Yazım"):          "cf869f6f-ffd1-5d72-8411-8112408166b0",
    ("TYT Türkçe",    "Anlatım"):        "cf869f6f-ffd1-5d72-8411-8112408166b0",
    ("TYT Türkçe",    "Sözcükte"):       "507c41d7-b8d9-5814-9faa-fbe0cb202e6c",
    ("TYT Türkçe",    "Cümle"):          "cf869f6f-ffd1-5d72-8411-8112408166b0",
    ("TYT Türkçe",    "Fiiller"):        "cf869f6f-ffd1-5d72-8411-8112408166b0",
    ("TYT Fizik",     "Hareket"):        "7bf2bfec-1514-5af4-8938-fbe1df9d2c89",
    ("TYT Fizik",     "Isı"):            "b4f7c702-a087-5573-b412-ee627f1a22d8",
    ("AYT Fizik",     "Dinamik"):        "4b2aa943-71ae-5824-8d7d-ec94b1dd7cbc",
    ("AYT Fizik",     "Elektrik"):       "b4f7c702-a087-5573-b412-ee627f1a22d8",
    ("AYT Fizik",     "Optik"):          "4d454370-3c78-5984-9903-a52335eb0df4",
    ("AYT Fizik",     "Dalgalar"):       "4d454370-3c78-5984-9903-a52335eb0df4",
    ("TYT Kimya",     "Periyodik"):      "8978f24a-451e-535b-8a6a-7cfdb1dfca6a",
    ("TYT Kimya",     "Asit-Baz"):       "a6c265f6-b562-5ef1-9aa9-0b92465e14e1",
    ("AYT Kimya",     "Termokimya"):     "a6c265f6-b562-5ef1-9aa9-0b92465e14e1",
    ("AYT Kimya",     "Kimyasal"):       "d8bb8dfd-00a2-5a7d-ae77-6bb74db8b812",
    ("AYT Kimya",     "Asit-Baz"):       "a6c265f6-b562-5ef1-9aa9-0b92465e14e1",
    ("AYT Kimya",     "Periyodik"):      "8978f24a-451e-535b-8a6a-7cfdb1dfca6a",
    ("TYT Biyoloji",  "Fotosentez"):     "e844444e-8281-5a23-9225-007c3a912818",
    ("AYT Biyoloji",  "Genetik"):        "380875d6-ab28-52d5-8c9b-11035c06ed2c",
    ("AYT Biyoloji",  "Hücre"):          "e844444e-8281-5a23-9225-007c3a912818",
    ("AYT Biyoloji",  "Proteinler"):     "e844444e-8281-5a23-9225-007c3a912818",
    ("TYT Coğrafya",  "Türkiye"):        "136e1665-c1a1-58e1-a542-d760538424d0",
    ("TYT Coğrafya",  "İklim"):          "7d675ae6-0020-4c1c-87dd-f03a8654bafa",
    ("TYT Tarih",     "Osmanlı"):        "5f3a7f45-0b66-599f-ad41-e5af26d4da75",
    ("TYT Vatandaşlık","Temel"):         "05c15a90-24b4-47cd-b266-4029c5ee9047",
    ("AYT Matematik", "Limit"):          "a59a54b7-2bb1-54f1-bdba-d14af9170966",
    ("AYT Matematik", "Türev"):          "07f54b84-2116-5970-a53d-90434a205676",
    ("AYT Matematik", "İntegral"):       "1838a15e-bea9-58ff-b8d3-560f2902c21a",
    ("AYT Matematik", "Analitik"):       "10624405-6671-5118-ad52-08295812a3b6",
    ("AYT Matematik", "Diziler"):        "a75144ef-8fb2-54fd-a9b9-eac809f4256a",
    ("AYT Matematik", "Logaritma"):      "1a3dc570-605c-5fe3-8936-f465d35ef46c",
}

SUBJECT_FALLBACK = {
    "TYT Matematik":   "bcbe6208-003a-5133-bcf4-9aedc3214d7e",
    "AYT Matematik":   "07f54b84-2116-5970-a53d-90434a205676",
    "TYT Türkçe":      "cf869f6f-ffd1-5d72-8411-8112408166b0",
    "TYT Fizik":       "7bf2bfec-1514-5af4-8938-fbe1df9d2c89",
    "AYT Fizik":       "4b2aa943-71ae-5824-8d7d-ec94b1dd7cbc",
    "TYT Kimya":       "b98e65f1-b27d-5348-ae97-0620f40bff1c",
    "AYT Kimya":       "d8bb8dfd-00a2-5a7d-ae77-6bb74db8b812",
    "TYT Biyoloji":    "e844444e-8281-5a23-9225-007c3a912818",
    "AYT Biyoloji":    "380875d6-ab28-52d5-8c9b-11035c06ed2c",
    "TYT Coğrafya":    "136e1665-c1a1-58e1-a542-d760538424d0",
    "TYT Tarih":       "5f3a7f45-0b66-599f-ad41-e5af26d4da75",
    "TYT Vatandaşlık": "05c15a90-24b4-47cd-b266-4029c5ee9047",
    "YDT İngilizce":   "f521bf6d-b97e-5879-ab2c-6ce7eb4299f6",
}

SUBJECT_AREA = {
    "TYT Matematik":"MATEMATIK", "AYT Matematik":"MATEMATIK",
    "TYT Türkçe":"TURKCE", "TYT Fizik":"FIZIK", "AYT Fizik":"FIZIK",
    "TYT Kimya":"KIMYA", "AYT Kimya":"KIMYA",
    "TYT Biyoloji":"BIYOLOJI", "AYT Biyoloji":"BIYOLOJI",
    "TYT Coğrafya":"COGRAFYA", "TYT Tarih":"TARIH",
    "TYT Vatandaşlık":"SOSYAL", "YDT İngilizce":"INGILIZCE",
}

def get_topic_id(subject, topic):
    for (s, t), tid in TOPIC_MAP.items():
        if subject == s and topic.startswith(t):
            return tid
    return SUBJECT_FALLBACK.get(subject, "bcbe6208-003a-5133-bcf4-9aedc3214d7e")

def diff_level(b):
    if b < -1.5: return "VERY_EASY"
    elif b < -0.5: return "EASY"
    elif b < 0.5: return "MEDIUM"
    elif b < 1.5: return "HARD"
    else: return "VERY_HARD"

def irt_label(b):
    if b < -1.5: return "cok_kolay"
    elif b < -0.5: return "kolay"
    elif b < 0.5: return "orta"
    elif b < 1.5: return "zor"
    else: return "cok_zor"

def word_stats(text):
    words = text.split()
    if not words: return 0, 0, 0.0
    wc = len(words)
    uw = len(set(w.lower() for w in words))
    aw = round(sum(len(w) for w in words) / wc, 2)
    return wc, uw, aw

def sq(s):
    if s is None: return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

# Parse source SQL
src = r"C:\Users\husey\kiro2\emergency_content_v2.sql"
with open(src, encoding="utf-8") as f:
    raw = f.read()

questions = []
i = 0
n = len(raw)

def parse_tuple(raw, start):
    i = start + 1
    fields = []
    buf = ""
    in_str = False
    brace_depth = 0
    while i < len(raw):
        c = raw[i]
        if in_str:
            if c == "'" and i+1 < len(raw) and raw[i+1] == "'":
                buf += "'"; i += 2; continue
            elif c == "'":
                in_str = False; buf += c
            else:
                buf += c
        elif c == "'": in_str = True; buf += c
        elif c == "{": brace_depth += 1; buf += c
        elif c == "}": brace_depth -= 1; buf += c
        elif c == "," and brace_depth == 0:
            fields.append(buf.strip()); buf = ""
        elif c == ")" and brace_depth == 0:
            if buf.strip(): fields.append(buf.strip())
            return fields, i+1
        else:
            buf += c
        i += 1
    return fields, i

pos = 0
while pos < n:
    idx = raw.find("('", pos)
    if idx == -1: break
    pre = raw[max(0, idx-30):idx].strip()
    if "VALUES" in pre or pre.endswith(","):
        fields, end = parse_tuple(raw, idx)
        if len(fields) >= 9:
            try:
                def sq2(s):
                    s = s.strip()
                    if s.startswith("'") and s.endswith("'"): return s[1:-1]
                    return s
                stem=sq2(fields[0]); opts_str=sq2(fields[1])
                correct=sq2(fields[2]); subject=sq2(fields[3])
                topic=sq2(fields[4]); diff=float(fields[5])
                year_s=fields[7].strip()
                year=int(year_s) if year_s.isdigit() else 2023
                expl=sq2(fields[8])
                opts=json.loads(opts_str)
                questions.append(dict(stem=stem,opts=opts,correct=correct,
                    subject=subject,topic=topic,diff=diff,year=year,expl=expl))
            except: pass
        pos = end
    else:
        pos = idx + 1

print(f"Parsed {len(questions)} questions")

# Generate SQL — difficulty_update_count dahil TUM NOT NULL alanlar
out = [
    "-- KIRO2 Emergency Content -> question_bank",
    "-- difficulty_update_count ve tum NOT NULL alanlar dahil",
    "BEGIN;", ""
]

COLS = (
    "id, question_text, option_a, option_b, option_c, option_d, option_e, "
    "correct_answer, explanation, primary_topic_id, "
    "bloom_level, bloom_category, difficulty_level, irt_based_difficulty, "
    "student_success_rate, irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote, "
    "is_calibrated, calibration_sample_size, calibration_quality_score, "
    "difficulty_update_count, "
    "morphology_complexity, word_count, unique_word_count, average_word_length, readability_score, "
    "times_asked, times_correct, times_wrong, times_skipped, "
    "average_response_time, median_response_time, exposure_rate, "
    "exam_type, subject_area, grade_level, osym_format_compliant, osym_year, "
    "quality_score, quality_review_status, is_active, is_public"
)

import uuid
for q in questions:
    qid = str(uuid.uuid4())
    opts = q["opts"]
    diff = q["diff"]
    subj = q["subject"]
    topic = q["topic"]

    opt_a = opts.get("A","")
    opt_b = opts.get("B","")
    opt_c = opts.get("C","")
    opt_d = opts.get("D","")
    opt_e = opts.get("E", None)

    area = SUBJECT_AREA.get(subj, "GENEL")
    exam = "AYT" if subj.startswith("AYT") or subj.startswith("YDT") else "TYT"
    tid = get_topic_id(subj, topic)
    dlevel = diff_level(diff)
    ilabel = irt_label(diff)
    wc, uw, aw = word_stats(q["stem"])
    oe = sq(opt_e) if opt_e else "NULL"

    vals = (
        f"{sq(qid)}, {sq(q['stem'])}, {sq(opt_a)}, {sq(opt_b)}, "
        f"{sq(opt_c)}, {sq(opt_d)}, {oe}, "
        f"{sq(q['correct'])}, {sq(q['expl'])}, {sq(tid)}, "
        f"1, 'Hatırlama', '{dlevel}', {sq(ilabel)}, "
        f"0.5, 1.0, {diff}, 0.25, 1.0, "
        f"FALSE, 0, 0.0, "
        f"0, "
        f"0.0, {wc}, {uw}, {aw}, 50.0, "
        f"0, 0, 0, 0, "
        f"60.0, 60.0, 0.0, "
        f"'{exam}', '{area}', 12, TRUE, {q['year']}, "
        f"70.0, 'approved', TRUE, TRUE"
    )
    out.append(f"INSERT INTO question_bank ({COLS}) VALUES ({vals}) ON CONFLICT (id) DO NOTHING;")

out += ["", "COMMIT;", f"-- Total: {len(questions)} sorular"]

dest = r"C:\Users\husey\kiro2\emergency_qbank_import.sql"
with open(dest, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"OK: {len(questions)} soru yazildi -> {dest}")
