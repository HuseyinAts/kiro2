"""
KIRO2 Turkish Exam Specific Middleware
Specialized middleware for Turkish university entrance examination system
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any

from core.application_metrics import MetricType, get_metrics_collector
from core.auth_middleware import AuthContext, AuthUser, UserRole
from core.cache_system_integration import get_unified_cache_system
from core.structured_logging import LogCategory, get_logger
from core.turkish_exam_event_handlers import TurkishExamType
from core.unified_api_gateway import APIRequest, APIResponse, RouteType
from core.unified_config import get_unified_config
from core.unified_event_bus import EventPriority, EventType, publish_event

config = get_unified_config()
logger = get_logger(__name__, LogCategory.EXAM)


class ExamPeriod(Enum):
    """Turkish exam periods"""

    REGISTRATION = "registration"
    PREPARATION = "preparation"
    EXAM_WEEK = "exam_week"
    RESULTS = "results"
    OFF_SEASON = "off_season"


class ExamSecurityLevel(Enum):
    """Exam security levels"""

    LOW = "low"  # Practice tests
    MEDIUM = "medium"  # Simulations
    HIGH = "high"  # Mock exams
    MAXIMUM = "maximum"  # Real exams


@dataclass
class ExamContext:
    """Turkish exam context information"""

    exam_type: TurkishExamType | None = None
    session_id: str | None = None
    current_period: ExamPeriod = ExamPeriod.OFF_SEASON
    security_level: ExamSecurityLevel = ExamSecurityLevel.LOW
    time_remaining: int | None = None  # minutes
    question_number: int | None = None
    total_questions: int | None = None
    subject: str | None = None
    difficulty: str = "orta"
    is_practice: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class TurkishLanguageMiddleware:
    """Turkish language and localization middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.turkish_subjects = {
            "matematik": "Matematik",
            "geometri": "Geometri",
            "turkce": "Türkçe-Edebiyat",
            "tarih": "Tarih",
            "cografya": "Coğrafya",
            "felsefe": "Felsefe",
            "din": "Din Kültürü ve Ahlak Bilgisi",
            "fizik": "Fizik",
            "kimya": "Kimya",
            "biyoloji": "Biyoloji",
        }

        self.exam_translations = {
            "tyt": "Temel Yeterlilik Testi",
            "ayt": "Alan Yeterlilik Testi",
            "yks": "Yükseköğretim Kurumları Sınavı",
            "msu": "Matematik ve Fen Bilimleri Testi",
            "dil": "Yabancı Dil Testi",
        }

        self.common_phrases = {
            "exam_started": "Sınav başladı",
            "exam_completed": "Sınav tamamlandı",
            "time_warning": "Zaman uyarısı",
            "good_luck": "Başarılar",
            "please_wait": "Lütfen bekleyin",
            "loading": "Yükleniyor",
            "processing": "İşleniyor",
        }

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process Turkish language middleware"""
        try:
            # Set Turkish locale context
            request.metadata["language"] = "tr"
            request.metadata["country"] = "TR"
            request.metadata["locale"] = "tr-TR"
            request.metadata["timezone"] = "Europe/Istanbul"

            # Translate request parameters if needed
            await self._translate_request_params(request)

            # Process request
            response = await next_handler(request)

            # Add Turkish translations to response
            if response.body:
                await self._add_turkish_translations(response, request)

            # Add Turkish headers
            response.add_header("Content-Language", "tr-TR")
            response.add_header("X-Turkish-Platform", "KIRO2-YKS-Hazırlık")
            response.add_header("X-Exam-System", "Turkish-University-Entrance")

            return response

        except Exception as e:
            logger.error(f"Turkish language middleware error: {e}")
            return await next_handler(request)

    async def _translate_request_params(self, request: APIRequest):
        """Translate Turkish request parameters"""
        try:
            if request.body:
                # Translate subject names
                if "subject" in request.body:
                    subject = request.body["subject"].lower()
                    if subject in self.turkish_subjects:
                        request.body["subject_tr"] = self.turkish_subjects[subject]
                        request.body["subject_name"] = self.turkish_subjects[subject]

                # Translate exam types
                if "exam_type" in request.body:
                    exam_type = request.body["exam_type"].lower()
                    if exam_type in self.exam_translations:
                        request.body["exam_type_tr"] = self.exam_translations[exam_type]
                        request.body["exam_name"] = self.exam_translations[exam_type]

            # Translate query parameters
            if "subject" in request.query_params:
                subject = str(request.query_params["subject"]).lower()
                if subject in self.turkish_subjects:
                    request.query_params["subject_tr"] = self.turkish_subjects[subject]

        except Exception as e:
            logger.error(f"Request parameter translation error: {e}")

    async def _add_turkish_translations(
        self, response: APIResponse, request: APIRequest
    ):
        """Add Turkish translations to response"""
        try:
            if not isinstance(response.body, dict):
                return

            # Add Turkish translations for common fields
            translations_added = {}

            for key, value in response.body.items():
                if isinstance(value, str):
                    # Translate common phrases
                    value_lower = value.lower()
                    for en_phrase, tr_phrase in self.common_phrases.items():
                        if en_phrase in value_lower:
                            tr_key = f"{key}_tr"
                            if tr_key not in response.body:
                                translations_added[tr_key] = value.replace(
                                    en_phrase, tr_phrase
                                )
                            break

            # Add Turkish exam context
            if request.route_type in {
                RouteType.TYT_EXAM,
                RouteType.AYT_EXAM,
                RouteType.YKS_INFO,
            }:
                response.body["platform_info"] = {
                    "name": "KIRO2 - Türkiye Üniversite Sınavları Hazırlık Platformu",
                    "description": "YKS, TYT ve AYT sınavlarına hazırlık sistemi",
                    "country": "Türkiye",
                    "education_system": "Turkish Higher Education",
                }

            # Add Turkish timestamp
            if "timestamp" in response.body:
                try:
                    dt = datetime.fromisoformat(
                        response.body["timestamp"].replace("Z", "+00:00")
                    )
                    turkey_tz = timezone(timedelta(hours=3))
                    turkey_dt = dt.astimezone(turkey_tz)
                    response.body["timestamp_turkey"] = turkey_dt.strftime(
                        "%d.%m.%Y %H:%M:%S"
                    )
                    response.body["date_turkish"] = turkey_dt.strftime("%d %B %Y")
                except Exception:
                    pass

            # Add translations to response
            response.body.update(translations_added)

        except Exception as e:
            logger.error(f"Response translation error: {e}")


class ExamSecurityMiddleware:
    """Security middleware for Turkish exam system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.security_violations: dict[str, list[datetime]] = {}
        self.blocked_users: dict[int, datetime] = {}
        self.exam_monitoring = config.get("exam_monitoring", True)
        self.anti_cheat_enabled = config.get("anti_cheat_enabled", True)

        # Security thresholds
        self.max_violations_per_hour = 5
        self.block_duration_minutes = 30
        self.suspicious_patterns = [
            r"copy|paste|ctrl\+c|ctrl\+v",  # Copy-paste attempts
            r"screenshot|print screen",  # Screenshot attempts
            r"developer tools|inspect",  # Dev tools
            r"view source|view-source",  # Source viewing
        ]

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process exam security middleware"""
        try:
            # Get auth context
            auth_context: AuthContext = request.metadata.get("auth_context")

            if not auth_context or not auth_context.user:
                return await next_handler(request)

            user = auth_context.user

            # Check if user is blocked
            if self._is_user_blocked(user.user_id):
                return self._create_security_error(
                    request.id,
                    "User temporarily blocked",
                    "Hesabınız geçici olarak engellenmiştir",
                )

            # Apply exam-specific security
            if request.is_exam_route():
                security_check = await self._check_exam_security(request, user)
                if not security_check["allowed"]:
                    return self._create_security_error(
                        request.id,
                        security_check["reason"],
                        security_check["reason_tr"],
                    )

            # Monitor for suspicious activity
            if self.anti_cheat_enabled:
                await self._monitor_suspicious_activity(request, user)

            # Process request with security headers
            response = await next_handler(request)

            # Add security headers to response
            self._add_security_headers(response, request)

            return response

        except Exception as e:
            logger.error(f"Exam security middleware error: {e}")
            return await next_handler(request)

    def _is_user_blocked(self, user_id: int) -> bool:
        """Check if user is currently blocked"""
        if user_id in self.blocked_users:
            blocked_until = self.blocked_users[user_id]
            if datetime.now(UTC) < blocked_until:
                return True
            del self.blocked_users[user_id]
        return False

    async def _check_exam_security(
        self, request: APIRequest, user: AuthUser
    ) -> dict[str, Any]:
        """Check exam-specific security requirements"""
        try:
            # Check for multiple active sessions
            if await self._has_multiple_active_sessions(user.user_id):
                return {
                    "allowed": False,
                    "reason": "Multiple active sessions detected",
                    "reason_tr": "Birden fazla aktif oturum tespit edildi",
                }

            # Check exam timing constraints
            if request.path.endswith("/start"):
                timing_check = await self._check_exam_timing(request, user)
                if not timing_check["allowed"]:
                    return timing_check

            # Check user eligibility
            eligibility_check = await self._check_user_eligibility(request, user)
            if not eligibility_check["allowed"]:
                return eligibility_check

            return {"allowed": True}

        except Exception as e:
            logger.error(f"Exam security check error: {e}")
            return {"allowed": True}  # Allow on error

    async def _has_multiple_active_sessions(self, user_id: int) -> bool:
        """Check if user has multiple active exam sessions"""
        try:
            cache_system = await get_unified_cache_system()
            active_sessions_key = f"active_exam_sessions:{user_id}"

            active_sessions = (
                await cache_system.cache_system.get(active_sessions_key) or []
            )

            # Clean expired sessions
            now = datetime.now(UTC)
            valid_sessions = []

            for session in active_sessions:
                session_start = datetime.fromisoformat(session.get("started_at", ""))
                if now - session_start < timedelta(hours=4):  # Max exam duration
                    valid_sessions.append(session)

            # Update cache
            if valid_sessions != active_sessions:
                await cache_system.cache_system.set(
                    active_sessions_key, valid_sessions, ttl=4 * 3600
                )

            return len(valid_sessions) > 1

        except Exception as e:
            logger.error(f"Multiple sessions check error: {e}")
            return False

    async def _check_exam_timing(
        self, request: APIRequest, user: AuthUser
    ) -> dict[str, Any]:
        """Check exam timing constraints"""
        try:
            # Get current time in Turkey timezone
            turkey_tz = timezone(timedelta(hours=3))
            now_turkey = datetime.now(turkey_tz)

            # Check if it's exam hours (typically 9:00 - 18:00)
            if request.body and request.body.get("exam_type") == "real":
                if not (9 <= now_turkey.hour <= 18):
                    return {
                        "allowed": False,
                        "reason": "Exam not available outside official hours",
                        "reason_tr": "Sınav resmi saatler dışında erişilebilir değil",
                    }

            # Check daily attempt limits
            daily_attempts = await self._get_daily_attempts(user.user_id)
            max_daily_attempts = 5  # Configurable

            if daily_attempts >= max_daily_attempts:
                return {
                    "allowed": False,
                    "reason": "Daily attempt limit exceeded",
                    "reason_tr": "Günlük deneme sınırı aşıldı",
                }

            return {"allowed": True}

        except Exception as e:
            logger.error(f"Exam timing check error: {e}")
            return {"allowed": True}

    async def _check_user_eligibility(
        self, request: APIRequest, user: AuthUser
    ) -> dict[str, Any]:
        """Check user eligibility for exam"""
        try:
            # Students can take exams
            if user.is_student():
                return {"allowed": True}

            # Teachers can access for demo purposes
            if user.role == UserRole.TEACHER:
                return {"allowed": True}

            # Admins have full access
            if user.is_admin():
                return {"allowed": True}

            return {
                "allowed": False,
                "reason": "User role not authorized for exams",
                "reason_tr": "Kullanıcı rolü sınavlar için yetkili değil",
            }

        except Exception as e:
            logger.error(f"User eligibility check error: {e}")
            return {"allowed": True}

    async def _get_daily_attempts(self, user_id: int) -> int:
        """Get user's daily exam attempts"""
        try:
            cache_system = await get_unified_cache_system()
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            attempts_key = f"daily_attempts:{user_id}:{today}"

            attempts = await cache_system.cache_system.get(attempts_key) or 0
            return int(attempts)

        except Exception as e:
            logger.error(f"Daily attempts check error: {e}")
            return 0

    async def _monitor_suspicious_activity(self, request: APIRequest, user: AuthUser):
        """Monitor for suspicious exam activity"""
        try:
            # Check request patterns
            suspicious_indicators = []

            # Check user agent for automation tools
            user_agent = request.user_agent.lower()
            if any(
                tool in user_agent
                for tool in ["selenium", "phantomjs", "headless", "bot"]
            ):
                suspicious_indicators.append("automated_tool")

            # Check for rapid requests
            if await self._is_rapid_requests(user.user_id):
                suspicious_indicators.append("rapid_requests")

            # Check request headers for suspicious patterns
            for pattern in self.suspicious_patterns:
                if any(
                    re.search(pattern, str(value), re.IGNORECASE)
                    for value in request.headers.values()
                ):
                    suspicious_indicators.append("suspicious_headers")
                    break

            # Log and handle violations
            if suspicious_indicators:
                await self._handle_security_violation(
                    user.user_id, suspicious_indicators, request
                )

        except Exception as e:
            logger.error(f"Suspicious activity monitoring error: {e}")

    async def _is_rapid_requests(self, user_id: int) -> bool:
        """Check if user is making rapid requests"""
        try:
            cache_system = await get_unified_cache_system()
            requests_key = f"user_requests:{user_id}"

            # Get recent requests
            recent_requests = await cache_system.cache_system.get(requests_key) or []
            now = datetime.now(UTC)

            # Keep only requests from last minute
            recent_requests = [
                req_time
                for req_time in recent_requests
                if (now - datetime.fromisoformat(req_time)).total_seconds() <= 60
            ]

            # Add current request
            recent_requests.append(now.isoformat())

            # Store updated list
            await cache_system.cache_system.set(requests_key, recent_requests, ttl=60)

            # Check if too many requests
            return len(recent_requests) > 20  # Max 20 requests per minute

        except Exception as e:
            logger.error(f"Rapid requests check error: {e}")
            return False

    async def _handle_security_violation(
        self, user_id: int, violations: list[str], request: APIRequest
    ):
        """Handle security violation"""
        try:
            now = datetime.now(UTC)

            # Record violation
            if user_id not in self.security_violations:
                self.security_violations[user_id] = []

            self.security_violations[user_id].append(now)

            # Clean old violations (older than 1 hour)
            hour_ago = now - timedelta(hours=1)
            self.security_violations[user_id] = [
                v for v in self.security_violations[user_id] if v > hour_ago
            ]

            violation_count = len(self.security_violations[user_id])

            # Block user if too many violations
            if violation_count >= self.max_violations_per_hour:
                block_until = now + timedelta(minutes=self.block_duration_minutes)
                self.blocked_users[user_id] = block_until

                logger.warning(
                    f"User {user_id} blocked due to security violations: {violations}",
                    extra={"violations": violations, "count": violation_count},
                )

                # Publish security event
                await publish_event(
                    EventType.SECURITY_ALERT,
                    {
                        "type": "exam_security_violation",
                        "user_id": user_id,
                        "violations": violations,
                        "violation_count": violation_count,
                        "blocked": True,
                        "client_ip": request.client_ip,
                    },
                    user_id=user_id,
                    priority=EventPriority.HIGH,
                )
            else:
                logger.info(
                    f"Security violation recorded for user {user_id}: {violations}",
                    extra={"violations": violations, "count": violation_count},
                )

        except Exception as e:
            logger.error(f"Security violation handling error: {e}")

    def _add_security_headers(self, response: APIResponse, request: APIRequest):
        """Add security headers to exam responses"""
        try:
            if request.is_exam_route():
                response.add_header("X-Frame-Options", "DENY")
                response.add_header("X-Content-Type-Options", "nosniff")
                response.add_header(
                    "Cache-Control", "no-store, no-cache, must-revalidate"
                )
                response.add_header("Pragma", "no-cache")
                response.add_header("X-Exam-Security", "enabled")
                response.add_header("X-Anti-Cheat", "active")

        except Exception as e:
            logger.error(f"Security headers error: {e}")

    def _create_security_error(
        self, request_id: str, reason: str, reason_tr: str
    ) -> APIResponse:
        """Create security error response"""
        return APIResponse(
            request_id=request_id,
            status_code=403,
            headers={"Content-Type": "application/json"},
            body={
                "error": "Security Violation",
                "detail": reason,
                "error_tr": "Güvenlik İhlali",
                "detail_tr": reason_tr,
                "support_contact": "destek@kiro2.com",
            },
            processing_time_ms=1.0,
        )


