"""
Simple Dashboard for Token Usage and A/B Test Metrics
Access at http://localhost:8090

Usage: python dashboard.py
"""

from flask import Flask, jsonify, render_template_string
from backend.monitoring.token_usage_tracker import get_tracker
from backend.services.ab_testing import get_ab_test_manager

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>KIRO Token Optimization Dashboard</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .metric-card {
            display: inline-block;
            background: #f9f9f9;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            min-width: 200px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .refresh-btn {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .refresh-btn:hover { background: #45a049; }
    </style>
    <script>
        function refreshData() {
            fetch('/api/token-stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-requests').textContent = data.total_requests;
                    document.getElementById('total-saved').textContent = data.total_tokens_saved;
                    document.getElementById('avg-savings').textContent = data.average_savings_percentage.toFixed(1) + '%';
                    document.getElementById('cost-saved').textContent = '$' + data.total_cost_saved_usd.toFixed(4);
                });

            fetch('/api/token-report')
                .then(r => r.text())
                .then(text => {
                    document.getElementById('token-report').textContent = text;
                });

            fetch('/api/ab-report')
                .then(r => r.text())
                .then(text => {
                    document.getElementById('ab-report').textContent = text;
                });
        }

        setInterval(refreshData, 30000); // Auto-refresh every 30 seconds
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <h1>🎯 KIRO Token Optimization Dashboard</h1>
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>

        <h2>📊 Current Metrics</h2>
        <div class="metric-card">
            <div class="metric-label">Total Requests</div>
            <div class="metric-value" id="total-requests">-</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Tokens Saved</div>
            <div class="metric-value" id="total-saved">-</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Average Savings</div>
            <div class="metric-value" id="avg-savings">-</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Cost Saved</div>
            <div class="metric-value" id="cost-saved">-</div>
        </div>

        <h2>📈 Token Usage Report (Last 7 Days)</h2>
        <pre id="token-report">Loading...</pre>

        <h2>🧪 A/B Test Results (Last 7 Days)</h2>
        <pre id="ab-report">Loading...</pre>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/token-stats')
def token_stats():
    tracker = get_tracker()
    stats = tracker.get_stats()
    return jsonify(stats)

@app.route('/api/token-report')
def token_report():
    tracker = get_tracker()
    report = tracker.generate_report(days=7)
    return report

@app.route('/api/ab-report')
def ab_report():
    manager = get_ab_test_manager()
    report = manager.generate_report(days=7)
    return report

@app.route('/api/projection')
def projection():
    tracker = get_tracker()
    proj = tracker.get_monthly_projection()
    return jsonify(proj)

if __name__ == '__main__':
    print("="*60)
    print("KIRO Token Optimization Dashboard")
    print("="*60)
    print()
    print("Dashboard running at: http://localhost:8090")
    print("Press Ctrl+C to stop")
    print()

    app.run(host='0.0.0.0', port=8090, debug=False)
