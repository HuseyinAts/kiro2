import asyncio, os, sys
sys.path.insert(0, '/app')

async def test():
    from elasticsearch import AsyncElasticsearch
    url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    idx = os.environ.get('ELASTICSEARCH_INDEX', 'turkiye_sinav_platform')
    es = AsyncElasticsearch([url])
    
    # 1. Index doc count
    stats = await es.indices.stats(index=idx)
    dc = stats['indices'][idx]['primaries']['docs']['count']
    print(f"Index '{idx}': {dc:,} docs")
    
    # 2. Sample doc
    r = await es.search(index=idx, query={"match_all":{}}, size=1)
    if r['hits']['hits']:
        doc = r['hits']['hits'][0]['_source']
        print(f"Sample doc keys: {list(doc.keys())[:8]}")
        print(f"Sample question_text: {str(doc.get('question_text',''))[:80]}")
        print(f"Sample subject_area: {doc.get('subject_area')}, exam_type: {doc.get('exam_type')}")
    
    # 3. Direct search by subject_area
    r2 = await es.search(index=idx, query={"term":{"subject_area":"MATEMATIK"}}, size=3)
    print(f"\nMatematik sorulari: {r2['hits']['total']['value']}")
    
    # 4. Full text search 'logaritma'
    r3 = await es.search(index=idx, query={
        "multi_match": {
            "query": "logaritma",
            "fields": ["question_text^2", "option_a", "explanation"],
            "fuzziness": "AUTO"
        }
    }, size=3)
    print(f"'logaritma' arama: {r3['hits']['total']['value']} hit")
    if r3['hits']['hits']:
        print(f"  First hit: {str(r3['hits']['hits'][0]['_source'].get('question_text',''))[:80]}")
    
    await es.close()

asyncio.run(test())
