from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import sys
import os

# Agregar la carpeta src al path para que Python pueda encontrar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Intentar importar el NLP
try:
    from nlp.intent_matcher import IntentMatcher
    intent_matcher = IntentMatcher()
    print("✅ NLP cargado correctamente desde src/nlp/")
except Exception as e:
    print(f"⚠️ Error cargando NLP: {e}")
    intent_matcher = None

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
        "message": "Servidor funcionando correctamente"
    })

@app.route('/', methods=['GET'])
def home():
    return """
    <h1>🤖 Asistente de WhatsApp</h1>
    <p>Servidor funcionando correctamente</p>
    <p>Estado: <strong>✅ Activo</strong></p>
    <hr>
    <p>Endpoints disponibles:</p>
    <ul>
        <li><a href="/health">/health</a> - Verificar estado</li>
        <li>/webhook/twilio - Endpoint para WhatsApp (POST)</li>
    </ul>
    """

@app.route('/webhook/twilio', methods=['POST'])
def webhook_twilio():
    try:
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '').strip()
        message_sid = request.values.get('MessageSid', '')

        print(f"📩 Mensaje recibido de {from_number}: {body}")

        # Usar NLP si está disponible
        if intent_matcher:
            intent, response_text = intent_matcher.get_response(body)
            print(f"🧠 Intención detectada: {intent}")
        else:
            response_text = f"✅ Recibí tu mensaje: {body}\n\n🔧 El NLP no está disponible."

        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response_text)

        print(f"✅ Respondiendo a {from_number}")
        return str(resp)

    except Exception as e:
        print(f"❌ Error: {e}")
        resp = MessagingResponse()
        msg = resp.message()
        msg.body("⚠️ Ocurrió un error. Por favor, intenta de nuevo.")
        return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
