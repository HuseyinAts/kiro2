#!/bin/bash

echo "========================================"
echo "  AI EDUCATION PLATFORM - MINIMAL"
echo "========================================"
echo ""

# Start backend
echo "[1/2] Starting Backend Server..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit
sleep 3

# Start frontend
echo "[2/2] Starting Frontend Server..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Servers running:"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"  
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "========================================"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait