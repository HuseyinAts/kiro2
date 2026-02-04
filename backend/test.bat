@echo off
REM Fast Test Commands for Windows Development

if "%1"=="fast" goto :fast
if "%1"=="coverage" goto :coverage 
if "%1"=="parallel" goto :parallel
if "%1"=="benchmark" goto :benchmark
if "%1"=="clean" goto :clean
if "%1"=="help" goto :help

REM Default: fast tests
:default
echo Running fast core tests...
py -m pytest tests/fast/ -v --tb=short --maxfail=3
goto :end

:fast
echo Fast tests (minimal output)...
py -m pytest tests/fast/ -q --tb=line --maxfail=3
goto :end

:coverage
echo Fast tests with coverage...
py -m pytest tests/fast/ --cov=core --cov-report=term-missing --cov-report=html
goto :end

:parallel
echo Running fast tests in parallel...
py -m pytest tests/fast/ -n 2 --dist worksteal -v
goto :end

:benchmark
echo Performance benchmark...
echo Testing collection speed...
py -c "import time; start=time.time(); import subprocess; subprocess.run(['py', '-m', 'pytest', 'tests/fast/', '--collect-only', '-q']); print(f'Collection: {time.time()-start:.2f}s')"
echo Testing execution speed...
py test_fast.py
goto :end

:clean
echo Cleaning test artifacts...
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist htmlcov rmdir /s /q htmlcov
if exist .coverage del .coverage
goto :end

:help
echo Available commands:
echo   test           - Run fast core tests (default)
echo   test fast      - Minimal output fast tests
echo   test coverage  - Fast tests with coverage report
echo   test parallel  - Run tests in parallel
echo   test benchmark - Performance benchmark
echo   test clean     - Clean test artifacts
echo   test help      - Show this help
goto :end

:end