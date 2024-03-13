# VectorDB

This repository contains the code for my presentation about vector databases. The presentation uses the Redis stack.

## Prerequisites
- Docker
- Python >=3.8 or Rust >=1.5
- Running Redis container (see setup.bash)

## How to run
1. Start the Redis container
```bash
./setup.bash
```

# TODO: Index Command/rust
FT.CREATE idx:bikes_vss ON JSON
PREFIX 1 bikes: SCORE 1.0
SCHEMA
$.model TEXT WEIGHT 1.0 NOSTEM
$.brand TEXT WEIGHT 1.0 NOSTEM
$.price NUMERIC
$.type TAG SEPARATOR ","
$.description AS description TEXT WEIGHT 1.0
$.description_embeddings AS vector VECTOR FLAT 6 TYPE FLOAT32 DIM 768 DISTANCE_METRIC COSINE

# TODOS
- [x] Create a Redis instance
- [x] Fill with data
- [x] Create Index
- [x] Query
- [x] Create a Gradio example
- [ ] Create everything in Rust
- [ ] Finish Readme(images, etc)