# KIRO2 Security Audit Report

**Scan Date:** 2026-01-24T01:19:59.479951
**Scanner Version:** 1.0.0
**Target:** KIRO2 Backend

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Findings | 1046 |
| CRITICAL | 75 |
| HIGH | 626 |
| MEDIUM | 331 |
| LOW | 0 |
| INFO | 14 |

### Status Distribution

| Status | Count |
|--------|-------|
| Vulnerable | 175 |
| Secure | 12 |
| Needs Review | 859 |

---

## Detailed Findings


### CRITICAL Severity

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\setup_database.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="postgres"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\core\enhanced_authentication.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['PASSWORD = "password"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\core\unified_auth_service.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['PASSWORD = "reset_password"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\migrations\create_db.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `["password='postgres'"]`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\models\study_room.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['PASSWORD = "password"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\scripts\update_answers_from_json.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="changeme_strong_password_here"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fsspec\spec.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `["password='password'"]`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\httpx\_urls.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="a secret"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\types.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `["password='password1'"]`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\starlette\datastructures.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="********"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mssql\pyodbc.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="tiger"', 'password="tiger"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mysql\mysqldb.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="passwd"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\oracle\cx_oracle.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="tiger"', 'password="tiger"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\sqlite\provision.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password="test"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded password
- **File:** `c:\Users\husey\kiro2\backend\hooks\reward_hacking\config\patterns.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['password = "password..."', 'password = "123..."']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded API key
- **File:** `c:\Users\husey\kiro2\backend\core\parallel_rag.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['api_key="your_api_key"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded API key
- **File:** `c:\Users\husey\kiro2\backend\services\hybrid_question_generator.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['api_key="your-anthropic-key"', 'api_key="your-openai-key"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded API key
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\inference\_client.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['api_key="<together_api_key>"', 'api_key="fal-ai-api-key"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\core\auth_middleware.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['TOKEN = "session_token"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\core\enhanced_authentication.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['TOKEN = "session_token"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\tsig.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `["secret='{base64.b64encode(self.secret).decode()}'"]`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jose\jws.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `["token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhIjoiYiJ9.jiMyrsmD8AoHWeQgmxZ5yq8z0lXS67_QGs52AzC8Ru8'"]`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\aya_vision\processing_aya_vision.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|START_OF_IMG|>"', 'token="<|END_OF_IMG|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blenderbot_small\tokenization_blenderbot_small_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\clip\tokenization_clip.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|startoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\clip\tokenization_clip_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|startoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\clvp\tokenization_clvp.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\codegen\tokenization_codegen.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\codegen\tokenization_codegen_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\cohere\tokenization_cohere_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<BOS_TOKEN>"', 'token="<|END_OF_TURN_TOKEN|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\modular_colqwen2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|image_pad|>"', 'token = "<|video_pad|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\processing_colqwen2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|image_pad|>"', 'token = "<|video_pad|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\csm\processing_csm.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|audio_eos|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\evolla\processing_evolla.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|reserved_special_token_0|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\flaubert\tokenization_flaubert.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<special1>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\got_ocr2\processing_got_ocr2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|im_start|>"', 'token = "<|im_end|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt2\tokenization_gpt2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt2\tokenization_gpt2_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_neox\tokenization_gpt_neox_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_neox_japanese\tokenization_gpt_neox_japanese.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_sw3\tokenization_gpt_sw3.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\idefics\processing_idefics.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<fake_token_around_image>"', 'token = "<end_of_utterance>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\kosmos2\processing_kosmos2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "</delimiter_of_multi_objects/>"', 'token = "<grounding>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\llama4\processing_llama4.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|image_start|>"', 'token="<|image_end|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mllama\processing_mllama.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|python_tag|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\pixtral\processing_pixtral.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="[IMG_BREAK]"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2\tokenization_qwen2.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2\tokenization_qwen2_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2_5_vl\processing_qwen2_5_vl.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|image_pad|>"', 'token = "<|video_pad|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2_audio\processing_qwen2_audio.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|audio_bos|>"', 'token="<|audio_eos|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2_vl\processing_qwen2_vl.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "<|image_pad|>"', 'token = "<|video_pad|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\splinter\tokenization_splinter.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="[QUESTION]"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\splinter\tokenization_splinter_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="[QUESTION]"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\whisper\tokenization_whisper.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\whisper\tokenization_whisper_fast.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"', 'token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlm\tokenization_xlm.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<special1>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\gptsan_japanese\tokenization_gptsan_japanese.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|nottoken|>"', 'token="<|separator|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\jukebox\tokenization_jukebox.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="<|endoftext|>"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\path_registry.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['TOKEN = "_sa_default"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\utils\_validators.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="a use_auth_token"', 'token="a use_auth_token"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\ttProgram.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token = "(%s)|(%s)|(%s)"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\script\write_hooks.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['TOKEN = "REVISION_SCRIPT_FILENAME"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\templates\multidb\env.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['token="%s_upgrades"', 'token="%s_downgrades"']`

#### A02-002: Potential Hardcoded Secret [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Hardcoded secret/token
- **File:** `c:\Users\husey\kiro2\backend\core\unified\auth_system.py`
- **Recommendation:** Use environment variables or secret management
- **Evidence:** `['TOKEN = "session_token"']`

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\core\sql_injection_auditor.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\core\transaction_context.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypy\metastore.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mssql\base.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mysql\base.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\oracle\cx_oracle.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\postgresql\pg8000.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\sqlite\base.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string in SQL execute
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\sqlite\provision.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** String formatting in SQL
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\sqlite\pysqlcipher.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM

#### A03-001: Potential SQL Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** String concatenation in SQL
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\postgresql\pg8000.py`
- **Recommendation:** Use parameterized queries with SQLAlchemy ORM


### HIGH Severity

#### A01-001: Endpoints Without Authentication Check [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Found 508 endpoints that may lack authentication
- **Recommendation:** Review and add appropriate authentication to all sensitive endpoints
- **Evidence:** `admin.py: GET /users
admin.py: POST /users
admin.py: GET /users/{kullanici_id}
admin.py: PUT /users/{kullanici_id}
admin.py: DELETE /users/{kullanici_id}
admin.py: GET /dashboard/stats
admin.py: GET /`

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\optimal_hybrid_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\api\soru_bankasi.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\api\student_dashboard.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\content\unified_content_management.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\bionic_reading_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\cache_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\cache_stampede_prevention.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\dynamic_content_generator.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\feature_flags.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\file_upload_security.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\improved_base_agent.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\rag_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\rbac_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\redis_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\revolutionary_optimizer.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\vector_optimizations.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\examples\multi_layer_cache_example.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\fact_checking\wikipedia_client.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\doc_updater_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\learning_path_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\multisensory_learning_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\safety_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\video_recommendation_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\visual_supports_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\youtube_discovery.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\lcovreport.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\rsync.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\rsync_remote.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fsspec\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\texmanager.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\starlette\_compat.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_config_module.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_logging\_internal.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\hipify\hipify_python.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\passes\graph_drawer.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\util\compat.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mysql\base.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sklearn\datasets\_openml.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\fontfinder.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\pdfencrypt.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfbase\cidfonts.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfbase\pdfdoc.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfgen\canvas.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\distlib\database.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\distlib\index.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\cisco.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\digests.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\django.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\ldap_digests.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\md5_crypt.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\phpass.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\postgres.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\sun_md5_crypt.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\sphinxext\mathmpl.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\providers\misc\__init__.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\services\youtube\search.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\cache\redis_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\hooks\claude_md_improvement\cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\cache\cache_manager.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\cache\query_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\decorators\cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\middleware\cache_headers.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\unified\cache_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\optimal_hybrid_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\api\soru_bankasi.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\api\student_dashboard.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\content\unified_content_management.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\bionic_reading_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\cache_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\cache_stampede_prevention.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\dynamic_content_generator.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\feature_flags.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\file_upload_security.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\improved_base_agent.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\rag_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\rbac_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\redis_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\revolutionary_optimizer.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\vector_optimizations.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\examples\multi_layer_cache_example.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\fact_checking\wikipedia_client.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\doc_updater_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\learning_path_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\multisensory_learning_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\safety_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\video_recommendation_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\visual_supports_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\youtube_discovery.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\lcovreport.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\tsig.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\httpx\_auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\texmanager.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\rsa\pkcs1.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\starlette\_compat.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_config_module.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_logging\_internal.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\hipify\hipify_python.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\passes\graph_drawer.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\util\compat.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sklearn\datasets\_openml.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfgen\canvas.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\distlib\database.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\distlib\index.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\digests.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\sphinxext\mathmpl.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\utils\insecure_hashlib.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\providers\misc\__init__.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elastic_transport\_node\_urllib3_chain_certs.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\services\youtube\search.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\cache\redis_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\hooks\claude_md_improvement\cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\cache\cache_manager.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\cache\query_cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\decorators\cache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\middleware\cache_headers.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** MD5 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\unified\cache_system.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\start_hybrid_system.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\scripts\coverage_analysis.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\PIL\ImageShow.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\package_index.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\websockets\cli.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\elastic\multiprocessing\redirects.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** os.system usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\f2py\diagnose.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\agents\langchain_study_buddy.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\core\berturk_service.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\question_generation_engine.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\sindbert_turkembed_service.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\video_solution_service.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\attr\_make.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\cffi\recompiler.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway_io.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fsspec\gui.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\hub_mixin.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\isort\literal.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\lexer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\nativetypes.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\nodes.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\memory.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\parallel.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mako\codegen.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\rcsetup.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mpmath\identification.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypy\evalexpr.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypy\modulefinder.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\packaging\_parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\PIL\GifImagePlugin.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\PIL\Image.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\PIL\ImageMath.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\psutil\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pyparsing\results.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\redis\cluster.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\tqdm\cli.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\modeling_utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\trainer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\training_args.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\training_args_tf.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\integrations\executorch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\integrations\flex_attention.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\integrations\peft.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\onnx\convert.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\pipelines\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\auto\auto_factory.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bigbird_pegasus\modeling_bigbird_pegasus.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\big_bird\modeling_big_bird.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blip\modeling_blip.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blip\modeling_tf_blip.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blip_2\modeling_blip_2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bridgetower\modeling_bridgetower.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\chameleon\modeling_chameleon.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colpali\configuration_colpali.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colpali\modeling_colpali.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colpali\modular_colpali.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colpali\processing_colpali.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\configuration_colqwen2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\modeling_colqwen2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\modular_colqwen2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\colqwen2\processing_colqwen2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\decision_transformer\modeling_decision_transformer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\emu3\modeling_emu3.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\emu3\modular_emu3.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\encoder_decoder\modeling_encoder_decoder.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\janus\modeling_janus.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\musicgen\modeling_musicgen.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\musicgen_melody\modeling_musicgen_melody.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rag\modeling_rag.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rag\retrieval_rag.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\speech_encoder_decoder\modeling_speech_encoder_decoder.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\timm_wrapper\modeling_timm_wrapper.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\vilt\modeling_vilt.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\vision_encoder_decoder\modeling_vision_encoder_decoder.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xcodec\modeling_xcodec.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlnet\configuration_xlnet.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\jukebox\modeling_jukebox.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\trajectory_transformer\modeling_trajectory_transformer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\continuous_batching\continuous_api.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\data\metrics\squad_metrics.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\amp\autocast_mode.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\export\exported_program.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\export\_trace.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\operator_schemas.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\jit\annotations.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\jit\_freeze.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\jit\_trace.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\onnx\verification.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\optim\lbfgs.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\mobile_optimizer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_traceback.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\guards.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_functorch\compilers.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\compiler_bisector.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\select_algorithm.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_library\infer_schema.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\fx_passes\efficient_conv_bn_eval.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\fx_passes\pre_grad.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\backends\torchxla.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\repro\after_dynamo.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\variables\tensor.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\tensorboard\_pytorch_graph.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_sympy\functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\onnx\_internal\exporter\_building.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\nn\modules\activation.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\nn\modules\batchnorm.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\nn\modules\module.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\nn\modules\transformer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\nn\utils\fusion.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\experimental\optimization.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\experimental\proxy_tensor.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\experimental\symbolic_shapes.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\passes\splitter_base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\fsdp\_flat_param.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\fsdp\_runtime_utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\nn\api\remote_module.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\ns\_numeric_suite_fx.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\fuser_method_mappings.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\fuse_modules.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\quantize.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\quantize_fx.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\quantize_jit.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\quantize_pt2e.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\backend_config\onednn.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\pt2e\export_utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\quantization\pt2e\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\pruning\_experimental\data_sparsifier\lightning\callbacks\data_sparsity.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\nn\quantizable\modules\activation.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\ao\nn\quantizable\modules\rnn.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\assumptions\assume.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\assumptions\wrapper.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\codegen\algorithms.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\codegen\cfunctions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\combinatorics\schur_number.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\core\function.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\core\mod.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\core\symbol.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\external\importtools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\integrals\manualintegrate.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\integrals\meijerint.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\integrals\prde.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\integrals\rde.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\integrals\risch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\logic\boolalg.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\parsing\ast_parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\parsing\sympy_parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\secondquant.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\plotting\series.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\appellseqs.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\compatibility.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\densetools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\euclidtools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\galoistools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\polyclasses.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\polyconfig.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\polyquinticconst.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\polyroots.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\polytools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\ring_series.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\rootisolation.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\rootoftools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\printing\dot.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\printing\repr.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\series\formal.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\simplify\gammasimp.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\solvers\polysys.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\tensor\tensor.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\utilities\lambdify.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\utilities\matchpy_connector.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\numberfields\galoisgroups.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\numberfields\galois_resolvents.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\numberfields\subfield.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\plotting\pygletplot\plot_axes.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\plotting\pygletplot\plot_interval.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\biomechanics\curve.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\control\control_plots.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\quantum\anticommutator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\quantum\commutator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\quantum\hilbert.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\physics\quantum\state.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\combinatorial\factorials.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\combinatorial\numbers.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\complexes.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\exponential.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\hyperbolic.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\integers.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\miscellaneous.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\piecewise.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\elementary\trigonometric.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\bessel.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\beta_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\delta_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\elliptic_integrals.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\error_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\gamma_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\hyper.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\mathieu_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\polynomials.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\singularity_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\spherical_harmonics.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\tensor_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\functions\special\zeta_functions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\assumptions\relation\binrel.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\assumptions\relation\equality.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\clsregistry.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\_orm_constructors.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\util\typing.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sklearn\metrics\_ranking.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\config\expand.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_distutils\ccompiler.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_vendor\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_vendor\jaraco\functools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_vendor\pyparsing\results.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\differentiate\_differentiate.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\integrate\_tanhsinh.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\optimize\_bracket.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\optimize\_chandrupatla.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\optimize\_optimize.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\signal\_spline_filters.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\stats\_continuous_distns.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\_elementwise_iterative_method.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\cobyqa\main.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\cobyqa\problem.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\special\_precompute\wright_bessel.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\colors.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\extformat.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\rl_safe_eval.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfbase\pdfpattern.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfbase\_cidfontdata.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\platypus\doctemplate.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\platypus\tableofcontents.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\graphics\charts\barcharts.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\redis\commands\core.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\v1\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\_internal\_typing_extra.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\cpp.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\yacc.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pkg_resources\_vendor\jaraco\functools.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pkg_resources\_vendor\pyparsing\results.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\pyparsing\results.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\rich\markup.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\crypto\digest.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\packaging\licenses\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\core\arrayprint.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\core\_internal.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\distutils\misc_util.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\f2py\auxfuncs.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\f2py\capi_maps.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\f2py\crackfortran.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\lib\format.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\lib\npyio.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\lib\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\ma\timer_comparison.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\polynomial\hermite_e.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\networkx\readwrite\edgelist.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\networkx\readwrite\gml.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\networkx\readwrite\multiline_adjlist.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\networkx\algorithms\bipartite\edgelist.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\backends\qt_editor\_formlayout.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\cffLib\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\misc\symfont.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\M_E_T_A_.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\otBase.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\otConverters.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\otTables.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\ttLib\tables\S_I_N_G_.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\sphinx\docstring.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\sphinx\validator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\script\socketserver.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elasticsearch\_sync\client\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elasticsearch\_async\client\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\blib2to3\pgen2\conv.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\blib2to3\pgen2\literals.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\blib2to3\pgen2\pgen.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\antlr4\atn\ParserATNSimulator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\antlr4\atn\SemanticContext.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\nlp_training\berturk_embedding.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\nlp_training\rlhf_training.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\nlp_training\t5_bart_generation.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\services\quality\metrics.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\scripts\security_audit\owasp_top10_scanner.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\plugins\math_genius\agent.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** eval() usage
- **File:** `c:\Users\husey\kiro2\backend\app\health\alerting\alert_manager.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\install_verify_langchain.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\content\multimedia_content_processor.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\hooks\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\services\video_solution_service.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\six.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\threadpoolctl.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\asyncpg\cursor.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\cffi\setuptools_ext.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\execfile.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\patch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\templite.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway_base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway_bootstrap.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway_io.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\gateway_socket.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\multi.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\rsync.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\debug.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\environment.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mako\template.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pkg_resources\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pluggy\_hooks.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pluggy\_manager.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\prometheus_client\decorator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\rl_config.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\build_meta.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\launch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\sandbox.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\abc.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\xdist\looponfail.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\xdist\workermanage.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\graph_module.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\jit\frontend.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\jit\unsupported_tensor_ops.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\package\package_importer.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\guards.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_higher_order_ops\triton_kernel_wrap.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\codecache.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\ops_handler.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\codegen\cpp_wrapper_cpu.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\codegen\wrapper.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\runtime\compile_tasks.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\runtime\triton_heuristics.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_export\serde\serialize.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\bottleneck\__main__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\fx\experimental\rewriter.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\benchmarks\bench_meijerint.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\codegen\algorithms.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\codegen\ast.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\core\sympify.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\interactive\session.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\parsing\ast_parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\parsing\sympy_parser.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\plotting\experimental_lambdify.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\polys\monomials.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\printing\python.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\utilities\lambdify.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\utilities\matchpy_connector.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\default.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\interfaces.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\bulk_persistence.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\context.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\events.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\instrumentation.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\session.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\strategies.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\sql\lambdas.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\util\langhelpers.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mssql\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mssql\pyodbc.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mysql\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\mysql\mariadbconnector.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\oracle\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\oracle\cx_oracle.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\postgresql\pg8000.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\dialects\postgresql\psycopg2.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_distutils\core.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_vendor\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\optimize\_nonlin.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\stats\_distn_infrastructure.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\decorator.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\_bunch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\array_api_compat\cupy\fft.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\array_api_compat\cupy\linalg.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\array_api_compat\torch\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\array_api_compat\dask\array\fft.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\_lib\array_api_compat\dask\array\linalg.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\graphics\utils.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\pdfencrypt.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\rl_accel.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\platypus\doctemplate.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\platypus\flowables.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\graphics\barcode\widgets.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\_internal\_typing_extra.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\lex.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\yacc.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\six.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\typing_extensions.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\pkg_resources\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\urllib3\packages\six.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\pygments\lexers\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_internal\utils\setuptools_build.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\networkx\utils\decorators.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mpmath\libmp\backend.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\backends\backend_qt.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\backends\qt_compat.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\sphinxext\plot_directive.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\backends\qt_editor\_formlayout.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\externals\loky\backend\fork_exec.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\externals\loky\backend\popen_loky_posix.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\functorch\einops\rearrange.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\misc\psLib.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\misc\psOperators.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\t1Lib\__init__.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\script\shell.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\execnet\script\socketserver.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\anyio\_backends\_asyncio.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\ddl\impl.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\ddl\mssql.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\ddl\mysql.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\ddl\oracle.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\ddl\postgresql.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\operations\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\operations\batch.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\runtime\migration.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\alembic\util\langhelpers.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\scripts\security_audit\owasp_top10_scanner.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A03-002: Potential Command Injection [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** exec() usage
- **File:** `c:\Users\husey\kiro2\backend\core\quality_gates\gates\base.py`
- **Recommendation:** Avoid shell=True and use subprocess with argument lists

#### A06-002: Potentially Vulnerable Package [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Package pyyaml found - check for CVE-2020-14343
- **File:** `c:\Users\husey\kiro2\backend\requirements.txt`
- **Recommendation:** Run 'pip-audit' or 'safety check' for detailed CVE scan

#### A06-002: Potentially Vulnerable Package [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Package pillow found - check for CVE-2021-23437
- **File:** `c:\Users\husey\kiro2\backend\requirements.txt`
- **Recommendation:** Run 'pip-audit' or 'safety check' for detailed CVE scan

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\config\redis_optimized_config.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\core\cache_service.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\services\enhanced_bloom_classifier.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\services\semantic_youtube_search.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\services\similar_question_service.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\cookiejar.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\anyio\to_process.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\black\cache.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\bccache.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\hashing.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\numpy_pickle.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\_store_backends.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\zemberek\normalization\deasciifier\deasciifier.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\integrations\integration_utils.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bloom\tokenization_bloom_fast.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\cohere\tokenization_cohere_fast.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rag\retrieval_rag.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\transfo_xl\tokenization_transfo_xl.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\data\datasets\language_modeling.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\cuda\_memory_viz.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\multiprocessing\queue.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\multiprocessing\spawn.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_config_module.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\package.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\pgo.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_dynamo\precompile_context.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_functorch\compilers.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\autotune_process.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\codecache.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\debug.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\fuzzer.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\standalone_compile.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\codegen\wrapper.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_inductor\compile_worker\subproc_pool.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_functorch\_aot_autograd\autograd_cache.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\model_dump\__init__.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\data\datapipes\datapipe.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\data\datapipes\utils\decoder.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\benchmark\examples\compare.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\benchmark\utils\valgrind_wrapper\timer_interface.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\checkpoint\filesystem.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\_tools\memory_tracker.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\elastic\rendezvous\dynamic_rendezvous.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\ext\serializer.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\sql\sqltypes.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sklearn\datasets\_twenty_newsgroups.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sklearn\utils\estimator_checks.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\scipy\datasets\_fetchers.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\fontfinder.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\utils.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\deprecated\parse.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\v1\parse.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\yacc.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\core\records.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\core\setup.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\lib\format.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\lib\npyio.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypy\dmypy\client.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\joblib\externals\loky\backend\popen_loky_posix.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fsspec\implementations\cache_metadata.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\cffLib\__init__.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\blib2to3\pgen2\grammar.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe pickle usage
- **File:** `c:\Users\husey\kiro2\backend\core\unified\cache_system.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\coverage\execfile.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\bccache.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\depends.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\command\bdist_egg.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\utils.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A08-001: Unsafe Deserialization [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Unsafe marshal usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\pdfbase\cidfonts.py`
- **Recommendation:** Use safe alternatives (json, yaml.safe_load)

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** f-string URL in aiohttp
- **File:** `c:\Users\husey\kiro2\backend\core\http_client.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\scripts\download_zemberek_jar.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jwt\jwks_client.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\image.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\__init__.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\package_index.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\_weights_only_unpickler.py`
- **Recommendation:** Validate and whitelist external URLs

#### A10-001: Potential SSRF Vulnerability [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** urllib.request usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_distutils\command\register.py`
- **Recommendation:** Validate and whitelist external URLs


### MEDIUM Severity

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\core\unified_auth_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\client.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\web_ws.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\dnssec.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\entropy.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\ecdsa\ecdsa.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\httpx\_auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_local_folder.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\bccache.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\jinja2\loaders.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypyc\build.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torchgen\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\websockets\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\distributed_c10d.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_content_store.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\redis\commands\core.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\django.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\ldap_digests.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\mssql.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\mysql.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\oracle.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\pbkdf2.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\distutils\fcompiler\gnu.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\utils\sha.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\varLib\interpolatablePlot.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\providers\misc\__init__.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hash usage detected
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\cryptography\x509\extensions.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\core\unified_auth_service.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\client.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\web_ws.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\dnssec.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\entropy.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\dns\tsig.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\ecdsa\keys.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\ecdsa\rfc6979.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\httpx\_auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_local_folder.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\mypyc\build.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\rsa\pkcs1.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torchgen\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\websockets\utils.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\distributed\distributed_c10d.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\torch\utils\_content_store.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\redis\commands\core.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\requests\auth.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\numpy\distutils\fcompiler\gnu.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\utils\insecure_hashlib.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fontTools\varLib\interpolatablePlot.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\faker\providers\misc\__init__.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elastic_transport\_node\_urllib3_chain_certs.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A02-001: Weak Cryptographic Algorithm [VULNERABLE]

- **Status:** VULNERABLE
- **Description:** SHA1 hashlib usage
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\cryptography\x509\extensions.py`
- **Recommendation:** Use SHA-256 or stronger algorithms

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\alembic\env.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\analytics\health_audit_service.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\api\enhanced_user_management_api.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\auth_security_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\enhanced_authentication.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\kvkk_compliance.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\passwordless_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\security_manager.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\sensitive_data_filter.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\scripts\backup_database.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\scripts\production_seed.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tasks\email_tasks.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\aiohttp\helpers.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_login.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\requests\utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\requests\utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\rich\logging.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_internal\network\auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\handlers\mssql.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\test_handlers.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\test_totp.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\fastapi\security\oauth2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\fast\test_fastapi_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\fixtures\integration_fixtures.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_auth_api_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_passwordless_webauthn.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_phase2_user_service.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_structured_logging.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\performance\test_elk_performance.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_api_auth_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_api_integration_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_authentication_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_comprehensive_api_coverage.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_services_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\unit\test_services_batch1.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\tests\unit\test_user_service.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\scripts\security_audit\owasp_top10_scanner.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\core\unified\auth_system.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\app\health\alerting\notifiers.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\alembic\versions\002_performance_indexes.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in log
- **File:** `c:\Users\husey\kiro2\backend\alembic\versions\003_real_performance_indexes.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\api\zemberek.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\auth_middleware.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\dependencies.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\enhanced_authentication.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\learning_path_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\learning_path_logger.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\message_queue_system.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\security_manager.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\two_factor_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\zemberek_service.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\middleware\rate_limit_middleware.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\monitoring\token_usage_tracker.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\services\bertscore_evaluator.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\services\khan_academy_client.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\services\zemberek_nlp_server.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\utils\zemberek_integration.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\hf_api.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\repocard.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\repository.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_login.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_oauth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\matplotlib\_type1font.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\convert_slow_tokenizer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\convert_slow_tokenizers_checkpoints_to_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\modeling_layers.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\testing_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\tokenization_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\tokenization_utils_base.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\trainer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\training_args.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\__init__.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\zemberek\lm\lm_vocabulary.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\zemberek\morphology\turkish_morphology.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\commands\serving.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\data\data_collator.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\candidate_generator.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\configuration_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\flax_logits_process.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\flax_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\logits_process.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\tf_logits_process.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\tf_utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\watermarking.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\integrations\peft.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\onnx\config.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\onnx\convert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\pipelines\automatic_speech_recognition.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\pipelines\base.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\pipelines\document_question_answering.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\pipelines\question_answering.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\utils\auto_docstring.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\utils\doc.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\utils\hub.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\albert\modeling_albert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\albert\modeling_tf_albert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\albert\tokenization_albert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\auto\tokenization_auto.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bamba\configuration_bamba.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bark\modeling_bark.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bart\modeling_bart.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bart\tokenization_bart_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bert\modeling_tf_bert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bigbird_pegasus\modeling_bigbird_pegasus.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\big_bird\modeling_big_bird.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blenderbot\modeling_blenderbot.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blenderbot\tokenization_blenderbot_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\blenderbot_small\modeling_blenderbot_small.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bloom\modeling_bloom.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\bros\modeling_bros.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\camembert\modeling_tf_camembert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\chameleon\modeling_chameleon.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\clip\tokenization_clip.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\clvp\modeling_clvp.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\csm\generation_csm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\ctrl\modeling_ctrl.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\ctrl\modeling_tf_ctrl.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deberta\tokenization_deberta_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\eomt\modeling_eomt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\eomt\modular_eomt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\falcon\modeling_falcon.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\falcon_h1\configuration_falcon_h1.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\flaubert\modeling_flaubert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\funnel\modeling_tf_funnel.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gemma3\modeling_gemma3.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gemma3\modular_gemma3.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\git\modeling_git.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt2\modeling_gpt2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt2\modeling_tf_gpt2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gptj\modeling_gptj.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gptj\modeling_tf_gptj.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_bigcode\modeling_gpt_bigcode.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_neo\modeling_gpt_neo.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_neox\modeling_gpt_neox.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\gpt_neox\modular_gpt_neox.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\granitemoe\modeling_granitemoe.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\granitemoehybrid\modeling_granitemoehybrid.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\granitemoeshared\modeling_granitemoeshared.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\grounding_dino\modeling_grounding_dino.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\jamba\configuration_jamba.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\jetmoe\modeling_jetmoe.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\led\modeling_led.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\led\tokenization_led_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\longformer\modeling_longformer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\longformer\modeling_tf_longformer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\longformer\tokenization_longformer_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\marian\modeling_flax_marian.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\marian\modeling_marian.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mbart\modeling_mbart.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mistral\modeling_tf_mistral.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mm_grounding_dino\modeling_mm_grounding_dino.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mobilebert\modeling_tf_mobilebert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\modernbert_decoder\modeling_modernbert_decoder.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\modernbert_decoder\modular_modernbert_decoder.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\moshi\modeling_moshi.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mpnet\tokenization_mpnet_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mpt\modeling_mpt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mra\modeling_mra.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mvp\modeling_mvp.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\mvp\tokenization_mvp_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\myt5\tokenization_myt5.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\openai\modeling_openai.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\openai\modeling_tf_openai.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\openai\tokenization_openai.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\opt\modeling_opt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\opt\modeling_tf_opt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\pegasus\modeling_pegasus.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\plbart\modeling_plbart.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\plbart\modular_plbart.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\prophetnet\modeling_prophetnet.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2_5_omni\configuration_qwen2_5_omni.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\qwen2_5_omni\modular_qwen2_5_omni.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rag\modeling_rag.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rag\modeling_tf_rag.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\reformer\modeling_reformer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\rembert\modeling_tf_rembert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\roberta\modeling_tf_roberta.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\roberta\tokenization_roberta_fast.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\roberta_prelayernorm\modeling_tf_roberta_prelayernorm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\roc_bert\modeling_roc_bert.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\roformer\modeling_tf_roformer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\shieldgemma2\modeling_shieldgemma2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\speecht5\processing_speecht5.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\switch_transformers\modeling_switch_transformers.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\t5gemma\modeling_t5gemma.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\t5gemma\modular_t5gemma.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\tapas\modeling_tapas.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\tapas\modeling_tf_tapas.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\tapas\tokenization_tapas.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\wav2vec2\tokenization_wav2vec2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\wav2vec2_phoneme\tokenization_wav2vec2_phoneme.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\wav2vec2_with_lm\processing_wav2vec2_with_lm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\whisper\generation_whisper.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\whisper\modeling_tf_whisper.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xglm\modeling_tf_xglm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlm\modeling_xlm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlm_roberta\modeling_tf_xlm_roberta.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlnet\modeling_tf_xlnet.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\xlnet\modeling_xlnet.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\zamba\configuration_zamba.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\zamba\modeling_zamba.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\zamba2\configuration_zamba2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\zamba2\modeling_zamba2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\gptsan_japanese\modeling_gptsan_japanese.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\realm\modeling_realm.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\transfo_xl\modeling_transfo_xl_utilities.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\transfo_xl\tokenization_transfo_xl.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\models\deprecated\xlm_prophetnet\modeling_xlm_prophetnet.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\continuous_batching\cache.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\continuous_batching\classes.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\generation\continuous_batching\continuous_api.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\transformers\data\processors\utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sympy\parsing\latex\lark\transformer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\base.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\create.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\engine\interfaces.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\orm\query.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\sql\base.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\sqlalchemy\ext\asyncio\engine.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\redis\auth\token_manager.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\lex.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pycparser\ply\yacc.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\test_totp.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\cli\auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\commands\user.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\inference\_client.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\utils\_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\inference\_generated\_async_client.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\inference\_generated\types\chat_completion.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elasticsearch\_sync\client\security.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\elasticsearch\_async\client\security.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_api_suite.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_auth_api_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_end_to_end_platform.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_exam_api_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_learning_path_api_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_learning_path_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_phase2_user_service.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\integration\test_user_workflow_integration.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\load\locustfile.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\property\test_endpoint_discovery.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_api_auth_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\slow\test_authentication_comprehensive.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\unit\test_api_batch1.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\tests\unit\test_services_batch1.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\services\llm\openai_provider.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\scripts\security_audit\owasp_top10_scanner.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\server.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\bridge\jpype_bridge.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\cache\redis_cache.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\tools\bpe_tokenizer.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\mcp_servers\zemberek_nlp\tools\tokenization.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\auth\jwt_handler.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\middleware\timing.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\unified\auth_system.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\core\unified\session_system.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\agents\context\context_manager.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Token in log
- **File:** `c:\Users\husey\kiro2\backend\agents\domain_experts\base_domain_agent.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\core\sensitive_data_filter.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\core\two_factor_auth.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\core\unified_config.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\huggingface_hub\_login.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\test_crypto_scrypt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\test_handlers_argon2.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\passlib\tests\utils.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\tests\performance\test_elk_performance.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Secret in log
- **File:** `c:\Users\husey\kiro2\backend\scripts\security_audit\owasp_top10_scanner.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\comprehensive_auth_test.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\setup_database.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\core\security_manager.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pydantic\types.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\urllib3\util\url.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\setuptools\_distutils\command\register.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\reportlab\lib\pdfencrypt.py`
- **Recommendation:** Never log passwords, tokens, or secrets

#### A09-003: Potential Sensitive Data Logging [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Password in print
- **File:** `c:\Users\husey\kiro2\backend\venv\Lib\site-packages\pip\_vendor\rich\prompt.py`
- **Recommendation:** Never log passwords, tokens, or secrets


### INFO Severity

#### A01-002: RBAC System Implementation [SECURE]

- **Status:** SECURE
- **Description:** RBAC system is implemented with role-based permissions
- **File:** `c:\Users\husey\kiro2\backend\core\rbac_system.py`

#### A03-003: SQL Injection Prevention Module [SECURE]

- **Status:** SECURE
- **Description:** SQL injection prevention module is implemented
- **File:** `c:\Users\husey\kiro2\backend\core\sql_injection_prevention.py`

#### A04-001: Rate Limiting Implementation [SECURE]

- **Status:** SECURE
- **Description:** Rate limiting is implemented
- **File:** `c:\Users\husey\kiro2\backend\core\advanced_rate_limiter.py`

#### A04-002: Input Validation with Pydantic [SECURE]

- **Status:** SECURE
- **Description:** Pydantic validation found in 84/105 API files

#### A05-001: DEBUG Mode Configured via Environment [SECURE]

- **Status:** SECURE
- **Description:** DEBUG mode is controlled by environment variable
- **File:** `c:\Users\husey\kiro2\backend\core\config.py`

#### A05-003: Security Headers Configured [SECURE]

- **Status:** SECURE
- **Description:** All recommended security headers are configured
- **File:** `c:\Users\husey\kiro2\backend\core\security_headers.py`

#### A06-003: Dependency Audit Recommendation [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Run 'pip-audit' for comprehensive vulnerability scan
- **Recommendation:** pip install pip-audit && pip-audit

#### A07-002: JWT Expiration Configured [SECURE]

- **Status:** SECURE
- **Description:** JWT token expiration is configured
- **File:** `c:\Users\husey\kiro2\backend\core\jwt_auth.py`

#### A07-003: Secure Password Hashing [SECURE]

- **Status:** SECURE
- **Description:** Secure password hashing algorithm found
- **File:** `c:\Users\husey\kiro2\backend\core\auth.py`

#### A07-004: Two-Factor Authentication [SECURE]

- **Status:** SECURE
- **Description:** 2FA implementation found
- **File:** `c:\Users\husey\kiro2\backend\core\two_factor_auth.py`

#### A08-002: Data Integrity Verification [REVIEW]

- **Status:** NEEDS_REVIEW
- **Description:** Manual review needed for data integrity checks
- **Recommendation:** Ensure checksums/signatures for critical data transfers

#### A09-001: Audit Logging Implementation [SECURE]

- **Status:** SECURE
- **Description:** Found 3 audit logging module(s)
- **File:** `c:\Users\husey\kiro2\backend\core\audit_logger.py`

#### A09-002: Structured Logging [SECURE]

- **Status:** SECURE
- **Description:** Structured logging is implemented
- **File:** `c:\Users\husey\kiro2\backend\core\structured_logger.py`

#### A10-002: URL Validation Present [SECURE]

- **Status:** SECURE
- **Description:** URL validation mechanism found

---

## Recommendations Summary

1. **Immediately Address:** All CRITICAL and HIGH findings marked as VULNERABLE
2. **Review Soon:** All MEDIUM findings and items marked NEEDS_REVIEW
3. **Best Practice:** Address LOW and INFO items as part of ongoing security hygiene

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

---

*Report generated by KIRO2 Security Audit Scanner*
