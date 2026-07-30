# Kalan Görevler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** KIRO2'de doğrulanmış olarak kalan 4 iş izini kapatmak — `/api/v1/me` agregasyon ucu, öğretmen roster silme UI'ı, iki kaynak-hijyeni temizliği ve ES indeks kapısı.

**Architecture:** Her iz bağımsız sevk edilebilir ve kendi başına çalışan yazılım üretir. A izi backend'e yeni bir okuma ucu ekler (frontend'de 0 değişiklik); B izi mevcut canlı DELETE ucunu UI'a bağlar; C izi iki dosya hijyeni; D izi ölçümle başlar çünkü "ES kapıyı tanımıyor" iddiası henüz doğrulanmadı.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async (backend), React 18 + TypeScript (frontend), PostgreSQL 18 @5434, Elasticsearch (harici ağ, `turkiye_sinav_elasticsearch`), pytest + vitest.

---

## Doğrulama Durumu (30 Tem 2026, plan yazılmadan ÖNCE ölçüldü)

| Görev | İddia | Ölçüm | Verdict |
|---|---|---|---|
| #447 | `/api/v1/me` yok | canlı **404** | GERÇEK |
| #433 | "ES yok → bloklu" | container 11 saattir up, `:9200` → **200** | **BLOKER FANTOM** |
| #444 | ekleme UI + uydurma fallback + silme | ekleme VAR (`:76`), fallback zaten silinmiş (`:111` yorum), **silme YOK** | %70 bitmiş |
| #458a | mojibake | 149 çift-kodlanmış dizi | GERÇEK |
| #458b | `fix_validators.py` referanssız | 0 referans | GERÇEK |

**Plana ALINMAYANLAR (operatör önkoşulu, kod işi değil):** #270 GitHub Actions · #390 gh CLI/Dependabot · #436 faturalama penceresi · #441 SMTP kimlik bilgisi · #445 73 STUDENT hesabının iş-kararı triyajı.

---

## File Structure

