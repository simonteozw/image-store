import requests
import redis
import json
from fastapi import FastAPI
import serpapi

with open('private_info.json') as f:
    data = json.load(f)

rd = redis.Redis(host=data["redis_host"], port=data["redis_port"], password=data["redis_password"], decode_responses=True)

app = FastAPI()

@app.get("/")
def read_root():
  return "Hello world"


@app.get("/images/{thing}")
def query_image(thing):
  cache = rd.get(thing)
  if cache:
    print("cache hit")
    results = cache
  else:
    print("cache miss")
    params = {
      "engine": "google_images",
      "q": thing,
      "api_key": data["serp_api_key"]
    }
    search = serpapi.search(params)
    results = []
    for result in search["images_results"]:
      results.append({"thumbnail_key": result['thumbnail'], "title": result['title'], "link": result['link']})
    results = json.dumps(results)
    rd.set(thing, results)
    rd.expire(thing, 10)
  return json.loads(results)