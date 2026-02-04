#!/usr/bin/env python3
"""
API Link Validation Script
Validates all frontend-backend API endpoint connections
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class APILinkValidator:
    def __init__(self, backend_root: str = "backend", frontend_root: str = "frontend"):
        self.backend_root = Path(backend_root)
        self.frontend_root = Path(frontend_root)
        self.backend_endpoints: Dict[str, List[str]] = defaultdict(list)
        self.frontend_calls: Dict[str, List[str]] = defaultdict(list)
        self.results = {
            "matched": [],
            "unmatched_frontend": [],
            "unused_backend": [],
            "version_mismatches": [],
            "missing_implementations": []
        }
    
    def extract_backend_endpoints(self):
        """Backend'deki tüm API endpoint'lerini çıkar"""
        print("🔍 Backend endpoint'leri taranıyor...")
        
        # FastAPI route patterns
        route_patterns = [
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'APIRouter\(prefix=["\']([^"\']+)["\']'
        ]
        
        # Backend API dosyalarını tara
        api_dirs = [
            self.backend_root / "api",
            self.backend_root / "app" / "api",
            self.backend_root / "backend" / "api"
        ]
        
        for api_dir in api_dirs:
            if not api_dir.exists():
                continue
                
            for py_file in api_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                    
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # Route decorator'ları bul
                    for pattern in route_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            if len(match.groups()) == 2:
                                method, endpoint = match.groups()
                                full_endpoint = endpoint
                            else:
                                # Prefix için
                                full_endpoint = match.group(1)
                            
                            self.backend_endpoints[str(py_file)].append({
                                "endpoint": full_endpoint,
                                "method": method if len(match.groups()) == 2 else "PREFIX",
                                "file": str(py_file.relative_to(self.backend_root))
                            })
                except Exception as e:
                    print(f"⚠️  Hata: {py_file}: {e}")
        
        total_endpoints = sum(len(v) for v in self.backend_endpoints.values())
        print(f"✅ {total_endpoints} backend endpoint bulundu")
        return total_endpoints
    
    def extract_frontend_calls(self):
        """Frontend'deki tüm API çağrılarını çıkar"""
        print("\n🔍 Frontend API çağrıları taranıyor...")
        
        # API call patterns - TypeScript/JavaScript için
        call_patterns = [
            # apiClient.get('/api/v1/...') pattern
            r'apiClient\.(get|post|put|delete|patch)\s*<[^>]*>\s*\(["\']([^"\']+)["\']',
            r'apiClient\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # axios.get('/api/v1/...') pattern
            r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # fetch('/api/v1/...') pattern
            r'fetch\(["\']([^"\']+)["\']',
            # this.client.get('/api/v1/...') pattern
            r'this\.client\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # Direct API path strings in services
            r'["\']/(api/v\d+/[^"\']+)["\']',
            # Template literals with API paths
            r'`/(api/v\d+/[^`]+)`'
        ]
        
        # Frontend dosyalarını tara
        if not self.frontend_root.exists():
            print(f"⚠️  Frontend dizini bulunamadı: {self.frontend_root}")
            return 0
        
        # TypeScript ve JavaScript dosyalarını tara
        extensions = ['*.ts', '*.tsx', '*.js', '*.jsx']
        for ext in extensions:
            for ts_file in self.frontend_root.rglob(ext):
                if "node_modules" in str(ts_file) or "dist" in str(ts_file) or "dev-dist" in str(ts_file):
                    continue
                    
                try:
                    content = ts_file.read_text(encoding='utf-8')
                    
                    for pattern in call_patterns:
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            groups = match.groups()
                            
                            # Method ve endpoint'i ayıkla
                            if len(groups) == 2:
                                method, endpoint = groups
                                method = method.upper() if method else "GET"
                            elif len(groups) == 1:
                                method = "GET"
                                endpoint = groups[0]
                            else:
                                continue
                            
                            # Template string'leri ve parametreleri temizle
                            endpoint = re.sub(r'\$\{[^}]+\}', ':param', endpoint)
                            endpoint = re.sub(r'`', '', endpoint)
                            
                            # Sadece /api ile başlayanları al
                            if not endpoint.startswith('/api'):
                                endpoint = '/' + endpoint if not endpoint.startswith('/') else endpoint
                            
                            if '/api' in endpoint:
                                self.frontend_calls[str(ts_file)].append({
                                    "endpoint": endpoint,
                                    "method": method,
                                    "file": str(ts_file.relative_to(self.frontend_root))
                                })
                except Exception as e:
                    print(f"⚠️  Hata: {ts_file}: {e}")
        
        total_calls = sum(len(v) for v in self.frontend_calls.values())
        print(f"✅ {total_calls} frontend API çağrısı bulundu")
        return total_calls
    
    def normalize_endpoint(self, endpoint: str) -> str:
        """Endpoint'i normalize et (parametreleri standartlaştır)"""
        # Path parametrelerini normalize et
        normalized = re.sub(r'\{[^}]+\}', ':param', endpoint)
        normalized = re.sub(r':[^/]+', ':param', normalized)
        
        # Trailing slash'i kaldır
        normalized = normalized.rstrip('/')
        
        # API version prefix'i ekle (yoksa)
        if not normalized.startswith('/api'):
            normalized = '/api' + normalized if normalized.startswith('/') else '/api/' + normalized
        
        return normalized
    
    def match_endpoints(self):
        """Frontend ve backend endpoint'lerini eşleştir"""
        print("\n🔗 Endpoint'ler eşleştiriliyor...")
        
        # Backend endpoint'lerini normalize et
        backend_set = set()
        for endpoints in self.backend_endpoints.values():
            for ep in endpoints:
                normalized = self.normalize_endpoint(ep['endpoint'])
                backend_set.add((normalized, ep['method']))
        
        # Frontend çağrılarını normalize et ve eşleştir
        frontend_set = set()
        for calls in self.frontend_calls.values():
            for call in calls:
                normalized = self.normalize_endpoint(call['endpoint'])
                frontend_set.add((normalized, call['method']))
                
                # Backend'de eşleşme var mı?
                if (normalized, call['method']) in backend_set:
                    self.results['matched'].append({
                        "endpoint": normalized,
                        "method": call['method'],
                        "status": "✅ Matched"
                    })
                else:
                    self.results['unmatched_frontend'].append({
                        "endpoint": normalized,
                        "method": call['method'],
                        "file": call['file'],
                        "status": "❌ Backend endpoint bulunamadı"
                    })
        
        # Kullanılmayan backend endpoint'leri
        for endpoint, method in backend_set:
            if (endpoint, method) not in frontend_set:
                self.results['unused_backend'].append({
                    "endpoint": endpoint,
                    "method": method,
                    "status": "⚠️  Frontend'de kullanılmıyor"
                })
        
        print(f"✅ {len(self.results['matched'])} eşleşme bulundu")
        print(f"❌ {len(self.results['unmatched_frontend'])} frontend çağrısı backend'de yok")
        print(f"⚠️  {len(self.results['unused_backend'])} backend endpoint kullanılmıyor")
    
    def check_api_versioning(self):
        """API versiyonlama tutarlılığını kontrol et"""
        print("\n🔍 API versiyonlama kontrol ediliyor...")
        
        version_pattern = r'/api/(v\d+)/'
        versions = set()
        
        # Tüm endpoint'lerdeki versiyonları topla
        for endpoints in self.backend_endpoints.values():
            for ep in endpoints:
                match = re.search(version_pattern, ep['endpoint'])
                if match:
                    versions.add(match.group(1))
        
        for calls in self.frontend_calls.values():
            for call in calls:
                match = re.search(version_pattern, call['endpoint'])
                if match:
                    versions.add(match.group(1))
        
        if len(versions) > 1:
            self.results['version_mismatches'].append({
                "versions": list(versions),
                "status": "⚠️  Birden fazla API versiyonu kullanılıyor"
            })
            print(f"⚠️  Birden fazla API versiyonu: {', '.join(sorted(versions))}")
        elif len(versions) == 1:
            print(f"✅ Tek API versiyonu kullanılıyor: {list(versions)[0]}")
        else:
            print("⚠️  API versiyonlama kullanılmıyor")
    
    def generate_report(self, output_file: str = "api_link_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_backend_endpoints": sum(len(v) for v in self.backend_endpoints.values()),
                "total_frontend_calls": sum(len(v) for v in self.frontend_calls.values()),
                "matched": len(self.results['matched']),
                "unmatched_frontend": len(self.results['unmatched_frontend']),
                "unused_backend": len(self.results['unused_backend']),
                "version_mismatches": len(self.results['version_mismatches'])
            },
            "details": self.results,
            "health_score": self._calculate_health_score()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapor kaydedildi: {output_file}")
        return report
    
    def _calculate_health_score(self) -> float:
        """Sağlık skoru hesapla (0-100)"""
        total_frontend = sum(len(v) for v in self.frontend_calls.values())
        if total_frontend == 0:
            return 100.0
        
        matched = len(self.results['matched'])
        score = (matched / total_frontend) * 100
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 API LINK VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n✅ Eşleşen endpoint'ler: {len(self.results['matched'])}")
        print(f"❌ Eşleşmeyen frontend çağrıları: {len(self.results['unmatched_frontend'])}")
        print(f"⚠️  Kullanılmayan backend endpoint'leri: {len(self.results['unused_backend'])}")
        print(f"⚠️  Versiyon uyumsuzlukları: {len(self.results['version_mismatches'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 90:
            print("✅ Mükemmel! API bağlantıları sağlıklı.")
        elif health_score >= 70:
            print("⚠️  İyi, ancak bazı iyileştirmeler gerekli.")
        else:
            print("❌ Dikkat! Ciddi sorunlar var, inceleme gerekli.")
        
        # Detaylı sorunları göster
        if self.results['unmatched_frontend']:
            print("\n❌ Eşleşmeyen Frontend Çağrıları (İlk 10):")
            for item in self.results['unmatched_frontend'][:10]:
                print(f"  - {item['method']} {item['endpoint']}")
                print(f"    Dosya: {item['file']}")
        
        if self.results['unused_backend']:
            print("\n⚠️  Kullanılmayan Backend Endpoint'leri (İlk 10):")
            for item in self.results['unused_backend'][:10]:
                print(f"  - {item['method']} {item['endpoint']}")


def main():
    """Ana fonksiyon"""
    print("🚀 API Link Validation başlatılıyor...\n")
    
    validator = APILinkValidator()
    
    # Backend endpoint'lerini çıkar
    validator.extract_backend_endpoints()
    
    # Frontend çağrılarını çıkar
    validator.extract_frontend_calls()
    
    # Eşleştir
    validator.match_endpoints()
    
    # Versiyonlama kontrolü
    validator.check_api_versioning()
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
