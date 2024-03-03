import os
import psycopg2
import pandas as pd
import redis

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


# Connect to redis
client = redis.Redis(host="localhost", port=6379, decode_responses=True)

res = client.ping()
print("Connection successfully:", res)

# Upload to redis
pipeline = client.pipeline()
for i, movie in all_movies.iterrows():
    redis_key = f"movies:{i:03}"
    pipeline.json().set(redis_key, "$", movie.to_dict())

res = pipeline.execute()

# Get from redis one result
result = client.json().get("movies:001")
print("First movies:", result)
