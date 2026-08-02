from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar el clasificador
try:
    from src.nlp.intent_matcher import IntentMatcher
    print("✅ NLP cargado correctamente")
except ImportError as e:
    print(f"❌ Error importando NLP: {e}")
    IntentMatcher = None

app = Flask(__name__)

# Inicializar clasificador
intent_matcher = IntentMatcher() if IntentMatcher else None

@app.route('/health', methods=['GET'])
def health_check():
    """Verificación de estado del servidor"""
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
        "message": "Servidor funcionando correctamente"
    })

@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
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
    """Endpoint para recibir mensajes de WhatsApp"""
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
            response_text = f"✅ ¡Mensaje recibido!\n\n📱 De: {from_number}\n💬 Mensaje: {body}\n\n🔧 El asistente está en desarrollo."

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
