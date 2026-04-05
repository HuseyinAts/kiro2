#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Orchestrator Quick Setup Script
Hibrit orkestrasyon sistemini 5 dakikada kur!
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import platform

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(cmd, description):
    """Run command and return success status"""
    print_info(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(description)
            return True
        else:
            print_error(f"Failed: {description}")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def check_requirements():
    """Check system requirements"""
    print_header("CHECKING REQUIREMENTS")
    
    requirements = {
        "python": "python --version",
        "pip": "pip --version",
        "git": "git --version",
        "docker": "docker --version",
        "redis": "redis-cli --version"
    }
    
    missing = []
    for name, cmd in requirements.items():
        try:
            subprocess.run(cmd.split(), capture_output=True)
            print_success(f"{name} installed")
        except:
            print_warning(f"{name} not found")
            missing.append(name)
    
    return missing

def install_packages():
    """Install required Python packages"""
    print_header("INSTALLING PACKAGES")
    
    packages = [
        "litellm[proxy]",
        "crewai",
        "langflow",
        "fastapi",
        "uvicorn",
        "redis",
        "pydantic",
        "python-dotenv"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    return True

def create_litellm_config():
    """Create LiteLLM configuration"""
    print_header("CONFIGURING LITELLM")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not anthropic_key:
        print_warning("ANTHROPIC_API_KEY not found in environment")
        anthropic_key = input("Enter your Anthropic API key (or press Enter to skip): ").strip()
    
    config = {
        "model_list": [
            {
                "model_name": "kiro2-main",
                "litellm_params": {
                    "model": "claude-3-opus-20240229",
                    "api_key": anthropic_key or "YOUR_ANTHROPIC_API_KEY",
                    "max_tokens": 4000
                }
            },
            {
                "model_name": "kiro2-fast",
                "litellm_params": {
                    "model": "claude-3-haiku-20240307",
                    "api_key": anthropic_key or "YOUR_ANTHROPIC_API_KEY",
                    "max_tokens": 2000
                }
            }
        ],
        "cache": {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "ttl": 3600
        },
        "router_settings": {
            "routing_strategy": "usage-based",
            "fallbacks": {
                "kiro2-main": ["kiro2-fast"]
            }
        },
        "general_settings": {
            "max_parallel_requests": 100,
            "request_timeout": 30
        }
    }
    
    # Add OpenAI backup if key exists
    if openai_key:
        config["model_list"].append({
            "model_name": "kiro2-backup",
            "litellm_params": {
                "model": "gpt-4-turbo",
                "api_key": openai_key,
                "max_tokens": 4000
            }
        })
    
    config_file = config_dir / "litellm_config.yaml"
    
    # Convert to YAML format
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print_success(f"LiteLLM config created at {config_file}")
    return True

def create_crew_agents():
    """Create CrewAI agents"""
    print_header("SETTING UP AGENTS")
    
    agents_dir = Path("agents")
    agents_dir.mkdir(exist_ok=True)
    
    agents_code = '''from crewai import Agent, Task, Crew, Process
import os

class KIRO2Crew:
    """KIRO2 Multi-Agent System"""
    
    def __init__(self):
        base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:8100")
        
        self.backend_agent = Agent(
            role='Backend API Specialist',
            goal='Create FastAPI endpoints and database operations',
            backstory='Expert in Python, FastAPI, and PostgreSQL',
            llm_config={"model": "kiro2-main", "base_url": base_url},
            verbose=True
        )
        
        self.frontend_agent = Agent(
            role='Frontend Developer',
            goal='Build React components with TypeScript',
            backstory='Expert in React 18, TypeScript, TailwindCSS',
            llm_config={"model": "kiro2-fast", "base_url": base_url},
            verbose=True
        )
        
        self.content_agent = Agent(
            role='Educational Content Manager',
            goal='Manage YKS/TYT/AYT educational content',
            backstory='Expert in Turkish education system',
            llm_config={"model": "kiro2-main", "base_url": base_url},
            verbose=True
        )
        
        self.nlp_agent = Agent(
            role='Turkish NLP Specialist',
            goal='Analyze Turkish text and questions',
            backstory='Expert in Turkish language processing',
            llm_config={"model": "kiro2-main", "base_url": base_url},
            verbose=True
        )
        
        self.devops_agent = Agent(
            role='DevOps Engineer',
            goal='Handle deployment and optimization',
            backstory='Expert in Docker, CI/CD, monitoring',
            llm_config={"model": "kiro2-fast", "base_url": base_url},
            verbose=True
        )
    
    def create_crew(self, tasks):
        return Crew(
            agents=[self.backend_agent, self.frontend_agent, 
                   self.content_agent, self.nlp_agent, self.devops_agent],
            tasks=tasks,
            process=Process.hierarchical,
            manager_llm="kiro2-main",
            verbose=True
        )
'''
    
    agents_file = agents_dir / "kiro2_crew.py"
    with open(agents_file, 'w', encoding='utf-8') as f:
        f.write(agents_code)
    
    print_success(f"Agent definitions created at {agents_file}")
    return True

def create_orchestrator_api():
    """Create FastAPI orchestrator"""
    print_header("CREATING API")
    
    api_code = '''from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sys
sys.path.append('.')

from agents.kiro2_crew import KIRO2Crew
from crewai import Task

app = FastAPI(title="KIRO2 Orchestrator")

# Initialize crew
crew_manager = KIRO2Crew()

class OrchestrationRequest(BaseModel):
    prompt: str
    priority: str = "normal"
    context: dict = {}

@app.post("/orchestrate")
async def orchestrate(request: OrchestrationRequest):
    """Main orchestration endpoint"""
    
    task = Task(
        description=request.prompt,
        expected_output="Complete solution"
    )
    
    crew = crew_manager.create_crew([task])
    result = crew.kickoff()
    
    return {
        "status": "completed",
        "result": str(result),
        "agents_used": ["backend", "frontend", "content"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kiro2-orchestrator"}
'''
    
    with open("orchestrator_api.py", 'w', encoding='utf-8') as f:
        f.write(api_code)
    
    print_success("Orchestrator API created")
    return True

def create_env_file():
    """Create .env file template"""
    print_header("CREATING ENVIRONMENT FILE")
    
    env_content = '''# KIRO2 Orchestrator Environment Variables

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional backup

# Service URLs
LITELLM_BASE_URL=http://localhost:8100
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://postgres:password@localhost:5434/kiro2

# Ports
LITELLM_PORT=8100
ORCHESTRATOR_PORT=8200
LANGFLOW_PORT=7860

# Environment
ENVIRONMENT=development
'''
    
    env_file = Path(".env.orchestrator")
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print_success(f"Environment template created at {env_file}")
    print_warning("Please update API keys in .env.orchestrator")
    return True

def create_start_script():
    """Create startup script"""
    print_header("CREATING STARTUP SCRIPT")
    
    if platform.system() == "Windows":
        script_name = "start_orchestrator.bat"
        script_content = '''@echo off
echo Starting KIRO2 Orchestrator...
echo.

REM Start Redis if not running
echo [1/4] Starting Redis...
start /B redis-server

REM Start LiteLLM Gateway
echo [2/4] Starting LiteLLM Gateway...
start /B cmd /c "litellm --config ./config/litellm_config.yaml --port 8100"

REM Wait for LiteLLM to start
timeout /t 5

REM Start Orchestrator API
echo [3/4] Starting Orchestrator API...
start /B cmd /c "uvicorn orchestrator_api:app --port 8200 --reload"

REM Optional: Start Langflow
echo [4/4] Starting Langflow UI (optional)...
REM start /B cmd /c "langflow run --port 7860"

echo.
echo ========================================
echo KIRO2 Orchestrator is running!
echo ========================================
echo.
echo Services:
echo - LiteLLM Gateway: http://localhost:8100
echo - Orchestrator API: http://localhost:8200/docs
echo - Langflow UI: http://localhost:7860
echo.
echo Press Ctrl+C to stop all services
pause
'''
    else:
        script_name = "start_orchestrator.sh"
        script_content = '''#!/bin/bash
echo "Starting KIRO2 Orchestrator..."
echo

# Start Redis if not running
echo "[1/4] Starting Redis..."
redis-server &

# Start LiteLLM Gateway
echo "[2/4] Starting LiteLLM Gateway..."
litellm --config ./config/litellm_config.yaml --port 8100 &

# Wait for LiteLLM to start
sleep 5

# Start Orchestrator API
echo "[3/4] Starting Orchestrator API..."
uvicorn orchestrator_api:app --port 8200 --reload &

# Optional: Start Langflow
echo "[4/4] Starting Langflow UI (optional)..."
# langflow run --port 7860 &

echo
echo "========================================"
echo "KIRO2 Orchestrator is running!"
echo "========================================"
echo
echo "Services:"
echo "- LiteLLM Gateway: http://localhost:8100"
echo "- Orchestrator API: http://localhost:8200/docs"
echo "- Langflow UI: http://localhost:7860"
echo
echo "Press Ctrl+C to stop all services"
wait
'''
        
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(script_name, 0o755)
    
    print_success(f"Startup script created: {script_name}")
    return True

def test_setup():
    """Test the setup"""
    print_header("TESTING SETUP")
    
    # Test imports
    try:
        import litellm
        import crewai
        import fastapi
        print_success("All packages imported successfully")
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False
    
    # Test Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print_success("Redis connection successful")
    except:
        print_warning("Redis not running (optional)")
    
    return True

def main():
    """Main setup function"""
    print_header("KIRO2 ORCHESTRATOR SETUP")
    print_info("This script will set up the hybrid orchestration system")
    
    # Check requirements
    missing = check_requirements()
    if missing:
        print_warning(f"Missing requirements: {', '.join(missing)}")
        if "python" in missing or "pip" in missing:
            print_error("Python and pip are required!")
            sys.exit(1)
    
    # Install packages
    if not install_packages():
        print_error("Package installation failed")
        sys.exit(1)
    
    # Create configurations
    create_litellm_config()
    create_crew_agents()
    create_orchestrator_api()
    create_env_file()
    create_start_script()
    
    # Test setup
    test_setup()
    
    # Final instructions
    print_header("SETUP COMPLETE! 🎉")
    print(f"""
{Colors.GREEN}Next steps:{Colors.END}

1. Update API keys in .env.orchestrator:
   {Colors.YELLOW}ANTHROPIC_API_KEY=your_key_here{Colors.END}

2. Start the orchestrator:
   {Colors.BLUE}{'start_orchestrator.bat' if platform.system() == 'Windows' else './start_orchestrator.sh'}{Colors.END}

3. Test the API:
   {Colors.BLUE}curl -X POST http://localhost:8200/orchestrate \\
     -H "Content-Type: application/json" \\
     -d '{{"prompt": "Create a user authentication API"}}'
   {Colors.END}

4. View API docs:
   {Colors.BLUE}http://localhost:8200/docs{Colors.END}

5. (Optional) Open Langflow UI:
   {Colors.BLUE}http://localhost:7860{Colors.END}

{Colors.BOLD}Happy orchestrating! 🚀{Colors.END}
""")

if __name__ == "__main__":
    main()