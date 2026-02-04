#!/usr/bin/env python3
"""
MCP Services Health Check Script
Version: 1.0
Description: Comprehensive health check for all MCP servers
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import socket
import subprocess
import requests
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ{Colors.RESET} {msg}")

def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a port is open and listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http_endpoint(url: str, timeout: float = 5.0) -> Tuple[bool, Optional[int], Optional[str]]:
    """Check HTTP endpoint health"""
    try:
        response = requests.get(url, timeout=timeout)
        return True, response.status_code, response.text[:100]
    except requests.exceptions.RequestException as e:
        return False, None, str(e)

def check_redis(host: str = "localhost", port: int = 6379) -> bool:
    """Check Redis connectivity"""
    try:
        import redis
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2)
        return r.ping()
    except Exception:
        return False

def check_elasticsearch(url: str = "http://localhost:9200") -> Tuple[bool, Optional[str]]:
    """Check Elasticsearch health"""
    try:
        response = requests.get(f"{url}/_cluster/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            return True, status
        return False, None
    except Exception:
        return False, None

def check_process_by_pid(pid: int) -> bool:
    """Check if process is running by PID"""
    try:
        # On Windows
        if sys.platform == 'win32':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        # On Unix-like systems
        else:
            import os
            import errno
            try:
                os.kill(pid, 0)
                return True
            except OSError as e:
                return e.errno == errno.EPERM
    except Exception:
        return False

def load_mcp_config() -> Dict:
    """Load MCP configuration from mcp.json"""
    config_path = Path(__file__).parent.parent / ".kiro" / "settings" / "mcp.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load MCP config: {e}")
        return {}

def check_docker_services() -> Dict[str, bool]:
    """Check Docker services health"""
    print_info("\n=== Docker Services Health ===\n")

    services = {
        "Redis": {"port": 6379, "check": lambda: check_redis()},
        "Elasticsearch": {"port": 9200, "check": lambda: check_elasticsearch()[0]},
        "PostgreSQL": {"port": 5432, "check": lambda: check_port("localhost", 5432)},
        "Prometheus": {"port": 9090, "check": lambda: check_port("localhost", 9090)},
    }

    results = {}
    for name, config in services.items():
        port = config["port"]
        check_func = config["check"]

        port_open = check_port("localhost", port)
        service_healthy = check_func() if port_open else False

        results[name] = service_healthy

        if service_healthy:
            print_success(f"{name} is healthy (port {port})")
        elif port_open:
            print_warning(f"{name} port {port} is open but service not responding")
        else:
            print_error(f"{name} is not running (port {port} not listening)")

    return results

def check_mcp_servers() -> Dict[str, Dict]:
    """Check MCP servers health"""
    print_info("\n=== MCP Servers Health ===\n")

    pid_dir = Path(__file__).parent.parent / ".mcp_pids"

    if not pid_dir.exists():
        print_warning("MCP PID directory not found. Services may not be started.")
        return {}

    results = {}
    pid_files = list(pid_dir.glob("*.pid"))

    if not pid_files:
        print_warning("No MCP service PID files found.")
        return {}

    for pid_file in pid_files:
        service_name = pid_file.stem

        try:
            pid = int(pid_file.read_text().strip())
            is_running = check_process_by_pid(pid)

            results[service_name] = {
                "pid": pid,
                "running": is_running,
                "pid_file": str(pid_file)
            }

            if is_running:
                print_success(f"{service_name} is running (PID: {pid})")
            else:
                print_error(f"{service_name} is NOT running (stale PID: {pid})")

        except Exception as e:
            print_error(f"{service_name}: Error reading PID file - {e}")
            results[service_name] = {
                "pid": None,
                "running": False,
                "error": str(e)
            }

    return results

def check_specific_ports() -> Dict[str, bool]:
    """Check specific service ports"""
    print_info("\n=== Service Ports Check ===\n")

    ports = {
        "Zemberek NLP (8081)": 8081,
        "Blackboard WS (8765)": 8765,
        "Prometheus Metrics (9091)": 9091,
    }

    results = {}
    for name, port in ports.items():
        is_open = check_port("localhost", port)
        results[name] = is_open

        if is_open:
            print_success(f"{name} is listening")
        else:
            print_warning(f"{name} is NOT listening")

    return results

def check_log_files() -> Dict[str, Dict]:
    """Check MCP log files for recent errors"""
    print_info("\n=== Recent Log Errors ===\n")

    log_dir = Path(__file__).parent.parent / "logs"

    if not log_dir.exists():
        print_warning("Log directory not found.")
        return {}

    results = {}
    log_files = list(log_dir.glob("*.log"))

    for log_file in log_files:
        service_name = log_file.stem

        try:
            # Read last 50 lines
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines

            # Count errors
            error_count = sum(1 for line in recent_lines if any(
                keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'traceback']
            ))

            results[service_name] = {
                "total_lines": len(lines),
                "recent_errors": error_count,
                "path": str(log_file)
            }

            if error_count == 0:
                print_success(f"{service_name}: No recent errors")
            elif error_count < 5:
                print_warning(f"{service_name}: {error_count} recent errors")
            else:
                print_error(f"{service_name}: {error_count} recent errors (check logs)")

        except Exception as e:
            print_error(f"{service_name}: Error reading log - {e}")

    return results

def generate_health_report(
    docker_health: Dict,
    mcp_health: Dict,
    port_health: Dict,
    log_health: Dict
) -> Dict:
    """Generate comprehensive health report"""

    docker_healthy = sum(1 for v in docker_health.values() if v)
    docker_total = len(docker_health)

    mcp_healthy = sum(1 for v in mcp_health.values() if v.get('running', False))
    mcp_total = len(mcp_health)

    port_healthy = sum(1 for v in port_health.values() if v)
    port_total = len(port_health)

    total_services = docker_total + mcp_total
    total_healthy = docker_healthy + mcp_healthy

    health_score = (total_healthy / total_services * 100) if total_services > 0 else 0

    return {
        "timestamp": datetime.now().isoformat(),
        "health_score": round(health_score, 2),
        "docker_services": {
            "healthy": docker_healthy,
            "total": docker_total,
            "details": docker_health
        },
        "mcp_servers": {
            "healthy": mcp_healthy,
            "total": mcp_total,
            "details": mcp_health
        },
        "service_ports": {
            "listening": port_healthy,
            "total": port_total,
            "details": port_health
        },
        "log_analysis": log_health
    }

def main():
    """Main health check function"""
    print(f"\n{Colors.BOLD}=== MCP Services Health Check ==={Colors.RESET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check Docker services
    docker_health = check_docker_services()

    # Check MCP servers
    mcp_health = check_mcp_servers()

    # Check specific ports
    port_health = check_specific_ports()

    # Check log files
    log_health = check_log_files()

    # Generate report
    report = generate_health_report(docker_health, mcp_health, port_health, log_health)

    # Print summary
    print_info(f"\n{Colors.BOLD}=== Health Summary ==={Colors.RESET}\n")
    print(f"Overall Health Score: {Colors.BOLD}{report['health_score']:.1f}%{Colors.RESET}")
    print(f"Docker Services: {report['docker_services']['healthy']}/{report['docker_services']['total']} healthy")
    print(f"MCP Servers: {report['mcp_servers']['healthy']}/{report['mcp_servers']['total']} running")
    print(f"Service Ports: {report['service_ports']['listening']}/{report['service_ports']['total']} listening")

    # Save report
    report_path = Path(__file__).parent.parent / "reports" / "health"
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    latest_file = report_path / "latest.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nHealth report saved to: {report_file}")

    # Exit code based on health score
    if report['health_score'] >= 80:
        print_success("\nSystem is healthy!")
        return 0
    elif report['health_score'] >= 50:
        print_warning("\nSystem has some issues. Check failed services.")
        return 1
    else:
        print_error("\nSystem is unhealthy! Multiple services are down.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
