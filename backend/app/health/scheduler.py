"""
Health Check Scheduler

Bu modul, periyodik health check işlemlerini zamanlayan
APScheduler konfigürasyonunu içerir.

Scheduled Jobs:
- Health Check: Her 30 saniye
- Dependency Check: Her 60 saniye
- SLA Monitoring: Her 5 dakika
- Alert Cleanup: Her saat
- Report Generation: Günlük

Requirements:
    REQ-2.1: Periyodik health check scheduling
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class HealthCheckScheduler:
    """
    Health check işlemlerini zamanlayan scheduler.

    Bu sınıf, APScheduler kullanarak periyodik health check,
    dependency check ve SLA monitoring işlemlerini zamanlar.

    Attributes:
        scheduler: APScheduler instance
        is_running: Scheduler çalışıyor mu
    """

    def __init__(self):
        """HealthCheckScheduler sınıfını başlatır."""
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": True,  # Biriken işleri tek seferde çalıştır
                "max_instances": 1,  # Aynı anda sadece bir instance
                "misfire_grace_time": 60  # Kaçırılan işler için tolerans
            }
        )

        self.is_running = False

        # Job callbacks
        self._health_check_callback: Callable | None = None
        self._dependency_check_callback: Callable | None = None
        self._sla_check_callback: Callable | None = None

        # Event listeners
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )

        logger.info("HealthCheckScheduler başlatıldı")

    def start(self) -> None:
        """
        Scheduler'ı başlatır.

        Requirements:
            REQ-2.1: Health check scheduling başlatma
        """
        if self.is_running:
            logger.warning("Scheduler zaten çalışıyor")
            return

        self.scheduler.start()
        self.is_running = True
        logger.info("Health check scheduler başlatıldı")

    def stop(self, wait: bool = True) -> None:
        """
        Scheduler'ı durdurur.

        Args:
            wait: Çalışan işlerin bitmesini bekle
        """
        if not self.is_running:
            return

        logger.info("Health check scheduler durduruluyor...")
        self.scheduler.shutdown(wait=wait)
        self.is_running = False
        logger.info("Health check scheduler durduruldu")

    def schedule_health_check(
        self,
        callback: Callable,
        interval_seconds: int = 30
    ) -> str:
        """
        Periyodik health check zamanlar.

        Args:
            callback: Health check fonksiyonu
            interval_seconds: Kontrol aralığı (saniye)

        Returns:
            Job ID

        Requirements:
            REQ-2.1: Her 30 saniyede health check
        """
        self._health_check_callback = callback

        job = self.scheduler.add_job(
            self._run_health_check,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="health_check",
            name="Endpoint Health Check",
            replace_existing=True
        )

        logger.info(f"Health check zamanlandı: her {interval_seconds} saniye")
        return job.id

    def schedule_dependency_check(
        self,
        callback: Callable,
        interval_seconds: int = 60
    ) -> str:
        """
        Periyodik dependency health check zamanlar.

        Args:
            callback: Dependency check fonksiyonu
            interval_seconds: Kontrol aralığı (saniye)

        Returns:
            Job ID
        """
        self._dependency_check_callback = callback

        job = self.scheduler.add_job(
            self._run_dependency_check,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="dependency_check",
            name="Dependency Health Check",
            replace_existing=True
        )

        logger.info(f"Dependency check zamanlandı: her {interval_seconds} saniye")
        return job.id

    def schedule_sla_monitoring(
        self,
        callback: Callable,
        interval_minutes: int = 5
    ) -> str:
        """
        Periyodik SLA monitoring zamanlar.

        Args:
            callback: SLA monitoring fonksiyonu
            interval_minutes: Kontrol aralığı (dakika)

        Returns:
            Job ID
        """
        self._sla_check_callback = callback

        job = self.scheduler.add_job(
            self._run_sla_monitoring,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="sla_monitoring",
            name="SLA Monitoring",
            replace_existing=True
        )

        logger.info(f"SLA monitoring zamanlandı: her {interval_minutes} dakika")
        return job.id

    def schedule_daily_report(
        self,
        callback: Callable,
        hour: int = 6,
        minute: int = 0
    ) -> str:
        """
        Günlük rapor oluşturma zamanlar.

        Args:
            callback: Report generation fonksiyonu
            hour: Çalışma saati (0-23)
            minute: Çalışma dakikası (0-59)

        Returns:
            Job ID
        """
        job = self.scheduler.add_job(
            callback,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_report",
            name="Daily Health Report",
            replace_existing=True
        )

        logger.info(f"Günlük rapor zamanlandı: {hour:02d}:{minute:02d}")
        return job.id

    def schedule_alert_cleanup(
        self,
        callback: Callable,
        interval_hours: int = 1
    ) -> str:
        """
        Periyodik alert temizleme zamanlar.

        Args:
            callback: Alert cleanup fonksiyonu
            interval_hours: Temizleme aralığı (saat)

        Returns:
            Job ID
        """
        job = self.scheduler.add_job(
            callback,
            trigger=IntervalTrigger(hours=interval_hours),
            id="alert_cleanup",
            name="Alert Cleanup",
            replace_existing=True
        )

        logger.info(f"Alert cleanup zamanlandı: her {interval_hours} saat")
        return job.id

    async def _run_health_check(self) -> None:
        """Health check job'ını çalıştırır."""
        if not self._health_check_callback:
            logger.warning("Health check callback tanımlanmamış")
            return

        try:
            logger.debug("Health check başlıyor...")

            if asyncio.iscoroutinefunction(self._health_check_callback):
                await self._health_check_callback()
            else:
                self._health_check_callback()

            logger.debug("Health check tamamlandı")

        except Exception as e:
            logger.error(f"Health check hatası: {e}")
            raise

    async def _run_dependency_check(self) -> None:
        """Dependency check job'ını çalıştırır."""
        if not self._dependency_check_callback:
            logger.warning("Dependency check callback tanımlanmamış")
            return

        try:
            logger.debug("Dependency check başlıyor...")

            if asyncio.iscoroutinefunction(self._dependency_check_callback):
                await self._dependency_check_callback()
            else:
                self._dependency_check_callback()

            logger.debug("Dependency check tamamlandı")

        except Exception as e:
            logger.error(f"Dependency check hatası: {e}")
            raise

    async def _run_sla_monitoring(self) -> None:
        """SLA monitoring job'ını çalıştırır."""
        if not self._sla_check_callback:
            logger.warning("SLA check callback tanımlanmamış")
            return

        try:
            logger.debug("SLA monitoring başlıyor...")

            if asyncio.iscoroutinefunction(self._sla_check_callback):
                await self._sla_check_callback()
            else:
                self._sla_check_callback()

            logger.debug("SLA monitoring tamamlandı")

        except Exception as e:
            logger.error(f"SLA monitoring hatası: {e}")
            raise

    def _on_job_executed(self, event) -> None:
        """Job tamamlandığında çağrılır."""
        logger.debug(f"Job tamamlandı: {event.job_id}")

    def _on_job_error(self, event) -> None:
        """Job hata verdiğinde çağrılır."""
        logger.error(
            f"Job hatası: {event.job_id} - {event.exception}"
        )

    def get_jobs(self) -> list[dict]:
        """Tüm zamanlanmış job'ları listeler."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs

    def pause_job(self, job_id: str) -> bool:
        """Job'ı duraklatır."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job duraklatıldı: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Job durdurulamadı: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Duraklatılmış job'ı devam ettirir."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job devam ettirildi: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Job devam ettirilemedi: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """Job'ı kaldırır."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job kaldırıldı: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Job kaldırılamadı: {e}")
            return False

    def trigger_job_now(self, job_id: str) -> bool:
        """Job'ı hemen çalıştırır."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now(UTC))
                logger.info(f"Job tetiklendi: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Job tetiklenemedi: {e}")
            return False


# Singleton instance
_scheduler_instance: HealthCheckScheduler | None = None


def get_scheduler() -> HealthCheckScheduler:
    """Scheduler singleton instance'ını getirir."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = HealthCheckScheduler()
    return _scheduler_instance


async def setup_default_schedule(
    health_check_callback: Callable,
    dependency_check_callback: Callable,
    sla_check_callback: Callable
) -> HealthCheckScheduler:
    """
    Varsayılan schedule'ı ayarlar ve başlatır.

    Args:
        health_check_callback: Health check fonksiyonu
        dependency_check_callback: Dependency check fonksiyonu
        sla_check_callback: SLA check fonksiyonu

    Returns:
        Konfigüre edilmiş scheduler instance
    """
    scheduler = get_scheduler()

    # Job'ları zamanla
    scheduler.schedule_health_check(health_check_callback, interval_seconds=30)
    scheduler.schedule_dependency_check(dependency_check_callback, interval_seconds=60)
    scheduler.schedule_sla_monitoring(sla_check_callback, interval_minutes=5)

    # Scheduler'ı başlat
    scheduler.start()

    logger.info("Varsayılan health check schedule ayarlandı")
    return scheduler


async def graceful_shutdown() -> None:
    """Graceful shutdown işlemi."""
    scheduler = get_scheduler()
    if scheduler.is_running:
        logger.info("Scheduler graceful shutdown başlıyor...")
        scheduler.stop(wait=True)
        logger.info("Scheduler graceful shutdown tamamlandı")
