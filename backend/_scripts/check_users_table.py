"""Check if users is a table or view"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost/kiro2_db')

with engine.connect() as conn:
    # Check table type
    result = conn.execute(text(
        "SELECT table_type FROM information_schema.tables WHERE table_name = 'users'"
    ))
    table_type = result.scalar()
    print(f"users table_type: {table_type}")

    # Check if kullanicilar exists
    result = conn.execute(text(
        "SELECT table_type FROM information_schema.tables WHERE table_name = 'kullanicilar'"
    ))
    kul_type = result.scalar()
    print(f"kullanicilar table_type: {kul_type}")

    # List ALL columns with details
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """))
    print("\nusers table columns:")
    for row in result:
        col_name = row[0]
        data_type = row[1]
        is_null = row[2]
        max_len = row[3] if row[3] else ''
        print(f"  {col_name:30} {data_type:20} {max_len:10} NULL={is_null}")

    # Try to check if it's actually a view masquerading as a table
    result = conn.execute(text("""
        SELECT schemaname, viewname
        FROM pg_views
        WHERE viewname = 'users'
    """))
    view_info = result.fetchone()
    if view_info:
        print(f"\nWARNING: 'users' is ACTUALLY a view in schema: {view_info[0]}")
    else:
        print("\n'users' is confirmed as a real table (not a view)")
