# Path Naming Drift Report — 2026-04-10

**Source:** http://localhost:8000/openapi.json
**Backend paths:** 1074
**Frontend fetch sites:** 144
**Unique frontend paths:** 129

## 1. TR/EN Duplicate Implementations (backend)

Both Turkish and English variants exist in OpenAPI. Frontend must guess.
Goal: drive this section to empty by removing the legacy Turkish variant.

_None — clean._

## 2. Turkish-Only Backend Paths (no English equivalent)

These exist only in Turkish form. Either rename to English or add
to `TR_ALLOWLIST` if they are intentional product names.

- `/api/v1/auth/profil`
- `/api/v1/ogretmen/bildirim`
- `/api/v1/ogretmen/bildirim/{bildirim_id}/okundu`
- `/api/v1/ogretmen/bildirimler`
- `/api/v1/ogretmen/dashboard`
- `/api/v1/ogretmen/istatistikler`
- `/api/v1/ogretmen/ogrenci/{ogrenci_id}/performans`
- `/api/v1/ogretmen/ogrenciler`
- `/api/v1/ogretmen/rapor/sinif`
- `/api/v1/ogretmen/rapor/{rapor_id}`
- `/api/v1/ogretmen/raporlar`
- `/api/v1/student-dashboard/bildirimler`
- `/api/v1/student-dashboard/istatistikler`
- `/api/v1/student-dashboard/profil`
- `/api/v1/veli/bildirimler`
- `/api/v1/veli/bildirimler/{bildirim_id}/okundu`
- `/api/v1/veli/cocuk/{ogrenci_id}/haftalik-rapor`
- `/api/v1/veli/cocuk/{ogrenci_id}/performans`
- `/api/v1/veli/cocuklar`
- `/api/v1/veli/istatistikler`
- `/api/v1/veli/onay-talebi-olustur`
- `/api/v1/veli/onay-talepleri`
- `/api/v1/veli/onay-talepleri/{talep_id}/yanitla`
- `/api/v1/zpd-maarif/gecmis/{ogrenci_id}`
- `/api/v1/zpd-maarif/hesapla`
- `/api/v1/zpd-maarif/istatistikler/{ogrenci_id}`
- `/api/v1/zpd-maarif/profil/kulturel/{ogrenci_id}`
- `/api/v1/zpd-maarif/profil/maarif/{ogrenci_id}`
- `/istatistikler`
- `/konular`
- `/soru/{soru_id}`
- `/sorular`

## 3. Frontend 404 Risk (fetch → missing endpoint)

Frontend calls a path that is NOT in the backend OpenAPI.
Either the endpoint was removed/renamed or the frontend has a typo.

- `/api/data`
  - frontend\src\lib\retryUtils.ts:37
  - frontend\src\lib\retryUtils.ts:126
  - frontend\src\lib\retryUtils.ts:245
- `/api/sync/analytics`
  - frontend\src\sw.ts:292
- `/api/sync/exam-results`
  - frontend\src\sw.ts:271
- `/api/v1/adhd-task-management/tasks/{x}/progress`
  - frontend\src\components\Accessibility\ADHD\TaskProgressVisualization.tsx:75
- `/api/v1/admin/content/questions/{x}/approve`
  - frontend\src\components\Admin\ContentManagement.tsx:275
- `/api/v1/admin/content/questions/{x}/reject`
  - frontend\src\components\Admin\ContentManagement.tsx:293
- `/api/v1/admin/dashboard`
  - frontend\src\.migration-backup\pages\AdminDashboardPage.tsx_20251118_174751.bak:50
- `/api/v1/admin/settings`
  - frontend\src\pages\ModernAdminSettingsPage.tsx:76
- `/api/v1/batch/queue/active`
  - frontend\src\components\Admin\BatchQueueMonitor.tsx:110
- `/api/v1/manipulatives/badges`
  - frontend\src\components\Manipulatives\ManipulativesProgressDashboard.tsx:91
- `/api/v1/manipulatives/progress/dashboard`
  - frontend\src\components\Manipulatives\ManipulativesProgressDashboard.tsx:78
- `/api/v1/monitoring/ab-test-results`
  - frontend\src\pages\ABTestResultsPage.tsx:105
- `/api/v1/monitoring/export-csv`
  - frontend\src\pages\TokenOptimizationDashboard.tsx:115
- `/api/v1/monitoring/token-stats`
  - frontend\src\pages\TokenOptimizationDashboard.tsx:89
- `/api/v1/multisensory/animations/demo/control`
  - frontend\src\components\Revolutionary\MultisensoryLearning.tsx:46
- `/api/v1/multisensory/animations/demo/speed`
  - frontend\src\components\Revolutionary\MultisensoryLearning.tsx:63
- `/api/v1/osym/generate-question`
  - frontend\src\pages\OSYMQuestionGeneratorPage.tsx:96
- `/api/v1/parent/children/{x}/weekly-reports`
  - frontend\src\.migration-backup\pages\ParentChildrenPage.tsx_20251118_174751.bak:96
