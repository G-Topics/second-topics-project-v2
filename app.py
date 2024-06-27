from flask import Flask, request, jsonify
from services.chat_service import procesar_mensaje_recibido

app = Flask(__name__)


@app.route('/webhooks/twilio/whatsapp', methods=['POST'])
def recibir_mensaje():
    try:
        remitente = request.form.get('From')
        telefono_remitente = remitente[remitente.find('+'):]
        mensaje_recibido = request.form.get('Body')
        print("Mensaje del remitente(",telefono_remitente,"): ",mensaje_recibido)
        respuesta = procesar_mensaje_recibido(mensaje_recibido, telefono_remitente)
        return str(respuesta)
    except Exception as e:
        print(f"Error al recibir el mensaje: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
