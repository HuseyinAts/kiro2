# Quick Start - WebSocket Load Testing

## 🚀 Fastest Way to Start

### Option 1: Pytest Smoke Test (30 seconds)
```bash
cd backend
pytest tests/load/test_websocket_load.py -v
```

### Option 2: Locust Web UI (Interactive)
```bash
cd backend/tests/load
locust -f locustfile_websocket.py --host http://localhost:8000
# Then open browser: http://localhost:8089
```

### Option 3: Automated Script
```bash
# Unix/Linux/Mac
cd backend/tests/load
./run_websocket_load_test.sh smoke

# Windows
cd backend\tests\load
run_websocket_load_test.bat smoke
```

## 📊 Quick Test Modes

| Mode | Users | Duration | Use Case |
|------|-------|----------|----------|
| `smoke` | 50 | 2min | CI/CD quick check |
| `dev` | 100 | 5min | Development testing |
| `staging` | 500 | 10min | Pre-production |
| `production` | 1000 | 15min | Full load test |
| `stress` | 5000 | 30min | Stress test |

## ⚡ One-Liners

```bash
# CI/CD
pytest tests/load/test_websocket_load.py -v

# Development
./run_websocket_load_test.sh dev

# Production (headless)
locust -f locustfile_websocket.py --users 1000 --spawn-rate 50 --run-time 10m --host http://localhost:8000 --headless --csv=results/ws_prod

# Custom
./run_websocket_load_test.sh custom 2000 100 20m
```

## ✅ Prerequisites

1. **Backend running:**
   ```bash
   cd backend && uvicorn main:app --reload --port 8000
   ```

2. **Locust installed:**
   ```bash
   pip install locust==2.41.5
   ```

3. **Health check works:**
   ```bash
   curl http://localhost:8000/health
   ```

## 📈 What to Expect

**Console output will show:**
- Total requests and failures
- Success rate (should be > 95%)
- Response times (P50, P95, P99)
- Requests per second
- ✅/❌ Requirement validation

**Result files (in `results/`):**
- `*_stats.csv` - Request statistics
- `*.html` - HTML report with charts
- `*.log` - Detailed logs

## 🎯 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| HTTP P95 | < 500ms | ✅ Auto-checked |
| WS Connection | < 2000ms | ✅ Auto-checked |
| Message Latency | < 100ms | ✅ Auto-checked |
| Success Rate | > 95% | ✅ Auto-checked |

## 🔧 Troubleshooting

**Backend not running?**
```bash
cd backend && uvicorn main:app --reload --port 8000
```

**Port conflict?**
```bash
export KIRO2_HOST=http://localhost:8001  # Unix
set KIRO2_HOST=http://localhost:8001     # Windows
```

**Too many errors?**
- Reduce spawn rate: `--spawn-rate 10`
- Reduce users: `--users 50`
- Check backend logs

## 📚 Full Documentation

See: `README_WEBSOCKET_LOAD_TESTS.md`

---

**TL;DR:**
```bash
# Just run this:
pytest tests/load/test_websocket_load.py -v
```
