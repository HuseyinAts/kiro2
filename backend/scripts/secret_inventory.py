"""Git geçmişindeki sızmış anahtarların envanteri — nerede, ne zaman, hâlâ canlı mı.

NEDEN: depo GitHub'da PUBLIC (28 Tem, auth'suz API 200). Geçmişteki anahtarlar
teorik risk değil. Ama "12 anahtar var" bir SAYIDIR, aksiyon planı değil.
Rotasyonu yapacak kişinin ihtiyacı olan şey:
    - hangi anahtar, hangi commit'te, hangi dosyada girdi (iptal ederken hangi
      projeye ait olduğunu bulmak için)
    - hangileri HÂLÂ ÇALIŞIYOR (canlı olan acil; zaten iptal edilmiş olan değil)

`--check-live` OLMADAN hiçbir ağ isteği yapılmaz; yalnız yerel geçmiş taranır.
`--check-live` ile her anahtar sağlayıcısının en ucuz doğrulama ucuna sorulur;
bu, kullanıcının KENDİ anahtarlarının durumunu öğrenmek içindir.

Anahtarlar HİÇBİR ZAMAN tam olarak basılmaz — çıktı terminal geçmişine düşer.
Tam değere ihtiyaç duyulursa `--reveal` gerekir ve bilinçli bir tercihtir.

Kullanım:
    python scripts/secret_inventory.py                 # yalnız envanter
    python scripts/secret_inventory.py --check-live    # + canlılık ölçümü
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — sabit `git` argv, shell yok
import sys
from collections import OrderedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATTERNS = {
    "google": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "huggingface": re.compile(r"\bhf_[A-Za-z0-9]{30,}"),
    "anthropic": re.compile(r"sk-ant-api[0-9]{2}-[A-Za-z0-9_\-]{20,}"),
    "openai": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}"),
}


def _git(*args: str) -> str:
    # Bastırma sırası için bkz. hooks/push_secret_guard.py açıklaması.
    return subprocess.run(  # nosec  # noqa: S603
        ["git", *args],  # noqa: S607
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout


def mask(k: str) -> str:
    return f"{k[:8]}…{k[-4:]}"


def envanter() -> OrderedDict[str, dict]:
    """Tüm geçmişte sızmış anahtarlar: {anahtar: {tip, commitler, dosyalar}}."""
    bulunan: OrderedDict[str, dict] = OrderedDict()

    # `--all` tüm dalları, `-p` her commit'in yamasını verir.
    # Ayırt edici işaretleyici ZORUNLU: yalnız "|" ve 40-hex aramak yetmez,
    # diff satırlarının kendisi de o kalıba uyabiliyor (ilk denemede
    # ValueError ile patladı).
    ISARET = "###KIROCOMMIT###"
    patch = _git("log", "--all", "-p", "-U0", "--no-color", f"--format={ISARET}%H|%ad")
    tarih = ""
    commit = ""
    dosya = ""

    for satir in patch.splitlines():
        if satir.startswith(ISARET):
            commit, _, tarih = satir[len(ISARET) :].partition("|")
            continue
        if satir.startswith("+++ b/"):
            dosya = satir[6:]
            continue
        if not satir.startswith("+") or satir.startswith("+++"):
            continue
        for tip, desen in PATTERNS.items():
            for m in desen.finditer(satir):
                k = m.group(0)
                kayit = bulunan.setdefault(
                    k, {"tip": tip, "commitler": set(), "dosyalar": set(), "ilk": tarih}
                )
                kayit["commitler"].add(commit[:9])
                kayit["dosyalar"].add(dosya)
    return bulunan


def canli_mi(tip: str, anahtar: str) -> str:
    """Sağlayıcıya sor: anahtar hâlâ geçerli mi?"""
    import httpx

    try:
        if tip == "google":
            r = httpx.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": anahtar},
                timeout=20,
            )
            return "CANLI" if r.status_code == 200 else f"gecersiz ({r.status_code})"
        if tip == "huggingface":
            r = httpx.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {anahtar}"},
                timeout=20,
            )
            return "CANLI" if r.status_code == 200 else f"gecersiz ({r.status_code})"
        if tip == "openai":
            r = httpx.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {anahtar}"},
                timeout=20,
            )
            return "CANLI" if r.status_code == 200 else f"gecersiz ({r.status_code})"
        if tip == "anthropic":
            # Listeleme ucu — token harcamaz, mesaj üretmez.
            r = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": anahtar, "anthropic-version": "2023-06-01"},
                timeout=20,
            )
            return "CANLI" if r.status_code == 200 else f"gecersiz ({r.status_code})"
    except Exception as exc:
        return f"kontrol edilemedi ({type(exc).__name__})"
    return "kontrol yok (bu tip icin uc tanimli degil)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-live", action="store_true", help="sağlayıcıya sor")
    ap.add_argument("--reveal", action="store_true", help="anahtarları tam bas")
    args = ap.parse_args()

    print("Git geçmişi taranıyor (tüm dallar)...\n")
    bulunan = envanter()

    if not bulunan:
        print("Geçmişte sağlayıcı-formatlı anahtar bulunamadı.")
        return 0

    tipler: dict[str, int] = {}
    for kayit in bulunan.values():
        tipler[kayit["tip"]] = tipler.get(kayit["tip"], 0) + 1

    print(f"{len(bulunan)} benzersiz anahtar: {tipler}\n")
    print("=" * 70)

    canli_sayisi = 0
    for i, (anahtar, kayit) in enumerate(bulunan.items(), 1):
        gosterim = anahtar if args.reveal else mask(anahtar)
        print(f"\n[{i}] {kayit['tip'].upper()}  {gosterim}")
        print(f"    ilk görülme : {kayit['ilk']}")
        print(f"    commit      : {', '.join(sorted(kayit['commitler'])[:4])}")
        print(f"    dosya       : {', '.join(sorted(kayit['dosyalar'])[:3])}")
        if args.check_live:
            durum = canli_mi(kayit["tip"], anahtar)
            print(f"    DURUM       : {durum}")
            if durum == "CANLI":
                canli_sayisi += 1

    if args.check_live:
        print("\n" + "=" * 70)
        print(f"HÂLÂ CANLI: {canli_sayisi} / {len(bulunan)}")
        if canli_sayisi:
            print(
                "\nDepo PUBLIC. Canlı her anahtar şu an kullanılabilir durumda.\n"
                "Google  -> console.cloud.google.com/apis/credentials (Sil/Kısıtla)\n"
                "HF      -> huggingface.co/settings/tokens (Revoke)\n"
                "Rotasyon geçmiş temizliğinin YERİNE geçmez ama ondan ÖNCE gelir:\n"
                "kopyalar zaten dışarıda olabilir."
            )
    else:
        print("\n(canlılık ölçümü için: --check-live)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
