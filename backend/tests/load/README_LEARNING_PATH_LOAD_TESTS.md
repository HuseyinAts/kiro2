# Learning Path Load Testing Guide

**P1.3 Implementation**: Comprehensive load testing for Learning Path API
**Date**: 2025-01-04
**Tool**: Locust (Python-based load testing framework)

---

## 🎯 Purpose

Test Learning Path system performance under various load conditions:
- ✅ Validate API can handle 100+ concurrent users
- ✅ Measure response times (P50, P95, P99)
- ✅ Identify performance bottlenecks
- ✅ Test cache effectiveness
- ✅ Verify system stability under load

---

## 📋 Prerequisites

### 1. Install Locust
```bash
pip install locust>=2.20.0
```

### 2. Ensure Backend is Running
```bash
# From backend directory
py -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 3. Optional: Start Infrastructure
```bash
# PostgreSQL and Redis (improves performance)
docker-compose up -d postgres redis
```

---

## 🚀 Quick Start

### Run with Web UI (Recommended for first-time)
```bash
cd backend/tests/load
locust -f locustfile_learning_path.py --host=http://localhost:8001
```

Then open: http://localhost:8089

**In the web UI**:
- Number of users: `50`
- Spawn rate: `5` (users/second)
- Host: `http://localhost:8001`
- Click "Start swarming"

### Run Headless (CLI mode)
```bash
cd backend/tests/load
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=50 --spawn-rate=5 --run-time=5m --headless
```

---

## 📊 Test Scenarios

### 1. Smoke Test (Quick Validation)
**Purpose**: Quick sanity check (1 minute)
**Users**: 5 concurrent users
**Duration**: 1 minute

```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=5 --spawn-rate=1 --run-time=1m --headless
```

**Expected Results**:
- Success Rate: > 99%
- P95 Response Time: < 2000ms
- No errors

---

### 2. Normal Load Test
**Purpose**: Simulate typical production load
**Users**: 50 concurrent users
**Duration**: 5 minutes

```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=50 --spawn-rate=5 --run-time=5m --headless
```

**Expected Results**:
- Success Rate: > 95%
- P50 Response Time (search): < 1500ms
- P95 Response Time (search): < 3000ms
- Throughput: > 50 requests/sec

---

### 3. Peak Load Test
**Purpose**: Test system at peak usage (e.g., exam period)
**Users**: 100 concurrent users
**Duration**: 10 minutes

```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=100 --spawn-rate=10 --run-time=10m --headless
```

**Expected Results**:
- Success Rate: > 95%
- P95 Response Time (search): < 5000ms
- P95 Response Time (create-path): < 8000ms
- Throughput: > 100 requests/sec

---

### 4. Stress Test
**Purpose**: Find system breaking point
**Users**: 200 concurrent users (aggressive)
**Duration**: 5 minutes

```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --user-classes=StressTestUser --users=200 --spawn-rate=20 \
       --run-time=5m --headless
```

**Expected Behavior**:
- System may show increased error rates
- Response times will increase
- Goal: Identify maximum capacity

---

### 5. Spike Test
**Purpose**: Test system resilience to sudden traffic spikes
**Users**: 500 concurrent users (burst)
**Duration**: 2 minutes

```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --user-classes=SpikeTestUser --users=500 --spawn-rate=100 \
       --run-time=2m --headless
```

**Expected Behavior**:
- Initial spike may cause errors
- System should recover and stabilize
- Circuit breakers may activate (if P1.4 implemented)

---

## 📈 Generating Reports

### HTML Report
```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=50 --spawn-rate=5 --run-time=5m --headless \
       --html=report_learning_path_$(date +%Y%m%d_%H%M%S).html
```

### CSV Reports
```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 \
       --users=50 --spawn-rate=5 --run-time=5m --headless \
       --csv=results_learning_path
```

This generates:
- `results_learning_path_stats.csv` - Request statistics
- `results_learning_path_stats_history.csv` - Time-series data
- `results_learning_path_failures.csv` - Failed requests

---

## 🎭 User Behavior Simulation

### LearningPathUser (Default)
Simulates realistic student behavior:
- **70%**: Resource search (most common)
- **20%**: Learning path creation
- **10%**: Quiz submission + completion updates

**Wait Time**: 1-3 seconds between actions (realistic think time)

### StressTestUser
Aggressive testing mode:
- Minimal wait time (0-0.1 seconds)
- High request rate
- Tests system limits

### SpikeTestUser
Sudden traffic burst:
- Very short wait time (0.1-0.5 seconds)
- Simulates viral traffic or exam rush

---

## 📊 Understanding Results

### Key Metrics

#### 1. **Success Rate**
```
Success Rate = (Total Requests - Failed Requests) / Total Requests * 100%
```
**Target**: > 95%

#### 2. **Response Time Percentiles**
- **P50 (Median)**: 50% of requests faster than this
- **P95**: 95% of requests faster than this
- **P99**: 99% of requests faster than this

