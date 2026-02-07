import subprocess, xml.etree.ElementTree as ET
xmlpath = r"c:\Users\husey\kiro2\test_results.xml"
result = subprocess.run(
    [r"c:\Users\husey\kiro2\.venv\Scripts\python.exe", "-m", "pytest", "tests/", "-q", "--tb=no",
     "--junitxml=" + xmlpath],
    cwd=r"c:\Users\husey\kiro2\backend",
    capture_output=True, text=True, timeout=240
)
try:
    tree = ET.parse(xmlpath)
    root = tree.getroot()
    ts = root.find('.//testsuite') or root
    a = ts.attrib
    print(f"Tests: {a.get('tests','?')}, Failures: {a.get('failures','?')}, Errors: {a.get('errors','?')}, Skipped: {a.get('skipped','?')}, Time: {a.get('time','?')}s")
except Exception as e:
    print(f"XML parse error: {e}")
print(f"Exit code: {result.returncode}")
