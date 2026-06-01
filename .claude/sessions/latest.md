## Session Handoff — 2026-06-01 (DB Kalite Temizliği — Kör-Çözüm Pipeline)
**Branch:** master
**Son commit:** 852c9ee8a docs(audit): K21 subject relabel — 991 wrong-subject (2-sinyal)
**Uncommitted:** temiz (yalnız untracked `backend/scripts/quality/_*_tmp/` çalışma artifactları)

### Yapilanlar (9 commit, hepsi backup'lı + DB doğrulandı)
- **P0** `45fe0e361`: K23 (`d-dataset/scripts/validate_3tier_selective.py`) + 3 Tier-H script mühürlendi (sys.exit(2)+ALLOW_DEPRECATED override, 0 importer)
- **P1** `991fd6d35`: beta `verified_gold`→`verified_provisional` (`backend/core/osym_exam_engine.py:1179,1186` + test + verify) + DB rename (2734) + canlı PASS
- **P2** `eb47151c5`: figür-crop PoC — "soru−cevaplar=figür" öncülü ÇÜRÜK (`docs/audits/2026-06-01_p2_figure_crop_poc.md`)
- **628 dispute** `f1203ae5e`: kör re-solve (Workflow) → 480 REAL_ERROR→pending (canlı yanlış-cevap gold'dan çıktı), 69 false, 30 split, 47 unsolv
- **270 cevap düzeltme** `3a44dbc49`+`b49eae653`: 148+135 MAT/GEO 3-sinyal → correct_answer düzeltildi (%97 hizalanma)
- **202 concept curator-ready** `2e91e4e52`+`ae3881e49`: `dispute_suggestion` metadata + `backend/api/curator.py` QueueItem alanı (docker'a cp'lendi)
- **991 subject relabel** `852c9ee8a`: K21 2-sinyal (`docs/audits/2026-06-01_subject_relabel_k21.md`)

### Fail Eden Testler
- YOK (test koşulmadı — değişiklik metadata/DB + audit doc; curator.py py_compile+ruff temiz, container smoke PASS)

### Engelleyiciler
- `backend/api/curator.py` docker'a `docker cp`'lendi (canlı smoke PASS) ama **kalıcılık için `docker compose build backend` gerek** (git'te commit'li)
- DB yazma Git Bash'ten `PGPASSWORD=1470 "C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434` ile (pg_isready PATH'te yok; full path çalışıyor). Türkçe inline `-c` bozuk → `-f` veya ASCII label kullan.

### Sonraki Adimlar (maks 5)
1. **202 concept + 85 split + 8 uncertain → curator manual** (dispute_suggestion API'de hazır; frontend render follow-up)
2. **884 blind_unsolvable** (hepsi image_url'li=figür-bağımlı, frontend `false &&` gizliyor) → P2 figür pipeline VEYA interim demote
3. **P2 (figür render+crop)** veya **K2 (re-OCR, 61K garbled)** — asıl kilit, çok-oturumluk infra
4. (Opsiyonel) Tam P3: 2,734 verified_provisional → farklı modelle gold terfi
5. curator.py kalıcılık için backend rebuild

### Kararlar (gelecek session tekrar tartismasin)
- **Kör-çözüm = doğru araç** (DB cevabı solver'a VERİLMEZ = K1b dairesellik panzehiri). MAT/GEO deterministik→auto-correct; concept=yargı→curator (ortak-bias riski, auto-correct YASAK).
- **correct_answer overwrite yalnız 3-sinyal hizalanınca** (orig_blind+new_blind+verify3). prev-disagree flip-flop hariç.
- **subject_area relabel yalnız geçerli DB değerlerine** (FELSEFE/DIN sistemde yok → SOSYAL şemsiyesi, dokunma).
- Ucuz quality-hygiene damarı BİTTİ; kalan değer P2/K2 infra'da.
