# Brainstorm: IRT/CAT/Placement Refactoring Stratejisi
Tarih: 2026-03-26 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet

## TL;DR
Conftest revert + hibrit strateji en dusuk maliyetle en yuksek kazanci verir. Eski conftest'i geri koy (5,146 testi kurtar), yeni CAT/IRT servisleri backend/app/ altinda kalsin, pytest.ini'ye `pythonpath = . app` ekleyerek import cakismasini coz. Gizli mayin: iki farkli get_redis() tanimi (main.py vs app.core.deps) sessizce None donup CAT session state'i kaybedebilir.

## Top 5 Aksiyon
1. **conftest.py revert** — `git checkout -- backend/tests/conftest.py` ile eski 1,079 satirlik halini geri koy. Etki: 5/5 - Zorluk: Kolay - Kaynak: Maliyet+Bakim
2. **pytest.ini'ye `pythonpath = . app` ekle** — `from services.xxx` import'larini cozer, sys.path hack'i gereksiz kalir. Etki: 4/5 - Zorluk: Kolay - Kaynak: Bakim
3. **main.py'deki `get_redis()` kaldir** — app.core.deps.get_redis tek kaynak olsun, cift Redis baglantisi riski sifirlansin. Etki: 4/5 - Zorluk: Kolay - Kaynak: Performans
4. **Yeni CAT/IRT testlerini backend/tests/ altinda tut** ama kendi conftest_cat.py fixture dosyasi ile izole et. Etki: 3/5 - Zorluk: Orta - Kaynak: Bakim
5. **PlacementWidget + frontend untracked dosyalari commit et** — aksi halde PlacementAssessmentPage kirik kalir. Etki: 3/5 - Zorluk: Kolay - Kaynak: Maliyet

## Konsensus
- **conftest.py kesinlikle revert**: 3/3 perspektif hemfikir — 18 satirlik minimal versiyon 5,146 test kaybina degmez
- **Yeni backend/app/ kodu korunmali**: Hicbir perspektif "tumu sil" demedi. CAT/IRT servisleri degerli, sorun sadece test altyapisi entegrasyonu
- **Import path standardizasyonu sart**: Hem Bakim hem Performans perspektifi sys.path hack'inin kirilgan oldugunu belirtti

## Catismalar
| Konu | Taraf A | Taraf B | Onerilen karar |
|------|---------|---------|----------------|
| Yeni branch vs master'da devam | Maliyet: branch=1-2 gun, merge conflict riski | Bakim: master'da kalma daha az overhead | **Master'da kal** — branch overhead'i degerli degil, degisiklikler izole edilebilir |
| conftest hibrit vs ayri conftest | Bakim: hibrit (path ekle + fixture koru) | Performans: kok conftest'e dokunma, ayri dosya | **Hibrit**: pytest.ini pythonpath ile path sorununu coz, kok conftest'e dokunma |
| Router yukleme eager vs lazy | Performans: lazy yukle (test ortaminda skip) | Maliyet: eager daha basit, try/except zaten var | **Eager tut** — try/except fallback yeterli, lazy complexity gereksiz |

## Perspektif Detaylari

### Performans Muhendisi
1. **isolate_environment autouse fixture overhead**: conftest:859'daki os.environ.copy/clear/update her testte calisiyor — 5K+ testte ciddi overhead. Etki: 4/5, Kolay
2. **Router yuklemeyi lazy'e cek**: 6 yeni router cold-start suresini artiriyor. TESTING=true ile devre disi birak. Etki: 3/5, Orta
3. **IRT EAP hesaplamalarini Redis cache'le**: Her yanit tam integral hesapliyor, session ID key ile cache'lemek p95'i dusurur. Etki: 4/5, Orta

Kor nokta: main.py:86 `_redis_pool = None` vs cat.py:24 `app.core.deps.get_redis` — iki ayri Redis baglantisi, test ortaminda ikisi de None donuyor, CAT session state kayboluyor.

Uyari: Revert yapmayin dedi — ama bu conftest icerigi okuma hatasindan kaynaklandi (stash pop sonrasi eski conftest gordu). Gercekte conftest revert DOGRUDIR.

### Bakim/Maintainability Uzmani
1. **conftest.py hibrit model**: .bak'taki path setup'i mevcut conftest'in USTUNE ekle, YERINE gecirme. Etki: 5/5, Orta
2. **Ayri conftest_cat.py**: Yeni CAT/IRT testleri icin izole fixture dosyasi. Etki: 4/5, Kolay
3. **pytest.ini pythonpath direktifi**: `pythonpath = . app` ile sys.path.insert hack'ini kaldir. Etki: 4/5, Kolay

Kor nokta: 1079 satirlik conftest'teki question_factory `from models.database import Question` ile BOS tabloyu kullaniyor. IRT/CAT testleri QuestionBankItem bekliyor — hibrit yaparken factory sessizce bos veri donebilir.

Uyari: .bak dosyasini direkt conftest.py ile swap etmeyin.

### Maliyet/Zaman Analisti
Secenek karsilastirmasi:
- A (Tumu revert): 1-2 saat, ama untracked dosyalar kaybolabilir. Etki: 2/5
- B (Conftest revert + geri kalani tut): 3-5 saat. Etki: 4/5 — ONERILEN
- C (Yeni branch): 1-2 gun, merge conflict riski. Etki: 5/5 ama maliyet yuksek

Kor nokta: conftest.bak zaten mevcut, restore tek komut — maliyet sanildigindan cok dusuk.

Uyari: `git checkout` yerine .bak uzerinden el ile restore edin dedi — ama aslinda git checkout dogrudan eski commit'teki halini getirir, .bak ile karistirma riski yok.

## Kor Noktalar & Uyarilar
1. **Cift Redis kaynagi**: main.py get_redis() vs app.core.deps.get_redis — sessiz None donusu
2. **Question vs QuestionBankItem**: Eski conftest factory'si BOS tabloyu kullaniyor, yeni testler production tabloyu bekliyor
3. **backend/api/ vs backend/app/api/ namespace cakismasi**: pytest.ini pythonpath eklenirken `from api.cat` hangisini secer belirsiz
4. **Untracked dosya kaybi riski**: git clean veya toplu revert untracked app/ dizinini silebilir
5. **nginx.conf ortam bagimliligi**: host.docker.internal Docker Compose'da calismaz, sadece host-backend icin gecerli
