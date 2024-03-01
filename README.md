# image-store

Simple image serving site to learn about redis

## Setup

1. Set up virtual env
2. Set up private_info.json with the following template `{"serp_api_key": <your_api_key>, "redis_host": <your_redis_host>, "redis_port": <your_redis_port>, "redis_password": <your_redis_password>}`
3. run `uvicorn main:app --reload`
