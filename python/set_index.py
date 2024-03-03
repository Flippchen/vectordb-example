import numpy as np
import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from sentence_transformers import SentenceTransformer
import time

# Connect to redis
client = redis.Redis(host="localhost", port=6379, decode_responses=True)

res = client.ping()
print("Connection successfully:", res)

# Get all keys
keys = sorted(client.keys("movies:*"))
print("Keys:", len(keys))
# Get all descriptions
titles = client.json().mget(keys, "$.title")
titles = [item for sublist in titles for item in sublist]
print("Titles:", len(titles))

# Embed descriptions
embedder = SentenceTransformer("msmarco-distilbert-base-v4")
embeddings = embedder.encode(titles).astype(np.float32).tolist()
VECTOR_DIMENSION = len(embeddings[0])
print("Vector dimension:", VECTOR_DIMENSION)

pipeline = client.pipeline()
for key, embedding in zip(keys, embeddings):
    pipeline.json().set(key, "$.title_embeddings", embedding)

res = pipeline.execute()

res = client.json().get("movies:001")

print("First movies with embeddings:", res)

schema = (
    NumericField("$.id", as_name="id"),
    TextField("$.title", no_stem=True, as_name="title"),
    TagField("$.overview", as_name="overview"),
    NumericField("$.runtime", as_name="runtime"),
    NumericField("$.budget", as_name="budget"),
    NumericField("$.revenue", as_name="revenue"),
    VectorField(
        "$.title_embeddings",
        as_name="title_embeddings",
        algorithm="HNSW", # Hierarchical Navigable Small World algorithm.
        attributes={"TYPE": "Float32", "DIM": VECTOR_DIMENSION, "DISTANCE_METRIC": "COSINE"},
    ),
)

definition = IndexDefinition(prefix=["movies:"], index_type=IndexType.JSON)

res = client.ft("idx:movies_vss").create_index(fields=schema, definition=definition)
print("Index created:", res)

time.sleep(10)
info = client.ft("idx:movies_vss").info()
print("Index info:", info)

indexing_failures = info["hash_indexing_failures"]
num_docs = info["num_docs"]
print(f"Number of documents: {num_docs}")
print(f"Indexing failures: {indexing_failures}")



