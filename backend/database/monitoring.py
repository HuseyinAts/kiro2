"""
Database Monitoring and Alerting System
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu

Veritabanı sağlık durumu, performans metrikleri ve alerting sistemi

Requirements: 7.1, 7.2, 7.3
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert önem seviyeleri"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DatabaseAlert:
    """Veritabanı alert modeli"""

    def __init__(
        self,
        severity: AlertSeverity,
        message: str,
        metric_name: str,
        current_value: Any,
        threshold_value: Any,
        timestamp: Optional[datetime] = None,
    ):
        self.severity = severity
        self.message = message
        self.metric_name = metric_name
        self.current_value = current_value
        self.threshold_value = threshold_value
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Alert'i dictionary'e çevir"""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.message} "
            f"(current: {self.current_value}, threshold: {self.threshold_value})"
        )


class DatabaseMonitor:
    """
    Veritabanı monitoring ve alerting sistemi

    Özellikler:
    - Connection pool monitoring
    - Query performance tracking
    - Disk space monitoring
    - Replication lag monitoring
    - Automatic alerting
    """

    def __init__(
        self,
        engine: AsyncEngine,
        alert_callback: Optional[Callable[[DatabaseAlert], None]] = None,
    ):
        self.engine = engine
        self.alert_callback = alert_callback or self._default_alert_handler
        self.alerts: List[DatabaseAlert] = []
        self.metrics_history: List[Dict[str, Any]] = []

        # Alert thresholds
        self.thresholds = {
            "pool_usage_percentage": 80,  # Pool kullanımı %80'i geçerse alert
            "slow_query_percentage": 10,  # Yavaş sorgu oranı %10'u geçerse
            "connection_wait_time_ms": 1000,  # Connection bekleme 1 saniyeyi geçerse
            "disk_usage_percentage": 85,  # Disk kullanımı %85'i geçerse
            "replication_lag_seconds": 10,  # Replication lag 10 saniyeyi geçerse
            "active_connections": 150,  # Aktif connection sayısı 150'yi geçerse
        }

    def _default_alert_handler(self, alert: DatabaseAlert):
        """Varsayılan alert handler - loglama"""
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            logger.error(str(alert))
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(str(alert))
        else:
            logger.info(str(alert))

    def _create_alert(
        self,
        severity: AlertSeverity,
        message: str,
        metric_name: str,
        current_value: Any,
        threshold_value: Any,
    ):
        """Alert oluştur ve callback'i çağır"""
        alert = DatabaseAlert(
            severity=severity,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
        )

        self.alerts.append(alert)
        self.alert_callback(alert)

        return alert

    async def check_pool_health(self) -> Dict[str, Any]:
        """
        Connection pool sağlığını kontrol et

        Returns:
            Pool sağlık durumu ve metrikler
        """
        try:
            pool = self.engine.pool

            pool_size = pool.size()
            checked_out = pool.checkedout()
            overflow = pool.overflow()

            # Pool kullanım yüzdesi
            total_capacity = pool_size + (
                pool._max_overflow if hasattr(pool, "_max_overflow") else 0
            )
            usage_percentage = (
                (checked_out / total_capacity * 100) if total_capacity > 0 else 0
            )

            metrics = {
                "pool_size": pool_size,
                "checked_out": checked_out,
                "overflow": overflow,
                "available": pool_size - checked_out,
                "usage_percentage": usage_percentage,
                "healthy": usage_percentage < self.thresholds["pool_usage_percentage"],
                "timestamp": datetime.now().isoformat(),
            }

            # Alert kontrolü
            if usage_percentage >= self.thresholds["pool_usage_percentage"]:
                self._create_alert(
                    severity=AlertSeverity.WARNING,
                    message=f"Connection pool kullanımı yüksek: %{usage_percentage:.1f}",
                    metric_name="pool_usage_percentage",
                    current_value=usage_percentage,
                    threshold_value=self.thresholds["pool_usage_percentage"],
                )

            return metrics

        except Exception as e:
            logger.error(f"Pool health check başarısız: {e}")
            return {"error": str(e), "healthy": False}

    async def check_connection_health(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Veritabanı bağlantı sağlığını kontrol et

        Args:
            session: Database session

        Returns:
            Bağlantı sağlık durumu
        """
        try:
            # Basit query ile bağlantı testi
            start_time = datetime.now()
            await session.execute(text("SELECT 1"))
            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Aktif connection sayısı (PostgreSQL)
            result = await session.execute(
                text(
                    """
            SELECT count(*) FROM pg_stat_activity
            WHERE state = 'active'
            """
                )
            )
            active_connections = result.scalar()

            metrics = {
                "response_time_ms": response_time_ms,
                "active_connections": active_connections,
                "healthy": response_time_ms < 100
                and active_connections < self.thresholds["active_connections"],
                "timestamp": datetime.now().isoformat(),
            }

            # Alert kontrolü
            if active_connections >= self.thresholds["active_connections"]:
                self._create_alert(
                    severity=AlertSeverity.WARNING,
                    message=f"Aktif connection sayısı yüksek: {active_connections}",
                    metric_name="active_connections",
                    current_value=active_connections,
                    threshold_value=self.thresholds["active_connections"],
                )

            return metrics

        except Exception as e:
            logger.error(f"Connection health check başarısız: {e}")
            return {"error": str(e), "healthy": False}

    async def check_disk_usage(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Veritabanı disk kullanımını kontrol et (PostgreSQL)

        Args:
            session: Database session

        Returns:
            Disk kullanım metrikleri
        """
        try:
            # Database boyutu
            result = await session.execute(
                text(
                    """
            SELECT pg_database_size(current_database())
            """
                )
            )
            db_size_bytes = result.scalar()
            db_size_mb = db_size_bytes / (1024 * 1024)
            db_size_gb = db_size_mb / 1024

            # Tablespace kullanımı (varsa)
            try:
                result = await session.execute(
                    text(
                        """
                SELECT
                    spcname,
                    pg_size_pretty(pg_tablespace_size(spcname)) as size
                FROM pg_tablespace
                """
                    )
                )
                tablespaces = [
                    {"name": row[0], "size": row[1]} for row in result.fetchall()
                ]
            except:
                tablespaces = []

            metrics = {
                "database_size_mb": db_size_mb,
                "database_size_gb": db_size_gb,
                "tablespaces": tablespaces,
                "timestamp": datetime.now().isoformat(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Disk usage check başarısız: {e}")
            return {"error": str(e)}

    async def check_replication_status(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Replication durumunu kontrol et (PostgreSQL)

        Args:
            session: Database session

        Returns:
            Replication durumu ve lag metrikleri
        """
        try:
            # Replication slots
            result = await session.execute(
                text(
                    """
            SELECT
                slot_name,
                slot_type,
                active,
                pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes
            FROM pg_replication_slots
            """
                )
            )

            replication_slots = []
            max_lag_bytes = 0

            for row in result.fetchall():
                lag_bytes = row[3] if row[3] else 0
                max_lag_bytes = max(max_lag_bytes, lag_bytes)

                replication_slots.append(
                    {
                        "slot_name": row[0],
                        "slot_type": row[1],
                        "active": row[2],
                        "lag_bytes": lag_bytes,
                        "lag_mb": lag_bytes / (1024 * 1024) if lag_bytes else 0,
                    }
                )

            # Standby sunucular
            result = await session.execute(
                text(
                    """
            SELECT
                client_addr,
                state,
                sync_state,
                pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) as send_lag,
                pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn) as write_lag,
                pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn) as flush_lag,
                pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) as replay_lag
            FROM pg_stat_replication
            """
                )
            )

            standby_servers = []
            for row in result.fetchall():
                standby_servers.append(
                    {
                        "client_addr": str(row[0]) if row[0] else None,
                        "state": row[1],
                        "sync_state": row[2],
                        "send_lag_bytes": row[3] if row[3] else 0,
                        "write_lag_bytes": row[4] if row[4] else 0,
                        "flush_lag_bytes": row[5] if row[5] else 0,
                        "replay_lag_bytes": row[6] if row[6] else 0,
                    }
                )

            metrics = {
                "replication_enabled": len(replication_slots) > 0
                or len(standby_servers) > 0,
                "replication_slots": replication_slots,
                "standby_servers": standby_servers,
                "max_lag_mb": max_lag_bytes / (1024 * 1024) if max_lag_bytes else 0,
                "healthy": max_lag_bytes < (10 * 1024 * 1024),  # 10MB threshold
                "timestamp": datetime.now().isoformat(),
            }

            return metrics

        except Exception as e:
            # Replication olmayabilir, bu normal
            logger.debug(f"Replication check: {e}")
            return {
                "replication_enabled": False,
                "message": "Replication yapılandırılmamış veya erişilemiyor",
            }

    async def check_query_performance(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Query performans istatistiklerini kontrol et (PostgreSQL)

        Args:
            session: Database session

        Returns:
            Query performans metrikleri
        """
        try:
            # En yavaş sorgular (pg_stat_statements extension gerekli)
            result = await session.execute(
                text(
                    """
            SELECT
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                max_exec_time
            FROM pg_stat_statements
            ORDER BY mean_exec_time DESC
            LIMIT 10
            """
                )
            )

            slow_queries = []
            for row in result.fetchall():
                slow_queries.append(
                    {
                        "query": row[0][:200],  # İlk 200 karakter
                        "calls": row[1],
                        "total_time_ms": row[2],
                        "mean_time_ms": row[3],
                        "max_time_ms": row[4],
                    }
                )

            # Yavaş sorgu oranı hesapla
            if slow_queries:
                slow_query_count = sum(
                    1 for q in slow_queries if q["mean_time_ms"] > 200
                )
                slow_query_percentage = (slow_query_count / len(slow_queries)) * 100
            else:
                slow_query_percentage = 0

            metrics = {
                "slow_queries": slow_queries,
                "slow_query_percentage": slow_query_percentage,
                "healthy": slow_query_percentage
                < self.thresholds["slow_query_percentage"],
                "timestamp": datetime.now().isoformat(),
            }

            # Alert kontrolü
            if slow_query_percentage >= self.thresholds["slow_query_percentage"]:
                self._create_alert(
                    severity=AlertSeverity.WARNING,
                    message=f"Yavaş sorgu oranı yüksek: %{slow_query_percentage:.1f}",
                    metric_name="slow_query_percentage",
                    current_value=slow_query_percentage,
                    threshold_value=self.thresholds["slow_query_percentage"],
                )

            return metrics

        except Exception as e:
            # pg_stat_statements extension olmayabilir
            logger.debug(f"Query performance check: {e}")
            return {
                "message": "pg_stat_statements extension gerekli",
                "slow_queries": [],
            }

    async def comprehensive_health_check(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Kapsamlı sağlık kontrolü - tüm metrikleri topla

        Args:
            session: Database session

        Returns:
            Tüm sağlık metrikleri
        """
        logger.info("Kapsamlı veritabanı sağlık kontrolü başlatılıyor...")

        # Tüm kontrolleri paralel çalıştır
        pool_health = await self.check_pool_health()
        connection_health = await self.check_connection_health(session)
        disk_usage = await self.check_disk_usage(session)
        replication_status = await self.check_replication_status(session)
        query_performance = await self.check_query_performance(session)

        # Genel sağlık durumu
        overall_healthy = all(
            [
                pool_health.get("healthy", False),
                connection_health.get("healthy", False),
                query_performance.get("healthy", True),  # Optional
            ]
        )

        metrics = {
            "overall_healthy": overall_healthy,
            "pool_health": pool_health,
            "connection_health": connection_health,
            "disk_usage": disk_usage,
            "replication_status": replication_status,
            "query_performance": query_performance,
            "recent_alerts": [alert.to_dict() for alert in self.alerts[-10:]],
            "timestamp": datetime.now().isoformat(),
        }

        # Metrikleri history'e ekle
        self.metrics_history.append(metrics)

        # Son 100 metriği tut (memory management)
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

        logger.info(
            f"Sağlık kontrolü tamamlandı: {'✓ Sağlıklı' if overall_healthy else '✗ Sorun var'}"
        )

        return metrics

    async def start_monitoring(self, session: AsyncSession, interval_seconds: int = 60):
        """
        Sürekli monitoring başlat

        Args:
            session: Database session
            interval_seconds: Kontrol aralığı (saniye)
        """
        logger.info(f"Veritabanı monitoring başlatıldı (interval: {interval_seconds}s)")

        while True:
            try:
                await self.comprehensive_health_check(session)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Monitoring hatası: {e}")
                await asyncio.sleep(interval_seconds)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Toplanan metriklerin özetini getir

        Returns:
            Metrik özeti
        """
        if not self.metrics_history:
            return {"message": "Henüz metrik toplanmadı"}

        recent_metrics = self.metrics_history[-10:]

        return {
            "total_checks": len(self.metrics_history),
            "recent_checks": len(recent_metrics),
            "total_alerts": len(self.alerts),
            "critical_alerts": len(
                [a for a in self.alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "error_alerts": len(
                [a for a in self.alerts if a.severity == AlertSeverity.ERROR]
            ),
            "warning_alerts": len(
                [a for a in self.alerts if a.severity == AlertSeverity.WARNING]
            ),
            "latest_check": recent_metrics[-1] if recent_metrics else None,
        }


# Global monitor instance
_monitor: Optional[DatabaseMonitor] = None


def get_database_monitor(
    engine: AsyncEngine,
    alert_callback: Optional[Callable[[DatabaseAlert], None]] = None,
) -> DatabaseMonitor:
    """Global database monitor instance'ı al"""
    global _monitor
    if _monitor is None:
        _monitor = DatabaseMonitor(engine, alert_callback)
    return _monitor
