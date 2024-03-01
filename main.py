import requests
import json
from fastapi import FastAPI
import serpapi

app = FastAPI()

@app.get("/")
def read_root():
  return "Hello world"


@app.get("/images/{thing}")
def read_fish(thing):
  with open('private_info.json') as f:
    data = json.load(f)
  params = {
    "engine": "google_images",
    "q": thing,
    "api_key": data["serp_api_key"]
  }
  print(data["serp_api_key"])
  search = serpapi.search(params)
  results = search["images_results"]
  return results