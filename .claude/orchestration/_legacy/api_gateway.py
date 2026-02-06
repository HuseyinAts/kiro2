#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Gateway for Full Automatic Orchestration
Routes requests to appropriate Claude agents via API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import asyncio
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestration.orchestrator_v2 import OrchestratorV2

app = FastAPI(title="KIRO2 Orchestration Gateway")

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = OrchestratorV2()

class PromptRequest(BaseModel):
    prompt: str
    auto_execute: bool = True
    context: Optional[Dict[str, Any]] = None

class RoutingResponse(BaseModel):
    agent: str
    confidence: float
    reasoning: str
    execution_mode: str
    result: Optional[str] = None

# Agent execution endpoints (simulated - replace with actual Claude API calls)
AGENT_ENDPOINTS = {
    "kiro2-backend-api": "http://localhost:8001/backend",
    "kiro2-frontend-specialist": "http://localhost:8002/frontend",
    "kiro2-content-manager": "http://localhost:8003/content",
    "kiro2-devops-engineer": "http://localhost:8004/devops",
    "debugger": "http://localhost:8005/debug",
    "test-runner": "http://localhost:8006/test",
    "code-reviewer": "http://localhost:8007/review",
    "turkish-nlp-specialist": "http://localhost:8008/nlp",
    "general-purpose": "http://localhost:8009/general"
}

@app.post("/orchestrate", response_model=RoutingResponse)
async def orchestrate(request: PromptRequest):
    """
    Main orchestration endpoint - fully automatic routing and execution
    """
    # Analyze and route
    result = orchestrator.process(request.prompt)
    routing = result['routing']
    
    response = RoutingResponse(
        agent=routing['primary_agent'],
        confidence=routing['confidence'],
        reasoning=routing['reasoning'],
        execution_mode=routing['execution_mode']
    )
    
    # Auto-execute if requested
    if request.auto_execute:
        execution_result = await execute_with_agent(
            request.prompt,
            routing['primary_agent'],
            request.context
        )
        response.result = execution_result
    
    return response

async def execute_with_agent(prompt: str, agent: str, context: Optional[Dict] = None) -> str:
    """
    Execute prompt with selected agent
    """
    # In production, this would make actual API calls to Claude or agent services
    # For now, we simulate the execution
    
    endpoint = AGENT_ENDPOINTS.get(agent, AGENT_ENDPOINTS["general-purpose"])
    
    try:
        # Simulated API call (replace with actual implementation)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json={"prompt": prompt, "context": context},
                timeout=30.0
            )
            return response.json().get("result", "Execution completed")
    except:
        # Fallback for demo
        return f"[Simulated] Agent '{agent}' processed: {prompt[:50]}..."

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": list(AGENT_ENDPOINTS.keys()),
        "total": len(AGENT_ENDPOINTS)
    }

@app.post("/analyze")
async def analyze_prompt(request: PromptRequest):
    """Analyze prompt without execution"""
    result = orchestrator.process(request.prompt)
    return result['analysis']

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "orchestration-gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, reload=True)