#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO/FIXME Analyzer and Prioritization Tool
Analyzes all TODO/FIXME comments and categorizes them by priority
"""
import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Priority keywords for classification
PRIORITY_KEYWORDS = {
    'P0_CRITICAL': [
        'security', 'vuln', 'breach', 'exploit', 'injection',
        'data loss', 'critical', 'urgent', 'crash', 'corruption',
        'auth', 'password', 'token', 'secret', 'leak'
    ],
    'P1_HIGH': [
        'bug', 'error', 'broken', 'fix', 'production', 'deploy',
        'performance', 'slow', 'timeout', 'memory', 'leak',
        'validation', 'sanitize', 'escape'
    ],
    'P2_MEDIUM': [
        'refactor', 'optimize', 'improve', 'cleanup', 'technical debt',
        'deprecated', 'legacy', 'migrate', 'update', 'modernize'
    ],
    'P3_LOW': [
        'nice to have', 'enhancement', 'feature', 'consider', 'maybe',
        'documentation', 'comment', 'test', 'example'
    ]
}

def classify_priority(todo_text):
    """Classify TODO based on content"""
    text_lower = todo_text.lower()

    # Check for explicit priority markers
    if re.search(r'\b(p0|critical|urgent)\b', text_lower):
        return 'P0_CRITICAL'
    if re.search(r'\b(p1|high|important)\b', text_lower):
        return 'P1_HIGH'
    if re.search(r'\b(p2|medium)\b', text_lower):
        return 'P2_MEDIUM'
    if re.search(r'\b(p3|low)\b', text_lower):
        return 'P3_LOW'

    # Check keywords
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return priority

    # Default to medium
    return 'P2_MEDIUM'

def analyze_file(file_path):
    """Analyze a single file for TODO/FIXME comments"""
    todos = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Find TODO or FIXME
                match = re.search(r'(TODO|FIXME)[:\s]*(.*)', line, re.IGNORECASE)
                if match:
                    marker = match.group(1).upper()
                    text = match.group(2).strip()
                    full_line = line.strip()

                    # Skip false positives
                    # 1. Enum values: TaskStatus.TODO = "todo"
                    if re.search(r'\w+\.TODO\s*[=:]', full_line):
                        continue

                    # 2. Dictionary keys: "TODO": value or TaskStatus.TODO: value
                    if re.search(r'["\']TODO["\']\s*:', full_line) or re.search(r'\w+\.TODO\s*:', full_line):
                        continue

                    # 3. String assignments: = "todo" or = "TODO"
                    if re.search(r'=\s*["\']todo["\']', full_line, re.IGNORECASE):
                        continue

                    # 4. Enum usages: status = TaskStatus.TODO or "status": TaskStatus.TODO
                    if re.search(r'[=:]\s*\w+\.TODO\b', full_line):
                        continue

                    # 5. Function names containing "ToDOM": applySettingsToDOM, etc.
                    if re.search(r'\w+To_?DOM', full_line, re.IGNORECASE):
                        continue

                    # 6. Turkish translation objects: todo: 'Yapılacak'
                    if re.search(r'todo:\s*["\']', full_line, re.IGNORECASE):
                        continue

                    # 7. Test assertions checking for "todo" string
                    if re.search(r'assert.*["\']todo["\']', full_line, re.IGNORECASE):
                        continue

                    # 8. Turkish words containing "TODO" pattern (metodoloji, teknoloji, etc.)
                    if re.search(r'(metodo?loji|teknoloji)', full_line, re.IGNORECASE):
                        continue

                    todos.append({
                        'file': str(file_path),
                        'line': line_num,
                        'marker': marker,
                        'text': text,
                        'full_line': full_line,
                        'priority': classify_priority(text)
                    })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return todos

def scan_directory(root_dir, extensions):
    """Scan directory for TODO/FIXME comments"""
    all_todos = []

    for ext in extensions:
        pattern = f"**/*{ext}"
        for file_path in Path(root_dir).glob(pattern):
            # Skip node_modules, venv, __pycache__, .git, and build artifacts
            skip_dirs = ['node_modules', 'venv', '__pycache__', '.git',
                        'dist', 'build', '.pytest_cache', 'htmlcov', 'assets',
                        '.next', 'out', 'coverage']
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue

            # Skip minified/compiled files
            skip_patterns = ['.min.js', '.min.css', '-D_ryMEPs.js', '.bundle.js', '.chunk.js']
            if any(pattern in file_path.name for pattern in skip_patterns):
                continue

            todos = analyze_file(file_path)
            all_todos.extend(todos)

    return all_todos

def generate_report(todos):
    """Generate detailed report"""
    # Group by priority
    by_priority = defaultdict(list)
    for todo in todos:
        by_priority[todo['priority']].append(todo)

    # Group by file
    by_file = defaultdict(list)
    for todo in todos:
        by_file[todo['file']].append(todo)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("TODO/FIXME ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")

    # Summary
    report.append("📊 SUMMARY")
    report.append("-" * 80)
    report.append(f"Total TODOs: {len(todos)}")
    report.append(f"Unique Files: {len(by_file)}")
    report.append("")

    # Priority breakdown
    report.append("🎯 PRIORITY BREAKDOWN")
    report.append("-" * 80)
    for priority in ['P0_CRITICAL', 'P1_HIGH', 'P2_MEDIUM', 'P3_LOW']:
        count = len(by_priority[priority])
        percentage = (count / len(todos) * 100) if todos else 0

        icon = {
            'P0_CRITICAL': '🔴',
            'P1_HIGH': '🟠',
            'P2_MEDIUM': '🟡',
            'P3_LOW': '🟢'
        }[priority]

        report.append(f"{icon} {priority:15s}: {count:5d} ({percentage:5.1f}%)")
    report.append("")

    # Top files with most TODOs
    report.append("📁 TOP 10 FILES WITH MOST TODOs")
    report.append("-" * 80)
    sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for i, (file_path, file_todos) in enumerate(sorted_files, 1):
        rel_path = Path(file_path).relative_to(Path.cwd()) if Path(file_path).is_absolute() else file_path
        report.append(f"{i:2d}. {rel_path} ({len(file_todos)} TODOs)")
    report.append("")

    # Helper function for relative path
    def get_rel_path(file_path):
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except (ValueError, TypeError):
            return str(file_path)

    # Critical TODOs (P0)
    if by_priority['P0_CRITICAL']:
        report.append("🔴 CRITICAL TODOs (P0) - FIX IMMEDIATELY!")
        report.append("-" * 80)
        for i, todo in enumerate(by_priority['P0_CRITICAL'][:20], 1):  # Show first 20
            rel_path = get_rel_path(todo['file'])
            report.append(f"{i:3d}. {rel_path}:{todo['line']}")
            report.append(f"     {todo['marker']}: {todo['text'][:100]}")
            report.append("")

        if len(by_priority['P0_CRITICAL']) > 20:
            report.append(f"... and {len(by_priority['P0_CRITICAL']) - 20} more critical TODOs")
        report.append("")

    # High priority TODOs (P1)
    if by_priority['P1_HIGH']:
        report.append("🟠 HIGH PRIORITY TODOs (P1) - Fix within 2 weeks")
        report.append("-" * 80)
        for i, todo in enumerate(by_priority['P1_HIGH'][:10], 1):  # Show first 10
            rel_path = get_rel_path(todo['file'])
            report.append(f"{i:3d}. {rel_path}:{todo['line']}")
            report.append(f"     {todo['marker']}: {todo['text'][:100]}")
            report.append("")

        if len(by_priority['P1_HIGH']) > 10:
            report.append(f"... and {len(by_priority['P1_HIGH']) - 10} more high priority TODOs")
        report.append("")

    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    report.append(f"1. IMMEDIATE: Fix {len(by_priority['P0_CRITICAL'])} critical TODOs")
    report.append(f"2. THIS WEEK: Address {len(by_priority['P1_HIGH'])} high priority TODOs")
    report.append(f"3. THIS MONTH: Reduce {len(by_priority['P2_MEDIUM'])} medium priority TODOs to <100")
    report.append(f"4. BACKLOG: {len(by_priority['P3_LOW'])} low priority TODOs can be deprioritized")
    report.append("")
    report.append(f"GOAL: Reduce total from {len(todos)} → 100 within 4 weeks")
    report.append("")

    return "\n".join(report), by_priority, by_file

def main():
    """Main function"""
    print("🔍 Scanning for TODO/FIXME comments...")
    print()

    # Scan backend
    print("Scanning backend/...")
    backend_todos = scan_directory('backend', ['.py'])

    # Scan frontend
    print("Scanning frontend/...")
    frontend_todos = scan_directory('frontend', ['.ts', '.tsx', '.js', '.jsx'])

    # Combine
    all_todos = backend_todos + frontend_todos

    print(f"\n✅ Found {len(all_todos)} TODOs/FIXMEs")
    print(f"   Backend: {len(backend_todos)}")
    print(f"   Frontend: {len(frontend_todos)}")
    print()

    # Generate report
    report_text, by_priority, by_file = generate_report(all_todos)

    # Save report
    report_path = 'TODO_ANALYSIS_REPORT.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"📄 Report saved to: {report_path}")
    print()

    # Save JSON for programmatic access
    json_path = 'TODO_ANALYSIS.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(all_todos),
            'by_priority': {k: len(v) for k, v in by_priority.items()},
            'todos': all_todos
        }, f, indent=2)

    print(f"📊 JSON data saved to: {json_path}")
    print()

    # Print summary
    print(report_text)

    # Return stats
    return {
        'total': len(all_todos),
        'backend': len(backend_todos),
        'frontend': len(frontend_todos),
        'by_priority': {k: len(v) for k, v in by_priority.items()}
    }

if __name__ == '__main__':
    stats = main()

    # Exit with warning if too many critical TODOs
    if stats['by_priority']['P0_CRITICAL'] > 10:
        print("\n⚠️  WARNING: High number of critical TODOs detected!")
        exit(1)
