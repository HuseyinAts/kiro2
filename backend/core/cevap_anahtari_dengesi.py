"""Sinav olustururken cevap anahtari dengesi (rapor madde 4a, 9 Eyl 2026).

OLCUM (canli TYT havuzu, 3.000 rastgele cekim, _ci_art/anahtar_mc.py):
  havuzda sik dagilimi A %15,7 / C %24,0 (KIMYA: A 506 vs C 858);
  rastgele cekilen bir denemede en baskin sikkin payi p50 %25,2, p90 %28,0,
  p99 %32,7; denemelerin %54'unde bir sik %25'i asiyor.
Gercek OSYM anahtarlarinda her sik ~%20 (18-22 bandi). Havuzdaki egiklik
sinava aynen tasiniyor ve "hep C isaretle" gibi stratejileri odullendiriyor.

KARAR: sik SIRALAMASI degistirilmez (sorunun bicimi/gorseli sabit kalir);
secim SONRASI sinav boyu her sik icin tavan uygulanir:
    tavan = max(1, ceil(fiili_soru_sayisi * TAVAN_ORANI))
Tavani asan sikkin sorulari, AYNI DERSIN havuzundan tavanin altindaki bir
sikka sahip secilmemis bir soruyla takas edilir. Aday yoksa takas yapilmaz:
tavan yumusak, soru sayisi ve ders dagilimi serttir (sinav asla kuculmez,
ders kotasi degismez).
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

# Sinav boyu bir sikkin alabilecegi azami pay. %25: p50 cekimin (%25,2)
# hemen altinda -- denemelerin yarisinda devreye girer, %30 olsa yalnizca
# %3,4'unde girerdi (olculdu).
TAVAN_ORANI: float = 0.25

GECERLI_SIKLAR = frozenset("ABCDE")

# (soru id, sik, ders)
Secim = tuple[str, str | None, str]


def sik_normalize(ham: Any) -> str | None:
    """'c', ' C) ', 'C' -> 'C'; bos/bilinmeyen -> None (tavana sayilmaz)."""
    if ham is None:
        return None
    s = str(ham).strip().upper()[:1]
    return s if s in GECERLI_SIKLAR else None


def tavan_hesapla(fiili_soru_sayisi: int, oran: float = TAVAN_ORANI) -> int:
    return max(1, math.ceil(fiili_soru_sayisi * oran))


def yeniden_dengele(
    secim: Sequence[Secim],
    havuzlar: Mapping[str, Sequence[tuple[str, str | None]]],
    tavan: int,
    rng: random.Random | Any = random,
) -> list[Secim]:
    """Tavani asan siklari ayni dersin havuzundan takasla dengeler.

    Sonuc `secim` ile ayni uzunlukta ve ayni sirada; yalnizca takas edilen
    konumlarin (id, sik) ciftleri degisir, ders sabit kalir. Takas adayi:
    ayni dersin havuzunda, secimde olmayan, sikki None ya da sayaci tavanin
    altinda olan soru. Aday yoksa o konum oldugu gibi birakilir.
    """
    sonuc = list(secim)
    sayac: Counter[str] = Counter(s for _, s, _ in sonuc if s is not None)
    secili = {sid for sid, _, _ in sonuc}
    for sik in sorted(sayac, key=lambda k: (-sayac[k], k)):
        if sayac[sik] <= tavan:
            continue
        konumlar = [i for i, (_, s, _) in enumerate(sonuc) if s == sik]
        rng.shuffle(konumlar)
        for i in konumlar:
            if sayac[sik] <= tavan:
                break
            _, _, ders = sonuc[i]
            adaylar = [
                (aid, ak)
                for aid, ak in havuzlar.get(ders, ())
                if aid not in secili and (ak is None or sayac[ak] < tavan)
            ]
            if not adaylar:
                continue
            yeni_id, yeni_sik = rng.choice(adaylar)
            secili.discard(sonuc[i][0])
            secili.add(yeni_id)
            sonuc[i] = (yeni_id, yeni_sik, ders)
            sayac[sik] -= 1
            if yeni_sik is not None:
                sayac[yeni_sik] += 1
    return sonuc
