"""Rol kapısı YAKINSAMA bekçisi — X06 (c) 1. adım (S252).

NEDEN VAR
---------
X06'nın iddiası *"5+ ayrı rol kontrolü implementasyonu"* idi. S249 envanteri
**sayının tek başına kusur olmadığını** doğru saptadı: kusur **tutarsızlıktır**.
S252 ölçümü tutarsızlığın nerede yaşadığını gösterdi ve beklenen yerde değildi.

    ADMIN+SUPER_ADMIN ikilisini LİTERAL yazan yer: **35** (AST, 24 Ağu 2026)
    `core/dependencies.py:214` `PLATFORM_ADMIN_ROLES` kanonu: **1'i** kullanıyor

Yani sapma riski KAPI SAYISINDA değil, **kopyalanmış rol kümelerinde**. Her kopya
bağımsız olarak kayabilir — nitekim S252'de tam bu sınıftan iki canlı kusur çıktı
(`api/ogretmen.py:46` ADMIN'i dışarıda bırakıyordu; `api/auth.py:348` haritası
kanonik yazımı hiç tanımıyordu).

BU DOSYA İKİ ŞEY ÇİVİLER
------------------------
1. **YAKINSAMA:** `admin_kullanici_getir` (17 uç) ile kanon `get_current_admin_user`
   (83 uç) BEŞ kanonik rolün BEŞİNDE de AYNI kararı vermeli. İkiz oldukları
   varsayılmaz — her rol için tek tek ölçülür.
2. **CIRCIR (ratchet):** kopya literal sayısı ÖLÇÜLEN değerin üstüne çıkamaz.
   Kalan borç görünür kalır; yeni kopya sessizce eklenemez.

Eşik **ölçülmüştür, seçilmemiştir**. Düşerse eşiği düşür (borç azaldı); yükselirse
yeni bir kopya girmiş demektir — kapı onu göstersin diye var.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

import pytest
from fastapi import HTTPException

from api.admin import admin_kullanici_getir
from core.dependencies import (
    AuthenticatedUser,
    get_current_admin_user,
)
from models.enums_db import UserRole

_BACKEND = Path(__file__).resolve().parents[2]

#: AST ölçümü — her adım ÖLÇÜLDÜ, tahmin edilmedi:
#:   35  başlangıç (24 Ağu)
#:   34  `api/admin.py:42` kanona bağlandı (X06 (c) 1. adım)
#:   23  "öğrenci verisine erişim" kümesinin **12 kopyası** kanona bağlandı,
#:       **+1** kanonun kendi tanımı (`STUDENT_DATA_ACCESS_ROLES`) yeni bir
#:       literaldir → 34 − 12 + 1 = 23. Bu +1 ilk hesabımda YOKTU; sayı
#:       tutmayınca aritmetik yeniden yapıldı.
#: Kalan 23'ün staff-üçlüsü olan 6'sı BİLEREK duruyor (ayrı politikalar):
#:   içerik/kalite (`soru_guncelle`, `soru_sil`, `_OVERRIDE_APPROVERS`) ·
#:   uyumluluk (`_STAFF_COMPLIANCE`) · öğretmen yüzeyi (`get_current_teacher_user`)
KOPYA_LITERAL_TAVANI = 23

#: "Başka bir öğrencinin verisine erişebilen personel" politikasını kullanan
#: modül-düzeyi takma adlar. Çağrı yerleri değişmedi; yalnız TANIM kanona bağlandı.
KANONA_BAGLI_TAKMA_ADLAR = [
    ("api.analytics", "_STUDENT_ANALYTICS_STAFF"),
    ("api.berturk_api", "_STAFF_CAN_TARGET_STUDENT"),
    ("api.cultural_adaptation_api", "_STAFF_STUDENT_ACCESS"),
    ("api.elasticsearch", "_ES_USER_ANALYTICS_STAFF"),
    ("api.exam_performance", "_STAFF_VIEW_STUDENT_PERFORMANCE"),
    ("api.learning_style", "_PRIVILEGED_ROLES"),
    ("api.v1.content_recommendation", "_STAFF_CAN_ACT_FOR_USER"),
]

#: Kanon rol yazımı (PG enum `userrole`, `models/enums_db.py:18`).
TUM_ROLLER = [
    UserRole.STUDENT,
    UserRole.TEACHER,
    UserRole.PARENT,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
]


def _kullanici(rol: UserRole) -> AuthenticatedUser:
    return AuthenticatedUser(
        id="k1", username="olcum", role=rol, email="olcum@kiro2.com", permissions=[]
    )


async def _karar(kapi, rol: UserRole) -> str:
    """Kapının verdiği yargıyı KABUL/RED-403/HATA olarak döndürür."""
    try:
        await kapi(_kullanici(rol))
    except HTTPException as hata:
        return f"RED-{hata.status_code}"
    except (
        Exception
    ) as hata:  # pragma: no cover  # kapi 4xx disi bir sey atarsa gorunsun
        return f"HATA-{type(hata).__name__}"
    return "KABUL"


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", TUM_ROLLER)
async def test_ikiz_kapilar_ayni_rolu_ayni_yargiliyor(rol: UserRole) -> None:
    """X06'nın ASIL sorusu: iki kapı aynı rolü farklı mı yargılıyor?

    `admin_kullanici_getir` 17 ucu, `get_current_admin_user` 83 ucu koruyor.
    İkisi ayrı yargılarsa aynı yetkiye sahip iki kullanıcı farklı muamele görür.
    """
    kanon = await _karar(get_current_admin_user, rol)
    ikiz = await _karar(admin_kullanici_getir, rol)
    assert kanon == ikiz, (
        f"{rol.value}: kanon={kanon} ama ikiz={ikiz}. İki kapı AYNI rolü FARKLI "
        "yargılıyor — X06'nın tam olarak aradığı kusur."
    )


@pytest.mark.asyncio
async def test_kontrol_kolu_yargilar_dejenere_degil() -> None:
    """KONTROL KOLU: yukarıdaki test her şeye 'KABUL' dese de geçerdi.

    Yakınsama testi tek başına anlamsız olurdu: iki kapı da hiçbir şey yapmasa
    (ikisi de KABUL) yine 'aynı' olurlardı. Burada yargıların GERÇEKTEN
    ayrıştığı — yani kapının kapı olduğu — çivilenir.
    """
    kararlar = {rol: await _karar(get_current_admin_user, rol) for rol in TUM_ROLLER}
    assert kararlar[UserRole.ADMIN] == "KABUL"
    assert kararlar[UserRole.SUPER_ADMIN] == "KABUL"
    assert kararlar[UserRole.STUDENT] == "RED-403"
    assert kararlar[UserRole.TEACHER] == "RED-403"
    assert kararlar[UserRole.PARENT] == "RED-403"


@lru_cache(maxsize=1)
def _kopya_literaller() -> tuple[str, ...]:
    """ADMIN+SUPER_ADMIN ikilisini LİTERAL olarak yazan yerler (AST).

    AST kullanılır: yorum satırları ve docstring'ler AST'de YOKTUR, bu yüzden
    bir deseni ANLATAN yorum kusur sanılamaz.

    `lru_cache`: tarama dört ağacı geziyor ve testler onu üç kez çağırıyordu
    (dosya tek koşuda ~170 sn sürüyordu). Sonuç aynı işlem içinde değişmez.
    """
    hedef = {"ADMIN", "SUPER_ADMIN"}
    bulunan: list[str] = []
    for kok in ("api", "core", "services", "app"):
        for yol in (_BACKEND / kok).rglob("*.py"):
            if "__pycache__" in str(yol):
                continue
            try:
                agac = ast.parse(yol.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for dugum in ast.walk(agac):
                if not isinstance(dugum, ast.Tuple | ast.Set | ast.List):
                    continue
                adlar = {e.attr for e in dugum.elts if isinstance(e, ast.Attribute)}
                if hedef <= adlar and len(adlar) <= 3:
                    bulunan.append(
                        f"{yol.relative_to(_BACKEND)}:{dugum.lineno} "
                        f"({', '.join(sorted(adlar))})"
                    )
    return tuple(bulunan)


def test_ogrenci_verisi_kanonu_dogru_uyeleri_tasiyor() -> None:
    """Kanon kümesi daraltılamaz/genişletilemez.

    Daralırsa (ör. TEACHER çıkarılırsa) 12 uç ailesi aynı anda kapanır;
    genişlerse aynı anda açılır. Bu yüzden tam eşitlik.
    """
    from core.dependencies import STUDENT_DATA_ACCESS_ROLES

    assert (
        frozenset({UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN})
        == STUDENT_DATA_ACCESS_ROLES
    )


@pytest.mark.parametrize(("modul_adi", "takma_ad"), KANONA_BAGLI_TAKMA_ADLAR)
def test_takma_adlar_kanonun_KENDISI(modul_adi: str, takma_ad: str) -> None:
    """Takma ad kanonla AYNI NESNE olmalı — eşit değil, AYNI.

    Eşitlik (`==`) yeterli değildi: birisi kanonla aynı üyelere sahip YENİ bir
    frozenset yazsa test geçerdi ve kopya sessizce geri gelirdi. Kimlik (`is`)
    tek kaynağı kanıtlar.
    """
    import importlib

    from core.dependencies import STUDENT_DATA_ACCESS_ROLES

    modul = importlib.import_module(modul_adi)
    assert hasattr(modul, takma_ad), f"{modul_adi}.{takma_ad} kayboldu"
    assert getattr(modul, takma_ad) is STUDENT_DATA_ACCESS_ROLES, (
        f"{modul_adi}.{takma_ad} kanonun kendisi DEĞİL — kopya geri gelmiş. "
        "`core/dependencies.STUDENT_DATA_ACCESS_ROLES` kullan."
    )


def test_alet_dogrulamasi_kanon_tanimi_bulunuyor() -> None:
    """KONTROL KOLU: tarayıcı bilinen-VAR bir kopyayı görüyor mu.

    Boş dönerse aşağıdaki çırçır hiçbir şey ölçmeden yeşil kalır — yanlış-SIFIR.
    """
    bulunan = _kopya_literaller()
    assert (
        len(bulunan) >= 10
    ), f"AST tarayıcı yalnız {len(bulunan)} kopya buldu; alet arızalı olabilir"
    assert any(
        "core/dependencies.py" in b or "core\\dependencies.py" in b for b in bulunan
    ), "kanon tanımının kendisi (dependencies.py:215) görünmüyor -> tarayıcı kör"


def test_circir_kopya_rol_kumesi_sayisi_artmiyor() -> None:
    """ÇIRÇIR: kopya literal sayısı ölçülen tavanı aşamaz.

    Kalan borç X06 (c) tam göçüdür ve GÖRÜNÜR bırakılmıştır — sessizce
    büyümesini bu kapı engeller.
    """
    bulunan = _kopya_literaller()
    assert len(bulunan) <= KOPYA_LITERAL_TAVANI, (
        f"Kopya rol kümesi {len(bulunan)} (tavan {KOPYA_LITERAL_TAVANI}). "
        "Yeni bir kopya eklendi — `core/dependencies.PLATFORM_ADMIN_ROLES` "
        "kanonunu kullan.\n" + "\n".join(sorted(bulunan))
    )


def test_circir_tavani_gercek_sayiyla_birebir_ayni() -> None:
    """ÇIRÇIRIN KENDİSİNİ korur — mutasyon bu boşluğu buldu (S252).

    İlk sürümde yalnız `<=` vardı: tavanı 999'a çekmek HİÇBİR testi düşürmedi
    (M3 hayatta kaldı), yani sayaç sessizce etkisizleştirilebiliyordu. Tam
    eşitlik bunu imkânsız kılar — tavan gerçek sayıyla oynamak zorunda.

    Borç AZALIRSA bu test de düşer; bu KASITLIDIR: tavanı düşürmek bir
    muhasebe adımıdır ve kazanımın kayda geçmesini zorunlu kılar.
    """
    gercek = len(_kopya_literaller())
    assert gercek == KOPYA_LITERAL_TAVANI, (
        f"Tavan {KOPYA_LITERAL_TAVANI} ama gerçek sayı {gercek}. "
        + (
            "Borç AZALMIŞ — tavanı düşür ve commit mesajına yaz."
            if gercek < KOPYA_LITERAL_TAVANI
            else "Borç ARTMIŞ — kanonu kullan, tavanı yükseltme."
        )
    )
