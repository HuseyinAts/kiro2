"""
KIRO2 Unified Integration Framework
Comprehensive third-party service integration system for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Birleşik Entegrasyon Framework
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
import hashlib
import base64
from pathlib import Path
import aiohttp
import asyncpg
import aiofiles
from collections import defaultdict, deque
import statistics
import time
from functools import wraps
import ssl
import hmac
import jwt
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.INTEGRATION)
config = get_unified_config()


class IntegrationType(Enum):
    """Types of third-party integrations"""
    GOVERNMENT_API = "government_api"      # MEB, YÖK, ÖSYM
    EDUCATION_SYSTEM = "education_system" # University systems
    PAYMENT_GATEWAY = "payment_gateway"   # Payment processors
    COMMUNICATION = "communication"       # SMS, Email providers
    AUTHENTICATION = "authentication"     # OAuth, SAML providers
    CONTENT_PROVIDER = "content_provider" # Educational content
    ANALYTICS = "analytics"               # Analytics services
    MONITORING = "monitoring"             # External monitoring


class AuthMethod(Enum):
    """Authentication methods for integrations"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    BASIC_AUTH = "basic_auth"
    CERTIFICATE = "certificate"
    HMAC = "hmac"
    CUSTOM = "custom"


class DataFormat(Enum):
    """Data exchange formats"""
    JSON = "json"
    XML = "xml"
    SOAP = "soap"
    CSV = "csv"
    FORM_DATA = "form_data"
    BINARY = "binary"


class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION_FAILED = "authentication_failed"


class SyncDirection(Enum):
    """Data synchronization direction"""
    PULL = "pull"          # Pull data from external system
    PUSH = "push"          # Push data to external system
    BIDIRECTIONAL = "bidirectional"  # Both directions


