# Contributing to Kiro2

Thank you for your interest in contributing to Kiro2! This guide will help you get started.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Review](#code-review)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, discrimination, or offensive comments
- Trolling, insulting/derogatory comments, or personal attacks
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Violations may be reported to [conduct@kiro2.com](mailto:conduct@kiro2.com). All complaints will be reviewed and investigated.

---

## 🚀 Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of the [Kiro2 repository](https://github.com/yourusername/kiro2).

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/kiro2.git
cd kiro2
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/yourusername/kiro2.git
git remote -v
```

### 4. Setup Development Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 6. Run Tests

```bash
# Ensure everything works
make test
```

---

## 🔄 Development Workflow

### 1. Sync with Upstream

```bash
git checkout master
git fetch upstream
git merge upstream/master
git push origin master
```

### 2. Create Feature Branch

```bash
# Use descriptive branch names
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
# or
git checkout -b docs/documentation-update
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `perf/` - Performance improvements

### 3. Make Changes

```bash
# Edit files
# ...

# Run tests frequently
make test

# Check code quality
make quality
```

### 4. Commit Changes

```bash
# Add changes
git add .

# Commit with descriptive message (see Commit Messages section)
git commit -m "feat: Add user profile analytics"

# Pre-commit hooks will run automatically
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

Go to your fork on GitHub and click "New Pull Request".

---

## 📝 Coding Standards

We follow strict coding standards to maintain code quality.

### Code Formatting

**Tools:**
- **Black**: Code formatter (line-length=88)
- **isort**: Import sorter (Black-compatible)

```bash
# Auto-format code
make format

# Check formatting
black --check .
isort --check-only .
```

**Example:**

```python
# Good
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from core.database import get_session
from models.user import User


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID with proper typing."""
    with get_session() as session:
        result = session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
```

```python
# Bad (will be auto-fixed by Black/isort)
import os,sys
from fastapi import FastAPI,HTTPException
from typing import Optional
from core.database import get_session


def get_user_by_id(user_id: str):  # Missing return type
    with get_session() as session:
        return session.execute(select(User).where(User.id==user_id)).scalar_one_or_none()
```

### Linting

**Tools:**
- **Flake8**: PEP 8 compliance
- **Ruff**: Fast, modern linter

```bash
# Run linters
make lint

# Check specific files
flake8 core/advanced_rate_limiter.py
ruff check core/
```

**Rules:**
- Max line length: 88
- Max complexity: 10
- No unused imports
- No undefined names

### Type Hints

**Always add type hints:**

```python
# Good
from typing import Optional, Dict, List

def calculate_score(
    answers: List[Dict[str, str]],
    exam_type: str,
    user_id: Optional[str] = None
) -> Dict[str, float]:
    """Calculate exam score with proper typing."""
    pass
```

```python
# Bad
def calculate_score(answers, exam_type, user_id=None):
    """No type hints - harder to maintain."""
    pass
```

**Type check:**
```bash
make type-check
```

### Documentation

**Docstrings:**

Use Google-style docstrings:

```python
def process_exam_results(
    exam_id: str,
    answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process exam results and calculate scores.

    This function processes student answers, calculates scores using
    IRT and FSRS algorithms, and updates the database.

    Args:
        exam_id: Unique identifier for the exam
        answers: List of answer dictionaries with question_id and answer

    Returns:
        Dictionary containing:
            - score: Total score (float)
            - correct_count: Number of correct answers (int)
            - irt_theta: Updated ability parameter (float)
            - next_review: Next review timestamp (datetime)

    Raises:
        ValueError: If exam_id is invalid
        DatabaseError: If database update fails

    Example:
        >>> results = process_exam_results(
        ...     "exam-123",
        ...     [{"question_id": "q1", "answer": "B"}]
        ... )
        >>> results["score"]
        85.5
    """
    pass
```

### Security

**Never:**
- Commit secrets or API keys
- Use `eval()` or `exec()`
- Allow SQL injection
- Expose internal errors to users

**Always:**
- Validate user input
- Use parameterized queries
- Hash passwords with bcrypt
- Use environment variables for secrets
- Check for security issues

```bash
# Security scan
make security
```

---

## 🧪 Testing Guidelines

### Test Coverage

- **Target**: 80%+ coverage
- **Current**: 40%+ (improving)

```bash
# Run tests with coverage
make test-coverage

# View coverage report
open htmlcov/index.html
```

### Writing Tests

**Test file naming:**
- `test_*.py` for test files
- `test_<module_name>.py` for module tests

**Test structure:**

```python
"""
Unit Tests for Advanced Rate Limiter
Sprint 7: Test Coverage

Tests for Redis-based distributed rate limiting.
"""
import pytest
from unittest.mock import Mock, AsyncMock

from core.advanced_rate_limiter import AdvancedRateLimiter, UserTier


@pytest.fixture
def rate_limiter():
    """Create rate limiter instance."""
    return AdvancedRateLimiter(redis_url="redis://localhost:6379/0")


class TestAdvancedRateLimiter:
    """Test suite for AdvancedRateLimiter."""

    def test_initialization(self, rate_limiter):
        """Test service initialization."""
        assert rate_limiter is not None
        assert rate_limiter.tier_limits[UserTier.FREE]["default"] == 60

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter):
        """Test rate limit check when allowed."""
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123",
            endpoint="/api/v1/test",
            tier=UserTier.FREE
        )

        assert allowed is True
        assert info["limit"] == 60
        assert info["remaining"] <= 60
