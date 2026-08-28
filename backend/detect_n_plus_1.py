"""
N+1 Query Detection Script - Sprint 1 Phase 2

Detects real N+1 query patterns vs false positives.
"""
import re
from collections import defaultdict
from pathlib import Path


def detect_n_plus_1_patterns(file_path):
    """Detect N+1 query patterns in a Python file"""
    with open(file_path, encoding='utf-8') as f:
        try:
            content = f.read()
        except Exception:
            return []

    lines = content.split('\n')
    issues = []

    # Pattern 1: Database query in for loop
    in_loop = False
    loop_indent = 0
    loop_start_line = 0

    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()

        # Detect loop start
        if re.match(r'(for|while)\s+.*:', stripped):
            in_loop = True
            loop_indent = len(line) - len(stripped)
            loop_start_line = i
            continue

        # Detect loop end (dedent)
        if in_loop and stripped and not stripped.startswith('#'):
            current_indent = len(line) - len(stripped)
            if current_indent <= loop_indent:
                in_loop = False
                continue

        # Check for queries inside loop
        if in_loop:
            # Pattern: db.execute, session.execute, db.query
            if re.search(r'(db|session)\.(execute|query|scalar|get)\(', stripped):
                # Exclude common false positives
                if 'in_' in stripped or '.in_(' in stripped:
                    continue  # Likely using IN clause (batch query)
                if 'bulk_' in stripped or 'batch_' in stripped:
                    continue  # Likely batch operation

                issues.append({
                    'type': 'CRITICAL',
                    'pattern': 'Query in loop',
                    'line': i,
                    'code': stripped[:80],
                    'loop_start': loop_start_line
                })

            # Pattern: await db operation
            if re.search(r'await.*\.(execute|query|scalar|get|add|commit)\(', stripped):
                if 'in_' in stripped or '.in_(' in stripped:
                    continue
                if 'bulk_' in stripped or 'batch_' in stripped:
                    continue

                issues.append({
                    'type': 'CRITICAL',
                    'pattern': 'Async query in loop',
                    'line': i,
                    'code': stripped[:80],
                    'loop_start': loop_start_line
                })

    return issues


def scan_codebase():
    """Scan all service files for N+1 patterns"""
    services_dir = Path(__file__).parent / 'services'
    api_dir = Path(__file__).parent / 'api'

    all_issues = defaultdict(list)
    file_priorities = {}

    for directory in [services_dir, api_dir]:
        if not directory.exists():
            continue

        for py_file in directory.rglob('*.py'):
            if '__pycache__' in str(py_file) or 'test_' in py_file.name:
                continue

            issues = detect_n_plus_1_patterns(py_file)
            if issues:
                rel_path = py_file.relative_to(Path(__file__).parent)
                all_issues[str(rel_path)] = issues

                # Calculate priority score
                critical_count = sum(1 for i in issues if i['type'] == 'CRITICAL')
                priority = critical_count * 10
                file_priorities[str(rel_path)] = priority

    return all_issues, file_priorities


def main():
    print("N+1 QUERY DETECTION - Sprint 1 Phase 2")
    print("=" * 80)

    all_issues, file_priorities = scan_codebase()

    if not all_issues:
        print("No N+1 query patterns detected!")
        return

    # Sort files by priority
    sorted_files = sorted(file_priorities.items(), key=lambda x: x[1], reverse=True)

    critical_total = sum(1 for issues in all_issues.values() for i in issues if i['type'] == 'CRITICAL')

    print(f"\nSUMMARY: Found {critical_total} potential CRITICAL N+1 issues in {len(all_issues)} files\n")
    print("TOP 10 FILES:\n")

    # Show top 10 files
    for file_path, priority in sorted_files[:10]:
        issues = all_issues[file_path]
        critical = sum(1 for i in issues if i['type'] == 'CRITICAL')

        print(f"{file_path}: {critical} critical issues")

        # Show issues
        for issue in issues[:2]:
            print(f"  Line {issue['line']}: {issue['pattern']}")
            print(f"  {issue['code'][:60]}")

        print()

if __name__ == '__main__':
    main()
