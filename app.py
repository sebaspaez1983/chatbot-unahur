from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Configuración para acceder a Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', scope)
client = gspread.authorize(credentials)

# Abrir la hoja de cálculo
spreadsheet = client.open("BaseChatbot")  # Asegurate que este sea el nombre exacto
sheet = spreadsheet.sheet1

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName']
    
    respuesta = "Lo siento, no tengo esa información ahora."
    rows = sheet.get_all_records()

    for row in rows:
        if row['Intencion'] == intent:
            respuesta = row['Respuesta']
            break

    return jsonify({'fulfillmentText': respuesta})

if __name__ == '__main__':
    app.run(debug=True)
