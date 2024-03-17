import requests
import redis
import json
from fastapi import FastAPI
import serpapi
import numpy as np
from redis.commands.search.query import Query
from embeddings import get_model_info, get_single_text_embedding, get_single_image_embedding
from schema import rd_schema, definition
from threading import Thread

# global constants
INDEX_NAME = "idx:image_signals"

# setup
with open('private_info.json') as f:
    data = json.load(f)

rd = redis.Redis(host=data["redis_host"], port=data["redis_port"], password=data["redis_password"], decode_responses=True)
try:
  rd.ft(INDEX_NAME).info()
except:
  res = rd.ft(INDEX_NAME).create_index(
      fields=rd_schema, definition=definition
  )

app = FastAPI()

# daemon thread
def add_to_cache(query, json_results):
  print("daemon is running")
  pipeline = rd.pipeline()
  for i, result in enumerate(json_results):
    rd_key = f"{query}-{i}"
    image_embedding = get_single_image_embedding(result['thumbnail_key'])
    pipeline.json().set(rd_key, "$", result, nx=True)
    pipeline.json().set(rd_key, "$.image_embedding", image_embedding)
    pipeline.expire(rd_key, 2000)
  pipeline.execute()

# important functions
@app.get("/")
def read_root():
  info = rd.ft("idx:image_signals").info()
  num_docs = info["num_docs"]
  indexing_failures = info["hash_indexing_failures"]

  return f"{num_docs} documents indexed with {indexing_failures} failures"

# just for testing, will remove eventually
@app.get("/text/{query}")
def get_text_embedding(query):
  e = get_single_text_embedding(query)
  print(e)
  print(e.shape)

@app.get("/images/{query}")
def query_image(query):

  text_embedding = get_single_text_embedding(query)

  rd_query = (
      Query("(*)=>[KNN 10 @image_embedding $query_vector AS score]")
      .sort_by("score", asc=True)
      .return_fields("score", "link", "thumbnail_key", "title")
      .dialect(2)
  )

  query_params = {
      "query_vector": text_embedding.astype(np.float32).tobytes()
  }

  search_docs = rd.ft(INDEX_NAME).search(rd_query, query_params).docs

  if len(search_docs) >= 10 and float(search_docs[-1]["score"]) < 0.8:
    print("cache hit")
    results = search_docs
  else:
    print("cache miss")
    params = {
      "engine": "google_images",
      "q": query,
      "api_key": data["serp_api_key"]
    }
    search = serpapi.search(params)
    results = []
    for i, result in enumerate(search["images_results"]):
      json_result = {"thumbnail_key": result['thumbnail'], "title": result['title'], "link": result['link']}
      results.append(json_result)
    daemon = Thread(target=add_to_cache, args=(query, results,))
    daemon.setDaemon(True)
    daemon.start()
  return results