from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sys
import os

# Agregar la carpeta src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from nlp.intent_matcher import IntentMatcher

app = Flask(__name__)

# Crear instancia del clasificador
intent_matcher = IntentMatcher()

@app.route('/webhook/twilio', methods=['POST'])
def webhook():
    try:
        # Obtener datos del mensaje
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '').strip()
        message_sid = request.values.get('MessageSid', '')

        print(f"📩 Mensaje recibido de {from_number}: {body}")

        # CLASIFICAR INTENCIÓN
        intent, response_text = intent_matcher.get_response(body)
        print(f"🧠 Intención detectada: {intent}")

        # Crear respuesta
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response_text)

        print(f"✅ Respondiendo a {from_number}")

        return str(resp)

    except Exception as e:
        print(f"❌ Error: {e}")
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(f"⚠️ Error: {str(e)}")
        return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)