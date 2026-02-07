# Requirements Document - GitHub MCP Sistemi

## Introduction

Bu spec, GitHub API entegrasyonunu MCP server üzerinden sağlayan sistemi tanımlar. Issue, PR, commit, release yönetimi %500 kolaylaşır.

## Glossary

- **GitHub MCP**: GitHub MCP server
- **Octokit**: GitHub API client
- **GraphQL**: GitHub GraphQL API
- **Webhook**: GitHub event notification
- **GitHub Actions**: CI/CD workflow

## Requirements

### Requirement 1: Repository Operations
**User Story:** As a developer, I want repository işlemleri yapmak, so that proje yönetimi yapabiliyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN repo oluşturulduğunda, THE System SHALL GitHub API ile repo create eder
2. **REQ-1.2** WHEN repo settings güncellendiğinde, THE System SHALL description, topics, visibility günceller
3. **REQ-1.3** WHEN repo clone edildiğinde, THE System SHALL git clone + submodule init yapar
4. **REQ-1.4** WHEN repo fork edildiğinde, THE System SHALL upstream tracking ayarlar
5. **REQ-1.5** WHEN repo archive edildiğinde, THE System SHALL read-only mode aktif eder
6. **REQ-1.6** WHEN repo delete edildiğinde, THE System SHALL confirmation + backup ister

### Requirement 2: Issue Management
**User Story:** As a project manager, I want issue yönetimi yapmak, so that task tracking yapabiliyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN issue oluşturulduğunda, THE System SHALL title, body, labels, assignees ekler
2. **REQ-2.2** WHEN issue search yapıldığında, THE System SHALL GitHub search API kullanır
3. **REQ-2.3** WHEN issue filter uygulandığında, THE System SHALL state, label, assignee, milestone filtreler
4. **REQ-2.4** WHEN issue comment eklendiğinde, THE System SHALL markdown formatting destekler
5. **REQ-2.5** WHEN issue close edildiğinde, THE System SHALL close reason (completed/not planned) belirtir
6. **REQ-2.6** WHEN issue link edildiğinde, THE System SHALL related issues/PRs bağlar

### Requirement 3: Pull Request Workflow
**User Story:** As a developer, I want PR workflow yönetmek, so that code review yapabiliyim.
#### Acceptance Criteria
1. **REQ-3.1** WHEN PR oluşturulduğunda, THE System SHALL branch, title, description, reviewers ekler
2. **REQ-3.2** WHEN PR review yapıldığında, THE System SHALL approve/request changes/comment destekler
3. **REQ-3.3** WHEN PR merge edildiğinde, THE System SHALL merge strategy (merge/squash/rebase) seçer
4. **REQ-3.4** WHEN PR conflict tespit edildiğinde, THE System SHALL conflict files listeler
5. **REQ-3.5** WHEN PR status check yapıldığında, THE System SHALL CI/CD status gösterir
6. **REQ-3.6** WHEN PR auto-merge ayarlandığında, THE System SHALL checks pass sonrası merge eder

### Requirement 4: Commit ve Branch Operations
**User Story:** As a developer, I want commit/branch işlemleri yapmak, so that version control yapabiliyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN commit history alındığında, THE System SHALL git log ile commit list döner
2. **REQ-4.2** WHEN commit detail görüntülendiğinde, THE System SHALL diff, files changed, stats gösterir
3. **REQ-4.3** WHEN branch oluşturulduğunda, THE System SHALL base branch'ten yeni branch oluşturur
4. **REQ-4.4** WHEN branch delete edildiğinde, THE System SHALL merged branch check yapar
5. **REQ-4.5** WHEN branch protection ayarlandığında, THE System SHALL required reviews, status checks ekler
6. **REQ-4.6** WHEN commit search yapıldığında, THE System SHALL author, message, date filtreler

### Requirement 5: Release Management
**User Story:** As a release manager, I want release yönetimi yapmak, so that versioning yapabiliyim.
#### Acceptance Criteria
1. **REQ-5.1** WHEN release oluşturulduğunda, THE System SHALL tag, name, body, assets ekler
2. **REQ-5.2** WHEN semantic versioning uygulandığında, THE System SHALL major/minor/patch increment yapar
3. **REQ-5.3** WHEN changelog generate edildiğinde, THE System SHALL conventional commits parse eder
4. **REQ-5.4** WHEN release asset upload edildiğinde, THE System SHALL binary/archive files destekler
5. **REQ-5.5** WHEN pre-release işaretlendiğinde, THE System SHALL beta/rc tag ekler
6. **REQ-5.6** WHEN release publish edildiğinde, THE System SHALL notification gönderir

### Requirement 6: GitHub Actions Integration
**User Story:** As a DevOps engineer, I want GitHub Actions yönetmek, so that CI/CD pipeline çalıştırayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN workflow trigger edildiğinde, THE System SHALL workflow_dispatch event gönderir
2. **REQ-6.2** WHEN workflow status sorgulandığında, THE System SHALL run status (queued/in_progress/completed) döner
3. **REQ-6.3** WHEN workflow logs alındığında, THE System SHALL step-by-step logs gösterir
4. **REQ-6.4** WHEN workflow cancel edildiğinde, THE System SHALL running jobs'ı durdurur
5. **REQ-6.5** WHEN workflow re-run yapıldığında, THE System SHALL failed jobs'ı yeniden çalıştırır
6. **REQ-6.6** WHEN workflow artifact download edildiğinde, THE System SHALL zip file indirir

### Requirement 7: Webhook Management
**User Story:** As a developer, I want webhook yönetmek, so that event-driven automation yapabiliyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN webhook oluşturulduğunda, THE System SHALL URL, events, secret ekler
2. **REQ-7.2** WHEN webhook event geldiğinde, THE System SHALL signature verification yapar
3. **REQ-7.3** WHEN webhook payload parse edildiğinde, THE System SHALL event type'a göre handler çağırır
4. **REQ-7.4** WHEN webhook delivery check yapıldığında, THE System SHALL success/failure status gösterir
5. **REQ-7.5** WHEN webhook redeliver yapıldığında, THE System SHALL failed delivery'yi yeniden gönderir
6. **REQ-7.6** WHEN webhook delete edildiğinde, THE System SHALL active subscriptions'ı temizler

### Requirement 8: GraphQL API Usage
**User Story:** As a developer, I want GraphQL API kullanmak, so that efficient data fetching yapabiliyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN GraphQL query çalıştığında, THE System SHALL GitHub GraphQL endpoint kullanır
2. **REQ-8.2** WHEN nested data fetch edildiğinde, THE System SHALL single request ile tüm data alır
3. **REQ-8.3** WHEN pagination yapıldığında, THE System SHALL cursor-based pagination kullanır
4. **REQ-8.4** WHEN rate limit kontrol edildiğinde, THE System SHALL remaining quota gösterir
5. **REQ-8.5** WHEN mutation yapıldığında, THE System SHALL optimistic update destekler
6. **REQ-8.6** WHEN query cache'lendiğinde, THE System SHALL 5 dakika TTL kullanır

## Bağımlılıklar
- **PyGithub**: GitHub REST API client
- **gql**: GraphQL client
- **GitPython**: Git operations
- **cryptography**: Webhook signature verification

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Workflow İyileşmesi:** %500

## Success Metrics
1. **API Success Rate:** >= %99
2. **Webhook Delivery Rate:** >= %98
3. **GraphQL Query Efficiency:** %300 improvement
4. **Developer Productivity:** %500 increase
5. **Automation Coverage:** >= %80

