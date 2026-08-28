"""Celery yönlendirme sözleşmesi — gönderilen görev, worker'ın dinlediği kuyruğa düşmeli.

29 Tem 2026 canlı ölçümü: Redis'in `celery` kuyruğunda **3.367** tüketilmemiş mesaj
birikmişti. `task_default_queue` set edilmemişti (celery varsayılanı "celery"),
`task_queues`'ta `default` adlı Queue tanımlı değildi, worker ise docker-compose'da
`-Q default,emails,reports,features,videos,bulk,claude_md` ile başlıyordu — yani
`celery` kuyruğunu hiç dinlemiyordu. Kesişim boştu.

Sonuç: `task_routes`'ta deseni olmayan her görev sessizce çürüdü —
`tasks.refresh_daily_plans` 92, `tasks.push_tasks.send_streak_reminders` 37,
`kiro2.tasks.irt_calibration` 14 kez gönderildi, **0 kez** koştu. Beat "Sending due
task" diye logluyordu, o yüzden zamanlama doğru görünüyordu; eksik olan tüketimdi.

Bu testler config'i AYNALAMAZ. Celery'nin gerçek router'ını
(`celery_app.amqp.router.route`) ve docker-compose'daki gerçek `-Q` listesini okur.
İkisinden biri değişip diğeri değişmezse test kırmızıya döner.

31 Tem 2026 — teslim zincirinin İKİNCİ halkası eklendi. Yukarıdaki testler mesajın
doğru kuyruğa düştüğünü kanıtlar; görevin o kuyruktan alınınca ÇALIŞABİLECEĞİNİ
kanıtlamaz. `tasks.es_sync_tasks` `include=[...]` listesine eklenmemişti: worker
modülü hiç import etmiyor, görev kayıt defterine hiç girmiyordu. Canlı ölçüm
(`inspect registered`) 36 görev döndü, gecelik ES senkronu içlerinde YOKTU — yani
04:00'te beat gönderecek, worker "unregistered task" ile reddedecekti.

Görev elle koşturulduğunda ÇALIŞIYORDU; çünkü elle koşum modülü doğrudan import
eder ve modül kendini import anında kaydeder. Elle koşum tam da kırık olan halkayı
atlar. Bu yüzden aşağıdaki test worker önyüklemesini taklit eder (`include`/`imports`
modüllerini yükler), kayıt defterini elle kurmaz.
"""

import re
from pathlib import Path

import pytest

from core.celery_app import celery_app

pytestmark = pytest.mark.unit

_COMPOSE = Path(__file__).resolve().parents[3] / "docker-compose.yml"

# `celery -A celery_worker worker -l info -Q a,b,c --concurrency=8`
_WORKER_Q_RE = re.compile(r"celery\s+-A\s+\S+\s+worker\b[^\n]*?-Q\s+([\w,]+)")


def _worker_queues() -> set[str]:
    """docker-compose.yml'deki worker komutundan `-Q` listesini oku.

    Sabit liste YAZMIYORUZ: deploy komutu değişirse test onu görmeli.
    """
    text = _COMPOSE.read_text(encoding="utf-8")
    match = _WORKER_Q_RE.search(text)
    assert match, f"{_COMPOSE} içinde `celery ... worker ... -Q ...` komutu bulunamadı"
    return {q.strip() for q in match.group(1).split(",") if q.strip()}


def _routed_queue(task_name: str) -> str:
    """Celery'nin kendi router'ına sor: bu görev hangi kuyruğa gider?"""
    queue = celery_app.amqp.router.route({}, task_name).get("queue")
    return getattr(queue, "name", queue)


def test_worker_queue_list_is_readable_from_compose():
    """Sözleşmenin bir ucu okunabilir olmalı — yoksa diğer testler sessizce anlamsızlaşır."""
    queues = _worker_queues()
    assert queues, "worker hiçbir kuyruk dinlemiyor görünüyor"


