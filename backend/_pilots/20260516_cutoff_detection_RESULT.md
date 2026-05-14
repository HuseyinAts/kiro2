# Cut-off Detection — 16 May 2026

**Total satır**: 4,994

## Verdict Dağılımı

| Verdict | Count | % | Aksiyon |
|---|---|---|---|
| `ok` | 4,939 | %98.9 | → DB korunur, Re-OCR yapılmaz |
| `unclear` | 37 | %0.7 | → Manuel review veya Re-OCR ile sample |
| `cutoff` | 18 | %0.4 | → Re-OCR adayı |

## Reason Dağılımı

| Reason | Count |
|---|---|
| `valid_end_?` | 4,723 |
| `valid_end_)` | 164 |
| `valid_end_.` | 48 |
| `unknown_end_$` | 36 |
| `alphanumeric_end` | 15 |
| `has_question_ending` | 4 |
| `few_words` | 2 |
| `unknown_end_}` | 1 |
| `latex_odd_dollar` | 1 |
