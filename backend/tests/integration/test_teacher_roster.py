"""Öğretmen sınıf listesi (roster) — öğretmen sınıfına öğrenci ekleyebiliyor mu?

29 Tem 2026 ÖLÇÜMÜ (satışa hazırlık blocker #6):

    backend/app/api/teacher_classroom.py
      GET  /api/v1/teacher/students   -> VAR, ama ad/soyad/email SABİT BOŞ STRING
                                         (satır 203: "filled by ... later")
      POST /api/v1/teacher/students   -> YOK
      DELETE .../students/{id}        -> YOK

Yani öğretmen sınıf açabiliyor ama içine öğrenci koyamıyor; koysa bile listede
kimliksiz satırlar görüyor. 27 Tem'de "6/6 uç 500->200" diye kapatılmıştı —
200 dönmek, anlamlı veri döndürmek DEĞİL.

AYRICA ÖLÇÜLDÜ: bu router'da HİÇ rol kapısı yok. `get_current_user` yalnız
kimlik doğruluyor, rol bakmıyor. Bugün herhangi bir öğrenci `POST
/teacher/classes` ile kendini "öğretmen" ilan edip sınıf açabiliyor. Eklediğimiz
uç BAŞKA İNSANLARIN KİMLİĞİNİ döndürdüğü için bu boşluk kopyalanamaz —
testler rol kapısını şart koşuyor.

TASARIM KARARI (sahiplik kontrolü nerede):
Sınıfın öğretmene ait olduğu kontrolü SQL `WHERE`ine gömülmüyor, handler'da
açık bir `if` olarak duruyor. İki sebep: (1) yetki kararı okunabilir ve
denetlenebilir olmalı, (2) `WHERE`e gömülü bir kontrol, sorguyu taklit eden
hiçbir testle doğrulanamaz — testin yanlışlıkla yeşil geçtiği sınıf tam olarak
budur.

VERİTABANI NEDEN SAHTE: bkz. test_password_recovery_flow.py modül docstring'i
(conftest DATABASE_URL'i sqlite'a eziyor). Buradaki iddia SQL değil, YETKİ ve
sözleşme. Yetki kararları Python'da olduğu için sahte oturum onları gizleyemez.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.security]

OGRETMEN_ID = "teacher-1"
BASKA_OGRETMEN_ID = "teacher-2"


class _Result:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalar_one_or_none(self) -> Any:
        return self._rows[0] if self._rows else None

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return list(self._rows)


def _duzlestir(degerler: Any) -> set[str]:
    """Bağlı parametreleri düz bir string kümesine indir.

    `col.in_([...])` bağlı DEĞERİ bir LİSTE olarak verir; `str()` alınca
    "[UUID('8a37…')]" çıkar ve hiçbir satıra eşleşmez. Bu tek satırlık kusur,
    kimlik testinin boş liste görmesine yol açtı.
    """
    duz: set[str] = set()
    for v in degerler:
        if isinstance(v, list | tuple | set):
            duz.update(str(i) for i in v)
        else:
            duz.add(str(v))
    return duz


class _Db:
    """Bağlı parametrelere göre satır döndüren asgari AsyncSession ikamesi.

    Filtre mantığı bilerek basit: sorgunun bağlı değerleri toplanır ve o
    varlığın satırlarından herhangi bir alanı bu değerlerle eşleşenler döner.
    Testlerdeki id/e-posta değerleri birbirinden ayrık olduğu için bu yeterli.
    """

    def __init__(self) -> None:
        self.satirlar: dict[str, list[Any]] = {}
        self.eklenen: list[Any] = []
        self.silinen: list[Any] = []
        self.commit_sayisi = 0

    def ekle(self, *nesneler: Any) -> None:
        for n in nesneler:
            self.satirlar.setdefault(type(n).__name__, []).append(n)

    async def execute(self, stmt: Any, *a: Any, **k: Any) -> _Result:
        try:
            varlik = stmt.column_descriptions[0]["entity"].__name__
            baglilar = _duzlestir(stmt.compile().params.values())
        except Exception:
            return _Result([])

        aday = self.satirlar.get(varlik, [])
        eslesen = [
            r
            for r in aday
            if baglilar & {str(getattr(r, alan, None)) for alan in _ESLESME_ALANLARI}
        ]
        return _Result(eslesen)

    def add(self, nesne: Any) -> None:
        self.eklenen.append(nesne)
        self.satirlar.setdefault(type(nesne).__name__, []).append(nesne)

    async def delete(self, nesne: Any) -> None:
        self.silinen.append(nesne)
        tur = type(nesne).__name__
        self.satirlar[tur] = [r for r in self.satirlar.get(tur, []) if r is not nesne]

    async def commit(self) -> None:
        self.commit_sayisi += 1

    async def refresh(self, nesne: Any) -> None:
        return None

    async def rollback(self) -> None:
        return None


_ESLESME_ALANLARI = (
    "id",
    "email",
    "classroom_id",
    "student_user_id",
    "teacher_user_id",
)


@pytest.fixture(scope="module")
def app_ve_db():
    """DB bağımlılığını devral.

    DİKKAT: bu router `get_db`yi `app.core.deps`ten alıyor, `core.dependencies`
    ten DEĞİL — ikincisini override etmek hiçbir şey yapmıyor ve istekler
    sessizce gerçek (sqlite) veritabanına gidiyor. Bağımlılık override'ı
    FONKSİYON KİMLİĞİNE göre çalışır; aynı adı taşıyan sarmalayıcı başka bir
    nesnedir.
    """
    from app.core.deps import get_db as app_get_db
    from main import app

    db = _Db()

    async def _override():
        yield db

    app.dependency_overrides[app_get_db] = _override
    try:
        yield app, db
    finally:
        app.dependency_overrides.pop(app_get_db, None)


@pytest.fixture
def db(app_ve_db):
    _app, db = app_ve_db
    db.satirlar.clear()
    db.eklenen.clear()
    db.silinen.clear()
    db.commit_sayisi = 0
    return db


@pytest.fixture
def client(app_ve_db):
    from fastapi.testclient import TestClient

    app, _db = app_ve_db
    with TestClient(app) as c:
        yield c


def _kimlik(app, rol: str, user_id: str):
    """`get_current_user`ı verilen rolle sabitle."""
    from core.dependencies import AuthenticatedUser, get_current_user

    async def _override() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user_id,
            username=f"{rol}-{user_id}",
            role=rol,
            email=f"{user_id}@kiro2.test",
        )

    app.dependency_overrides[get_current_user] = _override


@pytest.fixture
def ogretmen(app_ve_db):
    app, _db = app_ve_db
    _kimlik(app, "teacher", OGRETMEN_ID)
    yield
    from core.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def ogrenci_kimligi(app_ve_db):
    app, _db = app_ve_db
    _kimlik(app, "student", "student-999")
    yield
    from core.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)


def _sinif(teacher_id: str = OGRETMEN_ID):
    from models.teacher_classroom import TeacherClassroom

    return TeacherClassroom(
        id=uuid.uuid4(),
        teacher_user_id=teacher_id,
        sinif_adi="12-A",
        seviye="12",
        ders="MATEMATIK",
    )


def _kullanici(rol: str = "student", email: str | None = None):
    from models.database import User as DBUser

    benzersiz = uuid.uuid4().hex[:8]
    return DBUser(
        id=f"user-{benzersiz}",
        email=email or f"ogrenci-{benzersiz}@okul.test",
        username=f"ogrenci-{benzersiz}",
        password_hash="x",  # noqa: S106
        role=rol,
        first_name="Zeynep",
        last_name="Kaya",
    )


# ---------------------------------------------------------------------------
# Yetki — en kritik değişmezler
# ---------------------------------------------------------------------------


# Gerçek rol kümesi: STUDENT / TEACHER / PARENT / ADMIN / SUPER_ADMIN.
# Personel olmayan ikisi burada; "guest" diye bir rol YOK (uydurma rol
# `AuthenticatedUser` doğrulamasından geçmiyor — kapı değil, şema reddediyor).
@pytest.mark.parametrize("personel_disi_rol", ["student", "parent"])
def test_non_staff_roles_cannot_add_anyone_to_a_class(
    client, db, app_ve_db, personel_disi_rol
):
    """Personel OLMAYAN hiçbir rol bu ucu çağıramamalı.

    Önceden yalnız "student" sınanıyordu; kapı `parent`/`guest` için de
    tutmalı, aksi hâlde bir veli e-posta yazıp öğrenci adlarını okuyabilirdi.
    """
    app, _db = app_ve_db
    _kimlik(app, personel_disi_rol, f"{personel_disi_rol}-42")
    try:
        sinif = _sinif()
        hedef = _kullanici()
        db.ekle(sinif, hedef)

        resp = client.post(
            f"/api/v1/teacher/classes/{sinif.id}/students",
            json={"email": hedef.email},
        )

        assert resp.status_code == 403, (
            f"{personel_disi_rol} rolü sınıfa öğrenci ekleyebiliyor: "
            f"{resp.status_code} {resp.text[:200]}"
        )
        assert not db.eklenen, "yetkisiz istekte satır yazıldı"
    finally:
        from core.dependencies import get_current_user

        app.dependency_overrides.pop(get_current_user, None)


def test_student_role_cannot_add_anyone_to_a_class(client, db, ogrenci_kimligi):
    """Öğrenci rolü bu ucu HİÇ çağıramamalı.

    Bu router'da bugün rol kapısı yok; uç kimlik döndürdüğü için öğrenciye
    açık bırakmak, herkesin e-posta yazıp ad-soyad öğrenebilmesi demek olurdu.
    """
    sinif = _sinif()
    hedef = _kullanici()
    db.ekle(sinif, hedef)

    resp = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students",
        json={"email": hedef.email},
    )

    assert resp.status_code == 403, (
        f"öğrenci rolü sınıfa öğrenci ekleyebiliyor: {resp.status_code} "
        f"{resp.text[:200]}"
    )
    assert not db.eklenen, "yetkisiz istekte satır yazıldı"


def test_teacher_cannot_add_to_someone_elses_class(client, db, ogretmen):
    """IDOR: başkasının sınıf id'siyle ekleme yapılamamalı."""
    baskasinin_sinifi = _sinif(teacher_id=BASKA_OGRETMEN_ID)
    hedef = _kullanici()
    db.ekle(baskasinin_sinifi, hedef)

    resp = client.post(
        f"/api/v1/teacher/classes/{baskasinin_sinifi.id}/students",
        json={"email": hedef.email},
    )

    assert (
        resp.status_code == 404
    ), f"başkasının sınıfına ekleme yapılabildi: {resp.status_code} {resp.text[:200]}"
    assert (
        resp.json().get("detail") != "Not Found"
    ), "404 rotanın YOKLUĞUNDAN geliyor — IDOR iddiası doğrulanmış olmuyor"
    assert not db.eklenen, "IDOR isteğinde satır yazıldı"


