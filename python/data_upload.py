import os

import numpy as np
import psycopg2
import pandas as pd
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

db_params = {
    'dbname': 'movie_db',
    'user': 'postgres',
    'password': os.environ['POSTGRES_PASSWORD'],
    'host': '49.13.1.33',
    'port': '5333'
}


sql_query = """
    SELECT title, overview, budget, revenue, runtime
    FROM movies
    WHERE budget > 0 AND revenue > 0 AND runtime > 0 and title is not null and overview is not null
    """


def query_db(sql_query, conn):
    return pd.read_sql_query(sql_query, conn)


if os.path.exists('all_movies.csv'):
    all_movies = pd.read_csv('all_movies.csv', lineterminator='\n')
else:
    # Connection
    conn = psycopg2.connect(**db_params)
    all_movies = query_db(sql_query, conn)
    all_movies.to_csv('all_movies.csv', index=False)

# Remove all movies where title is null
all_movies = all_movies[all_movies['title'].notnull()]
all_movies = all_movies.where(pd.notnull(all_movies), None)
print(all_movies.head())






