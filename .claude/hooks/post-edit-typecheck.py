#!/usr/bin/env python
"""PostToolUse: TypeScript typecheck after Edit/Write (throttled, background)."""
import json
import os
import subprocess
import sys
import time

# Windows cp1254 fix (REQUIRED)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
THROTTLE_FILE = os.path.join(HOOKS_DIR, ".typecheck_last_run")
RESULT_FILE = os.path.join(HOOKS_DIR, ".typecheck_result")
THROTTLE_SECONDS = 300  # 5 minutes
FRONTEND_DIR = "C:/Users/husey/kiro2/frontend"


def is_throttled() -> bool:
    try:
        if os.path.isfile(THROTTLE_FILE):
            last_run = os.path.getmtime(THROTTLE_FILE)
            return (time.time() - last_run) < THROTTLE_SECONDS
    except OSError:
        pass
    return False


def touch_throttle():
    try:
        with open(THROTTLE_FILE, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def report_previous_result():
    """Print previous tsc result if available."""
    try:
        if os.path.isfile(RESULT_FILE):
            with open(RESULT_FILE, "r", encoding="utf-8") as f:
                lines = f.read().strip().splitlines()
            os.remove(RESULT_FILE)
            if lines:
                errors = [l for l in lines if "error TS" in l][:5]
                if errors:
                    print(f"[typecheck] {len(errors)} tsc error(s):", file=sys.stderr)
                    for e in errors:
                        print(f"  {e}", file=sys.stderr)
                elif lines[0].strip() == "OK":
                    print("[typecheck] tsc OK", file=sys.stderr)
    except OSError:
        pass


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only .ts/.tsx files in frontend/
    if not (file_path.endswith(".ts") or file_path.endswith(".tsx")):
        return 0
    normalized = file_path.replace("\\", "/")
    if "frontend" not in normalized:
        return 0
    skip_dirs = ["node_modules", ".git", "dist", "build", "coverage"]
    if any(f"/{d}/" in normalized for d in skip_dirs):
        return 0

    # Report previous background run result
    report_previous_result()

    # Throttle: max once per 5 minutes
    if is_throttled():
        return 0

    # Launch tsc in background via a small wrapper script
    touch_throttle()
    try:
        # Python one-liner that runs tsc and writes result to file
        bg_script = (
            f"import subprocess,os;"
            f"r=subprocess.run('npx tsc --noEmit',shell=True,capture_output=True,text=True,"
            f"cwd=r'{FRONTEND_DIR}',timeout=120);"
            f"f=open(r'{RESULT_FILE}','w',encoding='utf-8');"
            f"f.write('OK' if r.returncode==0 else r.stdout[:2000]);"
            f"f.close()"
        )
        subprocess.Popen(
            ["python", "-c", bg_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x00000008,  # DETACHED_PROCESS on Windows
        )
        print("[typecheck] tsc started (background)", file=sys.stderr)
    except (FileNotFoundError, OSError) as e:
        print(f"[typecheck] skip: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] post-edit-typecheck: {e}", file=sys.stderr)
        sys.exit(0)
