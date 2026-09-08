"""FastAPI 0.141'de GERCEK rota yuzeyini sayan tek tanim (SS10.69).

NEDEN VAR
---------
FastAPI 0.141 `include_router()` ile eklenen her router icin `app.routes`a
`fastapi.routing._IncludedRouter` adinda bir ISARETCI nesne koyuyor. Bu
nesnenin `.path` ozniteligi YOK ve alt rotalari `app.routes` icine
duzlestirilmiyor. Olculdu (7 Eyl 2026, `main.app`):

    app.routes toplam        : 156
      .path tasiyan          :   5   -> /openapi.json /docs /docs/oauth2-redirect
      /api ile baslayan      :   0      /redoc /
      path'siz (isaretci)    : 151   -> hepsi _IncludedRouter
    gercek rota sayisi       : 1214
    app.openapi() paths      : 1123 (1092 tanesi /api ile basliyor)

`app.openapi()` cagrisi `app.routes`u DUZLESTIRMIYOR; sonradan bakildiginda
yine 5 yol goruluyor.

SONUCU: `app.routes` uzerinde donen HER rota-butunlugu bekcisi bu surumde
KORDUR -- 1214 rotanin yalnizca 5'ini gorur ve hicbir sey bulamadigi icin
YESIL kalir. Bu, deponun `L-s231-hacim-vekil-olcum-icerik-degil` dersinin
rota yuzeyindeki karsiligidir: bekci kosuyor ama olcmuyor.

KULLANIM
--------
    from tests.rota_yuzeyi import gercek_rotalar

    for yol, yontemler, ad in gercek_rotalar(app):
        ...

`app.openapi()["paths"]` de dogru bir kaynaktir ama YOLA gore anahtarlanmis
oldugu icin CARPISMA (ayni path+method'un iki kez kaydi) goremez. Carpisma
aramak icin bu modul gerekir.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


def gercek_rotalar(uygulama: Any) -> Iterator[tuple[str, set[str], str]]:
    """`app.routes`taki isaretcileri acarak (yol, yontemler, ad) uret.

    `_IncludedRouter` nesnesi alt router'i `original_router`, kayit onekini
    ise `include_context.prefix` uzerinden tasiyor. Ic ice include'lar icin
    yigin kullanilir.
    """
    yigin: list[Any] = list(uygulama.routes)
    while yigin:
        dugum = yigin.pop()

        ic_router = getattr(dugum, "original_router", None)
        if ic_router is not None and hasattr(ic_router, "routes"):
            baglam = getattr(dugum, "include_context", None)
            onek = getattr(baglam, "prefix", "") or ""
            for alt in ic_router.routes:
                yol = getattr(alt, "path", None)
                if yol is None:
                    # ic ice include -> yigina at
                    yigin.append(alt)
                    continue
                yield (
                    onek + yol,
                    set(getattr(alt, "methods", set()) or set()),
                    getattr(alt, "name", "?"),
                )
            continue

        yol = getattr(dugum, "path", None)
        if yol is not None:
            yield (
                yol,
                set(getattr(dugum, "methods", set()) or set()),
                getattr(dugum, "name", "?"),
            )


def carpismalar(uygulama: Any) -> dict[tuple[str, str], list[str]]:
    """Ayni (yol, yontem) ciftine kayitli BIRDEN COK isleyiciyi dondur.

    Starlette'te son kayit kazanir: onceki isleyici sessizce golgede kalir.
    HEAD/OPTIONS disarida birakilir (Starlette bunlari otomatik uretir).
    """
    harita: dict[tuple[str, str], list[str]] = {}
    for yol, yontemler, ad in gercek_rotalar(uygulama):
        for yontem in yontemler or {"GET"}:
            if yontem in ("HEAD", "OPTIONS"):
                continue
            harita.setdefault((yol, yontem), []).append(ad)
    return {k: v for k, v in harita.items() if len(v) > 1}
