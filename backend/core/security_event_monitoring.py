"""
KIRO2 Security Event Monitoring System
Advanced security event detection, monitoring, and alerting
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import hashlib
import ipaddress
import json
import re
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import redis

from core.enhanced_database import get_enhanced_db_manager
from core.structured_logging import get_security_logger
from core.unified_config import get_unified_config

config = get_unified_config()
logger = get_security_logger(__name__)


class SecurityEventType(Enum):
    """Security event types with Turkish descriptions"""

    # Authentication Events
    LOGIN_SUCCESS = ("login_success", "Başarılı Giriş")
    LOGIN_FAILURE = ("login_failure", "Başarısız Giriş")
    LOGOUT = ("logout", "Çıkış")
    PASSWORD_CHANGE = ("password_change", "Şifre Değişikliği")
    ACCOUNT_LOCKED = ("account_locked", "Hesap Kilitlendi")
    ACCOUNT_UNLOCKED = ("account_unlocked", "Hesap Kilidi Açıldı")

    # Authorization Events
    UNAUTHORIZED_ACCESS = ("unauthorized_access", "Yetkisiz Erişim")
    PRIVILEGE_ESCALATION = ("privilege_escalation", "Yetki Yükseltme")
    PERMISSION_DENIED = ("permission_denied", "İzin Reddedildi")
    ROLE_CHANGED = ("role_changed", "Rol Değişikliği")

    # Attack Patterns
    BRUTE_FORCE_ATTACK = ("brute_force_attack", "Kaba Kuvvet Saldırısı")
    SQL_INJECTION_ATTEMPT = ("sql_injection_attempt", "SQL Enjeksiyon Girişimi")
    XSS_ATTEMPT = ("xss_attempt", "XSS Saldırı Girişimi")
    CSRF_ATTEMPT = ("csrf_attempt", "CSRF Saldırı Girişimi")
    PATH_TRAVERSAL_ATTEMPT = ("path_traversal_attempt", "Dizin Geçiş Saldırısı")
    COMMAND_INJECTION_ATTEMPT = (
        "command_injection_attempt",
        "Komut Enjeksiyon Girişimi",
    )

    # System Events
    RATE_LIMIT_EXCEEDED = ("rate_limit_exceeded", "Hız Sınırı Aşıldı")
    SUSPICIOUS_USER_AGENT = ("suspicious_user_agent", "Şüpheli User Agent")
    SUSPICIOUS_IP = ("suspicious_ip", "Şüpheli IP Adresi")
    GEO_ANOMALY = ("geo_anomaly", "Coğrafi Anomali")
    TIME_ANOMALY = ("time_anomaly", "Zaman Anomalisi")
    DEVICE_ANOMALY = ("device_anomaly", "Cihaz Anomalisi")

    # Data Events
    SENSITIVE_DATA_ACCESS = ("sensitive_data_access", "Hassas Veri Erişimi")
    DATA_EXPORT = ("data_export", "Veri Dışa Aktarma")
    DATA_MODIFICATION = ("data_modification", "Veri Değişikliği")
    DATA_DELETION = ("data_deletion", "Veri Silme")

    # System Security
    CONFIG_CHANGE = ("config_change", "Yapılandırma Değişikliği")
    SECURITY_BYPASS = ("security_bypass", "Güvenlik Atlama")
    MALWARE_DETECTED = ("malware_detected", "Kötü Amaçlı Yazılım Tespit")
    FIREWALL_VIOLATION = ("firewall_violation", "Güvenlik Duvarı İhlali")

    def __init__(self, event_type: str, turkish_description: str):
        self.event_type = event_type
        self.turkish_description = turkish_description


class SecuritySeverity(Enum):
    """Security severity levels with scoring"""

    INFO = ("info", "Bilgi", 1)
    LOW = ("low", "Düşük", 25)
    MEDIUM = ("medium", "Orta", 50)
    HIGH = ("high", "Yüksek", 75)
    CRITICAL = ("critical", "Kritik", 100)

    def __init__(self, level: str, turkish_description: str, score: int):
        self.level = level
        self.turkish_description = turkish_description
        self.score = score


@dataclass
class SecurityEvent:
    """Security event data structure"""

    event_id: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: datetime
    user_id: int | None = None
    session_id: str | None = None
    ip_address: str = ""
    user_agent: str = ""
    endpoint: str = ""
    method: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    response_status: int | None = None
    message: str = ""
    message_tr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    location_info: dict[str, Any] = field(default_factory=dict)
    device_info: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    parent_event_id: str | None = None
    tags: list[str] = field(default_factory=list)
    remediation_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.event_type,
            "event_type_tr": self.event_type.turkish_description,
            "severity": self.severity.level,
            "severity_tr": self.severity.turkish_description,
            "severity_score": self.severity.score,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "method": self.method,
            "payload": self.payload,
            "headers": self.headers,
            "response_status": self.response_status,
            "message": self.message,
            "message_tr": self.message_tr,
            "metadata": self.metadata,
            "location_info": self.location_info,
            "device_info": self.device_info,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
            "tags": self.tags,
            "remediation_actions": self.remediation_actions,
        }


class ThreatDetector:
    """Advanced threat detection algorithms"""

    def __init__(self):
        self.ip_reputation_cache: dict[str, dict[str, Any]] = {}
        self.user_behavior_cache: dict[int, dict[str, Any]] = {}
        self.attack_patterns = self._load_attack_patterns()
        self.geo_anomaly_threshold = 1000  # km
        self.time_anomaly_threshold = 6  # hours

    def _load_attack_patterns(self) -> dict[str, list[str]]:
        """Load attack pattern signatures"""
        return {
            "sql_injection": [
                r"('|\").*?('|\")|union\s+select|insert\s+into|delete\s+from|drop\s+table",
                r"or\s+1\s*=\s*1|and\s+1\s*=\s*1|''\s*or\s*''='|admin'\s*--",
                r"exec\s*\(|execute\s*\(|sp_executesql|xp_cmdshell",
            ],
            "xss": [
                r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=",
                r"<iframe[^>]*>|<object[^>]*>|<embed[^>]*>",
                r"document\.(cookie|location|write)|window\.(location|open)",
                r"eval\s*\(|setTimeout\s*\(|setInterval\s*\(",
            ],
            "path_traversal": [
                r"\.\./|\.\.\\\|%2e%2e%2f|%2e%2e%5c",
                r"\.\.%2f|\.\.%5c|/etc/passwd|/windows/system32",
            ],
            "command_injection": [
                r"[;&|`]|(\|\||&&)|system\s*\(|exec\s*\(",
                r"\$\([^)]+\)|`[^`]+`|\\x[0-9a-fA-F]{2}",
            ],
            "ldap_injection": [
                r"\(\|\(\w+=\*\)\)|&\(\w+=.*\)\)\(\w+=.*\)",
                r"\(\w+=.*\*\)|admin\)\(\|",
            ],
        }

    async def detect_threats(self, request_data: dict[str, Any]) -> list[SecurityEvent]:
        """Detect security threats in request data"""
        threats = []

        # Extract request information
        ip_address = request_data.get("ip_address", "")
        user_agent = request_data.get("user_agent", "")
        payload = request_data.get("payload", {})
        headers = request_data.get("headers", {})
        endpoint = request_data.get("endpoint", "")
        method = request_data.get("method", "")
        user_id = request_data.get("user_id")

        # Check for attack patterns in payload
        if payload:
            threats.extend(
                await self._detect_injection_attacks(payload, ip_address, user_id)
            )

        # Check for suspicious user agent
        if await self._is_suspicious_user_agent(user_agent):
            threats.append(
                await self._create_threat_event(
                    SecurityEventType.SUSPICIOUS_USER_AGENT,
                    SecuritySeverity.LOW,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    message=f"Suspicious user agent detected: {user_agent}",
                    message_tr=f"Şüpheli user agent tespit edildi: {user_agent}",
                )
            )

        # Check for rate limiting violations
        if await self._check_rate_limit_violation(ip_address, user_id):
            threats.append(
                await self._create_threat_event(
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                    SecuritySeverity.MEDIUM,
                    ip_address=ip_address,
                    user_id=user_id,
                    message=f"Rate limit exceeded for IP: {ip_address}",
                    message_tr=f"IP için hız sınırı aşıldı: {ip_address}",
                )
            )

        # Check for brute force attacks
        if await self._detect_brute_force(ip_address, user_id):
            threats.append(
                await self._create_threat_event(
                    SecurityEventType.BRUTE_FORCE_ATTACK,
                    SecuritySeverity.HIGH,
                    ip_address=ip_address,
                    user_id=user_id,
                    message=f"Brute force attack detected from IP: {ip_address}",
                    message_tr=f"IP'den kaba kuvvet saldırısı tespit edildi: {ip_address}",
                )
            )

        # Check for geographic anomalies
        if user_id:
            geo_threat = await self._detect_geographic_anomaly(user_id, ip_address)
            if geo_threat:
                threats.append(geo_threat)

        # Check for time-based anomalies
        if user_id:
            time_threat = await self._detect_time_anomaly(user_id)
            if time_threat:
                threats.append(time_threat)

        return threats

    async def _detect_injection_attacks(
        self, payload: dict[str, Any], ip_address: str, user_id: int | None
    ) -> list[SecurityEvent]:
        """Detect injection attacks in payload"""
        threats = []

        # Convert payload to string for pattern matching
        payload_str = json.dumps(payload, default=str).lower()

        # Check SQL injection patterns
        for pattern in self.attack_patterns["sql_injection"]:
            if re.search(pattern, payload_str, re.IGNORECASE):
                threats.append(
                    await self._create_threat_event(
                        SecurityEventType.SQL_INJECTION_ATTEMPT,
                        SecuritySeverity.HIGH,
                        ip_address=ip_address,
                        user_id=user_id,
                        message=f"SQL injection attempt detected: {pattern}",
                        message_tr=f"SQL enjeksiyon girişimi tespit edildi: {pattern}",
                        metadata={
                            "pattern": pattern,
                            "payload_sample": payload_str[:500],
                        },
                    )
                )

        # Check XSS patterns
        for pattern in self.attack_patterns["xss"]:
            if re.search(pattern, payload_str, re.IGNORECASE):
                threats.append(
                    await self._create_threat_event(
                        SecurityEventType.XSS_ATTEMPT,
                        SecuritySeverity.HIGH,
                        ip_address=ip_address,
                        user_id=user_id,
                        message=f"XSS attempt detected: {pattern}",
                        message_tr=f"XSS girişimi tespit edildi: {pattern}",
                        metadata={
                            "pattern": pattern,
                            "payload_sample": payload_str[:500],
                        },
                    )
                )

        # Check command injection patterns
        for pattern in self.attack_patterns["command_injection"]:
            if re.search(pattern, payload_str, re.IGNORECASE):
                threats.append(
                    await self._create_threat_event(
                        SecurityEventType.COMMAND_INJECTION_ATTEMPT,
                        SecuritySeverity.CRITICAL,
                        ip_address=ip_address,
                        user_id=user_id,
                        message=f"Command injection attempt detected: {pattern}",
                        message_tr=f"Komut enjeksiyon girişimi tespit edildi: {pattern}",
                        metadata={
                            "pattern": pattern,
                            "payload_sample": payload_str[:500],
                        },
                    )
                )

        # Check path traversal patterns
        for pattern in self.attack_patterns["path_traversal"]:
            if re.search(pattern, payload_str, re.IGNORECASE):
                threats.append(
                    await self._create_threat_event(
                        SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
                        SecuritySeverity.MEDIUM,
                        ip_address=ip_address,
                        user_id=user_id,
                        message=f"Path traversal attempt detected: {pattern}",
                        message_tr=f"Dizin geçiş girişimi tespit edildi: {pattern}",
                        metadata={
                            "pattern": pattern,
                            "payload_sample": payload_str[:500],
                        },
                    )
                )

        return threats

    async def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        if not user_agent or len(user_agent) < 10:
            return True

        suspicious_patterns = [
            r"bot|crawler|scraper|spider|scan",
            r"curl|wget|python|java|php",
            r"attack|hack|inject|exploit",
            r"^$|null|undefined|test",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True

        return False

    async def _check_rate_limit_violation(
        self, ip_address: str, user_id: int | None
    ) -> bool:
        """Check for rate limiting violations"""
        # This would typically check against Redis or database
        # For now, simulate with in-memory cache
        current_time = datetime.now()

        # Check IP-based rate limiting
        ip_key = f"rate_limit:ip:{ip_address}"
        # In production, this would use Redis

        # Check user-based rate limiting if user is authenticated
        if user_id:
            user_key = f"rate_limit:user:{user_id}"
            # In production, this would use Redis

        # Simplified check - in production, implement proper rate limiting
        return False

    async def _detect_brute_force(self, ip_address: str, user_id: int | None) -> bool:
        """Detect brute force attacks"""
        # Check for failed login attempts in short time window
        # This would query the database for recent failed attempts

        try:
            db_manager = get_enhanced_db_manager()

            # Check failed attempts in last 5 minutes
            query = """
                SELECT COUNT(*) as attempt_count
                FROM security_events 
                WHERE event_type = 'login_failure' 
                AND ip_address = %s 
                AND timestamp > NOW() - INTERVAL '5 minutes'
            """

            result = await db_manager.fetch_one(query, [ip_address])
            if result and result["attempt_count"] >= 5:
                return True

            # Check for user-specific attempts if user_id is available
            if user_id:
                user_query = """
                    SELECT COUNT(*) as attempt_count
                    FROM security_events 
                    WHERE event_type = 'login_failure' 
                    AND user_id = %s 
                    AND timestamp > NOW() - INTERVAL '10 minutes'
                """

                user_result = await db_manager.fetch_one(user_query, [user_id])
                if user_result and user_result["attempt_count"] >= 3:
                    return True

        except Exception as e:
            logger.error(f"Error checking brute force: {e}")

        return False

    async def _detect_geographic_anomaly(
        self, user_id: int, ip_address: str
    ) -> SecurityEvent | None:
        """Detect geographic location anomalies"""
        try:
            # Get user's historical locations
            db_manager = get_enhanced_db_manager()

            # Get recent locations for user
            query = """
                SELECT DISTINCT location_info
                FROM security_events 
                WHERE user_id = %s 
                AND location_info IS NOT NULL 
                AND timestamp > NOW() - INTERVAL '30 days'
                LIMIT 10
            """

            results = await db_manager.fetch_all(query, [user_id])

            if not results:
                return None  # No historical data

            # Get current location (would use IP geolocation service)
            current_location = await self._get_ip_location(ip_address)
            if not current_location:
                return None

            # Check if current location is significantly different
            for result in results:
                if result["location_info"]:
                    historical_location = json.loads(result["location_info"])
                    distance = self._calculate_distance(
                        current_location, historical_location
                    )

                    if distance < self.geo_anomaly_threshold:
                        return None  # Within normal range

            # All historical locations are far from current location
            return await self._create_threat_event(
                SecurityEventType.GEO_ANOMALY,
                SecuritySeverity.MEDIUM,
                user_id=user_id,
                ip_address=ip_address,
                message=f"Geographic anomaly detected for user {user_id}",
                message_tr=f"Kullanıcı {user_id} için coğrafi anomali tespit edildi",
                location_info=current_location,
            )

        except Exception as e:
            logger.error(f"Error detecting geographic anomaly: {e}")
            return None

    async def _detect_time_anomaly(self, user_id: int) -> SecurityEvent | None:
        """Detect unusual login times"""
        try:
            # Get user's typical login hours
            db_manager = get_enhanced_db_manager()

            query = """
                SELECT EXTRACT(HOUR FROM timestamp) as login_hour, COUNT(*) as frequency
                FROM security_events 
                WHERE user_id = %s 
                AND event_type = 'login_success'
                AND timestamp > NOW() - INTERVAL '30 days'
                GROUP BY EXTRACT(HOUR FROM timestamp)
                ORDER BY frequency DESC
            """

            results = await db_manager.fetch_all(query, [user_id])

            if len(results) < 5:  # Not enough data
                return None

            current_hour = datetime.now().hour

            # Check if current hour is in user's typical hours (top 50%)
            typical_hours = [int(r["login_hour"]) for r in results[: len(results) // 2]]

            if current_hour not in typical_hours:
                return await self._create_threat_event(
                    SecurityEventType.TIME_ANOMALY,
                    SecuritySeverity.LOW,
                    user_id=user_id,
                    message=f"Unusual login time detected for user {user_id} at hour {current_hour}",
                    message_tr=f"Kullanıcı {user_id} için saat {current_hour}'de alışılmadık giriş zamanı tespit edildi",
                    metadata={
                        "login_hour": current_hour,
                        "typical_hours": typical_hours,
                    },
                )

        except Exception as e:
            logger.error(f"Error detecting time anomaly: {e}")
            return None

    async def _get_ip_location(self, ip_address: str) -> dict[str, Any] | None:
        """Get IP address location information"""
        # In production, this would use a geolocation service like MaxMind
        # For now, return mock data
        try:
            if ipaddress.ip_address(ip_address).is_private:
                return None

            # Mock location data
            return {
                "country": "Turkey",
                "country_code": "TR",
                "city": "Istanbul",
                "latitude": 41.0082,
                "longitude": 28.9784,
                "timezone": "Europe/Istanbul",
            }
        except Exception:
            return None

    def _calculate_distance(self, loc1: dict[str, Any], loc2: dict[str, Any]) -> float:
        """Calculate distance between two geographic locations (simplified)"""
        try:
            lat1, lon1 = loc1.get("latitude", 0), loc1.get("longitude", 0)
            lat2, lon2 = loc2.get("latitude", 0), loc2.get("longitude", 0)

            # Simplified distance calculation (Haversine would be more accurate)
            lat_diff = abs(lat1 - lat2)
            lon_diff = abs(lon1 - lon2)

            # Rough conversion to kilometers
            return ((lat_diff**2 + lon_diff**2) ** 0.5) * 111
        except Exception:
            return 0

    async def _create_threat_event(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        ip_address: str = "",
        user_id: int | None = None,
        message: str = "",
        message_tr: str = "",
        metadata: dict[str, Any] = None,
        location_info: dict[str, Any] = None,
    ) -> SecurityEvent:
        """Create a security threat event"""
        return SecurityEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(UTC),
            ip_address=ip_address,
            user_id=user_id,
            message=message,
            message_tr=message_tr,
            metadata=metadata or {},
            location_info=location_info or {},
            correlation_id=self._generate_correlation_id(),
        )

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid

        return str(uuid.uuid4())

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID"""
        return hashlib.sha256(
            f"{datetime.now().isoformat()}:{id(self)}".encode()
        ).hexdigest()[:16]