def test_only_students_can_be_added(client, db, ogretmen):
    """Hedef kullanıcı ÖĞRENCİ olmalı.

    Aksi hâlde öğretmen bir admin'in e-postasını yazıp adını/soyadını
    listede okuyabilirdi — kimlik ifşası, roster değil.
    """
    sinif = _sinif()
    admin = _kullanici(rol="admin")  # e-posta fabrikadan — sabit adres yok
    db.ekle(sinif, admin)

    resp = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students",
        json={"email": admin.email},
    )

    assert resp.status_code in (400, 404), (
        f"öğrenci olmayan kullanıcı sınıfa eklendi: {resp.status_code} "
        f"{resp.text[:200]}"
    )
    assert not db.eklenen


# ---------------------------------------------------------------------------
# İşlevsellik
# ---------------------------------------------------------------------------


def test_teacher_adds_a_student_by_email(client, db, ogretmen):
    sinif = _sinif()
    hedef = _kullanici()
    db.ekle(sinif, hedef)

    resp = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students",
        json={"email": hedef.email},
    )

    assert resp.status_code == 200, resp.text
    govde = resp.json().get("data") or resp.json()
    assert govde.get("student_user_id") == hedef.id
    assert govde.get("email") == hedef.email
    assert db.commit_sayisi >= 1, "üyelik yazılmadı"


