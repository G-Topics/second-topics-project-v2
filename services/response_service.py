import openai
from config import OPENAI_API_KEY
from utils.embeddings import get_message_embedding
from database.queries import get_client_name
import chromadb

openai.api_key = OPENAI_API_KEY
chroma_client = chromadb.Client()

def generate_response(message, sender):
    embedding = get_message_embedding(message)
    results = chroma_client.search(embedding)
    context = results[0]['context'] if results else 'default'
    
    client_name = get_client_name(sender)
    prompt = f"Contexto del negocio: Venta de agroquímicos para cultivos.\nContexto del cliente: {context}\nNombre del cliente: {client_name}\nMensaje: {message}\nRespuesta:"
    
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150
    )
    
    generated_response = response.choices[0].text.strip()
    
    if 'fuera del contexto' in generated_response:
        generated_response += "\nPor favor, recuerde que nuestro negocio se centra en la venta de agroquímicos para cultivos. ¿Cómo puedo ayudarle en ese aspecto?"
    
    return generated_response
