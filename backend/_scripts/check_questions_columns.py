import asyncio

import asyncpg


async def check_columns():
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="1470",
        database="turkiye_sinav_db",
    )

    cols = await conn.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'questions'
        ORDER BY ordinal_position
    """)

    print("questions table columns:")
    for col in cols:
        print(f"  {col['column_name']} ({col['data_type']})")

    await conn.close()


asyncio.run(check_columns())
