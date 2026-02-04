# Makefile for Kiro2 Backend Development
# Performance-optimized test commands with automated coverage reporting
# Sprint 8: Code Quality & Standardization

.PHONY: test test-fast test-slow test-parallel test-coverage benchmark clean coverage-report coverage-dashboard coverage-install-hooks format lint type-check security quality pre-commit install ci

# Default test command - fast tests only
test:
	@echo "Running fast core tests..."
	python -m pytest tests/fast/ -v --tb=short --maxfail=3

# Fast tests with minimal output
test-fast:
	@echo "Fast tests (minimal output)..."
	python -m pytest tests/fast/ -q --tb=line --maxfail=3

# Slow/comprehensive tests
test-slow:
	@echo "Running slow tests..."
	python -m pytest tests/slow/ -v --tb=short --maxfail=5 --timeout=30

# Parallel execution
test-parallel:
	@echo "Running fast tests in parallel..."
	python -m pytest tests/fast/ -n 2 --dist worksteal -v

# Fast tests with coverage
test-coverage:
	@echo "Fast tests with coverage..."
	python -m pytest tests/fast/ --cov=core --cov-report=term-missing --cov-report=html

# Integration tests
test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v --tb=short --maxfail=5

# Performance benchmark
benchmark:
	@echo "Performance benchmark..."
	@echo "Testing collection speed..."
	@time python -m pytest tests/fast/ --collect-only -q
	@echo "Testing execution speed..."
	@time python test_fast.py

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Watch mode for development
test-watch:
	@echo "Watch mode - re-run tests on file changes..."
	python -m pytest tests/fast/ --tb=short -f

# Quick syntax check
syntax-check:
	@echo "Quick syntax check..."
	python -m py_compile tests/fast/*.py

# === AUTOMATED COVERAGE REPORTING ===

# Generate comprehensive coverage report
coverage-report:
	@echo "🧪 Generating comprehensive coverage report..."
	python scripts/run_coverage_automation.py --analyze --test-type critical --verbose

# Quick coverage summary
coverage-summary:
	@echo "📊 Quick coverage summary..."
	python scripts/run_coverage_automation.py --summary

# Start interactive coverage dashboard
coverage-dashboard:
	@echo "🎯 Starting coverage dashboard..."
	python scripts/run_coverage_automation.py --dashboard

# Install git hooks for coverage checking
coverage-install-hooks:
	@echo "🔗 Installing coverage git hooks..."
	python scripts/run_coverage_automation.py --install-hooks

# Coverage analysis for different test types
coverage-fast:
	@echo "⚡ Fast test coverage analysis..."
	python scripts/run_coverage_automation.py --analyze --test-type fast

coverage-integration:
	@echo "🔗 Integration test coverage analysis..."
	python scripts/run_coverage_automation.py --analyze --test-type integration

coverage-all:
	@echo "🎯 Complete coverage analysis..."
	python scripts/run_coverage_automation.py --analyze --test-type all

# Enhanced test-coverage with automation
test-coverage-enhanced:
	@echo "Enhanced coverage analysis with reporting..."
	python -m pytest tests/fast/ tests/integration/ --cov=core --cov=models --cov=services --cov=api --cov-report=html --cov-report=json --cov-report=term
	python scripts/run_coverage_automation.py --summary

help:
	@echo "Available commands:"
	@echo ""
	@echo "=== TESTING ==="
	@echo "  test                    - Run fast core tests (default)"
	@echo "  test-fast              - Minimal output fast tests" 
	@echo "  test-slow              - Run comprehensive slow tests"
	@echo "  test-parallel          - Run tests in parallel"
	@echo "  test-coverage          - Fast tests with coverage report"
	@echo "  test-integration       - Run integration tests"
	@echo "  test-coverage-enhanced - Enhanced coverage with automation"
	@echo ""
	@echo "=== COVERAGE AUTOMATION ==="
	@echo "  coverage-report        - Generate comprehensive coverage report"
	@echo "  coverage-summary       - Quick coverage summary"
	@echo "  coverage-dashboard     - Start interactive coverage dashboard"
	@echo "  coverage-install-hooks - Install git hooks for coverage checking"
	@echo "  coverage-fast          - Fast test coverage analysis"
	@echo "  coverage-integration   - Integration test coverage analysis"
	@echo "  coverage-all           - Complete coverage analysis"
	@echo ""
	@echo "=== UTILITIES ==="
	@echo "  benchmark              - Performance benchmark"
	@echo "  clean                  - Clean test artifacts"
	@echo "  test-watch             - Watch mode for development"
	@echo "  syntax-check           - Quick syntax validation"
	@echo ""
	@echo "=== CODE QUALITY (Sprint 8) ==="
	@echo "  install                - Install dependencies and pre-commit hooks"
	@echo "  format                 - Auto-format code (Black + isort)"
	@echo "  lint                   - Run linters (Flake8 + Ruff)"
	@echo "  type-check             - Run type checking (MyPy)"
	@echo "  security               - Run security scans (Bandit + Safety)"
	@echo "  quality                - Run all code quality checks"
	@echo "  pre-commit             - Run pre-commit hooks"
	@echo "  ci                     - Run full CI pipeline locally"

# === SPRINT 8: CODE QUALITY & STANDARDIZATION ===

# Install dependencies and setup
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install pre-commit
	pre-commit install
	@echo "✓ Installation complete"

# Auto-format code
format:
	@echo "🎨 Formatting code..."
	python -m black .
	python -m isort .
	@echo "✓ Code formatted"

# Run linters
lint:
	@echo "🔍 Running linters..."
	python -m flake8 . --count --statistics || true
	python -m ruff check . || true
	@echo "✓ Linting complete"

# Type checking
type-check:
	@echo "🔬 Running type checks..."
	python -m mypy core/ --ignore-missing-imports --explicit-package-bases || true
	@echo "✓ Type checking complete"

# Security scans
security:
	@echo "🔒 Running security scans..."
	python -m bandit -r . -x ./tests,./venv -ll || true
	python -m safety check || true
	@echo "✓ Security scan complete"

# Run all code quality checks
quality:
	@echo "✨ Running full code quality check..."
	python code_quality.py
	@echo "✓ Quality check complete"

# Run pre-commit hooks
pre-commit:
	@echo "🪝 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✓ Pre-commit complete"

# Full CI pipeline
ci: clean format lint type-check security test-coverage
	@echo "🚀 Full CI pipeline complete"