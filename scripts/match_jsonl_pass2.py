# -*- coding: utf-8 -*-
"""
2. gecis: opt_a eslesmeyen 335 kayit icin alternatif stratejiler
Str-1: book + page -> tek soru varsa direkt esles
Str-2: book + page -> option_a normalize ederek esles (bosluk/noktalama temizle)
Str-3: book + page + question_number siralama ile esles
"""
import json, glob, os, re
import psycopg2
from difflib import SequenceMatcher

JSONL_DIR = r"C:\Users\husey\d-dataset\output\final"
CONF_MIN  = 60

def norm_book(s):
    s = s.lower()
    s = re.sub(r'[_\-\s]+', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return s.strip()

def norm_opt(s):
    """Option metni normalize et: bosluk, noktalama, kucuk harf"""
    if not s: return ""
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return s.lower()[:50]   # ilk 50 char karsilastir

# Load jsonl
files = sorted(glob.glob(os.path.join(JSONL_DIR, "eslesmis_*.jsonl")))
all_entries = []
for fp in files:
    with open(fp, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                all_entries.append(json.loads(line))
            except: pass

print(f"Toplam entry: {len(all_entries)}")

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()

# DB book listesi
cur.execute("SELECT DISTINCT source_book FROM question_bank WHERE source_book IS NOT NULL")
db_books = [r[0] for r in cur.fetchall()]

def find_db_book(jbook):
    best_s, best_b = 0, None
    for b in db_books:
        s = SequenceMatcher(None, norm_book(jbook), norm_book(b)).ratio()
        if s > best_s:
            best_s, best_b = s, b
    return (best_b, best_s) if best_s >= 0.6 else (None, 0)

# Onceki geciste eslesen ID'leri bul (is_calib_pool=TRUE AND pipeline_metadata jsonl_match var)
cur.execute("""
    SELECT id FROM question_bank
    WHERE is_calib_pool = TRUE
      AND pipeline_metadata::text LIKE '%eslesmis_jsonl%'
""")
already_matched_ids = set(r[0] for r in cur.fetchall())
print(f"Onceden eslesmis: {len(already_matched_ids)}")

# Tum entry'leri tekrar isle
matched2 = []
skipped_conf = 0
skipped_book = 0
still_no_match = []

for e in all_entries:
    conf = e.get('confidence', 0)
    if conf < CONF_MIN:
        skipped_conf += 1
        continue

    jbook = e['book_name']
    db_book, score = find_db_book(jbook)
    if not db_book:
        skipped_book += 1
        continue

    page = e.get('page_number')
    opts = e.get('options', {})
    opt_a_raw = opts.get('A', '')
    answer = e.get('answer', '')
    q_num = e.get('question_number', None)

    # Str-1: book + page, tek soru varsa esles
    cur.execute("""
        SELECT id, correct_answer, is_calib_pool, option_a
        FROM question_bank
        WHERE source_book = %s AND source_page = %s AND is_active = TRUE
          AND id NOT IN (SELECT id FROM question_bank WHERE pipeline_metadata::text LIKE '%%eslesmis_jsonl%%' AND is_calib_pool=TRUE)
    """, (db_book, page))
    # Not: NOT IN subquery yavaş olabilir, önce tüm page rows al
    cur.execute("""
        SELECT id, correct_answer, is_calib_pool, option_a
        FROM question_bank
        WHERE source_book = %s AND source_page = %s AND is_active = TRUE
    """, (db_book, page))
    page_rows = cur.fetchall()

    # Zaten matched olanları filtrele
    page_rows = [r for r in page_rows if r[0] not in already_matched_ids]

    if not page_rows:
        still_no_match.append(e)
        continue

    # Str-1: Tek soru kaldıysa direkt eşleştir
    if len(page_rows) == 1:
        qid, ea, is_pool, db_opt_a = page_rows[0]
        matched2.append({'id': qid, 'answer': answer, 'existing': ea,
                         'is_pool': is_pool, 'conf': conf, 'strategy': 'single_on_page'})
        already_matched_ids.add(qid)
        continue

    # Str-2: Normalize option_a karşılaştır
    norm_a = norm_opt(opt_a_raw)
    candidates = [r for r in page_rows if norm_opt(str(r[3])) == norm_a]
    if len(candidates) == 1:
        qid, ea, is_pool, _ = candidates[0]
        matched2.append({'id': qid, 'answer': answer, 'existing': ea,
                         'is_pool': is_pool, 'conf': conf, 'strategy': 'norm_opt_a'})
        already_matched_ids.add(qid)
        continue

    # Str-3: question_number ile satır indeksi eşleştir
    # Soruları option_a lexicographic veya id sıralamasıyla sırala
    if q_num and 1 <= q_num <= len(page_rows):
        sorted_rows = sorted(page_rows, key=lambda r: r[0])  # id'ye göre sırala
        row = sorted_rows[q_num - 1]
        qid, ea, is_pool, _ = row
        matched2.append({'id': qid, 'answer': answer, 'existing': ea,
                         'is_pool': is_pool, 'conf': conf, 'strategy': 'q_number_idx'})
        already_matched_ids.add(qid)
        continue

    still_no_match.append(e)

print(f"\nPas 2 sonuclari:")
print(f"  Yeni eslesmis  : {len(matched2)}")
print(f"  Conf dusuk skip: {skipped_conf}")
print(f"  Kitap yok skip : {skipped_book}")
print(f"  Hala eslesmiyor: {len(still_no_match)}")

strats = {}
for m in matched2:
    strats[m['strategy']] = strats.get(m['strategy'], 0) + 1
print(f"  Strateji dagil.: {strats}")

# Str-3 (q_number_idx) tehlikeli olabilir — guvensiz sonuclari filtrele
# Sadece single_on_page ve norm_opt_a stratejileri guvenliyse uygula
SAFE_STRATEGIES = {'single_on_page', 'norm_opt_a'}

safe_matches = [m for m in matched2 if m['strategy'] in SAFE_STRATEGIES]
risky_matches = [m for m in matched2 if m['strategy'] not in SAFE_STRATEGIES]

print(f"\nGuvenli eslesme: {len(safe_matches)}")
print(f"Riskli eslesme : {len(risky_matches)} (uygulanmayacak)")

# Sadece guvenli eslesmeler uygula
ans_updated = 0
pool_marked = 0
already_ok  = 0

for m in safe_matches:
    qid = m['id']
    ja  = m['answer']
    ea  = m['existing']
    pool = m['is_pool']

    needs_ans  = (ea != ja) and ja in ('A','B','C','D','E')
    needs_pool = not pool

    if needs_ans or needs_pool:
        updates = []
        params = []
        if needs_ans:
            updates.append("correct_answer = %s")
            params.append(ja)
        if needs_pool:
            updates.append("is_calib_pool = TRUE")
        updates.append("pipeline_metadata = jsonb_set(COALESCE(pipeline_metadata::jsonb,'{}'), '{jsonl_match}', %s::jsonb)")
        params.append(json.dumps({"confidence": m['conf'],
                                  "source": "eslesmis_jsonl",
                                  "strategy": m['strategy']}))
        params.append(qid)
        cur.execute(f"UPDATE question_bank SET {', '.join(updates)} WHERE id = %s", params)
        if needs_ans: ans_updated += 1
        if needs_pool: pool_marked += 1
    else:
        already_ok += 1

conn.commit()

print(f"\nUygulanan guncelleme:")
print(f"  correct_answer guncellendi: {ans_updated}")
print(f"  is_calib_pool=TRUE markaldi: {pool_marked}")
print(f"  Zaten dogru: {already_ok}")

# Genel durum
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calib_pool=TRUE AND is_active=TRUE")
total_pool = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated=TRUE")
total_calib = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_active=TRUE")
total_active = cur.fetchone()[0]

print(f"\n=== GENEL DURUM ===")
print(f"Aktif soru      : {total_active:,}")
print(f"CAT pool (calib): {total_calib}")
print(f"CAT pool (havuz): {total_pool}")

cur.close(); conn.close()
print("TAMAM.")
