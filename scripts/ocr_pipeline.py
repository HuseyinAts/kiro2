"""
d-dataset OCR Pipeline v2 — Gemini 2.5 Flash (öncelikli) + Ollama fallback
Çalıştırma:
  1. .env dosyasına GEMINI_API_KEY ekle
  2. python scripts/ocr_pipeline.py --limit 10   (test)
  3. python scripts/ocr_pipeline.py               (tümü - ~8 saat)
  4. python scripts/ocr_pipeline.py --resume      (kaldığı yerden)
"""
import argparse, base64, json, os, re, time, uuid
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(r"C:\Users\husey\kiro2\backend\.env"))

CROPS_DIR    = Path(r"C:\Users\husey\d-dataset\output\crops")
# Eğer crops klasörü boşsa (PNG'ler subdirectory'lerde), üst klasörü kullan
try:
    if CROPS_DIR.exists() and not any(CROPS_DIR.glob("*.png")):
        _alt = Path(r"C:\Users\husey\d-dataset\output")
        if _alt.exists(): CROPS_DIR = _alt
except: pass
CHECKPOINT   = Path(r"C:\Users\husey\d-dataset\output\ocr_checkpoint.json")
DB_PARAMS    = dict(host="localhost", port=5434, dbname="kiro2",
                    user="postgres", password="changeme_strong_password_here")
DEFAULT_TOPIC = "c3261158-b5b3-5b21-aba0-926d0391c800"
ADMIN_USER    = "de384ad3-93f6-4ff4-8efb-d430bdc55733"

BOOK_SUBJECT_MAP = {
    "matematik": ("MATEMATIK","TYT"), "fizik": ("FIZIK","AYT"),
    "kimya": ("KIMYA","AYT"), "biyoloji": ("BIYOLOJI","AYT"),
    "turkce": ("TURKCE","TYT"), "türkce": ("TURKCE","TYT"),
    "edebiyat": ("EDEBIYAT","AYT"), "tarih": ("TARIH","AYT"),
    "cografya": ("COGRAFYA","AYT"), "sosyal": ("SOSYAL","TYT"),
    "fen": ("FEN","TYT"), "geometri": ("GEOMETRI","TYT"),
    "biyol": ("BIYOLOJI","AYT"),
}

OCR_PROMPT = (
    "Bu goruntu Turkce bir YKS sinav sorusudur. "
    "YALNIZCA asagidaki JSON formatini dondur, baska hicbir sey yazma:\n"
    '{"soru":"metin","A":"sik","B":"sik","C":"sik","D":"sik",'
    '"E":null,"dogru":null}'
)

def detect_subject(book_name):
    low = book_name.lower()
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
    raw = re.sub(r"```json|```","", raw).strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m: return None
    try: return json.loads(m.group())
    except: return None

# ── Gemini OCR ─────────────────────────────────────────────────────────────
def ocr_gemini(img_path):
    import google.genai as genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY","")
    if not api_key: return None
    client = genai.Client(api_key=api_key)
    img_bytes = img_path.read_bytes()
    resp = client.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            OCR_PROMPT,
        ],
    )
    return parse_json(resp.text)

# ── Ollama multimodal OCR (fallback) ───────────────────────────────────────
def ocr_ollama(img_path, model="minicpm-v:latest"):
    import requests
    b64 = encode_image(img_path)
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": model, "prompt": OCR_PROMPT,
        "images": [b64], "stream": False,
        "options": {"temperature": 0.1, "num_predict": 400},
    }, timeout=90)
    if not r.ok: return None
    return parse_json(r.json().get("response",""))

def ocr_image(img_path):
    """Önce Gemini dene, başarısız olursa Ollama."""
    result = ocr_gemini(img_path)
    if result: return result
    return ocr_ollama(img_path)

# ── DB insert ──────────────────────────────────────────────────────────────
def get_template(cur):
    cur.execute("""SELECT bloom_level,bloom_category,osym_format_compliant,
        student_success_rate,difficulty_update_count,
        calibration_sample_size,calibration_quality_score,
        morphology_complexity,word_count,unique_word_count,
        average_word_length,readability_score,
        average_response_time,median_response_time,exposure_rate,grade_level
        FROM question_bank LIMIT 1""")
    return cur.fetchone()

