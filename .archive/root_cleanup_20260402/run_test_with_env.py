#!/usr/bin/env python3
"""Set test environment and run tests"""
import os
import subprocess
import sys

# Set test environment before any imports
os.environ['TESTING'] = 'true'

print("TESTING environment variable set to:", os.environ.get('TESTING'))

# Run the test
if __name__ == "__main__":
    # Run pytest with the environment variable set
    test_args = sys.argv[1:] if len(sys.argv) > 1 else [
        "tests/test_database_models.py::TestEnums::test_sinav_tipi_enum",
        "-v", "--tb=short"
    ]
    
    cmd = [sys.executable, "-m", "pytest"] + test_args
    
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)