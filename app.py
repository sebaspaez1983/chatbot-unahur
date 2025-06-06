from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = Flask(__name__)

# Autenticación desde variable de entorno
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
cred_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(cred_json), scope)
client = gspread.authorize(credentials)

# Abrir la hoja
spreadsheet = client.open("BaseChatbot")  # <- Este debe coincidir con el nombre real de tu Google Sheet
sheet = spreadsheet.sheet1

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName']

    respuesta = "Lo siento, no tengo una respuesta en este momento."
    rows = sheet.get_all_records()

    for row in rows:
        if row['Intencion'] == intent:
            respuesta = row['Respuesta']
            break

    return jsonify({'fulfillmentText': respuesta})

if __name__ == '__main__':
    app.run(debug=True)

