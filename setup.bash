#!/bin/bash

# Pull the latest Redis Stack image
docker pull redis/redis-stack:latest

# Run the Redis Stack container
docker run -d --name vectordb -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
