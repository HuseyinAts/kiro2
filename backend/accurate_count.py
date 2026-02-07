import subprocess, sys, os, re

env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}
cwd = r"C:\Users\husey\kiro2\backend"

ignores = [
    "--ignore=tests/unit/services/claude_md_improvement/test_doc_updater_service.py",
    "--ignore=tests/unit/test_enums.py",
    "--ignore=tests/unit/test_services_batch2.py",
    "--ignore=tests/unit/test_user_models.py",
    "--ignore=tests/unit/test_core_batch1.py",
    "--ignore=tests/integration/test_elasticsearch_client.py",
    "--ignore=tests/integration/test_learning_path_database.py",
    "--ignore=tests/integration/test_models.py",
    "--ignore=tests/integration/test_multi_agent_blackboard.py",
    "--ignore=tests/integration/test_performance_optimization.py",
    "--ignore=tests/integration/test_production_health_monitor.py",
    "--ignore=tests/integration/test_real_database_operations.py",
    "--ignore=tests/integration/test_structured_logging.py",
]

args = [sys.executable, "-m", "pytest", "tests/unit/", "tests/integration/",
        "--no-cov", "-p", "no:cacheprovider", "-p", "no:capture",
        "--tb=no", "-v", "--maxfail=300"] + ignores

outfile = os.path.join(cwd, "_final_verbose.txt")
with open(outfile, 'w', encoding='utf-8', errors='replace') as fout:
    result = subprocess.run(args, cwd=cwd, stdout=fout, stderr=subprocess.STDOUT,
                           timeout=600, env=env)

with open(outfile, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

clean = re.sub(r'\x1b\[[0-9;]*m', '', content)
lines = clean.split('\n')

passed = sum(1 for l in lines if ' PASSED' in l and '::' in l)
failed = sum(1 for l in lines if ' FAILED' in l and '::' in l)
errored = sum(1 for l in lines if ' ERROR' in l and '::' in l)

print(f"PASSED: {passed}")
print(f"FAILED: {failed}")
print(f"ERROR: {errored}")
print(f"TOTAL: {passed + failed + errored}")
if passed + failed + errored > 0:
    print(f"PASS RATE: {passed/(passed+failed+errored)*100:.1f}%")

# Also find summary line
for l in lines[-20:]:
    if 'passed' in l or 'failed' in l or 'error' in l:
        print(f"SUMMARY: {l.strip()}")

# Failures by file
from collections import Counter
ff = Counter()
for l in lines:
    if ' FAILED' in l and '::' in l:
        fn = l.split(' FAILED')[0].split('::')[0].strip().split('\\')[-1].split('/')[-1]
        ff[fn] += 1
if ff:
    print("FAILURES BY FILE:")
    for k,v in sorted(ff.items(), key=lambda x:-x[1]):
        print(f"  {v:3d} {k}")

print(f"\nEXIT CODE: {result.returncode}")