- `/api/v1/parsed-questions`
  - frontend\src\components\QuestionParser\QuestionReviewDashboard.tsx:79
- `/api/v1/parsed-questions/stats`
  - frontend\src\components\QuestionParser\QuestionReviewDashboard.tsx:89
- `/api/v1/parsed-questions/{x}`
  - frontend\src\components\QuestionParser\QuestionReviewDashboard.tsx:115
- `/api/v1/parsed-questions/{x}/verify`
  - frontend\src\components\QuestionParser\QuestionReviewDashboard.tsx:98
- `/api/v1/questions/{x}/solutions`
  - frontend\src\components\MathSolution\AlternativeSolutionsViewer.tsx:80
- `/api/v1/questions/{x}/solutions/{x}/vote`
  - frontend\src\components\MathSolution\AlternativeSolutionsViewer.tsx:134
- `/api/v1/study-rooms`
  - frontend\src\components\StudyRooms\StudyRoomList.tsx:163
- `/api/v1/study-rooms/{x}`
  - frontend\src\components\StudyRooms\StudyRoomView.tsx:103
  - frontend\src\components\StudyRooms\StudyRoomView.tsx:146
- `/api/v1/study-rooms/{x}/archive`
  - frontend\src\components\StudyRooms\StudyRoomView.tsx:134
- `/api/v1/study-rooms/{x}/files`
  - frontend\src\components\StudyRooms\FileManager.tsx:126
- `/api/v1/study-rooms/{x}/files/upload`
  - frontend\src\components\StudyRooms\FileManager.tsx:167
- `/api/v1/study-rooms/{x}/files/{x}`
  - frontend\src\components\StudyRooms\FileManager.tsx:216
- `/api/v1/study-rooms/{x}/files/{x}/download`
  - frontend\src\components\StudyRooms\FileManager.tsx:196
- `/api/v1/study-rooms/{x}/files/{x}/versions`
  - frontend\src\components\StudyRooms\FileManager.tsx:227
- `/api/v1/study-rooms/{x}/join`
  - frontend\src\components\StudyRooms\StudyRoomList.tsx:185
  - frontend\src\components\StudyRooms\StudyRoomList.tsx:187
- `/api/v1/study-rooms/{x}/leave`
  - frontend\src\components\StudyRooms\StudyRoomView.tsx:123
- `/api/v1/study-rooms/{x}/members`
  - frontend\src\components\StudyRooms\StudyRoomView.tsx:112
- `/api/v1/study-rooms/{x}/messages`
  - frontend\src\components\StudyRooms\ChatInterface.tsx:115
  - frontend\src\components\StudyRooms\ChatInterface.tsx:155
  - frontend\src\components\StudyRooms\ChatInterface.tsx:192
- `/api/v1/study-rooms/{x}/messages/{x}`
  - frontend\src\components\StudyRooms\ChatInterface.tsx:244
- `/api/v1/study-rooms/{x}/messages/{x}/reaction`
  - frontend\src\components\StudyRooms\ChatInterface.tsx:204
- `/api/v1/study-rooms/{x}/upload`
  - frontend\src\components\StudyRooms\ChatInterface.tsx:178
- `/api/v1/study-rooms/{x}/video/join`
  - frontend\src\components\StudyRooms\VideoConference\VideoConference.tsx:193
- `/api/v1/study-rooms/{x}/video/leave`
  - frontend\src\components\StudyRooms\VideoConference\VideoConference.tsx:349
- `/api/v1/study-rooms/{x}/video/start-recording`
  - frontend\src\components\StudyRooms\VideoConference\VideoConference.tsx:336
- `/api/v1/study-rooms/{x}/video/stop-recording`
  - frontend\src\components\StudyRooms\VideoConference\VideoConference.tsx:339
- `/api/v1/study-rooms/{x}/whiteboard/clear`
  - frontend\src\components\StudyRooms\Whiteboard\WhiteboardSync.tsx:203
- `/api/v1/study-rooms/{x}/whiteboard/equation`
  - frontend\src\components\StudyRooms\Whiteboard\WhiteboardSync.tsx:191
- `/api/v1/study-rooms/{x}/whiteboard/shape`
  - frontend\src\components\StudyRooms\Whiteboard\WhiteboardSync.tsx:165
- `/api/v1/study-rooms/{x}/whiteboard/stroke`
  - frontend\src\components\StudyRooms\Whiteboard\WhiteboardSync.tsx:152
- `/api/v1/study-rooms/{x}/whiteboard/text`
  - frontend\src\components\StudyRooms\Whiteboard\WhiteboardSync.tsx:178
- `/api/v1/user/clear-cache`
  - frontend\src\.migration-backup\pages\SettingsPage.tsx_20251118_174751.bak:113
- `/api/v1/user/delete-account`
  - frontend\src\.migration-backup\pages\SettingsPage.tsx_20251118_174751.bak:145
- `/api/v1/user/export-data`
  - frontend\src\.migration-backup\pages\SettingsPage.tsx_20251118_174751.bak:75

**Total drift items:** 51