"""
Garble dedektörü — karakter-trigram dil modeli.
Bilinen-temiz (student_coherent=true) üzerinde eğitilir, tüm aktif sorulara
karakter-başına surprisal (bits/char) skoru verir. Yüksek = garbled.

Sadece ALFABETİK token üzerinde skorlar (matematik/sembol false-positive önleme).
Uygulamadan önce doğrulama: temiz<garble ayrımı + sentetik OCR-bozma testi.

Reproducible. Sampling/extrapolation YOK — tüm popülasyon deterministik skorlanır.
"""

import math
import random
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATH = r"C:/Users/husey/kiro2/backend/scripts/quality/_garble_tmp/qb_full.tsv"
TR = "abcçdefgğhıijklmnoöprsştuüvyz"


def norm(t):
    t = t.replace("I", "ı").replace("İ", "i").lower()
    return t


def tokens(t):
    # alfabetik token (>=3 char), Türkçe
    return [w for w in re.findall(r"[a-zçğıöşü]+", norm(t)) if len(w) >= 3]


# ---- load ----
recs = []  # (id, status, coherent, [tokens])
with open(PATH, encoding="utf-8") as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) < 4:
            continue
        recs.append((p[0], p[1], p[2], tokens(p[3])))
print(f"yüklenen soru: {len(recs)}")

# ---- train char-trigram on coherent=true ----
TRI = defaultdict(Counter)  # (c1,c2) -> Counter(c3)
ctx_tot = Counter()


def add_word(w, tri, tot):
    s = "^^" + w + "$"
    for i in range(2, len(s)):
        ctx = s[i - 2 : i]
        tri[ctx][s[i]] += 1
        tot[ctx] += 1


train = [r for r in recs if r[2] == "true"]
for _, _, _, tks in train:
    for w in tks:
        add_word(w, TRI, ctx_tot)
V = len(TR) + 2  # alphabet + boundary symbols
print(f"eğitim sorusu (coherent=true): {len(train)}, trigram bağlam: {len(TRI)}")


def word_surprisal(w):
    s = "^^" + w + "$"
    bits = 0.0
    n = 0
    for i in range(2, len(s)):
        ctx = s[i - 2 : i]
        ch = s[i]
        num = TRI[ctx][ch] + 0.1
        den = ctx_tot[ctx] + 0.1 * V
        bits += -math.log2(num / den)
        n += 1
    return bits, n


def text_score(tks):
    tb = 0.0
    tn = 0
    for w in tks:
        b, n = word_surprisal(w)
        tb += b
        tn += n
    if tn < 12:  # çok kısa metin = güvenilmez
        return None
    return tb / tn  # bits/char


# ---- score all ----
scored = []
for qid, st, coh, tks in recs:
    sc = text_score(tks)
    if sc is not None:
        scored.append((qid, st, coh, sc))
print(f"skorlanan (>=12 alf. char): {len(scored)}")

import statistics


def stats(sel):
    if not sel:
        return "n=0"
    sel = sorted(sel)
    q = lambda p: sel[min(len(sel) - 1, int(p * len(sel)))]
    return f"n={len(sel):6d} medyan={statistics.median(sel):.2f} p90={q(0.90):.2f} p99={q(0.99):.2f} max={sel[-1]:.2f}"


print("\n=== DOĞRULAMA 1: durum bazında bits/char (temiz DÜŞÜK olmalı) ===")
by = defaultdict(list)
for _, st, coh, sc in scored:
    by["coherent_true" if coh == "true" else st].append(sc)
for k in sorted(by, key=lambda k: statistics.median(by[k])):
    print(f"  {k:18s} {stats(by[k])}")

# ---- VALIDATION 2: synthetic OCR corruption ----
print("\n=== DOĞRULAMA 2: sentetik OCR-bozma (skor YÜKSELMELİ) ===")
random.seed(42)
SWAP = {
    "l": "t",
    "t": "l",
    "o": "e",
    "e": "o",
    "ı": "i",
    "i": "ı",
    "c": "ç",
    "n": "m",
    "u": "ü",
    "r": "n",
}


def corrupt(w, rate=0.18):
    out = []
    for ch in w:
        r = random.random()
        if r < rate and ch in SWAP:
            out.append(SWAP[ch])
        elif r < rate * 1.4:
            continue  # char yutulması
        else:
            out.append(ch)
    return "".join(out)


clean_sample = [r for r in train][:1500]
base, corr = [], []
for _, _, _, tks in clean_sample:
    if not tks:
        continue
    b = text_score(tks)
    c = text_score([corrupt(w) for w in tks])
    if b is not None and c is not None:
        base.append(b)
        corr.append(c)
print(f"  temiz   : {stats(base)}")
print(f"  bozulmuş: {stats(corr)}")
print(
    f"  medyan kayma: +{statistics.median(corr) - statistics.median(base):.2f} bits/char"
)

# ---- high-score tail examples ----
print("\n=== EN YÜKSEK SKORLU 12 ÖRNEK (gerçekten garble mı?) ===")
scored_sorted = sorted(scored, key=lambda x: -x[3])
idmap = {}
with open(PATH, encoding="utf-8") as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4:
            idmap[p[0]] = p[3]
for qid, st, coh, sc in scored_sorted[:12]:
    print(f"  [{sc:.2f}|{st}] {idmap.get(qid, '')[:120]}")

# ---- threshold sweep for deletion ----
print("\n=== EŞİK TARAMASI (silme adayı sayısı) ===")
allsc = [s for _, _, _, s in scored]
ct_scores = by["coherent_true"]
ct_p99 = sorted(ct_scores)[int(0.99 * len(ct_scores))]
print(f"  coherent_true p99 = {ct_p99:.2f} (temiz tavanı referansı)")
for th in [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]:
    n = sum(1 for s in allsc if s >= th)
    ct = sum(1 for s in ct_scores if s >= th)
    print(f"  eşik {th:.1f}: {n:6d} aday  (bunların temiz-set false-pozitifi: {ct})")
