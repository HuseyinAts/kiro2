"""Tur 2 doğrulama sonuçlarını kütüğe yaz (wf_285d1d38-c12).

Elle Edit yerine script: 4 kayıt aynı `kanit: null / commit: null /
zorlayici_test: null` kuyruğunu paylaşıyor, benzersiz ankraj gerekiyor.
Ankraj olarak her kaydın `curutme_sorusu`/`degerlendirme` satırı kullanılıyor.

Idempotent: ankraj bulunamazsa (zaten yamalanmışsa) o kayıt atlanır ve
GECERSIZ sayılır — sessiz no-op yok.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KUTUK = Path(__file__).resolve().parents[1] / "docs/audits/2026-08-12_25uzman/iddialar.yaml"

# (id, ankraj_satiri, yeni_alanlar_bloğu)
YAMALAR: list[tuple[str, str, str]] = [
    (
        "U25",
        '    - "grep -L \'def downgrade\' backend/alembic/versions/*.py | wc -l   # downgrade\'i OLMAYAN migration sayısı"',
        """    severity_olculen: P1
    durum: dogrulandi
    kanit: |
      TUR 2 (wf_285d1d38-c12), iki çürütücü MUTABIK.
      115 migration, 0'ında downgrade() eksik -> AMA bu VAR-YOK kontrolü,
      İŞLEVSELLİK değil.

      Dedektörün kaçırdığı somut vaka:
        alembic/versions/fa067642bdfe_force_drop_questions.py
          def upgrade():   op.execute("DROP TABLE IF EXISTS questions CASCADE")
          def downgrade(): pass          <- GERÇEKTEN geri alınamaz
        tests/db/test_migrations.py:96-112 yalnız ast.walk ile "downgrade adlı
        fonksiyon var mı" bakıyor; gövdeyi denetlemiyor -> testi GEÇİRİYOR.
        Canlı: pytest tests/db/test_migrations.py -> 9 passed (bu test dahil).

      Gerçek round-trip testleri VAR ama KOŞULSUZ atlanıyor:
        tests/test_migrations.py:37-40
          pytestmark = pytest.mark.skipif(True, reason="Migration tests require
                                          real PostgreSQL, 1F + 10E")
        Canlı: pytest tests/test_migrations.py -> 16 skipped
        (test_full_upgrade_downgrade_cycle, test_stepwise_upgrade_downgrade,
         test_partial_downgrade, test_downgrade_preserves_base_schema DAHİL)
        skipif(True) DB varlığına bakmıyor — koşulsuz.

      CI'da downgrade adımı YOK: ci.yml:269 yalnız "alembic upgrade head".
      scripts/ci/test_migrations.py (DryRunTester ile GERÇEK upgrade+downgrade
      yapan script) HİÇBİR workflow'dan çağrılmıyor -> yazılmış ama bağlı değil.

      BAĞIMSIZ TEYİT: docs/HANDOFF_2026-08-07_gemini.md:352-366 "İş #9 — Alembic
      round-trip testi gerçek değil", AYNI bulgu, AYNI örnek (fa067642bdfe), P1.
      git log --since=2026-08-07 -- <bu dosyalar> -> BOŞ. 5 gündür açık.
    fix_degeri: |
      ÖLÇÜLEBİLİR ve mutasyonla çivilenebilir: gerçek round-trip test
      (upgrade head -> downgrade -1 -> upgrade head, tek-kullanımlık DB)
      eklenirse fa067642bdfe gibi boş-pass downgrade'i olan HER migration
      derhal FAIL verir. Mutasyon: sahte boş-downgrade migration ekle ->
      yeni test düşmeli, mevcut AST testi DÜŞMEMELİ (ikisinin farkı budur).
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U18",
        '    on_bulgu: "MEMORY (7 Ağu): \'111 frontend testi kırık\' — flakiness değil, DÜZ KIRIK olabilir. Önce onu ölç."',
        """    severity_olculen: P3
    durum: abartili
    kanit: |
      TUR 2 (wf_285d1d38-c12). İki çürütücü ANLAŞAMADI (P3 vs P2)
      -> 3. HAKEM (opus) karar verdi: abartili / P3.
      anlasmazlik_tipi: severity  (varlıkta değil, önemde ayrılık)

      İDDİANIN ÇEKİRDEĞİ DOĞRU (fantom değil):
        playwright.config.ts:16-18  fullyParallel: true, retries: CI ? 2 : 0
        grep "repeatEach|repeat-each|quarantine|flaky" frontend -> 0 sonuç
        -> flakiness mekanizması gerçekten YOK.

      AMA HAKEMİN BAĞIMSIZ ÖLÇÜMÜ (iki çürütücünün de yapmadığı deney):
        vitest ile koşunca hata veriyor (yanlış runner):
          "Playwright Test did not expect test.describe() to be called here"
        DOĞRU runner ile:
          npx playwright test ... --project=chromium
            actualWorkers 8, retries 0 -> 44/44 PASS (20,9 sn)
          --repeat-each=3
            -> 132/132 PASS, flaky 0 (66,1 sn)
        8 worker altında 3 tekrarda SIFIR varyans. Yani "paralel flakiness"
        şu an ölçülebilir bir problem ÜRETMİYOR.

      SEVERITY'Yİ P3'E ÇİVİLEYEN BAĞLAM:
        git log --all -- <ankraj dosya> -> BOŞ  (dosya hiç commit edilmemiş)
        git status --short -> ?? untracked (11 Ağu 21:44)
        ci.yml:7-13 on: push/PR [main, master, develop]
        git rev-list --count master..HEAD -> 391
        -> Dosya hiçbir merge'ü etkilemiyor VE CI bu dalı zaten dinlemiyor.

      YAN BULGU (assertion yüzeyi zayıf, ayrı kalem değil ama kayda geçti):
        spec:70-92 yalnız body görünür + "Fatal Application Crash" yok
        -> boş sayfa / error boundary / SPA 404 fallback bu testten YEŞİL geçer.
    fix_degeri: |
      YAKIN SIFIR, ölçülebilir. Fix'in tetiklenebileceği hiçbir gerçek akış yok:
      (a) ankraj dosya commit'siz, (b) commit edilse bile ci.yml aktif dalı
      dinlemiyor (391 commit fark), (c) CI zaten retries=2 ile temel flake
      azaltması yapıyor. Gerçek kazanç ancak dosya commit edilir VE dal CI'ya
      bağlanırsa doğar. Ondan önce "8-worker flakiness check" eklemek, hiç
      çalışmayan bir borunun contasını değiştirmektir.

      ÖNCE YAPILACAK (bu iddiadan bağımsız, daha yüksek kaldıraç):
      dosyayı commit et + ci.yml'i aktif dala bağla. FAZ 3'ün mekanik hakemi
      bunlar olmadan zaten yok.
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U01",
        '    curutme_sorusu: "Kalibrasyon zaten cache\'i temizliyor olabilir mi? irt_daemon içinde cache.clear()/pop çağrısı var mı?"',
        """    severity_olculen: yok
    durum: fantom
    kanit: |
      TUR 2 (wf_285d1d38-c12), iki çürütücü MUTABIK. İDDİA ÇÜRÜTÜLDÜ.

      1) Ankraj satırı YANLIŞ: osym_exam_engine.py:25 TTLCache DEĞİL,
         `from core.structured_logger import get_logger`.
         Gerçek TTLCache satırları: 147 (_question_pool_cache, ttl=3600)
         ve 149 (_performance_cache).

      2) 🔴 BELİRLEYİCİ: cache SORU SATIRI tutmuyor, yalnız ÇIPLAK ID LİSTESİ:
           1429-1442: cache_key="BETA:verified_provisional:all"
                      pool = [row[0] for row in id_result.all()]
         IRT parametreleri (irt_discrimination/difficulty/guessing) taşıyan
         Question satırı HER çağrıda TAZE SELECT ile geliyor:
           select(Question).where(Question.id.in_(sampled_ids),
                                  Question.is_active == True)   (1621-1624)
         -> Kalibre edilen parametre bayat servis EDİLMİYOR.
         Cache'in bayatlattığı tek şey: havuza YENİ eklenen/çıkarılan soru
         kimlikleri (1 saate kadar) — iddianın anlattığı kusur bu değil.

      3) Ankrajın diğer yarısı DOĞRU: question_bank.py:234-237
         irt_discrimination / irt_difficulty / irt_guessing(0.25) /
         irt_upper_asymptote(1.0) alanları var.

      4) curutme_sorusu'nun hipotezi de YANLIŞ çıktı: irt_daemon içinde
         invalidate/publish/subscribe YOK — yani kalibrasyon cache'i
         temizlemiyor. Ama (2) yüzünden temizlemesine GEREK de yok.
    fix_degeri: |
      SIFIR (iddia edilen kusur için). Redis Pub/Sub invalidation eklemek,
      olmayan bir bayatlığı çözer. Kalan gerçek etki — havuz üyeliğinin
      1 saate kadar bayat kalması — ayrı ve çok daha küçük bir konu;
      ölçülmeden aksiyon alınmamalı (yeni soru eklenme sıklığı nedir?).
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U03",
        '    curutme_sorusu: "NULL sayısı 0 ise iddia FANTOM. 0 değilse: o satırlar aktif mi, yoksa ölü/kullanılmayan mı?"',
        """    severity_olculen: yok
    durum: fantom
    kanit: |
      TUR 2 (wf_285d1d38-c12), iki çürütücü MUTABIK. Kütüğün KENDİ kriteri
      ("NULL sayısı 0 ise iddia FANTOM") tam olarak karşılandı.

      psql -p 5434 -d kiro2 -U postgres:
        SELECT subject_area, count(*) FROM topic_hierarchy GROUP BY 1  -> (0 satır)
        SELECT count(*) FROM topic_hierarchy WHERE subject_area IS NULL -> 0
        SELECT count(*) FROM topic_hierarchy                            -> 0
      KONTROL KOLU: users -> 3, refresh_tokens -> 10 (sıfır DEĞİL)
        -> sorgu mekanizması dolu/boş ayırt edebiliyor, alet arızası değil.

      ZATEN KAPALI (kısmi): commit c96a2d3c0 (9 Nis 2026)
        backend/scripts/seed_dungeon_topics.py docstring:
        "1. Fix subject_area=NULL on MAT.xxx topics (-> MATEMATIK)"
        idempotent UPDATE ... WHERE subject_area IS NULL. Kapsam yalnız MAT.*

      BAŞKA KATMAN: soru sunumunda kullanılan alan question_metadata.subject_area
        (question_bank.py:195) DB'de is_nullable='NO' — NOT NULL kısıtlı.
        TopicHierarchy.subject_area (satır 62, nullable) DAG/prereq amaçlı,
        ayrı katman.

      SEMANTİK: iddia iki farklı şeyi birleştiriyor. "Tarih/Felsefe Sosyal
        altında birleşme" bir NULL-veri hatası değil, KASITLI tasarım:
        agents/coordination/question_classifier.py:416-421 tarih/coğrafya/
        felsefe/din kültürü -> DomainType.SOSYAL (agent yönlendirme granülerliği).

      ⚠️ ÖLÇÜM BAĞLAMI: topic_hierarchy 0 satır çünkü canlı DB'nin İÇERİK
      tablolarının tamamı boş — bkz. X09. Bu, iddianın fantomluğunu
      değiştirmez (kriter NULL sayısıydı) ama tekrar-ölçüm gerektirir:
      tablo yeniden doldurulursa MAT.* dışındaki 13 alt dal için boşluk
      tekrar açılabilir.
    fix_degeri: |
      Şu anki veriyle SIFIR: önerilen migrasyon 0 satır günceller.
      X09 çözülüp tablo dolduktan SONRA yeniden ölçülmeli — o zamana kadar
      P1 aksiyon gerekçesi yok.
    commit: null
    zorlayici_test: null""",
    ),
]


