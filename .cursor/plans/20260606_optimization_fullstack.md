# Plan: E2E Full-Stack Query & Algorithm Optimization (N+1 Query Elimination & Unit Test Fixes)

**Tarih:** 2026-06-06
**Tür:** Kod Entegrasyonu ve Performans İyileştirme
**Yürütücü:** Antigravity (YOLO modunda, kendi kendine test ve onarım)
**Hedef Dosyalar:**
- `backend/services/offline_sync_service.py`
- `backend/tests/unit/services/test_offline_sync_service.py`
- `backend/services/learning_event_service.py`
- `backend/tests/unit/test_learning_event_service.py`
- `backend/tests/unit/test_exam_event_wiring.py`
**Süre Tahmini:** 45 dakika
**Risk Seviyesi:** Düşük-Orta (Tüm değişiklikler unit testler ve dry-run'larla doğrulanacaktır)

---

## 1. Neden Bu Plan?
1. **N+1 Sorgularının Yok Edilmesi**: `detect_n_plus_1.py` taramasında en yüksek öncelikli N+1 problemleri arasında `offline_sync_service` (4 kritik bulgu) ve `learning_event_service` (8 kritik bulgu) yer almaktadır. Bu servislerdeki döngü içi veritabanı sorgularını toplu (batch) sorgulara dönüştürerek veritabanı yuvarlak geçişlerini (RTT) azaltacağız.
2. **Kırık Unit Testlerin Düzeltilmesi**: `test_learning_event_service.py` ve `test_exam_event_wiring.py` içerisindeki 3 test, S180/S179 değişikliklerinden dolayı `topic_hierarchy` sorgularının mock edilmemesi nedeniyle "Placement seed skipped" uyarısıyla başarısız olmaktadır. Bu testlerin mock verilerini güncelleyip hem performansı iyileştireceğiz hem de test paketinin %100 pass olmasını sağlayacağız.

---

## 2. Tespit Edilen Bulgular ve Çözüm Ayrıntıları

### A. `backend/services/offline_sync_service.py`
- **Mevcut Durum**: `process_sync_results` metodu içinde her bir test sonucu için `QuestionBankItem` ve `FSRSCard` tablosuna tek tek sorgu atılıyor.
- **Hedef Çözüm**:
  1. `results` listesindeki tüm benzersiz `question_id` değerlerini topla.
  2. Tek bir `select(QuestionBankItem)` ile bu ID'leri `in_` filtresiyle çek.
  3. Tek bir `select(FSRSCard)` ile öğrencinin bu ID'leri içeren kartlarını `or_` ve `contains` filtresiyle çek.
  4. Bellekte eşleştirip güncellemeleri yap.

### B. `backend/services/learning_event_service.py`
- **Mevcut Durum**: `on_assessment_completed` metodu içinde her ders için ayrı `topic_hierarchy` sorgusu atılıyor, her ders için `StudentAbility` upsert'i yapılıyor ve her bir `topic_id` için `BKTState` insert'i tek tek döngüde yapılıyor.
- **Hedef Çözüm**:
  1. Gelen tüm ders adlarını (subject) topla.
  2. Tek bir ORM sorgusuyla bu derslere ait aktif `TopicHierarchy` kayıtlarını çek:
     ```python
     select(TopicHierarchy.id, TopicHierarchy.subject_area).where(
         and_(TopicHierarchy.subject_area.in_(subjects_upper), TopicHierarchy.is_active == True)
     )
     ```
  3. `StudentAbility` ve `BKTState` için postgresql `pg_insert` komutlarına toplu değer listesi (`.values(list_of_dicts)`) vererek tek bir veritabanı çağrısıyla bulk upsert gerçekleştir.

### C. Unit Testler ve Mocking
- **`test_offline_sync_service.py`**: Batch sorgu yapısına uygun mock dönüşleri (`.scalars().all()`) sağlayacak şekilde `db.execute` mock'unu güncelle.
- **`test_learning_event_service.py`** & **`test_exam_event_wiring.py`**: `on_assessment_completed` testlerinde mock DB'nin `topic_hierarchy` sorgusuna sahte konu ID'leri dönmesini sağla, böylece "Placement seed skipped" uyarısı ortadan kalksın ve testler geçsin.

---

## 3. Yapılacak Değişiklikler (Taslak)

### 3.1. `offline_sync_service.py`
`process_sync_results` fonksiyonu içerisinde:
```python
    # 1. Collect question IDs
    question_ids = [item["question_id"] for item in results if "question_id" in item]
    
    # 2. Batch fetch questions
    questions_map = {}
    if question_ids:
        q_result = await db.execute(
            select(QuestionBankItem).where(
                and_(
                    QuestionBankItem.id.in_(question_ids),
                    QuestionBankItem.is_active == True,
                )
            )
        )
        questions_map = {q.id: q for q in q_result.scalars().all()}
        
    # 3. Batch fetch FSRSCards
    cards = []
    if question_ids:
        from sqlalchemy import or_
        clauses = [FSRSCard.front_text.contains(qid) for qid in question_ids]
        card_result = await db.execute(
            select(FSRSCard).where(
                and_(
                    FSRSCard.student_id == student_id,
                    or_(*clauses)
                )
            )
        )
        cards = card_result.scalars().all()
```
Döngü içinde ise bu cached yapılardan sorgu sonucunu alacağız.

### 3.2. `learning_event_service.py`
`on_assessment_completed` fonksiyonu içerisinde:
```python
        # Batch fetch topic_ids for all subjects at once
        from models.question_bank import TopicHierarchy
        subjects_upper = [s.upper() for s in subjects.keys()]
        
        topic_rows = await db.execute(
            select(TopicHierarchy.id, TopicHierarchy.subject_area).where(
                and_(
                    TopicHierarchy.subject_area.in_(subjects_upper),
                    TopicHierarchy.is_active == True
                )
            )
        )
        
        from collections import defaultdict
        topics_by_subject = defaultdict(list)
        for row in topic_rows.all():
            subj = row.subject_area.lower() if row.subject_area else ""
            topics_by_subject[subj].append(str(row.id))
```
Ve bulk `pg_insert` kullanarak toplu kayıt ekle/güncelle.

---

## 4. Uygulama Adımları ve Doğrulama
1. `backend/services/offline_sync_service.py` dosyasını güncelle.
2. `backend/tests/unit/services/test_offline_sync_service.py` dosyasını güncelle.
3. `backend/services/learning_event_service.py` dosyasını güncelle.
4. `backend/tests/unit/test_learning_event_service.py` ve `backend/tests/unit/test_exam_event_wiring.py` dosyalarını güncelle.
5. `python -m pytest` komutunu çalıştırarak tüm testlerin başarılı olduğunu doğrula.
6. `ULTRA_ARCHITECTURE_REPORT.md` dosyasını oluştur.
