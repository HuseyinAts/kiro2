#!/usr/bin/env python3
"""
External Service Integration Validation Script
Tests connections to external APIs and services
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ExternalServiceValidator:
    def __init__(self):
        self.results = {
            "youtube": {},
            "khan_academy": {},
            "eba_tv": {},
            "openai": {},
            "zemberek": {},
            "other_services": []
        }
        self.timeout = 10  # seconds
    
    def test_youtube_api(self) -> Dict:
        """YouTube Data API v3 bağlantısını test et"""
        print("\n🔍 YouTube API test ediliyor...")
        
        api_key = os.getenv('YOUTUBE_API_KEY', '')
        
        if not api_key:
            print("⚠️  YOUTUBE_API_KEY environment variable bulunamadı")
            return {
                "status": "⚠️  Not Configured",
                "message": "API key bulunamadı",
                "response_time": None
            }
        
        try:
            start_time = time.time()
            
            # Test query - search for educational content
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": "matematik dersi",
                "type": "video",
                "maxResults": 1,
                "key": api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response_time = round((time.time() - start_time) * 1000, 2)  # ms
            
            if response.status_code == 200:
                data = response.json()
                video_count = len(data.get('items', []))
                
                print(f"✅ YouTube API çalışıyor ({response_time}ms)")
                return {
                    "status": "✅ Connected",
                    "response_time": response_time,
                    "test_query": "matematik dersi",
                    "results_found": video_count,
                    "quota_used": True
                }
            elif response.status_code == 403:
                print(f"❌ YouTube API quota aşıldı veya key geçersiz")
                return {
                    "status": "❌ Quota Exceeded or Invalid Key",
                    "response_time": response_time,
                    "error": response.json().get('error', {}).get('message', 'Unknown error')
                }
            else:
                print(f"❌ YouTube API hatası: {response.status_code}")
                return {
                    "status": f"❌ Error {response.status_code}",
                    "response_time": response_time,
                    "error": response.text
                }
        
        except requests.Timeout:
            print(f"❌ YouTube API timeout ({self.timeout}s)")
            return {
                "status": "❌ Timeout",
                "message": f"API {self.timeout} saniye içinde yanıt vermedi"
            }
        except Exception as e:
            print(f"❌ YouTube API test hatası: {e}")
            return {
                "status": "❌ Error",
                "error": str(e)
            }
    
    def test_khan_academy_api(self) -> Dict:
        """Khan Academy API bağlantısını test et"""
        print("\n🔍 Khan Academy API test ediliyor...")
        
        # Khan Academy public API endpoint
        try:
            start_time = time.time()
            
            # Test with topic tree endpoint
            url = "https://www.khanacademy.org/api/v1/topictree"
            
            response = requests.get(url, timeout=self.timeout)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                print(f"✅ Khan Academy API çalışıyor ({response_time}ms)")
                return {
                    "status": "✅ Connected",
                    "response_time": response_time,
                    "endpoint": url
                }
            else:
                print(f"⚠️  Khan Academy API yanıt verdi ama beklenmeyen status: {response.status_code}")
                return {
                    "status": f"⚠️  Status {response.status_code}",
                    "response_time": response_time
                }
        
        except requests.Timeout:
            print(f"❌ Khan Academy API timeout ({self.timeout}s)")
            return {
                "status": "❌ Timeout",
                "message": f"API {self.timeout} saniye içinde yanıt vermedi"
            }
        except Exception as e:
            print(f"❌ Khan Academy API test hatası: {e}")
            return {
                "status": "❌ Error",
                "error": str(e)
            }
    
    def test_eba_tv_api(self) -> Dict:
        """EBA TV API bağlantısını test et"""
        print("\n🔍 EBA TV API test ediliyor...")
        
        # EBA TV endpoint (MEB)
        try:
            start_time = time.time()
            
            # EBA TV ana sayfası (API endpoint'i public değil, ana sayfa kontrolü)
            url = "https://www.eba.gov.tr"
            
            response = requests.get(url, timeout=self.timeout, allow_redirects=True)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                print(f"✅ EBA TV erişilebilir ({response_time}ms)")
                return {
                    "status": "✅ Accessible",
                    "response_time": response_time,
                    "note": "EBA TV API public değil, ana sayfa kontrolü yapıldı"
                }
            else:
                print(f"⚠️  EBA TV erişim sorunu: {response.status_code}")
                return {
                    "status": f"⚠️  Status {response.status_code}",
                    "response_time": response_time
                }
        
        except requests.Timeout:
            print(f"❌ EBA TV timeout ({self.timeout}s)")
            return {
                "status": "❌ Timeout",
                "message": f"Site {self.timeout} saniye içinde yanıt vermedi"
            }
        except Exception as e:
            print(f"❌ EBA TV test hatası: {e}")
            return {
                "status": "❌ Error",
                "error": str(e)
            }
    
    def test_openai_api(self) -> Dict:
        """OpenAI API bağlantısını test et"""
        print("\n🔍 OpenAI API test ediliyor...")
        
        api_key = os.getenv('OPENAI_API_KEY', '')
        
        if not api_key:
            print("⚠️  OPENAI_API_KEY environment variable bulunamadı")
            return {
                "status": "⚠️  Not Configured",
                "message": "API key bulunamadı"
            }
        
        try:
            start_time = time.time()
            
            # Test with models endpoint (lightweight)
            url = "https://api.openai.com/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get('data', []))
                
                print(f"✅ OpenAI API çalışıyor ({response_time}ms)")
                return {
                    "status": "✅ Connected",
                    "response_time": response_time,
                    "models_available": model_count
                }
            elif response.status_code == 401:
                print(f"❌ OpenAI API key geçersiz")
                return {
                    "status": "❌ Invalid API Key",
                    "response_time": response_time
                }
            else:
                print(f"❌ OpenAI API hatası: {response.status_code}")
                return {
                    "status": f"❌ Error {response.status_code}",
                    "response_time": response_time,
                    "error": response.text
                }
        
        except requests.Timeout:
            print(f"❌ OpenAI API timeout ({self.timeout}s)")
            return {
                "status": "❌ Timeout",
                "message": f"API {self.timeout} saniye içinde yanıt vermedi"
            }
        except Exception as e:
            print(f"❌ OpenAI API test hatası: {e}")
            return {
                "status": "❌ Error",
                "error": str(e)
            }
    
    def test_zemberek_nlp(self) -> Dict:
        """Zemberek NLP servis bağlantısını test et"""
        print("\n🔍 Zemberek NLP servisi test ediliyor...")
        
        # Zemberek genellikle local service olarak çalışır
        zemberek_url = os.getenv('ZEMBEREK_URL', 'http://localhost:8080')
        
        try:
            start_time = time.time()
            
            # Health check endpoint (varsayılan)
            url = f"{zemberek_url}/health"
            
            response = requests.get(url, timeout=self.timeout)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                print(f"✅ Zemberek NLP servisi çalışıyor ({response_time}ms)")
                return {
                    "status": "✅ Connected",
                    "response_time": response_time,
                    "url": zemberek_url
                }
            else:
                print(f"⚠️  Zemberek NLP yanıt verdi ama beklenmeyen status: {response.status_code}")
                return {
                    "status": f"⚠️  Status {response.status_code}",
                    "response_time": response_time
                }
        
        except requests.ConnectionError:
            print(f"❌ Zemberek NLP servisine bağlanılamadı ({zemberek_url})")
            return {
                "status": "❌ Not Running",
                "message": "Servis çalışmıyor veya erişilemiyor",
                "url": zemberek_url
            }
        except requests.Timeout:
            print(f"❌ Zemberek NLP timeout ({self.timeout}s)")
            return {
                "status": "❌ Timeout",
                "message": f"Servis {self.timeout} saniye içinde yanıt vermedi"
            }
        except Exception as e:
            print(f"❌ Zemberek NLP test hatası: {e}")
            return {
                "status": "❌ Error",
                "error": str(e)
            }
    
    def test_other_services(self) -> List[Dict]:
        """Diğer servisleri test et"""
        print("\n🔍 Diğer servisler test ediliyor...")
        
        other_services = []
        
        # Wikipedia API
        try:
            start_time = time.time()
            url = "https://tr.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": "matematik",
                "srlimit": 1
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                print(f"✅ Wikipedia API çalışıyor ({response_time}ms)")
                other_services.append({
                    "name": "Wikipedia API",
                    "status": "✅ Connected",
                    "response_time": response_time
                })
            else:
                print(f"⚠️  Wikipedia API sorun: {response.status_code}")
                other_services.append({
                    "name": "Wikipedia API",
                    "status": f"⚠️  Status {response.status_code}",
                    "response_time": response_time
                })
        except Exception as e:
            print(f"❌ Wikipedia API test hatası: {e}")
            other_services.append({
                "name": "Wikipedia API",
                "status": "❌ Error",
                "error": str(e)
            })
        
        return other_services
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 External Service Integration Tests başlatılıyor...\n")
        print("="*60)
        
        # YouTube API
        self.results['youtube'] = self.test_youtube_api()
        
        # Khan Academy API
        self.results['khan_academy'] = self.test_khan_academy_api()
        
        # EBA TV API
        self.results['eba_tv'] = self.test_eba_tv_api()
        
        # OpenAI API
        self.results['openai'] = self.test_openai_api()
        
        # Zemberek NLP
        self.results['zemberek'] = self.test_zemberek_nlp()
        
        # Other services
        self.results['other_services'] = self.test_other_services()
    
    def generate_report(self, output_file: str = "external_services_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        # Summary hesapla
        services = [
            self.results['youtube'],
            self.results['khan_academy'],
            self.results['eba_tv'],
            self.results['openai'],
            self.results['zemberek']
        ] + self.results['other_services']
        
        connected = sum(1 for s in services if '✅' in s.get('status', ''))
        not_configured = sum(1 for s in services if '⚠️  Not Configured' in s.get('status', ''))
        errors = sum(1 for s in services if '❌' in s.get('status', ''))
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": len(services),
                "connected": connected,
                "not_configured": not_configured,
                "errors": errors,
                "health_score": round((connected / len(services)) * 100, 2) if services else 0
            },
            "services": self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapor kaydedildi: {output_file}")
        return report
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 EXTERNAL SERVICES VALIDATION SUMMARY")
        print("="*60)
        
        services = [
            ("YouTube API", self.results['youtube']),
            ("Khan Academy API", self.results['khan_academy']),
            ("EBA TV", self.results['eba_tv']),
            ("OpenAI API", self.results['openai']),
            ("Zemberek NLP", self.results['zemberek'])
        ]
        
        for name, result in services:
            status = result.get('status', '❌ Unknown')
            response_time = result.get('response_time')
            
            print(f"\n{name}:")
            print(f"  Status: {status}")
            if response_time:
                print(f"  Response Time: {response_time}ms")
        
        # Other services
        if self.results['other_services']:
            print(f"\nDiğer Servisler:")
            for service in self.results['other_services']:
                print(f"  {service['name']}: {service['status']}")
        
        # Health score
        services_list = [s[1] for s in services] + self.results['other_services']
        connected = sum(1 for s in services_list if '✅' in s.get('status', ''))
        total = len(services_list)
        health_score = round((connected / total) * 100, 2) if total else 0
        
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        print(f"✅ Bağlı: {connected}/{total}")
        
        if health_score >= 80:
            print("✅ Mükemmel! Çoğu servis çalışıyor.")
        elif health_score >= 50:
            print("⚠️  Orta seviye. Bazı servisler yapılandırılmalı.")
        else:
            print("❌ Dikkat! Çoğu servis çalışmıyor.")


def main():
    """Ana fonksiyon"""
    validator = ExternalServiceValidator()
    
    # Tüm testleri çalıştır
    validator.run_all_tests()
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")
    print("\n💡 Not: API key'leri .env dosyasında tanımlayın:")
    print("   YOUTUBE_API_KEY=your_key")
    print("   OPENAI_API_KEY=your_key")
    print("   ZEMBEREK_URL=http://localhost:8080")


if __name__ == "__main__":
    main()