**Targets**:
- P50 (search): < 1500ms
- P95 (search): < 3000ms
- P95 (create-path): < 5000ms

#### 3. **Throughput (RPS)**
Requests per second the system can handle.
**Target**: > 100 RPS at 100 users

#### 4. **Error Rate**
```
Error Rate = Failed Requests / Total Requests * 100%
```
**Target**: < 5%

---

## 🔍 Analyzing Performance Issues

### High Response Times

**Symptoms**:
- P95 > 5000ms for searches
- P95 > 10000ms for path creation

**Possible Causes**:
1. **Database queries not optimized**
   - Check query execution plans
   - Add missing indexes
   - Use query caching

2. **External API calls (YouTube) slow**
   - Check YouTube API rate limits
   - Verify cache is working
   - Consider timeout adjustments

3. **AI agent processing slow**
   - Check LLM API latency
   - Monitor agent queue depth
   - Consider parallel processing

### High Error Rates

**Symptoms**:
- Error rate > 5%
- HTTP 500 errors

**Possible Causes**:
1. **Resource exhaustion**
   - Database connection pool full
   - Redis connection limits
   - Memory issues

2. **API rate limits**
   - YouTube API quota exceeded
   - LLM API rate limiting

3. **Uncaught exceptions**
   - Check server logs
   - Review error traces

### Low Throughput

**Symptoms**:
- RPS < 50 at 100 users
- System not fully utilized

**Possible Causes**:
1. **Synchronous operations blocking**
   - Use async/await properly
   - Avoid blocking I/O

2. **Single-threaded bottleneck**
   - Increase worker processes
   - Use Uvicorn workers

3. **Database connection bottleneck**
   - Increase connection pool size
   - Use connection pooling

---

## 🔧 Prometheus Integration

Load tests automatically record metrics via existing Prometheus instrumentation:

```promql
# Monitor during load test
rate(learning_path_creation_total[1m])
histogram_quantile(0.95, rate(learning_path_creation_duration_seconds_bucket[1m]))
rate(learning_path_api_requests_total{status="error"}[1m])
```

**Grafana Dashboard**: View real-time metrics during load test (if P1.10 implemented)

---

## 📝 Best Practices

### Before Running Load Tests

1. **Baseline Metrics**: Run smoke test first to establish baseline
2. **Monitor Resources**: Open `htop`/Task Manager to watch CPU/memory
3. **Check Logs**: Tail server logs to catch errors immediately
4. **Prometheus Ready**: Ensure Prometheus is scraping metrics

### During Load Tests

1. **Monitor Continuously**: Watch web UI or logs
2. **Check Prometheus**: Verify metrics are being recorded
3. **Resource Usage**: Watch for CPU/memory spikes
4. **Error Logs**: Monitor for exceptions

### After Load Tests

1. **Review HTML Report**: Analyze detailed statistics
2. **Check Metrics**: Query Prometheus for historical data
3. **Identify Bottlenecks**: Find slowest endpoints
4. **Document Findings**: Record results and action items

---

## 🎯 Performance Targets Summary

| Metric | Target | Notes |
|--------|--------|-------|
| **Success Rate** | > 95% | At 100 concurrent users |
| **P50 (search)** | < 1500ms | Resource search endpoint |
| **P95 (search)** | < 3000ms | 95th percentile |
| **P95 (create-path)** | < 5000ms | AI agent processing |
| **Throughput** | > 100 RPS | Requests per second |
| **Error Rate** | < 5% | Failed requests |

---

## 🐛 Troubleshooting

### "Connection refused" error
**Solution**: Ensure backend is running on port 8001
```bash
py -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### "Too many open files" error
**Solution**: Increase file descriptor limit
```bash
# Linux/Mac
ulimit -n 10000

# Windows: Usually not an issue
```

### Locust web UI not accessible
**Solution**: Specify web host explicitly
```bash
locust -f locustfile_learning_path.py --host=http://localhost:8001 --web-host=0.0.0.0
```

### High error rate immediately
**Possible Issues**:
1. Backend not ready (wait for startup)
2. Database not connected
3. Redis not available (non-critical but impacts performance)

---

## 📚 Additional Resources

- **Locust Documentation**: https://docs.locust.io/
- **Prometheus Queries**: Check P1.2 implementation docs
- **Grafana Dashboards**: Coming in P1.10

---

## 🎉 Success Criteria

Load tests are successful if:
- ✅ Smoke test passes with 100% success rate
- ✅ Normal load test achieves > 95% success rate
- ✅ P95 response times meet targets
- ✅ Throughput > 100 RPS at 100 users
- ✅ No critical errors or crashes
- ✅ System recovers from stress/spike tests

---

**P1.3 Implementation**: ✅ Complete
**Date**: 2025-01-04
**Next**: P1.4 - Circuit Breaker Integration
