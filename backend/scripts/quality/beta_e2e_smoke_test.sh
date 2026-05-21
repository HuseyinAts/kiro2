#!/bin/bash
# Beta E2E Smoke Test — Bug #1-11 fix validation
# Karpathy: "Doğrulanana kadar döngüde kal"

set -u
URL="https://ates.tail610d7b.ts.net"
EMAIL="beta01@kiro2.com"
PASS_CRED="Beta01!Kiro2026"

# ANSI colors
GR='\033[0;32m'; RD='\033[0;31m'; YL='\033[1;33m'; NC='\033[0m'
ok() { printf "${GR}✓ PASS${NC} %s\n" "$1"; }
fail() { printf "${RD}✗ FAIL${NC} %s\n" "$1"; }
warn() { printf "${YL}⚠ WARN${NC} %s\n" "$1"; }

PASS=0; FAIL=0

# ============================================================
# STEP 1: Login
# ============================================================
echo ""
echo "═══ STEP 1: Login (beta01) ═══"
LOGIN_RESP=$(curl -s -X POST "$URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS_CRED\"}")
TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
if [ -z "$TOKEN" ]; then
  fail "Login failed"
  FAIL=$((FAIL+1))
  exit 1
else
  ok "Login HTTP 200, token alındı"
  PASS=$((PASS+1))
fi

# ============================================================
# STEP 2: Health + DB connectivity
# ============================================================
echo ""
echo "═══ STEP 2: Infrastructure Health ═══"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health")
if [ "$HEALTH" = "200" ]; then ok "Health HTTP 200"; PASS=$((PASS+1)); else fail "Health HTTP $HEALTH"; FAIL=$((FAIL+1)); fi

# ============================================================
# STEP 3: Karışık Pratik all 9 subjects (Bug #2 + #11)
# ============================================================
echo ""
echo "═══ STEP 3: Karışık Pratik 9 subject (text-self-contained pool) ═══"
for SUB in MATEMATIK FIZIK GEOMETRI KIMYA BIYOLOJI TURKCE TARIH EDEBIYAT COGRAFYA; do
  RESP=$(curl -s -H "Authorization: Bearer $TOKEN" "$URL/api/v1/learning-path/interleaved-practice?subjects=$SUB&count=3")
  CNT=$(echo "$RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('count',0))")
  if [ "$CNT" -ge "1" ]; then
    # Verify text-self-contained (no şekil reference)
    HAS_IMG_REF=$(echo "$RESP" | python -c "
import sys,json,re
d=json.load(sys.stdin)
qs=d.get('questions',[])
imgref_pat=re.compile(r'şekil|yukarıda|aşağıda|verilen graf|verilen tablo|tabloda|grafikte|şemada|haritada|verilenler|aşağıdaki şek', re.IGNORECASE)
count_ref=sum(1 for q in qs if imgref_pat.search(q.get('question_text','')))
print(count_ref)
")
    if [ "$HAS_IMG_REF" -eq "0" ]; then
      ok "$SUB: $CNT/3 soru, image-required ref 0"
      PASS=$((PASS+1))
    else
      warn "$SUB: $CNT/3 soru AMA $HAS_IMG_REF tanesinde image-ref var"
      FAIL=$((FAIL+1))
    fi
  else
    fail "$SUB: 0/3 soru gelmedi"
    FAIL=$((FAIL+1))
  fi
done

# ============================================================
# STEP 4: Placement 9 subjects (Bug #2)
# ============================================================
echo ""
echo "═══ STEP 4: Placement 9 subject ═══"
for SUB in MATEMATIK FIZIK GEOMETRI KIMYA BIYOLOJI TURKCE TARIH EDEBIYAT COGRAFYA; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL/api/v1/placement/start" \
    -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
    -d "{\"subject_id\":\"$SUB\"}")
  if [ "$CODE" = "201" ]; then
    ok "Placement $SUB: HTTP 201"
    PASS=$((PASS+1))
  else
    fail "Placement $SUB: HTTP $CODE"
    FAIL=$((FAIL+1))
  fi
done

# ============================================================
# STEP 5: CAT 9 subjects (Bug #2)
# ============================================================
echo ""
echo "═══ STEP 5: CAT (Adaptif Test) 9 subject ═══"
for SUB in MATEMATIK FIZIK GEOMETRI KIMYA BIYOLOJI TURKCE TARIH EDEBIYAT COGRAFYA; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL/api/v1/cat/sessions" \
    -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
    -d "{\"subject_id\":\"$SUB\"}")
  if [ "$CODE" = "201" ]; then
    ok "CAT $SUB: HTTP 201"
    PASS=$((PASS+1))
  else
    fail "CAT $SUB: HTTP $CODE"
    FAIL=$((FAIL+1))
  fi
