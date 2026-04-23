# Chroma (F1 / plan §8) — operasyon checklist + FE kararı

**Tarih:** 2026-04-23  
**Kaynak plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md` §8.

## Altyapı

- [ ] `docker compose -f docker-compose.dev.yml --profile chroma up` ile servis ayakta.  
- [ ] Volume: restart sonrası koleksiyon kalıcılığı doğrulandı.  
- [ ] Backend env: `CHROMADB_HOST`, `CHROMADB_PORT` — TLS yoksa dokümante `http://`.

## Embedding

- [ ] Model / API anahtarı tanımlı; anahtar yoksa **DUR** (sahte vektör üretme).  
- [ ] Koleksiyon boyutu ↔ embedding boyutu uyumu.

## Ingest

- [ ] Kaynak: `question_bank` veya onaylı pipeline çıktısı.  
- [ ] Idempotent job: iki kez çalışınca tutarlı (ör. `scripts/chroma_seed_kiro2_questions.py`).  
- [ ] J10 için minimum kayıt veya anlamlı “boş sonuç” JSON.

## Router dörtlüsü (J10–J13)

- [ ] `GET .../search/health`, `.../recommendations/health`, `.../duplicates/health` — `chroma_connection_mode` alanı.  
- [ ] Öğrenci: 401/403 kuralları; boş sonuç tanımlı JSON; **5xx yok**.

## J10–J13 frontend kararı (matris)

| Journey | Karar (2026-04-23) |
|---------|---------------------|
| J10 Semantic | **API-first**; FE route TBD — öğrenci UI’si ikinci faz. |
| J11 Recommendation | **API-first**; FE, dashboard entegrasyonu kademeli. |
| J12 Clustering | **API-only** (matris notu ile uyumlu); admin/analitik UI isteğe bağlı. |
| J13 Duplicate | **API-first**; içerik yönetimi ekranı sonra. |

**Gerekçe:** DoD ve Chroma ayakta olmadan “arama tamam” denmez; FE, API sözleşmesi kilitlendikten sonra bağlanır.
