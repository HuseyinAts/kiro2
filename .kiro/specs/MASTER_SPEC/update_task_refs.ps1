# PowerShell script to update task requirement references

$filePath = ".kiro/specs/MASTER_SPEC/tasks.md"
$content = Get-Content $filePath -Raw -Encoding UTF8

# Task 53-58: REQ-26.X → REQ-48.X
$content = $content -replace '_Requirements: 26\.(\d+)-26\.(\d+)_', '_Requirements: 48.$1-48.$2_'
$content = $content -replace '_Requirements: 26\.(\d+)_', '_Requirements: 48.$1_'

# Task 59-64: REQ-27.X → REQ-49.X
$content = $content -replace '_Requirements: 27\.(\d+)-27\.(\d+)_', '_Requirements: 49.$1-49.$2_'
$content = $content -replace '_Requirements: 27\.(\d+)_', '_Requirements: 49.$1_'

# Task 76-82: REQ-30.X → REQ-50.X
$content = $content -replace '_Requirements: 30\.(\d+)-30\.(\d+)_', '_Requirements: 50.$1-50.$2_'
$content = $content -replace '_Requirements: 30\.(\d+)_', '_Requirements: 50.$1_'

# Task 83-87: REQ-31.X → REQ-51.X
$content = $content -replace '_Requirements: 31\.(\d+)-31\.(\d+)_', '_Requirements: 51.$1-51.$2_'
$content = $content -replace '_Requirements: 31\.(\d+)_', '_Requirements: 51.$1_'

# Task 88-92: REQ-32.X → REQ-52.X
$content = $content -replace '_Requirements: 32\.(\d+)-32\.(\d+)_', '_Requirements: 52.$1-52.$2_'
$content = $content -replace '_Requirements: 32\.(\d+)_', '_Requirements: 52.$1_'

# Task 93-96: REQ-33.X → REQ-53.X
$content = $content -replace '_Requirements: 33\.(\d+)-33\.(\d+)_', '_Requirements: 53.$1-53.$2_'
$content = $content -replace '_Requirements: 33\.(\d+)_', '_Requirements: 53.$1_'

# Write back
$content | Set-Content $filePath -Encoding UTF8 -NoNewline

Write-Host "✅ Task requirement references updated successfully!" -ForegroundColor Green
Write-Host "Updated mappings:"
Write-Host "  - Task 53-58: REQ-26.X → REQ-48.X (LLM Soru Üretim)"
Write-Host "  - Task 59-64: REQ-27.X → REQ-49.X (Adaptif Test CAT)"
Write-Host "  - Task 76-82: REQ-30.X → REQ-50.X (Disleksi)"
Write-Host "  - Task 83-87: REQ-31.X → REQ-51.X (Diskalkuli)"
Write-Host "  - Task 88-92: REQ-32.X → REQ-52.X (DEHB)"
Write-Host "  - Task 93-96: REQ-33.X → REQ-53.X (OSB)"
