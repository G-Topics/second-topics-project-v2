import json
from openai import OpenAI
from config import OPENAI_API_KEY,TWILIO_SID,TWILIO_AUTH_TOKEN,TWILIO_FROM,API_KEY_DE_FILESTACK
from database.chroma_manager import cargar_bd_vectorial, generar_embedding, realizar_busqueda_semantica
from database.queries import crear_nueva_conversacion, existe_conversacion_activa,get_client_info, get_product_info, guardar_chat, obtener_contexto, obtener_historial, obtener_informacion_bd, obtener_mensajes_enviados_de_conversacion_activa, verificar_inactividad_de_conversacion
from twilio.rest import Client
from filestack import Client as FilestackClient
from models.PDF import generar_pdf

client = OpenAI(api_key=OPENAI_API_KEY,)
collection = cargar_bd_vectorial()

def procesar_mensaje_recibido(mensaje_recibido, telefono_remitente):

    embedding_de_mensaje_recibido = generar_embedding(mensaje_recibido)
    resultados_de_busqueda = realizar_busqueda_semantica(embedding_de_mensaje_recibido)
    cliente = get_client_info(telefono_remitente)
    id_cliente = cliente['id']
    print("cliente id", id_cliente)
    if resultados_de_busqueda:

        metadata_de_resultados = resultados_de_busqueda['metadatas'][0][0]
        tipo_de_mensaje = metadata_de_resultados.get('document_title', 'Documento Predeterminado')
        print("Tipo de mensaje: ",tipo_de_mensaje)
        if tipo_de_mensaje == "Cotizacion":
            mensajes = obtener_mensajes_enviados_de_conversacion_activa(id_cliente)
            print("Mensajes: ",mensajes)
            productos = get_product_info()
            cotizacion = estructurar_cotizacion(mensajes, productos)
            pdf_file_path = generar_pdf(cotizacion)
            pdf_url = subir_pdf_a_nube(pdf_file_path)
            respuesta_generada="Aquí le mandamos un cotización aproximada"
            enviar_pdf_por_twilio(telefono_remitente, respuesta_generada,pdf_url)
        else:
            contexto_de_empresa = obtener_contexto()
            historial_chat = obtener_historial(id_cliente)
            informacion_segun_tipo_mensaje = obtener_informacion_bd(tipo_de_mensaje,telefono_remitente)
            prompt = construir_prompt(contexto_de_empresa, historial_chat, informacion_segun_tipo_mensaje, mensaje_recibido)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            respuesta_generada = response.choices[0].message.content.strip()
            print("Mensaje de respuesta: ",respuesta_generada)
            enviar_mensaje(telefono_remitente,respuesta_generada)
        gestionar_historial_de_chats(mensaje_recibido,respuesta_generada,id_cliente)
    else:
        return "No se pudo identificar el tipo de mensaje"

def construir_prompt(contexto, historial_chat, informacion_segun_tipo_mensaje,mensaje_recibido):
    prompt = f"Contexto: {contexto}\n"
    if historial_chat:
        prompt += f"Historial de chat: {historial_chat}\n"
    if informacion_segun_tipo_mensaje:
        prompt += f"Información según tipo de mensaje: {informacion_segun_tipo_mensaje}\n"
    prompt += f"mensaje del cliente: {mensaje_recibido}\n"
    prompt += "responde como si fueras un personal humano del negocio de atencion al cliente, en caso de que se salen del contexto no respodas a ese mensaje y solo responde usando el contexto del negocio"
    prompt += "en caso de que te pida una cotizacion solo toma en cuenta los mensajes recibidos"
    return prompt

def enviar_mensaje(telefono_remitente, respuesta_generada):
    try:
        twilioClient = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        twilioClient.messages.create(
            to=f"whatsapp:{telefono_remitente}",
            from_=f"whatsapp:{TWILIO_FROM}",
            body=respuesta_generada
        )
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")

def gestionar_historial_de_chats(mensaje_enviado, mensaje_recibido,id_cliente):
    verificar_inactividad_de_conversacion(id_cliente)
    conversacion_id = existe_conversacion_activa(id_cliente)
    
    if conversacion_id:
        guardar_chat(mensaje_enviado, mensaje_recibido, conversacion_id,id_cliente)
    else:
        nueva_conversacion_id = crear_nueva_conversacion()
        guardar_chat(mensaje_enviado, mensaje_recibido, nueva_conversacion_id,id_cliente)

def estructurar_cotizacion(mensajes, productos):
    
    prompt = f"""
    Estructura y prepara una cotización de todos los productos mencionados por el cliente en los mensajes, incluyendo el nombre del producto, la cantidad, y el precio total de cada producto cantidad * precio. 
    La respuesta debe estar en un formato estructurado y sin saludos ni explicaciones adicionales, lista para ser pasada directamente a la librería fpdf para generar un PDF, solo respondeme el json sin ningun texto adicional.

    Mensajes del cliente:
    {mensajes}

    Información de los productos:
    {productos}

    Formato esperado de ejemplo:
    """
    
    formato = '''[
        {
            "nombre": "Herbicida Total",
            "cantidad": 10,
            "precio": 85.50
        },
        {
            "nombre": "Insecticida Pro",
            "cantidad": 5,
            "precio": 45.30
        },
        {
            "nombre": "Fungicida Max",
            "cantidad": 7,
            "precio": 60.75
        }
    ]'''
    prompt += formato
    print("Prompt: ",prompt)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
                {"role": "user", "content": prompt}
            ]
    )
    
    print("mensaje cualquiera si llega: ")
    
    cotizacion_estructurada = response.choices[0].message.content.strip()
    print("Cotizacion estructurada: ",cotizacion_estructurada)
    cotizacion = json.loads(cotizacion_estructurada)
    print("Cotizacion: ",cotizacion) 
    return cotizacion

def subir_pdf_a_nube(pdf_file_path):

    filestackClientClient = FilestackClient(API_KEY_DE_FILESTACK)
    new_filelink = filestackClientClient.upload(filepath=pdf_file_path)
    return new_filelink.url

def enviar_pdf_por_twilio(telefono_remitente, respuesta_generada, pdf_url):
    try:
        twilioClient = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        twilioClient.messages.create(
            to=f"whatsapp:{telefono_remitente}",
            from_=f"whatsapp:{TWILIO_FROM}",
            body=respuesta_generada,
            media_url=[pdf_url]
        )
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")