#!/usr/bin/env python3
"""Set test environment and run all tests"""
import os
import subprocess
import sys

# Set test environment before any imports
os.environ['TESTING'] = 'true'

print("TESTING environment variable set to:", os.environ.get('TESTING'))

# Run all tests
if __name__ == "__main__":
    # Run pytest with the environment variable set
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", "--tb=no", "-q"
    ]
    
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)