**A izi — `/api/v1/me`**
- Create `backend/api/me.py` — tek router, tek GET. Sadece HTTP katmanı: auth bağımlılığı + servis çağrısı + şema.
- Create `backend/schemas/persona.py` — Pydantic yanıt şeması; frontend `Persona` tipiyle birebir alan adları.
- Create `backend/services/persona_service.py` — tek sorguda `users` + `student_profiles` + `streaks` join; sıralama için window function.
- Modify `backend/api/routers/loader.py` — ROUTER_MAPPING kaydı (kayıtsız router = 404, testing.md #27).
- Create `backend/tests/api/test_me_endpoint.py` — sözleşme + auth + alan kaynağı testleri.
- Modify `frontend/src/kiro/types/types.ts` — kaynağı olmayan 3 alan `| null` yapılır (uydurma YASAK).

**B izi — roster silme UI**
- Modify `frontend/src/pages/ModernTeacherStudentsPage.tsx` — satır sonu "Çıkar" butonu + DELETE çağrısı + iyimser liste güncellemesi.
- Create `frontend/src/pages/__tests__/ModernTeacherStudentsPage.delete.test.tsx` — buton → DELETE → liste güncellenir.

**C izi — hijyen**
- Modify `backend/tests/integration/test_end_to_end_platform.py` — çift kodlama geri çevrilir.
- Delete `backend/fix_validators.py` + Modify `backend/pyproject.toml` (per-file-ignores girdisi kaldırılır).

**D izi — ES**
- Create `backend/scripts/quality/es_gate_audit.py` — ES indeksindeki soruların kapıya (`mv_safe_for_beta`) uyup uymadığını ÖLÇER. Reindex kararı ölçümden SONRA.

---

## Track A — `GET /api/v1/me` agregasyon ucu

### Task A1: Alan kaynaklarını canlı DB'de doğrula

**Files:**
- Create: `backend/scripts/quality/persona_source_probe.py`

- [ ] **Step 1: Probe script'ini yaz**

```python
"""Persona alanlarinin canli DB'de gercekten dolu olup olmadigini olcer (#447 A1)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text  # noqa: E402

from core.database import get_db_session_context  # noqa: E402

SORGU = text(
    """
    SELECT
      (SELECT count(*) FROM users)                                   AS kullanici,
      (SELECT count(*) FROM users WHERE total_xp > 0)                AS xp_dolu,
      (SELECT count(*) FROM users WHERE level > 1)                   AS seviye_dolu,
      (SELECT count(*) FROM streaks)                                 AS streak_satiri,
      (SELECT count(*) FROM student_profiles)                        AS profil,
      (SELECT count(*) FROM student_profiles
         WHERE target_university IS NOT NULL)                        AS hedef_uni_dolu,
      (SELECT count(*) FROM student_profiles
         WHERE study_hours_per_day IS NOT NULL)                      AS gunluk_saat_dolu
    """
)


async def main() -> int:
    async with get_db_session_context() as oturum:
        satir = (await oturum.execute(SORGU)).mappings().one()
    for ad, deger in satir.items():
        print(f"  {ad:20s}: {deger}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

- [ ] **Step 2: Çalıştır ve çıktıyı kaydet**

Run: `cd /c/Users/husey/kiro2/backend && python scripts/quality/persona_source_probe.py`
Expected: her satır bir sayı. `streak_satiri` veya `profil` **0 ise** o alanlar v1'de `null` döner ve Task A3'teki şema o şekilde yazılır.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/quality/persona_source_probe.py
git commit -m "chore(me): Persona alan kaynaklari canli DB'de olculdu (#447 A1)"
```

---

### Task A2: RED — sözleşme testi

**Files:**
- Create: `backend/tests/api/test_me_endpoint.py`

- [ ] **Step 1: Testi yaz**

```python
"""GET /api/v1/me sozlesmesi (#447).

Bu uc 30 cagri yerinin (19 ekran) tek veri kaynagi. Sozlesme: 15 anahtar HER
ZAMAN mevcut; kaynagi olmayan alan `None` doner. UYDURMA DEGER YASAK — #444'te
silinen "uydurma ogrenci fallback" desenine donmemek icin.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.security]

PERSONA_ANAHTARLARI = {
    "ad", "adKisa", "bas", "sinif", "seri", "seriRekor", "xp", "seviye",
    "hedefBolum", "hedefUni", "hedefSiralama", "guncelSiralama",
    "yksTarihi", "gunlukHedefDk", "bugunCozulenDk",
}


def test_auth_yoksa_401(client: TestClient):
    """Kimliksiz erisim persona sizdirmamali."""
    assert client.get("/api/v1/me").status_code == 401


def test_ogrenci_15_anahtarin_tamamini_alir(client: TestClient, ogrenci_headers):
    """Sozlesme: eksik anahtar YOK. Frontend Persona tipi 15 alani zorunlu sayar."""
    yanit = client.get("/api/v1/me", headers=ogrenci_headers)
    assert yanit.status_code == 200
    assert set(yanit.json()) == PERSONA_ANAHTARLARI


def test_bas_ad_soyaddan_turetilir(client: TestClient, ogrenci_headers):
    """`bas` = bas harfler. Turkce buyuk harf kurali: i -> I DEGIL, i -> Ilk harf."""
    veri = client.get("/api/v1/me", headers=ogrenci_headers).json()
    assert len(veri["bas"]) in (1, 2)
    assert veri["bas"] == veri["bas"].upper()


def test_sayisal_alanlar_negatif_olamaz(client: TestClient, ogrenci_headers):
    """KORLESME GUVENCESI: xp/seri/seviye gercek kolondan gelir, uydurulmaz."""
    veri = client.get("/api/v1/me", headers=ogrenci_headers).json()
    for alan in ("xp", "seviye", "seri", "seriRekor"):
        assert veri[alan] is not None, f"{alan} kaynagi var, None olamaz"
        assert veri[alan] >= 0
```

- [ ] **Step 2: RED doğrula**

Run: `cd backend && python -m pytest tests/api/test_me_endpoint.py -q`
Expected: FAIL — 404 (router yok). `test_auth_yoksa_401` da 404 alıp düşer.

- [ ] **Step 3: Commit (RED testler)**

```bash
git add backend/tests/api/test_me_endpoint.py
git commit -m "test(me): GET /api/v1/me sozlesme testleri (RED, #447 A2)"
```

---

### Task A3: GREEN — şema + servis + router

**Files:**
- Create: `backend/schemas/persona.py`
- Create: `backend/services/persona_service.py`
- Create: `backend/api/me.py`
- Modify: `backend/api/routers/loader.py`

- [ ] **Step 1: Pydantic şeması**

```python
"""GET /api/v1/me yanit semasi — frontend Persona tipiyle BIREBIR (#447)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PersonaResponse(BaseModel):
    """15 alan HER ZAMAN mevcut; kaynagi olmayan alan None.

    None = "bu veri sistemde YOK". Sifir/bos string DEGIL — cunku 0 XP ile
    "XP bilinmiyor" ayni sey degil ve uydurma deger bu depoda yasak (#444).
    """

    model_config = ConfigDict(populate_by_name=True)

    ad: str
    adKisa: str
    bas: str
    sinif: str | None
    seri: int | None
    seriRekor: int | None
    xp: int | None
    seviye: int | None
    hedefBolum: str | None
    hedefUni: str | None
    hedefSiralama: int | None
    guncelSiralama: int | None
    yksTarihi: str | None
    gunlukHedefDk: int | None
    bugunCozulenDk: int | None
```

- [ ] **Step 2: Servis — tek sorgu**

```python
"""Persona agregasyonu: users + student_profiles + streaks tek sorguda (#447)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.persona import PersonaResponse

# Tek sorgu: N+1 YOK. guncelSiralama window function ile GERCEK veriden
# hesaplanir (total_xp'ye gore), uydurulmaz.
_SORGU = text(
    """
    WITH siralama AS (
        SELECT id, RANK() OVER (ORDER BY total_xp DESC) AS sira
        FROM users WHERE is_active = TRUE
    )
    SELECT u.first_name, u.last_name, u.total_xp, u.level,
           s.current_streak, s.largest_streak,
           p.grade_level, p.target_department, p.target_university,
           p.study_hours_per_day,
           r.sira
    FROM users u
    LEFT JOIN streaks s          ON s.user_id = u.id
    LEFT JOIN student_profiles p ON p.user_id = u.id
    LEFT JOIN siralama r         ON r.id = u.id
    WHERE u.id = :kullanici_id
    """
)


def _bas_harfler(ad: str, soyad: str) -> str:
    """Avatar bas harfleri. Turkce: 'i' -> 'I' DEGIL 'İ'."""
    harfler = [k[0] for k in (ad, soyad) if k]
    return "".join(harfler).replace("i", "İ").upper()


async def persona_getir(oturum: AsyncSession, kullanici_id: str) -> PersonaResponse:
    satir = (await oturum.execute(_SORGU, {"kullanici_id": kullanici_id})).mappings().one()
    ad = satir["first_name"] or ""
    soyad = satir["last_name"] or ""
    saat = satir["study_hours_per_day"]
    return PersonaResponse(
        ad=f"{ad} {soyad}".strip(),
        adKisa=ad,
        bas=_bas_harfler(ad, soyad),
        sinif=str(satir["grade_level"]) if satir["grade_level"] is not None else None,
        seri=satir["current_streak"],
        seriRekor=satir["largest_streak"],
        xp=satir["total_xp"],
        seviye=satir["level"],
        hedefBolum=satir["target_department"],
        hedefUni=satir["target_university"],
        # Kaynagi olmayan 3 alan — A1 olcumu bunlari dolduracak bir kolon
        # bulamadi; uydurmak yerine None doneriz.
        hedefSiralama=None,
        yksTarihi=None,
        bugunCozulenDk=None,
        guncelSiralama=satir["sira"],
        gunlukHedefDk=saat * 60 if saat is not None else None,
    )
```

- [ ] **Step 3: Router**

```python
"""GET /api/v1/me — frontend getMe() tek veri kaynagi (#447)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_user, get_db
from schemas.persona import PersonaResponse
from services.persona_service import persona_getir

router = APIRouter(prefix="/api/v1", tags=["me"])


@router.get("/me", response_model=PersonaResponse, summary="Oturumdaki kullanicinin personasi")
async def me(
    mevcut: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    return await persona_getir(db, mevcut.id)
```

- [ ] **Step 4: loader.py kaydı (ATLANIRSA 404 — testing.md #27)**

`backend/api/routers/loader.py` içindeki `ROUTER_MAPPING` sözlüğüne ekle:

```python
    "api.me": ("core", "api.me"),
```

- [ ] **Step 5: GREEN doğrula**

Run: `cd backend && python -m pytest tests/api/test_me_endpoint.py -q`
Expected: 4 passed

- [ ] **Step 6: Canlı duman testi**

Run: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/me`
Expected: `401` (404 DEĞİL — router yüklendi, auth kapısı çalışıyor)

- [ ] **Step 7: Commit**

```bash
git add backend/schemas/persona.py backend/services/persona_service.py backend/api/me.py backend/api/routers/loader.py
git commit -m "feat(me): GET /api/v1/me agregasyon ucu (#447 A3)"
```

---

### Task A4: Frontend tipini gerçeğe uydur

**Files:**
- Modify: `frontend/src/kiro/types/types.ts:47-62`

- [ ] **Step 1: Kaynağı olmayan alanları nullable yap**

`Persona` içinde şu üç satırı değiştir:

```typescript
  hedefSiralama: number | null;   // #447: kalici kolon YOK, null doner
  yksTarihi: string | null;       // #447: learning_path.exam_date ayri tabloda
  bugunCozulenDk: number | null;  // #447: gunluk dakika toplami kolonu YOK
```

- [ ] **Step 2: Tip kontrolü**

Run: `cd frontend && npx tsc --noEmit`
Expected: bu üç alanı guard'sız okuyan yerler hata verir — her biri `?? '—'` ile düzeltilir.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/kiro/types/types.ts
git commit -m "fix(kiro): Persona'da kaynagi olmayan 3 alan nullable (#447 A4)"
```

---

## Track B — Öğretmen roster silme UI

### Task B1: RED — silme testi

**Files:**
- Create: `frontend/src/pages/__tests__/ModernTeacherStudentsPage.delete.test.tsx`

- [ ] **Step 1: Testi yaz**

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import ModernTeacherStudentsPage from '../ModernTeacherStudentsPage';

describe('Ogretmen ogrenci listesi — cikarma', () => {
  it('Cikar butonu DELETE atar ve satir listeden kalkar', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ([{ id: 's1', ad: 'Zeynep', soyad: 'Kaya', email: 'z@k.com' }]) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ok: true }) });
    vi.stubGlobal('fetch', fetchMock);

    render(<ModernTeacherStudentsPage />);
    await screen.findByText('Zeynep');

    await userEvent.click(screen.getByRole('button', { name: /çıkar/i }));

    await waitFor(() => {
      const cagri = fetchMock.mock.calls[1];
      expect(cagri[0]).toContain('/students/s1');
      expect(cagri[1].method).toBe('DELETE');
    });
    expect(screen.queryByText('Zeynep')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: RED doğrula**

Run: `cd frontend && npx vitest run src/pages/__tests__/ModernTeacherStudentsPage.delete.test.tsx`
Expected: FAIL — "Unable to find role button /çıkar/i" (buton yok)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/__tests__/ModernTeacherStudentsPage.delete.test.tsx
git commit -m "test(teacher): roster cikarma testi (RED, #444 B1)"
```

### Task B2: GREEN — buton + DELETE

**Files:**
- Modify: `frontend/src/pages/ModernTeacherStudentsPage.tsx`

- [ ] **Step 1: Handler ekle** (`ogrenciEkle`'nin hemen altına)

```tsx
  const ogrenciCikar = async (ogrenciId: string) => {
    const yanit = await fetch(
      `/api/v1/teacher/classes/${seciliSinif}/students/${ogrenciId}`,
      { method: 'DELETE', credentials: 'include' },
    );
    if (!yanit.ok) {
      setHata('Öğrenci çıkarılamadı');
      return;
    }
    setOgrenciler((onceki) => onceki.filter((o) => o.id !== ogrenciId));
  };
```

- [ ] **Step 2: Satır sonuna buton ekle** (öğrenci `map`'inin içinde)

```tsx
              <button
                type="button"
                onClick={() => void ogrenciCikar(ogrenci.id)}
                style={{ minHeight: 44 }}
              >
                Çıkar
              </button>
```

- [ ] **Step 3: GREEN doğrula**

Run: `cd frontend && npx vitest run src/pages/__tests__/ModernTeacherStudentsPage.delete.test.tsx`
Expected: 1 passed

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ModernTeacherStudentsPage.tsx
git commit -m "feat(teacher): roster cikarma butonu (#444 B2)"
```

---

## Track C — Kaynak hijyeni

### Task C1: Mojibake geri çevir

**Files:**
- Modify: `backend/tests/integration/test_end_to_end_platform.py`

- [ ] **Step 1: Geri çevir ve DOĞRULA (tek script)**

```python
import pathlib
p = pathlib.Path("backend/tests/integration/test_end_to_end_platform.py")
ham = p.read_text(encoding="utf-8")
duzeltilmis = ham.encode("latin-1", errors="strict").decode("utf-8")
assert "İlk agent" in duzeltilmis, "geri cevirme beklenen metni uretmedi"
p.write_text(duzeltilmis, encoding="utf-8")
print("cift-kodlama geri cevrildi")
```

- [ ] **Step 2: Test toplama bozulmadı mı**

Run: `cd backend && python -m pytest tests/integration/test_end_to_end_platform.py -q --collect-only`
Expected: `10 tests collected` (öncekiyle aynı)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_end_to_end_platform.py
git commit -m "fix(tests): cift-kodlanmis Turkce yorumlar geri cevrildi (#458a)"
```

### Task C2: `fix_validators.py` sil

**Files:**
- Delete: `backend/fix_validators.py`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Referanssızlığı TEKRAR doğrula (silmeden önce)**

Run: `cd /c/Users/husey/kiro2 && grep -rl "fix_validators" --include="*.py" --include="*.md" --include="*.yml" . | grep -v "fix_validators.py"`
Expected: yalnız `backend/pyproject.toml` (ignore girdisi). Başka çıktı varsa **SİLME**.

- [ ] **Step 2: Sil + ignore girdisini kaldır**

```bash
git rm backend/fix_validators.py
```

`backend/pyproject.toml` içindeki `"fix_validators.py" = [...]` bloğunu tamamen sil.

- [ ] **Step 3: Kapı hâlâ geçiyor mu**

Run: `cd backend && python -m ruff check . 2>&1 | tail -2`
Expected: yeni hata yok

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: referanssiz fix_validators.py silindi (#458b)"
```

---

## Track D — ES kapı denetimi (ölçüm önce)

### Task D1: ES indeksi kapıya uyuyor mu — ÖLÇ

**Files:**
- Create: `backend/scripts/quality/es_gate_audit.py`

- [ ] **Step 1: Denetim script'ini yaz**

```python
"""ES indeksindeki sorular beta kapisina uyuyor mu (#433).

"ES kapiyi tanimiyor" bir IDDIA. Reindex 190K+ dokuman demek; once kapinin
GERCEKTEN bypass edildigini olc. Yontem: ES'ten orneklem cek, ayni id'leri
mv_safe_for_beta'da ara. Kapida OLMAYAN id sayisi = sizinti.
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ES = "http://localhost:9200"
INDEKS = "questions"


def ornek_id_ler(n: int = 200) -> list[str]:
    govde = json.dumps({"size": n, "_source": False}).encode()
    istek = urllib.request.Request(
        f"{ES}/{INDEKS}/_search", data=govde,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(istek, timeout=20) as yanit:  # noqa: S310
        veri = json.load(yanit)
    return [h["_id"] for h in veri["hits"]["hits"]]


if __name__ == "__main__":
    idler = ornek_id_ler()
    print(f"ES orneklem: {len(idler)} dokuman")
    print("SONRAKI ADIM: bu id'leri mv_safe_for_beta'da ara (psql), kapida")
    print("olmayanlarin orani sizinti oranidir. Oran 0 ise REINDEX GEREKMEZ.")
```

- [ ] **Step 2: Çalıştır**

Run: `cd backend && python scripts/quality/es_gate_audit.py`
Expected: örneklem sayısı. `questions` indeksi yoksa hata → indeks adını `curl -s localhost:9200/_cat/indices` ile bul ve script'teki `INDEKS`'i düzelt.

- [ ] **Step 3: Sızıntı oranını ölç**

Run:
```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -t \
  -c "SELECT count(*) FROM mv_safe_for_beta;"
```
Expected: kapıdaki soru sayısı. ES doküman sayısı bundan **büyükse** sızıntı vardır ve reindex gerekir; **eşit/küçükse** #433 fantomdur ve kapatılır.

- [ ] **Step 4: Commit (ölçüm aracı + verdict)**

```bash
git add backend/scripts/quality/es_gate_audit.py
git commit -m "chore(es): kapi denetim araci — reindex karari olcume baglandi (#433 D1)"
```

---

## Self-Review

**1. Spec coverage.** Doğrulanmış 5 gerçek iş → A (#447), B (#444 silme), C1 (#458a), C2 (#458b), D (#433). Operatör-bağımlı 5 görev bilinçli olarak dışarıda ve gerekçesi yazılı. Boşluk yok.

**2. Placeholder taraması.** "TBD/TODO/uygun hata yönetimi ekle" yok; her kod adımı gerçek kod içeriyor. A3 Step 4'teki loader satırı birebir yazılı. D1'de "sonraki adım" metni bir placeholder değil, script'in **çıktısı** — karar verisi üretir.

**3. Tip tutarlılığı.** `PersonaResponse` alan adları A2'deki `PERSONA_ANAHTARLARI` kümesiyle birebir aynı (15). Servis `persona_getir(oturum, kullanici_id)` imzası router'daki çağrıyla uyumlu. B1 testindeki `/students/s1` yolu, canlı ölçülen `DELETE /api/v1/teacher/classes/{class_id}/students/{student_user_id}` ile uyumlu.

**A1 ÇALIŞTIRILDI (30 Tem 2026) — sonuç plana geri beslendi:**

- **Şema 14/14 mevcut** → A3'ün SQL varsayımları geçerli, kolon-adı riski KAPANDI.
- **Veri doluluğu zayıf:** 77 kullanıcı · `total_xp>0` **8** · `level>1` **2** ·
  `streaks` satırı **4** · `student_profiles` 74 · `target_university` dolu **0** ·
  `study_hours_per_day` dolu **0**.
- **Sonuç:** uç dürüst olacak ama 15 alanın ~7'si neredeyse her kullanıcı için
  `null`/varsayılan dönecek (hedefUni ve gunlukHedefDk **her zaman** null;
  seri/seriRekor %95 null; xp 0, seviye 1).
- **Plan değişikliği:** Task A4'ün kapsamı 3 alandan ~7 alana çıkar. Frontend'de
  `?? '—'` guard'ı gereken alanlar: hedefSiralama, yksTarihi, bugunCozulenDk,
  **hedefUni, hedefBolum, gunlukHedefDk, seri, seriRekor**.
- **Değişmeyen karar:** boş veriyi uydurmakla doldurmuyoruz (#444 dersi). 404 ile
  19 ekranın kırılması, dürüst boş alanlardan kötüdür.
