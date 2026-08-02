from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import json
import os
from datetime import datetime

app = Flask(__name__)

# ============================================
# GESTOR DE SESIONES Y CONTEXTO
# ============================================

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_file = "data/sessions.json"
        self._load_sessions()
    
    def _load_sessions(self):
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    self.sessions = json.load(f)
        except:
            self.sessions = {}
    
    def _save_sessions(self):
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except:
            pass
    
    def get_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "last_intent": None,
                "context": {},
                "history": [],
                "last_activity": datetime.now().isoformat()
            }
            self._save_sessions()
        return self.sessions[user_id]
    
    def update_session(self, user_id, intent=None, context=None, message=None):
        session = self.get_session(user_id)
        if intent:
            session["last_intent"] = intent
        if context:
            session["context"].update(context)
        if message:
            session["history"].append({
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            if len(session["history"]) > 100:
                session["history"] = session["history"][-100:]
        session["last_activity"] = datetime.now().isoformat()
        self._save_sessions()
    
    def clear_session(self, user_id):
        if user_id in self.sessions:
            del self.sessions[user_id]
            self._save_sessions()

session_manager = SessionManager()

# ============================================
# CLASIFICADOR DE INTENCIONES CON CONTEXTO
# ============================================

def clasificar_mensaje(mensaje, user_id=None):
    mensaje = mensaje.lower().strip()
    
    # Obtener sesión si existe
    session = None
    if user_id:
        session = session_manager.get_session(user_id)
        last_intent = session.get("last_intent")
    else:
        last_intent = None
    
    # ==== CONTEXTO: RESPUESTA A SELECCIÓN DE CATEGORÍA ====
    if last_intent == "ventas" and re.match(r'^[1-4]$', mensaje):
        categorias = {
            "1": "Ropa Deportiva",
            "2": "Accesorios",
            "3": "Calzado",
            "4": "Ofertas Especiales"
        }
        return "categoria_seleccionada", f"✅ Has seleccionado: {categorias.get(mensaje, 'Categoría no válida')}\n\n📋 ¿Qué te gustaría hacer?\n1️⃣ Ver productos\n2️⃣ Pedir información\n3️⃣ Volver al catálogo\n\nResponde con el número de tu opción."
    
    # ==== CONTEXTO: MENÚ DE CATEGORÍA ====
    if last_intent == "categoria_seleccionada" and re.match(r'^[1-3]$', mensaje):
        opciones = {
            "1": "Te muestro los productos disponibles de esa categoría. ¿Qué buscas en particular?",
            "2": "Puedes preguntarme sobre precios, disponibilidad o materiales. ¿Qué necesitas saber?",
            "3": "Volviendo al catálogo principal..."
        }
        if mensaje == "3":
            return "ventas", "🔄 Volviendo al catálogo...\n\n" + get_ventas_response()
        return "menu_categoria", opciones.get(mensaje, "Opción no válida.")
    
    # ==== INTENCIONES PRINCIPALES ====
    
    # Saludo
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas|hola que tal)\b', mensaje):
        return "saludo", "¡Hola! Bienvenido al asistente. ¿En qué puedo ayudarte?"
    
    # Despedida
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau|me voy)\b', mensaje):
        return "despedida", "¡Hasta luego! Que tengas un excelente día. 👋"
    
    # Ventas/Catálogo
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|comprar|lista|que venden|tienen)\b', mensaje):
        return "ventas", get_ventas_response()
    
    # Precio/Cotización
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion)\b', mensaje):
        return "precio", "💰 Te ayudo con los precios. ¿Qué producto te interesa? Puedes decirme el nombre o la categoría."
    
    # Horario
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas)\b', mensaje):
        return "horario", "🕐 Nuestro horario de atención es:\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado"
    
    # Queja/Problema
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje):
        return "queja", "Lamento escuchar eso. 📞 Voy a escalar tu caso a un agente especializado que te ayudará personalmente. Por favor, espera un momento."
    
    # Agente humano
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante|atencion personal)\b', mensaje):
        return "agente", "👤 Te voy a conectar con un agente humano. Por favor, espera un momento mientras te asignamos al mejor asesor para ti."
    
    # Contacto
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan)\b', mensaje):
        return "contacto", "📞 Puedes contactarnos a través de:\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá\n\n🌐 WhatsApp: +57 301 234 5678"
    
    # Agradecimiento
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido|excelente servicio)\b', mensaje):
        return "agradecimiento", "¡De nada! 😊 Es un placer ayudarte. Si necesitas algo más, aquí estoy. ¡Que tengas un excelente día!"
    
    # Ayuda
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu)\b', mensaje):
        return "ayuda", get_ayuda_response()
    
    # Fallback
    return "fallback", "No entendí tu mensaje. ¿Podrías reformularlo?\n\n📋 Escribe 'ayuda' para ver qué puedo hacer, o 'agente' para hablar con un humano."


def get_ventas_response():
    return """🛍️ ¡Genial! Te ayudo con nuestra selección de productos.

📋 **Categorías disponibles:**

1️⃣ Ropa Deportiva
2️⃣ Accesorios
3️⃣ Calzado
4️⃣ Ofertas Especiales

💡 Responde con el **número de la categoría** que te interesa.
🔍 O escribe el nombre de lo que buscas.
👤 Escribe 'agente' para hablar con un asesor."""


def get_ayuda_response():
    return """🤖 **Qué puedo hacer por ti:**

📦 **Catálogo** - Ver productos y categorías
💰 **Precios** - Consultar precios y cotizaciones
🕐 **Horario** - Conocer nuestra atención
📍 **Contacto** - Teléfono, email y dirección
👤 **Agente** - Hablar con un asesor humano
❓ **Preguntas** - Resolver dudas comunes

💡 Escribe lo que necesitas y te ayudaré.
👋 Escribe 'agente' para hablar con un humano."""


# ============================================
# ENDPOINTS DE FLASK
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
        "message": "Servidor funcionando correctamente",
        "sessions": len(session_manager.sessions)
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

        print(f"📩 Mensaje de {from_number}: {body}")

        # Clasificar con contexto
        intent, response_text = clasificar_mensaje(body, from_number)
        print(f"🧠 Intención: {intent}")

        # Actualizar sesión
        session_manager.update_session(from_number, intent, {}, body)

        # Enviar respuesta
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