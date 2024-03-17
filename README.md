# image-store

Simple image serving site to learn about redis

## User Experience

1. Search (text) to find images of similar nature
2. Upload an image to find images of similar nature

## Setup

1. Set up virtual env
2. Set up private_info.json with the following template `{"serp_api_key": <your_api_key>, "redis_host": <your_redis_host>, "redis_port": <your_redis_port>, "redis_password": <your_redis_password>}`
3. run `uvicorn main:app --reload`

## Next Steps

1. find top X similar embeddings [DONE]
2. backend optimizations to shift long things to background processes [DONE]
3. build simple frontend to display images
