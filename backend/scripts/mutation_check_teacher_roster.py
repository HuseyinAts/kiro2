"""Mutasyon testi — roster testleri gerçekten hassas mı?

`test_teacher_roster.py` beş güvenlik değişmezi iddia ediyor: rol kapısı,
sınıf sahipliği (IDOR), hedefin öğrenci olması, çift eklememe, gerçek kimlik.
Bu script her birini TEK TEK bozar ve doğru testin kırmızıya döndüğünü
doğrular; sonra dosyayı harfi harfine geri yükler.

Kullanım:
    cd backend && python scripts/mutation_check_teacher_roster.py

Çıkış 0 = her mutasyon yakalandı. 1 = en az biri fark edilmedi, yani o
değişmez test EDİLMİYOR demektir.
"""

from __future__ import annotations

import os
import subprocess  # nosec - yalnız sabit pytest komutu koşturur, dış girdi yok
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

HEDEF = Path(__file__).resolve().parent.parent / "app" / "api" / "teacher_classroom.py"
TEST = "tests/integration/test_teacher_roster.py"

# "çift ekleme" mutasyonu: erken dönüşü kaldır -> her istekte yeni satır yazılır.
_DEDUP_ESKI = "    if mevcut is not None:"
_DEDUP_YENI = "    if False:"


MUTASYONLAR = [
    (
        "rol kapısı yok (öğrenci de ekleyebilir)",
        [("    _staff: None = _STAFF_ONLY,\n", "")],
        "test_student_role_cannot_add_anyone_to_a_class",
    ),
    (
        "sınıf sahipliği kontrol edilmiyor (IDOR)",
        # DESEN, dosyadaki HÂLİYLE olmalı. İlk turda ruff-format satırı tek
        # satıra topladığı için desen tutmadı ve mutasyon ATLANDI — yani en
        # kritik değişmez (IDOR) sessizce doğrulanmamış kaldı. Atlanan bir
        # mutasyon "yakalandı" değildir; script bunu 'kaçtı' sayıyor.
        [
            (
                "if classroom is None or str(classroom.teacher_user_id) != "
                "str(teacher_user_id):",
                "if classroom is None:",
            )
        ],
        "test_teacher_cannot_add_to_someone_elses_class",
    ),
    (
        "hedefin öğrenci olması aranmıyor",
        [
            (
                'if str(rol).lower() not in {"student", "ogrenci", "öğrenci"}:',
                "if False:",
            )
        ],
        "test_only_students_can_be_added",
    ),
    (
        "çift ekleme engellenmiyor",
        [(_DEDUP_ESKI, _DEDUP_YENI)],
        "test_adding_the_same_student_twice_does_not_duplicate",
    ),
    (
        "kimlik alanları yine boş dönüyor",
        [
            (
                "**profiller.get(\n                str(r.student_user_id), "
                '{"ad": "", "soyad": "", "email": ""}\n            ),',
                '"ad": "",\n            "soyad": "",\n            "email": "",',
            )
        ],
        "test_list_students_returns_real_identity",
    ),
]

# "çift ekleme" mutasyonu: erken dönüşü kaldır -> her istekte yeni satır yazılır.
_DEDUP_ESKI = "    if mevcut is not None:"
_DEDUP_YENI = "    if False:"


def testleri_kos() -> tuple[int, str]:
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
        env={**os.environ},
        check=False,
    )
    return sonuc.returncode, (sonuc.stdout or "") + (sonuc.stderr or "")


def main() -> int:
    orijinal = HEDEF.read_text(encoding="utf-8")

    kod, cikti = testleri_kos()
    if kod != 0:
        print("Temel paket zaten kırmızı — mutasyon testi anlamsız.")
        print(cikti[-1200:])
        return 1
    print("temel: YEŞİL\n")

    kacan: list[str] = []
    try:
        for ad, yamalar, beklenen in MUTASYONLAR:
            eksik = [a for a, _ in yamalar if a not in orijinal]
            if eksik:
                print(f"[ATLA  ] {ad}: desen bulunamadı")
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
            elif beklenen in cikti:
                print(f"[YAKALA] {ad}  -> {beklenen}")
            else:
                print(f"[YAKALA] {ad}  -> başka test yakaladı (beklenen: {beklenen})")
    finally:
        HEDEF.write_text(orijinal, encoding="utf-8")

    kod, _ = testleri_kos()
    print(f"\ngeri yükleme sonrası paket: {'YEŞİL' if kod == 0 else 'KIRMIZI'}")
    if kod != 0:
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
