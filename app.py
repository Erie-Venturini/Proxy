# app.py - CÓDIGO DEL PROXY SIMPLIFICADO Y RECOMENDADO PARA RENDER.COM
from flask import Flask, request, jsonify
import requests
import os
import json # Necesario para json.dumps, si aún no lo tienes

app = Flask(__name__)

TARGET_SERVER_URL = os.environ.get("TARGET_SERVER_URL", "https://eskate.onrender.com/index.php/skate/update")

@app.route('/proxy/skate/update', methods=['POST'])
def proxy_request():
    try:
        if not request.is_json:
            print("Proxy: Content-Type no es application/json")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        sim_data = request.get_json()
        print(f"Proxy - Recibido del SIM800L (HTTP): {sim_data}")
        print(f"Headers recibidos: {dict(request.headers)}") 
        print(f"Datos recibidos (raw): {request.data.decode('utf-8', 'ignore')}") 

        response = requests.post(TARGET_SERVER_URL, json=sim_data, timeout=30) 

        print(f"Proxy - Reenviado a {TARGET_SERVER_URL} (HTTPS). Status: {response.status_code}")
        print(f"Proxy - Respuesta del servidor final: {response.text}")

        # --- ESTA ES LA RESPUESTA SIMPLIFICADA PARA EL SIM800L ---
        response_data_for_sim = {
            "status": "success",
            "code": response.status_code, 
            "message": "Datos recibidos y reenviados"
        }
        json_response_for_sim = json.dumps(response_data_for_sim)

        return json_response_for_sim, response.status_code, {
            'Content-Type': 'application/json',
            'Connection': 'close', 
            'Content-Length': str(len(json_response_for_sim.encode('utf-8')))
        }
        # --- FIN DE LA RESPUESTA SIMPLIFICADA ---

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
    port = int(os.environ.get("PORT", 10000))
    print(f"Proxy Flask iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port)