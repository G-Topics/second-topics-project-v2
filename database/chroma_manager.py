import re
import os
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY,)
settings = Settings(persist_directory="local_db")
chroma_client = chromadb.Client(settings)

def cargar_bd_vectorial():
    collection = chroma_client.get_or_create_collection(name="docs_collection")

    file_path = os.path.join(os.path.dirname(__file__), '../resources/chroma/data.txt')
    with open(file_path, 'r') as file:
        content = file.read()
        chunks = split_text(content)
        generate_embeddings(chunks, file_path, collection)
    
    
    return collection

def generate_embeddings(chunks, file_name, collection):
    document_id = 1  
    for chunk in chunks:
        document_title = get_title(chunk)
        embedding = generar_embedding(chunk)
        collection.add(
            metadatas=[{
                "document_title": document_title if document_title else "Untitled Document",
                "file_name": file_name
            }],
            documents=[chunk],
            ids=[str(document_id)],
            embeddings=[embedding]
        )
        document_id += 1

def generar_embedding(chunk):
    response = client.embeddings.create(input=chunk, model='text-embedding-ada-002')
    embedding = response.data[0].embedding
    return embedding

def get_title(content):
    lines = content.strip().split('\n')
    first_line = lines[0].strip()
    match = re.match(r"^### (.+)", first_line)
    if match:
        return match.group(1)
    else:
        return "Sin Título"

def split_text(content):
    separator = "\n### "
    marcador = "### "
    chunks = content.split(separator)
    chunks = [chunks[0]] + [marcador + chunk for chunk in chunks[1:]]
    return chunks

def get_message_embedding(message):
    response = client.embeddings.create(input=message, model='text-embedding-ada-002')
    embedding = response['data'][0]['embedding']
    return embedding

def realizar_busqueda_semantica(embedding):
    collection = chroma_client.get_or_create_collection(name="docs_collection")
    results = collection.query(
        query_embeddings=[embedding],
        n_results=2,
    )
    return results
