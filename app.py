from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import pandas as pd 

app = Flask(__name__)

# --- 1. CARGA DE DATOS EN CACHÉ AL INICIO ---

def load_faqs_from_sheet():
    """
    Se conecta a Google Sheets UNA SOLA VEZ y carga todo en un DataFrame de pandas.
    Esto mejora drásticamente el rendimiento del webhook.
    """
    print("INFO: Intentando conectar con Google Sheets y cargar FAQs...")
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        cred_json_str = os.environ.get('GOOGLE_CREDENTIALS')
        if not cred_json_str:
            print("ERROR CRÍTICO: Variable de entorno GOOGLE_CREDENTIALS no encontrada.")
            return pd.DataFrame() # Devuelve un DataFrame vacío si falla

        cred_dict = json.loads(cred_json_str)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
        client = gspread.authorize(credentials)

        # Abrimos la nueva hoja de cálculo por su nombre
        spreadsheet = client.open("FAQs_intent_entidades")
        sheet = spreadsheet.sheet1
        records = sheet.get_all_records()

        # Convertimos los datos a un DataFrame de Pandas y lo devolvemos
        df = pd.DataFrame(records)
        # Reemplazamos las celdas vacías ('') con None para un filtrado más consistente
        df.replace('', pd.NA, inplace=True)
        print(f"INFO: Se cargaron {len(df)} filas de FAQs exitosamente.")
        return df
    except Exception as e:
        print(f"ERROR CRÍTICO al cargar FAQs desde Google Sheets: {e}")
        return pd.DataFrame()

# Variable global para almacenar nuestro DataFrame de FAQs
faqs_df = load_faqs_from_sheet()

# --- 2. NUEVA FUNCIÓN DE BÚSQUEDA DINÁMICA ---

def find_faq_response(df, intent, params):
    """
    Busca en el DataFrame una respuesta que coincida con la intención y
    TODAS las entidades (parámetros) recibidas desde Dialogflow.
    """
    if df.empty:
        return None

    # Primero, filtramos por la intención. Esto reduce drásticamente el universo de búsqueda.
    filtered_df = df[df['intencion'] == intent]

    # Ahora, iteramos sobre los parámetros (entidades) que Dialogflow nos envió
    for entity_name, entity_value in params.items():
        # Solo filtramos si la entidad tiene un valor y si existe como columna en nuestro DF
        if entity_value and entity_name in filtered_df.columns:
            # Filtramos el DataFrame para quedarnos solo con las filas que coinciden
            # con el valor de la entidad actual. Usamos .dropna() para ignorar celdas vacías.
            filtered_df = filtered_df.dropna(subset=[entity_name])
            filtered_df = filtered_df[filtered_df[entity_name] == entity_value]

    # Si después de todos los filtros nos queda al menos una fila, encontramos una coincidencia
    if not filtered_df.empty:
        # Devolvemos el valor de la columna 'respuesta' de la primera fila coincidente
        return filtered_df.iloc[0]['respuesta']

    # Si no queda ninguna fila, no hubo una coincidencia exacta
    return None

# --- 3. WEBHOOK ORQUESTADOR (MÁS LIMPIO) ---

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    
    intent = req['queryResult']['intent']['displayName']
    # 'parameters' es un diccionario que ya contiene TODAS las entidades detectadas
    entities = req['queryResult']['parameters']

    print(f"Intent detectado: {intent}")
    print(f"Entidades recibidas: {entities}")

    # Llamamos a nuestra nueva y potente función de búsqueda
    respuesta = find_faq_response(faqs_df, intent, entities)

    # Si la búsqueda no encontró nada, preparamos una respuesta por defecto
    if not respuesta:
        respuesta = "Lo siento, no encontré una respuesta para esa consulta específica. ¿Puedes intentar reformular tu pregunta?"

    # Devolvemos la respuesta a Dialogflow
    return jsonify({'fulfillmentText': respuesta})

# --- INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    if faqs_df.empty:
        print("ADVERTENCIA: El DataFrame de FAQs está vacío. El bot podría no responder correctamente.")
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


