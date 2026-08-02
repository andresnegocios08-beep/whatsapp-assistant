from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import os

app = Flask(__name__)

# ============================================
# CLASIFICADOR SIMPLE
# ============================================

def clasificar_mensaje(mensaje):
    mensaje = mensaje.lower()
    
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas)\b', mensaje):
        return "saludo", "¡Hola! Bienvenido al asistente. ¿En qué puedo ayudarte?"
    
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau)\b', mensaje):
        return "despedida", "¡Hasta luego! Que tengas un excelente día."
    
    if re.search(r'\b(precio|catalogo|producto|comprar|menu|cotizar|muestrame|enseñar)\b', mensaje):
        return "ventas", "¡Genial! Te ayudo con nuestra selección de productos. Tenemos:\n\n1️⃣ Ropa Deportiva\n2️⃣ Accesorios\n3️⃣ Calzado\n4️⃣ Ofertas Especiales\n\nResponde con el número de la categoría que te interesa."
    
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren)\b', mensaje):
        return "horario", "Nuestro horario de atención es de Lunes a Viernes de 8:00 AM a 6:00 PM, y Sábados de 9:00 AM a 2:00 PM."
    
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado)\b', mensaje):
        return "queja", "Lamento escuchar eso. Voy a escalar tu caso a un agente especializado."
    
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante)\b', mensaje):
        return "agente", "Te voy a conectar con un agente humano. Por favor, espera un momento."
    
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp)\b', mensaje):
        return "contacto", "Puedes contactarnos a través de:\n\n📞 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá"
    
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias)\b', mensaje):
        return "agradecimiento", "¡De nada! Es un placer ayudarte. Si necesitas algo más, aquí estoy."
    
    return "fallback", "No entendí tu mensaje. ¿Podrías reformularlo? O escribe 'agente' para hablar con un humano."


# ============================================
# RUTAS DE FLASK
# ============================================

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

        print(f"📩 Mensaje de {from_number}: {body}")

        intent, response_text = clasificar_mensaje(body)
        print(f"🧠 Intención: {intent}")

        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response_text)

        return str(resp)

    except Exception as e:
        print(f"❌ Error: {e}")
        resp = MessagingResponse()
        msg = resp.message()
        msg.body("⚠️ Error. Intenta de nuevo.")
        return str(resp)


# ============================================
# IMPORTANTE: Esto solo se ejecuta localmente
# ============================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
else:
    # En producción, gunicorn usa este objeto
    application = app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
