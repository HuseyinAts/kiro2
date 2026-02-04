# 🚀 CI/CD Pipeline Setup Guide

## Overview

This guide covers the complete setup and configuration of our modern CI/CD pipeline for the Turkish Education Platform project. Our pipeline emphasizes code quality, comprehensive testing, and security.

## 📋 Table of Contents

1. [Pipeline Architecture](#pipeline-architecture)
2. [Workflow Files](#workflow-files)
3. [Quality Gates](#quality-gates)
4. [Test Coverage Strategy](#test-coverage-strategy)
5. [Security & Dependencies](#security--dependencies)
6. [Branch Protection](#branch-protection)
7. [Setup Instructions](#setup-instructions)
8. [Troubleshooting](#troubleshooting)

## 🏗️ Pipeline Architecture

### Workflow Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Pull Request / Push                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │    Modern Testing       │
         │    (Fast & Focused)     │
         └────────────┬────────────┘
                      │
    ┌─────────────────▼─────────────────┐
    │         Enhanced CI/CD           │
    │    (Comprehensive Pipeline)      │
    └─────────────────┬─────────────────┘
                      │
         ┌────────────▼────────────┐
         │  Comprehensive CI/CD    │
         │  (Production Deployment) │
         └─────────────────────────┘
```

### Pipeline Components

1. **Modern Testing Pipeline** (`modern-testing.yml`)
   - Fast, focused testing
   - Modern code quality tools
   - Coverage analysis
   - Security scanning

2. **Enhanced CI/CD Pipeline** (`enhanced-ci-cd.yml`)
   - Multi-environment testing
   - Performance checks
   - Integration testing
   - Quality gates

3. **Comprehensive CI/CD Pipeline** (`comprehensive-ci-cd.yml`)
   - Full deployment pipeline
   - Blue-green deployments
   - Production monitoring

## 📄 Workflow Files

### 1. Modern Testing Pipeline

**File**: `.github/workflows/modern-testing.yml`

**Triggers**:
- Push to `main`, `master`, `develop`, `feature/*`
- Pull requests to `main`, `master`, `develop`

**Key Features**:
- ⚡ **Super-fast execution** (< 5 minutes)
- 🎯 **Targeted test groups** (config, base-service, exceptions, etc.)
- 📊 **52%+ coverage requirement** on core modules
- 🔒 **Security scanning** with Bandit, Safety, pip-audit
- 🎨 **Modern tools**: Ruff, Black, isort, pre-commit

**Jobs**:
```yaml
modern-quality          # Ruff, Black, pre-commit
├── fast-comprehensive-tests  # Parallel test execution
├── coverage-analysis   # Combined coverage reporting
├── security-scan      # Security & dependency checks
├── performance-check  # Performance profiling
└── modern-quality-gate # Final quality decision
```

### 2. Enhanced CI/CD Pipeline

**File**: `.github/workflows/enhanced-ci-cd.yml`

**Advanced Features**:
- 🔄 **Multi-Python version testing** (3.11, 3.12)
- 🐘 **PostgreSQL & Redis services**
- 🧪 **Integration testing**
- ⚡ **Performance testing** with Locust
- 📈 **Coverage combination & reporting**

### 3. Comprehensive CI/CD Pipeline

**File**: `.github/workflows/comprehensive-ci-cd.yml`

**Production Features**:
- 🚀 **Blue-green deployments**
- ☸️ **Kubernetes orchestration**
- 🌍 **Multi-environment support** (dev, staging, prod)
- 📱 **Frontend & backend coordination**
- 📊 **Performance monitoring**

## 🚨 Quality Gates

### Fast Quality Gates (Every PR)

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Code Quality | Ruff | 0 errors | ✅ Yes |
| Formatting | Black | Perfect format | ✅ Yes |
| Import Order | isort | Sorted | ✅ Yes |
| Test Coverage | pytest-cov | 52%+ core modules | ✅ Yes |
| Security | Bandit | High severity | ✅ Yes |
| Dependencies | Safety | High severity | ⚠️ Warning |

### Enhanced Quality Gates (Main/Develop)

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Integration Tests | pytest | 100% pass | ✅ Yes |
| Performance | Locust | < 500ms avg | ⚠️ Warning |
| E2E Tests | Playwright | 100% pass | ✅ Yes |
| SonarCloud | SonarQube | Quality Gate | ✅ Yes |

## 📊 Test Coverage Strategy

### Target Coverage by Module

```
core/
├── config.py          → 100% ✅ (Critical configuration)
├── base_service.py    → 58%  ✅ (Base functionality)
├── exceptions.py      → 38%  ✅ (Error handling)
├── database.py        → 29%  ✅ (Database layer)
├── structured_logger.py → 73% ✅ (Logging system)
└── [other modules]    → 0-50% (Gradual improvement)
```

### Test Structure

```
tests/
├── fast/                    # < 2 minutes total
│   ├── test_core_config_fixed.py
│   ├── test_core_base_service_realistic.py
│   ├── test_core_exceptions_comprehensive.py
│   ├── test_core_database_comprehensive.py
│   └── test_core_structured_logger_comprehensive.py
├── integration/             # Real services
└── performance/            # Load testing
```

### Coverage Commands

```bash
# Run fast tests with coverage
cd backend
pytest tests/fast/ \
  --cov=core \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=52

# Generate coverage report
coverage html
open htmlcov/index.html
```

## 🔒 Security & Dependencies

### Security Tools

1. **Bandit** - Python security linter
   ```bash
   bandit -r . -f json -o bandit-report.json
   ```

2. **Safety** - Vulnerability scanner
   ```bash
   safety check --json --output safety-report.json
   ```

3. **pip-audit** - Dependency auditing
   ```bash
   pip-audit --format=json --output=pip-audit-report.json
   ```

### Security Gates

- ❌ **High severity vulnerabilities** → Block merge
- ⚠️ **Medium severity** → Warning + review required
- ✅ **Low severity** → Log for tracking

## 🛡️ Branch Protection

### Protected Branches

- `main` / `master` - Production
- `develop` - Development integration
- `feature/*` - Feature development

### Protection Rules

```python
# Main/Master branches
required_reviews: 2
required_status_checks: [
  "Modern Code Quality",
  "Coverage Analysis", 
  "Security & Dependencies",
  "Modern Quality Gate"
]
dismiss_stale_reviews: true
require_code_owner_reviews: true
```

### Setup Branch Protection

```bash
# Set environment variables
export GITHUB_REPOSITORY_OWNER="your-org"
export GITHUB_REPOSITORY_NAME="teknofest-2025-egitim-eylemci"
export GITHUB_TOKEN="your-token"

# Run setup script
python scripts/setup-branch-protection.py
```

## 🚀 Setup Instructions

### 1. Prerequisites

- GitHub repository with Actions enabled
- Python 3.11+ in your development environment
- Docker for integration testing
- Access to secrets configuration

### 2. Required Secrets

Add these secrets to your GitHub repository:

```bash
# Code Quality & Coverage
CODECOV_TOKEN=your-codecov-token
SONAR_TOKEN=your-sonar-token
SONAR_ORGANIZATION=your-org
SONAR_PROJECT_KEY=your-project-key

# Deployment
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
HEROKU_API_KEY=your-heroku-key
HEROKU_EMAIL=your-email

# Notifications
SLACK_WEBHOOK=your-slack-webhook
```

### 3. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/teknofest-2025-egitim-eylemci.git
cd teknofest-2025-egitim-eylemci

# Backend setup
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ruff black isort mypy pre-commit

# Install pre-commit hooks
pre-commit install

# Run initial quality check
python quality.py --fix
```

### 4. Test the Pipeline

```bash
# Create a test branch
git checkout -b test/ci-cd-setup

# Make a small change
echo "# CI/CD Test" >> README.md
git add README.md
git commit -m "test: CI/CD pipeline setup"

# Push and create PR
git push origin test/ci-cd-setup
# Create PR through GitHub UI
```

### 5. Monitor Results

1. **GitHub Actions tab** - Watch workflow execution
2. **Codecov dashboard** - Monitor coverage trends
3. **SonarCloud** - Review quality metrics
4. **PR comments** - Automated quality reports

## 🔧 Troubleshooting

### Common Issues

#### 1. Coverage Below Threshold

```bash
# Check current coverage
cd backend
pytest tests/fast/ --cov=core --cov-report=term-missing

# Add more tests for uncovered lines
# Focus on core modules with <52% coverage
```

#### 2. Ruff Linting Errors

```bash
# Auto-fix most issues
cd backend
ruff check . --fix

# Manual fixes for remaining issues
ruff check . --output-format=github
```

#### 3. Pre-commit Failures

```bash
# Run pre-commit manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

#### 4. Integration Test Failures

```bash
# Run with services locally
docker-compose up -d postgres redis
pytest tests/integration/ -v

# Check service health
docker-compose ps
```

### Performance Issues

#### Slow Test Execution

```bash
# Run tests in parallel
pytest tests/fast/ -n auto

# Profile slow tests
pytest tests/fast/ --durations=10
```

#### Large Artifact Sizes

```bash
# Clean up coverage HTML
rm -rf backend/htmlcov/

# Use coverage XML for CI
pytest --cov=core --cov-report=xml
```

### Debug CI/CD Issues

#### GitHub Actions Debugging

```yaml
# Add to workflow for debugging
- name: Debug Environment
  run: |
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
    echo "Working directory: $(pwd)"
    echo "Python path: $PYTHONPATH"
    ls -la
```

#### Local Simulation

```bash
# Run similar to CI environment
export PYTHONPATH=$PWD/backend
export DATABASE_URL=sqlite+aiosqlite:///./test.db
export TESTING=true

cd backend
pytest tests/fast/ --cov=core --cov-fail-under=52
```

## 📈 Metrics & Monitoring

### Key Metrics to Track

1. **Build Success Rate** - Target: >95%
2. **Test Coverage** - Target: 52%+ (core), 80%+ (overall)
3. **Build Time** - Target: <10 minutes
4. **Security Issues** - Target: 0 high severity
5. **Code Quality Score** - Target: A rating

### Dashboard Links

- **GitHub Actions**: `https://github.com/your-org/repo/actions`
- **Codecov**: `https://codecov.io/gh/your-org/repo`
- **SonarCloud**: `https://sonarcloud.io/project/overview?id=your-project`

### Continuous Improvement

1. **Weekly Reviews** - Check metrics and trends
2. **Monthly Optimizations** - Improve build times
3. **Quarterly Updates** - Update tools and dependencies
4. **Annual Review** - Assess overall strategy

## 🎯 Best Practices

### Development Workflow

1. **Feature Development**:
   ```bash
   git checkout -b feature/new-feature
   # Develop with pre-commit hooks
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   # Create PR → Auto quality checks
   ```

2. **Code Reviews**:
   - ✅ Check CI/CD status before review
   - ✅ Review coverage report
   - ✅ Verify security scan results
   - ✅ Test locally if needed

3. **Merging**:
   - ✅ All quality gates pass
   - ✅ Required approvals obtained
   - ✅ Up-to-date with target branch
   - ✅ Squash commits for clean history

### Quality Standards

- **Code Coverage**: Maintain 52%+ on core modules
- **Code Quality**: Zero Ruff errors
- **Security**: Zero high-severity issues
- **Performance**: <500ms average response time
- **Documentation**: Update docs with features

---

## 🎉 Success Criteria

Your CI/CD pipeline is successfully configured when:

- ✅ All workflows run without errors
- ✅ Coverage reports are generated automatically
- ✅ Security scans complete successfully
- ✅ Branch protection prevents broken merges
- ✅ Team can develop with confidence
- ✅ Deployment pipeline is ready for production

**Next Steps**: Once setup is complete, focus on expanding test coverage to additional modules and optimizing build performance.

---

*For questions or issues, check the [Troubleshooting](#troubleshooting) section or create an issue in the repository.*