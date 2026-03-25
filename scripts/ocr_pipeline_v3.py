"""
OCR Pipeline v3 — Gemini öncelikli, Ollama (qwen3) fallback, manual fallback
Mevcut Ollama: qwen3:8b (text-only), vision model yoksa Gemini şart
"""
import argparse, base64, json, os, re, time, uuid, pathlib, sys
import psycopg2
from pathlib import Path

# .env yükle
env_path = Path(r"C:\Users\husey\kiro2\backend\.env")
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8', errors='replace').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

CROPS_DIR  = Path(r"C:\Users\husey\d-dataset\output\crops")
CHECKPOINT = Path(r"C:\Users\husey\d-dataset\output\ocr_checkpoint.json")
DB_PARAMS  = dict(host="localhost", port=5434, dbname="kiro2",
                  user="postgres", password="changeme_strong_password_here")
DEFAULT_TOPIC = "c3261158-b5b3-5b21-aba0-926d0391c800"
ADMIN_USER    = "de384ad3-93f6-4ff4-8efb-d430bdc55733"

BOOK_SUBJECT_MAP = {
    "matematik": ("MATEMATIK","TYT"), "fizik": ("FIZIK","AYT"),
    "kimya":     ("KIMYA","AYT"),     "biyoloji": ("BIYOLOJI","AYT"),
    "turkce":    ("TURKCE","TYT"),    "türkce": ("TURKCE","TYT"),
    "edebiyat":  ("EDEBIYAT","AYT"), "tarih": ("TARIH","AYT"),
    "cografya":  ("COGRAFYA","AYT"), "sosyal": ("SOSYAL","TYT"),
    "fen":       ("FEN","TYT"),       "geometri": ("GEOMETRI","TYT"),
}

OCR_PROMPT = (
    "Bu goruntu Turkce bir YKS sinav sorusudur. "
    "YALNIZCA asagidaki JSON formatini dondur, baska hicbir sey yazma:\n"
    '{"soru":"metin","A":"sik","B":"sik","C":"sik","D":"sik",'
    '"E":null,"dogru":null}'
)

def detect_subject(name):
    low = name.lower()
    for k, v in BOOK_SUBJECT_MAP.items():
        if k in low: return v
    return ("MATEMATIK", "TYT")

def load_checkpoint():
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text("utf-8")))
    return set()

def save_checkpoint(done):
    CHECKPOINT.write_text(json.dumps(list(done)), "utf-8")

def encode_image(path):
    return base64.b64encode(path.read_bytes()).decode()

def parse_json(raw):
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m: return None
    try: return json.loads(m.group())
    except: return None

# ── Gemini OCR ─────────────────────────────────────────────────────────────
def ocr_gemini(img_path):
    try:
        import google.genai as genai
        from google.genai import types
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key or len(api_key) < 10: return None
        client = genai.Client(api_key=api_key)
        img_data = img_path.read_bytes()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_data, mime_type="image/png"),
                OCR_PROMPT,
            ],
        )
        return parse_json(response.text)
    except Exception as e:
        if "API_KEY" not in str(e):
            print(f"  Gemini hatası: {e}")
        return None

# ── Ollama Vision OCR (qwen2.5vl veya llava) ────────────────────────────────
def ocr_ollama_vision(img_path):
    """Sadece vision-capable model varsa çalışır."""
    import urllib.request
    # Mevcut modelleri kontrol et
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        models = json.loads(r.read()).get("models", [])
        vision_models = [m["name"] for m in models
                         if any(x in m["name"] for x in ["vision","vl","llava","bakllava"])]
        if not vision_models: return None
        model = vision_models[0]
    except: return None

    payload = json.dumps({
        "model": model,
        "prompt": OCR_PROMPT,
        "images": [encode_image(img_path)],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 400}
    }).encode()
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload, headers={"Content-Type": "application/json"}
        )
        r = urllib.request.urlopen(req, timeout=45)
        return parse_json(json.loads(r.read()).get("response", ""))
    except: return None

def ocr_image(img_path):
    """Sırayla Gemini → Ollama Vision dene."""
    result = ocr_gemini(img_path)
    if result: return result, "gemini"
    result = ocr_ollama_vision(img_path)
    if result: return result, "ollama"
    return None, "none"
