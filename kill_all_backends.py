"""
Kill all backend processes
"""
import subprocess
import time

print("=" * 70)
print("KILLING ALL BACKEND PROCESSES")
print("=" * 70)

# Kill all python.exe processes
result = subprocess.run(
    ['taskkill', '/F', '/IM', 'python.exe'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(result.stdout)
    print("[OK] All Python processes killed")
else:
    print("[INFO] No Python processes found or already killed")

# Wait for cleanup
print("Waiting 3 seconds for cleanup...")
time.sleep(3)

# Check port 8000
print("\nChecking port 8000...")
port_check = subprocess.run(
    ['netstat', '-ano'],
    capture_output=True,
    text=True
)

port_8000_in_use = False
for line in port_check.stdout.split('\n'):
    if ':8000' in line and 'LISTENING' in line:
        port_8000_in_use = True
        print(f"[WARNING] Port 8000 still in use: {line.strip()}")

if not port_8000_in_use:
    print("[OK] Port 8000 is FREE - ready to start backend!")

print("\n" + "=" * 70)
print("CLEANUP COMPLETE")
print("=" * 70)