class SecurityEventMonitor:
    """Main security event monitoring system"""

    def __init__(self):
        self.logger = get_security_logger(__name__)
        self.db_manager = get_enhanced_db_manager()
        self.threat_detector = ThreatDetector()
        self.redis_client = self._get_redis_client()
        self.event_handlers: list[Callable] = []
        self.alert_handlers: list[Callable] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Event counters for analytics
        self.event_counters = defaultdict(int)
        self.severity_counters = defaultdict(int)
        self.ip_counters = defaultdict(int)

        # Event queues for processing
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.alert_queue = asyncio.Queue(maxsize=1000)

    def _get_redis_client(self):
        """Get Redis client for caching"""
        try:
            if hasattr(config, "redis") and config.redis.host:
                return redis.Redis(
                    host=config.redis.host,
                    port=config.redis.port,
                    password=config.redis.password,
                    decode_responses=True,
                )
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
        return None

    async def start_monitoring(self):
        """Start the security monitoring system"""
        if self.running:
            return

        self.running = True
        self.logger.info(
            "Security Event Monitor started",
            message_tr="Güvenlik Olay İzleyicisi başlatıldı",
        )

        # Start background tasks
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._process_alerts())
        asyncio.create_task(self._cleanup_old_events())

    async def stop_monitoring(self):
        """Stop the security monitoring system"""
        self.running = False
        self.logger.info(
            "Security Event Monitor stopped",
            message_tr="Güvenlik Olay İzleyicisi durduruldu",
        )

    async def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        try:
            # Store in database
            await self._store_event(event)

            # Cache in Redis if available
            if self.redis_client:
                await self._cache_event(event)

            # Update counters
            self.event_counters[event.event_type.event_type] += 1
            self.severity_counters[event.severity.level] += 1
            self.ip_counters[event.ip_address] += 1

            # Log to structured logger
            self.logger.security_event(
                event.message,
                severity=event.severity.level,
                message_tr=event.message_tr,
                metadata={
                    "event_id": event.event_id,
                    "event_type": event.event_type.event_type,
                    "severity_score": event.severity.score,
                    "ip_address": event.ip_address,
                    "user_id": event.user_id,
                    "endpoint": event.endpoint,
                    **event.metadata,
                },
            )

            # Queue for processing
            if not self.event_queue.full():
                await self.event_queue.put(event)

            # Generate alerts if needed
            await self._check_alert_conditions(event)

        except Exception as e:
            self.logger.error(
                f"Failed to log security event: {e}",
                message_tr=f"Güvenlik olayı kaydetme başarısız: {e}",
            )

    async def _store_event(self, event: SecurityEvent):
        """Store event in database"""
        try:
            query = """
                INSERT INTO security_events (
                    event_id, event_type, severity, timestamp, user_id, session_id,
                    ip_address, user_agent, endpoint, method, payload, headers,
                    response_status, message, message_tr, metadata, location_info,
                    device_info, correlation_id, parent_event_id, tags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            await self.db_manager.execute_query(
                query,
                [
                    event.event_id,
                    event.event_type.event_type,
                    event.severity.level,
                    event.timestamp,
                    event.user_id,
                    event.session_id,
                    event.ip_address,
                    event.user_agent,
                    event.endpoint,
                    event.method,
                    json.dumps(event.payload),
                    json.dumps(event.headers),
                    event.response_status,
                    event.message,
                    event.message_tr,
                    json.dumps(event.metadata),
                    json.dumps(event.location_info),
                    json.dumps(event.device_info),
                    event.correlation_id,
                    event.parent_event_id,
                    json.dumps(event.tags),
                ],
            )

        except Exception as e:
            self.logger.error(f"Failed to store security event in database: {e}")

    async def _cache_event(self, event: SecurityEvent):
        """Cache event in Redis"""
        try:
            # Cache recent events by IP
            ip_key = f"security:events:ip:{event.ip_address}"
            await self.redis_client.lpush(ip_key, event.event_id)
            await self.redis_client.ltrim(ip_key, 0, 99)  # Keep last 100 events
            await self.redis_client.expire(ip_key, 3600)  # 1 hour expiry

            # Cache recent events by user
            if event.user_id:
                user_key = f"security:events:user:{event.user_id}"
                await self.redis_client.lpush(user_key, event.event_id)
                await self.redis_client.ltrim(user_key, 0, 99)
                await self.redis_client.expire(user_key, 3600)

            # Cache event details
            event_key = f"security:event:{event.event_id}"
            await self.redis_client.hmset(event_key, event.to_dict())
            await self.redis_client.expire(event_key, 86400)  # 24 hours

        except Exception as e:
            self.logger.error(f"Failed to cache security event: {e}")

    async def _check_alert_conditions(self, event: SecurityEvent):
        """Check if event should trigger alerts"""
        try:
            # Always alert on critical events
            if event.severity == SecuritySeverity.CRITICAL:
                await self._generate_alert(event, "Critical security event detected")
                return

            # Check for brute force patterns
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                recent_failures = await self._count_recent_events(
                    event.ip_address, SecurityEventType.LOGIN_FAILURE, minutes=5
                )
                if recent_failures >= 5:
                    await self._generate_alert(event, "Brute force attack detected")

            # Check for injection attack patterns
            if event.event_type in [
                SecurityEventType.SQL_INJECTION_ATTEMPT,
                SecurityEventType.XSS_ATTEMPT,
                SecurityEventType.COMMAND_INJECTION_ATTEMPT,
            ]:
                await self._generate_alert(event, "Code injection attack detected")

            # Check for privilege escalation
            if event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
                await self._generate_alert(event, "Privilege escalation detected")

            # Check for geographic anomalies
            if event.event_type == SecurityEventType.GEO_ANOMALY:
                await self._generate_alert(event, "Geographic anomaly detected")

        except Exception as e:
            self.logger.error(f"Failed to check alert conditions: {e}")

    async def _count_recent_events(
        self, ip_address: str, event_type: SecurityEventType, minutes: int = 5
    ) -> int:
        """Count recent events of specific type from IP"""
        try:
            query = """
                SELECT COUNT(*) as event_count
                FROM security_events 
                WHERE ip_address = %s 
                AND event_type = %s 
                AND timestamp > NOW() - INTERVAL '%s minutes'
            """

            result = await self.db_manager.fetch_one(
                query, [ip_address, event_type.event_type, minutes]
            )

            return result["event_count"] if result else 0

        except Exception as e:
            self.logger.error(f"Failed to count recent events: {e}")
            return 0

    async def _generate_alert(self, event: SecurityEvent, alert_message: str):
        """Generate security alert"""
        try:
            alert = {
                "alert_id": self._generate_alert_id(),
                "event_id": event.event_id,
                "alert_message": alert_message,
                "alert_message_tr": self._translate_alert(alert_message),
                "severity": event.severity.level,
                "timestamp": datetime.now(UTC).isoformat(),
                "ip_address": event.ip_address,
                "user_id": event.user_id,
                "event_type": event.event_type.event_type,
                "metadata": event.metadata,
            }

            # Queue for processing
            if not self.alert_queue.full():
                await self.alert_queue.put(alert)

            # Log alert
            self.logger.critical(
                f"SECURITY ALERT: {alert_message}",
                message_tr=f"GÜVENLİK ALARMI: {alert['alert_message_tr']}",
                metadata=alert,
            )

        except Exception as e:
            self.logger.error(f"Failed to generate alert: {e}")

    def _translate_alert(self, message: str) -> str:
        """Translate alert message to Turkish"""
        translations = {
            "Critical security event detected": "Kritik güvenlik olayı tespit edildi",
            "Brute force attack detected": "Kaba kuvvet saldırısı tespit edildi",
            "Code injection attack detected": "Kod enjeksiyon saldırısı tespit edildi",
            "Privilege escalation detected": "Yetki yükseltme tespit edildi",
            "Geographic anomaly detected": "Coğrafi anomali tespit edildi",
        }
        return translations.get(message, message)

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid

        return f"alert_{uuid.uuid4().hex[:8]}"

    async def _process_events(self):
        """Background task to process security events"""
        while self.running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Process event with registered handlers
                for handler in self.event_handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        self.logger.error(f"Event handler error: {e}")

            except TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing events: {e}")
                await asyncio.sleep(1)

    async def _process_alerts(self):
        """Background task to process security alerts"""
        while self.running:
            try:
                # Get alert from queue with timeout
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)

                # Process alert with registered handlers
                for handler in self.alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        self.logger.error(f"Alert handler error: {e}")

            except TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(1)

    async def _cleanup_old_events(self):
        """Background task to cleanup old events"""
        while self.running:
            try:
                # Run cleanup every hour
                await asyncio.sleep(3600)

                # Delete events older than configured retention period
                retention_days = getattr(config, "security_event_retention_days", 90)

                query = """
                    DELETE FROM security_events 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                """

                deleted_count = await self.db_manager.execute_query(
                    query, [retention_days]
                )

                if deleted_count > 0:
                    self.logger.info(
                        f"Cleaned up {deleted_count} old security events",
                        message_tr=f"{deleted_count} eski güvenlik olayı temizlendi",
                    )

            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")

    def register_event_handler(self, handler: Callable):
        """Register event handler"""
        self.event_handlers.append(handler)

    def register_alert_handler(self, handler: Callable):
        """Register alert handler"""
        self.alert_handlers.append(handler)

    async def get_security_metrics(self, hours: int = 24) -> dict[str, Any]:
        """Get security metrics for specified time period"""
        try:
            query = """
                SELECT 
                    event_type,
                    severity,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    COUNT(DISTINCT user_id) as unique_users
                FROM security_events 
                WHERE timestamp > NOW() - INTERVAL '%s hours'
                GROUP BY event_type, severity
                ORDER BY event_count DESC
            """

            results = await self.db_manager.fetch_all(query, [hours])

            metrics = {
                "time_period_hours": hours,
                "total_events": sum(r["event_count"] for r in results),
                "unique_ips": len(set(r["unique_ips"] for r in results)),
                "unique_users": len(
                    set(r["unique_users"] for r in results if r["unique_users"])
                ),
                "events_by_type": {},
                "events_by_severity": {},
                "top_ips": await self._get_top_ips(hours),
                "recent_alerts": await self._get_recent_alerts(hours),
            }

            for result in results:
                event_type = result["event_type"]
                severity = result["severity"]
                count = result["event_count"]

                if event_type not in metrics["events_by_type"]:
                    metrics["events_by_type"][event_type] = 0
                metrics["events_by_type"][event_type] += count

                if severity not in metrics["events_by_severity"]:
                    metrics["events_by_severity"][severity] = 0
                metrics["events_by_severity"][severity] += count

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get security metrics: {e}")
            return {"error": str(e)}

    async def _get_top_ips(self, hours: int, limit: int = 10) -> list[dict[str, Any]]:
        """Get top IP addresses by event count"""
        try:
            query = """
                SELECT 
                    ip_address,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT event_type) as event_types,
                    MAX(severity) as max_severity
                FROM security_events 
                WHERE timestamp > NOW() - INTERVAL '%s hours'
                AND ip_address != ''
                GROUP BY ip_address
                ORDER BY event_count DESC
                LIMIT %s
            """

            results = await self.db_manager.fetch_all(query, [hours, limit])
            return [dict(r) for r in results] if results else []

        except Exception as e:
            self.logger.error(f"Failed to get top IPs: {e}")
            return []

    async def _get_recent_alerts(
        self, hours: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent security alerts"""
        try:
            # This would typically be stored in a separate alerts table
            # For now, get high-severity events
            query = """
                SELECT 
                    event_id, event_type, severity, timestamp, ip_address, 
                    user_id, message, message_tr
                FROM security_events 
                WHERE timestamp > NOW() - INTERVAL '%s hours'
                AND severity IN ('high', 'critical')
                ORDER BY timestamp DESC
                LIMIT %s
            """

            results = await self.db_manager.fetch_all(query, [hours, limit])
            return [dict(r) for r in results] if results else []

        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []


# Global security monitor instance
_security_monitor: SecurityEventMonitor | None = None


def get_security_monitor() -> SecurityEventMonitor:
    """Get global security monitor instance"""
    global _security_monitor

    if _security_monitor is None:
        _security_monitor = SecurityEventMonitor()

    return _security_monitor


# Convenience functions
async def log_security_event(
    event_type: SecurityEventType,
    severity: SecuritySeverity,
    message: str,
    message_tr: str = "",
    **kwargs,
):
    """Log a security event"""
    monitor = get_security_monitor()

    event = SecurityEvent(
        event_id=ThreatDetector()._generate_event_id(),
        event_type=event_type,
        severity=severity,
        timestamp=datetime.now(UTC),
        message=message,
        message_tr=message_tr,
        **kwargs,
    )

    await monitor.log_security_event(event)


async def detect_and_log_threats(request_data: dict[str, Any]):
    """Detect threats and log security events"""
    monitor = get_security_monitor()
    threats = await monitor.threat_detector.detect_threats(request_data)

    for threat in threats:
        await monitor.log_security_event(threat)
