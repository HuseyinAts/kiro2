# -*- coding: utf-8 -*-
"""
D-Dataset eslesmis_*.jsonl -> question_bank eslestirme
Strateji: source_book (fuzzy) + source_page + option_a eslesimi
Aksiyon:  eslesme bulunursa is_calib_pool=TRUE, correct_answer guncelle
"""
import json, glob, os, re
import psycopg2
from difflib import SequenceMatcher

JSONL_DIR = r"C:\Users\husey\d-dataset\output\final"
CONF_MIN  = 60   # minimum confidence threshold

# --- Book name normalization ---
def norm(s):
    s = s.lower()
    s = re.sub(r'[_\-\s]+', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return s.strip()

def book_sim(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

# --- Load all jsonl entries ---
files = sorted(glob.glob(os.path.join(JSONL_DIR, "eslesmis_*.jsonl")))
entries = []
for fp in files:
    with open(fp, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                d = json.loads(line)
                entries.append(d)
            except: pass

print(f"Yuklendi: {len(entries)} entry, {len(files)} dosya")

# --- Get unique book names from DB ---
conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()

cur.execute("SELECT DISTINCT source_book FROM question_bank WHERE source_book IS NOT NULL")
db_books = [r[0] for r in cur.fetchall()]
print(f"DB'de {len(db_books)} farkli source_book")

# --- Build book_name -> db_source_book mapping ---
jsonl_books = list(set(e['book_name'] for e in entries))
book_map = {}   # jsonl_book_name -> db_source_book (best match)

for jbook in jsonl_books:
    best_score, best_db = 0, None
    for dbbook in db_books:
        s = book_sim(jbook, dbbook)
        if s > best_score:
            best_score, best_db = s, dbbook
    book_map[jbook] = (best_db, best_score)
    print(f"  '{jbook[:50]}' -> '{best_db[:50]}' ({best_score:.2f})")

print()

# --- Match each entry to question_bank ---
matched = []
no_book = []
no_page = []
ambiguous = []
no_opt_match = []

for e in entries:
    conf = e.get('confidence', 0)
    if conf < CONF_MIN:
        continue   # Dusuk guvensizlik - atla

    jbook = e['book_name']
    db_book, score = book_map.get(jbook, (None, 0))
    if not db_book or score < 0.6:
        no_book.append(e)
        continue

    page = e.get('page_number')
    opts = e.get('options', {})
    opt_a = opts.get('A', '')
    answer = e.get('answer', '')

    if not page or not opt_a:
        no_page.append(e)
        continue

    # Find by book + page + option_a
    cur.execute("""
        SELECT id, correct_answer, is_calib_pool
        FROM question_bank
        WHERE source_book = %s
          AND source_page = %s
          AND option_a = %s
          AND is_active = TRUE
    """, (db_book, page, opt_a))
    rows = cur.fetchall()

    if len(rows) == 1:
        qid, existing_ans, is_pool = rows[0]
        matched.append({
            'id': qid,
            'jsonl_answer': answer,
            'existing_answer': existing_ans,
            'is_pool': is_pool,
            'confidence': conf,
            'book': jbook
        })
    elif len(rows) > 1:
        ambiguous.append(e)
    else:
        # Try with option_a trimmed / whitespace variation
        cur.execute("""
            SELECT id, correct_answer, is_calib_pool
            FROM question_bank
            WHERE source_book = %s
              AND source_page = %s
              AND TRIM(option_a) = TRIM(%s)
              AND is_active = TRUE
        """, (db_book, page, opt_a))
        rows2 = cur.fetchall()
        if len(rows2) == 1:
            qid, existing_ans, is_pool = rows2[0]
            matched.append({
                'id': qid, 'jsonl_answer': answer,
                'existing_answer': existing_ans,
                'is_pool': is_pool, 'confidence': conf, 'book': jbook
            })
        else:
            no_opt_match.append(e)

print(f"Eslesme sonuclari (conf>={CONF_MIN}):")
print(f"  Eslesti      : {len(matched)}")
print(f"  Kitap yok    : {len(no_book)}")
print(f"  Sayfa/opt yok: {len(no_page)}")
print(f"  Belirsiz     : {len(ambiguous)}")
print(f"  Opt mismatch : {len(no_opt_match)}")

# --- Apply updates ---
answer_updated = 0
pool_marked = 0
already_ok = 0

for m in matched:
    qid = m['id']
    ja  = m['jsonl_answer']
    ea  = m['existing_answer']
    pool = m['is_pool']
    conf = m['confidence']

    needs_answer_update = (ea != ja) and (ja in ('A','B','C','D','E'))
    needs_pool          = not pool

    if needs_answer_update or needs_pool:
        if needs_answer_update and needs_pool:
            cur.execute("""
                UPDATE question_bank
                SET correct_answer = %s, is_calib_pool = TRUE,
                    pipeline_metadata = jsonb_set(
                        COALESCE(pipeline_metadata::jsonb, '{}'),
                        '{jsonl_match}',
                        %s::jsonb
                    )
                WHERE id = %s
            """, (ja, json.dumps({"confidence": conf, "source": "eslesmis_jsonl"}), qid))
            answer_updated += 1
            pool_marked += 1
        elif needs_answer_update:
            cur.execute("""
                UPDATE question_bank SET correct_answer = %s WHERE id = %s
            """, (ja, qid))
            answer_updated += 1
        else:   # only pool flag needed
            cur.execute("""
                UPDATE question_bank
                SET is_calib_pool = TRUE,
                    pipeline_metadata = jsonb_set(
                        COALESCE(pipeline_metadata::jsonb, '{}'),
                        '{jsonl_match}',
                        %s::jsonb
                    )
                WHERE id = %s
            """, (json.dumps({"confidence": conf, "source": "eslesmis_jsonl"}), qid))
            pool_marked += 1
    else:
        already_ok += 1

conn.commit()

print(f"\nGuncelleme sonuclari:")
print(f"  correct_answer guncellendi : {answer_updated}")
print(f"  is_calib_pool=TRUE markaldi: {pool_marked}")
print(f"  Zaten dogru                : {already_ok}")

# Son durum
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calib_pool=TRUE AND is_active=TRUE")
print(f"\nToplam is_calib_pool=TRUE: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated=TRUE")
print(f"Toplam is_calibrated=TRUE: {cur.fetchone()[0]}")

cur.close(); conn.close()
print("\nTAMAM.")