def test_unknown_email_is_rejected_without_writing(client, db, ogretmen):
    """Kayıtlı olmayan e-posta reddedilmeli — ama ROTANIN VARLIĞI da şart.

    RED turunda bu test TEK BAŞINA yeşil geçti: uç henüz yokken FastAPI zaten
    404 döndürüyordu ve iddia boşa doğrulanıyordu. Aynı tuzağa aynı gün
    ikinci kez düşülmemesi için önce ucun kayıtlı olduğunu şart koşuyoruz.
    """
    sinif = _sinif()
    db.ekle(sinif)

    resp = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students",
        json={"email": "kayitli-degil@okul.test"},
    )

    assert resp.status_code == 404
    assert (
        resp.json().get("detail") != "Not Found"
    ), "404 rotanın YOKLUĞUNDAN geliyor — uç kayıtlı değil, test sahte yeşil"
    assert not db.eklenen


def test_adding_the_same_student_twice_does_not_duplicate(client, db, ogretmen):
    """Çift ekleme satır çoğaltmamalı — liste ve sayaçlar bozulur."""
    sinif = _sinif()
    hedef = _kullanici()
    db.ekle(sinif, hedef)

    ilk = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students", json={"email": hedef.email}
    )
    assert ilk.status_code == 200, ilk.text
    yazilan_ilk = len(db.eklenen)

    ikinci = client.post(
        f"/api/v1/teacher/classes/{sinif.id}/students", json={"email": hedef.email}
    )

    assert ikinci.status_code in (200, 409), ikinci.text
    assert len(db.eklenen) == yazilan_ilk, "aynı öğrenci ikinci kez yazıldı"


