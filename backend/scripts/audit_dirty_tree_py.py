#!/usr/bin/env python
"""S209: Gemini devrinden kalan kirli agactaki .py dosyalarini siniflandir.

NEDEN BU ALET VAR
-----------------
S206'da "M = kozmetik reformat" varsayimi DORT KEZ yanlis cikti (bkz.
memory/project_kirli-agac-gemini-devir-20260813.md). Son turda 197 dosyanin
yalnizca 66'si gercekten AST-birebir ayniydi; 111'i yapisal/mantik farki
tasiyordu -- iclerinde bir RLS predicate degisikligi ve bir null-safety fix'i
vardi. Ayni sekilde "D = tasindi, gereksiz" varsayimi da curudu:
`bkt_service.py` silinmis gorunuyordu ama 12 canli dosyadan hala import
ediliyordu.

Bu yuzden iki iddia da BURADA OLCULUR, okunarak varsayilmaz:

  "M kozmetik"  -> ast.dump(HEAD) == ast.dump(worktree)  (docstring-normalize)
  "D gereksiz"  -> canli korpusta import referansi kaldi mi?

ast.dump karsilastirmasi string literal DEGERLERINI de kapsadigi icin
regex/whitespace diff'inden guvenilirdir; tirnak stili ve bosluk degisikligi
onu etkilemez, bir sabitin degerinin degismesi ise etkiler.

KULLANIM
--------
    python backend/scripts/audit_dirty_tree_py.py            # ozet
    python backend/scripts/audit_dirty_tree_py.py --tsv rapor.tsv

Salt-okunurdur: hicbir dosyayi degistirmez, git durumuna dokunmaz.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import subprocess  # nosec B404 - yalnizca sabit `git` sorgulari; asagiya bak
import sys
from collections import defaultdict
from functools import cache
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    out = subprocess.run(  # nosec B603 B607 - sabit `git` argumanlari, kullanici girdisi yok (salt-okunur denetim aleti)
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return out.stdout


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Docstring'leri dusur: yeniden bicimlendirme onlari sik sik degistirir."""
    for node in ast.walk(tree):
        if not isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]
    return tree


def _ast_key(src: str) -> str | None:
    """Parse edilemiyorsa None -- 'ayni' diye raporlanmasin."""
    try:
        return ast.dump(_strip_docstrings(ast.parse(src)))
    except SyntaxError:
        return None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


# ---------------------------------------------------------------- canli korpus


def live_corpus() -> list[Path]:
    """Diskte GERCEKTEN duran .py dosyalari (takipli + takipsiz)."""
    seen: dict[str, Path] = {}
    for rel in _git("ls-files", "*.py").splitlines():
        p = REPO / rel
        if p.is_file():
            seen[rel] = p
    for line in _git("status", "--porcelain").splitlines():
        if line[:2] == "??" and line[3:].endswith(".py"):
            rel = line[3:]
            p = REPO / rel
            if p.is_file():
                seen[rel] = p
    return list(seen.values())


def import_index(corpus: list[Path]) -> dict[str, set[str]]:
    """token -> onu import eden canli dosyalarin yolu.

    Import DEYIMLERINDEN toplanir (yorum/dizge degil): `import a.b.c` ve
    `from a.b import c` her iki bicimde de hem tam nokta yolunu hem son
    bileseni kaydeder. AST kullanilir -- yorum icindeki `import x` sayilmaz.
    """
    idx: dict[str, set[str]] = defaultdict(set)
    for path in corpus:
        src = _read(path)
        if src is None or "import" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        rel = path.relative_to(REPO).as_posix()
        for node in ast.walk(tree):
            # SADECE TAM MODUL YOLLARI. Son-bilesen ("core.config" -> "config")
            # veya ciplak sembol adi ("from x import config" -> "config")
            # kaydedilmez: ilk turda tam bunu yaptigim icin `orchestrator/
            # config.py` "93 canli import" ile sahte P0 olarak raporlandi --
            # oysa o 93 dosya `core.config`/`app.core.config` import ediyordu.
            if isinstance(node, ast.Import):
                for alias in node.names:
                    idx[alias.name].add(rel)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if node.level:
                    # GORELI import: atlanamaz, COZULUR. `from .memory import X`
                    # icin node.module == "memory" ama level==1'dir; level'a
                    # bakmadigim turda bu `orchestrator/config.py`ye "23 canli
                    # import" yazdirdi, tumden atladigim turda ise
                    # `orchestrator/core/__init__.py`nin komsularina yaptigi
                    # GERCEK referanslar kayboldu. Dogrusu: hedefi dosya
                    # yoluna cevir, sonra kok-goreli token uret.
                    for hedef in _goreli_hedefler(rel, node.level, mod, node.names):
                        for tok in rooted_tokens(hedef):
                            idx[tok].add(rel)
                    continue
                if not mod:
                    continue
                idx[mod].add(rel)
                for alias in node.names:
                    # `from paket import altmodul` da bir modul referansidir
                    idx[f"{mod}.{alias.name}"].add(rel)
    return idx


