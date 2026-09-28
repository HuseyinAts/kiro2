"""Profil gudumlu ortak kitap hatti (FERNUS ekran goruntusu -> pasif ithal).

Her kitap `kitap_hat/profiller/<kod>.py` icinde yalniz kendi olculen
sabitlerini ve sayfa turu / anahtar bolgesi kancalarini tasir; tarama,
anahtar, harita, kutu, kirpim, metin, mukerrer ve ithal adimlari bu paketin
ortak modulleridir (acil2021tyt_* kitap-ozel betiklerinin genellestirilmis
hali; KITAP_ISLEME_DARBOGAZ.md madde 7).

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.tarama --profil acl23ag [--yaz]
"""
