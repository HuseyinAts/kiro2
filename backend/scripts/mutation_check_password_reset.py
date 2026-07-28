"""Mutasyon testi — `test_password_reset_codes.py` gerçekten hassas mı?

Yeşil bir test, ölçtüğünü sandığı şeyi ölçmüyor olabilir (bu depoda 28 Tem'de
üç kez yaşandı). Bu script `core/password_reset_codes.py`'yi geçici olarak
BOZAR, testleri koşar ve doğru testlerin KIRMIZIYA döndüğünü doğrular; sonra
dosyayı harfi harfine geri yükler.

Kullanım:
    cd backend && python scripts/mutation_check_password_reset.py

Çıkış kodu 0 = her mutasyon yakalandı. 1 = en az bir mutasyon fark edilmedi,
yani o güvenlik değişmezi test edilmiyor demektir.
"""

from __future__ import annotations

import subprocess  # nosec - yalnız sabit pytest komutu koşturur, dış girdi yok
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

HEDEF = Path(__file__).resolve().parent.parent / "core" / "password_reset_codes.py"
TEST = "tests/unit/test_password_reset_codes.py"

_SLOT_ORIJINAL = (
    'return hmac.new(\n        _pepper(), f"slot:{_normalize_email(email)}".encode(), '
    "sha256\n    ).hexdigest()[:40]"
)
_SLOT_SABIT = 'return "GLOBAL_SLOT_MUTASYON"'
_DIGEST_ORIJINAL = 'f"code:{_normalize_email(email)}:{code}".encode()'
_DIGEST_EPOSTASIZ = 'f"code:{code}".encode()'

# (ad, [(aranan, yerine), ...], bu mutasyonu yakalaması BEKLENEN test)
MUTASYONLAR = [
    (
        "anahtar e-postadan bağımsız (paylaşımlı ad alanı)",
        [(_SLOT_ORIJINAL, _SLOT_SABIT)],
        "test_issue_limit_is_per_account_not_global",
    ),
    (
        "kod HMAC'i e-postadan bağımsız",
        [(_DIGEST_ORIJINAL, _DIGEST_EPOSTASIZ)],
        "test_code_digest_is_bound_to_email",
    ),
    (
        "İKİSİ BİRDEN: ne anahtar ne özet e-postaya bağlı (gerçek zafiyet)",
        [(_SLOT_ORIJINAL, _SLOT_SABIT), (_DIGEST_ORIJINAL, _DIGEST_EPOSTASIZ)],
        "test_code_is_bound_to_its_email",
    ),
    (
        "deneme kilidi yok",
        [("if attempts >= self.MAX_ATTEMPTS:", "if attempts >= 10**9:")],
        "test_correct_code_rejected_after_max_wrong_attempts",
    ),
    (
        "hesap başına kod limiti yok",
        [("if issued > self.MAX_ISSUES_PER_WINDOW:", "if issued > 10**9:")],
        "test_issue_is_limited_per_account",
    ),
    (
        "kod tek kullanımlık değil",
        [
            (
                "await self._delete(code_key, attempts_key)\n        return user_id or None",
                "return user_id or None",
            )
        ],
        "test_code_is_single_use",
    ),
]


def testleri_kos() -> tuple[int, str]:
    # Sabit komut listesi, kullanıcı girdisi yok.
    sonuc = subprocess.run(  # nosec  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            TEST,
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**__import__("os").environ, "TEST_REDIS_URL": "redis://localhost:6379/15"},
        check=False,
    )
    return sonuc.returncode, (sonuc.stdout or "") + (sonuc.stderr or "")


def main() -> int:
    orijinal = HEDEF.read_text(encoding="utf-8")

    kod, cikti = testleri_kos()
    if kod != 0:
        print("Temel paket zaten kırmızı — mutasyon testi anlamsız.")
        print(cikti[-1500:])
        return 1
    print("temel: YEŞİL\n")

    kacan: list[str] = []
    try:
        for ad, yamalar, beklenen_test in MUTASYONLAR:
            eksik = [aranan for aranan, _ in yamalar if aranan not in orijinal]
            if eksik:
                print(f"[ATLA  ] {ad}: mutasyon deseni dosyada bulunamadı")
                kacan.append(f"{ad} (desen yok)")
                continue

            bozuk = orijinal
            for aranan, yerine in yamalar:
                bozuk = bozuk.replace(aranan, yerine, 1)
            HEDEF.write_text(bozuk, encoding="utf-8")
            kod, cikti = testleri_kos()

            if kod == 0:
                print(f"[KAÇTI ] {ad}: paket hâlâ yeşil — bu değişmez test EDİLMİYOR")
                kacan.append(ad)
            elif beklenen_test in cikti:
                print(f"[YAKALA] {ad}  -> {beklenen_test}")
            else:
                print(
                    f"[YAKALA] {ad}  -> beklenen test adı çıktıda yok "
                    f"({beklenen_test}); başka test yakaladı"
                )
    finally:
        HEDEF.write_text(orijinal, encoding="utf-8")

    kod, _ = testleri_kos()
    print(f"\ngeri yükleme sonrası paket: {'YEŞİL' if kod == 0 else 'KIRMIZI'}")
    if kod != 0:
        print("UYARI: dosya geri yüklendi ama paket kırmızı — elle kontrol et.")
        return 1

    if kacan:
        print(f"\n{len(kacan)} mutasyon fark edilmedi:")
        for ad in kacan:
            print(f"  - {ad}")
        return 1

    print(f"\n{len(MUTASYONLAR)}/{len(MUTASYONLAR)} mutasyon yakalandı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
