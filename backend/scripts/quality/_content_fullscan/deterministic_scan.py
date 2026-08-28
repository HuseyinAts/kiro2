"""Tüm servis havuzu (v_safe, 25.127) deterministik içerik taraması.

%100 kapsam, LLM YOK. 3 sinyal:
1. garble: char-trigram LM skoru (garble_char_lm eğitimi) >= eşik
2. figure_orphan: metin şekil/grafik/tabloya atıf yapıyor AMA görsel yok (çözülemez)
3. structural: şık boş / key A-E değil / çok kısa metin

Çıktı: flagged.json (LLM-doğrulanacak şüpheli alt-küme) + rapor.
Deterministik = reproducible, sampling yok.
"""

import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = Path("scripts/quality/_content_fullscan")

# garble char-LM'i yükle (module-level eğitim + skor fonksiyonları)
spec = importlib.util.spec_from_file_location(
    "glm", "scripts/quality/garble_char_lm.py"
)
glm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glm)  # coherent=true üzerinde eğitir

GARBLE_TH = 4.0  # tüm-aktif taramada temiz-set false-pozitif=0 eşiği
FIG_REF = re.compile(
    r"şekil|şekild|grafik|grafiğ|tablo|tablod|aşağıdaki görsel|yukarıdaki görsel|"
    r"görselde|resimde|çizim|diyagram|haritada|krokide",
    re.IGNORECASE,
)


def garble_score(text: str) -> float:
    toks = glm.tokens(text or "")
    s = glm.text_score(toks)
    return s if s is not None else 0.0


def scan_one(q: dict) -> dict | None:
    """Bir soruyu tara, sorun varsa flag dict döndür (yoksa None)."""
    flags = []
    text = q.get("q", "") or ""
    opts = [q.get(k, "") or "" for k in ("a", "b", "c", "d", "ee")]

    # 1) garble
    gs = garble_score(text)
    if gs >= GARBLE_TH:
        flags.append(("garble", f"score={gs:.2f}"))

    # 2) figure orphan: metin görsele atıf + görsel yok
    if q.get("g", 0) == 0 and FIG_REF.search(text):
        m = FIG_REF.search(text)
        flags.append(("figure_orphan", f"atıf='{m.group(0)}' ama görsel yok"))

    # 3) structural
    key = (q.get("k") or "").strip().upper()
    if key not in ("A", "B", "C", "D", "E"):
        flags.append(("bad_key", f"key='{key}'"))
    # ilk 4 şık boş olmamalı (E opsiyonel)
    if any(not o.strip() for o in opts[:4]):
        flags.append(("empty_option", "ilk 4 şıktan biri boş"))
    if len(text.strip()) < 15:
        flags.append(("too_short", f"len={len(text.strip())}"))

    if flags:
        return {
            "id": q["id"],
            "subject": q.get("s"),
            "flags": [f[0] for f in flags],
            "detail": {f[0]: f[1] for f in flags},
        }
    return None


def main():
    chunks = sorted(D.glob("chunk_*.json"))
    total = 0
    flagged = []
    cat = Counter()
    subj_total = Counter()
    subj_flag = Counter()
    for cf in chunks:
        for q in json.loads(cf.read_text(encoding="utf-8")):
            total += 1
            subj_total[q.get("s")] += 1
            r = scan_one(q)
            if r:
                flagged.append(r)
                subj_flag[r["subject"]] += 1
                for f in r["flags"]:
                    cat[f] += 1

    (D / "flagged.json").write_text(
        json.dumps(flagged, ensure_ascii=False), encoding="utf-8"
    )
    print(f"===== DETERMİNİSTİK TAM TARAMA — {total} servis soru =====")
    print(f"flagged (şüpheli): {len(flagged)} (%{100 * len(flagged) / total:.2f})")
    print("kategori dağılımı:", dict(cat))
    print("\nbranş flag oranı:")
    for s in sorted(subj_total, key=lambda x: -subj_flag[x] / max(subj_total[x], 1)):
        pct = 100 * subj_flag[s] / max(subj_total[s], 1)
        print(f"  {s:<12} {subj_flag[s]:>4}/{subj_total[s]:<5} (%{pct:.1f})")
    print(f"\nyazıldı: flagged.json ({len(flagged)} kayıt — LLM-doğrulama adayı)")


if __name__ == "__main__":
    main()
