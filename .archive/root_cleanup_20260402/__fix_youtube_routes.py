"""youtube_routes.py icindeki bare slowapi import'u try/except icerisine al."""

path = r"C:\Users\husey\kiro2\backend\api\youtube_routes.py"

with open(path, encoding="utf-8") as f:
    content = f.read()

OLD = '''except (ImportError, TypeError):
    get_youtube_rate_limiter = None
    YouTubeRateLimiter = None
from slowapi.errors import RateLimitExceeded'''

NEW = '''except (ImportError, TypeError):
    get_youtube_rate_limiter = None
    YouTubeRateLimiter = None

try:
    from slowapi.errors import RateLimitExceeded
except ImportError:
    # slowapi optional — rate limit handler devre disi kalir
    RateLimitExceeded = Exception'''

if OLD not in content:
    print("HATA: Hedef kod bulunamadi!")
    idx = content.find("from slowapi")
    print(f"  'from slowapi' pozisyonu: {idx}")
    print(repr(content[idx:idx+100]))
else:
    new_content = content.replace(OLD, NEW, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("OK: slowapi bare import try/except ile sargilandi")
    # Dogrula
    assert "try:\n    from slowapi.errors import RateLimitExceeded" in new_content
    print("Dogrulama gecti.")
