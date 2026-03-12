# OCR Preprocess Inventory

## Scope
- `d-dataset/scripts/pipeline.py`
- `d-dataset/scripts/vision_solve_gemini.py`
- `d-dataset/scripts/vision_solve_codex.py`
- `d-dataset/scripts/vision_solve_opus.py`
- `d-dataset/scripts/script_common.py`

## Shared Utility
- `script_common.preprocess_image(image_path, max_dim, retry_enhance)`
- `script_common.image_to_base64_jpeg(img)`
- `script_common.image_to_png_bytes(img)`

## Active Preprocess Steps
1. Resize (LANCZOS) with provider-specific max dimension.
2. Retry enhancement (for retry attempts): grayscale + contrast + sharpness.
3. Encoding:
- API payloads: JPEG base64.
- Gemini vision solver payload: PNG bytes.
4. Fallback-only advanced preprocessing (routing-triggered):
- Small-angle deskew
- Median denoise
- Adaptive threshold

## Routing Policy
- Standard pass: `processing.ocr_standard_max_dim` (default `1024`).
- Triggered fallback pass: `processing.ocr_fallback_max_dim` (default `1280`) + advanced preprocessing.
- Trigger condition: contrast/sharpness under thresholds:
  - `processing.quality_routing_contrast_threshold`
  - `processing.quality_routing_sharpness_threshold`

## Provider Paths
- OpenAI OCR (`pipeline.py`): shared preprocess + JPEG base64.
- Gemini OCR (`pipeline.py`): shared preprocess; retry uses enhancement.
- Ollama OCR (`pipeline.py`): shared preprocess + JPEG base64.
- Answer-key OCR (`pipeline.py`): shared preprocess for OpenAI/Gemini/Ollama.
- Gemini vision solver (`vision_solve_gemini.py`): shared preprocess + PNG bytes.
- Codex/Opus vision solvers: screenshot path is passed to CLI (no local pixel transform).

## Current Limitations
- No deskew
- No denoise filter
- No adaptive threshold / binarization
- Crop padding defaults to fixed (`processing.crop_padding`), with optional adaptive ratio (`processing.crop_padding_ratio`)

## Turkish Normalization Standard
- All Turkish text comparisons should use:
1. NFC
2. `İ -> i`, `I -> ı`
3. lowercase
- Reference: `script_common.normalize_tr()`

## A/B Validation
- Script: `d-dataset/scripts/ab_validate_ocr.py`
- Acceptance checks:
  - `cannot_solve` relative drop >= 20%
  - `invalid_option/no_answer` relative drop >= 15%
  - answer-key match delta >= +2 pp
  - average latency increase <= 25%
