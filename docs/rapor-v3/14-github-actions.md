# BÖLÜM 14: GitHub Actions Entegrasyonu

## 14.1 Genel Bakış

### Claude Code + GitHub Actions

GitHub Actions, Claude Code'u CI/CD pipeline'larına entegre etmenizi sağlar. Bu entegrasyon ile:
- Otomatik code review
- PR açıklaması oluşturma
- Bug fix önerileri
- Dokümantasyon güncelleme
- Test yazma

### Resmi Action

**Repository:** `anthropics/claude-code-action`

**Özellikler:**
- GitHub-hosted runner desteği
- Self-hosted runner desteği
- PR ve Issue tetikleme
- Direct invocation

---

## 14.2 Kurulum

### Temel Workflow

```yaml
# .github/workflows/claude-code.yml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      pull-requests: write
      issues: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Run Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          trigger_phrase: "@claude"
          timeout_minutes: 10
```

### Secrets Yapılandırması

**GitHub Repository Settings → Secrets → Actions:**

| Secret | Açıklama |
|--------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key |

### Permissions

```yaml
permissions:
  contents: read        # Kod okuma
  pull-requests: write  # PR yorumlama
  issues: write         # Issue yorumlama
  actions: read         # Workflow okuma
```

---

## 14.3 Tetikleme Yöntemleri

### 1. PR Açılışında Otomatik

```yaml
on:
  pull_request:
    types: [opened]

jobs:
  auto-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review this PR for:
            - Code quality
            - Security issues
            - Test coverage
            
            Provide specific, actionable feedback.
```

### 2. Mention ile Tetikleme

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  mention-triggered:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          trigger_phrase: "@claude"
```

**Kullanım:**
```
@claude Please review this code for security vulnerabilities
```

### 3. Label ile Tetikleme

```yaml
on:
  pull_request:
    types: [labeled]

jobs:
  label-triggered:
    if: github.event.label.name == 'needs-review'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Perform thorough code review"
```

### 4. Scheduled Review

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Her Pazartesi 09:00

jobs:
  weekly-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Analyze the codebase for:
            - Technical debt
            - Deprecated dependencies
            - Security vulnerabilities
            - Documentation gaps
```

---

## 14.4 Action Parametreleri

### Tam Parametre Listesi

| Parametre | Zorunlu | Varsayılan | Açıklama |
|-----------|---------|------------|----------|
| `anthropic_api_key` | ✅ | - | API key |
| `prompt` | ❌ | Auto | Custom prompt |
| `trigger_phrase` | ❌ | `@claude` | Tetikleme ifadesi |
| `model` | ❌ | `claude-sonnet-4-5-20250929` | Model |
| `timeout_minutes` | ❌ | `10` | Timeout |
| `max_tokens` | ❌ | `4096` | Max output token |
| `allowed_tools` | ❌ | All | Tool whitelist |
| `disallowed_tools` | ❌ | None | Tool blacklist |

### Örnek Konfigürasyonlar

**Güvenlik odaklı:**
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    model: claude-opus-4-5-20251101
    prompt: |
      Perform security audit focusing on:
      - SQL injection
      - XSS vulnerabilities
      - Authentication bypasses
      - Sensitive data exposure
    allowed_tools: "Read,Grep,Glob"
    timeout_minutes: 15
```

**Hızlı review:**
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    model: claude-haiku-4-5-20251001
    prompt: "Quick review for obvious issues"
    timeout_minutes: 5
    max_tokens: 1024
```

---

## 14.5 KIRO2 Workflow'ları

### PR Review Workflow

```yaml
# .github/workflows/pr-review.yml
name: KIRO2 PR Review

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'orchestrator/**'
      - 'backend/**'
      - 'tests/**'

jobs:
  code-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@v41
        with:
          files: |
            **/*.py
            **/*.ts
            **/*.tsx
      
      - name: Claude Review
        if: steps.changed-files.outputs.any_changed == 'true'
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-sonnet-4-5-20250929
          prompt: |
            Review this PR for KIRO2 project standards:
            
            ## Code Quality
            - Type hints for all functions
            - Google-style docstrings
            - Error handling patterns
            
            ## Security
            - No hardcoded credentials
            - Input validation
            - SQL injection prevention
            
            ## KIRO2 Specific
            - UTF-8 encoding for Turkish content
            - PostgreSQL on port 5434
            - Question format compliance
            
            Changed files: ${{ steps.changed-files.outputs.all_changed_files }}
            
            Provide specific line-by-line feedback.
          timeout_minutes: 10

  security-scan:
    runs-on: ubuntu-latest
    needs: code-review
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Security Audit
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-opus-4-5-20251101
          prompt: |
            Security audit for authentication and data handling:
            - Check for SQL injection in orchestrator/
            - Verify API key handling
            - Review rate limiting implementation
          allowed_tools: "Read,Grep,Glob"
          timeout_minutes: 15
```

### Soru Doğrulama Workflow