def _goreli_hedefler(
    rel: str, level: int, mod: str, names: list[ast.alias]
) -> list[str]:
    """Goreli import'un isaret ettigi olasi dosya yollari (.py olarak)."""
    base = Path(rel).parent
    for _ in range(level - 1):
        base = base.parent
    kok = base.joinpath(*mod.split(".")) if mod else base
    hedefler = [f"{kok.as_posix()}.py", f"{kok.as_posix()}/__init__.py"]
    for alias in names:
        alt = kok / alias.name
        hedefler.append(f"{alt.as_posix()}.py")
        hedefler.append(f"{alt.as_posix()}/__init__.py")
    return hedefler


@cache
def disaridan_saglaniyor(tok: str) -> str:
    """Tek-bilesenli bir ad site-packages/stdlib'de var mi?

    `backend/websocket.py` silinmis ve `import websocket` goruluyor diye
    "kirik" demek yanlis olurdu: `websocket` bir PyPI paketi. Dosya diskten
    zaten silindigi icin find_spec yalnizca depo DISINDAKI saglayiciyi bulur;
    ust paketi olmayan bir ad icin find_spec modulu CALISTIRMAZ.
    """
    if "." in tok:
        return ""
    try:
        spec = importlib.util.find_spec(tok)
    except (ImportError, ValueError):
        return ""
    origin = getattr(spec, "origin", None) if spec else None
    if not origin or origin == "built-in":
        return "built-in" if spec else ""
    try:
        Path(origin).relative_to(REPO)
    except ValueError:
        # str(): spec.origin getattr uzerinden Any geliyor, mypy --strict
        # no-any-return veriyor.
        return str(origin)  # depo disinda -> ucuncu taraf/stdlib
    return ""


# sys.path koku olabilecek dizinler: bu depoda testler hem kokten
# (`orchestrator.core.x`) hem backend'in icinden (`models.x`) import ediyor.
ROOTS = ("", "backend", "orchestrator")


def module_tokens(rel: str) -> list[str]:
    """Silinen bir yol icin olasi import token'lari (uzundan kisaya)."""
    parts = Path(rel).with_suffix("").as_posix().split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return []
    return [".".join(parts[i:]) for i in range(len(parts))]


def rooted_tokens(rel: str) -> list[str]:
    """Bu dosyanin MESRU import adlari (bilinen sys.path koklerine gore).

    `module_tokens` her son-eki uretir; `backend/models.py` icin uretilen
    ciplak `models` token'i canli `backend/models/` PAKETIYLE de eslesir ve
    "184 canli import" gibi sahte bir aciklik raporlatir. Mesru ad kumesi
    yalnizca koklerden turetilir.
    """
    out = []
    for root in ROOTS:
        prefix = f"{root}/" if root else ""
        if rel.startswith(prefix):
            parts = Path(rel[len(prefix) :]).with_suffix("").as_posix().split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if parts:
                out.append(".".join(parts))
    return out


def live_providers(corpus: list[Path]) -> set[str]:
    """Diskte DURAN dosyalarin sagladigi import adlari.

    Bir silinen dosyanin adini canli bir dosya/paket hala sagliyorsa, silme
    o import'u KIRMAZ. Olcumun can alici adimi budur: `backend/models.py`
    silinse de `backend/models/__init__.py` durdugu icin `import models`
    calismaya devam eder.
    """
    provided: set[str] = set()
    for path in corpus:
        rel = path.relative_to(REPO).as_posix()
        provided.update(rooted_tokens(rel))
    return provided


# ---------------------------------------------------------------------- akis


