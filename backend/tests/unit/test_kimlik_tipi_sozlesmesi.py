"""VARCHAR kimlik `int` diye tiplenmez — yanıt şeması sözleşmesi.

NEDEN VAR (gf25'in ÜÇÜNCÜ sebebi, 2 Ağu 2026)
---------------------------------------------
`POST /api/v1/coaching/signals` üç SERİ BAĞLI sebeple 500 veriyordu. İlk ikisi
kapatıldıktan sonra üçüncüsü göründü:

    1 validation error for RecordSignalResponse
    id
      Input should be a valid integer, unable to parse string as an integer
      [type=int_parsing, input_value='4291f920-af94-4521-a7a9-fcbb28f7032d']

Bu, satır YAZILDIKTAN sonra patlıyordu: 8 ardışık istek 8 satır yazdı
(28 → 37 ölçüldü) ve sekizi de 500 döndü. Yani veri kaydediliyor, istemci
"başarısız" duyuyor — sessiz tutarsızlık.

SINIF
-----
CLAUDE.md sert kuralı: **`users.id` ve `user_badges.id` VARCHAR, UUID değil.**
Bu depoda kimlikler `String` + `default=lambda: str(uuid.uuid4())`. Bir Pydantic
yanıt şemasının `id: int` demesi, o ucu ilk gerçek satırda 500 yapar.
`golden-flows.md` bunu zaten "rule-of-five Pydantic `user_id: int`" olarak
adlandırıyor (S148 önleyici süpürmesi) — süpürme yanıt şemalarını kaçırmış.

ÖLÇÜM (2 Ağu, canlı `information_schema`)
-----------------------------------------
`api/` + `app/api/` genelinde `int` tipli kimlik alanı 5 isabet:
  api/coaching_api.py:59    id  -> student_engagement_signals.id  = VARCHAR  ✗
  api/audit_logs_api.py:24  id  -> audit_logs.id                  = VARCHAR  ✗
  api/oba_api.py:40         id  -> obalar.id                      = INTEGER  ✓
  api/ebatv.py:475          video_id — Path parametresi, DB kimliği değil     ✓
  api/yolo_detection_api.py:76  class_id — ML sınıf indeksi                   ✓

Yani ölçüm iki gerçek kusur + üç yanlış-pozitif ayırdı. `obalar.id`
GERÇEKTEN integer — ölçüm yapılmasaydı o da "düzeltilip" bozulacaktı.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from api.audit_logs_api import AuditLogResponse
from api.coaching_api import RecordSignalResponse

# Bu depodaki kimlik uretecinin gercek ciktisi:
# models/coaching.py:64  default=lambda: str(uuid.uuid4())
ORNEK_KIMLIK = str(uuid.uuid4())


def test_sinyal_yaniti_uuid_kimligi_kabul_eder() -> None:
    """gf25'in ucuncu sebebi. Fix'ten ONCE ValidationError ile duser."""
    yanit = RecordSignalResponse(
        id=ORNEK_KIMLIK,
        student_id="0d3b011a-8be9-49cb-9a87-f8a8317ccc3d",
        signal_type="session_duration",
        value=1800.0,
        recorded_at="2026-08-02T14:41:29+03:00",
    )

    assert (
        yanit.id == ORNEK_KIMLIK
    ), "Kimlik yuvarlanmis/donusturulmus — VARCHAR kimlik AYNEN korunmali."


def test_denetim_kaydi_yaniti_uuid_kimligi_kabul_eder() -> None:
    """KACAN KARDES: audit_logs.id de VARCHAR (canli olcum, 2 Agu)."""
    yanit = AuditLogResponse(
        id=ORNEK_KIMLIK,
        timestamp=datetime(2026, 8, 2, 14, 41, 29, tzinfo=UTC),
        event_type="login",
        severity="info",
        user_id="0d3b011a-8be9-49cb-9a87-f8a8317ccc3d",
        user_email="test@kiro2.com",
        user_role="student",
        ip_address="127.0.0.1",
        resource_type=None,
        resource_id=None,
        action="login",
        description=None,
        success="true",
        error_message=None,
    )

    assert yanit.id == ORNEK_KIMLIK


def test_sayisal_dize_kimlik_sessizce_int_olmaz() -> None:
    """Mutasyon kalkani: alan `int | None` birakilirsa bu test de duser.

    Pydantic v2 `int` alanina "123" verildiginde onu 123'e cevirir. Yani
    yalnizca UUID ile sinamak, birinin alani `int` yapip testleri sayisal
    dizeyle "duzeltmesine" acik kalirdi. Burada kimligin TIP olarak dize
    kaldigini iddia ediyoruz.
    """
    yanit = RecordSignalResponse(
        id="123",
        student_id="s1",
        signal_type="session_duration",
        value=1.0,
        recorded_at="2026-08-02T14:41:29+03:00",
    )

    assert yanit.id == "123"
    assert isinstance(yanit.id, str), (
        "Kimlik int'e donusturuldu — VARCHAR sutunla eslesmez, "
        "sifir-onekli/UUID kimlikler bozulur."
    )


def test_alet_dogrulamasi_sema_gercekten_dogruluyor() -> None:
    """KONTROL KOLU — sema hic dogrulama yapmiyorsa yukarisi anlamsiz olurdu.

    `value` alani float; ayristirilamaz bir dize KIRMIZI vermeli. Bu
    dusmezse Pydantic dogrulamasi devre disidir ve olcum gecersizdir.
    """
    with pytest.raises(ValidationError):
        RecordSignalResponse(
            id=ORNEK_KIMLIK,
            student_id="s1",
            signal_type="session_duration",
            value="sayi-degil",
            recorded_at="2026-08-02T14:41:29+03:00",
        )
