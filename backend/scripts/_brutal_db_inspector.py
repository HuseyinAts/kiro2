import asyncio
import json
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/kiro2"

async def inspect_db():
    conn = await asyncpg.connect(DATABASE_URL)
    results = {}
    try:
        # 1. SHOW max_connections;
        max_conn_row = await conn.fetchrow("SHOW max_connections;")
        max_connections = int(max_conn_row['max_connections'])
        results['max_connections'] = max_connections

        # 2. Broken/Invalid Indexes (indisvalid = false)
        invalid_idx_query = """
        SELECT
            c.relname as index_name,
            t.relname as table_name
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        JOIN pg_class t ON t.oid = i.indrelid
        WHERE i.indisvalid = false
        LIMIT 50;
        """
        invalid_rows = await conn.fetch(invalid_idx_query)
        results['invalid_indexes'] = [
            {"index_name": r['index_name'], "table_name": r['table_name']}
            for r in invalid_rows
        ]

        # 3. JSONB columns in the database
        jsonb_cols_query = """
        SELECT 
            table_name, 
            column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND udt_name = 'jsonb'
        LIMIT 50;
        """
        jsonb_cols = await conn.fetch(jsonb_cols_query)

        # 4. GIN indexes in the database
        gin_idx_query = """
        SELECT 
            t.relname as table_name,
            i.relname as index_name,
            a.attname as column_name
        FROM pg_class t
        JOIN pg_index idx ON t.oid = idx.indrelid
        JOIN pg_class i ON i.oid = idx.indexrelid
        JOIN pg_am am ON i.relam = am.oid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
        WHERE am.amname = 'gin' AND t.relnamespace = 'public'::regnamespace
        LIMIT 50;
        """
        gin_rows = await conn.fetch(gin_idx_query)
        gin_indexed_cols = {(r['table_name'], r['column_name']) for r in gin_rows}

        # Determine which JSONB columns lack GIN indexes
        missing_gin_indexes = []
        for col in jsonb_cols:
            tbl = col['table_name']
            clm = col['column_name']
            if (tbl, clm) not in gin_indexed_cols:
                missing_gin_indexes.append({"table_name": tbl, "column_name": clm})
        
        results['missing_gin_indexes'] = missing_gin_indexes

        # Output in JSON format
        print(json.dumps(results, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(inspect_db())
