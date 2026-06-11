"""Deterministic garble detector (char-trigram LM) — faithful port of garble_char_lm.py,
DB-driven (DATABASE_URL) instead of hardcoded TSV. READ-ONLY (no DB write).
Trains on a known-clean set; scores the unverified+pending pool; runs BOTH validation gates
(status separation + synthetic OCR corruption) before any threshold is trusted."""
import os, re, math, random, statistics, datetime
from collections import Counter, defaultdict
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":20})

TR = "abcçdefgğhıijklmnoöprsştuüvyz"
def norm(t): return (t or "").replace("I","ı").replace("İ","i").lower()
def tokens(t): return [w for w in re.findall(r"[a-zçğıöşü]+", norm(t)) if len(w) >= 3]

with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    has_sc = c.exec_driver_sql("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='question_bank' AND column_name='student_coherent')").scalar()
    if has_sc:
        sc_true = c.exec_driver_sql("SELECT count(*) FROM question_bank WHERE is_active AND student_coherent=true").scalar()
    else:
        sc_true = 0
    use_sc = bool(has_sc and sc_true >= 500)
    clean_expr = "student_coherent=true" if use_sc else "quality_review_status IN ('auto_judged_high','bronze_clean')"
    print("GARBLE SCORE -", datetime.datetime.now().isoformat())
    print(f"  student_coherent kolonu: {'VAR' if has_sc else 'YOK'}  true={sc_true:,}  -> egitim seti: {clean_expr}")

    rows = c.exec_driver_sql(f"""
        SELECT id::text, quality_review_status,
               CASE WHEN {clean_expr} THEN 'clean' ELSE 'other' END AS cl,
               question_text
        FROM question_bank WHERE is_active AND question_text IS NOT NULL
    """).fetchall()
print(f"  yuklenen aktif soru: {len(rows):,}")
recs = [(r[0], r[1], r[2], tokens(r[3])) for r in rows]

# ---- train char-trigram on clean ----
TRI = defaultdict(Counter); ctx_tot = Counter()
def add_word(w):
    s = "^^" + w + "$"
    for i in range(2, len(s)):
        ctx = s[i-2:i]; TRI[ctx][s[i]] += 1; ctx_tot[ctx] += 1
train = [r for r in recs if r[2] == "clean"]
for _,_,_,tks in train:
    for w in tks: add_word(w)
V = len(TR) + 2
print(f"  egitim soru(clean): {len(train):,}  trigram baglam: {len(TRI):,}")

def word_surprisal(w):
    s = "^^" + w + "$"; bits=0.0; n=0
    for i in range(2, len(s)):
        ctx=s[i-2:i]; ch=s[i]
        bits += -math.log2((TRI[ctx][ch]+0.1)/(ctx_tot[ctx]+0.1*V)); n+=1
    return bits, n
def text_score(tks):
    tb=0.0; tn=0
    for w in tks:
        b,n=word_surprisal(w); tb+=b; tn+=n
    return (tb/tn) if tn>=12 else None

scored = [(qid,st,cl,text_score(tks)) for qid,st,cl,tks in recs]
scored = [x for x in scored if x[3] is not None]
print(f"  skorlanan(>=12 alf char): {len(scored):,}")

# VALIDATION 1: status separation
print("\n=== DOGRULAMA 1: bits/char durum bazinda (clean DUSUK olmali) ===")
by = defaultdict(list)
for _,st,cl,sc in scored: by["clean" if cl=="clean" else st].append(sc)
def stat(sel):
    if not sel: return "n=0"
    sel=sorted(sel); q=lambda p: sel[min(len(sel)-1,int(p*len(sel)))]
    return f"n={len(sel):6d} medyan={statistics.median(sel):.2f} p90={q(.90):.2f} p99={q(.99):.2f} max={sel[-1]:.2f}"
for k in sorted(by, key=lambda k: statistics.median(by[k])):
    print(f"  {k:20s} {stat(by[k])}")

# VALIDATION 2: synthetic OCR corruption
print("\n=== DOGRULAMA 2: sentetik OCR-bozma (skor YUKSELMELI) ===")
random.seed(42)
SWAP={"l":"t","t":"l","o":"e","e":"o","ı":"i","i":"ı","c":"ç","n":"m","u":"ü","r":"n"}
def corrupt(w, rate=0.18):
    out=[]
    for ch in w:
        r=random.random()
        if r<rate and ch in SWAP: out.append(SWAP[ch])
        elif r<rate*1.4: continue
        else: out.append(ch)
    return "".join(out)
base, corr = [], []
for _,_,_,tks in train[:1500]:
    b=text_score(tks)
    cb=text_score([corrupt(w) for w in tks])
    if b is not None: base.append(b)
    if cb is not None: corr.append(cb)
print(f"  temiz    : {stat(base)}")
print(f"  bozulmus : {stat(corr)}")
gate2 = statistics.median(corr) > statistics.median(base) if base and corr else False
print(f"  GATE-2 (bozulmus>temiz medyan): {'GECTI' if gate2 else 'KALDI'}")

# Pool high-garble counts at thresholds derived from clean p99
clean_scores = sorted(by.get("clean", []))
p99 = clean_scores[min(len(clean_scores)-1,int(.99*len(clean_scores)))] if clean_scores else 0
pool = [sc for _,st,cl,sc in scored if cl!="clean" and st in ("unverified","pending")]
print(f"\n=== POOL (unverified+pending) garble dagilimi ===")
print(f"  {stat(pool)}")
print(f"  clean p99 esigi = {p99:.2f}")
for thr in (p99, p99+0.5, p99+1.0, 8.0, 10.0):
    n = sum(1 for x in pool if x > thr)
    print(f"  esik > {thr:5.2f} : {n:6,} soru ({100.0*n/max(len(pool),1):.1f}%)")
print("\nNOT: Esik uygulanmadan once GATE-1 (clean<pool ayrimi) + GATE-2 GECMELI. Hicbir sey yazilmadi.")
