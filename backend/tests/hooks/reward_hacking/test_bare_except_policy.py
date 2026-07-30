"""bare-except politikası kendisiyle çelişmemeli (#449).

30 TEM 2026 ÖLÇÜMÜ — dört asgari fixture, `EmptyExceptionDetector().detect()`:

    except: pass                                    -> CRITICAL
    except: log.warning(...)                        -> CRITICAL   <-- yanlis-pozitif
    except: pass  + try BLOGUNDAN SONRA log.info()  -> INFO       <-- yanlis-NEGATIF
    except ValueError: log.warning(...)             -> (bulgu yok)

Yani dosya iki zıt yönde birden hatalı: doğru şekilde loglanan bir bare except,
hiç loglanmayan `pass` ile AYNI sınıfa düşüyor; buna karşılık gerçek bir yutma,
yakınında alâkasız bir log satırı olduğu için görünmez oluyor.

İKİ KÖK NEDEN

1) `_has_logging_or_comment(content, line_number)` — `except` satırından sonraki
   ÜÇ SATIRA bakıyor, handler GÖVDESİYLE sınırlı değil. `try` bloğu bittikten
   sonraki bir `log.info()` bile "bu handler logluyor" sanılıyor. Yakınlık
   sezgisi, kapsam bilgisinin yerini tutmuyor.

2) `_detect_bare_except()` log kontrolünü HİÇ yapmıyor; her bare except'e
   `confidence=0.95` veriyor ve `default_severity` CRITICAL olduğu için
   loglanmış olan da bloklayıcı oluyor.

POLİTİKA (bu testlerin sabitlediği)

    bare except + gövdede log/raise YOK   -> CRITICAL  (sessiz yutma)
    bare except + gövdede log/raise VAR   -> WARNING   (görünür ama hâlâ
                                             KeyboardInterrupt/SystemExit
                                             yakalıyor; INFO'ya indirilemez)
    belirli tip except + log              -> bulgu yok

FIX'IN DEĞERİ ÖLÇÜLDÜ (#451 dersi): tüm backend'de 31 bare except var —
`_scripts/` 25 (2'si print'li), `alembic/` 5, `tests/` 1; üretim yollarında
(api/core/services/models) SIFIR. Yani yanlış-pozitif kazancı 2 vaka, gözlenen
yanlış-negatif 0. Fix yine yapıldı çünkü BEDELİ de sıfır: kapsam daraltmak yeni
yanlış-pozitif üretmiyor. #451'de fix uygulanmamıştı, çünkü orada bedel +231
CRITICAL'di — burada öyle bir bedel yok.
"""

from __future__ import annotations

import asyncio

import pytest

from hooks.reward_hacking.detectors import EmptyExceptionDetector
from hooks.reward_hacking.models.enums import SeverityLevel

pytestmark = [pytest.mark.unit, pytest.mark.security]

SESSIZ_YUTMA = """\
def f():
    try:
        g()
    except:
        pass
"""

LOGLANMIS_BARE = """\
import logging

log = logging.getLogger(__name__)


def f():
    try:
        g()
    except:
        log.warning("basarisiz")
"""

# KRITIK FIXTURE: log satiri try BLOGUNUN DISINDA, handler govdesinde DEGIL.
# Yutma gercek; yakinlik sezgisi bunu INFO'ya indiriyordu.
YUTMA_AMA_YAKINDA_LOG = """\
import logging

log = logging.getLogger(__name__)


def f():
    try:
        g()
    except:
        pass
    log.info("devam")
"""

BELIRLI_TIP_LOGLU = """\
import logging

log = logging.getLogger(__name__)


def f():
    try:
        g()
    except ValueError:
        log.warning("basarisiz")
"""


def _bulgular(kaynak: str):
    return asyncio.run(EmptyExceptionDetector().detect("app/servis.py", kaynak))


def _sev(deger) -> str:
    """severity'yi tek biçime indir.

    Dedektör TUTARSIZ tip saklıyordu: `_create_result` yolu `use_enum_values`
    sayesinde düz string ("CRITICAL") verirken, `result.severity =
    SeverityLevel.INFO` satırı ENUM'u ham atıyor (Pydantic v2'de
    `validate_assignment` kapalı olduğu için dönüşüm olmuyor) ve `str()` onu
    "SeverityLevel.INFO" yapıyor. Bu normalize edilmezse `SeverityLevel.INFO
    not in {...}` iddiası INFO mevcut olsa bile SESSİZCE GEÇER — ilk sürümde
    tam bu oldu, RED çıktısından yakalandı.
    """
    return str(deger).rsplit(".", 1)[-1]


def _severityler(kaynak: str) -> set[str]:
    return {_sev(r.severity) for r in _bulgular(kaynak)}


def test_sessiz_yutma_kritik_kalir():
    """MUTASYON GÜVENCESİ: `except: pass` her koşulda CRITICAL olmalı."""
    assert SeverityLevel.CRITICAL.value in _severityler(SESSIZ_YUTMA)


def test_yakinda_log_olmasi_gercek_yutmayi_gizlemez():
    """Handler GÖVDESİ dışındaki bir log satırı yutmayı INFO'ya indirmemeli.

    Ölçüm: fix öncesi bu fixture tek bulgu üretiyordu ve severity INFO'ydu —
    yani `except: pass` görünmez oluyordu. Sebep: `_has_logging_or_comment`
    except satırından sonraki 3 satıra bakıyor, blok sınırına bakmıyor.
    """
    severityler = _severityler(YUTMA_AMA_YAKINDA_LOG)
    assert (
        SeverityLevel.INFO.value not in severityler
    ), f"gercek yutma INFO'ya indirildi: {severityler}"
    assert SeverityLevel.CRITICAL.value in severityler


def test_loglanmis_bare_except_push_bloklamaz():
    """Gövdesinde log olan bare except CRITICAL olmamalı (yanlış-pozitif)."""
    assert SeverityLevel.CRITICAL.value not in _severityler(LOGLANMIS_BARE)


def test_loglanmis_bare_except_yine_de_raporlanir():
    """KÖRLEŞME GÜVENCESİ: gevşetme = susturma DEĞİL.

    bare `except:` loglansa bile KeyboardInterrupt/SystemExit yakalar; bu
    yüzden WARNING olarak GÖRÜNÜR kalmalı, INFO'ya veya hiçliğe indirilemez.
    """
    bulgular = _bulgular(LOGLANMIS_BARE)
    assert bulgular, "loglanmis bare except tamamen susturulmus"
    assert SeverityLevel.WARNING.value in {_sev(r.severity) for r in bulgular}


def test_belirli_tip_except_loglu_ise_bulgu_uretmez():
    """`except ValueError: log...` mesru — bekçi burada susmalı."""
    assert _bulgular(BELIRLI_TIP_LOGLU) == []
