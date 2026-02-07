# KIRO2 Plugin Template

Bu template, KIRO2 Claude Code plugin'leri oluşturmak için başlangıç noktasıdır.

## Dizin Yapısı

```
plugin-template/
├── plugin.json          # Plugin manifest
├── README.md            # Bu dosya
├── CHANGELOG.md         # Değişiklik geçmişi
├── index.py             # Ana giriş noktası
│
├── tools/               # Tool tanımları
│   └── example_tool.py
│
├── skills/              # Skill tanımları
│   └── SKILL.md
│
├── hooks/               # Hook handler'ları
│   ├── post_edit.py
│   └── pre_bash.py
│
├── commands/            # Komut handler'ları
│   └── example.py
│
├── agents/              # Agent tanımları
│   └── example_agent.md
│
├── scripts/             # Lifecycle scriptleri
│   ├── install.py
│   ├── uninstall.py
│   ├── update.py
│   ├── enable.py
│   └── disable.py
│
├── assets/              # Statik dosyalar
├── templates/           # Template dosyaları
├── data/                # Veri dosyaları
└── docs/                # Dokümantasyon
    └── README.md
```

## Başlarken

### 1. Template'i Kopyala

```bash
cp -r .claude/plugins/templates/plugin-template .claude/plugins/installed/my-plugin
```

### 2. plugin.json Güncelle

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  ...
}
```

### 3. Tool Ekle

`tools/example_tool.py` dosyasını düzenle veya yeni tool ekle:

```python
from typing import Any

async def execute(input: str, options: dict | None = None) -> dict[str, Any]:
    """
    Tool implementation.

    Args:
        input: Input text
        options: Optional configuration

    Returns:
        Tool result
    """
    result = f"Processed: {input}"

    return {
        "result": result,
        "metadata": {
            "input_length": len(input),
            "options": options or {}
        }
    }
```

### 4. Skill Tanımla

`skills/SKILL.md` dosyasını düzenle:

```yaml
---
name: my-skill
description: My custom skill
user-invocable: true
context: fork
allowed-tools:
  - Read
  - Grep
---

# My Skill

Skill açıklaması ve kullanım kılavuzu...
```

### 5. Hook Ekle

`hooks/post_edit.py`:

```python
import json
import sys

def handle_hook(event_data: dict) -> int:
    """
    PostToolUse hook handler.

    Args:
        event_data: Hook event data

    Returns:
        Exit code (0=success, 2=blocking error)
    """
    file_path = event_data.get("file_path", "")

    # Validation logic
    if file_path.endswith(".py"):
        # Python file validation
        pass

    return 0

if __name__ == "__main__":
    event_data = json.loads(sys.stdin.read())
    exit_code = handle_hook(event_data)
    sys.exit(exit_code)
```

### 6. Registry'e Ekle

`.claude/plugins/registry.json`:

```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "path": ".claude/plugins/installed/my-plugin",
      "enabled": true,
      "version": "1.0.0"
    }
  ]
}
```

## Plugin Manifest (plugin.json)

### Zorunlu Alanlar

| Alan | Tip | Açıklama |
|------|-----|----------|
| name | string | Unique plugin adı |
| version | string | Semantic versioning (X.Y.Z) |
| description | string | Kısa açıklama |

### Opsiyonel Alanlar

| Alan | Tip | Açıklama |
|------|-----|----------|
| author | string | Yazar bilgisi |
| license | string | Lisans (MIT, Apache-2.0, vb.) |
| main | string | Ana giriş dosyası |
| tools | array | Tool tanımları |
| skills | array | Skill tanımları |
| hooks | array | Hook tanımları |
| commands | array | Komut tanımları |
| agents | array | Agent tanımları |
| dependencies | object | Bağımlılıklar |
| config | object | Yapılandırma şeması |
| permissions | object | Gerekli izinler |

## Lifecycle Hooks

Plugin lifecycle olayları için script'ler:

### onInstall

Plugin yüklendiğinde çalışır:

```python
# scripts/install.py
def on_install(config: dict) -> bool:
    print("Plugin installing...")
    # Initialization logic
    return True
```

### onUninstall

Plugin kaldırıldığında çalışır:

```python
# scripts/uninstall.py
def on_uninstall(config: dict) -> bool:
    print("Plugin uninstalling...")
    # Cleanup logic
    return True
```

### onUpdate

Plugin güncellendiğinde çalışır:

```python
# scripts/update.py
def on_update(old_version: str, new_version: str) -> bool:
    print(f"Updating from {old_version} to {new_version}")
    # Migration logic
    return True
```

## Best Practices

1. **Semantic Versioning**: MAJOR.MINOR.PATCH formatını kullan
2. **Type Hints**: Tüm fonksiyonlarda type hint kullan
3. **Documentation**: Her tool ve skill için dokümantasyon yaz
4. **Error Handling**: Hataları düzgün yakala ve raporla
5. **Testing**: Testler yaz ve coverage sağla
6. **Permissions**: Minimum gerekli izinleri iste

## KIRO2 Spesifik

KIRO2 platformuna özel plugin'ler için:

### IRT Tool Örneği

```python
@register_tool("irt-custom")
async def irt_custom(difficulty: float, ability: float) -> dict:
    # Parametre validasyonu
    if not -4.0 <= difficulty <= 4.0:
        raise ValueError("difficulty must be in [-4.0, 4.0]")

    # IRT hesaplama
    probability = calculate_irt(difficulty, ability)

    return {"probability": probability}
```

### Turkish NLP Skill

```yaml
---
name: turkish-custom
skills: [turkish-nlp]  # Bağımlılık
---

# Custom Turkish Processing

Zemberek entegrasyonu ile özel Türkçe işleme...
```

## Yardım

- [Claude Code Plugin Docs](https://docs.anthropic.com/claude-code/plugins)
- [KIRO2 Plugin API](https://github.com/kiro2/plugin-api)
- [Example Plugins](https://github.com/kiro2/example-plugins)