def test_list_students_returns_real_identity(client, db, ogretmen):
    """`GET /students` gerçek ad/soyad/e-posta döndürmeli.

    Bugün bu alanlar sabit boş string; öğretmen listede kimliksiz satır
    görüyor. Uç 200 dönüyor diye "çalışıyor" sayılmıştı.
    """
    from models.teacher_classroom import TeacherClassroomStudent

    sinif = _sinif()
    hedef = _kullanici()
    uyelik = TeacherClassroomStudent(
        id=uuid.uuid4(), classroom_id=sinif.id, student_user_id=hedef.id
    )
    db.ekle(sinif, hedef, uyelik)

    resp = client.get("/api/v1/teacher/students")

    assert resp.status_code == 200, resp.text
    ogrenciler = resp.json()["data"]["students"]
    assert len(ogrenciler) == 1, resp.text
    kayit = ogrenciler[0]
    assert kayit["email"] == hedef.email, f"e-posta boş/yanlış: {kayit}"
    assert kayit["ad"], f"ad boş döndü — kimliksiz satır: {kayit}"
    assert kayit["sinif"] == "12-A"


def test_teacher_can_remove_a_student_from_own_class(client, db, ogretmen):
    from models.teacher_classroom import TeacherClassroomStudent

    sinif = _sinif()
    hedef = _kullanici()
    uyelik = TeacherClassroomStudent(
        id=uuid.uuid4(), classroom_id=sinif.id, student_user_id=hedef.id
    )
    db.ekle(sinif, hedef, uyelik)

    resp = client.delete(f"/api/v1/teacher/classes/{sinif.id}/students/{hedef.id}")

    assert resp.status_code == 200, resp.text
    assert db.silinen, "üyelik satırı silinmedi"


def test_cannot_remove_from_someone_elses_class(client, db, ogretmen):
    from models.teacher_classroom import TeacherClassroomStudent

    baskasinin = _sinif(teacher_id=BASKA_OGRETMEN_ID)
    hedef = _kullanici()
    uyelik = TeacherClassroomStudent(
        id=uuid.uuid4(), classroom_id=baskasinin.id, student_user_id=hedef.id
    )
    db.ekle(baskasinin, hedef, uyelik)

    resp = client.delete(f"/api/v1/teacher/classes/{baskasinin.id}/students/{hedef.id}")

    assert resp.status_code == 404, resp.text
    assert (
        resp.json().get("detail") != "Not Found"
    ), "404 rotanın YOKLUĞUNDAN geliyor — silme yetkisi iddiası doğrulanmıyor"
    assert not db.silinen, "başkasının sınıfından silme yapıldı"
