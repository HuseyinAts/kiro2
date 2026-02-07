# Design Document - Disleksi Desteği Tamamlama

## Architecture Overview

Disleksi (okuma güçlüğü) öğrenciler için erişilebilirlik sistemi. Font customization, reading aids, text-to-speech ile %85 user satisfaction sağlar.

## Components

### 1. Font Customizer (frontend/src/features/accessibility/FontCustomizer.tsx)
- **Purpose**: Font özelleştirme
- **Dependencies**: @fontsource/opendyslexic>=5.0.0
- **Key Features**:
  - Font options (OpenDyslexic, Comic Sans, Arial)
  - Size adjustment (14-24px)
  - Weight options (normal, bold)
  - User profile persistence
  - Apply to all text content
  - Sample text preview

### 2. Text Spacing Controller (frontend/src/features/accessibility/TextSpacing.tsx)
- **Purpose**: Metin aralığı ayarlama
- **Dependencies**: None
- **Key Features**:
  - Line spacing (1.5x-2.5x)
  - Word spacing (0.1em-0.5em)
  - Letter spacing (0.05em-0.2em)
  - Paragraph spacing (1.5em-3em)
  - Presets ("Comfortable", "Extra Comfortable")
  - CSS custom properties

### 3. Reading Aids (frontend/src/features/accessibility/ReadingAids.tsx)
- **Purpose**: Okuma yardımcıları
- **Dependencies**: None
- **Key Features**:
  - Reading ruler (highlight current line)
  - Reading mask (dimmed overlay)
  - Focus mode (distraction-free)
  - Syllable highlighting
  - Word highlighting (hover)
  - Customizable color/opacity/height

### 4. Text-to-Speech Engine (frontend/src/features/accessibility/TextToSpeech.tsx)
- **Purpose**: Metinden sese
- **Dependencies**: react-speech-kit>=3.0.0
- **Key Features**:
  - Web Speech API integration
  - Turkish voice options
  - Speech rate (0.5x-2x)
  - Pitch adjustment (0.5-2)
  - Word highlighting (current word)
  - Playback controls (play, pause, stop, skip)

### 5. Color & Contrast Manager (frontend/src/features/accessibility/ColorContrast.tsx)
- **Purpose**: Renk özelleştirme
- **Dependencies**: None
- **Key Features**:
  - Background colors (cream, light blue, light green)
  - High contrast text colors
  - WCAG AA compliance
  - Dyslexia-friendly dark theme
  - Tinted screen filter
  - Color blindness modes

### 6. Content Simplifier (app/services/content/simplifier_service.py)
- **Purpose**: İçerik basitleştirme
- **Dependencies**: nltk>=3.8.0
- **Key Features**:
  - Complex sentence simplification
  - Vocabulary adaptation (synonym replacement)
  - Key points extraction
  - Visual aid addition (icons, images)
  - Hover tooltip definitions
  - Age-appropriate content adjustment

### 7. Progress Tracker (app/services/accessibility/progress_tracker_service.py)
- **Purpose**: Gelişim takibi
- **Dependencies**: matplotlib>=3.8.0
- **Key Features**:
  - Reading time tracking
  - Reading speed (words per minute)
  - Comprehension quiz scoring
  - Progress visualization (charts, graphs)
  - Milestone achievements
  - Weekly summary reports

### 8. Settings Persistence Manager (app/services/accessibility/settings_manager_service.py)
- **Purpose**: Ayar kalıcılığı
- **Dependencies**: None
- **Key Features**:
  - Automatic save on change
  - Load on user login
  - JSON export/import
  - Validation
  - Default values restore
  - Cross-device sync

## Correctness Properties

### Property 1: Font Application Consistency
```python
@given(font=st.sampled_from(['OpenDyslexic', 'Comic Sans', 'Arial']))
def test_font_consistency(font):
    font_customizer.apply(font)
    assert all_text_elements_use_font(font)
```

### Property 2: Spacing Range Validation
```python
@given(line_spacing=st.floats(min_value=1.5, max_value=2.5))
def test_spacing_range(line_spacing):
    text_spacing.set_line_spacing(line_spacing)
    assert 1.5 <= text_spacing.get_line_spacing() <= 2.5
```

### Property 3: Settings Persistence
```python
@given(settings=st.dictionaries(st.text(), st.text()))
def test_settings_persistence(settings):
    settings_manager.save(settings)
    loaded = settings_manager.load()
    assert settings == loaded
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Feature adoption | >= 60% | >= 45% |
| Reading speed improvement | >= 30% | >= 20% |
| Comprehension improvement | >= 25% | >= 15% |
| User satisfaction | >= 85% | >= 75% |
| Settings persistence | 100% | 100% |

## Monitoring

- Feature usage (%)
- Reading speed (WPM)
- Comprehension score (%)
- User satisfaction score
- Settings save/load success rate (%)
