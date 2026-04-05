"""
query_monitoring.py: record_query() icerisine health-check sorgu filtresi ekle.
Bu sayede /health endpoint'inin tekrar eden sorgulari N+1 olarak isaretlenmez.
"""

path = r"C:\Users\husey\kiro2\backend\core\query_monitoring.py"

with open(path, encoding="utf-8") as f:
    content = f.read()

# record_query'nin basindaki ilk satira health filtresi ekle
OLD_RECORD = '''    def record_query(
        self, statement: str, duration: float, row_count: Optional[int] = None
    ):
        """Record a query execution"""
        self.queries_executed += 1
        self.total_duration += duration'''

NEW_RECORD = '''    # Sorgular bu patterndeyse N+1 sayacina dahil edilmez
    _HEALTH_QUERY_PATTERNS = (
        "information_schema",
        "SELECT 1",
        "select 1",
        "pg_stat",
        "pg_database",
    )

    def record_query(
        self, statement: str, duration: float, row_count: Optional[int] = None
    ):
        """Record a query execution"""
        # Health-check ve sistem sorgularini N+1 sayacindan hariç tut
        if any(p in statement for p in self._HEALTH_QUERY_PATTERNS):
            return  # Sayaca katma, log'a yazma

        self.queries_executed += 1
        self.total_duration += duration'''

if OLD_RECORD not in content:
    print("HATA: Hedef kod bulunamadi!")
    idx = content.find("def record_query")
    print(repr(content[idx:idx+200]))
else:
    new_content = content.replace(OLD_RECORD, NEW_RECORD, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("OK: record_query() health-check filtresi eklendi")
    # Dogrula
    assert "_HEALTH_QUERY_PATTERNS" in new_content
    assert "information_schema" in new_content
    print("Dogrulama gecti.")
    print(f"  Eski: {content.count(chr(10))+1} satir")
    print(f"  Yeni: {new_content.count(chr(10))+1} satir")
