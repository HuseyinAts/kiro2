import asyncio, asyncpg

async def verify():
    conn = await asyncpg.connect(host='localhost', port=5434, user='postgres', password='1470', database='turkiye_sinav_db')
    count = await conn.fetchval('SELECT COUNT(*) FROM sorular WHERE aktif = true')
    sample = await conn.fetch('SELECT metin, dogru_cevap, sinav_tipi, konu FROM sorular WHERE aktif = true LIMIT 3')
    print(f'\n========================================')
    print(f'SORULAR TABLE VERIFICATION')
    print(f'========================================')
    print(f'Total active questions: {count}')
    print(f'\nSample questions:')
    for i, q in enumerate(sample, 1):
        print(f'\n{i}. {q["metin"][:80]}')
        print(f'   Answer: {q["dogru_cevap"]} | Type: {q["sinav_tipi"]} | Topic: {q["konu"]}')
    await conn.close()
    print(f'\n========================================\n')
    return count

asyncio.run(verify())
