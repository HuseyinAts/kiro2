# Learning Path Configuration Usage Guide

## Overview

The `config.py` module provides centralized configuration for all learning path components. It consolidates scattered configuration values into a single, immutable, thread-safe configuration object.

## Quick Start

```python
from agents.learning_path.config import config

# Access configuration values directly
redis_url = config.CACHE_REDIS_URL
rate_limit = config.RATE_LIMIT_CREATE_PATH
```

## Usage Examples

### 1. Basic Usage (Recommended)

```python
from agents.learning_path import config

# Cache settings
cache_url = config.CACHE_REDIS_URL
cache_ttl = config.CACHE_DEFAULT_TTL

# Rate limits
create_path_limit = config.RATE_LIMIT_CREATE_PATH
search_limit = config.RATE_LIMIT_SEARCH_RESOURCES

# IRT/ZPD parameters
zpd_min = config.ZPD_SUCCESS_PROB_MIN
zpd_max = config.ZPD_SUCCESS_PROB_MAX
```

### 2. Function-Based Access

```python
from agents.learning_path import get_learning_path_config

config = get_learning_path_config()
print(f"Redis URL: {config.CACHE_REDIS_URL}")
```

### 3. Class Import (Advanced)

```python
from agents.learning_path import LearningPathConfig

# For type hints in function signatures
def my_function(config: LearningPathConfig) -> None:
    print(config.CACHE_REDIS_URL)
```

## Configuration Groups

### Cache Settings

```python
config.CACHE_REDIS_URL           # "redis://localhost:6379/0"
config.CACHE_L1_MAX_SIZE         # 20
config.CACHE_DEFAULT_TTL         # 300 seconds
config.PROFILE_CACHE_TTL         # 1800 seconds
config.RESOURCE_CACHE_TTL        # 3600 seconds
```

### Rate Limits

```python
config.RATE_LIMIT_CREATE_PROFILE    # "10/minute"
config.RATE_LIMIT_CREATE_PATH       # "5/minute"
config.RATE_LIMIT_SEARCH_RESOURCES  # "30/minute"
config.RATE_LIMIT_DEFAULT           # "60/minute"
```

### Circuit Breaker

```python
config.CB_FAILURE_THRESHOLD      # 5
config.CB_RECOVERY_TIMEOUT       # 30 seconds
config.CB_MAX_RETRY_ATTEMPTS     # 3
```

### Search Settings

```python
config.MAX_RESOURCES_PER_SEARCH  # 20
config.DEFAULT_VIDEO_DURATION    # 10 minutes
config.SEARCH_TIMEOUT            # 30 seconds
```

### IRT/ZPD Parameters

```python
config.ZPD_SUCCESS_PROB_MIN      # 0.15
config.ZPD_SUCCESS_PROB_MAX      # 0.85
config.IRT_DIFFICULTY_MIN        # -4.0
config.IRT_DIFFICULTY_MAX        # 4.0
config.IRT_DISCRIMINATION_MIN    # 0.2
config.IRT_DISCRIMINATION_MAX    # 4.0
```

### Feature Flags

```python
config.ENABLE_REDIS_CACHE               # true
config.ENABLE_CIRCUIT_BREAKER           # true
config.ENABLE_RESOURCE_RANKING          # true
config.ENABLE_LEARNING_STYLE_DETECTION  # true
```

## Environment Variables

All configuration values can be overridden via environment variables:

```bash
# Cache settings
export REDIS_URL="redis://production:6379/0"
export LEARNING_PATH_CACHE_L1_SIZE="50"
export LEARNING_PATH_CACHE_TTL="600"

# Feature flags
export ENABLE_REDIS_CACHE="true"
export ENABLE_CIRCUIT_BREAKER="true"
export LEARNING_PATH_VERBOSE_LOGGING="true"
```

## Key Features

### 1. Immutability

Configuration is frozen and cannot be modified at runtime:

```python
config.CACHE_REDIS_URL = "new_value"  # ❌ Raises FrozenInstanceError
```

### 2. Singleton Pattern

Only one instance exists throughout the application:

```python
from agents.learning_path import config, get_learning_path_config

config1 = config
config2 = get_learning_path_config()

assert config1 is config2  # ✅ Same instance
```

### 3. Thread-Safe

Safe to use in multi-threaded environments (FastAPI async handlers).

### 4. Type-Safe

All values have proper type annotations:

```python
config.CACHE_L1_MAX_SIZE      # int
config.CACHE_REDIS_URL        # str
config.ZPD_SUCCESS_PROB_MIN   # float
config.ENABLE_REDIS_CACHE     # bool
```

## Migration from Old Pattern

### Before (Scattered Config)

```python
# Old pattern - config scattered everywhere
CACHE_TTL = 300
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT = "5/minute"
```

### After (Centralized Config)

```python
# New pattern - centralized config
from agents.learning_path import config

cache_ttl = config.CACHE_DEFAULT_TTL
redis_url = config.CACHE_REDIS_URL
rate_limit = config.RATE_LIMIT_CREATE_PATH
```

## Best Practices

1. **Import at module level** for better performance:
   ```python
   from agents.learning_path import config

   # Use config throughout module
   def my_function():
       return config.CACHE_REDIS_URL
   ```

2. **Use type hints** for clarity:
   ```python
   from agents.learning_path import LearningPathConfig

   def setup_cache(config: LearningPathConfig) -> None:
       ...
   ```

3. **Don't modify config** - it's immutable for a reason

4. **Use environment variables** for deployment-specific settings

## Testing

For testing, you can mock the config:

```python
from unittest.mock import patch
from agents.learning_path import config

def test_with_mocked_config():
    with patch.object(config, 'CACHE_REDIS_URL', 'redis://test:6379'):
        # Your test code here
        pass
```

## Related Files

- `backend/agents/learning_path/config.py` - Main configuration module
- `backend/agents/learning_path/__init__.py` - Package exports
- `.env` - Environment variables (not committed to git)
- `.env.example` - Environment variable template
