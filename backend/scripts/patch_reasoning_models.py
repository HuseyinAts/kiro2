import re

file_path = 'models/reasoning_models.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'from pgvector.sqlalchemy import Vector' not in content:
    content = content.replace(
        'from sqlalchemy import (',
        'from pgvector.sqlalchemy import Vector\nfrom sqlalchemy import ('
    )

content = content.replace(
    'problem_embedding = Column(ARRAY(Float), nullable=True)',
    'problem_embedding = Column(Vector(1536), nullable=True)'
)

# We also need an index on problem_embedding.
# Wait, this is a table class, let's see if __table_args__ exists.
if '__table_args__ = (' in content and 'ix_problem_embedding_hnsw' not in content:
    content = content.replace(
        '__table_args__ = (',
        '__table_args__ = (\n        Index(\n            "ix_problem_embedding_hnsw",\n            "problem_embedding",\n            postgresql_using="hnsw",\n            postgresql_with={"m": 16, "ef_construction": 64},\n            postgresql_ops={"problem_embedding": "vector_cosine_ops"}\n        ),'
    )
elif 'class ReasoningTree(Base):' in content and 'ix_problem_embedding_hnsw' not in content:
    # If no table_args, we might need to add it, but it's risky without seeing the class. Let's just leave the column type change.
    pass

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated reasoning_models.py")
