"""Push bekçisi: uzağa gidecek TÜM commit'lerde sağlayıcı-formatlı sır ara.

NEDEN COMMIT BEKÇİSİ YETMİYOR
-----------------------------
`kiro2-secret-detector` commit anında YALNIZ o commit'in staged dosyalarına
bakar. Bu iyi bir ilk savunma ama tek başına yetersizdi ve bu depo bunu pahalı
öğrendi:

  - 27 Tem 2026: sır tarayıcısının kendisi aylardır hiç koşmuyordu
    (`core.hooksPath = nul` + yanlış config + `types: [python]`). O sessiz
    pencerede 12 gerçek kimlik bilgisi geçmişe girdi.
  - 28 Tem 2026 ölçümü: depo GitHub'da PUBLIC — `api.github.com/repos/...`
    kimlik doğrulaması olmadan 200 dönüyor. Yani o 12 anahtar teorik risk
    değil, herkese açık.

Ders: içeriğin geri alınamaz biçimde kamuya çıktığı an **push**'tur, commit
değil. Son savunma hattı orada olmalı ve **push edilen aralığın tamamına**
bakmalı — commit bekçisi bir gün yine sessizce ölürse bu yakalasın.

NEDEN BURADA TAM TEST PAKETİ KOŞMUYORUZ
---------------------------------------
Kök config'in eski pre-push kapısı `pytest -x backend/tests/` idi: 16.743 test
ve `-x` ile bilinen tek bir pre-existing fail her push'u bloke ederdi. Böyle
bir kapı yürütülebilir değildir; ilk sıkıştığında `--no-verify` alışkanlığa
dönüşür ve bekçi fiilen kapanır — bu depoda tam olarak bu olmuştu. Bu yüzden
pre-push kapısı DAR ve HIZLI tutuldu; tam paket CI'ın işi.

DAVRANIŞ
--------
git, pre-push hook'una stdin'den satır satır şunu verir:
    <local_ref> <local_sha> <remote_ref> <remote_sha>

`remote_sha` sıfırsa dal uzakta yeni demektir; o durumda diğer uzak dalların
kapsamadığı commit'ler taranır (aksi halde tüm depo geçmişi taranırdı).

Yalnız SAĞLAYICI-FORMATLI desenler bloklar. Jenerik `password = "..."`
sezgiseli burada YOK: bu depoda 110 bulgunun 99'u test fixture'ı/yerel DSN idi
ve bloklamak bekçiyi yeniden kapattırmanın en kısa yoluydu.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 — yalnız sabit `git` argv, shell yok
import sys

ZERO = "0" * 40

# Sağlayıcı formatları — hepsi kendine özgü, yanlış pozitifi düşük.
PATTERNS: dict[str, re.Pattern[str]] = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "HuggingFace token": re.compile(r"\bhf_[A-Za-z0-9]{30,}"),
    "Anthropic key": re.compile(r"sk-ant-api[0-9]{2}-[A-Za-z0-9_\-]{20,}"),
    "OpenAI project key": re.compile(r"\bsk-proj-[A-Za-z0-9_\-]{20,}"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key blob": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def _run(*args: str) -> str:
    # Çağrı güvenli — argv sabit, shell=False, kullanıcı girdisi girmiyor.
    #
    # AŞAĞIDAKİ SATIR SONU BASTIRMALARININ SIRASINI DEĞİŞTİRME.
    # İki ayrı araç aynı satırdan iki ayrı direktif sözdizimi okuyor ve
    # 28 Tem'de ölçüldü: bandit'in bastırması ÖNCE gelmeli ve test kimliği
    # ALMAMALI; ters sırada (ve kimlikli) yazıldığında bandit B603'ü
    # bastırmıyor, bu satır kırmızı kalıyor.
    #
    # Bu yorum, o direktiflerin metnini BİLEREK tekrarlamıyor: ruff düz
    # yorumda gördüğü bastırma metnini gerçek direktif sanıp "kullanılmayan"
    # diye siliyor ve cümleyi ortadan kesiyor (aynı tuzak bugün 4. kez).
    return subprocess.run(  # nosec  # noqa: S603
        ["git", *args],  # noqa: S607
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout


def _mask(bulgu: str) -> str:
    """Bulguyu ASLA olduğu gibi basma — çıktı CI logu ve terminal geçmişidir."""
    return f"{bulgu[:6]}…{bulgu[-2:]} (len={len(bulgu)})"


def _added_lines(local_sha: str, remote_sha: str) -> list[str]:
    """Aralıktaki HER COMMIT'in eklediği satırlar.

    NET DIFF KULLANMAK YETMEZ — bu bekçinin en kritik ayrıntısı.
    `git diff remote..local` yalnız NET sonucu gösterir: bir commit'te eklenip
    sonrakinde silinen sır net diff'te GÖRÜNMEZ. Ama o sır push edilen
    geçmişte kalıcıdır ve public bir depoda herkes `git log -p` ile okur.
    28 Tem'de bu betiğin ilk sürümü net diff kullanıyordu; "sır ekle + sil"
    senaryosu 0 satır taratıp yeşil döndü. Bu depodaki 12 anahtarın bir kısmı
    büyük ihtimalle tam olarak böyle girdi.

    `git log -p` her commit'in kendi yamasını verir; silinmiş olsa bile
    eklendiği commit yakalanır.
    """
    if remote_sha == ZERO:
        # Dal uzakta yeni: diğer uzak dalların kapsamadığı commit'ler.
        patch = _run("log", "-p", "-U0", "--no-color", local_sha, "--not", "--remotes")
    else:
        patch = _run("log", "-p", "-U0", "--no-color", f"{remote_sha}..{local_sha}")

    return [
        ln[1:] for ln in patch.splitlines() if ln.startswith("+") and ln[1:2] != "+"
    ]


def _ranges() -> list[tuple[str, str]]:
    """Taranacak (local_sha, remote_sha) çiftleri.

    İKİ ÇAĞRI BİÇİMİ VAR ve ilkini atlamak bekçiyi sessizce kör bırakır:

    1. pre-commit altında (normal durum): pre-commit git'in stdin'ini KENDİSİ
       tüketir ve aralığı `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` env
       değişkenleriyle verir. Yalnız stdin okuyan bir hook burada HİÇBİR ŞEY
       taramaz ama "sır yok" deyip yeşil döner — 28 Tem'de bu betiğin ilk
       sürümü tam olarak böyleydi, mutasyon testi yakaladı.
    2. Doğrudan git hook'u olarak: stdin'den
       `<local_ref> <local_sha> <remote_ref> <remote_sha>` satırları gelir.
    """
    frm = os.environ.get("PRE_COMMIT_FROM_REF") or os.environ.get("PRE_COMMIT_ORIGIN")
    to = os.environ.get("PRE_COMMIT_TO_REF") or os.environ.get("PRE_COMMIT_SOURCE")
    if to:
        return [(to, frm or ZERO)]

    # pre-commit'in pre-push için GERÇEKTE verdiği değişkenler (28 Tem'de
    # ölçüldü — FROM_REF/TO_REF yok):
    #   PRE_COMMIT_LOCAL_BRANCH / _REMOTE_BRANCH / _REMOTE_NAME / _REMOTE_URL
    yerel = os.environ.get("PRE_COMMIT_LOCAL_BRANCH")
    if yerel:
        local_sha = _run("rev-parse", yerel).strip()
        remote_sha = ZERO
        uzak_dal = os.environ.get("PRE_COMMIT_REMOTE_BRANCH", "")
        uzak_ad = os.environ.get("PRE_COMMIT_REMOTE_NAME", "")
        if uzak_dal and uzak_ad:
            kisa = uzak_dal.rsplit("refs/heads/", 1)[-1]
            izleyen = _run(
                "rev-parse", "--verify", "--quiet", f"{uzak_ad}/{kisa}"
            ).strip()
            if izleyen:
                remote_sha = izleyen
        if local_sha:
            return [(local_sha, remote_sha)]

    ciftler: list[tuple[str, str]] = []
    for satir in sys.stdin:
        parca = satir.split()
        if len(parca) != 4:
            continue
        _, local_sha, _, remote_sha = parca
        if local_sha == ZERO:  # dal siliniyor
            continue
        ciftler.append((local_sha, remote_sha))
    return ciftler


def main() -> int:
    bulgular: list[str] = []
    taranan = 0
    araliklar = _ranges()

    if not araliklar:
        # Aralık çözülemediyse SESSİZCE GEÇME. Bekçinin en tehlikeli hâli
        # "hiçbir şey bulamadım" diyen kör hâlidir.
        # YALNIZ anahtar ADLARI. Değer basmak yasak: `PRE_COMMIT_REMOTE_URL`
        # kimlik bilgisi gömülü bir URL olabilir (https://kullanici:token@...)
        # ve bu çıktı CI loguna + terminal geçmişine düşer. Sır sızıntısını
        # engellemek için yazılmış aracın sır sızdırması olmaz.
        gorulen = sorted(k for k in os.environ if k.startswith("PRE_COMMIT"))
        print(
            "[push-secret-guard] UYARI: push aralığı çözülemedi. Tarama YAPILMADI.\n"
            f"  görülen ortam değişkenleri (yalnız adlar): {gorulen}"
        )
        return 1

    for local_sha, remote_sha in araliklar:
        for line in _added_lines(local_sha, remote_sha):
            taranan += 1
            for ad, desen in PATTERNS.items():
                m = desen.search(line)
                if m:
                    bulgular.append(f"{ad}: {_mask(m.group(0))}")

    if bulgular:
        print("\n[PUSH ENGELLENDİ] Uzağa gidecek commit'lerde sır bulundu:\n")
        for b in dict.fromkeys(bulgular):
            print(f"  - {b}")
        print(
            "\nBu depo PUBLIC. Push edilen içerik geri alınamaz biçimde kamuya\n"
            "açılır; silseniz bile önbellek/kopya kalır.\n"
            "Yapılacak: sırrı geçmişten çıkarın (rebase/filter-repo) VE anahtarı\n"
            "iptal edip yenileyin. Yanlış pozitifse: git push --no-verify\n"
        )
        return 2

    print(f"[push-secret-guard] {taranan} eklenen satır tarandı, sır yok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
