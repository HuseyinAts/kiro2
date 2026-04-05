import asyncio, os, sys
sys.path.insert(0, '/app')
os.environ['ELASTICSEARCH_URL'] = 'http://turkiye_sinav_elasticsearch:9200'

async def test_hc():
    # Health check modulu import et
    import importlib
    import core.comprehensive_health_check as hc_mod
    importlib.reload(hc_mod)
    
    # Elasticsearch URL'yi kontrol et
    from elasticsearch import AsyncElasticsearch
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    print(f"Testing with URL: {es_url}")
    es = AsyncElasticsearch([es_url], request_timeout=5)
    try:
        h = await es.cluster.health()
        print(f"Direct check: {h['status']}")
    except Exception as e:
        print(f"Direct check ERROR: {e}")
    finally:
        await es.close()

asyncio.run(test_hc())
