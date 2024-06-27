import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_message_embedding(message):
    response = openai.Embedding.create(
        input=message,
        model='text-embedding-ada-002'
    )
    return response['data'][0]['embedding']
