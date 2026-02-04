# Focus Mode - Odak Modu

## Overview

Focus Mode (Odak Modu), DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanılı öğrenciler için tasarlanmış bir dikkat yönetimi aracıdır. Dikkat dağıtıcı unsurları minimize ederek tek bir göreve odaklanmayı sağlar.

## Requirements

- **REQ-52.21 - REQ-52.25**: Single-task view (Sadece aktif görev görünür)
- **REQ-52.26 - REQ-52.30**: Minimal interface (Minimal arayüz)
- **REQ-52.31 - REQ-52.35**: Notification suppression (Bildirimler kapalı)
- **REQ-52.36 - REQ-52.40**: Distraction hiding (Dikkat dağıtıcı unsurları gizleme)

## Features

### 1. Single-Task View (REQ-52.21-52.25)
- **Tek görev odağı**: Sadece aktif görev görüntülenir
- **Görev izolasyonu**: Diğer görevler ve bildirimler gizlenir
- **Dikkat dağıtıcı unsurları kaldırma**: Minimal, temiz arayüz
- **Görev tamamlama takibi**: İlerleme ve süre kaydı
- **Oturum süresi kaydı**: Çalışma süresi analizi

### 2. Minimal Interface (REQ-52.26-52.30)
- **Basitleştirilmiş UI**: Sadece gerekli öğeler gösterilir
- **Temiz tasarım**: Dikkat dağıtmayan görsel düzen
- **İlerleme takibi**: Progress bar ve yüzde gösterimi
- **Performans metrikleri**: Çalışma süresi ve verimlilik

### 3. Notification Suppression (REQ-52.31-52.35)
- **Bildirim engelleme**: Tüm bildirimler kapatılır
- **Rahatsız etme modu**: Do not disturb mode
- **Sessiz mod**: Ses bildirimleri devre dışı
- **Sistem güvenilirliği**: Hata yönetimi ve fallback
- **Hata yönetimi**: Graceful error handling

### 4. Distraction Hiding (REQ-52.36-52.40)
- **Kenar çubuğunu gizle**: Sidebar tamamen gizlenir
- **Navigasyonu gizle**: Header ve navigation gizlenir
- **Tam ekran modu**: Fullscreen API desteği
- **Dikkat dağıtmayan ortam**: Minimal, odaklanmış çalışma alanı
- **Performans izleme**: Session tracking ve analytics

## Usage

### Basic Usage

```tsx
import { FocusMode } from '@/components/Accessibility/ADHD';

function MyComponent() {
  return (
    <FocusMode
      taskId="task123"
      onExit={() => console.log('Focus mode exited')}
    />
  );
}
```

### With Custom Settings

