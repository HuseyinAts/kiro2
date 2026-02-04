"""Quick script to check database schema"""
from sqlalchemy import create_engine, inspect

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost:5432/turkiye_sinav_db')
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
