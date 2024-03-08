import gradio as gr
import numpy as np
import pandas as pd
import redis
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
import plotly.graph_objects as go
from sklearn.manifold import TSNE
import ast

# Connect to redis
client = redis.Redis(host="localhost", port=6379, decode_responses=True)

res = client.ping()
print("Connection successfully:", res)

keys = sorted(client.keys("movies:*"))

embedder = SentenceTransformer("msmarco-distilbert-base-v4")


def to_float_list(string):
    return [float(i) for i in ast.literal_eval(string)]


def create_query_table(encoded_queries, num_results):
    query = (
        Query(f"(*)=>[KNN {num_results} @title_embeddings $query_vector AS vector_score]")
        .sort_by("vector_score")
        .return_fields("vector_score", "id", "title", "overview", "runtime", "budget", "revenue", "title_embeddings")
        .dialect(2)
        .paging(0, num_results)
    )
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
                },
            )
            .docs
        )
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
    queries_table.sort_values(
        by=["score"], ascending=[False], inplace=True
    )

    return queries_table


