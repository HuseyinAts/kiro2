#!/usr/bin/env python3
"""
Static Assets Validation Script
Validates image sources, video URLs, CSS/JS bundles, fonts, and CDN links
"""

import os
import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from urllib.parse import urlparse

class StaticAssetsValidator:
    def __init__(self, frontend_root: str = "frontend", backend_root: str = "backend"):
        self.frontend_root = Path(frontend_root)
        self.backend_root = Path(backend_root)
        self.results = {
            "images": [],
            "videos": [],
            "css_js_bundles": [],
            "fonts": [],
            "cdn_links": [],
            "broken_links": []
        }
        self.timeout = 5
    
    def extract_image_sources(self):
        """Image src link'lerini çıkar"""
        print("🔍 Image source'ları taranıyor...")
        
        image_patterns = [
            r'<img[^>]+src=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+\.(?:jpg|jpeg|png|gif|svg|webp|ico))["\']',
            r'background(?:-image)?:\s*url\(["\']?([^"\'()]+)["\']?\)',
            r'import\s+\w+\s+from\s+["\']([^"\']+\.(?:jpg|jpeg|png|gif|svg|webp))["\']'
        ]
        
        for ext in ['*.tsx', '*.ts', '*.jsx', '*.js', '*.css', '*.html']:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    for pattern in image_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            src = match.group(1)
                            
                            # Skip data URLs and placeholders
                            if src.startswith('data:') or src.startswith('${'):
                                continue
                            
                            self.results['images'].append({
                                "src": src,
                                "file": str(file.relative_to(self.frontend_root)),
                                "type": self._get_url_type(src)
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['images'])} image source bulundu")
        return len(self.results['images'])
    
    def extract_video_urls(self):
        """Video URL'lerini çıkar"""
        print("\n🔍 Video URL'leri taranıyor...")
        
        video_patterns = [
            r'<video[^>]+src=["\']([^"\']+)["\']',
            r'<source[^>]+src=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+\.(?:mp4|webm|ogg|mov))["\']',
            r'(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/)?([a-zA-Z0-9_-]+)',
            r'videoUrl:\s*["\']([^"\']+)["\']'
        ]
        
        for ext in ['*.tsx', '*.ts', '*.jsx', '*.js', '*.html']:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    for pattern in video_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            url = match.group(1)
                            
                            if url.startswith('${'):
                                continue
                            
                            self.results['videos'].append({
                                "url": url,
                                "file": str(file.relative_to(self.frontend_root)),
                                "type": self._get_url_type(url)
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['videos'])} video URL bulundu")
        return len(self.results['videos'])
    
    def extract_css_js_bundles(self):
        """CSS/JS bundle link'lerini çıkar"""
        print("\n🔍 CSS/JS bundle'ları taranıyor...")
        
        bundle_patterns = [
            r'<link[^>]+href=["\']([^"\']+\.css)["\']',
            r'<script[^>]+src=["\']([^"\']+\.js)["\']',
            r'import\s+["\']([^"\']+\.(?:css|scss|sass))["\']',
            r'import\s+.*\s+from\s+["\']([^"\']+\.js)["\']'
        ]
        
        for ext in ['*.tsx', '*.ts', '*.jsx', '*.js', '*.html']:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    for pattern in bundle_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            bundle = match.group(1)
                            
                            if bundle.startswith('${'):
                                continue
                            
                            self.results['css_js_bundles'].append({
                                "bundle": bundle,
                                "file": str(file.relative_to(self.frontend_root)),
                                "type": self._get_url_type(bundle)
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['css_js_bundles'])} CSS/JS bundle bulundu")
        return len(self.results['css_js_bundles'])
    
    def extract_font_links(self):
        """Font dosyası link'lerini çıkar"""
        print("\n🔍 Font dosyaları taranıyor...")
        
        font_patterns = [
            r'<link[^>]+href=["\']([^"\']+\.(?:woff|woff2|ttf|otf|eot))["\']',
            r'url\(["\']?([^"\'()]+\.(?:woff|woff2|ttf|otf|eot))["\']?\)',
            r'src:\s*url\(["\']?([^"\'()]+\.(?:woff|woff2|ttf|otf|eot))["\']?\)',
            r'@font-face[^}]+url\(["\']?([^"\'()]+)["\']?\)'
        ]
        
        for ext in ['*.css', '*.scss', '*.sass', '*.html']:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    for pattern in font_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            font = match.group(1)
                            
                            if font.startswith('data:'):
                                continue
                            
                            self.results['fonts'].append({
                                "font": font,
                                "file": str(file.relative_to(self.frontend_root)),
                                "type": self._get_url_type(font)
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['fonts'])} font dosyası bulundu")
        return len(self.results['fonts'])
    
    def extract_cdn_links(self):
        """CDN link'lerini çıkar"""
        print("\n🔍 CDN link'leri taranıyor...")
        
        cdn_domains = [
            'cdn.jsdelivr.net',
            'unpkg.com',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            'maxcdn.bootstrapcdn.com',
            'stackpath.bootstrapcdn.com'
        ]
        
        cdn_pattern = r'(?:href|src)=["\']([^"\']+)["\']'
        
        for ext in ['*.tsx', '*.ts', '*.jsx', '*.js', '*.html', '*.css']:
            for file in self.frontend_root.rglob(ext):
                if "node_modules" in str(file) or "dist" in str(file):
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8')
                    
                    matches = re.finditer(cdn_pattern, content)
                    for match in matches:
                        url = match.group(1)
                        
                        # CDN domain'i var mı kontrol et
                        if any(cdn in url for cdn in cdn_domains):
                            self.results['cdn_links'].append({
                                "url": url,
                                "file": str(file.relative_to(self.frontend_root)),
                                "cdn": self._get_cdn_name(url)
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['cdn_links'])} CDN link bulundu")
        return len(self.results['cdn_links'])
    
    def validate_local_assets(self):
        """Local asset'lerin varlığını kontrol et"""
        print("\n🔍 Local asset'ler doğrulanıyor...")
        
        broken_count = 0
        
        # Images
        for img in self.results['images']:
            if img['type'] == 'local':
                src = img['src']
                # Remove leading slash and resolve path
                asset_path = self.frontend_root / src.lstrip('/')
                
                if not asset_path.exists():
                    broken_count += 1
                    self.results['broken_links'].append({
                        "asset": src,
                        "type": "image",
                        "file": img['file'],
                        "status": "❌ File not found"
                    })
        
        # CSS/JS bundles
        for bundle in self.results['css_js_bundles']:
            if bundle['type'] == 'local':
                bundle_path = bundle['bundle']
                asset_path = self.frontend_root / bundle_path.lstrip('/')
                
                if not asset_path.exists():
                    broken_count += 1
                    self.results['broken_links'].append({
                        "asset": bundle_path,
                        "type": "bundle",
                        "file": bundle['file'],
                        "status": "❌ File not found"
                    })
        
        # Fonts
        for font in self.results['fonts']:
            if font['type'] == 'local':
                font_path = font['font']
                asset_path = self.frontend_root / font_path.lstrip('/')
                
                if not asset_path.exists():
                    broken_count += 1
                    self.results['broken_links'].append({
                        "asset": font_path,
                        "type": "font",
                        "file": font['file'],
                        "status": "❌ File not found"
                    })
        
        if broken_count > 0:
            print(f"❌ {broken_count} broken local asset bulundu")
        else:
            print(f"✅ Tüm local asset'ler mevcut")
        
        return broken_count
    
    def test_cdn_links(self, sample_size: int = 5):
        """CDN link'lerini test et (sample)"""
        print(f"\n🔍 CDN link'leri test ediliyor (sample: {sample_size})...")
        
        tested = 0
        working = 0
        
        for cdn_link in self.results['cdn_links'][:sample_size]:
            url = cdn_link['url']
            
            try:
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    working += 1
                    print(f"✅ {cdn_link['cdn']}: OK")
                else:
                    print(f"⚠️  {cdn_link['cdn']}: Status {response.status_code}")
                    self.results['broken_links'].append({
                        "asset": url,
                        "type": "cdn",
                        "file": cdn_link['file'],
                        "status": f"⚠️  Status {response.status_code}"
                    })
                
                tested += 1
            
            except Exception as e:
                print(f"❌ {cdn_link['cdn']}: {str(e)[:50]}")
                self.results['broken_links'].append({
                    "asset": url,
                    "type": "cdn",
                    "file": cdn_link['file'],
                    "status": f"❌ {str(e)[:50]}"
                })
                tested += 1
        
        print(f"✅ {working}/{tested} CDN link çalışıyor")
        return working, tested
    
    def _get_url_type(self, url: str) -> str:
        """URL tipini belirle (local, external, cdn)"""
        if url.startswith('http://') or url.startswith('https://'):
            return 'external'
        elif url.startswith('/'):
            return 'local'
        elif url.startswith('./') or url.startswith('../'):
            return 'relative'
        else:
            return 'local'
    
    def _get_cdn_name(self, url: str) -> str:
        """CDN adını çıkar"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if 'jsdelivr' in domain:
            return 'jsDelivr'
        elif 'unpkg' in domain:
            return 'unpkg'
        elif 'cdnjs' in domain:
            return 'cdnjs'
        elif 'googleapis' in domain:
            return 'Google Fonts'
        elif 'gstatic' in domain:
            return 'Google Static'
        elif 'bootstrapcdn' in domain:
            return 'Bootstrap CDN'
        else:
            return domain
    
    def generate_report(self, output_file: str = "static_assets_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_images": len(self.results['images']),
                "total_videos": len(self.results['videos']),
                "total_css_js_bundles": len(self.results['css_js_bundles']),
                "total_fonts": len(self.results['fonts']),
                "total_cdn_links": len(self.results['cdn_links']),
                "broken_links": len(self.results['broken_links'])
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
        total_assets = (
            len(self.results['images']) +
            len(self.results['videos']) +
            len(self.results['css_js_bundles']) +
            len(self.results['fonts']) +
            len(self.results['cdn_links'])
        )
        
        if total_assets == 0:
            return 100.0
        
        broken = len(self.results['broken_links'])
        score = max(0, 100 - (broken / total_assets * 100))
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 STATIC ASSETS VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n🖼️  Images: {len(self.results['images'])}")
        print(f"🎥 Videos: {len(self.results['videos'])}")
        print(f"📦 CSS/JS Bundles: {len(self.results['css_js_bundles'])}")
        print(f"🔤 Fonts: {len(self.results['fonts'])}")
        print(f"🌐 CDN Links: {len(self.results['cdn_links'])}")
        
        print(f"\n❌ Broken Links: {len(self.results['broken_links'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 95:
            print("✅ Mükemmel! Tüm asset'ler sağlıklı.")
        elif health_score >= 80:
            print("⚠️  İyi, ancak bazı broken link'ler var.")
        else:
            print("❌ Dikkat! Çok sayıda broken link var.")
        
        # Broken link'leri göster
        if self.results['broken_links']:
            print(f"\n❌ Broken Links (İlk 10):")
            for item in self.results['broken_links'][:10]:
                print(f"  - {item['asset']}")
                print(f"    Type: {item['type']}, Status: {item['status']}")


def main():
    """Ana fonksiyon"""
    print("🚀 Static Assets Validation başlatılıyor...\n")
    
    validator = StaticAssetsValidator()
    
    # Asset'leri çıkar
    validator.extract_image_sources()
    validator.extract_video_urls()
    validator.extract_css_js_bundles()
    validator.extract_font_links()
    validator.extract_cdn_links()
    
    # Local asset'leri doğrula
    validator.validate_local_assets()
    
    # CDN link'lerini test et (sample)
    validator.test_cdn_links(sample_size=5)
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
