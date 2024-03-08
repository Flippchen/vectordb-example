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


def create_plot(embeddings_table, perplexity_value):
    tsne = TSNE(n_components=3, random_state=0, perplexity=perplexity_value - 1)
    embeddings = np.array(embeddings_table["title_embeddings"].tolist())
    embeddings_3d = tsne.fit_transform(embeddings)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=embeddings_3d[:, 0],
                y=embeddings_3d[:, 1],
                z=embeddings_3d[:, 2],
                mode="markers",
                marker=dict(
                    size=5,
                    color=embeddings_table["score"],
                    colorscale="Viridis",
                    opacity=0.8,
                ),
                text=embeddings_table["title"],
            )
        ]
    )

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
        ),
    )

    return fig


def find_similar_movies(query, num_results):
    if query is None or query == "":
        return pd.DataFrame(columns=["score", "title", "runtime", "budget", "revenue", "overview"])

    # Create encoded query
    queries = [query]
    encoded_queries = embedder.encode(queries).astype(np.float32).tolist()

    # Create table
    table = create_query_table(encoded_queries, num_results)

    # Extract embeddings and add query to the table
    embeddings_table = table[["title", "title_embeddings", "score"]]
    embeddings_table['title_embeddings'] = embeddings_table['title_embeddings'].apply(to_float_list)
    embeddings_table.loc[-1] = [query, encoded_queries[0], 1]  # adding a row

    # Plot 3D visualization
    figure = create_plot(embeddings_table, num_results)

    # Remove title_embeddings from the table for better visualization
    table.drop(columns=["title_embeddings"], inplace=True)

    return table, figure


# Get the total number of movies
total_movies = len(keys)

# Short description of the application
description = f"""
## Description
This application allows you to find movies similar to a given title using BERT embeddings and TSNE for visualization.
Just enter a movie title, select the number of similar movies you want to see, and the application will display a list of similar movies along with a 3D plot.

## Number of movies in the database: {total_movies}.
"""

with gr.Blocks() as iface:
    gr.Markdown("# Movie Similarity Search")
    gr.Markdown(description)

    with gr.Row():
        movie_title = gr.Textbox(label="Enter a Movie Title")
        num_similar = gr.Slider(minimum=1, maximum=50, label="Number of most Similar Movies", step=1, value=5)
        submit_btn = gr.Button("Submit", variant="primary")
        visualization_plot = gr.Plot(label="Visualization Plot", min_width=800)

    with gr.Row():
        similar_movies = gr.DataFrame(label="Similar Movies", min_width=300, headers=["Score", "Title", "Runtime", "Budget", "Revenue", "Overview"])

    submit_btn.click(find_similar_movies, inputs=[movie_title, num_similar], outputs=[similar_movies, visualization_plot])

    iface.launch(share=False)

