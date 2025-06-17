# app.py - Código del servidor proxy inverso en Python Flask
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración del servidor final al que el proxy reenviará las peticiones
# Guarda tu dominio original de Render aquí.
# Es mejor usar una variable de entorno para la URL de destino para mayor flexibilidad.
TARGET_SERVER_URL = os.environ.get("TARGET_SERVER_URL", "https://eskate.onrender.com/index.php/skate/update")

@app.route('/proxy/skate/update', methods=['POST'])
def proxy_request():
    """
    Este endpoint recibirá las peticiones HTTP del SIM800L
    y las reenviará a tu servidor HTTPS final.
    """
    try:
        # Asegúrate de que la petición tiene el tipo de contenido correcto
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        # Obtener los datos JSON del cuerpo de la petición del SIM800L
        sim_data = request.get_json()
        print(f"Proxy - Recibido del SIM800L (HTTP): {sim_data}")

        # Reenviar la petición al servidor final (HTTPS)
        # Usamos 'verify=False' si hay problemas con certificados autofirmados,
        # pero para Render.com deberías usar el valor por defecto (True)
        # o dejarlo sin especificar, ya que manejan certificados válidos.
        response = requests.post(TARGET_SERVER_URL, json=sim_data, timeout=30) # Timeout de 30 segundos para la petición externa

        # Imprimir la respuesta del servidor final
        print(f"Proxy - Reenviado a {TARGET_SERVER_URL} (HTTPS). Status: {response.status_code}")
        print(f"Proxy - Respuesta del servidor final: {response.text}")

        # Devolver la respuesta del servidor final al SIM800L
        # El SIM800L espera OK o un error HTTP, no necesita JSON de vuelta.
        return response.text, response.status_code, response.headers.items()

    except Exception as e:
        print(f"Proxy - Error procesando la petición: {e}")
        return jsonify({"error": f"Error interno del proxy: {str(e)}"}), 500

if __name__ == '__main__':
    # Usamos 0.0.0.0 para que Flask escuche en todas las interfaces disponibles,
    # lo cual es necesario en entornos de contenedores como Render.
    app.run(host='0.0.0.0', port=10000) # Render asignará un puerto, 10000 es un valor común para apps web