@pytest.mark.parametrize("task_name", sorted(celery_app.conf.beat_schedule or {}))
def test_scheduled_task_lands_in_a_queue_the_worker_consumes(task_name):
    """Beat'in gönderdiği HER görev, worker'ın dinlediği bir kuyruğa düşmeli.

    Bu testin yakaladığı arıza sınıfı: görev zamanlanır, beat gönderir, hiçbir worker
    tüketmez. Log'da hata YOKTUR — mesaj sadece kimsenin bakmadığı kuyrukta birikir.
    """
    entry = celery_app.conf.beat_schedule[task_name]
    target = _routed_queue(entry["task"])
    consumed = _worker_queues()
    assert target in consumed, (
        f"'{task_name}' ({entry['task']}) -> '{target}' kuyruğuna yönlendiriliyor "
        f"ama worker sadece {sorted(consumed)} dinliyor. Görev hiç koşmaz."
    )


def _registered_tasks() -> set[str]:
    """Worker önyüklemesini taklit et ve kayıt defterini döndür.

    Worker açılışta `app.loader.import_default_modules()` çağırır; `include` ve
    `imports` altındaki modüller ancak o an import edilir. Bu yüzden sıradan bir
    Python sürecinde `celery_app.tasks` worker'ın defterini YANSITMAZ — ölçüm
    aleti olarak kullanılırsa bu gece başarıyla koşmuş görevleri bile "kayıtsız"
    gösterir (31 Tem'de tam olarak bu yanlış ölçüm alındı).

    Canlı worker'a `inspect registered` ile sorulan sonuçla birebir aynı kümeyi
    üretir; ikisi 31 Tem 2026'da karşılaştırılarak doğrulandı.
    """
    celery_app.loader.import_default_modules()
    return set(celery_app.tasks)


def test_worker_bootstrap_actually_imports_task_modules():
    """Sözleşmenin bu ucu da okunabilir olmalı — yoksa aşağıdaki test anlamsızlaşır.

    `import_default_modules()` sessizce hiçbir şey yapmazsa aşağıdaki parametrik
    test topluca kırmızıya döner ve gerçek eksiği gizler. Bu çapa, "alet çalışıyor"
    ile "bir görev eksik" durumlarını ayırır.
    """
    registered = _registered_tasks()
    assert "tasks.bulk_tasks.cleanup_expired_cache_entries" in registered, (
        "Worker önyüklemesi taklit edilemedi: `include` listesindeki bilinen bir "
        f"görev bile kayıt defterinde yok (defterde {len(registered)} görev var)."
    )


@pytest.mark.parametrize("task_name", sorted(celery_app.conf.beat_schedule or {}))
def test_scheduled_task_is_registered_in_the_worker(task_name):
    """Beat'in gönderdiği HER görev worker'ın kayıt defterinde olmalı.

    Bu testin yakaladığı arıza sınıfı: görev doğru kuyruğa düşer, worker mesajı
    alır, ama adı defterde olmadığı için `unregistered task` diye reddeder. Beat
    "Sending due task" loglar — zamanlama sağlıklı görünür, iş asla yapılmaz.

    Yeni bir görev modülü yazmak yetmez; `core/celery_app.py` içindeki `include`
    listesine eklenmesi gerekir. Bu insan kontrolü bu depoda başarısız oldu.
    """
    entry = celery_app.conf.beat_schedule[task_name]
    registered = _registered_tasks()
    assert entry["task"] in registered, (
        f"'{task_name}' -> '{entry['task']}' zamanlanmış ama worker'ın kayıt "
        f"defterinde yok. `core/celery_app.py` içindeki `include` listesine görevin "
        f"modülü eklenmemiş olabilir. Beat gönderir, worker reddeder, iş koşmaz."
    )


def test_task_without_an_explicit_route_still_reaches_the_worker():
    """Rotası OLMAYAN yeni bir görev de worker'a ulaşmalı.

    Her yeni görev modülü için `task_routes`'a satır eklemeyi hatırlamak bir insan
    kontrolüdür ve bu depoda dört kez başarısız oldu. Varsayılan kuyruk tüketilen bir
    kuyruk olursa unutmak zararsız hale gelir.
    """
    target = _routed_queue("tasks.henuz_olmayan_bir_modul.yeni_gorev")
    consumed = _worker_queues()
    assert target in consumed, (
        f"Rotası olmayan görev '{target}' kuyruğuna düşüyor ama worker "
        f"{sorted(consumed)} dinliyor. task_default_queue tüketilen bir kuyruk olmalı."
    )
