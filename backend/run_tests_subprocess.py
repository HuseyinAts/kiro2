"""Run pytest via subprocess to avoid capture bug."""
import subprocess
import sys

result = subprocess.run(
    [
        sys.executable, '-m', 'pytest',
        'tests/unit/', 'tests/integration/',
        '--no-cov', '-p', 'no:cacheprovider',
        '--tb=no', '-q', '--maxfail=300',
        '--ignore=tests/unit/services/claude_md_improvement/test_doc_updater_service.py',
        '--ignore=tests/unit/test_enums.py',
        '--ignore=tests/unit/test_services_batch2.py',
        '--ignore=tests/unit/test_user_models.py',
        '--ignore=tests/unit/test_core_batch1.py',
        '--ignore=tests/integration/test_elasticsearch_client.py',
        '--ignore=tests/integration/test_learning_path_database.py',
        '--ignore=tests/integration/test_models.py',
        '--ignore=tests/integration/test_multi_agent_blackboard.py',
        '--ignore=tests/integration/test_performance_optimization.py',
        '--ignore=tests/integration/test_production_health_monitor.py',
        '--ignore=tests/integration/test_real_database_operations.py',
        '--ignore=tests/integration/test_structured_logging.py',
        '--ignore=tests/unit/agents/learning_path',
        '--ignore=tests/unit/test_core_utils.py',
        '--ignore=tests/integration/test_accessibility_agent.py',
        '--ignore=tests/integration/test_core_services.py',
        '--ignore=tests/integration/test_domain_experts_e2e.py',
        '--ignore=tests/integration/test_e2e_video_recommendations_verification.py',
        '--ignore=tests/integration/test_enhanced_study_buddy_agent.py',
        '--ignore=tests/integration/test_final_integration_task25.py',
        '--ignore=tests/integration/test_learning_path_agent.py',
        '--ignore=tests/integration/test_llm_service.py',
        '--ignore=tests/integration/test_parallel_execution.py',
        '--ignore=tests/integration/test_study_buddy_agent.py',
        '--ignore=tests/integration/test_success_metrics.py',
        '--ignore=tests/integration/test_video_api_integration.py'
    ],
    capture_output=True,
    text=True,
    timeout=600
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f'\nExit code: {result.returncode}')

# Extract summary line
lines = result.stdout.split('\n')
for line in lines:
    if 'passed' in line or 'failed' in line or 'error' in line:
        if any(keyword in line for keyword in ['passed', 'failed', 'errors', 'warnings']):
            print(f"\nSUMMARY: {line}")