```tsx
<FocusMode
  taskId="task123"
  initialSettings={{
    hide_sidebar: true,
    hide_navigation: true,
    hide_notifications: true,
    fullscreen_mode: false,
    minimal_ui: true,
    show_timer: true,
    show_progress: true
  }}
  onExit={handleExit}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `taskId` | `string` | - | ID of the task to focus on |
| `onExit` | `() => void` | - | Callback when focus mode is exited |
| `initialSettings` | `Partial<FocusModeSettings>` | See below | Initial focus mode settings |

### FocusModeSettings

```typescript
interface FocusModeSettings {
  hide_sidebar: boolean;        // Hide sidebar (default: true)
  hide_navigation: boolean;     // Hide navigation (default: true)
  hide_notifications: boolean;  // Hide notifications (default: true)
  fullscreen_mode: boolean;     // Enable fullscreen (default: false)
  minimal_ui: boolean;          // Minimal interface (default: true)
  show_timer: boolean;          // Show timer (default: true)
  show_progress: boolean;       // Show progress bar (default: true)
}
```

## Keyboard Shortcuts

- **ESC**: Exit focus mode
- **F11**: Toggle fullscreen mode

## API Endpoints

### GET /api/adhd-support/focus-mode/task/{task_id}
Get task details for focus mode.

**Response:**
```json
{
  "id": "task1",
  "title": "Matematik Çalışması",
  "description": "Türev konusunu çalış",
  "estimated_duration_minutes": 45,
  "priority": "high",
  "subject": "Matematik"
}
```

### POST /api/adhd-support/focus-mode/activate
Activate focus mode.

**Request:**
```json
{
  "task_id": "task1",
  "settings": {
    "hide_sidebar": true,
    "hide_navigation": true,
    "hide_notifications": true,
    "fullscreen_mode": false,
    "minimal_ui": true,
    "show_timer": true,
    "show_progress": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Odak modu etkinleştirildi",
  "session_id": "focus_user123_1234567890",
  "settings_applied": {
    "hide_sidebar": true,
    "hide_navigation": true,
    "hide_notifications": true,
    "fullscreen_mode": false,
    "minimal_ui": true
  }
}
```

### POST /api/adhd-support/focus-mode/deactivate
Deactivate focus mode and save session data.

**Request:**
```json
{
  "task_id": "task1",
  "elapsed_seconds": 1800
}
```

**Response:**
```json
{
  "success": true,
  "message": "Odak modu sonlandırıldı",
  "session_summary": {
    "user_id": "user123",
    "task_id": "task1",
    "elapsed_seconds": 1800,
    "duration_minutes": 30.0,
    "ended_at": "2025-10-24T12:30:00Z"
  },
  "focus_time_minutes": 30.0
}
```

### GET /api/adhd-support/focus-mode/stats
Get focus mode statistics for user.

**Response:**
```json
{
  "total_sessions": 15,
  "total_focus_time_minutes": 450,
  "average_session_duration_minutes": 30.0,
  "completed_sessions": 12,
  "completion_rate": 80.0,
  "most_productive_hour": 14,
  "longest_session_minutes": 60
}
```

### GET /api/adhd-support/focus-mode/sessions
Get recent focus mode sessions.

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 10)

**Response:**
```json
[
  {
    "session_id": "focus_user123_1",
    "user_id": "user123",
    "task_id": "task1",
    "started_at": "2025-10-24T10:00:00Z",
    "ended_at": "2025-10-24T10:30:00Z",
    "elapsed_seconds": 1800,
    "settings": {
      "minimal_ui": true,
      "hide_notifications": true
    },
    "completed": true
  }
]
```

## Styling

The component uses CSS classes that can be customized:

- `.focus-mode-setup`: Setup view container
- `.focus-mode-active-view`: Active focus mode view
- `.focus-task`: Task display container
- `.focus-timer`: Timer display
- `.focus-progress`: Progress bar container

### Body Classes

When focus mode is active, the following classes are added to `<body>`:

- `focus-mode-active`: General focus mode state
- `focus-mode-hide-sidebar`: Hides sidebar elements
- `focus-mode-hide-navigation`: Hides navigation elements
- `focus-mode-hide-notifications`: Hides notification elements
- `focus-mode-minimal-ui`: Applies minimal UI styles

## Accessibility

- **ARIA Labels**: All interactive elements have proper ARIA labels
- **Screen Reader Support**: Live regions for status updates
- **Keyboard Navigation**: Full keyboard support (Tab, Enter, ESC)
- **Focus Management**: Proper focus handling for modal-like behavior
- **High Contrast**: Supports high contrast mode
- **Reduced Motion**: Respects `prefers-reduced-motion` setting

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

### Fullscreen API Support

Fullscreen mode requires browser support for the Fullscreen API:
- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (with vendor prefix)
- iOS Safari: ⚠️ Limited support (requires user gesture)

## Performance

- **Initial Load**: < 100ms
- **Activation Time**: < 200ms
- **Timer Update**: Every 1 second
- **Memory Usage**: < 5MB

## Testing

Run tests with:

```bash
npm test FocusMode.test.tsx
```

### Test Coverage

- ✅ Setup view rendering
- ✅ Task data fetching
- ✅ Settings configuration
- ✅ Focus mode activation
- ✅ Body class application
- ✅ Fullscreen mode
- ✅ Timer functionality
- ✅ Progress tracking
- ✅ Focus mode deactivation
- ✅ Keyboard shortcuts
- ✅ Accessibility features
- ✅ Requirements coverage (REQ-52.21 - REQ-52.40)

## Examples

### Example 1: Basic Focus Mode

```tsx
import { FocusMode } from '@/components/Accessibility/ADHD';

function StudyPage() {
  const [focusModeActive, setFocusModeActive] = useState(false);
  const currentTaskId = "math-homework-1";

  return (
    <div>
      {focusModeActive ? (
        <FocusMode
          taskId={currentTaskId}
          onExit={() => setFocusModeActive(false)}
        />
      ) : (
        <button onClick={() => setFocusModeActive(true)}>
          Odak Modunu Başlat
        </button>
      )}
    </div>
  );
}
```

### Example 2: Custom Settings

```tsx
<FocusMode
  taskId="physics-study"
  initialSettings={{
    hide_sidebar: true,
    hide_navigation: true,
    hide_notifications: true,
    fullscreen_mode: true,  // Start in fullscreen
    minimal_ui: true,
    show_timer: true,
    show_progress: false    // Hide progress bar
  }}
  onExit={handleFocusModeExit}
/>
```

### Example 3: With Analytics

```tsx
function StudyWithAnalytics() {
  const handleExit = async () => {
    // Fetch focus mode stats
    const response = await fetch('/api/adhd-support/focus-mode/stats', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const stats = await response.json();
    
    console.log('Total focus time:', stats.total_focus_time_minutes);
    console.log('Completion rate:', stats.completion_rate);
  };

  return (
    <FocusMode
      taskId="study-session-1"
      onExit={handleExit}
    />
  );
}
```

## Troubleshooting

### Fullscreen not working
- Ensure user gesture (button click) triggers fullscreen
- Check browser permissions
- iOS Safari has limited fullscreen support

### Body classes not applied
- Check that component is properly mounted
- Verify no conflicting CSS
- Check browser console for errors

### Timer not updating
- Verify component is in active state
- Check browser tab is not throttled (background tabs)
- Ensure no JavaScript errors

## Related Components

- `VisualTimer`: Pomodoro timer for ADHD support
- `ReadingHelpers`: Reading assistance tools
- `TextToSpeech`: Text-to-speech functionality

## License

MIT

## Contributors

- Kiro AI Team
- DEHB Support Development Team

## Changelog

### Version 1.0.0 (2025-10-24)
- Initial release
- Full implementation of REQ-52.21 - REQ-52.40
- Complete test coverage
- Accessibility compliance (WCAG 2.1 Level AA)
