import pandas as pd
import redis
from sentence_transformers import SentenceTransformer
import numpy as np
from redis.commands.search.query import Query

client = redis.Redis(host="localhost", port=6379, decode_responses=True)
embedder = SentenceTransformer("msmarco-distilbert-base-v4")

res = client.ping()
print("Connection successfully:", res)

query_text = "The Matrix"
num_results = 5

queries = [query_text]
encoded_query = embedder.encode(queries).astype(np.float32).tolist()

query = (
        Query(f"(*)=>[KNN {num_results} @title_embeddings $query_vector AS vector_score]")
        .sort_by("vector_score")
        .return_fields("vector_score", "id", "title", "overview", "runtime", "budget", "revenue", "title_embeddings")
        .dialect(2)
        .paging(0, num_results)
    )

result_docs = (
            client.ft("idx:movies_vss")
            .search(
                query,
                {
                    "query_vector": np.array(
                        encoded_query, dtype=np.float32
                    ).tobytes()
                },
            )
            .docs
        )

results_list = []
for doc in result_docs:
    vector_score = round(1 - float(doc.vector_score), 2)
    results_list.append(
        {
            "score": vector_score,
            "title": doc.title,
            "runtime": doc.runtime,
            "budget": doc.budget,
            "revenue": doc.revenue,
            "overview": doc.overview,
            "title_embeddings": doc.title_embeddings,
        }
    )

queries_table = pd.DataFrame(results_list)
queries_table.drop(columns=["title_embeddings"], inplace=True)
queries_table.sort_values(
        by=["score"], ascending=[False], inplace=True
    )

print(queries_table)
queries_table.to_csv("queries_table.csv", index=False)