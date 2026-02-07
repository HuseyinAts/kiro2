"""
Endpoint Discovery System

Bu modül, FastAPI uygulamasındaki tüm endpoint'leri otomatik olarak
keşfeder ve metadata bilgilerini toplar.
"""

import logging
from typing import List, Optional, Set

from fastapi import FastAPI
from fastapi.routing import APIRoute

from .models import EndpointMetadata

logger = logging.getLogger(__name__)


class EndpointDiscovery:
    """
    FastAPI endpoint'lerini otomatik keşfeden ve izleyen sınıf.
    
    Bu sınıf, FastAPI uygulamasındaki tüm registered endpoint'leri tarar,
    metadata bilgilerini toplar ve Redis'e kaydeder.
    
    Attributes:
        app: FastAPI uygulama instance'ı
        redis_client: Redis client (metadata storage için)
        discovered_endpoints: Keşfedilen endpoint'lerin set'i
    """
    
    def __init__(self, app: FastAPI, redis_client=None):
        """
        EndpointDiscovery sınıfını başlatır.
        
        Args:
            app: FastAPI uygulama instance'ı
            redis_client: Redis client instance'ı (opsiyonel)
        """
        self.app = app
        self.redis_client = redis_client
        self.discovered_endpoints: Set[str] = set()
        logger.info("EndpointDiscovery başlatıldı")
    
    async def discover_all_endpoints(self) -> List[EndpointMetadata]:
        """
        Tüm registered endpoint'leri keşfeder ve metadata toplar.
        
        Bu method, FastAPI app.routes listesini tarayarak tüm endpoint'leri
        bulur ve her biri için EndpointMetadata oluşturur.
        
        Returns:
            EndpointMetadata listesi
            
        Requirements:
            REQ-1.1: FastAPI uygulaması başlatıldığında tüm endpoint'leri tarar
            REQ-1.2: Her endpoint'in path, method ve handler bilgisini toplar
        """
        endpoints: List[EndpointMetadata] = []
        
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                # Her HTTP method için ayrı endpoint oluştur
                for method in route.methods:
                    endpoint_key = f"{method}:{route.path}"
                    
                    # Yeni endpoint keşfedildi mi kontrol et
                    if endpoint_key not in self.discovered_endpoints:
                        logger.info(f"Yeni endpoint keşfedildi: {endpoint_key}")
                        self.discovered_endpoints.add(endpoint_key)
                    
                    # Metadata oluştur
                    metadata = await self._extract_metadata(route, method)
                    endpoints.append(metadata)
                    
                    # Redis'e kaydet
                    if self.redis_client:
                        await self._store_metadata(metadata)
        
        logger.info(f"Toplam {len(endpoints)} endpoint keşfedildi")
        return endpoints
    
    async def _extract_metadata(
        self, 
        route: APIRoute, 
        method: str
    ) -> EndpointMetadata:
        """
        Endpoint'ten metadata bilgilerini çıkarır.
        
        Args:
            route: FastAPI APIRoute instance'ı
            method: HTTP method (GET, POST, vb.)
            
        Returns:
            EndpointMetadata instance'ı
            
        Requirements:
            REQ-1.5: Expected response time ve status code'ları kaydeder
            REQ-1.6: Authentication requirement'ı işaretler
        """
        # Handler fonksiyon adını al
        handler_name = route.endpoint.__name__ if route.endpoint else "unknown"
        
        # Authentication gereksinimi kontrolü
        requires_auth = self._check_auth_requirement(route)
        
        # Kritik endpoint kontrolü (tag'lerden veya path'ten)
        is_critical = self._check_critical_endpoint(route)
        
        # Expected status codes (route response_model'den çıkarılabilir)
        expected_status_codes = self._extract_expected_status_codes(route)
        
        metadata = EndpointMetadata(
            path=route.path,
            method=method,
            handler=handler_name,
            requires_auth=requires_auth,
            is_critical=is_critical,
            expected_status_codes=expected_status_codes
        )
        
        logger.debug(f"Metadata çıkarıldı: {metadata.path} ({metadata.method})")
        return metadata
    
    def _check_auth_requirement(self, route: APIRoute) -> bool:
        """
        Endpoint'in authentication gerektirip gerektirmediğini kontrol eder.
        
        Args:
            route: FastAPI APIRoute instance'ı
            
        Returns:
            True ise authentication gerekli, False değilse
            
        Requirements:
            REQ-1.6: Authentication requirement'ı işaretler
        """
        # Dependencies içinde auth kontrolü var mı?
        if route.dependencies:
            for dependency in route.dependencies:
                # Dependency adında 'auth', 'token', 'jwt' gibi kelimeler var mı?
                dep_str = str(dependency)
                if any(keyword in dep_str.lower() for keyword in ['auth', 'token', 'jwt', 'security']):
                    return True
        
        # Route'un kendisinde security tanımı var mı?
        if hasattr(route, 'security') and route.security:
            return True
        
        return False
    
    def _check_critical_endpoint(self, route: APIRoute) -> bool:
        """
        Endpoint'in kritik olup olmadığını kontrol eder.
        
        Kritik endpoint'ler:
        - /health, /ready gibi health check endpoint'leri
        - /api/v1/auth/* gibi authentication endpoint'leri
        - Tag'lerinde 'critical' olan endpoint'ler
        
        Args:
            route: FastAPI APIRoute instance'ı
            
        Returns:
            True ise kritik endpoint, False değilse
        """
        # Path bazlı kontrol
        critical_paths = ['/health', '/ready', '/api/v1/auth']
        if any(route.path.startswith(path) for path in critical_paths):
            return True
        
        # Tag bazlı kontrol
        if route.tags:
            if any('critical' in tag.lower() for tag in route.tags):
                return True
        
        return False
    
    def _extract_expected_status_codes(self, route: APIRoute) -> List[int]:
        """
        Endpoint'in beklenen status code'larını çıkarır.
        
        Args:
            route: FastAPI APIRoute instance'ı
            
        Returns:
            Beklenen status code listesi
        """
        # Default status codes
        status_codes = [200]
        
        # Route'un response_model'i varsa, status code'ları çıkar
        if hasattr(route, 'status_code') and route.status_code:
            status_codes = [route.status_code]
        
        # POST endpoint'leri için 201 ekle
        if 'POST' in route.methods:
            status_codes.append(201)
        
        # DELETE endpoint'leri için 204 ekle
        if 'DELETE' in route.methods:
            status_codes.append(204)
        
        return list(set(status_codes))  # Duplicate'leri kaldır
    
    async def _store_metadata(self, metadata: EndpointMetadata) -> None:
        """
        Endpoint metadata'sını Redis'e kaydeder.
        
        Args:
            metadata: EndpointMetadata instance'ı
            
        Requirements:
            REQ-1.2: Metadata bilgilerini Redis'e kaydeder
        """
        if not self.redis_client:
            return
        
        try:
            # Redis key formatı: kiro2:health:endpoints:{method}:{path}
            redis_key = f"kiro2:health:endpoints:{metadata.method}:{metadata.path}"
            
            # Metadata'yı JSON olarak kaydet
            await self.redis_client.hset(
                redis_key,
                mapping={
                    "path": metadata.path,
                    "method": metadata.method,
                    "handler": metadata.handler,
                    "requires_auth": str(metadata.requires_auth),
                    "is_critical": str(metadata.is_critical),
                    "expected_status_codes": ",".join(map(str, metadata.expected_status_codes))
                }
            )
            
            # TTL ayarla (24 saat)
            await self.redis_client.expire(redis_key, 86400)
            
            logger.debug(f"Metadata Redis'e kaydedildi: {redis_key}")
        except Exception as e:
            logger.error(f"Metadata Redis'e kaydedilemedi: {e}")
    
    async def check_new_endpoints(self) -> List[EndpointMetadata]:
        """
        Yeni eklenen endpoint'leri kontrol eder.
        
        Bu method, mevcut endpoint listesini tarayarak daha önce
        keşfedilmemiş endpoint'leri bulur.
        
        Returns:
            Yeni keşfedilen endpoint'lerin listesi
            
        Requirements:
            REQ-1.3: Yeni endpoint eklendiğinde otomatik tespit eder
        """
        new_endpoints: List[EndpointMetadata] = []
        
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    endpoint_key = f"{method}:{route.path}"
                    
                    # Daha önce keşfedilmemiş mi?
                    if endpoint_key not in self.discovered_endpoints:
                        logger.info(f"Yeni endpoint tespit edildi: {endpoint_key}")
                        self.discovered_endpoints.add(endpoint_key)
                        
                        metadata = await self._extract_metadata(route, method)
                        new_endpoints.append(metadata)
                        
                        if self.redis_client:
                            await self._store_metadata(metadata)
        
        if new_endpoints:
            logger.info(f"{len(new_endpoints)} yeni endpoint tespit edildi")
        
        return new_endpoints
    
    async def check_removed_endpoints(self) -> List[str]:
        """
        Silinen endpoint'leri kontrol eder.
        
        Bu method, daha önce keşfedilmiş ancak artık mevcut olmayan
        endpoint'leri bulur.
        
        Returns:
            Silinen endpoint key'lerinin listesi
            
        Requirements:
            REQ-1.4: Endpoint silindiğinde monitoring listesinden çıkarır
        """
        # Mevcut endpoint'leri topla
        current_endpoints: Set[str] = set()
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    endpoint_key = f"{method}:{route.path}"
                    current_endpoints.add(endpoint_key)
        
        # Silinen endpoint'leri bul
        removed_endpoints = self.discovered_endpoints - current_endpoints
        
        if removed_endpoints:
            logger.info(f"{len(removed_endpoints)} endpoint silindi")
            
            # Silinen endpoint'leri discovered_endpoints'ten çıkar
            self.discovered_endpoints -= removed_endpoints
            
            # Redis'ten de sil
            if self.redis_client:
                for endpoint_key in removed_endpoints:
                    method, path = endpoint_key.split(":", 1)
                    redis_key = f"kiro2:health:endpoints:{method}:{path}"
                    try:
                        await self.redis_client.delete(redis_key)
                        logger.debug(f"Endpoint Redis'ten silindi: {redis_key}")
                    except Exception as e:
                        logger.error(f"Endpoint Redis'ten silinemedi: {e}")
        
        return list(removed_endpoints)
    
    async def get_endpoint_metadata(
        self, 
        method: str, 
        path: str
    ) -> Optional[EndpointMetadata]:
        """
        Belirli bir endpoint'in metadata'sını getirir.
        
        Args:
            method: HTTP method
            path: Endpoint path'i
            
        Returns:
            EndpointMetadata instance'ı veya None
        """
        if not self.redis_client:
            # Redis yoksa, app.routes'tan bul
            for route in self.app.routes:
                if isinstance(route, APIRoute) and route.path == path:
                    if method in route.methods:
                        return await self._extract_metadata(route, method)
            return None
        
        try:
            redis_key = f"kiro2:health:endpoints:{method}:{path}"
            data = await self.redis_client.hgetall(redis_key)
            
            if not data:
                return None
            
            # Redis'ten gelen data'yı EndpointMetadata'ya dönüştür
            return EndpointMetadata(
                path=data.get(b"path", b"").decode(),
                method=data.get(b"method", b"").decode(),
                handler=data.get(b"handler", b"").decode(),
                requires_auth=data.get(b"requires_auth", b"False").decode() == "True",
                is_critical=data.get(b"is_critical", b"False").decode() == "True",
                expected_status_codes=[
                    int(code) 
                    for code in data.get(b"expected_status_codes", b"200").decode().split(",")
                ]
            )
        except Exception as e:
            logger.error(f"Metadata getirilemedi: {e}")
            return None
