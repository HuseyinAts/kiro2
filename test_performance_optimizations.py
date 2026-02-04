#!/usr/bin/env python3
"""
Performance Optimization Test Script
Teknofest 2025 - Test performance improvements
"""

import asyncio
import time
import requests
import json
from typing import Dict, List
import statistics

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_MESSAGES = [
    "LGS matematik konuları neler?",
    "Pisagor teoremi nasıl uygulanır?",
    "EBOB EKOK nasıl bulunur?",
    "Cebirsel özdeşlikler nelerdir?",
    "Geometri sorularını nasıl çözmeliyim?",
    "Öğrenme planı oluştur",
    "Quiz oluştur matematik",
    "Sınav stratejileri",
    "Flashcard oluştur",
    "LGS fen bilimleri konuları"
]

class PerformanceTester:
    """Performance testing utility"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {}
    
    def test_api_endpoint(self, endpoint: str, method: str = "GET", data: dict = None, iterations: int = 10) -> Dict:
        """Test API endpoint performance"""
        print(f"Testing {method} {endpoint} ({iterations} iterations)...")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                elif method == "POST":
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(response_time)
                else:
                    print(f"  Error {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                print(f"  Request failed: {str(e)[:100]}")
                continue
        
        if response_times:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "success_count": success_count,
                "success_rate": (success_count / iterations) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99)
            }
        else:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "success_count": 0,
                "success_rate": 0,
                "error": "No successful requests"
            }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def test_chat_performance(self, iterations: int = 20) -> Dict:
        """Test chat endpoint performance with various messages"""
        print(f"Testing chat performance ({iterations} iterations)...")
        
        all_response_times = []
        agent_stats = {"learning": [], "study": [], "exam": []}
        
        for i in range(iterations):
            message = TEST_MESSAGES[i % len(TEST_MESSAGES)]
            agent = ["learning", "study", "exam"][i % 3]
            
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "agent": agent,
                        "message": message,
                        "session_id": f"test_session_{i}"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    all_response_times.append(response_time)
                    agent_stats[agent].append(response_time)
                    
                    # Check if response contains cache hit info
                    try:
                        data = response.json()
                        print(f"  {agent}: {response_time:.0f}ms - {message[:30]}...")
                    except:
                        pass
                else:
                    print(f"  Error {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                print(f"  Request failed: {str(e)[:100]}")
                continue
        
        # Calculate overall stats
        if all_response_times:
            stats = {
                "total_requests": iterations,
                "successful_requests": len(all_response_times),
                "success_rate": (len(all_response_times) / iterations) * 100,
                "avg_response_time": statistics.mean(all_response_times),
                "min_response_time": min(all_response_times),
                "max_response_time": max(all_response_times),
                "median_response_time": statistics.median(all_response_times),
                "p95_response_time": self._percentile(all_response_times, 95),
                "p99_response_time": self._percentile(all_response_times, 99),
                "agent_performance": {}
            }
            
            # Calculate per-agent stats
            for agent, times in agent_stats.items():
                if times:
                    stats["agent_performance"][agent] = {
                        "avg_response_time": statistics.mean(times),
                        "min_response_time": min(times),
                        "max_response_time": max(times),
                        "request_count": len(times)
                    }
        else:
            stats = {"error": "No successful requests"}
        
        return stats
    
    def test_content_endpoints(self) -> Dict:
        """Test content management endpoints"""
        print("Testing content management endpoints...")
        
        endpoints_to_test = [
            ("/api/content/questions/sayilar_islemler", "GET"),
            ("/api/content/topics/sayilar_islemler", "GET"),
            ("/api/content/study-plan", "GET"),
            ("/api/content/curriculum/matematik", "GET"),
            ("/api/content/exam-strategies", "GET"),
            ("/api/content/performance-metrics", "GET"),
            ("/api/content/cache-stats", "GET")
        ]
        
        results = {}
        
        for endpoint, method in endpoints_to_test:
            try:
                stats = self.test_api_endpoint(endpoint, method, iterations=5)
                results[endpoint] = stats
            except Exception as e:
                results[endpoint] = {"error": str(e)}
        
        return results
    
    def test_rag_performance(self) -> Dict:
        """Test RAG endpoints performance"""
        print("Testing RAG endpoints...")
        
        # Test search endpoint
        search_data = {
            "query": "LGS matematik konuları",
            "k": 5
        }
        
        search_stats = self.test_api_endpoint(
            "/api/rag/search",
            "POST",
            search_data,
            iterations=10
        )
        
        # Test query with context
        query_data = {
            "query": "Pisagor teoremi nasıl uygulanır?",
            "context_size": 3
        }
        
        query_stats = self.test_api_endpoint(
            "/api/rag/query",
            "POST",
            query_data,
            iterations=10
        )
        
        return {
            "search": search_stats,
            "query_with_context": query_stats
        }
    
    def test_cache_effectiveness(self) -> Dict:
        """Test cache effectiveness by making repeated requests"""
        print("Testing cache effectiveness...")
        
        # Test same message multiple times to check caching
        test_message = "LGS matematik konuları neler?"
        
        # First request (cache miss)
        print("  First request (cache miss)...")
        first_stats = self.test_api_endpoint(
            "/api/chat",
            "POST",
            {"agent": "learning", "message": test_message},
            iterations=1
        )
        
        # Subsequent requests (should be cache hits)
        print("  Subsequent requests (cache hits)...")
        cached_stats = self.test_api_endpoint(
            "/api/chat",
            "POST",
            {"agent": "learning", "message": test_message},
            iterations=5
        )
        
        # Calculate cache improvement
        if (first_stats.get("avg_response_time") and 
            cached_stats.get("avg_response_time")):
            
            improvement = (
                (first_stats["avg_response_time"] - cached_stats["avg_response_time"]) /
                first_stats["avg_response_time"]
            ) * 100
            
            return {
                "first_request": first_stats,
                "cached_requests": cached_stats,
                "cache_improvement_percent": improvement,
                "cache_effective": improvement > 10  # Consider effective if >10% improvement
            }
        
        return {
            "first_request": first_stats,
            "cached_requests": cached_stats,
            "cache_improvement_percent": 0,
            "cache_effective": False
        }
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive performance test suite"""
        print("[ROCKET] Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        results = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url
        }
        
        try:
            # Test basic endpoints
            print("\n1. Testing Basic Endpoints...")
            results["basic_endpoints"] = {
                "health": self.test_api_endpoint("/health", iterations=5),
                "agents": self.test_api_endpoint("/api/agents", iterations=5),
                "performance_stats": self.test_api_endpoint("/api/performance/stats", iterations=3)
            }
            
            # Test chat performance
            print("\n2. Testing Chat Performance...")
            results["chat_performance"] = self.test_chat_performance(iterations=15)
            
            # Test content endpoints
            print("\n3. Testing Content Management...")
            results["content_endpoints"] = self.test_content_endpoints()
            
            # Test RAG performance
            print("\n4. Testing RAG Performance...")
            results["rag_performance"] = self.test_rag_performance()
            
            # Test cache effectiveness
            print("\n5. Testing Cache Effectiveness...")
            results["cache_effectiveness"] = self.test_cache_effectiveness()
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def print_summary(self, results: Dict):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("[CHART] PERFORMANCE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Chat performance summary
        if "chat_performance" in results:
            chat = results["chat_performance"]
            if "avg_response_time" in chat:
                print(f"\n💬 Chat Performance:")
                print(f"  Average Response Time: {chat['avg_response_time']:.0f}ms")
                print(f"  95th Percentile: {chat['p95_response_time']:.0f}ms")
                print(f"  Success Rate: {chat['success_rate']:.1f}%")
                
                # Performance rating
                avg_time = chat['avg_response_time']
                if avg_time < 500:
                    rating = "🟢 Excellent"
                elif avg_time < 1000:
                    rating = "🟡 Good"
                elif avg_time < 2000:
                    rating = "🟠 Fair"
                else:
                    rating = "🔴 Needs Improvement"
                
                print(f"  Performance Rating: {rating}")
        
        # Cache effectiveness summary
        if "cache_effectiveness" in results:
            cache = results["cache_effectiveness"]
            if cache.get("cache_improvement_percent", 0) > 0:
                print(f"\n[ROCKET] Cache Performance:")
                print(f"  Cache Improvement: {cache['cache_improvement_percent']:.1f}%")
                print(f"  Cache Effective: {'[CHECK] Yes' if cache['cache_effective'] else '[X] No'}")
        
        # Content endpoints summary
        if "content_endpoints" in results:
            content = results["content_endpoints"]
            successful_endpoints = sum(1 for ep in content.values() if "avg_response_time" in ep)
            total_endpoints = len(content)
            print(f"\n[BOOKS] Content Endpoints:")
            print(f"  Successful: {successful_endpoints}/{total_endpoints}")
            
            # Find fastest and slowest
            times = [ep["avg_response_time"] for ep in content.values() if "avg_response_time" in ep]
            if times:
                print(f"  Fastest Response: {min(times):.0f}ms")
                print(f"  Slowest Response: {max(times):.0f}ms")
        
        # Overall recommendations
        print(f"\n[TARGET] Recommendations:")
        
        if "chat_performance" in results and results["chat_performance"].get("avg_response_time", 0) > 1000:
            print("  • Consider optimizing LLM response caching")
            print("  • Review agent processing logic for bottlenecks")
        
        if "cache_effectiveness" in results and not results["cache_effectiveness"].get("cache_effective", False):
            print("  • Cache implementation may need tuning")
            print("  • Consider increasing cache TTL or size")
        
        print("  • Monitor performance regularly")
        print("  • Set up automated performance alerts")
        
        print("\n" + "=" * 60)


def main():
    """Main test execution"""
    print("[MICROSCOPE] Teknofest 2025 - Performance Optimization Test")
    print("Testing performance improvements...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"[X] Server not responding properly: {response.status_code}")
            return
    except Exception as e:
        print(f"[X] Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the backend is running: python backend/main.py")
        print(f"   Error: {e}")
        return
    
    print(f"[CHECK] Server is running at {BASE_URL}")
    
    # Run tests
    tester = PerformanceTester(BASE_URL)
    results = tester.run_comprehensive_test()
    
    # Print summary
    tester.print_summary(results)
    
    # Save detailed results
    with open("performance_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[PAGE] Detailed results saved to: performance_test_results.json")


if __name__ == "__main__":
    main()