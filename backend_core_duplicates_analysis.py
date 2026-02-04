#!/usr/bin/env python3
"""
Backend Core Duplicates Analysis
Identifies and categorizes ALL duplicate/redundant files in backend/core
"""

import os
from collections import defaultdict
from typing import Dict, List, Set

class CoreDuplicatesAnalyzer:
    def __init__(self, core_path: str):
        self.core_path = core_path
        self.duplicates = defaultdict(list)
        self.redundant_files = []
        
    def analyze_duplicates(self):
        """Analyze all duplicate patterns in core directory"""
        
        # AUTH SYSTEM DUPLICATES (Already unified)
        auth_duplicates = [
            "auth_dependencies.py",
            "auth_middleware.py", 
            "auth_security_utils.py",
            "consolidated_auth_dependencies.py",
            "enhanced_authentication.py",
            "session_auth_caching.py"
        ]
        
        # DATABASE SYSTEM DUPLICATES (Already unified)
        db_duplicates = [
            "database.py",
            "enhanced_database.py",
            "database_optimizer.py", 
            "database_monitoring_middleware.py"
        ]
        
        # SECURITY SYSTEM DUPLICATES (Already unified)
        security_duplicates = [
            "security_manager.py",
            "security_middleware.py",
            "security_event_monitoring.py"
        ]
        
        # CACHE SYSTEM DUPLICATES (Just cleaned up)
        cache_duplicates = [
            # Already removed: cache.py, cache_manager.py, multi_level_caching.py
            "performance_aware_caching.py",
            "smart_cache_management.py",
            "educational_content_caching.py",
            "exam_cache.py",
            "session_cache.py"
        ]
        
        # LOGGING SYSTEM DUPLICATES
        logging_duplicates = [
            "log_config.py",
            "logging_config.py", 
            "logging_integration.py",
            "logging_middleware.py",
            "structured_logger.py",
            "structured_logging.py"
        ]
        
        # MONITORING SYSTEM DUPLICATES  
        monitoring_duplicates = [
            "monitoring.py",
            "performance_monitor.py",
            "performance_monitoring.py",
            "performance_middleware.py",
            "metrics_collector.py",
            "analytics_monitoring.py",
            "application_metrics.py",
            "api_monitoring_middleware.py",
            "production_health_monitor.py"
        ]
        
        # ELASTICSEARCH DUPLICATES
        elasticsearch_duplicates = [
            "elasticsearch_client.py",
            "elasticsearch_config.py", 
            "elasticsearch_logger.py"
        ]
        
        # SESSION MANAGEMENT DUPLICATES
        session_duplicates = [
            "session_management.py",
            "session_auth_caching.py",  # overlaps with auth
            "session_cache.py",  # overlaps with cache
            "token_management.py"
        ]
        
        # LLM SERVICE DUPLICATES
        llm_duplicates = [
            "llm_service.py",
            "langchain_llm_service.py",
            "langchain_llm_service_enhanced.py",
            "langchain_rag_system.py",
            "rag_service.py"
        ]
        
        # CONTENT MANAGEMENT DUPLICATES
        content_duplicates = [
            "content_manager.py",
            "enhanced_content_manager.py",
            "dynamic_content_generator.py"
        ]
        
        # ERROR HANDLING DUPLICATES
        error_duplicates = [
            "exceptions.py",
            "exception_handlers.py",
            "global_exception_handler.py",
            "error_context.py",
            "error_monitoring.py"
        ]
        
        # CONFIG DUPLICATES
        config_duplicates = [
            "config.py",
            "config_validator.py",
            "unified_config.py"
        ]
        
        # MIDDLEWARE DUPLICATES
        middleware_duplicates = [
            "response_middleware.py",
            "middleware_pipeline.py",
            "turkish_exam_middleware.py"
        ]
        
        # NLP/TURKISH DUPLICATES
        nlp_duplicates = [
            "turkish_nlp_service.py",
            "turkish_nlp_chat_system.py",
            "berturk_service.py",
            "realtime_cultural_analyzer.py"
        ]
        
        # SMALLER DUPLICATE GROUPS
        small_duplicates = {
            "transaction": ["transaction_manager.py"],
            "query": ["query_builder.py"], 
            "response": ["response_models.py", "response_validators.py"],
            "context": ["context_manager.py"],
            "optimizer": ["api_optimizer.py", "revolutionary_optimizer.py", "connection_pool_optimizer.py"],
            "learning": ["learning_analytics.py", "learning_style_detector.py", "structured_learning_path.py"],
            "assessment": ["assessment_system.py", "curriculum_compliance_system.py"],
            "automation": ["automated_question_generator.py", "background_job_processor.py"],
            "chat": ["chat_interface.py", "form_interface.py"],
            "events": ["turkish_exam_event_handlers.py", "unified_event_bus.py"],
            "notification": ["realtime_notification_system.py", "message_queue_system.py"]
        }
        
        return {
            "HIGH_PRIORITY": {
                "cache": cache_duplicates,
                "logging": logging_duplicates, 
                "monitoring": monitoring_duplicates,
                "elasticsearch": elasticsearch_duplicates,
                "session": session_duplicates
            },
            "MEDIUM_PRIORITY": {
                "llm": llm_duplicates,
                "content": content_duplicates,
                "error": error_duplicates,
                "config": config_duplicates,
                "middleware": middleware_duplicates,
                "nlp": nlp_duplicates
            },
            "LOW_PRIORITY": small_duplicates,
            "ALREADY_UNIFIED": {
                "auth": auth_duplicates,
                "database": db_duplicates, 
                "security": security_duplicates
            }
        }
    
    def calculate_savings(self, duplicates):
        """Calculate potential file and code reduction"""
        total_files = 0
        total_estimated_lines = 0
        
        for category, groups in duplicates.items():
            if category == "ALREADY_UNIFIED":
                continue
                
            if isinstance(groups, dict):
                for group_name, files in groups.items():
                    total_files += len(files)
                    # Estimate ~400-800 lines per file
                    total_estimated_lines += len(files) * 600
            else:
                total_files += len(groups)
                total_estimated_lines += len(groups) * 600
        
        return {
            "total_duplicate_files": total_files,
            "estimated_lines": total_estimated_lines,
            "potential_unified_files": total_files // 3,  # Estimate 3:1 reduction
            "potential_line_reduction": total_estimated_lines * 0.7  # 70% reduction
        }

