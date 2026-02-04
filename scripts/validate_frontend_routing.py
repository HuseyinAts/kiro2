#!/usr/bin/env python3
"""
Frontend Routing Validation Script
Validates React Router routes, navigation links, and component mappings
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class FrontendRoutingValidator:
    def __init__(self, frontend_root: str = "frontend"):
        self.frontend_root = Path(frontend_root)
        self.routes = []
        self.navigation_links = []
        self.components = {}
        self.results = {
            "routes": [],
            "broken_links": [],
            "missing_components": [],
            "unused_components": [],
            "deep_links": [],
            "redirect_chains": []
        }
    
    def extract_routes(self):
        """Route tanımlarını çıkar"""
        print("🔍 Route tanımları taranıyor...")
        
        # App.tsx ve diğer route dosyalarını bul
        route_files = []
        for pattern in ['**/app.tsx', '**/App.tsx', '**/routes.tsx', '**/Routes.tsx']:
            route_files.extend(self.frontend_root.glob(pattern))
        
        for route_file in route_files:
            if "node_modules" in str(route_file) or "dist" in str(route_file):
                continue
            
            try:
                content = route_file.read_text(encoding='utf-8')
                
                # <Route path="..." element={...} /> pattern
                route_pattern = r'<Route\s+path=["\']([^"\']+)["\']\s+element=\{(?:<([^>]+)>|([^}]+))\}'
                matches = re.finditer(route_pattern, content, re.MULTILINE)
                
                for match in matches:
                    path = match.group(1)
                    component = match.group(2) or match.group(3)
                    
                    # Component name'i temizle
                    if component:
                        component = component.strip().replace('<', '').replace('>', '').split()[0]
                    
                    self.routes.append({
                        "path": path,
                        "component": component,
                        "file": str(route_file.relative_to(self.frontend_root))
                    })
                    
                    self.results['routes'].append({
                        "path": path,
                        "component": component,
                        "file": str(route_file.relative_to(self.frontend_root)),
                        "status": "✅ Defined"
                    })
            
            except Exception as e:
                print(f"⚠️  {route_file} okunamadı: {e}")
        
        print(f"✅ {len(self.routes)} route tanımı bulundu")
        return len(self.routes)
    
    def extract_navigation_links(self):
        """Navigation link'lerini çıkar"""
        print("\n🔍 Navigation link'leri taranıyor...")
        
        # TypeScript/JavaScript dosyalarını tara
        extensions = ['*.ts', '*.tsx', '*.js', '*.jsx']
        for ext in extensions:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    # Navigation patterns
                    patterns = [
                        # navigate('/path')
                        r'navigate\(["\']([^"\']+)["\']\)',
                        # <Link to="/path">
                        r'<Link\s+to=["\']([^"\']+)["\']',
                        # <NavLink to="/path">
                        r'<NavLink\s+to=["\']([^"\']+)["\']',
                        # history.push('/path')
                        r'history\.push\(["\']([^"\']+)["\']\)',
                        # window.location.href = '/path'
                        r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                        # <Navigate to="/path" />
                        r'<Navigate\s+to=["\']([^"\']+)["\']'
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            path = match.group(1)
                            
                            # Template string'leri temizle
                            path = re.sub(r'\$\{[^}]+\}', ':param', path)
                            
                            # Sadece internal path'leri al (http:// ile başlamayanlar)
                            if not path.startswith('http'):
                                self.navigation_links.append({
                                    "path": path,
                                    "file": str(file.relative_to(self.frontend_root))
                                })
                
                except Exception as e:
                    pass  # Sessizce devam et
        
        print(f"✅ {len(self.navigation_links)} navigation link bulundu")
        return len(self.navigation_links)
    
    def find_components(self):
        """Component dosyalarını bul"""
        print("\n🔍 Component dosyaları taranıyor...")
        
        # Pages ve Components dizinlerini tara
        search_dirs = [
            self.frontend_root / "src" / "pages",
            self.frontend_root / "src" / "components"
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for file in search_dir.rglob("*.tsx"):
                if "node_modules" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    # Component export'larını bul
                    export_patterns = [
                        r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
                        r'export\s+\{\s*(\w+)\s*\}',
                        r'export\s+default\s+(\w+)'
                    ]
                    
                    for pattern in export_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            component_name = match.group(1)
                            self.components[component_name] = str(file.relative_to(self.frontend_root))
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.components)} component bulundu")
        return len(self.components)
    
    def validate_routes(self):
        """Route'ları doğrula"""
        print("\n🔍 Route'lar doğrulanıyor...")
        
        # Route path'lerini normalize et
        route_paths = set()
        for route in self.routes:
            path = route['path']
            # Parametreleri normalize et
            normalized = re.sub(r':[^/]+', ':param', path)
            route_paths.add(normalized)
        
        # Navigation link'lerini kontrol et
        broken_links = 0
        for link in self.navigation_links:
            path = link['path']
            
            # Parametreleri normalize et
            normalized = re.sub(r':[^/]+', ':param', path)
            
            # Route'da var mı?
            if normalized not in route_paths:
                # Partial match dene (deep link için)
                found = False
                for route_path in route_paths:
                    if self._path_matches(normalized, route_path):
                        found = True
                        break
                
                if not found:
                    broken_links += 1
                    self.results['broken_links'].append({
                        "path": path,
                        "file": link['file'],
                        "status": "❌ Route tanımı bulunamadı"
                    })
        
        print(f"✅ {len(self.navigation_links) - broken_links}/{len(self.navigation_links)} link geçerli")
        if broken_links > 0:
            print(f"❌ {broken_links} broken link bulundu")
        
        return broken_links
    
    def _path_matches(self, link_path: str, route_path: str) -> bool:
        """İki path'in eşleşip eşleşmediğini kontrol et"""
        # Exact match
        if link_path == route_path:
            return True
        
        # Wildcard match (*)
        if '*' in route_path:
            pattern = route_path.replace('*', '.*')
            if re.match(f'^{pattern}$', link_path):
                return True
        
        # Parameter match (:param)
        link_parts = link_path.split('/')
        route_parts = route_path.split('/')
        
        if len(link_parts) != len(route_parts):
            return False
        
        for link_part, route_part in zip(link_parts, route_parts):
            if route_part == ':param' or link_part == route_part:
                continue
            else:
                return False
        
        return True
    
    def check_component_mapping(self):
        """Component mapping'i kontrol et"""
        print("\n🔍 Component mapping kontrol ediliyor...")
        
        missing_components = 0
        used_components = set()
        
        for route in self.routes:
            component = route['component']
            if component and component != 'Navigate':
                used_components.add(component)
                
                # Component dosyası var mı?
                if component not in self.components:
                    missing_components += 1
                    self.results['missing_components'].append({
                        "route": route['path'],
                        "component": component,
                        "status": "❌ Component dosyası bulunamadı"
                    })
        
        # Kullanılmayan component'leri bul
        unused_count = 0
        for component_name in self.components:
            if component_name not in used_components:
                # Page component'leri için uyarı ver
                if 'Page' in component_name or 'page' in component_name:
                    unused_count += 1
                    self.results['unused_components'].append({
                        "component": component_name,
                        "file": self.components[component_name],
                        "status": "⚠️  Route'da kullanılmıyor"
                    })
        
        print(f"✅ {len(used_components)} component route'da kullanılıyor")
        if missing_components > 0:
            print(f"❌ {missing_components} component dosyası bulunamadı")
        if unused_count > 0:
            print(f"⚠️  {unused_count} page component kullanılmıyor")
        
        return missing_components, unused_count
    
    def check_deep_links(self):
        """Deep link'leri kontrol et"""
        print("\n🔍 Deep link'ler kontrol ediliyor...")
        
        deep_link_count = 0
        for route in self.routes:
            path = route['path']
            # 3+ segment olan path'ler deep link
            if path.count('/') >= 3:
                deep_link_count += 1
                self.results['deep_links'].append({
                    "path": path,
                    "component": route['component'],
                    "status": "✅ Deep link"
                })
        
        print(f"✅ {deep_link_count} deep link bulundu")
        return deep_link_count
    
    def check_redirects(self):
        """Redirect chain'leri kontrol et"""
        print("\n🔍 Redirect'ler kontrol ediliyor...")
        
        redirects = []
        for route in self.routes:
            if route['component'] == 'Navigate':
                redirects.append(route)
                self.results['redirect_chains'].append({
                    "from": route['path'],
                    "status": "✅ Redirect tanımlı"
                })
        
        print(f"✅ {len(redirects)} redirect bulundu")
        return len(redirects)
    
    def check_404_handling(self):
        """404 sayfası handling'ini kontrol et"""
        print("\n🔍 404 handling kontrol ediliyor...")
        
        has_404 = False
        for route in self.routes:
            if route['path'] == '*' or route['path'] == '/*':
                has_404 = True
                print(f"✅ 404 catch-all route bulundu: {route['component']}")
                break
        
        if not has_404:
            print(f"⚠️  404 catch-all route bulunamadı")
        
        return has_404
    
    def generate_report(self, output_file: str = "frontend_routing_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_routes": len(self.routes),
                "total_navigation_links": len(self.navigation_links),
                "total_components": len(self.components),
                "broken_links": len(self.results['broken_links']),
                "missing_components": len(self.results['missing_components']),
                "unused_components": len(self.results['unused_components']),
                "deep_links": len(self.results['deep_links']),
                "redirects": len(self.results['redirect_chains'])
            },
            "details": self.results,
            "health_score": self._calculate_health_score()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapor kaydedildi: {output_file}")
        return report
    
    def _calculate_health_score(self) -> float:
        """Sağlık skoru hesapla"""
        total_issues = (
            len(self.results['broken_links']) +
            len(self.results['missing_components'])
        )
        
        total_checks = (
            len(self.navigation_links) +
            len(self.routes)
        )
        
        if total_checks == 0:
            return 100.0
        
        score = max(0, 100 - (total_issues / total_checks * 100))
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 FRONTEND ROUTING VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n📍 Toplam Route: {len(self.routes)}")
        print(f"🔗 Toplam Navigation Link: {len(self.navigation_links)}")
        print(f"📦 Toplam Component: {len(self.components)}")
        
        print(f"\n❌ Broken Link'ler: {len(self.results['broken_links'])}")
        print(f"❌ Eksik Component'ler: {len(self.results['missing_components'])}")
        print(f"⚠️  Kullanılmayan Component'ler: {len(self.results['unused_components'])}")
        print(f"✅ Deep Link'ler: {len(self.results['deep_links'])}")
        print(f"✅ Redirect'ler: {len(self.results['redirect_chains'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 90:
            print("✅ Mükemmel! Routing yapısı sağlıklı.")
        elif health_score >= 70:
            print("⚠️  İyi, ancak bazı iyileştirmeler gerekli.")
        else:
            print("❌ Dikkat! Ciddi sorunlar var, inceleme gerekli.")
        
        # Detaylı sorunları göster
        if self.results['broken_links']:
            print("\n❌ Broken Link'ler (İlk 10):")
            for item in self.results['broken_links'][:10]:
                print(f"  - {item['path']}")
                print(f"    Dosya: {item['file']}")
        
        if self.results['missing_components']:
            print("\n❌ Eksik Component'ler:")
            for item in self.results['missing_components']:
                print(f"  - {item['component']} (Route: {item['route']})")
        
        if self.results['unused_components']:
            print(f"\n⚠️  Kullanılmayan Page Component'ler (İlk 5):")
            for item in self.results['unused_components'][:5]:
                print(f"  - {item['component']}")
                print(f"    Dosya: {item['file']}")


def main():
    """Ana fonksiyon"""
    print("🚀 Frontend Routing Validation başlatılıyor...\n")
    
    validator = FrontendRoutingValidator()
    
    # Route'ları çıkar
    validator.extract_routes()
    
    # Navigation link'lerini çıkar
    validator.extract_navigation_links()
    
    # Component'leri bul
    validator.find_components()
    
    # Route'ları doğrula
    validator.validate_routes()
    
    # Component mapping'i kontrol et
    validator.check_component_mapping()
    
    # Deep link'leri kontrol et
    validator.check_deep_links()
    
    # Redirect'leri kontrol et
    validator.check_redirects()
    
    # 404 handling'i kontrol et
    validator.check_404_handling()
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