class ExamSessionMiddleware:
    """Exam session management middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_system = None
        self.session_timeout_minutes = config.get(
            "session_timeout_minutes", 240
        )  # 4 hours

    async def _get_cache_system(self):
        """Get cache system instance"""
        if not self.cache_system:
            self.cache_system = await get_unified_cache_system()
        return self.cache_system

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process exam session middleware"""
        try:
            # Only process exam routes
            if not request.is_exam_route():
                return await next_handler(request)

            auth_context: AuthContext = request.metadata.get("auth_context")
            if not auth_context or not auth_context.user:
                return await next_handler(request)

            user = auth_context.user

            # Handle exam session operations
            if request.path.endswith("/start"):
                response = await self._handle_exam_start(request, user, next_handler)
            elif request.path.endswith("/submit") or request.path.endswith("/complete"):
                response = await self._handle_exam_completion(
                    request, user, next_handler
                )
            elif "/question/" in request.path:
                response = await self._handle_question_access(
                    request, user, next_handler
                )
            else:
                response = await self._handle_exam_progress(request, user, next_handler)

            return response

        except Exception as e:
            logger.error(f"Exam session middleware error: {e}")
            return await next_handler(request)

    async def _handle_exam_start(
        self, request: APIRequest, user: AuthUser, next_handler: Callable
    ) -> APIResponse:
        """Handle exam start request"""
        try:
            # Determine exam type from path
            exam_type = self._extract_exam_type_from_path(request.path)

            # Check for existing active session
            existing_session = await self._get_active_exam_session(
                user.user_id, exam_type
            )
            if existing_session:
                return APIResponse(
                    request_id=request.id,
                    status_code=409,
                    headers={"Content-Type": "application/json"},
                    body={
                        "error": "Active session exists",
                        "detail": "You already have an active exam session",
                        "error_tr": "Aktif oturum mevcut",
                        "detail_tr": "Zaten aktif bir sınav oturumunuz var",
                        "existing_session_id": existing_session["session_id"],
                    },
                    processing_time_ms=10.0,
                )

            # Process exam start
            response = await next_handler(request)

            # If successful, create session tracking
            if response.is_success() and response.body:
                session_id = response.body.get("session_id")
                if session_id:
                    await self._track_exam_session(
                        user.user_id, session_id, exam_type, request
                    )

            return response

        except Exception as e:
            logger.error(f"Exam start handling error: {e}")
            return await next_handler(request)

    async def _handle_exam_completion(
        self, request: APIRequest, user: AuthUser, next_handler: Callable
    ) -> APIResponse:
        """Handle exam completion request"""
        try:
            # Process completion
            response = await next_handler(request)

            # Clean up session tracking
            if response.is_success():
                exam_type = self._extract_exam_type_from_path(request.path)
                await self._cleanup_exam_session(user.user_id, exam_type)

                # Record completion metrics
                metrics_collector = get_metrics_collector()
                metrics_collector.record_metric(
                    MetricType.EXAM_COMPLETED,
                    1,
                    metadata={
                        "exam_type": exam_type,
                        "user_id": user.user_id,
                        "completion_time": datetime.now(UTC).isoformat(),
                    },
                )

            return response

        except Exception as e:
            logger.error(f"Exam completion handling error: {e}")
            return await next_handler(request)

    async def _handle_question_access(
        self, request: APIRequest, user: AuthUser, next_handler: Callable
    ) -> APIResponse:
        """Handle question access during exam"""
        try:
            # Validate session is active
            exam_type = self._extract_exam_type_from_path(request.path)
            active_session = await self._get_active_exam_session(
                user.user_id, exam_type
            )

            if not active_session:
                return APIResponse(
                    request_id=request.id,
                    status_code=403,
                    headers={"Content-Type": "application/json"},
                    body={
                        "error": "No active session",
                        "detail": "No active exam session found",
                        "error_tr": "Aktif oturum yok",
                        "detail_tr": "Aktif sınav oturumu bulunamadı",
                    },
                    processing_time_ms=5.0,
                )

            # Check session timeout
            if self._is_session_expired(active_session):
                await self._cleanup_exam_session(user.user_id, exam_type)
                return APIResponse(
                    request_id=request.id,
                    status_code=408,
                    headers={"Content-Type": "application/json"},
                    body={
                        "error": "Session expired",
                        "detail": "Exam session has expired",
                        "error_tr": "Oturum süresi doldu",
                        "detail_tr": "Sınav oturumunun süresi doldu",
                    },
                    processing_time_ms=5.0,
                )

            # Update session activity
            await self._update_session_activity(user.user_id, exam_type)

            return await next_handler(request)

        except Exception as e:
            logger.error(f"Question access handling error: {e}")
            return await next_handler(request)

    async def _handle_exam_progress(
        self, request: APIRequest, user: AuthUser, next_handler: Callable
    ) -> APIResponse:
        """Handle general exam progress requests"""
        try:
            response = await next_handler(request)

            # Add session info to response if available
            if response.is_success() and response.body:
                exam_type = self._extract_exam_type_from_path(request.path)
                active_session = await self._get_active_exam_session(
                    user.user_id, exam_type
                )

                if active_session:
                    response.body["session_info"] = {
                        "session_id": active_session["session_id"],
                        "started_at": active_session["started_at"],
                        "time_remaining": self._calculate_time_remaining(
                            active_session
                        ),
                        "activity_count": active_session.get("activity_count", 0),
                    }

            return response

        except Exception as e:
            logger.error(f"Exam progress handling error: {e}")
            return await next_handler(request)

    def _extract_exam_type_from_path(self, path: str) -> str:
        """Extract exam type from request path"""
        path_lower = path.lower()
        if "tyt" in path_lower:
            return "tyt"
        if "ayt" in path_lower:
            return "ayt"
        if "yks" in path_lower:
            return "yks"
        return "unknown"

    async def _get_active_exam_session(
        self, user_id: int, exam_type: str
    ) -> dict[str, Any] | None:
        """Get active exam session for user"""
        try:
            cache_system = await self._get_cache_system()
            session_key = f"active_exam:{user_id}:{exam_type}"
            return await cache_system.cache_system.get(session_key)
        except Exception as e:
            logger.error(f"Get active session error: {e}")
            return None

    async def _track_exam_session(
        self, user_id: int, session_id: str, exam_type: str, request: APIRequest
    ):
        """Track active exam session"""
        try:
            cache_system = await self._get_cache_system()

            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "exam_type": exam_type,
                "started_at": datetime.now(UTC).isoformat(),
                "last_activity": datetime.now(UTC).isoformat(),
                "client_ip": request.client_ip,
                "user_agent": request.user_agent,
                "activity_count": 1,
            }

            # Store session
            session_key = f"active_exam:{user_id}:{exam_type}"
            await cache_system.cache_system.set(
                session_key, session_data, ttl=self.session_timeout_minutes * 60
            )

            # Track in user sessions list
            await self._add_to_user_sessions(user_id, session_data)

            logger.info(f"Exam session tracked: {session_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Session tracking error: {e}")

    async def _add_to_user_sessions(self, user_id: int, session_data: dict[str, Any]):
        """Add session to user's active sessions list"""
        try:
            cache_system = await self._get_cache_system()
            user_sessions_key = f"user_exam_sessions:{user_id}"

            current_sessions = (
                await cache_system.cache_system.get(user_sessions_key) or []
            )
            current_sessions.append(session_data)

            await cache_system.cache_system.set(
                user_sessions_key, current_sessions, ttl=24 * 3600
            )

        except Exception as e:
            logger.error(f"Add to user sessions error: {e}")

    async def _update_session_activity(self, user_id: int, exam_type: str):
        """Update session last activity"""
        try:
            cache_system = await self._get_cache_system()
            session_key = f"active_exam:{user_id}:{exam_type}"

            session_data = await cache_system.cache_system.get(session_key)
            if session_data:
                session_data["last_activity"] = datetime.now(UTC).isoformat()
                session_data["activity_count"] = (
                    session_data.get("activity_count", 0) + 1
                )

                await cache_system.cache_system.set(
                    session_key, session_data, ttl=self.session_timeout_minutes * 60
                )

        except Exception as e:
            logger.error(f"Update session activity error: {e}")

    async def _cleanup_exam_session(self, user_id: int, exam_type: str):
        """Clean up exam session"""
        try:
            cache_system = await self._get_cache_system()
            session_key = f"active_exam:{user_id}:{exam_type}"

            # Get session data before deletion
            session_data = await cache_system.cache_system.get(session_key)

            # Remove session
            await cache_system.cache_system.delete(session_key)

            if session_data:
                # Remove from user sessions list
                await self._remove_from_user_sessions(
                    user_id, session_data["session_id"]
                )

                logger.info(
                    f"Exam session cleaned up: {session_data['session_id']} for user {user_id}"
                )

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

    async def _remove_from_user_sessions(self, user_id: int, session_id: str):
        """Remove session from user's sessions list"""
        try:
            cache_system = await self._get_cache_system()
            user_sessions_key = f"user_exam_sessions:{user_id}"

            current_sessions = (
                await cache_system.cache_system.get(user_sessions_key) or []
            )
            updated_sessions = [
                s for s in current_sessions if s.get("session_id") != session_id
            ]

            if updated_sessions:
                await cache_system.cache_system.set(
                    user_sessions_key, updated_sessions, ttl=24 * 3600
                )
            else:
                await cache_system.cache_system.delete(user_sessions_key)

        except Exception as e:
            logger.error(f"Remove from user sessions error: {e}")

    def _is_session_expired(self, session_data: dict[str, Any]) -> bool:
        """Check if session is expired"""
        try:
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            now = datetime.now(UTC)

            timeout_delta = timedelta(minutes=self.session_timeout_minutes)
            return now - last_activity > timeout_delta

        except Exception as e:
            logger.error(f"Session expiry check error: {e}")
            return False

    def _calculate_time_remaining(self, session_data: dict[str, Any]) -> int | None:
        """Calculate time remaining in session (minutes)"""
        try:
            started_at = datetime.fromisoformat(session_data["started_at"])
            now = datetime.now(UTC)

            elapsed_minutes = (now - started_at).total_seconds() / 60
            remaining_minutes = self.session_timeout_minutes - elapsed_minutes

            return max(0, int(remaining_minutes))

        except Exception as e:
            logger.error(f"Time remaining calculation error: {e}")
            return None


