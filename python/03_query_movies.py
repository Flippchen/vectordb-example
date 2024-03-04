import os

import numpy as np
import psycopg2
import pandas as pd
import redis
import requests
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

# Connect to redis
client = redis.Redis(host="localhost", port=6379, decode_responses=True)

res = client.ping()
print("Connection successfully:", res)

embedder = SentenceTransformer("msmarco-distilbert-base-v4")


def create_query_table(query, queries, encoded_queries, extra_params={}):
    results_list = []
    for i, encoded_query in enumerate(encoded_queries):
        result_docs = (
            client.ft("idx:movies_vss")
            .search(
                query,
                {
                    "query_vector": np.array(
                        encoded_query, dtype=np.float32
                    ).tobytes()
                }
                | extra_params,
            )
            .docs
        )
        for doc in result_docs:
            vector_score = round(1 - float(doc.vector_score), 2)
            results_list.append(
                {
                    "query": queries[i],
                    "score": vector_score,
                    "id": doc.id,
                    "title": doc.title,
                    "overview": doc.overview,
                    "runtime": doc.runtime,
                    "budget": doc.budget,
                    "revenue": doc.revenue,
                }
            )

    # Optional: convert the table to Markdown using Pandas
    queries_table = pd.DataFrame(results_list)
    queries_table.sort_values(
        by=["query", "score"], ascending=[True, False], inplace=True
    )
    queries_table["query"] = queries_table.groupby("query")["query"].transform(
        lambda x: [x.iloc[0]] + [""] * (len(x) - 1)
    )
    queries_table["overview"] = queries_table["overview"].apply(
        lambda x: (x[:497] + "...") if len(x) > 500 else x
    )
    queries_table.to_markdown(index=False)

    return queries_table


number_of_neighbors = 4
query = (
    Query(f"(*)=>[KNN {number_of_neighbors} @title_embeddings $query_vector AS vector_score]")
    .sort_by("vector_score")
    .return_fields("vector_score", "id", "title", "overview", "runtime", "budget", "revenue")
    .dialect(2)
)
queries = [
    "Star Wars",
    "Harry Potter",
    "French",
    "Toast",
    "The Lord of the Rings",
]
encoded_queries = embedder.encode(queries).astype(np.float32).tolist()
table = create_query_table(query, queries, encoded_queries)

print(table)
table.to_csv("query_results.csv", index=False)
