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


