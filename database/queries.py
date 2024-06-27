from database.connection import get_connection
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

def get_client_info(phone_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, telefono, email FROM cliente WHERE telefono = %s", (phone_number,))
    result = cursor.fetchone()
    conn.close()

    if result:
        id, nombre, telefono, correo = result
        return {
            "id" : id,
            "nombre": nombre,
            "telefono": telefono,
            "correo": correo
        }
    else:
        return None

def get_product_info():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, descripcion, modo_de_accion, precio, stock_disponible FROM producto")
    results = cursor.fetchall()
    conn.close()

    products = []
    for result in results:
        nombre, descripcion, modo_de_accion, precio, stock_disponible = result
        products.append({
            "nombre": nombre,
            "descripcion": descripcion,
            "modo_de_accion": modo_de_accion,
            "precio": precio,
            "stock_disponible": stock_disponible
        })
    
    return products

def get_application_info():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT advice FROM agricultural_advice")
    results = cursor.fetchall()
    conn.close()
    return results


def obtener_contexto():
    
    return f"El contexto principal del negocio es una tienda de productos agroquimicos, aunque también se hace asesoria de uso de productos y diagnostico sobre enfermedades de cultivo"

def obtener_historial(id_cliente):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener los IDs de las últimas tres conversaciones del cliente
        cursor.execute("""
            SELECT DISTINCT id_conversacion 
            FROM public.chat 
            WHERE id_cliente = %s  
            LIMIT 3
        """, (id_cliente,))
        conversaciones = cursor.fetchall()

        if not conversaciones:
            return []

        historial = []

        # Obtener los mensajes de cada conversación
        for conversacion in conversaciones:
            id_conversacion = conversacion['id_conversacion']
            cursor.execute("""
                SELECT mensaje_enviado, mensaje_recibido 
                FROM public.chat 
                WHERE id_conversacion = %s
            """, (id_conversacion,))
            chats = cursor.fetchall()
            
            mensajes = []
            for chat in chats:
                if chat['mensaje_enviado']:
                    mensajes.append(chat['mensaje_enviado'])
                if chat['mensaje_recibido']:
                    mensajes.append(chat['mensaje_recibido'])
            
            historial.append({
                'id_conversacion': id_conversacion,
                'mensajes': mensajes
            })
        print ("historial: ", historial)
        return historial

    finally:
        cursor.close()
        conn.close()

def obtener_informacion_bd(tipo_de_mensaje,telefono_remitente):
    if tipo_de_mensaje == "Saludos":
        client_info = get_client_info(telefono_remitente)
        if client_info:
            return (f"El nombre del cliente es {client_info['nombre']}, "
                    f"su teléfono es {client_info['telefono']} y "
                    f"su correo es {client_info['correo']}.")
        else:
            return "No se encontraron datos para el cliente con ese número de teléfono."
    elif tipo_de_mensaje == "Consulta de Producto":
        products = get_product_info()
        product_info = "Tenemos los siguientes productos disponibles:\n"
        for product in products:
            product_info += (f"Nombre: {product['nombre']}\n"
                             f"Descripción: {product['descripcion']}\n"
                             f"Modo de acción: {product['modo_de_accion']}\n"
                             f"Stock disponible: {product['stock_disponible']}\n"
                             f"Precio: ${product['precio']}\n\n")
        return product_info
    elif tipo_de_mensaje == "Consulta Técnica":
        advice = get_application_info()
        advice_info = "\n".join([a[0] for a in advice])
        return f"Aquí hay algunos consejos técnicos:\n{advice_info}"
    else:
        return f"Vendemos estos productos: Glifosato, Triazinas, Mancozeb, Benomilo, Clorpirifosy Piretroides"

def ultimo_chat_de_conversacion(conversacion_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT fecha FROM public.chat WHERE id_conversacion = %s ORDER BY fecha DESC LIMIT 1",
        (conversacion_id,)
    )
    ultimo_chat = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return ultimo_chat[0] if ultimo_chat else None

def verificar_inactividad_de_conversacion(id_cliente):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id_conversacion FROM public.chat WHERE id_cliente = %s ORDER BY fecha DESC LIMIT 1"
    cursor.execute(query, (id_cliente,))
    id_conversacion = cursor.fetchone()
    print("chat: ", id_conversacion)
    query = "SELECT id FROM public.conversacion WHERE estado = TRUE AND id = %s LIMIT 1"
    cursor.execute(query, (id_conversacion,))
    conversacion_activa = cursor.fetchone()
    
    if conversacion_activa:
        conversacion_id = conversacion_activa[0]
        fecha = ultimo_chat_de_conversacion(conversacion_id)
        if fecha and datetime.now() - fecha > timedelta(minutes=60):
            cursor.execute("UPDATE public.conversacion SET estado = FALSE WHERE id = %s", (conversacion_id,))
            conn.commit()
    
    cursor.close()
    conn.close()

def existe_conversacion_activa(id_cliente):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT id_conversacion FROM public.chat WHERE id_cliente = %s ORDER BY fecha DESC LIMIT 1"
    cursor.execute(query, (id_cliente,))
    id_conversacion = cursor.fetchone()
    print("chat: ", id_conversacion)
    query = "SELECT id FROM public.conversacion WHERE estado = TRUE AND id = %s LIMIT 1"
    cursor.execute(query, (id_conversacion,))
    conversacion_activa = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return conversacion_activa[0] if conversacion_activa else None

def crear_nueva_conversacion():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO public.conversacion (estado, fecha_inicio, fecha_fin) VALUES (%s, %s, %s) RETURNING id",
        (True, datetime.now(), datetime.now())
    )
    nueva_conversacion_id = cursor.fetchone()[0]
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return nueva_conversacion_id

def guardar_chat(mensaje_enviado, mensaje_recibido, conversacion_id, id_cliente, id_cultivo=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO public.chat (mensaje_enviado, role, id_cultivo, id_cliente, id_conversacion, fecha, mensaje_recibido) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (mensaje_enviado, 'user', 1, id_cliente, conversacion_id, datetime.now(),mensaje_recibido)
    )
    cursor.execute("UPDATE public.conversacion SET fecha_fin = %s WHERE id = %s", (datetime.now(), conversacion_id))
    
    conn.commit()
    
    cursor.close()
    conn.close()

def obtener_mensajes_enviados_de_conversacion_activa(id_cliente):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        id_conversacion = obtener_conversacion_cliente(id_cliente)
        print("id conversacion: ", id_conversacion)
        cursor.execute("SELECT id FROM public.conversacion WHERE estado = TRUE AND id = %s LIMIT 1", (id_conversacion,))
        
        conversacion_activa = cursor.fetchone()

        if not conversacion_activa:
            return []

        cursor.execute("SELECT mensaje_enviado FROM public.chat WHERE id_conversacion = %s", (conversacion_activa['id'],))
        chats = cursor.fetchall()

        mensajes = [chat['mensaje_enviado'] for chat in chats]
        return mensajes

    finally:
        cursor.close()
        conn.close()

def obtener_conversacion_cliente(id_cliente):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT id_conversacion FROM public.chat WHERE id_cliente = %s ORDER BY fecha DESC LIMIT 1"
    cursor.execute(query, (id_cliente,))
    id_conversacion = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return id_conversacion
