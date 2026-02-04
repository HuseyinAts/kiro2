#!/usr/bin/env python3
"""
Backend Endpoint Lister
Lists all FastAPI endpoints with their methods and paths
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

def extract_endpoints_from_file(file_path: Path) -> list:
    """Extract endpoints from a Python file"""
    endpoints = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Pattern for FastAPI route decorators
        patterns = [
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                endpoints.append({
                    'method': method,
                    'path': path,
                    'file': str(file_path)
                })
        
        # Pattern for APIRouter prefix
        prefix_pattern = r'APIRouter\(prefix=["\']([^"\']+)["\']'
        prefix_matches = re.finditer(prefix_pattern, content)
        for match in prefix_matches:
            prefix = match.group(1)
            # Store prefix for later use
            for endpoint in endpoints:
                if endpoint['file'] == str(file_path) and not endpoint['path'].startswith('/api'):
                    endpoint['path'] = prefix + endpoint['path']
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    return endpoints

def main():
    backend_root = Path("backend")
    
    if not backend_root.exists():
        print("Backend directory not found!")
        return
    
    all_endpoints = []
    
    # Search for Python files in API directories
    api_dirs = [
        backend_root / "api",
        backend_root / "app" / "api",
        backend_root / "backend" / "api"
    ]
    
    for api_dir in api_dirs:
        if not api_dir.exists():
            continue
        
        for py_file in api_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            endpoints = extract_endpoints_from_file(py_file)
            all_endpoints.extend(endpoints)
    
    # Group by method
    by_method = defaultdict(list)
    for endpoint in all_endpoints:
        by_method[endpoint['method']].append(endpoint)
    
    # Print organized list
    print("=" * 80)
    print("BACKEND API ENDPOINTS")
    print("=" * 80)
    print(f"\nTotal Endpoints: {len(all_endpoints)}\n")
    
    for method in sorted(by_method.keys()):
        print(f"\n{method} ({len(by_method[method])} endpoints)")
        print("-" * 80)
        for endpoint in sorted(by_method[method], key=lambda x: x['path']):
            print(f"  {endpoint['path']}")
    
    # Print by path (sorted)
    print("\n\n" + "=" * 80)
    print("ALL ENDPOINTS (Sorted by Path)")
    print("=" * 80)
    for endpoint in sorted(all_endpoints, key=lambda x: x['path']):
        print(f"{endpoint['method']:6} {endpoint['path']}")

if __name__ == "__main__":
    main()
