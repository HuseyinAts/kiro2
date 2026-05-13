# quality_review_status — Convention v2

**Tarih:** 15 May 2026
**Yazan:** Claude session
**Trigger:** 14 May audit'inin "approved %87 hatalı" bulgusu +
`import_d_dataset.py:212` hardcoded literal'in kanıtlanması.

---

## Mevcut durum (v1 — 15 May öncesi)

| Değer | Anlam (iddia edilen) | Anlam (gerçek) |
|---|---|---|
| `pending` | İlk insert default, hiç işlenmemiş | DB schema default'u, ~2,775 satır |
| `unverified` | Pipeline otomatik etiketledi, manuel onay yok | v4.14e Gemini Flash çıktısı, ~143,078 satır |
| `approved` | **Manuel kalite review'dan geçti** | **HARDCODED literal**, ~17,950 satır, manuel onay YOK |

**Sorun:** `approved` etiketi insan değerlendirmesi gibi gözüküyor ama
sadece `import_d_dataset.py:212`'deki bir Python string'i. 14 May audit'i
%87 hata oranı gösterdi.

---

## Yeni convention (v2 — 15 May)

| Değer | Anlam | Set eden | Beta'ya uygun |
|---|---|---|---|
| `pending` | İlk insert default, hiç işlenmemiş | DB schema | ❌ |
| `unverified` | Pipeline otomatik etiketledi, manuel onay yok | Pipeline post-process | ❌ |
| `legacy_v3_unaudited` | v3.5 import'undan otomatik "approved" alan, **gerçek manuel onay almamış** satırlar | Migration `D2_legacy_approved_downgrade` | ❌ |
| `human_verified` | **Gerçek insan onayı geçirdi** — curator workflow tamamlanmış | Curator UI / manuel SQL | ✅ |
| `auto_judged_high` | LLM-as-judge yüksek güven ile onayladı (geleceğe) | Judge pipeline | ⚠ Sınırlı |
| `rejected` | Curator/judge tarafından reddedildi, beta'ya alınmaz | Curator UI / judge | ❌ |
| `archived` | Soft-delete marker (is_active=False ile birlikte). Production'da `question_crud_service` kullanıyor | CRUD endpoint | ❌ |

### CHECK constraint (önerilen)

```sql
ALTER TABLE question_bank
  DROP CONSTRAINT IF EXISTS quality_review_status_check;

ALTER TABLE question_bank
  ADD CONSTRAINT quality_review_status_check
  CHECK (quality_review_status IN (
    'pending',
    'unverified',
    'legacy_v3_unaudited',
    'human_verified',
    'auto_judged_high',
    'rejected',
    'archived'
  ));
```

**Eski değer `approved` artık YASAK** — `legacy_v3_unaudited`'a downgrade
edilir.

---

## Migration yolu (D2 ile birlikte)

1. **D1** — `import_d_dataset.py:212` hardcoded'u kaldır (DB default'una bırak).
   Bu script tekrar çalışırsa yeni satırlar `pending` olur.
2. **D2** — Mevcut `approved` satırlarını `legacy_v3_unaudited`'a çevir
   (yaklaşık 17,950 satır).
3. **D3** — CHECK constraint güncellemesi (Alembic migration).
4. **D4** — `v_safe_for_beta` view yeniden tanımı: `approved` ve
   `legacy_v3_unaudited` artık güvenli sayılmaz. Sadece `human_verified`
   ve (geleceğe) `auto_judged_high` kabul edilir.

## v_safe_for_beta yeni filter (önerilen)

```sql
CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT * FROM v_safe_for_beta_unfiltered
WHERE quality_review_status IN ('human_verified', 'auto_judged_high')
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'));
```

**Beklenen pool boyutu (post-migration):** **0 satır** — şu anda hiç
`human_verified` satır yok. Bu **doğru bir sıfır** — pool'u yeniden inşa
etmenin gerçek başlangıç noktası.

---

## Acil sonuç

Manuel curator workflow kurulana kadar `v_safe_for_beta` boş kalır.
Beta launch **bu pool'un üzerine yapılamaz**. Bu rahatsız edici ama
**dürüst** durum — eski `v_safe_for_beta` (81,760 satır) %61 hatalı
veriyi "güvenli" olarak gösteriyordu.

## Geri uyumluluk

Eski callsite'lar `quality_review_status='approved'` ile sorgu yapıyorsa
**boş sonuç döner**. 3 bilinen dosya update gerektirir:
- `backend/core/osym_exam_engine.py`
- `backend/app/services/cat_session.py`
- `backend/app/services/placement_service.py`

Bu dosyalar D5 adımında güncellenir.
