import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer

def get_model_info(model_ID, device):
  # Save the model to device
	model = CLIPModel.from_pretrained(model_ID).to(device)
 	# Get the processor
	processor = CLIPProcessor.from_pretrained(model_ID)
  # Get the tokenizer
	tokenizer = CLIPTokenizer.from_pretrained(model_ID)
  # Return model, processor & tokenizer
	return model, processor, tokenizer
# Set the device
device = "cpu"
# Define the model ID
model_ID = "openai/clip-vit-base-patch32"
# Get model, processor & tokenizer
model, processor, tokenizer = get_model_info(model_ID, device)

def get_single_text_embedding(text):
  inputs = tokenizer(text, return_tensors = "pt")
  text_embeddings = model.get_text_features(**inputs)
  # convert the embeddings to numpy array
  embedding_as_np = text_embeddings.cpu().detach().numpy()
  return embedding_as_np

def get_single_image_embedding(my_image):
  image = processor(
		text = None,
		images = my_image,
		return_tensors="pt"
		)["pixel_values"].to(device)
  embedding = model.get_image_features(image)
  # convert the embeddings to numpy array
  embedding_as_np = embedding.cpu().detach().numpy()
  return embedding_as_np
