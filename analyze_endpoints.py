#!/usr/bin/env python3
"""Endpoint analiz scripti"""
import json
import requests
from collections import defaultdict

try:
    # OpenAPI spec'i al
    response = requests.get('http://localhost:8000/openapi.json', timeout=5)
    data = response.json()

    paths = data.get('paths', {})

    # Endpoint'leri kategorize et
    categories = defaultdict(list)
    total = 0

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                total += 1
                tags = details.get('tags', ['Diğer'])
                tag = tags[0] if tags else 'Diğer'

                categories[tag].append({
                    'method': method.upper(),
                    'path': path,
                    'summary': details.get('summary', 'N/A'),
                    'operationId': details.get('operationId', 'N/A')
                })

    # Sonuçları yazdır
    print('=' * 100)
    print(f'🎯 TOPLAM ENDPOINT SAYISI: {total}')
    print('=' * 100)
    print()

    # Kategorilere göre sırala ve yazdır
    for category in sorted(categories.keys()):
        endpoints = categories[category]
        print(f'\n📦 {category}')
        print(f'   Toplam: {len(endpoints)} endpoint')
        print('-' * 100)

        # Her kategoriden ilk 15 endpoint'i göster
        for i, ep in enumerate(endpoints[:15], 1):
            method_color = {
                'GET': '🔵',
                'POST': '🟢',
                'PUT': '🟡',
                'DELETE': '🔴',
                'PATCH': '🟠'
            }.get(ep['method'], '⚪')

            print(f'  {i:2}. {method_color} {ep["method"]:6} {ep["path"][:65]}')
            if ep['summary'] != 'N/A':
                print(f'      → {ep["summary"][:80]}')

        if len(endpoints) > 15:
            print(f'\n      ... ve {len(endpoints) - 15} endpoint daha\n')

    # Özet istatistikler
    print('\n' + '=' * 100)
    print('📊 KATEGORİ İSTATİSTİKLERİ')
    print('=' * 100)

    sorted_cats = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
    for category, endpoints in sorted_cats[:10]:
        print(f'  {category:40} : {len(endpoints):3} endpoint')

    # HTTP method istatistikleri
    method_counts = defaultdict(int)
    for endpoints in categories.values():
        for ep in endpoints:
            method_counts[ep['method']] += 1

    print('\n' + '=' * 100)
    print('📊 HTTP METHOD İSTATİSTİKLERİ')
    print('=' * 100)
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {method:6} : {count:3} endpoint')

    print('\n' + '=' * 100)

except Exception as e:
    print(f'❌ Hata: {e}')
    import traceback
    traceback.print_exc()