# Factory functions


def create_turkish_language_middleware(
    config: dict[str, Any] = None
) -> TurkishLanguageMiddleware:
    """Create Turkish language middleware instance"""
    config = config or {}
    return TurkishLanguageMiddleware(config)


def create_exam_security_middleware(
    config: dict[str, Any] = None
) -> ExamSecurityMiddleware:
    """Create exam security middleware instance"""
    config = config or {}
    return ExamSecurityMiddleware(config)


def create_exam_session_middleware(
    config: dict[str, Any] = None
) -> ExamSessionMiddleware:
    """Create exam session middleware instance"""
    config = config or {}
    return ExamSessionMiddleware(config)


# Middleware configuration


def get_turkish_exam_middleware_stack() -> list[tuple[str, Callable, int]]:
    """Get Turkish exam specific middleware stack"""
    return [
        ("exam_security", create_exam_security_middleware(), 200),
        ("exam_session", create_exam_session_middleware(), 300),
        ("turkish_language", create_turkish_language_middleware(), 900),
    ]


def configure_exam_middleware(exam_type: str) -> dict[str, Any]:
    """Configure middleware for specific exam type"""
    base_config = {
        "exam_monitoring": True,
        "anti_cheat_enabled": True,
        "session_timeout_minutes": 240,
    }

    if exam_type.lower() == "tyt":
        base_config.update(
            {"session_timeout_minutes": 135, "max_daily_attempts": 3}  # TYT duration
        )
    elif exam_type.lower() == "ayt":
        base_config.update(
            {"session_timeout_minutes": 180, "max_daily_attempts": 2}  # AYT duration
        )

    return base_config
