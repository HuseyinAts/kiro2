#!/usr/bin/env python3
"""
Test Monitoring Setup
Video API Monitoring - Task 19

Bu script monitoring stack'in doğru çalıştığını test eder.
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

# Service endpoints
SERVICES = {
    'Prometheus': 'http://localhost:9090/-/healthy',
    'Alertmanager': 'http://localhost:9093/-/healthy',
    'Grafana': 'http://localhost:3000/api/health',
    'Prometheus Exporter': 'http://localhost:9091/metrics',
    'Redis': 'http://localhost:6379',  # Will use redis-cli instead
}

# Prometheus queries to test
TEST_QUERIES = [
    ('Video API Request Rate', 'rate(kiro_api_requests_total{endpoint="/api/youtube/recommendations"}[5m])'),
    ('Cache Hit Rate', 'rate(kiro_cache_hits_total[5m])'),
    ('Health Check Status', 'health_check_overall_status'),
    ('Component Health', 'health_check_component_status'),
]


def check_service_health(name: str, url: str) -> Tuple[bool, str]:
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, "✅ Healthy"
        else:
            return False, f"❌ Unhealthy (Status: {response.status_code})"
    except requests.exceptions.ConnectionError:
        return False, "❌ Connection refused (Service not running?)"
    except requests.exceptions.Timeout:
        return False, "❌ Timeout"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def check_prometheus_metrics() -> Tuple[bool, str]:
    """Check if Prometheus is collecting metrics"""
    try:
        url = 'http://localhost:9090/api/v1/query'
        params = {'query': 'up'}
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                results = data['data']['result']
                if results:
                    return True, f"✅ Collecting metrics ({len(results)} targets)"
                else:
                    return False, "❌ No metrics found"
            else:
                return False, f"❌ Query failed: {data.get('error', 'Unknown error')}"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def check_prometheus_targets() -> Tuple[bool, str]:
    """Check Prometheus scrape targets"""
    try:
        url = 'http://localhost:9090/api/v1/targets'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                targets = data['data']['activeTargets']
                up_count = sum(1 for t in targets if t['health'] == 'up')
                total_count = len(targets)
                
                if up_count == total_count:
                    return True, f"✅ All targets up ({up_count}/{total_count})"
                else:
                    return False, f"⚠️  Some targets down ({up_count}/{total_count})"
            else:
                return False, "❌ Failed to get targets"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def check_alertmanager_alerts() -> Tuple[bool, str]:
    """Check Alertmanager alerts"""
    try:
        url = 'http://localhost:9093/api/v1/alerts'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                alerts = data['data']
                firing_count = sum(1 for a in alerts if a['status']['state'] == 'firing')
                
                if firing_count == 0:
                    return True, f"✅ No firing alerts ({len(alerts)} total)"
                else:
                    return False, f"⚠️  {firing_count} alerts firing"
            else:
                return False, "❌ Failed to get alerts"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def check_grafana_datasources() -> Tuple[bool, str]:
    """Check Grafana datasources"""
    try:
        url = 'http://localhost:3000/api/datasources'
        auth = ('admin', 'admin')
        response = requests.get(url, auth=auth, timeout=5)
        
        if response.status_code == 200:
            datasources = response.json()
            prometheus_ds = [ds for ds in datasources if ds['type'] == 'prometheus']
            
            if prometheus_ds:
                return True, f"✅ Prometheus datasource configured"
            else:
                return False, "❌ No Prometheus datasource found"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def test_video_api_metrics() -> Tuple[bool, str]:
    """Test video API specific metrics"""
    try:
        url = 'http://localhost:9091/metrics'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            metrics_text = response.text
            
            # Check for key metrics
            required_metrics = [
                'kiro_video_recommendations_total',
                'kiro_api_requests_total',
                'kiro_cache_hits_total',
                'kiro_turkish_content_filter_score',
            ]
            
            found_metrics = [m for m in required_metrics if m in metrics_text]
            
            if len(found_metrics) == len(required_metrics):
                return True, f"✅ All video metrics present ({len(found_metrics)}/{len(required_metrics)})"
            else:
                missing = set(required_metrics) - set(found_metrics)
                return False, f"⚠️  Missing metrics: {', '.join(missing)}"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def main():
    """Run all monitoring tests"""
    print("=" * 60)
    print("Teknofest Video API Monitoring - Health Check")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Test 1: Service Health
    print("📊 Testing Service Health...")
    print("-" * 60)
    for service_name, url in SERVICES.items():
        if service_name == 'Redis':
            # Skip Redis HTTP check (use redis-cli instead)
            print(f"{service_name:25} ⏭️  Skipped (use redis-cli ping)")
            continue
        
        passed, message = check_service_health(service_name, url)
        print(f"{service_name:25} {message}")
        if not passed:
            all_passed = False
    print()
    
    # Test 2: Prometheus Metrics
    print("📈 Testing Prometheus Metrics...")
    print("-" * 60)
    passed, message = check_prometheus_metrics()
    print(f"{'Metrics Collection':25} {message}")
    if not passed:
        all_passed = False
    
    passed, message = check_prometheus_targets()
    print(f"{'Scrape Targets':25} {message}")
    if not passed:
        all_passed = False
    print()
    
    # Test 3: Alertmanager
    print("🔔 Testing Alertmanager...")
    print("-" * 60)
    passed, message = check_alertmanager_alerts()
    print(f"{'Alert Status':25} {message}")
    if not passed:
        all_passed = False
    print()
    
    # Test 4: Grafana
    print("📊 Testing Grafana...")
    print("-" * 60)
    passed, message = check_grafana_datasources()
    print(f"{'Datasources':25} {message}")
    if not passed:
        all_passed = False
    print()
    
    # Test 5: Video API Metrics
    print("🎥 Testing Video API Metrics...")
    print("-" * 60)
    passed, message = test_video_api_metrics()
    print(f"{'Video Metrics':25} {message}")
    if not passed:
        all_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Monitoring stack is healthy.")
        print()
        print("Next steps:")
        print("  1. Open Grafana: http://localhost:3000")
        print("  2. Import video dashboard: backend/config/grafana_video_dashboard.json")
        print("  3. Configure Slack webhook in .env")
        print("  4. Start backend to generate metrics")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        print()
        print("Troubleshooting:")
        print("  1. Check if all containers are running:")
        print("     docker-compose -f docker-compose.monitoring.yml ps")
        print("  2. Check container logs:")
        print("     docker-compose -f docker-compose.monitoring.yml logs")
        print("  3. Restart monitoring stack:")
        print("     ./scripts/start_monitoring.sh")
        return 1


if __name__ == '__main__':
    sys.exit(main())
