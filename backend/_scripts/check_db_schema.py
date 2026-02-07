"""Quick script to check database schema"""
import os
from sqlalchemy import create_engine, inspect

db_password = os.getenv("DATABASE_PASSWORD", "")
engine = create_engine(f'postgresql://postgres:{db_password}@localhost:5434/turkiye_sinav_db')
inspector = inspect(engine)

tables_to_check = ['users', 'kullanicilar', 'questions', 'sorular', 'sinavlar', 'sinav_sonuclari']

for table in tables_to_check:
    print(f'\n=== {table} ===')
    try:
        columns = inspector.get_columns(table)
        print(f'Columns ({len(columns)}):')
        for col in columns[:8]:
            print(f'  - {col["name"]}: {col["type"]}')
        if len(columns) > 8:
            print(f'  ... and {len(columns) - 8} more')
    except Exception as e:
        print(f'Error: {e}')
