"""Remove test column"""

import os
import sys

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL env var required.")

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS test_column"))
    print("Test column removed")
