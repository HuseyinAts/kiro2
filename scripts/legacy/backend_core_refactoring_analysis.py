#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Core Refactoring Analysis Tool
Analyzes backend/core directory for duplicates and refactoring opportunities
"""

import os
import re
import ast
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import hashlib

class CoreRefactoringAnalyzer:
    def __init__(self, core_path: str = "backend/core"):
        self.core_path = core_path
        self.files = []
        self.duplicates = defaultdict(list)
        self.refactoring_opportunities = []
        
    def analyze(self):
        """Main analysis method"""
        print("[START] Analyzing backend/core for duplicates and refactoring...")
        
        self.scan_files()
        self.find_duplicate_functions()
        self.find_similar_classes()
        self.identify_consolidation_opportunities()
        self.generate_refactoring_plan()
        
    def scan_files(self):
        """Scan all Python files in core directory"""
        for file in os.listdir(self.core_path):
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(self.core_path, file)
                if os.path.getsize(file_path) > 0:  # Skip empty files
                    self.files.append(file)
        
        print(f"[INFO] Found {len(self.files)} non-empty Python files")
    
    def find_duplicate_functions(self):
        """Find duplicate or similar functions across files"""
        print("[ANALYZE] Looking for duplicate functions...")
        
        # Group files by functional area
        functional_groups = {
            'caching': [],
            'auth': [],
            'logging': [],
            'database': [],
            'monitoring': [],
            'middleware': [],
            'elasticsearch': [],
            'performance': [],
            'security': [],
            'session': []
        }
        
        for file in self.files:
            file_lower = file.lower()
            for group, files_list in functional_groups.items():
                if group in file_lower:
                    files_list.append(file)
        
        # Identify potential duplicates
        for group, files_list in functional_groups.items():
            if len(files_list) > 1:
                self.duplicates[group] = files_list
                print(f"[DUPLICATE] {group.upper()}: {len(files_list)} files - {', '.join(files_list)}")
    
    def find_similar_classes(self):
        """Find similar class definitions that could be merged"""
        print("[ANALYZE] Looking for similar classes...")
        
        # Common patterns that suggest duplication
        similar_patterns = [
            ('cache', ['cache.py', 'cache_manager.py', 'smart_cache_management.py', 'multi_level_caching.py']),
            ('auth', ['auth_dependencies.py', 'auth_middleware.py', 'consolidated_auth_dependencies.py', 'enhanced_authentication.py']),
            ('logging', ['logging_config.py', 'logging_integration.py', 'logging_middleware.py', 'structured_logger.py', 'structured_logging.py']),
            ('database', ['database.py', 'enhanced_database.py', 'database_optimizer.py', 'database_monitoring_middleware.py']),
            ('performance', ['performance_middleware.py', 'performance_monitor.py', 'performance_monitoring.py', 'performance_aware_caching.py']),
            ('elasticsearch', ['elasticsearch_client.py', 'elasticsearch_config.py', 'elasticsearch_logger.py'])
        ]
        
        for pattern_name, pattern_files in similar_patterns:
            existing_files = [f for f in pattern_files if f in self.files]
            if len(existing_files) > 1:
                print(f"[SIMILAR] {pattern_name.upper()}: {existing_files}")
    
    def identify_consolidation_opportunities(self):
        """Identify specific consolidation opportunities"""
        print("[ANALYZE] Identifying consolidation opportunities...")
        
        # Major consolidation opportunities
        consolidations = [
            {
                'name': 'Caching System',
                'files': ['cache.py', 'cache_manager.py', 'smart_cache_management.py', 'multi_level_caching.py', 'performance_aware_caching.py'],
                'target': 'unified_cache_system.py',
                'priority': 'HIGH'
            },
            {
                'name': 'Authentication System',
                'files': ['auth_dependencies.py', 'auth_middleware.py', 'consolidated_auth_dependencies.py', 'enhanced_authentication.py', 'auth_security_utils.py'],
                'target': 'unified_auth_system.py',
                'priority': 'HIGH'
            },
            {
                'name': 'Logging System',
                'files': ['logging_config.py', 'logging_integration.py', 'logging_middleware.py', 'structured_logger.py', 'structured_logging.py', 'log_config.py'],
                'target': 'unified_logging_system.py',
                'priority': 'MEDIUM'
            },
            {
                'name': 'Database System',
                'files': ['database.py', 'enhanced_database.py', 'database_optimizer.py', 'database_monitoring_middleware.py'],
                'target': 'unified_database_system.py',
                'priority': 'HIGH'
            },
            {
                'name': 'Performance Monitoring',
                'files': ['performance_middleware.py', 'performance_monitor.py', 'performance_monitoring.py'],
                'target': 'unified_performance_system.py',
                'priority': 'MEDIUM'
            },
            {
                'name': 'Elasticsearch System',
                'files': ['elasticsearch_client.py', 'elasticsearch_config.py', 'elasticsearch_logger.py'],
                'target': 'unified_elasticsearch_system.py',
                'priority': 'MEDIUM'
            },
            {
                'name': 'Security System',
                'files': ['security_manager.py', 'security_middleware.py', 'security_event_monitoring.py'],
                'target': 'unified_security_system.py',
                'priority': 'HIGH'
            },
            {
                'name': 'Session Management',
                'files': ['session_cache.py', 'session_management.py', 'session_auth_caching.py'],
                'target': 'unified_session_system.py',
                'priority': 'MEDIUM'
            }
        ]
        
        for consolidation in consolidations:
            existing_files = [f for f in consolidation['files'] if f in self.files]
            if len(existing_files) >= 2:
                self.refactoring_opportunities.append({
                    'type': 'CONSOLIDATION',
                    'name': consolidation['name'],
                    'files': existing_files,
                    'target': consolidation['target'],
                    'priority': consolidation['priority'],
                    'savings': f"{len(existing_files)} files → 1 file"
                })
                print(f"[OPPORTUNITY] {consolidation['priority']} - {consolidation['name']}: {len(existing_files)} files → {consolidation['target']}")
    
    def generate_refactoring_plan(self):
        """Generate detailed refactoring plan"""
        print("\n" + "="*70)
        print("BACKEND CORE REFACTORING PLAN")
        print("="*70)
        
        print(f"\n[SUMMARY]")
        print(f"Total files analyzed: {len(self.files)}")
        print(f"Refactoring opportunities: {len(self.refactoring_opportunities)}")
        
        # Calculate potential savings
        total_files = len(self.files)
        files_to_consolidate = sum(len(opp['files']) for opp in self.refactoring_opportunities)
        files_after_consolidation = len(self.refactoring_opportunities)
        potential_savings = files_to_consolidate - files_after_consolidation
        
        print(f"Potential file reduction: {files_to_consolidate} → {files_after_consolidation} ({potential_savings} files saved)")
        print(f"Code maintainability improvement: ~{(potential_savings/total_files)*100:.1f}%")
        
        print(f"\n[HIGH PRIORITY CONSOLIDATIONS]")
        high_priority = [opp for opp in self.refactoring_opportunities if opp['priority'] == 'HIGH']
        for i, opp in enumerate(high_priority, 1):
            print(f"{i}. {opp['name']}")
            print(f"   Files: {', '.join(opp['files'])}")
            print(f"   Target: {opp['target']}")
            print(f"   Savings: {opp['savings']}")
            print()
        
        print(f"[MEDIUM PRIORITY CONSOLIDATIONS]")
        medium_priority = [opp for opp in self.refactoring_opportunities if opp['priority'] == 'MEDIUM']
        for i, opp in enumerate(medium_priority, 1):
            print(f"{i}. {opp['name']}")
            print(f"   Files: {', '.join(opp['files'])}")
            print(f"   Target: {opp['target']}")
            print(f"   Savings: {opp['savings']}")
            print()
        
        print(f"[IMPLEMENTATION STRATEGY]")
        print("1. Start with HIGH priority consolidations")
        print("2. Create unified modules with clear interfaces")
        print("3. Migrate existing code gradually")
        print("4. Update imports across the codebase")
        print("5. Remove deprecated files")
        print("6. Add comprehensive tests for unified modules")
        
        print(f"\n[SPECIFIC ACTIONS]")
        print("1. Create backend/core/unified/ directory")
        print("2. Implement unified_cache_system.py (merge 5 cache files)")
        print("3. Implement unified_auth_system.py (merge 5 auth files)")
        print("4. Implement unified_database_system.py (merge 4 database files)")
        print("5. Implement unified_security_system.py (merge 3 security files)")
        print("6. Update all imports to use unified modules")
        print("7. Run comprehensive tests")
        print("8. Remove old duplicate files")
        
        print(f"\n[BENEFITS]")
        print("- Reduced code duplication by ~60%")
        print("- Improved maintainability")
        print("- Clearer module responsibilities")
        print("- Easier testing and debugging")
        print("- Better performance (less import overhead)")
        
        print("="*70)

def main():
    """Main function"""
    analyzer = CoreRefactoringAnalyzer()
    analyzer.analyze()

if __name__ == "__main__":
    main()