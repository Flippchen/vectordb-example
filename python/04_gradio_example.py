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

