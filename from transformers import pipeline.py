from transformers import pipeline
chatbot = pipeline("text-generation", model="gpt2")