@dataclass
class IntegrationCredentials:
    """Integration authentication credentials"""
    credential_id: str
    auth_method: AuthMethod
    
    # Basic credentials
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # OAuth2 credentials
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    
    # JWT credentials
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # Certificate credentials
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    
    # Custom headers
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Security settings
    encrypted: bool = True
    rotation_interval_days: int = 90
    last_rotated: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.credential_id:
            self.credential_id = str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        """Check if credentials are expired"""
        if self.auth_method == AuthMethod.OAUTH2 and self.token_expiry:
            return datetime.now(timezone.utc) > self.token_expiry
        
        if self.last_rotated and self.rotation_interval_days > 0:
            rotation_due = self.last_rotated + timedelta(days=self.rotation_interval_days)
            return datetime.now(timezone.utc) > rotation_due
        
        return False
    
    def needs_refresh(self) -> bool:
        """Check if OAuth2 token needs refresh"""
        if self.auth_method == AuthMethod.OAUTH2 and self.token_expiry:
            # Refresh 5 minutes before expiry
            refresh_time = self.token_expiry - timedelta(minutes=5)
            return datetime.now(timezone.utc) > refresh_time
        
        return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers"""
        headers = self.custom_headers.copy()
        
        if self.auth_method == AuthMethod.API_KEY:
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        elif self.auth_method == AuthMethod.BASIC_AUTH:
            if self.username and self.password:
                credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        elif self.auth_method == AuthMethod.OAUTH2:
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
        
        elif self.auth_method == AuthMethod.JWT:
            if self.jwt_secret:
                payload = {
                    "iss": "kiro2",
                    "iat": int(time.time()),
                    "exp": int(time.time()) + (self.jwt_expiry_hours * 3600)
                }
                token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def generate_hmac_signature(self, data: str, timestamp: str = None) -> str:
        """Generate HMAC signature for request"""
        if not self.secret_key:
            raise ValueError("Secret key required for HMAC signature")
        
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        message = f"{timestamp}{data}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature


@dataclass
class IntegrationEndpoint:
    """Integration endpoint configuration"""
    endpoint_id: str
    integration_id: str
    endpoint_url: str
    http_method: str = "GET"
    
    # Data format
    request_format: DataFormat = DataFormat.JSON
    response_format: DataFormat = DataFormat.JSON
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: int = 1
    exponential_backoff: bool = True
    
    # Timeout configuration
    connection_timeout: int = 30
    read_timeout: int = 60
    
    # Request transformation
    request_mapping: Dict[str, Any] = field(default_factory=dict)
    response_mapping: Dict[str, Any] = field(default_factory=dict)
    
    # Validation
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    
    # Turkish education specific
    meb_compliance: bool = False
    yok_integration: bool = False
    osym_compatible: bool = False
    
    def __post_init__(self):
        if not self.endpoint_id:
            self.endpoint_id = str(uuid.uuid4())
    
    def build_url(self, path_params: Dict[str, Any] = None, query_params: Dict[str, Any] = None) -> str:
        """Build complete URL with parameters"""
        url = self.endpoint_url
        
        # Replace path parameters
        if path_params:
            for key, value in path_params.items():
                url = url.replace(f"{{{key}}}", str(value))
        
        # Add query parameters
        if query_params:
            url += "?" + urlencode(query_params)
        
        return url
    
    def transform_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform request data based on mapping"""
        if not self.request_mapping:
            return data
        
        transformed = {}
        for source_key, target_key in self.request_mapping.items():
            if source_key in data:
                if isinstance(target_key, str):
                    transformed[target_key] = data[source_key]
                elif isinstance(target_key, dict):
                    # Nested mapping
                    self._apply_nested_mapping(transformed, target_key, data[source_key])
        
        return transformed
    
    def transform_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform response data based on mapping"""
        if not self.response_mapping:
            return data
        
        transformed = {}
        for source_key, target_key in self.response_mapping.items():
            if source_key in data:
                if isinstance(target_key, str):
                    transformed[target_key] = data[source_key]
                elif isinstance(target_key, dict):
                    self._apply_nested_mapping(transformed, target_key, data[source_key])
        
        return transformed
    
    def _apply_nested_mapping(self, target: Dict[str, Any], mapping: Dict[str, Any], value: Any) -> None:
        """Apply nested field mapping"""
        for map_key, map_value in mapping.items():
            if isinstance(map_value, dict):
                if map_key not in target:
                    target[map_key] = {}
                self._apply_nested_mapping(target[map_key], map_value, value)
            else:
                target[map_key] = value


@dataclass
class IntegrationConfiguration:
    """Complete integration configuration"""
    integration_id: str
    integration_name: str
    integration_type: IntegrationType
    provider_name: str
    
    # Basic settings
    base_url: str
    enabled: bool = True
    priority: int = 1  # 1-10, higher = more important
    
    # Authentication
    credentials: IntegrationCredentials
    
    # Endpoints
    endpoints: Dict[str, IntegrationEndpoint] = field(default_factory=dict)
    
    # Synchronization settings
    sync_enabled: bool = True
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes: int = 60
    last_sync: Optional[datetime] = None
    
    # Error handling
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 300  # 5 minutes
    
    # Monitoring
    health_check_enabled: bool = True
    health_check_interval: int = 300  # 5 minutes
    health_check_endpoint: str = "/health"
    
    # Turkish compliance
    meb_registered: bool = False
    kvkk_compliant: bool = True
    data_residency_turkey: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if not self.integration_id:
            self.integration_id = str(uuid.uuid4())
    
    def add_endpoint(self, endpoint: IntegrationEndpoint) -> None:
        """Add endpoint to integration"""
        endpoint.integration_id = self.integration_id
        self.endpoints[endpoint.endpoint_id] = endpoint
    
    def get_endpoint(self, endpoint_id: str) -> Optional[IntegrationEndpoint]:
        """Get endpoint by ID"""
        return self.endpoints.get(endpoint_id)
    
    def is_healthy(self) -> bool:
        """Check if integration is healthy"""
        return (
            self.enabled and
            not self.credentials.is_expired() and
            len(self.endpoints) > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "integration_id": self.integration_id,
            "integration_name": self.integration_name,
            "integration_type": self.integration_type.value,
            "provider_name": self.provider_name,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "priority": self.priority,
            "sync_settings": {
                "enabled": self.sync_enabled,
                "direction": self.sync_direction.value,
                "interval_minutes": self.sync_interval_minutes,
                "last_sync": self.last_sync.isoformat() if self.last_sync else None
            },
            "compliance": {
                "meb_registered": self.meb_registered,
                "kvkk_compliant": self.kvkk_compliant,
                "data_residency_turkey": self.data_residency_turkey
            },
            "endpoints_count": len(self.endpoints),
            "health_status": self.is_healthy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RateLimiter:
    """Rate limiting for API integrations"""
    
    def __init__(self):
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_until: Dict[str, datetime] = {}
    
    async def check_rate_limit(
        self,
        integration_id: str,
        endpoint_id: str,
        per_minute_limit: int,
        per_hour_limit: int = None,
        per_day_limit: int = None
    ) -> bool:
        """Check if request is within rate limits"""
        
        key = f"{integration_id}:{endpoint_id}"
        now = datetime.now(timezone.utc)
        
        # Check if temporarily blocked
        if key in self.blocked_until and now < self.blocked_until[key]:
            return False
        
        # Clean old requests
        await self._clean_old_requests(key, now)
        
        requests = self.request_counts[key]
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_requests = sum(1 for req_time in requests if req_time > minute_ago)
        
        if recent_requests >= per_minute_limit:
            # Block for 1 minute
            self.blocked_until[key] = now + timedelta(minutes=1)
            logger.warning(f"Rate limit exceeded for {key}: {recent_requests}/{per_minute_limit} per minute")
            return False
        
        # Check per-hour limit
        if per_hour_limit:
            hour_ago = now - timedelta(hours=1)
            hour_requests = sum(1 for req_time in requests if req_time > hour_ago)
            
            if hour_requests >= per_hour_limit:
                self.blocked_until[key] = now + timedelta(minutes=5)  # Block for 5 minutes
                logger.warning(f"Hourly rate limit exceeded for {key}: {hour_requests}/{per_hour_limit}")
                return False
        
        # Check per-day limit
        if per_day_limit:
            day_ago = now - timedelta(days=1)
            day_requests = sum(1 for req_time in requests if req_time > day_ago)
            
            if day_requests >= per_day_limit:
                # Block until tomorrow
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                self.blocked_until[key] = tomorrow
                logger.warning(f"Daily rate limit exceeded for {key}: {day_requests}/{per_day_limit}")
                return False
        
        # Record this request
        requests.append(now)
        return True
    
    async def _clean_old_requests(self, key: str, current_time: datetime) -> None:
        """Clean old request records"""
        requests = self.request_counts[key]
        cutoff_time = current_time - timedelta(days=1)  # Keep 1 day of history
        
        while requests and requests[0] < cutoff_time:
            requests.popleft()


class CircuitBreaker:
    """Circuit breaker for integration fault tolerance"""
    
    def __init__(self):
        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.last_failure_time: Dict[str, datetime] = {}
        self.circuit_state: Dict[str, str] = defaultdict(lambda: "closed")  # closed, open, half-open
        self.success_counts: Dict[str, int] = defaultdict(int)
    
    async def call_with_circuit_breaker(
        self,
        integration_id: str,
        threshold: int,
        timeout_seconds: int,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """Execute function with circuit breaker protection"""
        
        key = f"{integration_id}"
        current_state = self.circuit_state[key]
        
        # Check circuit state
        if current_state == "open":
            # Check if timeout has passed
            if key in self.last_failure_time:
                time_since_failure = (datetime.now(timezone.utc) - self.last_failure_time[key]).total_seconds()
                if time_since_failure >= timeout_seconds:
                    # Move to half-open state
                    self.circuit_state[key] = "half-open"
                    logger.info(f"Circuit breaker {key} moved to half-open state")
                else:
                    # Still in timeout
                    return False, {"error": "Circuit breaker open", "state": "open"}
        
        try:
            # Execute function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Success - reset failure count
            self.failure_counts[key] = 0
            self.success_counts[key] += 1
            
            if current_state == "half-open":
                # Move back to closed state after successful call
                self.circuit_state[key] = "closed"
                logger.info(f"Circuit breaker {key} closed after successful call")
            
            return True, result
            
        except Exception as e:
            # Failure
            self.failure_counts[key] += 1
            self.last_failure_time[key] = datetime.now(timezone.utc)
            
            logger.error(f"Circuit breaker {key} failure #{self.failure_counts[key]}: {e}")
            
            # Check if threshold exceeded
            if self.failure_counts[key] >= threshold:
                self.circuit_state[key] = "open"
                logger.warning(f"Circuit breaker {key} opened after {self.failure_counts[key]} failures")
            
            return False, {"error": str(e), "state": self.circuit_state[key], "failures": self.failure_counts[key]}


class IntegrationClient:
    """HTTP client for integration requests"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()
        
        # Request statistics
        self.request_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_request_time": None
        })
    
    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes total timeout
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": "KIRO2-Integration/1.0"}
            )
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def make_request(
        self,
        integration: IntegrationConfiguration,
        endpoint: IntegrationEndpoint,
        data: Dict[str, Any] = None,
        path_params: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Make HTTP request to integration endpoint"""
        
        if not self.session:
            await self.initialize()
        
        key = f"{integration.integration_id}:{endpoint.endpoint_id}"
        start_time = time.time()
        
        try:
            # Check rate limits
            rate_check = await self.rate_limiter.check_rate_limit(
                integration.integration_id,
                endpoint.endpoint_id,
                endpoint.rate_limit_per_minute,
                endpoint.rate_limit_per_hour,
                endpoint.rate_limit_per_day
            )
            
            if not rate_check:
                return False, {"error": "Rate limit exceeded"}
            
            # Use circuit breaker
            success, result = await self.circuit_breaker.call_with_circuit_breaker(
                integration.integration_id,
                integration.circuit_breaker_threshold,
                integration.circuit_breaker_timeout,
                self._execute_request,
                integration,
                endpoint,
                data,
                path_params,
                query_params
            )
            
            # Update statistics
            response_time = time.time() - start_time
            await self._update_request_stats(key, success, response_time)
            
            return success, result
            
        except Exception as e:
            response_time = time.time() - start_time
            await self._update_request_stats(key, False, response_time)
            
            logger.error(f"Request failed for {key}: {e}")
            return False, {"error": str(e)}
    
    async def _execute_request(
        self,
        integration: IntegrationConfiguration,
        endpoint: IntegrationEndpoint,
        data: Dict[str, Any] = None,
        path_params: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute the actual HTTP request"""
        
        # Build URL
        url = endpoint.build_url(path_params, query_params)
        
        # Get authentication headers
        headers = integration.credentials.get_auth_headers()
        headers["Content-Type"] = self._get_content_type(endpoint.request_format)
        
        # Transform request data
        if data:
            data = endpoint.transform_request_data(data)
        
        # Prepare request body
        request_body = await self._prepare_request_body(data, endpoint.request_format)
        
        # Add HMAC signature if required
        if integration.credentials.auth_method == AuthMethod.HMAC:
            timestamp = str(int(time.time()))
            signature = integration.credentials.generate_hmac_signature(
                request_body if isinstance(request_body, str) else json.dumps(request_body),
                timestamp
            )
            headers["X-Timestamp"] = timestamp
            headers["X-Signature"] = signature
        
        # Make request with retries
        for attempt in range(endpoint.max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(
                    connect=endpoint.connection_timeout,
                    total=endpoint.read_timeout
                )
                
                async with self.session.request(
                    method=endpoint.http_method.upper(),
                    url=url,
                    headers=headers,
                    data=request_body,
                    timeout=timeout
                ) as response:
                    
                    # Handle response
                    response_data = await self._process_response(response, endpoint)
                    
                    if response.status < 400:
                        # Success
                        return endpoint.transform_response_data(response_data)
                    else:
                        # HTTP error
                        error_msg = f"HTTP {response.status}: {response_data}"
                        if attempt < endpoint.max_retries:
                            logger.warning(f"Request failed (attempt {attempt + 1}), retrying: {error_msg}")
                            await self._wait_for_retry(attempt, endpoint)
                            continue
                        else:
                            raise Exception(error_msg)
                            
            except asyncio.TimeoutError:
                if attempt < endpoint.max_retries:
                    logger.warning(f"Request timeout (attempt {attempt + 1}), retrying")
                    await self._wait_for_retry(attempt, endpoint)
                    continue
                else:
                    raise Exception("Request timeout")
            
            except Exception as e:
                if attempt < endpoint.max_retries:
                    logger.warning(f"Request error (attempt {attempt + 1}), retrying: {e}")
                    await self._wait_for_retry(attempt, endpoint)
                    continue
                else:
                    raise
        
        raise Exception("Max retries exceeded")
    
    async def _prepare_request_body(self, data: Any, data_format: DataFormat) -> Any:
        """Prepare request body based on format"""
        if not data:
            return None
        
        if data_format == DataFormat.JSON:
            return json.dumps(data)
        elif data_format == DataFormat.XML:
            return self._dict_to_xml(data)
        elif data_format == DataFormat.FORM_DATA:
            return aiohttp.FormData(data)
        else:
            return data
    
    async def _process_response(self, response: aiohttp.ClientResponse, endpoint: IntegrationEndpoint) -> Any:
        """Process HTTP response based on format"""
        content_type = response.headers.get("Content-Type", "").lower()
        
        if endpoint.response_format == DataFormat.JSON or "json" in content_type:
            return await response.json()
        elif endpoint.response_format == DataFormat.XML or "xml" in content_type:
            text = await response.text()
            return self._xml_to_dict(text)
        else:
            return await response.text()
    
    def _get_content_type(self, data_format: DataFormat) -> str:
        """Get content type header for data format"""
        content_types = {
            DataFormat.JSON: "application/json",
            DataFormat.XML: "application/xml",
            DataFormat.SOAP: "text/xml",
            DataFormat.FORM_DATA: "application/x-www-form-urlencoded",
            DataFormat.CSV: "text/csv"
        }
        return content_types.get(data_format, "application/json")
    
    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = "root") -> str:
        """Convert dictionary to XML"""
        def dict_to_xml_recursive(d, root):
            for key, value in d.items():
                if isinstance(value, dict):
                    child = ET.SubElement(root, key)
                    dict_to_xml_recursive(value, child)
                elif isinstance(value, list):
                    for item in value:
                        child = ET.SubElement(root, key)
                        if isinstance(item, dict):
                            dict_to_xml_recursive(item, child)
                        else:
                            child.text = str(item)
                else:
                    child = ET.SubElement(root, key)
                    child.text = str(value)
        
        root = ET.Element(root_name)
        dict_to_xml_recursive(data, root)
        return ET.tostring(root, encoding='unicode')
    
    def _xml_to_dict(self, xml_string: str) -> Dict[str, Any]:
        """Convert XML to dictionary"""
        def xml_to_dict_recursive(element):
            result = {}
            
            for child in element:
                if len(child) == 0:
                    result[child.tag] = child.text
                else:
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(xml_to_dict_recursive(child))
                    else:
                        result[child.tag] = xml_to_dict_recursive(child)
            
            return result
        
        try:
            root = ET.fromstring(xml_string)
            return {root.tag: xml_to_dict_recursive(root)}
        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            return {"error": "Invalid XML"}
    
    async def _wait_for_retry(self, attempt: int, endpoint: IntegrationEndpoint) -> None:
        """Wait before retry with exponential backoff"""
        if endpoint.exponential_backoff:
            delay = endpoint.retry_delay_seconds * (2 ** attempt)
        else:
            delay = endpoint.retry_delay_seconds
        
        await asyncio.sleep(min(delay, 60))  # Cap at 60 seconds
    
    async def _update_request_stats(self, key: str, success: bool, response_time: float) -> None:
        """Update request statistics"""
        stats = self.request_stats[key]
        
        stats["total_requests"] += 1
        stats["last_request_time"] = datetime.now(timezone.utc).isoformat()
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        # Update average response time
        total_requests = stats["total_requests"]
        current_avg = stats["average_response_time"]
        stats["average_response_time"] = ((current_avg * (total_requests - 1)) + response_time) / total_requests


class DataSynchronizer:
    """Data synchronization between systems"""
    
    def __init__(self, client: IntegrationClient):
        self.client = client
        self.sync_jobs: Dict[str, Dict[str, Any]] = {}
        self.sync_history: deque = deque(maxlen=1000)
    
    async def schedule_sync(
        self,
        integration: IntegrationConfiguration,
        sync_config: Dict[str, Any]
    ) -> str:
        """Schedule data synchronization job"""
        
        job_id = str(uuid.uuid4())
        
        sync_job = {
            "job_id": job_id,
            "integration_id": integration.integration_id,
            "config": sync_config,
            "scheduled_at": datetime.now(timezone.utc),
            "next_run": datetime.now(timezone.utc) + timedelta(minutes=integration.sync_interval_minutes),
            "last_run": None,
            "status": "scheduled",
            "run_count": 0,
            "success_count": 0,
            "error_count": 0
        }
        
        self.sync_jobs[job_id] = sync_job
        
        logger.info(f"Scheduled sync job {job_id} for integration {integration.integration_name}")
        return job_id
    
    async def run_sync_job(self, job_id: str, integration: IntegrationConfiguration) -> Dict[str, Any]:
        """Run synchronization job"""
        
        if job_id not in self.sync_jobs:
            return {"error": f"Sync job {job_id} not found"}
        
        job = self.sync_jobs[job_id]
        start_time = time.time()
        
        try:
            job["status"] = "running"
            job["last_run"] = datetime.now(timezone.utc)
            job["run_count"] += 1
            
            sync_config = job["config"]
            sync_direction = sync_config.get("direction", integration.sync_direction.value)
            
            result = {
                "job_id": job_id,
                "started_at": job["last_run"].isoformat(),
                "direction": sync_direction,
                "records_processed": 0,
                "errors": []
            }
            
            if sync_direction in ["pull", "bidirectional"]:
                pull_result = await self._pull_data(integration, sync_config)
                result["pull_result"] = pull_result
                result["records_processed"] += pull_result.get("records", 0)
            
            if sync_direction in ["push", "bidirectional"]:
                push_result = await self._push_data(integration, sync_config)
                result["push_result"] = push_result
                result["records_processed"] += push_result.get("records", 0)
            
            # Update job status
            job["status"] = "completed"
            job["success_count"] += 1
            
            execution_time = time.time() - start_time
            result["execution_time_seconds"] = execution_time
            
            # Record in history
            self.sync_history.append({
                "job_id": job_id,
                "integration_id": integration.integration_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result
            })
            
            logger.info(f"Sync job {job_id} completed: {result['records_processed']} records in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            job["status"] = "failed"
            job["error_count"] += 1
            
            error_result = {
                "job_id": job_id,
                "error": str(e),
                "execution_time_seconds": time.time() - start_time
            }
            
            logger.error(f"Sync job {job_id} failed: {e}")
            return error_result
        
        finally:
            # Schedule next run
            if integration.sync_enabled:
                job["next_run"] = datetime.now(timezone.utc) + timedelta(minutes=integration.sync_interval_minutes)
    
    async def _pull_data(self, integration: IntegrationConfiguration, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Pull data from external system"""
        pull_endpoint_id = sync_config.get("pull_endpoint_id")
        if not pull_endpoint_id:
            return {"error": "No pull endpoint configured"}
        
        endpoint = integration.get_endpoint(pull_endpoint_id)
        if not endpoint:
            return {"error": f"Pull endpoint {pull_endpoint_id} not found"}
        
        try:
            success, response = await self.client.make_request(
                integration,
                endpoint,
                query_params=sync_config.get("pull_params", {})
            )
            
            if success:
                # Process and store data
                records = response.get("data", [])
                if not isinstance(records, list):
                    records = [records]
                
                # Here you would store the data in your local database
                # For now, just return the count
                
                return {
                    "success": True,
                    "records": len(records),
                    "data": records[:5]  # Sample data
                }
            else:
                return {"error": response.get("error", "Unknown error")}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _push_data(self, integration: IntegrationConfiguration, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Push data to external system"""
        push_endpoint_id = sync_config.get("push_endpoint_id")
        if not push_endpoint_id:
            return {"error": "No push endpoint configured"}
        
        endpoint = integration.get_endpoint(push_endpoint_id)
        if not endpoint:
            return {"error": f"Push endpoint {push_endpoint_id} not found"}
        
        try:
            # Get data to push (this would come from your local database)
            data_to_push = sync_config.get("push_data", [])
            
            pushed_count = 0
            errors = []
            
            for record in data_to_push:
                success, response = await self.client.make_request(
                    integration,
                    endpoint,
                    data=record
                )
                
                if success:
                    pushed_count += 1
                else:
                    errors.append(response.get("error", "Unknown error"))
            
            return {
                "success": len(errors) == 0,
                "records": pushed_count,
                "errors": errors
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        active_jobs = [job for job in self.sync_jobs.values() if job["status"] in ["scheduled", "running"]]
        completed_jobs = [job for job in self.sync_jobs.values() if job["status"] == "completed"]
        failed_jobs = [job for job in self.sync_jobs.values() if job["status"] == "failed"]
        
        return {
            "total_jobs": len(self.sync_jobs),
            "active_jobs": len(active_jobs),
            "completed_jobs": len(completed_jobs),
            "failed_jobs": len(failed_jobs),
            "recent_history": list(self.sync_history)[-10:],
            "next_scheduled": [
                {
                    "job_id": job["job_id"],
                    "integration_id": job["integration_id"],
                    "next_run": job["next_run"].isoformat()
                }
                for job in active_jobs
                if job["next_run"]
            ]
        }


class UnifiedIntegrationFramework:
    """Main integration framework manager"""
    
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfiguration] = {}
        self.client = IntegrationClient()
        self.synchronizer = DataSynchronizer(self.client)
        
        # Health monitoring
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Webhook handling
        self.webhook_handlers: Dict[str, Callable] = {}
        
        # Event logging
        self.event_history: deque = deque(maxlen=1000)
    
    async def initialize(self, config_path: Optional[str] = None) -> bool:
        """Initialize integration framework"""
        try:
            await self.client.initialize()
            
            if config_path:
                await self._load_configurations(config_path)
            
            # Start health monitoring
            await self._start_health_monitoring()
            
            # Start sync scheduler
            asyncio.create_task(self._sync_scheduler())
            
            logger.info("Unified Integration Framework initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize integration framework: {e}")
            return False
    
    async def _load_configurations(self, config_path: str) -> None:
        """Load integration configurations from file"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                async with aiofiles.open(config_file, 'r') as f:
                    config_data = json.loads(await f.read())
                
                for integration_data in config_data.get("integrations", []):
                    # Create credentials
                    cred_data = integration_data.pop("credentials", {})
                    credentials = IntegrationCredentials(**cred_data)
                    
                    # Create integration
                    integration = IntegrationConfiguration(
                        credentials=credentials,
                        **integration_data
                    )
                    
                    # Add endpoints
                    for endpoint_data in integration_data.get("endpoints", []):
                        endpoint = IntegrationEndpoint(**endpoint_data)
                        integration.add_endpoint(endpoint)
                    
                    self.add_integration(integration)
                    
            logger.info(f"Loaded {len(self.integrations)} integrations from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
    
    def add_integration(self, integration: IntegrationConfiguration) -> None:
        """Add integration configuration"""
        self.integrations[integration.integration_id] = integration
        logger.info(f"Added integration: {integration.integration_name}")
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationConfiguration]:
        """Get integration by ID"""
        return self.integrations.get(integration_id)
    
    async def call_integration(
        self,
        integration_id: str,
        endpoint_id: str,
        data: Dict[str, Any] = None,
        path_params: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Call integration endpoint"""
        
        integration = self.get_integration(integration_id)
        if not integration:
            return {"error": f"Integration {integration_id} not found"}
        
        if not integration.enabled:
            return {"error": f"Integration {integration_id} is disabled"}
        
        endpoint = integration.get_endpoint(endpoint_id)
        if not endpoint:
            return {"error": f"Endpoint {endpoint_id} not found"}
        
        # Log event
        self._log_event("integration_call", {
            "integration_id": integration_id,
            "endpoint_id": endpoint_id,
            "has_data": data is not None
        })
        
        try:
            success, result = await self.client.make_request(
                integration, endpoint, data, path_params, query_params
            )
            
            return {
                "success": success,
                "data": result,
                "integration_name": integration.integration_name,
                "endpoint_url": endpoint.endpoint_url
            }
            
        except Exception as e:
            logger.error(f"Integration call failed: {e}")
            return {"error": str(e)}
    
    async def _start_health_monitoring(self) -> None:
        """Start health monitoring for all integrations"""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())
    
    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop"""
        while True:
            try:
                for integration in self.integrations.values():
                    if integration.health_check_enabled:
                        await self._check_integration_health(integration)
                
                # Wait for next check interval
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_integration_health(self, integration: IntegrationConfiguration) -> None:
        """Check health of specific integration"""
        try:
            health_endpoint = IntegrationEndpoint(
                endpoint_id="health_check",
                integration_id=integration.integration_id,
                endpoint_url=f"{integration.base_url.rstrip('/')}{integration.health_check_endpoint}",
                http_method="GET",
                rate_limit_per_minute=10
            )
            
            success, result = await self.client.make_request(integration, health_endpoint)
            
            self.health_status[integration.integration_id] = {
                "status": "healthy" if success else "unhealthy",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "response_time": result.get("response_time", 0),
                "details": result
            }
            
            if not success:
                logger.warning(f"Integration {integration.integration_name} health check failed: {result}")
            
        except Exception as e:
            self.health_status[integration.integration_id] = {
                "status": "error",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    async def _sync_scheduler(self) -> None:
        """Background sync scheduler"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                for job in self.synchronizer.sync_jobs.values():
                    if (job["status"] == "scheduled" and 
                        job.get("next_run") and 
                        current_time >= job["next_run"]):
                        
                        integration = self.get_integration(job["integration_id"])
                        if integration and integration.sync_enabled:
                            asyncio.create_task(
                                self.synchronizer.run_sync_job(job["job_id"], integration)
                            )
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync scheduler error: {e}")
                await asyncio.sleep(60)
    
    def register_webhook_handler(self, integration_id: str, handler: Callable) -> None:
        """Register webhook handler for integration"""
        self.webhook_handlers[integration_id] = handler
        logger.info(f"Registered webhook handler for {integration_id}")
    
    async def handle_webhook(self, integration_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook"""
        if integration_id in self.webhook_handlers:
            try:
                handler = self.webhook_handlers[integration_id]
                
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(data)
                else:
                    result = handler(data)
                
                self._log_event("webhook_received", {
                    "integration_id": integration_id,
                    "data_keys": list(data.keys())
                })
                
                return {"success": True, "result": result}
                
            except Exception as e:
                logger.error(f"Webhook handler error: {e}")
                return {"error": str(e)}
        
        return {"error": f"No webhook handler for {integration_id}"}
    
    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log integration event"""
        self.event_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": event_data
        })
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        active_integrations = [i for i in self.integrations.values() if i.enabled]
        healthy_integrations = [
            i_id for i_id, health in self.health_status.items()
            if health.get("status") == "healthy"
        ]
        
        return {
            "integrations": {
                "total": len(self.integrations),
                "active": len(active_integrations),
                "healthy": len(healthy_integrations),
                "types": {
                    int_type.value: len([
                        i for i in self.integrations.values()
                        if i.integration_type == int_type
                    ])
                    for int_type in IntegrationType
                }
            },
            "sync_status": self.synchronizer.get_sync_status(),
            "client_stats": dict(self.client.request_stats),
            "recent_events": list(self.event_history)[-10:],
            "health_status": self.health_status,
            "framework_health": {
                "client_initialized": self.client.session is not None,
                "health_monitoring_active": self.health_check_task is not None and not self.health_check_task.done(),
                "total_events_logged": len(self.event_history)
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown integration framework"""
        try:
            if self.health_check_task and not self.health_check_task.done():
                self.health_check_task.cancel()
                await self.health_check_task
            
            await self.client.close()
            
            logger.info("Integration framework shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Unified Integration Framework")
    print("=" * 40)
    
    async def test_integration_framework():
        """Test integration framework"""
        
        # Create framework
        framework = UnifiedIntegrationFramework()
        
        # Initialize framework
        await framework.initialize()
        
        print("Testing integration framework...")
        
        # Create test integration (Mock MEB API)
        credentials = IntegrationCredentials(
            credential_id="meb_creds",
            auth_method=AuthMethod.API_KEY,
            api_key="test_api_key_123"
        )
        
        integration = IntegrationConfiguration(
            integration_id="meb_integration",
            integration_name="MEB Student Data API",
            integration_type=IntegrationType.GOVERNMENT_API,
            provider_name="Ministry of Education",
            base_url="https://api.meb.gov.tr",
            credentials=credentials,
            meb_registered=True,
            kvkk_compliant=True
        )
        
        # Add endpoints
        student_endpoint = IntegrationEndpoint(
            endpoint_id="get_student",
            integration_id=integration.integration_id,
            endpoint_url=f"{integration.base_url}/students/{{student_id}}",
            http_method="GET",
            response_format=DataFormat.JSON,
            meb_compliance=True
        )
        
        integration.add_endpoint(student_endpoint)
        
        # Add integration to framework
        framework.add_integration(integration)
        
        print(f"Added integration: {integration.integration_name}")
        
        # Test webhook handler
        def mock_webhook_handler(data: Dict[str, Any]) -> Dict[str, Any]:
            return {"processed": True, "data_received": len(data)}
        
        framework.register_webhook_handler("meb_integration", mock_webhook_handler)
        
        # Test webhook
        webhook_result = await framework.handle_webhook("meb_integration", {
            "student_id": "12345",
            "event": "exam_registration",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        print(f"Webhook test result: {webhook_result}")
        
        # Test synchronization
        sync_config = {
            "direction": "pull",
            "pull_endpoint_id": "get_student",
            "pull_params": {"limit": 100}
        }
        
        sync_job_id = await framework.synchronizer.schedule_sync(integration, sync_config)
        print(f"Scheduled sync job: {sync_job_id}")
        
        # Get system status
        status = framework.get_system_status()
        
        print(f"\nSystem Status:")
        print(f"Total integrations: {status['integrations']['total']}")
        print(f"Active integrations: {status['integrations']['active']}")
        print(f"Healthy integrations: {status['integrations']['healthy']}")
        
        print(f"\nIntegration types:")
        for int_type, count in status['integrations']['types'].items():
            if count > 0:
                print(f"  {int_type}: {count}")
        
        print(f"\nSync status:")
        sync_status = status['sync_status']
        print(f"  Total jobs: {sync_status['total_jobs']}")
        print(f"  Active jobs: {sync_status['active_jobs']}")
        print(f"  Completed jobs: {sync_status['completed_jobs']}")
        
        print(f"\nFramework health:")
        health = status['framework_health']
        print(f"  Client initialized: {health['client_initialized']}")
        print(f"  Health monitoring: {health['health_monitoring_active']}")
        print(f"  Events logged: {health['total_events_logged']}")
        
        # Test rate limiting and circuit breaker
        print(f"\nTesting rate limiting...")
        
        for i in range(5):
            # These would normally fail due to no actual endpoint
            result = await framework.call_integration(
                "meb_integration",
                "get_student",
                path_params={"student_id": f"test_{i}"}
            )
            print(f"  Call {i+1}: {'Success' if result.get('success') else 'Failed'}")
        
        # Cleanup
        await framework.shutdown()
        
        print("\nIntegration framework test completed!")
    
    # Run test
    asyncio.run(test_integration_framework())