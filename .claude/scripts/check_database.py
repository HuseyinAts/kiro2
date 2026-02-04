#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Fact-Checker for Kiro2 Project
Verifies database status and provides accurate metrics for reporting
"""

import sqlite3
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Database file paths (relative to project root)
DB_PATHS = [
    "backend/kiro2.db",
    "backend/turkiye_sinav.db",
    "turkiye_sinav.db"
]

# Key tables to check
TABLES_TO_CHECK = [
    "sorular",
    "users",
    "exams",
    "exam_answers",
    "questions",
    "ai_chat_sessions",
    "learning_paths"
]

def check_file_exists(db_path):
    """Check if database file exists and get size"""
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        return True, size
    return False, 0

def format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_table_info(conn, table_name):
    """Get row count for a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return {"exists": True, "count": count, "error": None}
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return {"exists": False, "count": 0, "error": "Table doesn't exist"}
        return {"exists": False, "count": 0, "error": str(e)}

def list_all_tables(conn):
    """List all tables in database"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Exception as e:
        return []

def main():
    print("=" * 60)
    print("KIRO2 DATABASE FACT-CHECKER")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}
    total_tables = 0
    total_rows = 0

    # Check each database
    for db_path in DB_PATHS:
        db_name = os.path.basename(db_path)
        results[db_name] = {
            "path": db_path,
            "exists": False,
            "size": 0,
            "tables": {},
            "all_tables": []
        }

        # Check if file exists
        exists, size = check_file_exists(db_path)
        results[db_name]["exists"] = exists
        results[db_name]["size"] = size

        print(f"[DB] Database: {db_name}")
        print(f"   Path: {db_path}")

        if not exists:
            print(f"   Status: [X] NOT FOUND")
            print()
            continue

        print(f"   Status: [OK] EXISTS")
        print(f"   Size: {format_size(size)}")

        if size == 0:
            print(f"   [WARNING] Database file is EMPTY (0 bytes)")
            print()
            continue

        # Connect and check tables
        try:
            conn = sqlite3.connect(db_path)

            # List all tables
            all_tables = list_all_tables(conn)
            results[db_name]["all_tables"] = all_tables
            total_tables += len(all_tables)

            print(f"   Tables found: {len(all_tables)}")

            if len(all_tables) == 0:
                print(f"   [WARNING] No tables in database (migrations not run?)")
            else:
                print(f"   Table list: {', '.join(all_tables[:5])}" +
                      ("..." if len(all_tables) > 5 else ""))

            print()

            # Check specific key tables
            for table in TABLES_TO_CHECK:
                info = get_table_info(conn, table)
                results[db_name]["tables"][table] = info

                if info["exists"]:
                    total_rows += info["count"]
                    status = "[OK]" if info["count"] > 0 else "[EMPTY]"
                    print(f"   {status} {table}: {info['count']} rows")
                else:
                    print(f"   [X] {table}: {info['error']}")

            conn.close()

        except Exception as e:
            print(f"   [ERROR] Error connecting: {e}")

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    db_count = sum(1 for r in results.values() if r["exists"])
    non_empty_db = sum(1 for r in results.values() if r["exists"] and r["size"] > 0)

    print(f"Databases found: {db_count}/{len(DB_PATHS)}")
    print(f"Non-empty databases: {non_empty_db}/{db_count}")
    print(f"Total tables across all DBs: {total_tables}")
    print(f"Total rows in key tables: {total_rows}")
    print()

    # Assessment
    print("ASSESSMENT:")
    if total_rows == 0:
        print("[CRITICAL] No data in any database")
        print("   - Database structure may exist but tables are empty")
        print("   - Migration files need to be executed")
        print("   - Seed data needs to be loaded")
        print()
        print("REPORTING GUIDANCE:")
        print("   [X] Do NOT say: 'Database ready' or 'Database operational'")
        print("   [OK] DO say: 'Database files exist but tables are empty (0 rows)'")
    elif total_rows < 100:
        print(f"[WARNING] Minimal data ({total_rows} total rows)")
        print("   - Database has some test data")
        print("   - Not ready for production use")
        print("   - Needs significant data population")
        print()
        print("REPORTING GUIDANCE:")
        print(f"   [X] Do NOT say: 'Database ready with 10,000+ rows'")
        print(f"   [OK] DO say: 'Database structure exists with {total_rows} test rows (production needs more)'")
    elif total_rows < 1000:
        print(f"[PARTIAL] Development data ({total_rows} total rows)")
        print("   - Database has reasonable test data")
        print("   - Suitable for development/testing")
        print("   - Needs more data for production")
        print()
        print("REPORTING GUIDANCE:")
        print(f"   [OK] 'Database functional with {total_rows} rows (expanding to production scale)'")
    else:
        print(f"[GOOD] Production-scale data ({total_rows} total rows)")
        print("   - Database appears well-populated")
        print("   - Suitable for production use")
        print()
        print("REPORTING GUIDANCE:")
        print(f"   [OK] 'Database operational with {total_rows}+ rows'")

    print()

    # Export to JSON for automation
    output_file = ".claude/scripts/database_facts.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "databases": results,
            "summary": {
                "databases_found": db_count,
                "non_empty_databases": non_empty_db,
                "total_tables": total_tables,
                "total_rows": total_rows
            }
        }, f, indent=2)

    print(f"[OUTPUT] Detailed results saved to: {output_file}")
    print()

    # Return exit code based on data readiness
    if total_rows == 0:
        sys.exit(1)  # Critical - no data
    elif total_rows < 100:
        sys.exit(2)  # Warning - minimal data
    else:
        sys.exit(0)  # OK

if __name__ == "__main__":
    main()
