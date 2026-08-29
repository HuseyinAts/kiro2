"""
KIRO2 — FSRS API Compatibility Module
"""

# F403 bilerek birakildi: bu bilincli bir geriye-uyumluluk shim'i.
# router_registry.py "dead entry" yorumu tasisa da tam olu degil --
# test_api_batch2.py:932 hala `from api import fsrs` kullaniyor. Somut bir
# import listesine gecmek bu dosyanin amacini (app.api.fsrs ile senkron kalan
# tam bir re-export) bozar ve app.api.fsrs'e her yeni public isim eklendiginde
# burayi da elle guncellemeyi gerektirirdi.
from app.api.fsrs import *  # noqa: F403
