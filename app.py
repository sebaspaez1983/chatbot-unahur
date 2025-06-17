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
    
    # 1. Extraer la intención
    intent = req['queryResult']['intent']['displayName']

    # 2. Extraer el VALOR DE LA ENTIDAD de los parámetros.
    entity_value = req['queryResult']['parameters'].get('asunto_materia', None)
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Si Dialogflow envía una lista (ej: ['optatividad']), 
    # nos quedamos solo con el primer elemento.
    if isinstance(entity_value, list) and entity_value:
        entity_value = entity_value[0]
    # --- FIN DE LA CORRECCIÓN ---

    respuesta = "Lo siento, no tengo una respuesta en este momento."
    rows = sheet.get_all_records()

    # 3. Búsqueda (Esta lógica ya es correcta y no necesita cambios)
    for row in rows:
        # ESCENARIO 1: Si el intent viene con nuestra entidad
        if entity_value:
            # La condición ahora es DOBLE: debe coincidir la intención Y el valor de la entidad
            if row['Intencion'] == intent and row['Valor_entidad'] == entity_value:
                respuesta = row['Respuesta']
                break
        # ESCENARIO 2: Si el intent NO tiene la entidad
        else:
            # La lógica vuelve a ser la de antes, solo busca por intención
            if row['Intencion'] == intent:
                respuesta = row['Respuesta']
                break
                
    print("Intent:", intent)
    print("Entidad asunto_materia procesada:", entity_value) # Modificado para ver el valor final
    # print("Datos recibidos:", req) # Puedes descomentar esto para depurar si lo necesitas

    return jsonify({'fulfillmentText': respuesta})

    

if __name__ == '__main__':
    # Se recomienda obtener el puerto de una variable de entorno para Render
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


