#!/usr/bin/env python3
"""
Interactive Coverage Dashboard
Real-time coverage monitoring with web interface
"""

import sqlite3
import threading
import webbrowser
from dataclasses import asdict
from typing import Any

try:
    from flask import Flask, jsonify, render_template_string, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from automated_coverage_reporter import CoverageDatabase, CoverageMetrics


class CoverageDashboard:
    """Interactive coverage dashboard with web interface"""

    def __init__(self, db_path: str = "coverage_reports/coverage_history.db"):
        self.db = CoverageDatabase(db_path)
        self.app = None
        if FLASK_AVAILABLE:
            self.setup_flask_app()

    def setup_flask_app(self):
        """Setup Flask web application"""
        self.app = Flask(__name__)
        self.app.secret_key = "coverage_dashboard_secret"

        @self.app.route("/")
        def dashboard():
            return render_template_string(self.get_dashboard_template())

        @self.app.route("/api/coverage/current")
        def current_coverage():
            latest = self.get_latest_coverage()
            return jsonify(asdict(latest) if latest else {})

        @self.app.route("/api/coverage/trend")
        def coverage_trend():
            days = request.args.get("days", 30, type=int)
            trend_data = self.get_coverage_trend_data(days)
            return jsonify(trend_data)

        @self.app.route("/api/coverage/modules")
        def module_coverage():
            modules = self.get_module_coverage_data()
            return jsonify(modules)

        @self.app.route("/api/coverage/stats")
        def coverage_stats():
            stats = self.get_coverage_statistics()
            return jsonify(stats)

    def get_dashboard_template(self) -> str:
        """Get HTML template for dashboard"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Dashboard - Turkish Education Platform</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .metric-label {
            color: #7f8c8d;
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .coverage-high { color: #27ae60; }
        .coverage-medium { color: #f39c12; }
        .coverage-low { color: #e74c3c; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        .chart-title {
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
        }
        
        .modules-table {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .modules-table h3 {
            background: #34495e;
            color: white;
            padding: 20px;
            margin: 0;
            text-align: center;
        }
        
        .table-container {
            max-height: 400px;
            overflow-y: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
            position: sticky;
            top: 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .auto-refresh {
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #2980b9;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #27ae60; }
        .status-updating { background: #f39c12; }
        .status-offline { background: #e74c3c; }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Coverage Dashboard</h1>
            <p>Turkish Education Platform - Test Coverage Monitoring</p>
        </div>
        
        <div class="auto-refresh">
            <span class="status-indicator status-online"></span>
            <span>Auto-refresh: <span id="status">Active</span></span>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Now</button>
            <span id="last-update" style="margin-left: 20px; color: #7f8c8d;"></span>
        </div>
        
        <div class="metrics-grid" id="metrics-grid">
            <!-- Metrics will be populated here -->
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h3 class="chart-title">📈 Coverage Trend (30 Days)</h3>
                <canvas id="trendChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">🧪 Test Results Distribution</h3>
                <canvas id="testChart"></canvas>
            </div>
        </div>
        
        <div class="modules-table">
            <h3>📦 Module Coverage Details</h3>
            <div class="table-container">
                <table id="modules-table">
                    <thead>
                        <tr>
                            <th>Module</th>
                            <th>Coverage</th>
                            <th>Statements</th>
                            <th>Missing</th>
                            <th>Progress</th>
                        </tr>
                    </thead>
                    <tbody id="modules-tbody">
                        <!-- Module data will be populated here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let trendChart = null;
        let testChart = null;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        });
        
        function initializeCharts() {
            // Trend Chart
            const trendCtx = document.getElementById('trendChart').getContext('2d');
            trendChart = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Coverage %',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
            
            // Test Results Chart
            const testCtx = document.getElementById('testChart').getContext('2d');
            testChart = new Chart(testCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Passed', 'Failed', 'Skipped'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            '#27ae60',
                            '#e74c3c',
                            '#f39c12'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        async function refreshData() {
            try {
                document.getElementById('status').textContent = 'Updating...';
                document.querySelector('.status-indicator').className = 'status-indicator status-updating';
                
                // Fetch current coverage
                const currentResponse = await fetch('/api/coverage/current');
                const currentData = await currentResponse.json();
                
                // Fetch trend data
                const trendResponse = await fetch('/api/coverage/trend?days=30');
                const trendData = await trendResponse.json();
                
                // Fetch module data
                const modulesResponse = await fetch('/api/coverage/modules');
                const modulesData = await modulesResponse.json();
                
                // Update UI
                updateMetrics(currentData);
                updateTrendChart(trendData);
                updateTestChart(currentData);
                updateModulesTable(modulesData);
                
                document.getElementById('status').textContent = 'Active';
                document.querySelector('.status-indicator').className = 'status-indicator status-online';
                document.getElementById('last-update').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Failed to refresh data:', error);
                document.getElementById('status').textContent = 'Error';
                document.querySelector('.status-indicator').className = 'status-indicator status-offline';
            }
        }
        
        function updateMetrics(data) {
            const metricsGrid = document.getElementById('metrics-grid');
            
            const coverage = data.coverage_percentage || 0;
            const coverageClass = coverage >= 80 ? 'coverage-high' : coverage >= 50 ? 'coverage-medium' : 'coverage-low';
            
            metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value ${coverageClass}">${coverage.toFixed(1)}%</div>
                    <div class="metric-label">Overall Coverage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.test_count || 0}</div>
                    <div class="metric-label">Total Tests</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.covered_lines || 0}</div>
                    <div class="metric-label">Covered Lines</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(data.test_duration || 0).toFixed(1)}s</div>
                    <div class="metric-label">Test Duration</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(data.branch_coverage || 0).toFixed(1)}%</div>
                    <div class="metric-label">Branch Coverage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.missing_lines || 0}</div>
                    <div class="metric-label">Missing Lines</div>
                </div>
            `;
        }
        
        function updateTrendChart(data) {
            if (data.trend && data.trend.length > 0) {
                trendChart.data.labels = data.trend.map(item => 
                    new Date(item.timestamp).toLocaleDateString()
                );
                trendChart.data.datasets[0].data = data.trend.map(item => 
                    item.coverage_percentage
                );
                trendChart.update();
            }
        }
        
        function updateTestChart(data) {
            const passed = data.test_count - (data.failed_tests || 0) - (data.skipped_tests || 0);
            testChart.data.datasets[0].data = [
                passed,
                data.failed_tests || 0,
                data.skipped_tests || 0
            ];
            testChart.update();
        }
        
        function updateModulesTable(modules) {
            const tbody = document.getElementById('modules-tbody');
            
            if (!modules || modules.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #7f8c8d;">No module data available</td></tr>';
                return;
            }
            
            tbody.innerHTML = modules.map(module => {
                const coverage = module.coverage || 0;
                const coverageClass = coverage >= 80 ? 'coverage-high' : coverage >= 50 ? 'coverage-medium' : 'coverage-low';
                
                return `
                    <tr>
                        <td>${module.name}</td>
                        <td class="${coverageClass}">${coverage.toFixed(1)}%</td>
                        <td>${module.statements || 0}</td>
                        <td>${module.missing || 0}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill ${coverageClass}" style="width: ${coverage}%"></div>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    </script>
</body>
</html>
        """

    def get_latest_coverage(self) -> CoverageMetrics | None:
        """Get latest coverage metrics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT timestamp, total_lines, covered_lines, coverage_percentage,
                           missing_lines, branch_coverage, function_coverage, class_coverage,
                           test_count, test_duration, failed_tests, skipped_tests
                    FROM coverage_runs 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                )

                row = cursor.fetchone()
                if row:
                    return CoverageMetrics(*row)

        except Exception as e:
            print(f"Error getting latest coverage: {e}")

        return None

    def get_coverage_trend_data(self, days: int = 30) -> dict[str, Any]:
        """Get coverage trend data for API"""
        try:
            trend_data = self.db.get_coverage_trend(days)

            return {
                "trend": [asdict(metrics) for metrics in trend_data],
                "summary": {
                    "total_runs": len(trend_data),
                    "date_range": days,
                    "latest_coverage": trend_data[-1].coverage_percentage
                    if trend_data
                    else 0,
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def get_module_coverage_data(self) -> list[dict[str, Any]]:
        """Get module coverage data"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Get latest run ID
                cursor.execute(
                    "SELECT id FROM coverage_runs ORDER BY timestamp DESC LIMIT 1"
                )
                latest_run = cursor.fetchone()

                if not latest_run:
                    return []

                run_id = latest_run[0]

                # Get module coverage for latest run
                cursor.execute(
                    """
                    SELECT module_name, statements, missing, coverage,
                           branches, partial_branches, branch_coverage
                    FROM module_coverage 
                    WHERE run_id = ?
                    ORDER BY coverage DESC
                """,
                    (run_id,),
                )

                modules = []
                for row in cursor.fetchall():
                    modules.append(
                        {
                            "name": row[0],
                            "statements": row[1],
                            "missing": row[2],
                            "coverage": row[3],
                            "branches": row[4],
                            "partial_branches": row[5],
                            "branch_coverage": row[6],
                        }
                    )

                return modules

        except Exception as e:
            print(f"Error getting module coverage: {e}")
            return []

    def get_coverage_statistics(self) -> dict[str, Any]:
        """Get coverage statistics"""
        try:
            recent_data = self.db.get_coverage_trend(days=7)

            if not recent_data:
                return {}

            coverages = [run.coverage_percentage for run in recent_data]

            return {
                "average_coverage": sum(coverages) / len(coverages),
                "min_coverage": min(coverages),
                "max_coverage": max(coverages),
                "coverage_variance": max(coverages) - min(coverages),
                "total_runs": len(recent_data),
                "trend": "improving" if coverages[-1] > coverages[0] else "declining",
            }

        except Exception as e:
            return {"error": str(e)}

    def run_dashboard(
        self, host: str = "localhost", port: int = 5000, debug: bool = False
    ):
        """Run the coverage dashboard"""
        if not FLASK_AVAILABLE:
            print("Flask not available. Install with: pip install flask")
            return

        if not self.app:
            print("Dashboard not properly initialized")
            return

        print("\n🎯 Coverage Dashboard Starting...")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print("🔄 Auto-refresh: Enabled (30s interval)")
        print("📈 Real-time monitoring: Active")

        # Auto-open browser
        if not debug:
            threading.Timer(
                1.0, lambda: webbrowser.open(f"http://{host}:{port}")
            ).start()

        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")


def main():
    """Main entry point for dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage Dashboard")
    parser.add_argument(
        "--db-path",
        default="coverage_reports/coverage_history.db",
        help="Path to coverage database",
    )
    parser.add_argument("--host", default="localhost", help="Dashboard host")
    parser.add_argument("--port", default=5000, type=int, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    dashboard = CoverageDashboard(args.db_path)
    dashboard.run_dashboard(args.host, args.port, args.debug)


if __name__ == "__main__":
    main()