```

**Test types:**
- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete workflows

**Markers:**
```python
@pytest.mark.fast  # Fast unit tests
@pytest.mark.slow  # Slow integration tests
@pytest.mark.asyncio  # Async tests
@pytest.mark.integration  # Integration tests
```

### Running Tests

```bash
# All tests
make test

# Fast tests only
make test-fast

# Slow/integration tests
make test-slow

# Specific file
pytest tests/unit/test_advanced_rate_limiter.py -v

# Specific test
pytest tests/unit/test_advanced_rate_limiter.py::TestAdvancedRateLimiter::test_initialization -v
```

---

## 💬 Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding tests
- **perf**: Performance improvements
- **chore**: Maintenance tasks

### Examples

**Simple commit:**
```bash
git commit -m "feat: Add user profile analytics endpoint"
```

**Commit with scope:**
```bash
git commit -m "fix(auth): Resolve 2FA token validation issue"
```

**Commit with body:**
```bash
git commit -m "feat(learning-path): Add FSRS algorithm integration

- Implement 17-parameter FSRS model
- Add spaced repetition scheduling
- Update database schema for review tracking

Closes #123"
```

**Breaking change:**
```bash
git commit -m "feat(api)!: Change authentication to JWT

BREAKING CHANGE: Session-based auth replaced with JWT tokens.
All clients must update to use Bearer token authentication."
```

### Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Fix bug" not "Fixes bug")
- First line max 72 characters
- Reference issues/PRs in footer

---

## 🔀 Pull Request Process

### Before Creating PR

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

2. **Run all checks:**
   ```bash
   make ci
   ```

3. **Update documentation** if needed

4. **Add tests** for new features

### Creating PR

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature
   ```

2. **Create PR** on GitHub

3. **Fill out PR template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] All tests passing

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No new warnings
   - [ ] Tests added and passing

   ## Related Issues
   Closes #123
   ```

### PR Title

Follow commit message format:
```
feat: Add user analytics dashboard
fix(auth): Resolve token expiration issue
docs: Update API reference for v2 endpoints
```

---

## 👀 Code Review

### For Contributors

**When receiving feedback:**
- Be open to suggestions
- Ask questions if unclear
- Make requested changes promptly
- Respond to all comments
- Mark conversations as resolved

**Example responses:**
- "Good catch! Fixed in latest commit."
- "Interesting idea. Let me explore that approach."
- "Could you clarify what you mean here?"

### For Reviewers

**What to check:**
- [ ] Code follows style guidelines
- [ ] Changes are well-tested
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations
- [ ] Error handling is appropriate
- [ ] Code is maintainable

**Review guidelines:**
- Be constructive and kind
- Explain the "why" behind suggestions
- Approve small improvements even if not perfect
- Block PRs with security issues or breaking changes

---

## 📊 Sprint Process

We work in 2-week sprints:

### Sprint Planning
- Review backlog
- Assign issues
- Set sprint goals

### Daily Work
- Regular commits
- Frequent testing
- Code reviews

### Sprint Review
- Demo completed work
- Gather feedback
- Update documentation

### Sprint Retrospective
- What went well?
- What can improve?
- Action items

---

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Annual contributor report

Top contributors receive:
- Special Discord role
- Early access to features
- Kiro2 swag

---

## 📞 Getting Help

### Questions?

- **Discord**: [Join our Discord](https://discord.gg/kiro2)
- **GitHub Discussions**: [Start a discussion](https://github.com/yourusername/kiro2/discussions)
- **Email**: [dev@kiro2.com](mailto:dev@kiro2.com)

### Resources

- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/overview.md)
- [Development Setup](setup.md)
- [Code Quality Guide](../reference/code-quality.md)

---

## 🎉 Thank You!

Thank you for contributing to Kiro2! Your efforts help thousands of Turkish students prepare for university entrance exams.

**Happy coding! 🚀**

---

**Questions?** Open an issue or join our [Discord community](https://discord.gg/kiro2).
