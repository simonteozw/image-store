import requests
import redis
import json
from fastapi import FastAPI
import serpapi
from embeddings import get_model_info, get_single_text_embedding, get_single_image_embedding
from PIL import Image
from io import BytesIO

with open('private_info.json') as f:
    data = json.load(f)

rd = redis.Redis(host=data["redis_host"], port=data["redis_port"], password=data["redis_password"], decode_responses=True)

app = FastAPI()

def get_image(image_URL):
  response = requests.get(image_URL)
  image = Image.open(BytesIO(response.content)).convert("RGB")
  return image

@app.get("/")
def read_root():
  return "Hello world"

# just for testing, will remove eventually
@app.get("/text/{query}")
def get_text_embedding(query):
  e = get_single_text_embedding(query)
  print(e)
  print(e.shape)

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