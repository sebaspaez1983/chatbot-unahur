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

@app.route('/webhook', methods=['POST'])
def webhook():
    # Se recomienda usar silent=True y force=True para mayor robustez
    req = request.get_json(silent=True, force=True)
    
    # 1. Extraer la intención (esto sigue igual)
    intent = req['queryResult']['intent']['displayName']

    # --- INICIO DE LA MODIFICACIÓN ---

    # 2. Extraer el VALOR DE LA ENTIDAD de los parámetros de Dialogflow.
    # El nombre del parámetro ('asunto_materia') debe coincidir EXACTAMENTE
    # con el nombre de tu entidad en Dialogflow.
    # Usamos .get() para que no de error si un intent no tiene esta entidad.
    entity_value = req['queryResult']['parameters'].get('asunto_materia', None)
    
    # ---------------------------------

    respuesta = "Lo siento, no tengo una respuesta en este momento."
    rows = sheet.get_all_records()

    # 3. Búsqueda modificada: ahora considera la entidad
    for row in rows:
        # ESCENARIO 1: Si el intent viene con nuestra entidad (ej: consultar_info_materias)
        if entity_value:
            # La condición ahora es DOBLE: debe coincidir la intención Y el valor de la entidad
            if row['Intencion'].strip().lower() == intent.strip().lower() and  row['Valor_entidad'].strip().lower() == entity_value.strip().lower():
                respuesta = row['Respuesta']
                break
        # ESCENARIO 2: Si el intent NO tiene la entidad (ej: un saludo o despedida)
        else:
            # La lógica vuelve a ser la de antes, solo busca por intención
            if row['Intencion'].strip().lower() == intent.strip().lower():
                respuesta = row['Respuesta']
                break
    
    # --- FIN DE LA MODIFICACIÓN ---

    return jsonify({'fulfillmentText': respuesta})

if __name__ == '__main__':
    # Se recomienda obtener el puerto de una variable de entorno para Render
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


