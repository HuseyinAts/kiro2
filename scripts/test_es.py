import asyncio, os, sys
sys.path.insert(0, '/app')

async def test():
    from elasticsearch import AsyncElasticsearch
    url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    print("Connecting to:", url)
    es = AsyncElasticsearch([url])
    try:
        h = await es.cluster.health()
        print("Cluster status:", h['status'])
        i = await es.cat.indices(format='json')
        print("Indices:", [x['index'] for x in i] if i else 'EMPTY')
        # Ping
        ok = await es.ping()
        print("Ping:", ok)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e)[:120])
    finally:
        await es.close()

asyncio.run(test())