def insert_question(cur, data, subject, exam_type, book, tmpl):
    soru = (data.get("soru") or "").strip()
    if len(soru) < 8: return False
    (bl,bc,osym,ssr,du,cs,cq,mc,wc,uwc,awl,rs,ar,mr,er,gl) = tmpl
    cur.execute("""INSERT INTO question_bank (
        id,question_text,option_a,option_b,option_c,option_d,option_e,
        correct_answer,exam_type,subject_area,primary_topic_id,
        bloom_level,bloom_category,difficulty_level,irt_based_difficulty,
        student_success_rate,difficulty_update_count,
        irt_discrimination,irt_difficulty,irt_guessing,irt_upper_asymptote,
        is_calibrated,calibration_sample_size,calibration_quality_score,
        morphology_complexity,word_count,unique_word_count,
        average_word_length,readability_score,osym_format_compliant,
        times_asked,times_correct,times_wrong,times_skipped,
        average_response_time,median_response_time,exposure_rate,
        grade_level,quality_score,quality_review_status,
        is_active,is_public,source_book,created_by,created_at,updated_at
    ) VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,'MEDIUM','medium',%s,%s,
        1.0,0.0,0.25,1.0,
        FALSE,%s,%s,%s,%s,%s,%s,%s,%s,
        0,0,0,0,%s,%s,%s,%s,
        0.6,'ocr_pending',TRUE,FALSE,%s,%s,NOW(),NOW()
    )""", (
        str(uuid.uuid4()),soru,
        data.get("A"),data.get("B"),data.get("C"),data.get("D"),data.get("E"),
        data.get("dogru"),exam_type,subject,DEFAULT_TOPIC,
        bl,bc,ssr,du,cs,cq,mc,wc,uwc,awl,rs,osym,ar,mr,er,gl,
        book,ADMIN_USER,
    ))
    return True

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--book",   type=str, default="")
    args = parser.parse_args()

    has_gemini = bool(os.environ.get("GEMINI_API_KEY",""))
    print(f"Gemini API: {'AKTIF' if has_gemini else 'YOK - .env dosyasina GEMINI_API_KEY ekle'}")

    conn = psycopg2.connect(**DB_PARAMS)
    cur  = conn.cursor()
    tmpl = get_template(cur)
    done = load_checkpoint() if args.resume else set()

    all_crops = []
    for bd in sorted(CROPS_DIR.iterdir()):
        if not bd.is_dir(): continue
        if args.book and args.book.lower() not in bd.name.lower(): continue
        all_crops.extend(sorted(bd.glob("*.png")))

    pending = [c for c in all_crops if str(c) not in done]
    if args.limit > 0: pending = pending[:args.limit]

    print(f"Toplam: {len(all_crops)} | Bekleyen: {len(pending)}")
    if not pending: print("Hepsi islendi!"); conn.close(); return

    ins=skip=err=0
    for i, img in enumerate(pending):
        subj, exam = detect_subject(img.parent.name)
        print(f"[{i+1}/{len(pending)}] {img.name[:45]}", end="  ")
        t0 = time.time()
        data = ocr_image(img)
        elapsed = round(time.time()-t0, 1)
        if data is None:
            print(f"HATA ({elapsed}s)"); err+=1
        else:
            ok = insert_question(cur, data, subj, exam, img.parent.name, tmpl)
            if ok: print(f"OK ({elapsed}s) {data.get('soru','')[:35]}"); ins+=1
            else:  print(f"ATLANDI ({elapsed}s)"); skip+=1

        done.add(str(img))
        if len(done) % 10 == 0:
            conn.commit(); save_checkpoint(done)
            print(f"  [CP] +{ins} eklendi / {err} hata")

    conn.commit(); save_checkpoint(done); conn.close()
    print(f"\nSONUC: {ins} eklendi | {err} hata | {skip} atlandi")

if __name__ == "__main__":
    main()