```yaml
# .github/workflows/question-validation.yml
name: Question Validation

on:
  push:
    paths:
      - 'd-dataset/questions/**/*.json'

jobs:
  validate-questions:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install jsonschema sentence-transformers
      
      - name: Schema Validation
        run: |
          python scripts/validate_questions.py d-dataset/questions/
      
      - name: Claude Content Review
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review the new/modified questions in d-dataset/questions/:
            
            1. Pedagogical quality
            2. Difficulty appropriateness
            3. Turkish grammar and spelling
            4. LaTeX syntax correctness
            5. Distractor plausibility
            
            Flag any issues that need human review.
          timeout_minutes: 10
```

### Dokümantasyon Sync

```yaml
# .github/workflows/docs-sync.yml
name: Documentation Sync

on:
  push:
    branches: [main]
    paths:
      - 'orchestrator/**/*.py'
      - 'backend/**/*.py'

jobs:
  update-docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate API Docs
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Update documentation for changed Python files:
            
            1. Extract docstrings and type hints
            2. Generate API reference in docs/api/
            3. Update README if public interfaces changed
            
            Create a PR with the changes.
          allowed_tools: "Read,Write,Bash,Glob"
          timeout_minutes: 15
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "docs: Auto-update API documentation"
          commit-message: "docs: Update API documentation"
          branch: docs/auto-update
```

---

## 14.6 Matrix Builds

### Çoklu Modül Test

```yaml
name: Multi-Module Review

on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        module: [orchestrator, backend, frontend]
        include:
          - module: orchestrator
            focus: "AI workflows and state management"
          - module: backend
            focus: "API endpoints and database"
          - module: frontend
            focus: "React components and UX"
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Review ${{ matrix.module }}
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review the ${{ matrix.module }} module focusing on:
            ${{ matrix.focus }}
            
            Path: ${{ matrix.module }}/
          timeout_minutes: 10
```

---

## 14.7 Artifact Handling

### Review Raporu Kaydetme

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Claude Review
        id: review
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Generate detailed code review report"
      
      - name: Save Report
        run: |
          echo "${{ steps.review.outputs.response }}" > review-report.md
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: review-report
          path: review-report.md
          retention-days: 30
```

### Önceki Artifact'ı Kullanma

```yaml
jobs:
  compare:
    runs-on: ubuntu-latest
    
    steps:
      - name: Download Previous Report
        uses: actions/download-artifact@v4
        with:
          name: review-report
          path: previous/
        continue-on-error: true
      
      - name: Compare with Previous
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Compare current code with previous review in previous/review-report.md
            Identify:
            - Addressed issues
            - New issues
            - Recurring patterns
```

---

## 14.8 Self-Hosted Runner

### Runner Kurulumu

```bash
# GitHub Runner kurulumu (Linux)
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/USER/REPO --token YOUR_TOKEN
./run.sh
```

### Self-Hosted Workflow

```yaml
jobs:
  review:
    runs-on: self-hosted
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Claude Review (Self-Hosted)
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # Self-hosted avantajı: lokal resources
          prompt: |
            Review code using local database for context.
            Database: postgresql://localhost:5434/kiro2
```

---

## 14.9 Maliyet Yönetimi

### Token Limitleri

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          max_tokens: 2048  # Output limit
          timeout_minutes: 5  # Time limit
          model: claude-haiku-4-5-20251001  # Cost-effective model
```

### Conditional Execution

```yaml
jobs:
  review:
    # Sadece önemli değişikliklerde çalış
    if: |
      github.event.pull_request.additions > 50 ||
      github.event.pull_request.deletions > 50
    
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Günlük Limit

```yaml
jobs:
  check-budget:
    runs-on: ubuntu-latest
    outputs:
      within_budget: ${{ steps.check.outputs.within_budget }}
    
    steps:
      - id: check
        run: |
          # Günlük review sayısını kontrol et
          TODAY=$(date +%Y-%m-%d)
          COUNT=$(gh api repos/${{ github.repository }}/actions/runs \
            --jq "[.workflow_runs[] | select(.created_at | startswith(\"$TODAY\"))] | length")
          
          if [ $COUNT -lt 20 ]; then
            echo "within_budget=true" >> $GITHUB_OUTPUT
          else
            echo "within_budget=false" >> $GITHUB_OUTPUT
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  
  review:
    needs: check-budget
    if: needs.check-budget.outputs.within_budget == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        # ...
```

---

## 14.10 Özet

### Checklist

- [ ] `ANTHROPIC_API_KEY` secret eklendi
- [ ] Workflow dosyası oluşturuldu
- [ ] Permissions yapılandırıldı
- [ ] Tetikleme kuralları belirlendi
- [ ] Maliyet limitleri ayarlandı
- [ ] Matrix builds yapılandırıldı (gerekirse)

### Quick Reference

```yaml
# Minimal setup
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Review accuracy | > 90% |
| False positive rate | < 10% |
| Average runtime | < 5 min |
| Daily cost | < $10 |

---

**Önceki Bölüm:** [13 - Claude Agent SDK](./13-claude-agent-sdk.md)  
**Sonraki Bölüm:** [15 - LangGraph Entegrasyonu](./15-langgraph-entegrasyonu.md)