done

# ============================================================
# STEP 6: Exam create + start + current-question + timer (Bug #3)
# ============================================================
echo ""
echo "═══ STEP 6: Exam Lifecycle (TYT) ═══"
EXAM_CREATE=$(curl -s -X POST "$URL/api/v1/osym-exam/create" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"exam_type":"tyt"}')
SID=$(echo "$EXAM_CREATE" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))")
if [ -z "$SID" ]; then
  fail "Exam create failed"
  FAIL=$((FAIL+1))
else
  ok "Exam create: session_id=${SID:0:8}..."
  PASS=$((PASS+1))

  # Start
  START_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL/api/v1/osym-exam/$SID/start" -H "Authorization: Bearer $TOKEN")
  if [ "$START_CODE" = "200" ]; then ok "Exam start: HTTP 200"; PASS=$((PASS+1)); else fail "Exam start: HTTP $START_CODE"; FAIL=$((FAIL+1)); fi

  # Timer
  TIMER=$(curl -s -H "Authorization: Bearer $TOKEN" "$URL/api/v1/osym-exam/$SID/remaining-time" | python -c "import sys,json; print(json.load(sys.stdin).get('remaining_seconds',0))")
  if [ "$TIMER" -gt "8000" ]; then ok "Timer: ${TIMER}s (≈$(($TIMER/60)) dk)"; PASS=$((PASS+1)); else fail "Timer too low: ${TIMER}s"; FAIL=$((FAIL+1)); fi

  # Current question
  QCODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$URL/api/v1/osym-exam/$SID/current-question")
  if [ "$QCODE" = "200" ]; then ok "Current-question: HTTP 200"; PASS=$((PASS+1)); else fail "Current-question: HTTP $QCODE"; FAIL=$((FAIL+1)); fi
fi

# ============================================================
# STEP 7: Feedback flag endpoint (Bug #7.2)
# ============================================================
echo ""
echo "═══ STEP 7: Feedback Flag (Faz 7.2) ═══"
# Bad question_id → 400 FK violation expected (validation works)
FLAG_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL/api/v1/quality/feedback/flag" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"question_id":"00000000-0000-0000-0000-000000000000","flag_type":"other","note":"e2e smoke test"}')
if [ "$FLAG_CODE" = "400" ]; then ok "Feedback flag FK validation: HTTP 400 (expected)"; PASS=$((PASS+1)); else warn "Feedback flag: HTTP $FLAG_CODE"; fi

# Valid question_id (real beta question)
REAL_QID=$(curl -s -H "Authorization: Bearer $TOKEN" "$URL/api/v1/learning-path/interleaved-practice?subjects=MATEMATIK&count=1" | python -c "import sys,json; d=json.load(sys.stdin); qs=d.get('questions',[]); print(qs[0]['id'] if qs else '')")
if [ -n "$REAL_QID" ]; then
  REAL_FLAG=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL/api/v1/quality/feedback/flag" \
    -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
    -d "{\"question_id\":\"$REAL_QID\",\"flag_type\":\"other\",\"note\":\"e2e smoke test\"}")
  if [ "$REAL_FLAG" = "201" ]; then ok "Feedback flag REAL: HTTP 201 (created)"; PASS=$((PASS+1)); else fail "Feedback flag REAL: HTTP $REAL_FLAG"; FAIL=$((FAIL+1)); fi
fi

# ============================================================
# STEP 8: Public Funnel reachability
# ============================================================
echo ""
echo "═══ STEP 8: Public Funnel (Tailscale) ═══"
FRONTEND_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
if [ "$FRONTEND_HTTP" = "200" ]; then ok "Frontend HTTP 200 (Funnel reachable)"; PASS=$((PASS+1)); else fail "Frontend HTTP $FRONTEND_HTTP"; FAIL=$((FAIL+1)); fi

NEW_BUNDLE=$(curl -s "$URL/" | grep -oE "index-[A-Za-z0-9_-]+\.js" | head -1)
if [ -n "$NEW_BUNDLE" ]; then ok "New asset bundle: $NEW_BUNDLE"; PASS=$((PASS+1)); else warn "No bundle detected"; fi

# ============================================================
# Final report
# ============================================================
echo ""
echo "═══════════════════════════════════════════"
TOTAL=$((PASS+FAIL))
echo "TOTAL: ${PASS}/${TOTAL} PASS, ${FAIL} FAIL"
echo "═══════════════════════════════════════════"

if [ "$FAIL" = "0" ]; then
  printf "${GR}✓ BETA-READY${NC} — Davetiye gönderilebilir\n"
  exit 0
else
  printf "${RD}✗ FIX GEREK${NC} — Yukarıdaki FAIL'leri çöz\n"
  exit 1
fi
