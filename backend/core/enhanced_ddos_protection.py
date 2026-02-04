"""
Enhanced DDoS Protection System (Task 51.4)
Advanced DDoS detection and mitigation with connection throttling and IP management

Author: Claude
Date: 2025-10-27
"""
import ipaddress
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import redis

from core.structured_logger import get_logger

logger = get_logger("enhanced_ddos_protection")


class ThreatLevel(str, Enum):
    """Threat levels for DDoS detection"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlockReason(str, Enum):
    """Reasons for blocking an IP"""

    BURST_THRESHOLD = "burst_threshold_exceeded"
    SUSTAINED_THRESHOLD = "sustained_threshold_exceeded"
    ENDPOINT_SCANNING = "endpoint_scanning_detected"
    SLOWLORIS = "slowloris_attack_detected"
    REQUEST_SIZE = "request_size_exceeded"
    MANUAL = "manual_block"
    SUSPICIOUS_PATTERN = "suspicious_pattern_detected"


@dataclass
class ConnectionInfo:
    """Information about a connection"""

    ip: str
    timestamp: float
    endpoint: str
    user_agent: str
    request_size: int
    response_time: float = 0.0
    status_code: int = 0


@dataclass
class IPReputation:
    """IP reputation tracking"""

    ip: str
    threat_level: ThreatLevel = ThreatLevel.LOW
    total_requests: int = 0
    blocked_count: int = 0
    last_seen: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    suspicious_patterns: list[str] = field(default_factory=list)
    whitelist: bool = False


class EnhancedDDoSProtection:
    """
    Enhanced DDoS Protection System (Task 51.4)

    Features:
    - Burst and sustained request rate detection
    - Endpoint scanning detection
    - Slowloris attack prevention (connection timeout)
    - Request size limits
    - IP whitelist/blacklist management
    - Connection throttling per IP
    - Automatic IP blocking with Redis integration
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        burst_threshold: int = 100,
        sustained_threshold: int = 1000,
        endpoint_threshold: int = 50,
        max_request_size_mb: int = 10,
        connection_timeout: int = 30,
        block_duration: int = 3600,
    ):
        self.redis_client = redis_client

        # Thresholds
        self.burst_threshold = burst_threshold  # requests per minute
        self.sustained_threshold = sustained_threshold  # requests per 10 minutes
        self.endpoint_threshold = endpoint_threshold  # unique endpoints per minute
        self.max_request_size = max_request_size_mb * 1024 * 1024  # MB to bytes
        self.connection_timeout = connection_timeout  # seconds
        self.block_duration = block_duration  # seconds

        # In-memory data structures
        self.ip_reputations: dict[str, IPReputation] = {}
        self.active_connections: dict[str, list[ConnectionInfo]] = defaultdict(list)
        self.blocked_ips: set[str] = set()
        self.whitelisted_ips: set[str] = set()
        self.blacklisted_ips: set[str] = set()

        # Load persistent data from Redis
        if self.redis_client:
            self._load_from_redis()

    def _load_from_redis(self):
        """Load blocked/whitelisted IPs from Redis"""
        try:
            # Load blocked IPs
            blocked_keys = self.redis_client.keys("ddos:blocked:*")
            for key in blocked_keys:
                ip = key.decode("utf-8").split(":")[-1]
                self.blocked_ips.add(ip)

            # Load whitelist
            whitelist = self.redis_client.smembers("ddos:whitelist")
            self.whitelisted_ips = {ip.decode("utf-8") for ip in whitelist}

            # Load blacklist
            blacklist = self.redis_client.smembers("ddos:blacklist")
            self.blacklisted_ips = {ip.decode("utf-8") for ip in blacklist}

            logger.info(
                f"[DDOS] Loaded {len(self.blocked_ips)} blocked, {len(self.whitelisted_ips)} whitelisted, "
                f"{len(self.blacklisted_ips)} blacklisted IPs from Redis"
            )

        except Exception as e:
            logger.error(f"[DDOS] Failed to load from Redis: {e}")

    def analyze_request(
        self,
        ip: str,
        endpoint: str,
        user_agent: str,
        request_size: int = 0,
        connection_duration: float = 0.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Analyze request for DDoS patterns

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_agent: User agent string
            request_size: Request size in bytes
            connection_duration: Time since connection started

        Returns:
            Tuple of (is_allowed, block_reason)
        """
        # Check blacklist first
        if ip in self.blacklisted_ips:
            return False, BlockReason.MANUAL.value

        # Check whitelist (bypass all checks)
        if ip in self.whitelisted_ips:
            return True, None

        # Check if already blocked
        if self.is_blocked(ip):
            return False, "IP is currently blocked"

        # Check request size
        if request_size > self.max_request_size:
            self._block_ip(ip, BlockReason.REQUEST_SIZE, duration=600)  # 10 min block
            return False, BlockReason.REQUEST_SIZE.value

        # Check slowloris attack (long-lived connections)
        if connection_duration > self.connection_timeout:
            self._block_ip(ip, BlockReason.SLOWLORIS, duration=1800)  # 30 min block
            return False, BlockReason.SLOWLORIS.value

        now = time.time()

        # Update IP reputation
        if ip not in self.ip_reputations:
            self.ip_reputations[ip] = IPReputation(ip=ip)

        reputation = self.ip_reputations[ip]
        reputation.total_requests += 1
        reputation.last_seen = now

        # Record connection
        connection = ConnectionInfo(
            ip=ip,
            timestamp=now,
            endpoint=endpoint,
            user_agent=user_agent,
            request_size=request_size,
        )
        self.active_connections[ip].append(connection)

        # Clean old connections
        cutoff_time = now - 600  # 10 minutes
        self.active_connections[ip] = [
            conn for conn in self.active_connections[ip] if conn.timestamp > cutoff_time
        ]

        # Analyze patterns
        is_allowed, reason = self._analyze_patterns(ip, endpoint, now)

        if not is_allowed:
            self._block_ip(ip, reason or BlockReason.SUSPICIOUS_PATTERN)
            reputation.blocked_count += 1
            reputation.threat_level = self._calculate_threat_level(reputation)

        return is_allowed, reason

    def _analyze_patterns(
        self, ip: str, endpoint: str, now: float
    ) -> tuple[bool, Optional[str]]:
        """Analyze request patterns for DDoS indicators"""
        connections = self.active_connections[ip]

        if not connections:
            return True, None

        # Burst detection (1 minute)
        recent_connections = [
            conn for conn in connections if now - conn.timestamp <= 60
        ]
        if len(recent_connections) > self.burst_threshold:
            logger.warning(
                f"[DDOS] Burst threshold exceeded for {ip}",
                extra_data={"ip": ip, "count": len(recent_connections)},
            )
            return False, BlockReason.BURST_THRESHOLD.value

        # Sustained detection (10 minutes)
        if len(connections) > self.sustained_threshold:
            logger.warning(
                f"[DDOS] Sustained threshold exceeded for {ip}",
                extra_data={"ip": ip, "count": len(connections)},
            )
            return False, BlockReason.SUSTAINED_THRESHOLD.value

        # Endpoint scanning detection
        unique_endpoints = set(conn.endpoint for conn in recent_connections)
        if len(unique_endpoints) > self.endpoint_threshold:
            logger.warning(
                f"[DDOS] Endpoint scanning detected for {ip}",
                extra_data={"ip": ip, "unique_endpoints": len(unique_endpoints)},
            )
            return False, BlockReason.ENDPOINT_SCANNING.value

        return True, None

    def _calculate_threat_level(self, reputation: IPReputation) -> ThreatLevel:
        """Calculate threat level based on IP reputation"""
        if reputation.blocked_count >= 5:
            return ThreatLevel.CRITICAL
        elif reputation.blocked_count >= 3:
            return ThreatLevel.HIGH
        elif reputation.blocked_count >= 1:
            return ThreatLevel.MEDIUM
        return ThreatLevel.LOW

    def _block_ip(self, ip: str, reason: BlockReason, duration: Optional[int] = None):
        """
        Block an IP address

        Args:
            ip: IP address to block
            reason: Reason for blocking
            duration: Block duration in seconds (default: self.block_duration)
        """
        duration = duration or self.block_duration
        self.blocked_ips.add(ip)

        # Store in Redis with TTL
        if self.redis_client:
            block_key = f"ddos:blocked:{ip}"
            block_data = {
                "reason": reason.value
                if isinstance(reason, BlockReason)
                else str(reason),
                "timestamp": time.time(),
                "duration": duration,
            }
            self.redis_client.setex(block_key, duration, str(block_data))

            # Increment block counter
            counter_key = f"ddos:block_count:{ip}"
            self.redis_client.incr(counter_key)
            self.redis_client.expire(counter_key, 86400)  # 1 day

        logger.warning(
            f"[DDOS] IP blocked: {ip}",
            extra_data={"ip": ip, "reason": str(reason), "duration": duration},
        )

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        # Check in-memory cache
        if ip in self.blocked_ips:
            # Verify with Redis if available
            if self.redis_client:
                block_key = f"ddos:blocked:{ip}"
                if not self.redis_client.exists(block_key):
                    # Block expired, remove from cache
                    self.blocked_ips.discard(ip)
                    return False
            return True

        # Check Redis
        if self.redis_client:
            block_key = f"ddos:blocked:{ip}"
            if self.redis_client.exists(block_key):
                self.blocked_ips.add(ip)
                return True

        return False

    def whitelist_ip(self, ip: str):
        """Add IP to whitelist"""
        self.whitelisted_ips.add(ip)

        if self.redis_client:
            self.redis_client.sadd("ddos:whitelist", ip)

        # Remove from blocked if present
        self.unblock_ip(ip)

        logger.info(f"[DDOS] IP whitelisted: {ip}")

    def blacklist_ip(self, ip: str, reason: str = "manual"):
        """Add IP to permanent blacklist"""
        self.blacklisted_ips.add(ip)

        if self.redis_client:
            self.redis_client.sadd("ddos:blacklist", ip)
            self.redis_client.hset(f"ddos:blacklist_reason:{ip}", "reason", reason)

        logger.warning(f"[DDOS] IP blacklisted: {ip} - Reason: {reason}")

    def unblock_ip(self, ip: str):
        """Manually unblock an IP"""
        self.blocked_ips.discard(ip)

        if self.redis_client:
            block_key = f"ddos:blocked:{ip}"
            self.redis_client.delete(block_key)

        logger.info(f"[DDOS] IP unblocked: {ip}")

    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist"""
        self.whitelisted_ips.discard(ip)

        if self.redis_client:
            self.redis_client.srem("ddos:whitelist", ip)

        logger.info(f"[DDOS] IP removed from whitelist: {ip}")

    def remove_from_blacklist(self, ip: str):
        """Remove IP from blacklist"""
        self.blacklisted_ips.discard(ip)

        if self.redis_client:
            self.redis_client.srem("ddos:blacklist", ip)
            self.redis_client.delete(f"ddos:blacklist_reason:{ip}")

        logger.info(f"[DDOS] IP removed from blacklist: {ip}")

    def get_ip_reputation(self, ip: str) -> Optional[IPReputation]:
        """Get reputation information for an IP"""
        return self.ip_reputations.get(ip)

    def get_blocked_ips(self) -> list[str]:
        """Get list of currently blocked IPs"""
        # Sync with Redis
        if self.redis_client:
            blocked_keys = self.redis_client.keys("ddos:blocked:*")
            redis_blocked = {key.decode("utf-8").split(":")[-1] for key in blocked_keys}
            self.blocked_ips = redis_blocked

        return list(self.blocked_ips)

    def get_whitelisted_ips(self) -> list[str]:
        """Get list of whitelisted IPs"""
        return list(self.whitelisted_ips)

    def get_blacklisted_ips(self) -> list[str]:
        """Get list of blacklisted IPs"""
        return list(self.blacklisted_ips)

    def get_statistics(self) -> dict:
        """Get DDoS protection statistics"""
        return {
            "blocked_ips_count": len(self.blocked_ips),
            "whitelisted_ips_count": len(self.whitelisted_ips),
            "blacklisted_ips_count": len(self.blacklisted_ips),
            "tracked_ips_count": len(self.ip_reputations),
            "active_connections": sum(
                len(conns) for conns in self.active_connections.values()
            ),
            "thresholds": {
                "burst": self.burst_threshold,
                "sustained": self.sustained_threshold,
                "endpoints": self.endpoint_threshold,
                "max_request_size_mb": self.max_request_size / (1024 * 1024),
                "connection_timeout": self.connection_timeout,
            },
        }


# Global instance
_ddos_protection: Optional[EnhancedDDoSProtection] = None


def get_ddos_protection(
    redis_client: Optional[redis.Redis] = None,
) -> EnhancedDDoSProtection:
    """Get global DDoS protection instance"""
    global _ddos_protection

    if _ddos_protection is None:
        _ddos_protection = EnhancedDDoSProtection(redis_client=redis_client)

    return _ddos_protection
