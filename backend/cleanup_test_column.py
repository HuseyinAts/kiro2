"""Remove test column"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost/kiro2_db')

with engine.begin() as conn:
    conn.execute(text('ALTER TABLE users DROP COLUMN IF EXISTS test_column'))
    print('Test column removed')