ESKI_KUYRUK = "\n    kanit: null\n    commit: null\n    zorlayici_test: null"


def blok_sinirlari(metin: str, iddia_id: str) -> tuple[int, int] | None:
    """Bir kaydin [bas, son) araligini dondur — `- id: X` .. sonraki `- id:`."""
    bas_isaret = f"\n  - id: {iddia_id}\n"
    if bas_isaret not in metin:
        return None
    bas = metin.index(bas_isaret) + 1
    sonraki = metin.find("\n  - id: ", bas)
    return (bas, sonraki if sonraki != -1 else len(metin))


def main() -> int:
    metin = KUTUK.read_text(encoding="utf-8")
    basarili: list[str] = []
    basarisiz: list[str] = []

    for iddia_id, ankraj, yeni in YAMALAR:
        sinir = blok_sinirlari(metin, iddia_id)
        if sinir is None:
            basarisiz.append(f"{iddia_id}: kayit bulunamadi")
            continue
        bas, son = sinir
        blok = metin[bas:son]

        # Idempotentlik: zaten yamalanmissa dokunma ama BASARISIZ say (sessiz no-op yok)
        if "durum: beklemede" not in blok:
            basarisiz.append(f"{iddia_id}: durum zaten 'beklemede' degil — atlandi")
            continue
        if ankraj not in blok:
            basarisiz.append(f"{iddia_id}: ANKRAJ blok icinde yok")
            continue
        if ESKI_KUYRUK not in blok:
            basarisiz.append(f"{iddia_id}: kanit/commit kuyrugu blok icinde yok")
            continue

        # 1) kuyrugu yeni alanlarla degistir
        a_idx = blok.index(ankraj)
        a_son = blok.index("\n", a_idx)
        k_idx = blok.index(ESKI_KUYRUK, a_idx)
        blok = blok[: a_son + 1] + yeni + blok[k_idx + len(ESKI_KUYRUK) :]

        # 2) ESKI severity_olculen/durum satirlarini SIL (yenisi yukarida geldi)
        #    -> cift YAML anahtari olusmasin
        blok = blok.replace("    severity_olculen: null\n    durum: beklemede\n", "", 1)

        metin = metin[:bas] + blok + metin[son:]
        basarili.append(iddia_id)

    KUTUK.write_text(metin, encoding="utf-8")
    for x in basarili:
        print(f"[YAMALANDI] {x}")
    for x in basarisiz:
        print(f"[BASARISIZ] {x}")
    return 0 if not basarisiz else 1


if __name__ == "__main__":
    raise SystemExit(main())
