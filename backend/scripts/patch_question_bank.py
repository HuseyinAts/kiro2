file_path = "models/question_bank.py"

with open(file_path, encoding="utf-8") as f:
    content = f.read()

# Add import
if "from pgvector.sqlalchemy import Vector" not in content:
    content = content.replace(
        "from sqlalchemy import (",
        "from pgvector.sqlalchemy import Vector\nfrom sqlalchemy import (",
    )

# Replace commented embedding column with actual column
target_block = """    # NOT: embedding kolonu pgvector tipinde - SQLAlchemy NullType ile görünmez,
    #      alembic/env.py include_object ile hariç tutuldu"""

replacement = """    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True, comment="HNSW indexli Soru Embedding vektörü"
    )"""

if target_block in content:
    content = content.replace(target_block, replacement)

# Add HNSW Index at the bottom
if 'Index("ix_question_embedding_hnsw"' not in content:
    content = content.replace(
        "__table_args__ = (",
        '__table_args__ = (\n        Index(\n            "ix_question_embedding_hnsw",\n            "embedding",\n            postgresql_using="hnsw",\n            postgresql_with={"m": 16, "ef_construction": 64},\n            postgresql_ops={"embedding": "vector_cosine_ops"}\n        ),',
    )

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated question_bank.py")
