$body='{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
$authJson = ((Invoke-WebRequest http://localhost:8000/api/v1/auth/giris -Method POST -ContentType "application/json" -Body $body -UseBasicParsing).Content | ConvertFrom-Json)
$t = $authJson.access_token
if (-not $t) { $t = $authJson.token }
$h=@{Authorization="Bearer $t"}
$api = Invoke-RestMethod http://localhost:8000/openapi.json

# Path parametresi olmayan GET endpointleri - kritik olanlar
$targetPaths = @(
  "/api/v1/auth/me",
  "/api/v1/auth/profil",
  "/api/v1/fsrs/due",
  "/api/v1/fsrs/stats",
  "/api/v1/cat/sessions",
  "/api/v1/learning-path/status",
  "/api/v1/learning-path/today",
  "/api/v1/learning-path/weekly",
  "/api/v1/estimate/tyt",
  "/api/v1/admin/dashboard/stats",
  "/api/v1/admin/users",
  "/api/v1/admin/content/questions",
  "/api/v1/gamification/achievements",
  "/api/v1/gamification/leaderboard",
  "/api/v1/gamification/streaks",
  "/api/v1/league/current",
  "/api/v1/placement/status",
  "/api/v1/dag/topics",
  "/api/v1/veli/cocuklar",
  "/api/v1/parent/children",
  "/api/v1/analytics/admin/dashboard",
  "/api/v1/turkish-nlp-chat/health",
  "/api/v1/notifications/list",
  "/api/v1/search/quick",
  "/api/v1/search/health",
  "/api/v1/yks-roadmap/status"
)

$results = @{ok=0; err=@()}
foreach ($path in $targetPaths) {
  try {
    $r = Invoke-WebRequest "http://localhost:8000$path" -Headers $h -UseBasicParsing -ErrorAction Stop
    $results.ok++
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -ne 403 -and $code -ne 404) {
      $results.err += "$code $path"
    } else {
      $results.ok++
    }
  }
}
Write-Host "OK/Expected: $($results.ok)"
Write-Host "Hata (500 vb):"
$results.err | ForEach-Object { Write-Host "  $_" }
