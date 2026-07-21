import subprocess

import psycopg2


def get_time_wait():
    # Use powershell
    try:
        cmd = 'netstat -anp tcp | findstr TIME_WAIT'
        output = subprocess.check_output(['powershell', '-Command', f'@({cmd}).Count'])
        return int(output.decode().strip())
    except Exception as e:
        print(f"Error getting TIME_WAIT: {e}")
        return -1

def get_pg_activity():
    try:
        conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5434/kiro2')
        cur = conn.cursor()
        cur.execute("SELECT pid, usename, state, wait_event_type, wait_event, query FROM pg_stat_activity WHERE wait_event_type IS NOT NULL AND state = 'active';")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        return str(e)

def apply_registry_fix():
    print("Applying registry fix for TcpTimedWaitDelay and MaxUserPort...")
    try:
        subprocess.check_call(['powershell', '-Command', 'Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v TcpTimedWaitDelay /t REG_DWORD /d 30 /f; reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v MaxUserPort /t REG_DWORD /d 65534 /f`"" -Verb RunAs'])
        print("Registry fix applied successfully (requires reboot to take full effect).")
    except Exception as e:
        print(f"Failed to apply registry fix: {e}")

if __name__ == "__main__":
    count = get_time_wait()
    print(f"TIME_WAIT Count: {count}")

    if count > 4000:
        apply_registry_fix()

    activity = get_pg_activity()
    print("Postgres Blocked/Waiting Queries:")
    if isinstance(activity, list):
        if not activity:
            print("  None")
        for row in activity:
            print(f"  {row}")
    else:
        print(f"  Error: {activity}")
