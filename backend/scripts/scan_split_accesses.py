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
  ENTITY  — `select(<alias>)` / `select(<alias>, ...)` (entity-select → lazy='select'
            ilişkilere örnek-düzeyi erişim async'te MissingGreenlet riski)
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.question_bank import (
    QuestionContent,
    QuestionMetadata,
    QuestionStatistics,
)

SPLIT_FIELDS: dict[str, str] = {}
for table in (QuestionContent, QuestionMetadata, QuestionStatistics):
    for col in table.__table__.columns:
        if col.name != "id":
            SPLIT_FIELDS[col.name] = table.__name__

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


def scan(path: Path) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return [], []

    names = aliases_for(tree)
    if not names:
        return [], []

    class_level: list[tuple[int, str, str]] = []
    entity_selects: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        # SINIF düzeyi: <alias>.<split_alan>
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in names
            and node.attr in SPLIT_FIELDS
        ):
            class_level.append((node.lineno, node.attr, SPLIT_FIELDS[node.attr]))

        # ENTITY select: select(<alias>) veya select(<alias>, X)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "select"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in names:
                    entity_selects.append((node.lineno, arg.id))

    return class_level, entity_selects


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    tot_c = tot_e = 0
    for d in SCAN_DIRS:
        for p in sorted((root / d).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            cls, ent = scan(p)
            if not cls and not ent:
                continue
            rel = p.relative_to(root)
            tot_c += len(cls)
            tot_e += len(ent)
            print(f"\n{rel}  [SINIF={len(cls)} ENTITY={len(ent)}]")
            for lineno, attr, table in cls:
                print(f"    SINIF   :{lineno:<5} .{attr}  -> {table}")
            for lineno, alias in ent:
                print(f"    ENTITY  :{lineno:<5} select({alias})")
    print(f"\n{'=' * 60}\nTOPLAM  SINIF={tot_c}  ENTITY={tot_e}")


if __name__ == "__main__":
    main()
