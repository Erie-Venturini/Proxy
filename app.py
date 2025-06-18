# app.py - Código del servidor proxy inverso en Python Flask para Render.com
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración del servidor final al que el proxy reenviará las peticiones
# Guarda tu dominio original de Render aquí.
# Render.com utiliza variables de entorno para una configuración flexible.
# ASEGÚRATE de que esta URL APUNTE A TU SERVIDOR FINAL HTTPS.
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
            print("Proxy: Content-Type no es application/json")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        # Obtener los datos JSON del cuerpo de la petición del SIM800L
        sim_data = request.get_json()
        print(f"Proxy - Recibido del SIM800L (HTTP): {sim_data}")

        # Reenviar la petición al servidor final (HTTPS)
        # requests por defecto verifica certificados SSL (verify=True), lo cual es seguro.
        # No necesitas verify=False si tu servidor final tiene un certificado válido (como Render.com).
        response = requests.post(TARGET_SERVER_URL, json=sim_data, timeout=30) # Timeout de 30 segundos para la petición externa

        # Imprimir la respuesta del servidor final
        print(f"Proxy - Reenviado a {TARGET_SERVER_URL} (HTTPS). Status: {response.status_code}")
        print(f"Proxy - Respuesta del servidor final: {response.text}")

        # Devolver la respuesta del servidor final al SIM800L
        # Reconstruimos una respuesta HTTP básica para el SIM800L
        response_headers_str = ""
        for k, v in response.headers.items():
            # Evitar encabezados de transferencia que el SIM800L podría no manejar bien
            # y también Content-Encoding si requests lo descomprime automáticamente
            if k.lower() not in ['transfer-encoding', 'content-encoding']:
                response_headers_str += f"{k}: {v}\r\n"

        response_to_sim = (
            f"HTTP/1.1 {response.status_code} {response.reason}\r\n"
            f"{response_headers_str}"
            f"Connection: close\r\n" # Indicar al SIM800L que cierre la conexión
            "\r\n"
        ).encode('utf-8') + response.content # Adjuntar el cuerpo de la respuesta original
        
        return response_to_sim, response.status_code

    except json.JSONDecodeError as e:
        print(f"Proxy - Error al decodificar JSON del SIM800L: {e}. Cuerpo recibido (posiblemente no JSON):\n{request.data.decode('utf-8', 'ignore')}")
        return jsonify({"error": f"Bad Request: JSON mal formado: {str(e)}"}), 400
    except requests.exceptions.Timeout:
        print("Proxy - Timeout al reenviar petición a servidor final (Render).")
        return jsonify({"error": "Gateway Timeout: Servidor final no responde a tiempo."}), 504
    except requests.exceptions.ConnectionError as e:
        print(f"Proxy - Error de conexión al servidor final (Render): {e}")
        return jsonify({"error": "Bad Gateway: No se pudo conectar al servidor final."}), 502
    except Exception as e:
        print(f"Proxy - Error general al procesar/reenviar petición: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    # Usamos 0.0.0.0 para que Flask escuche en todas las interfaces disponibles.
    # Render asignará un puerto dinámico (generalmente a través de la variable de entorno PORT).
    # Por lo tanto, el script debe escuchar en el puerto proporcionado por Render.
    port = int(os.environ.get("PORT", 10000)) # Render usa la variable PORT
    print(f"Proxy Flask iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port)