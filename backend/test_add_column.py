"""Test adding column to users table"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost/kiro2_db')

try:
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE users ADD COLUMN test_column VARCHAR(10)'))
        print('SUCCESS: Column added successfully')
except Exception as e:
    print(f'ERROR: {e}')
