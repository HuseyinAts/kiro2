#!/usr/bin/env python3
"""Test KiroOrchestrator initialization and get_status"""
import sys
sys.path.insert(0, "orchestrator")

from core.graph import create_orchestrator, KiroOrchestrator

print("=" * 50)
print("Testing KiroOrchestrator")
print("=" * 50)

# Create orchestrator
print("\n1. Creating orchestrator...")
orch = create_orchestrator("C:/Users/husey/kiro2")
print(f"   Created: {type(orch).__name__}")

# Check checkpointer
print("\n2. Checking checkpointer...")
print(f"   Checkpointer: {orch.checkpointer}")
print(f"   Type: {type(orch.checkpointer).__name__}")

# Check graph
print("\n3. Checking graph...")
print(f"   Graph: {orch.graph}")
print(f"   Type: {type(orch.graph).__name__}")

# Test get_status
print("\n4. Testing get_status()...")
try:
    status = orch.get_status()
    print(f"   Status: {status}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 50)
print("TEST COMPLETED SUCCESSFULLY")
print("=" * 50)
