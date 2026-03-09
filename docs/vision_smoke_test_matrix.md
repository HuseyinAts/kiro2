# Vision Smoke Test Matrix

## Setup

```powershell
cd C:\Users\husey\kiro2\d-dataset\scripts
```

## 1-Question Smoke (Fast)

```powershell
python .\vision_solve_codex.py --sample 1 --seed 123 --workers 1 --timeout 150 --min-interval 1.0 --model gpt-5.2-codex
python .\vision_solve_gemini.py --sample 1 --seed 123 --workers 1 --timeout 150
python .\vision_solve_opus.py --sample 1 --seed 123 --workers 1 --timeout 180
```

## 5-Question Smoke (Stability)

```powershell
python .\vision_solve_codex.py --sample 5 --seed 123 --workers 1 --timeout 150 --min-interval 1.0 --model gpt-5.2-codex
python .\vision_solve_gemini.py --sample 5 --seed 123 --workers 1 --timeout 150
python .\vision_solve_opus.py --sample 5 --seed 123 --workers 1 --timeout 180
```

## Result Checks

```powershell
Get-Content ..\processed\vision_solve_codex\vision_results.jsonl -Tail 3
Get-Content ..\processed\vision_solve_gemini\vision_results.jsonl -Tail 3
Get-Content ..\processed\vision_solve_sonnet\vision_results.jsonl -Tail 3
```

## Pass Criteria

- Preflight fails only for auth/quota/model access issues.
- No `"error":"cannot_solve"` entries caused by missing instructions.
- At least one solved record with non-empty `ai_answer` for each model.
- Output lines are valid JSON and include `book_name`, `page_number`, `question_number`.
