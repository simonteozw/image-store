import requests
import redis
import json
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import serpapi
import numpy as np
from redis.commands.search.query import Query
from embeddings import get_model_info, get_single_text_embedding, get_single_image_embedding
from schema import rd_schema, definition
from threading import Thread
import starlette.status as status


# global constants
INDEX_NAME = "idx:image_signals"
CACHE_TTL = 10000
SIMILARITY_THRESHOLD = 0.7 # lower is more similar
templates = Jinja2Templates(directory="templates")

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
    pipeline.expire(rd_key, CACHE_TTL)
  pipeline.execute()

# important functions
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
  results = []

  if len(search_docs) >= 10 and float(search_docs[-1]["score"]) < SIMILARITY_THRESHOLD:
    print("cache hit")
    for result in search_docs:
      json_result = {"thumbnail_key": result['thumbnail_key'], "title": result['title'], "link": result['link']}
      results.append(json_result)
  else:
    print("cache miss")
    params = {
      "engine": "google_images",
      "q": query,
      "api_key": data["serp_api_key"]
    }
    search = serpapi.search(params)
    for _, result in enumerate(search["images_results"]):
      json_result = {"thumbnail_key": result['thumbnail'], "title": result['title'], "link": result['link']}
      results.append(json_result)
    daemon = Thread(target=add_to_cache, args=(query, results,))
    daemon.setDaemon(True)
    daemon.start()
  return results

# core functions
@app.get("/")
def read_root(request: Request):
  info = rd.ft("idx:image_signals").info()
  num_docs = info["num_docs"]
  indexing_failures = info["hash_indexing_failures"]
  return templates.TemplateResponse("index.html",{"request":request, "num_docs": num_docs, "indexing_failures": indexing_failures})

@app.get("/image_search")
def image_form(request: Request):
  return templates.TemplateResponse("image_form.html",{"request":request})

@app.post("/image_search", response_class=RedirectResponse)
def redirect(request: Request, query: str = Form(...)):
  redirect_url = request.url_for('search_images', **{ 'query' : query})
  return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
  # image_results = query_image(query)
  # return templates.TemplateResponse("image_results.html",{"request":request, "image_results": image_results})

@app.get("/image_results/{query}")
def search_images(request: Request, query):
  image_results = query_image(query)
  image_titles = []
  image_links = []
  image_thumbnails = []

  for res in image_results:
    image_titles.append(res['title'])
    image_links.append(res['link'])
    image_thumbnails.append(res['thumbnail_key'])
  return templates.TemplateResponse("image_results.html",{"request":request, "image_titles": image_titles, "image_links": image_links, "image_thumbnails": image_thumbnails})
