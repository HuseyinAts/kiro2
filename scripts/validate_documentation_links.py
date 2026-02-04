#!/usr/bin/env python3
"""
Documentation Links Validation Script
Validates links in README, API docs, and code comments
"""

import os
import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class DocumentationLinksValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {
            "readme_links": [],
            "api_doc_links": [],
            "code_comment_links": [],
            "broken_links": [],
            "external_links": []
        }
        self.timeout = 10
        self.tested_urls = {}  # Cache for tested URLs
    
    def extract_readme_links(self):
        """README.md içindeki link'leri çıkar"""
        print("🔍 README.md link'leri taranıyor...")
        
        readme_files = list(self.project_root.glob("**/README.md"))
        readme_files.extend(self.project_root.glob("**/readme.md"))
        
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for readme in readme_files:
            if "node_modules" in str(readme) or "venv" in str(readme):
                continue
            
            try:
                content = readme.read_text(encoding='utf-8')
                
                matches = re.finditer(link_pattern, content)
                for match in matches:
                    text = match.group(1)
                    url = match.group(2)
                    
                    self.results['readme_links'].append({
                        "text": text,
                        "url": url,
                        "file": str(readme.relative_to(self.project_root)),
                        "type": self._get_link_type(url)
                    })
            
            except Exception as e:
                print(f"⚠️  {readme} okunamadı: {e}")
        
        print(f"✅ {len(self.results['readme_links'])} README link bulundu")
        return len(self.results['readme_links'])
    
    def extract_api_doc_links(self):
        """API dokümantasyon link'lerini çıkar"""
        print("\n🔍 API dokümantasyon link'leri taranıyor...")
        
        # OpenAPI/Swagger dosyaları
        doc_patterns = [
            "**/openapi.yaml",
            "**/openapi.yml",
            "**/swagger.yaml",
            "**/swagger.yml",
            "**/api-docs.md",
            "**/API.md"
        ]
        
        link_pattern = r'(?:url|href|link):\s*["\']?([^"\'\s]+)["\']?'
        markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for pattern in doc_patterns:
            for doc_file in self.project_root.glob(pattern):
                if "node_modules" in str(doc_file) or "venv" in str(doc_file):
                    continue
                
                try:
                    content = doc_file.read_text(encoding='utf-8')
                    
                    # YAML/JSON links
                    matches = re.finditer(link_pattern, content)
                    for match in matches:
                        url = match.group(1)
                        
                        if url.startswith('http'):
                            self.results['api_doc_links'].append({
                                "url": url,
                                "file": str(doc_file.relative_to(self.project_root)),
                                "type": "external"
                            })
                    
                    # Markdown links
                    matches = re.finditer(markdown_link_pattern, content)
                    for match in matches:
                        text = match.group(1)
                        url = match.group(2)
                        
                        self.results['api_doc_links'].append({
                            "text": text,
                            "url": url,
                            "file": str(doc_file.relative_to(self.project_root)),
                            "type": self._get_link_type(url)
                        })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['api_doc_links'])} API doc link bulundu")
        return len(self.results['api_doc_links'])
    
    def extract_code_comment_links(self):
        """Code comment'lerdeki link'leri çıkar"""
        print("\n🔍 Code comment link'leri taranıyor...")
        
        # URL pattern in comments
        url_pattern = r'(?:https?://|www\.)[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        
        # File extensions to search
        extensions = ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']
        
        for ext in extensions:
            for code_file in self.project_root.rglob(ext):
                if "node_modules" in str(code_file) or "venv" in str(code_file) or "dist" in str(code_file):
                    continue
                
                try:
                    content = code_file.read_text(encoding='utf-8')
                    
                    # Extract comments
                    if ext == '*.py':
                        comment_pattern = r'#\s*(.+)$'
                    else:
                        comment_pattern = r'//\s*(.+)$|/\*\s*(.+?)\s*\*/'
                    
                    comments = re.finditer(comment_pattern, content, re.MULTILINE | re.DOTALL)
                    
                    for comment_match in comments:
                        comment_text = comment_match.group(1) or comment_match.group(2) or ''
                        
                        # Find URLs in comment
                        url_matches = re.finditer(url_pattern, comment_text)
                        for url_match in url_matches:
                            url = url_match.group(0)
                            
                            self.results['code_comment_links'].append({
                                "url": url,
                                "file": str(code_file.relative_to(self.project_root)),
                                "type": "external"
                            })
                
                except Exception as e:
                    pass
        
        print(f"✅ {len(self.results['code_comment_links'])} code comment link bulundu")
        return len(self.results['code_comment_links'])
    
    def validate_links(self, sample_size: int = 20):
        """Link'leri doğrula (sample)"""
        print(f"\n🔍 Link'ler doğrulanıyor (sample: {sample_size})...")
        
        # Tüm link'leri topla
        all_links = []
        
        for link in self.results['readme_links']:
            all_links.append(('readme', link))
        
        for link in self.results['api_doc_links']:
            all_links.append(('api_doc', link))
        
        for link in self.results['code_comment_links']:
            all_links.append(('code_comment', link))
        
        # Sample al
        import random
        if len(all_links) > sample_size:
            sample_links = random.sample(all_links, sample_size)
        else:
            sample_links = all_links
        
        tested = 0
        working = 0
        broken = 0
        
        for source, link in sample_links:
            url = link.get('url', '')
            
            # Skip non-HTTP links
            if not url.startswith('http'):
                continue
            
            # Check cache
            if url in self.tested_urls:
                result = self.tested_urls[url]
                if result['status'] == 'working':
                    working += 1
                else:
                    broken += 1
                tested += 1
                continue
            
            # Test URL
            try:
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    working += 1
                    self.tested_urls[url] = {'status': 'working'}
                    print(f"✅ {url[:60]}...")
                elif response.status_code == 405:
                    # HEAD not allowed, try GET
                    response = requests.get(url, timeout=self.timeout, allow_redirects=True, stream=True)
                    if response.status_code == 200:
                        working += 1
                        self.tested_urls[url] = {'status': 'working'}
                        print(f"✅ {url[:60]}...")
                    else:
                        broken += 1
                        self.tested_urls[url] = {'status': 'broken', 'code': response.status_code}
                        print(f"❌ {url[:60]}... (Status: {response.status_code})")
                        self.results['broken_links'].append({
                            "url": url,
                            "source": source,
                            "file": link.get('file', ''),
                            "status": f"❌ Status {response.status_code}"
                        })
                else:
                    broken += 1
                    self.tested_urls[url] = {'status': 'broken', 'code': response.status_code}
                    print(f"❌ {url[:60]}... (Status: {response.status_code})")
                    self.results['broken_links'].append({
                        "url": url,
                        "source": source,
                        "file": link.get('file', ''),
                        "status": f"❌ Status {response.status_code}"
                    })
                
                tested += 1
            
            except requests.Timeout:
                broken += 1
                self.tested_urls[url] = {'status': 'broken', 'error': 'timeout'}
                print(f"❌ {url[:60]}... (Timeout)")
                self.results['broken_links'].append({
                    "url": url,
                    "source": source,
                    "file": link.get('file', ''),
                    "status": "❌ Timeout"
                })
                tested += 1
            
            except Exception as e:
                broken += 1
                self.tested_urls[url] = {'status': 'broken', 'error': str(e)}
                print(f"❌ {url[:60]}... ({str(e)[:30]})")
                self.results['broken_links'].append({
                    "url": url,
                    "source": source,
                    "file": link.get('file', ''),
                    "status": f"❌ {str(e)[:50]}"
                })
                tested += 1
        
        print(f"\n✅ {working}/{tested} link çalışıyor")
        if broken > 0:
            print(f"❌ {broken} broken link bulundu")
        
        return working, tested
    
    def _get_link_type(self, url: str) -> str:
        """Link tipini belirle"""
        if url.startswith('http://') or url.startswith('https://'):
            return 'external'
        elif url.startswith('#'):
            return 'anchor'
        elif url.startswith('/'):
            return 'absolute'
        else:
            return 'relative'
    
    def generate_report(self, output_file: str = "documentation_links_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_readme_links": len(self.results['readme_links']),
                "total_api_doc_links": len(self.results['api_doc_links']),
                "total_code_comment_links": len(self.results['code_comment_links']),
                "broken_links": len(self.results['broken_links']),
                "tested_urls": len(self.tested_urls)
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
        if not self.tested_urls:
            return 100.0
        
        working = sum(1 for result in self.tested_urls.values() if result['status'] == 'working')
        total = len(self.tested_urls)
        
        score = (working / total) * 100 if total > 0 else 100.0
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 DOCUMENTATION LINKS VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n📄 README Links: {len(self.results['readme_links'])}")
        print(f"📚 API Doc Links: {len(self.results['api_doc_links'])}")
        print(f"💬 Code Comment Links: {len(self.results['code_comment_links'])}")
        
        print(f"\n✅ Tested URLs: {len(self.tested_urls)}")
        print(f"❌ Broken Links: {len(self.results['broken_links'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 90:
            print("✅ Mükemmel! Dokümantasyon link'leri sağlıklı.")
        elif health_score >= 70:
            print("⚠️  İyi, ancak bazı broken link'ler var.")
        else:
            print("❌ Dikkat! Çok sayıda broken link var.")
        
        # Broken link'leri göster
        if self.results['broken_links']:
            print(f"\n❌ Broken Links (İlk 10):")
            for item in self.results['broken_links'][:10]:
                print(f"  - {item['url'][:80]}")
                print(f"    Source: {item['source']}, Status: {item['status']}")


def main():
    """Ana fonksiyon"""
    print("🚀 Documentation Links Validation başlatılıyor...\n")
    
    validator = DocumentationLinksValidator()
    
    # Link'leri çıkar
    validator.extract_readme_links()
    validator.extract_api_doc_links()
    validator.extract_code_comment_links()
    
    # Link'leri doğrula (sample)
    validator.validate_links(sample_size=20)
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
