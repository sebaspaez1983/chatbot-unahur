from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = Flask(__name__)

# --- NO HAY CAMBIOS AQUÍ ---
# Autenticación desde variable de entorno
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
cred_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(cred_json), scope)
client = gspread.authorize(credentials)

# Abrir la hoja
spreadsheet = client.open("BaseChatbot")
sheet = spreadsheet.sheet1
# -----------------------------

import json # Asegúrate de que esta línea esté al principio de tu archivo

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    # --- LÍNEAS DE DEPURACIÓN ---
    # Imprimimos en los logs de Render para ver exactamente qué llega
    print("--- INICIO DE LA PETICIÓN ---")
    print(f"Petición JSON completa: {json.dumps(req, indent=2)}")
    # ---------------------------

    intent = req['queryResult']['intent']['displayName']
    # Usamos el nombre que ya verificamos que es correcto
    entity_value = req['queryResult']['parameters'].get('asunto_materia', None)

    # --- MÁS LÍNEAS DE DEPURACIÓN ---
    print(f"Intención detectada: {intent}")
    print(f"Parámetros recibidos: {req['queryResult']['parameters']}")
    print(f"Valor de entidad extraído ('asunto_materia'): {entity_value}")
    print("--- FIN DE LA PETICIÓN ---")
    # -----------------------------

    respuesta = "Lo siento, no tengo una respuesta en este momento."
    rows = sheet.get_all_records()

    for row in rows:
        if entity_value:
            if row['Intencion'] == intent and row['Valor_entidad'] == entity_value:
                respuesta = row['Respuesta']
                break
        else:
            if row['Intencion'] == intent:
                respuesta = row['Respuesta']
                break

    # Una última línea de depuración antes de responder
    print(f"Respuesta final que se enviará: {respuesta}")

    return jsonify({'fulfillmentText': respuesta})
    
if __name__ == '__main__':
    # Se recomienda obtener el puerto de una variable de entorno para Render
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