def _siniflandir_silinen(
    rel: str,
    idx: dict[str, set[str]],
    saglanan: set[str],
    by_basename: dict[str, list[Path]],
) -> tuple[str, str]:
    """Silinen (`D`) bir dosyayi siniflandir -> (sinif, kanit).

    KIRIK = mesru adiyla import ediliyor VE o adi baska canli dosya saglamiyor.
    Iki kosul da sart: ilki olmadan bulgu yok, ikincisi olmadan `backend/
    models.py` gibi vakalar sahte P0 uretir (canli `backend/models/` paketi
    ayni adi sagliyor).
    """
    kirik: set[str] = set()
    kirik_tok = cozulen = disari = ""
    mesru = rooted_tokens(rel)
    for tok in mesru:
        if tok not in idx:
            continue
        if tok in saglanan:
            cozulen = cozulen or tok
            continue
        dis = disaridan_saglaniyor(tok)
        if dis:
            disari = disari or f"{tok} <- {dis}"
            continue
        kirik |= idx[tok]
        kirik_tok = kirik_tok or tok
    kirik.discard(rel)

    zayif: set[str] = set()
    for tok in module_tokens(rel):
        if tok not in mesru:
            zayif |= idx.get(tok, set())
    zayif.discard(rel)

    ikiz = [p.relative_to(REPO).as_posix() for p in by_basename.get(Path(rel).name, [])]

    if kirik:
        return "KIRIK_IMPORT", (
            f"{len(kirik)} canli import '{kirik_tok}' adini istiyor, "
            f"canli saglayici YOK; ilk: {sorted(kirik)[0]}"
        )
    if cozulen:
        return "AD_COZULUYOR", f"'{cozulen}' adini baska canli dosya/paket sagliyor"
    if disari:
        return "UCUNCU_TARAF", f"ad depo disindan cozuluyor: {disari}"
    if ikiz:
        return "TASINMIS_OLABILIR", f"ayni adli canli dosya: {ikiz[0]}"
    if zayif:
        return "ZAYIF_ESLESME", (
            f"yalniz ciplak-ad eslesmesi ({len(zayif)}); mesru adiyla import EDILMIYOR"
        )
    return "REFERANSSIZ", "canli import yok, ayni adli dosya yok"


def classify() -> list[dict[str, str]]:
    corpus = live_corpus()
    idx = import_index(corpus)
    saglanan = live_providers(corpus)
    by_basename: dict[str, list[Path]] = defaultdict(list)
    for p in corpus:
        by_basename[p.name].append(p)

    rows: list[dict[str, str]] = []
    for line in _git("status", "--porcelain").splitlines():
        code, rel = line[:2], line[3:].strip().strip('"')
        if not rel.endswith(".py"):
            continue

        row = {"durum": code.strip() or code, "yol": rel, "sinif": "", "kanit": ""}

        if code.strip() == "M":
            head = _git("show", f"HEAD:{rel}")
            disk = _read(REPO / rel)
            if disk is None:
                row["sinif"] = "OKUNAMADI"
            else:
                k_head, k_disk = _ast_key(head), _ast_key(disk)
                if k_head is None or k_disk is None:
                    row["sinif"] = "PARSE_HATASI"
                    row["kanit"] = (
                        f"HEAD={'ok' if k_head else 'FAIL'} disk={'ok' if k_disk else 'FAIL'}"
                    )
                elif k_head == k_disk:
                    row["sinif"] = "KOZMETIK"
                    row["kanit"] = "AST birebir ayni (docstring-normalize)"
                else:
                    row["sinif"] = "YAPISAL"
                    row["kanit"] = (
                        f"AST farkli; satir {len(head.splitlines())}->{len(disk.splitlines())}"
                    )

        elif code.strip() == "D":
            row["sinif"], row["kanit"] = _siniflandir_silinen(
                rel, idx, saglanan, by_basename
            )

        elif code.strip() == "??":
            tok_hits: set[str] = set()
            for tok in module_tokens(rel):
                tok_hits |= idx.get(tok, set())
            tok_hits.discard(rel)
            row["sinif"] = "YENI_BAGLI" if tok_hits else "YENI_YETIM"
            row["kanit"] = (
                f"{len(tok_hits)} import, ilk: {sorted(tok_hits)[0]}"
                if tok_hits
                else "hicbir canli dosya import etmiyor"
            )

        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tsv", type=str, default=None, help="TSV raporu yaz")
    args = ap.parse_args()

    rows = classify()

    sayim: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        sayim[(r["durum"], r["sinif"])] += 1

    print(f"Kirli agacta {len(rows)} .py dosyasi\n")
    print(f"{'durum':6} {'sinif':20} {'adet':>5}")
    print("-" * 34)
    for (durum, sinif), n in sorted(sayim.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{durum:6} {sinif:20} {n:5d}")

    if args.tsv:
        out = Path(args.tsv)
        with out.open("w", encoding="utf-8", newline="") as fh:
            fh.write("durum\tsinif\tyol\tkanit\n")
            for r in sorted(rows, key=lambda r: (r["sinif"], r["yol"])):
                fh.write(f"{r['durum']}\t{r['sinif']}\t{r['yol']}\t{r['kanit']}\n")
        print(f"\nTSV: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
