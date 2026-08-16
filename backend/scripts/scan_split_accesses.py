"""#485 göç sayacı — AST tabanlı, alias-farkında.

Eski sayaç (`re.finditer(r'QuestionBankItem\\.(\\w+)')`) iki yönde de yanılıyor:
  - FAZLA sayar: yorum ve docstring içindeki metni erişim sanar.
  - EKSİK sayar: `from models.question_bank import QuestionBankItem as Question`
    şeklindeki alias'lı import'lardan sonraki `Question.subject_area` erişimini görmez.
    Aynı körlük S214'te yedek kontrol olarak önerilen `grep 'select(QuestionBankItem)'`
    için de geçerlidir.

Bu script AST kullanır: yorum/docstring otomatik elenir, alias'lar takip edilir.

Çıktı sınıfları:
  SINIF   — `<alias>.<split_alan>` (SQL ifadesi; devredici AttributeError atar → sorgu kurulamaz)
  KWARG   — `.values(<split_alan>=...)` / `.filter_by(<split_alan>=...)`. Alan adı burada
            **keyword argüman adı** olarak geçer; AST'de `Attribute` düğümü YOKTUR, yani
            SINIF taraması bunu yapısal olarak göremez. Ölçüldü: `update(QuestionBankItem)
            .values(irt_difficulty=...)` çalışma anında `CompileError: Unconsumed column
            names` verir — sessiz değil ama sayaçta görünmezdi.
  ENTITY  — `select(<alias>)` / `<db>.query(<alias>)` (entity-select → lazy='select'
            ilişkilere örnek-düzeyi erişim async'te MissingGreenlet riski)

Kör noktalar (ÖLÇÜLDÜ — bugün hepsi bu depoda 0 kalem, ama alet bunları GÖREMEZ):
  - `sa.select(X)` / `sqlalchemy.select(X)` — modül-nitelikli çağrı biçimi.
  - `aliased(QuestionBankItem)` — ORM alias nesnesi üzerinden erişim.
  - `qb.QuestionBankItem.field` — modül-nitelikli sınıf erişimi (`import models.question_bank`).
  - `QB = QuestionBankItem` — yerel yeniden bağlama (rebind); yalnız import alias'ları izlenir.
  - `from models import QuestionBankItem` — re-export üzerinden import (yalnız modül adında
    "question_bank" geçen import'lar eşleşir).
  - KWARG sınıfı sahiplik doğrulaması yapmaz: aynı dosyada BAŞKA bir modelin
    `.values(readability_score=...)` çağrısı olsaydı yanlış-pozitif olurdu. Bugün ölçüldü:
    12 KWARG kaleminin 12'si de `update(<QuestionBankItem alias>)` köküne bağlı
    (irt_daemon:211 ×6, irt_analysis_service:235 ×4, osym_exam_engine:1779/1785 ×2).

Kapsam: `SCAN_DIRS` bir ALLOW-LIST'tir; listede olmayan her şey (özellikle `tests/`,
`scripts/`, `hooks/`, `alembic/`) taranmaz. Yani TOPLAM, üretim kodu için bir ölçüm,
depo geneli için bir ALT SINIR'dır.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.question_bank import (
    QuestionBankItem,
    QuestionContent,
    QuestionMetadata,
    QuestionStatistics,
)

# Yalnizca GERCEKTEN tasinmis alanlar sayilir. `hasattr` guard'i shim'den
# devralindi (models/question_bank.py:596): bir yavru tablo ileride bir PARENT
# kolon adiyla cakisirsa shim parent'in gercek kolonunu korur, yani o erisim
# gecerli kalir -- sayac onu "kalan is" diye raporlamamalidir. Cakisma bugun YOK
# (olculdu), ama guard olmasaydi ornegin `is_active` cakismasi 95 gecerli erisimi
# borc gibi gosterirdi.
SPLIT_FIELDS: dict[str, str] = {}
for table in (QuestionContent, QuestionMetadata, QuestionStatistics):
    for col in table.__table__.columns:
        if col.name != "id" and not hasattr(QuestionBankItem, col.name):
            SPLIT_FIELDS[col.name] = table.__name__

# `.values(alan=...)` / `.filter_by(alan=...)` -- alan adinin keyword olarak gectigi cagrilar.
KWARG_METHODS = frozenset({"values", "filter_by"})

SCAN_DIRS = (
    "services",
    "api",
    "core",
    "app",
    "tasks",
    "models",
    "algorithms",
    # Asagidaki uc dizin ilk surumde atlanmisti; kapsam disi kalmalari sayaci
    # yine bir ALT SINIR haline getiriyordu. Katki OLCULDU: bu dosyanin main()'i
    # SCAN_DIRS monkeypatch'lenerek iki kez kosuldu --
    #     ilk 7 dizin -> TOPLAM SINIF=105 ENTITY=60
    #     tam 10 dizin -> TOPLAM SINIF=146 ENTITY=66
    # yani uc dizinin katkisi = 41 SINIF + 6 ENTITY (iki kosumun farki).
    "analytics",
    "application",
    "repositories",
)


def aliases_for(tree: ast.AST) -> set[str]:
    """`QuestionBankItem` bu dosyada hangi isimlerle görünüyor?"""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and "question_bank" in (node.module or ""):
            for a in node.names:
                if a.name == "QuestionBankItem":
                    names.add(a.asname or a.name)
    return names


def _call_hits(
    node: ast.Call, names: set[str]
) -> tuple[list[tuple[int, str, str]], list[tuple[int, str, str, str]]]:
    """Bir çağrı düğümünden ENTITY ve KWARG kalemlerini çıkarır.

    `scan`'den ayrıldı: tek gövdede tutmak dal sayısını ruff eşiğinin üstüne
    çıkarıyordu (PLR0912, 14 > 12).
    """
    entities: list[tuple[int, str, str]] = []
    kwargs_hits: list[tuple[int, str, str, str]] = []
    func = node.func

    # ENTITY: select(<alias>) / select(<alias>, X)  --> ciplak isim cagrisi
    if isinstance(func, ast.Name) and func.id == "select":
        entities += [
            (node.lineno, a.id, "select")
            for a in node.args
            if isinstance(a, ast.Name) and a.id in names
        ]
    elif isinstance(func, ast.Attribute):
        # ENTITY: <db>.query(<alias>) --> select() ile ayni entity, ayni lazy-load riski
        if func.attr == "query":
            entities += [
                (node.lineno, a.id, "query")
                for a in node.args
                if isinstance(a, ast.Name) and a.id in names
            ]
        # KWARG: .values(<split_alan>=...) / .filter_by(<split_alan>=...)
        if func.attr in KWARG_METHODS:
            kwargs_hits += [
                (node.lineno, kw.arg, SPLIT_FIELDS[kw.arg], func.attr)
                for kw in node.keywords
                if kw.arg in SPLIT_FIELDS
            ]
    return entities, kwargs_hits


def scan(
    path: Path,
) -> tuple[
    list[tuple[int, str, str]],
    list[tuple[int, str, str]],
    list[tuple[int, str, str, str]],
]:
    """Dosyayı tara. Parse edilemeyen dosyada `SyntaxError` YÜKSELTİR (yutmaz).

    Sessiz `return [], []` bir ölçüm aletinde yanlış-sıfır üretir: dosya çıktıdan
    tamamen kaybolur ve TOPLAM düşer — bu, "iş bitti" gibi okunur. BOM'lu dosya
    bu yüzden `utf-8-sig` ile okunuyor (görev #456 emsali).
    """
    tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="ignore"))

    names = aliases_for(tree)
    if not names:
        return [], [], []

    class_level: list[tuple[int, str, str]] = []
    entities: list[tuple[int, str, str]] = []
    kwargs_hits: list[tuple[int, str, str, str]] = []

    for node in ast.walk(tree):
        # SINIF düzeyi: <alias>.<split_alan>
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in names
            and node.attr in SPLIT_FIELDS
        ):
            class_level.append((node.lineno, node.attr, SPLIT_FIELDS[node.attr]))
        elif isinstance(node, ast.Call):
            ent, kws = _call_hits(node, names)
            entities.extend(ent)
            kwargs_hits.extend(kws)

    return class_level, entities, kwargs_hits


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    tot_c = tot_e = tot_k = 0
    unparsed: list[tuple[Path, str]] = []

    for d in SCAN_DIRS:
        for p in sorted((root / d).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            try:
                cls, ent, kws = scan(p)
            except SyntaxError as exc:  # KOR NOKTA: yutma, gorunur kil
                unparsed.append((p.relative_to(root), str(exc)))
                continue
            if not cls and not ent and not kws:
                continue
            rel = p.relative_to(root)
            tot_c += len(cls)
            tot_e += len(ent)
            tot_k += len(kws)
            print(f"\n{rel}  [SINIF={len(cls)} KWARG={len(kws)} ENTITY={len(ent)}]")
            for lineno, attr, table in cls:
                print(f"    SINIF   :{lineno:<5} .{attr}  -> {table}")
            for lineno, kwname, table, method in kws:
                print(f"    KWARG   :{lineno:<5} .{method}({kwname}=...)  -> {table}")
            for lineno, alias, kind in ent:
                print(f"    ENTITY  :{lineno:<5} {kind}({alias})")

    for rel, err in unparsed:
        print(f"PARSE EDILEMEDI: {rel} -- {err}", file=sys.stderr)

    print(
        f"\n{'=' * 60}\n"
        f"TOPLAM  SINIF={tot_c}  KWARG={tot_k}  ENTITY={tot_e}"
        f"  (parse edilemeyen dosya: {len(unparsed)})"
    )


if __name__ == "__main__":
    main()
