# AGPL-3.0 License Exposure — KIRO2

**Status:** OPEN — Business decision required
**Tracker:** B-P0-49 (Session 179 audit)
**Last verified:** 2026-05-21

---

## What

KIRO2 imports two AGPL-3.0-licensed packages in production code paths:

| Package | Version | License | Production usage |
|---|---|---|---|
| `ultralytics` | 8.4.12 | **AGPL-3.0+** | `backend/services/yolo_question_detector.py`, `backend/services/question_parser/yolo_detector.py`, `backend/services/question_parser/train_yolo.py` (YOLO question-region detection) |
| `ultralytics-thop` | 2.0.18 | **AGPL-3.0+** | Transitive of `ultralytics` |
| `PyMuPDF` (`fitz`) | 1.27.2.2 | **AGPL-3.0 OR Artifex Commercial** | PDF processing pipeline |

Both are exposed to end users via `api/ocr_api.py` and
`api/yolo_detection_api.py`.

---

## Risk

**AGPL-3.0 is a network copyleft license.** Section 13 ("Remote Network
Interaction") triggers when:

1. The covered software is "modified" — KIRO2 calls it; whether config
   files / training scripts count as a derivative work is the legal
   question.
2. Users interact over a network — they do (every PDF upload, every
   image processed by YOLO).

The license then requires the operator to:

- Offer the **complete corresponding source** of the covered work, AND
- "Prominently offer" the source to network users.

This is **the same trigger that affects most SaaS deployments** of
ultralytics, Postiz, etc.

---

## Three options (in order of preference)

### Option A — Replace with permissively-licensed alternatives

For YOLO question-region detection:

- `yolov5` (GPL-3.0) — same problem, but smaller surface
- `detectron2` (Apache-2.0) — Facebook's, no AGPL
- Self-hosted small model fine-tuned via `transformers` (Apache-2.0)
- OpenCV-based contour detection (BSD) — sufficient for clean PDFs

For PDF:

- `pdfplumber` (MIT) — already in `requirements.txt`
- `pypdf` (BSD) — pure-Python, low-feature
- `pdf2image` + `poppler` (GPL but as a separate binary, not linked)
- For OCR specifically: `pytesseract` + `tesserocr` (Apache-2.0)

**Effort: ~1 week to migrate YOLO + ~3 days to migrate PyMuPDF.**

### Option B — Buy commercial licenses

- **Ultralytics:** "Enterprise License" via ultralytics.com (~$1.5K-15K/yr
  depending on usage); permits closed-source use.
- **PyMuPDF:** "Artifex Commercial" license. Pricing per build target;
  contact Artifex Software directly.

**Effort: legal + procurement, 2-4 weeks.**

### Option C — Comply with AGPL

Publish full source of KIRO2 backend (the entire FastAPI repository,
not just the YOLO usage) with prominent offer-to-source link in the
UI footer. Requires:

- Repository must be public (currently private)
- All third-party secrets removed from history
- KVKK / business data segregation strategy
- Legal review

**Effort: weeks-to-months.**

---

## Recommended action

**Do NOT ship to commercial beta until one option is chosen.**

Default recommendation: **Option A** for ultralytics, **Option A or B**
for PyMuPDF. Both depend on a 1-2 week engineering sprint and no legal
cost.

Until the decision is made, the YOLO and PDF endpoints should be
disabled behind a feature flag in production:

```bash
ENABLE_YOLO=false
ENABLE_PDF_PIPELINE=false
```

(Add these to `.env.mvp.example` and the router loader.)

---

## Runtime guard

`backend/main.py` (or `core/application.py`) emits a startup log:

```
[LICENSE] AGPL-3.0 packages loaded: ultralytics, ultralytics-thop, PyMuPDF.
[LICENSE] Production deploy without commercial license or source-disclosure
[LICENSE] strategy may violate terms. See docs/compliance/AGPL_LICENSE_EXPOSURE.md.
```

If `ENVIRONMENT=production` and no `KIRO2_LICENSE_DECISION` env var is
set, the startup logs an `ERROR` level entry. (Hard refusal is a
business decision — log-and-go is the safe-not-blocking default.)

---

## Owner

Hüseyin (`huseyinates038@gmail.com`) — please decide and update this
file's `Status:` line.
