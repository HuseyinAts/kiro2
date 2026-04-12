"""Audit: ORM column types vs live PostgreSQL schema (rule-of-seven sweep).

Session 155 prophylactic tooling. Closes the gap that let GF106 (Wave 12)
and GF115 (Session 153) hide for weeks.

Background
==========
Two recurring asyncpg crash classes have been ground out of KIRO2 by hand
across Sessions 142-154. Both are silent until the first INSERT/SELECT
hits the live driver:

  Forward rule-of-seven  (Session 142, GF26/GF36/GF49/GF59/GF94, etc.)
      ORM declares  Column(String, default=lambda: str(uuid4()))
      DB column is  uuid NOT NULL DEFAULT gen_random_uuid()
      asyncpg refuses the $1::VARCHAR bind: "expected str, got UUID"
      Fix: caller-side  id=str(uuid4())  coercion (or convert ORM to UUID)

  Inverse rule-of-seven  (Session 153/154, GF115 osb_settings + 6 review tables)
      ORM declares  Column(UUID(as_uuid=True))  *or*  Column(String)
      DB column is  uuid (or vice versa)
      asyncpg refuses the bind: "column is of type uuid but expression is
      character varying"  /  "operator does not exist"
      Fix: align the ORM declaration to the live DB column

A third class is **schema drift**: the ORM declares columns the live table
doesn't have (GF106 student_reviews dropped 18+ columns; GF113 COPPA had
child_id type mismatch; GF115 osb_settings was missing 3 booleans). The
crash signature is `UndefinedColumnError` wrapped as SQLAlchemy
`ProgrammingError`.

This audit walks every ORM table in `models/` and compares column-by-column
against `information_schema.columns` in the live `kiro2` database. It does
not run any DDL, does not write anything, and does not need superuser.

What it flags
=============
HIGH    String/Text in ORM, uuid in DB             (inverse rule-of-seven)
HIGH    UUID in ORM, varchar/text in DB            (forward rule-of-seven)
HIGH    Integer in ORM, varchar/text in DB         (GF113 COPPA pattern)
HIGH    String in ORM, integer in DB
HIGH    ORM declares column the DB does not have   (schema drift, GF106)
MEDIUM  bool/timestamp/json family mismatch        (less common, asyncpg
                                                    will usually coerce)
LOW     DB has columns the ORM does not declare    (ORM out of date — info)
LOW     nullability mismatch                       (no crash, but wrong
                                                    constraint contract)

What it does NOT flag (intentional)
- ORM table that is not present in DB (migration pending — different audit)
- DB table that is not in any ORM (legacy / not tracked yet)
- ARRAY type granularity (asyncpg handles array element types fine)
- Numeric precision/scale, varchar length
- Default values (DEFAULT gen_random_uuid() vs Python default=uuid4 are
  semantically equivalent and live in two different layers)

Usage
=====
    python backend/scripts/audit_orm_schema_drift.py            # report
    python backend/scripts/audit_orm_schema_drift.py --fail     # CI gate
    python backend/scripts/audit_orm_schema_drift.py --json out.json
    python backend/scripts/audit_orm_schema_drift.py --table student_reviews

Environment
-----------
DATABASE_URL  must be set to a postgresql:// URL with read access to the
              kiro2 database. Falls back to
              postgresql://postgres:postgres@localhost:5434/kiro2

Exit codes
----------
0  clean (or report-only mode without --fail)
1  HIGH-severity findings AND --fail passed
2  could not connect to DB / could not load ORM
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pkgutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# psycopg2 is already a project dep (used elsewhere in scripts/).
import psycopg2

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))


# ---------------------------------------------------------------------------
# SQLAlchemy type → canonical PostgreSQL udt_name mapping
# ---------------------------------------------------------------------------
#
# We collapse the SQLAlchemy column type to a small set of canonical names
# that match psql's udt_name convention. The mapping is intentionally coarse:
# we only care about the *family*, not the precision/length, because asyncpg
# only refuses binds across families (varchar→uuid, int→varchar, etc.).
#
# Probed against the 222 ORM tables in models/ on 2026-04-12 — see the
# table at the bottom of `# Probe …` in the docstring above for the full
# class list. New SQLAlchemy types should be added here as they appear.

STRING_FAMILY = {"varchar", "text", "bpchar", "char", "name"}
INTEGER_FAMILY = {"int2", "int4", "int8"}
FLOAT_FAMILY = {"float4", "float8", "numeric"}
TIMESTAMP_FAMILY = {"timestamp", "timestamptz"}
JSON_FAMILY = {"json", "jsonb"}


def canonicalize_orm_type(col_type) -> str:
    """Return the canonical udt_name for a SQLAlchemy column type.

    Returns 'unknown' for types we don't model — those produce LOW-severity
    findings instead of crashing the audit.
    """
    cls = type(col_type).__name__
    # Check class name first (cheapest), then fall back to the str repr.
    mapping = {
        "UUID": "uuid",
        "String": "varchar",
        "VARCHAR": "varchar",
        "Text": "text",
        "TEXT": "text",
        "Integer": "int4",
        "INTEGER": "int4",
        "BigInteger": "int8",
        "BIGINT": "int8",
        "SmallInteger": "int2",
        "SMALLINT": "int2",
        "Boolean": "bool",
        "BOOLEAN": "bool",
        "Date": "date",
        "DATE": "date",
        "DateTime": "timestamp",
        "DATETIME": "timestamp",
        "TIMESTAMP": "timestamp",
        "Time": "time",
        "TIME": "time",
        "Float": "float8",
        "FLOAT": "float8",
        "Numeric": "numeric",
        "NUMERIC": "numeric",
        "JSON": "json",
        "JSONB": "jsonb",
        "ARRAY": "array",
        # SQLAlchemy Enum compiles to varchar by default in our codebase
        # (we use values_callable + create_type=False — see GF16 KVKK fix).
        "Enum": "varchar",
        "SQLEnum": "varchar",
    }
    return mapping.get(cls, "unknown")


def family(udt: str) -> str:
    """Group canonical types into compatibility families."""
    if udt in STRING_FAMILY:
        return "string"
    if udt in INTEGER_FAMILY:
        return "integer"
    if udt in FLOAT_FAMILY:
        return "float"
    if udt in TIMESTAMP_FAMILY:
        return "timestamp"
    if udt in JSON_FAMILY:
        return "json"
    return udt  # uuid, bool, date, time, array, unknown — each their own family


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    severity: str  # "HIGH" | "MEDIUM" | "LOW"
    pattern: str  # short tag, see PATTERN_* below
    table: str
    column: str
    orm_type: str
    db_type: str
    detail: str

    def fmt(self) -> str:
        return (
            f"  [{self.severity}] {self.table}.{self.column}  "
            f"orm={self.orm_type}  db={self.db_type}  "
            f"({self.pattern})\n"
            f"      {self.detail}"
        )


PATTERN_INVERSE_R7 = "inverse-rule-of-seven"
PATTERN_FORWARD_R7 = "forward-rule-of-seven"
PATTERN_INT_VS_STR = "int-vs-string"
PATTERN_MISSING_DB_COL = "orm-declares-missing-db-col"
PATTERN_EXTRA_DB_COL = "db-has-extra-col"
PATTERN_NULLABILITY = "nullability-mismatch"
PATTERN_FAMILY_MISMATCH = "family-mismatch"
PATTERN_TIMESTAMP_TZ = "timestamp-tz-mismatch"


# ---------------------------------------------------------------------------
# ORM loader
# ---------------------------------------------------------------------------


def load_orm_metadata():
    """Walk-import every module under backend/models/ and return Base.metadata."""
    import models
    from models.base import Base

    for _finder, name, _ispkg in pkgutil.iter_modules(models.__path__):
        if name.startswith("_") or name == "base" or "deprecated" in name:
            continue
        try:
            importlib.import_module(f"models.{name}")
        except Exception:
            # Some modules have heavy import-time side effects (LLM init,
            # JVM bridges, optional deps). The audit doesn't need them to
            # parse — Base.metadata is populated as a side effect of class
            # body execution, which happens at module import. Modules that
            # fail to import contribute zero tables but don't break the
            # other 200+.
            continue

    return Base.metadata


# ---------------------------------------------------------------------------
# DB loader
# ---------------------------------------------------------------------------


def fetch_db_columns(conn) -> dict[str, dict[str, dict]]:
    """Return {table: {column: {udt_name, is_nullable, data_type}}} for public schema."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name, column_name, udt_name, is_nullable, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )
    out: dict[str, dict[str, dict]] = {}
    for table, col, udt, nullable, dtype in cur.fetchall():
        out.setdefault(table, {})[col] = {
            "udt_name": udt,
            "is_nullable": nullable == "YES",
            "data_type": dtype,
        }
    cur.close()
    return out


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare_table(
    table_name: str,
    orm_table,
    db_columns: dict[str, dict],
    table_filter: str | None,
) -> list[Finding]:
    if table_filter and table_name != table_filter:
        return []

    findings: list[Finding] = []
    orm_cols = {col.name: col for col in orm_table.columns}

    # Pass 1: every ORM column has a corresponding DB column with compatible type.
    for col_name, orm_col in orm_cols.items():
        if col_name not in db_columns:
            findings.append(
                Finding(
                    severity="HIGH",
                    pattern=PATTERN_MISSING_DB_COL,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type="<missing>",
                    detail=(
                        f"ORM declares `{col_name}` but live DB has no such column. "
                        f"Every INSERT/SELECT touching this column will crash with "
                        f"UndefinedColumnError. Either add a migration or remove the "
                        f"ORM declaration."
                    ),
                )
            )
            continue

        db_col = db_columns[col_name]
        orm_canonical = canonicalize_orm_type(orm_col.type)
        db_canonical = db_col["udt_name"]

        # Skip unknowns (custom types, server-side types we don't model).
        if orm_canonical == "unknown":
            continue

        # ARRAY in ORM matches anything starting with `_` (PG array convention).
        if orm_canonical == "array":
            if not db_canonical.startswith("_"):
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        pattern=PATTERN_FAMILY_MISMATCH,
                        table=table_name,
                        column=col_name,
                        orm_type=str(orm_col.type),
                        db_type=db_canonical,
                        detail="ORM declares ARRAY but DB column is not an array type.",
                    )
                )
            continue

        orm_fam = family(orm_canonical)
        db_fam = family(db_canonical)

        if orm_fam == db_fam:
            # Same family — no crash. Optionally check tz / nullability.
            if (orm_canonical == "timestamp" and db_canonical == "timestamptz") or (
                orm_canonical == "timestamptz" and db_canonical == "timestamp"
            ):
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        pattern=PATTERN_TIMESTAMP_TZ,
                        table=table_name,
                        column=col_name,
                        orm_type=str(orm_col.type),
                        db_type=db_col["data_type"],
                        detail=(
                            "Timestamp tz-awareness drift. Caller may pass tz-aware "
                            "datetime to a tz-naive column (or vice versa) — asyncpg "
                            "raises DataError. See Wave 6 GF41 reasoning_cache."
                        ),
                    )
                )
            # Nullability check (LOW)
            orm_nullable = bool(orm_col.nullable)
            db_nullable = db_col["is_nullable"]
            if orm_nullable != db_nullable:
                findings.append(
                    Finding(
                        severity="LOW",
                        pattern=PATTERN_NULLABILITY,
                        table=table_name,
                        column=col_name,
                        orm_type=f"nullable={orm_nullable}",
                        db_type=f"nullable={db_nullable}",
                        detail=(
                            "Nullability contract drift. No crash, but ORM and DB "
                            "disagree on whether NULL is allowed."
                        ),
                    )
                )
            continue

        # Cross-family mismatches → flag with severity by class.
        if orm_fam == "string" and db_canonical == "uuid":
            findings.append(
                Finding(
                    severity="HIGH",
                    pattern=PATTERN_INVERSE_R7,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type=db_canonical,
                    detail=(
                        "INVERSE rule-of-seven: ORM declares String/VARCHAR but DB "
                        "column is uuid. asyncpg refuses $1::VARCHAR bind with "
                        "DatatypeMismatchError. Fix at the model: "
                        "Column(UUID(as_uuid=True), default=uuid4). See "
                        "Session 153 GF115 osb_settings + Session 154 6 review tables."
                    ),
                )
            )
        elif orm_canonical == "uuid" and db_fam == "string":
            findings.append(
                Finding(
                    severity="HIGH",
                    pattern=PATTERN_FORWARD_R7,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type=db_canonical,
                    detail=(
                        "FORWARD rule-of-seven: ORM declares UUID but DB column is "
                        "varchar/text. asyncpg refuses bind with DataError "
                        "'expected str, got UUID'. Fix at the caller: "
                        "id=str(uuid4()), or convert the column to uuid in DB. "
                        "See Wave 6 GF26/GF36/GF49 + Session 142 VideoAnalytics."
                    ),
                )
            )
        elif orm_fam == "integer" and db_fam == "string":
            findings.append(
                Finding(
                    severity="HIGH",
                    pattern=PATTERN_INT_VS_STR,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type=db_canonical,
                    detail=(
                        "ORM declares Integer but DB column is varchar/text. "
                        "asyncpg crashes with 'operator does not exist'. See "
                        "Session 149 GF113 COPPA child_id."
                    ),
                )
            )
        elif orm_fam == "string" and db_fam == "integer":
            findings.append(
                Finding(
                    severity="HIGH",
                    pattern=PATTERN_INT_VS_STR,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type=db_canonical,
                    detail=(
                        "ORM declares String but DB column is integer. Bind crashes "
                        "with InvalidTextRepresentation."
                    ),
                )
            )
        else:
            # Other cross-family mismatches: usually MEDIUM (asyncpg may coerce).
            findings.append(
                Finding(
                    severity="MEDIUM",
                    pattern=PATTERN_FAMILY_MISMATCH,
                    table=table_name,
                    column=col_name,
                    orm_type=str(orm_col.type),
                    db_type=db_canonical,
                    detail=(
                        f"Type family mismatch: orm={orm_fam} ({orm_canonical}) "
                        f"vs db={db_fam} ({db_canonical}). May cause runtime "
                        f"DataError on bind."
                    ),
                )
            )

    # Pass 2: DB has columns ORM doesn't declare → LOW (info, not a crash).
    for db_col_name in db_columns:
        if db_col_name not in orm_cols:
            findings.append(
                Finding(
                    severity="LOW",
                    pattern=PATTERN_EXTRA_DB_COL,
                    table=table_name,
                    column=db_col_name,
                    orm_type="<not declared>",
                    db_type=db_columns[db_col_name]["udt_name"],
                    detail=(
                        "Live DB has this column, ORM does not. ORM is out of date "
                        "or the column is migration-only. Not a crash."
                    ),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def get_db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5434/kiro2",
    )
    # psycopg2 doesn't understand SQLAlchemy driver suffixes like +asyncpg.
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def parse_db_url(url: str) -> dict:
    # Minimal parser — psycopg2.connect() takes a DSN string directly, but
    # we want to fall through to host/port/etc. for nicer error messages.
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return {"dsn": url}
    return {"dsn": url}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit ORM column types vs live PostgreSQL schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fail",
        action="store_true",
        help="Exit with code 1 if any HIGH-severity finding is reported (CI gate).",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Write the full findings list to this path as JSON.",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="Limit the audit to a single table (debugging).",
    )
    parser.add_argument(
        "--severity",
        choices=["HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Minimum severity to print on stdout (default: HIGH).",
    )
    args = parser.parse_args()

    # Step 1: load ORM metadata.
    try:
        metadata = load_orm_metadata()
    except Exception as exc:
        print(f"[FATAL] Could not load ORM metadata: {exc}", file=sys.stderr)
        return 2

    # Step 2: connect to live DB.
    try:
        conn = psycopg2.connect(get_db_url())
    except Exception as exc:
        print(
            f"[FATAL] Could not connect to DB ({get_db_url()}): {exc}", file=sys.stderr
        )
        return 2

    try:
        db_schema = fetch_db_columns(conn)
    finally:
        conn.close()

    # Step 3: walk ORM tables, compare each.
    all_findings: list[Finding] = []
    orm_only_tables: list[str] = []
    for table_name, orm_table in sorted(metadata.tables.items()):
        if table_name not in db_schema:
            orm_only_tables.append(table_name)
            continue
        all_findings.extend(
            compare_table(table_name, orm_table, db_schema[table_name], args.table)
        )

    # Step 4: tally + print.
    by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for f in all_findings:
        by_severity[f.severity].append(f)

    severity_order = ["HIGH", "MEDIUM", "LOW"]
    visible_levels = severity_order[: severity_order.index(args.severity) + 1]

    print("=" * 78)
    print("ORM ↔ PostgreSQL schema drift audit")
    print("=" * 78)
    print(
        f"ORM tables loaded:    {len(metadata.tables)}  "
        f"({len(orm_only_tables)} not in live DB — likely pending migration)"
    )
    print(f"Live DB tables:       {len(db_schema)}")
    print(
        f"Findings:             HIGH={len(by_severity['HIGH'])}  "
        f"MEDIUM={len(by_severity['MEDIUM'])}  LOW={len(by_severity['LOW'])}"
    )
    print()

    for severity in visible_levels:
        bucket = by_severity[severity]
        if not bucket:
            continue
        print(f"--- {severity} ({len(bucket)}) " + "-" * (60 - len(severity)))
        # Group by table for readability.
        by_table: dict[str, list[Finding]] = {}
        for f in bucket:
            by_table.setdefault(f.table, []).append(f)
        for table in sorted(by_table.keys()):
            print(f"\n  {table}")
            for f in by_table[table]:
                print(f.fmt())
        print()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "summary": {
                        "orm_tables": len(metadata.tables),
                        "db_tables": len(db_schema),
                        "high": len(by_severity["HIGH"]),
                        "medium": len(by_severity["MEDIUM"]),
                        "low": len(by_severity["LOW"]),
                    },
                    "findings": [asdict(f) for f in all_findings],
                    "orm_only_tables": orm_only_tables,
                },
                fh,
                indent=2,
                ensure_ascii=False,
            )
        print(f"Wrote JSON report: {args.json}")

    if args.fail and by_severity["HIGH"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