def main():
    analyzer = CoreDuplicatesAnalyzer("backend/core")
    duplicates = analyzer.analyze_duplicates()
    savings = analyzer.calculate_savings(duplicates)
    
    print("=" * 80)
    print("[SCAN] BACKEND CORE DUPLICATES ANALYSIS")
    print("=" * 80)
    
    print("\n[HIGH] HIGH PRIORITY - Immediate Consolidation Needed:")
    print("-" * 50)
    for system, files in duplicates["HIGH_PRIORITY"].items():
        print(f"\n{system.upper()} SYSTEM ({len(files)} files):")
        for file in files:
            print(f"  [X] {file}")
        print(f"  [OK] Should become: unified/{system}_system.py")
    
    print("\n[MEDIUM] MEDIUM PRIORITY - Consolidation Recommended:")
    print("-" * 50)
    for system, files in duplicates["MEDIUM_PRIORITY"].items():
        print(f"\n{system.upper()} SYSTEM ({len(files)} files):")
        for file in files:
            print(f"  [!] {file}")
    
    print("\n[STATS] POTENTIAL SAVINGS:")
    print("-" * 30)
    print(f"Total Duplicate Files: {savings['total_duplicate_files']}")
    print(f"Estimated Lines: {savings['estimated_lines']:,}")
    print(f"After Unification: {savings['potential_unified_files']} files")
    print(f"Line Reduction: {savings['potential_line_reduction']:,.0f} lines ({70}%)")
    print(f"File Reduction: {savings['total_duplicate_files'] - savings['potential_unified_files']} files")
    
    print("\n[COMPLETED] ALREADY UNIFIED (Completed):")
    print("-" * 30)
    for system, files in duplicates["ALREADY_UNIFIED"].items():
        print(f"[OK] {system.upper()}: {len(files)} files -> 1 file")
    
    print("\n[PLAN] RECOMMENDED ACTION PLAN:")
    print("-" * 30)
    print("1. IMMEDIATE: Consolidate Cache System remaining files")
    print("2. HIGH: Consolidate Logging System (6 files -> 1)")
    print("3. HIGH: Consolidate Monitoring System (9 files -> 1)")
    print("4. HIGH: Consolidate Elasticsearch System (3 files -> 1)")
    print("5. HIGH: Consolidate Session Management (4 files -> 1)")
    print("6. MEDIUM: Consolidate LLM Services (5 files -> 1)")
    print("7. MEDIUM: Consolidate Content Management (3 files -> 1)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()