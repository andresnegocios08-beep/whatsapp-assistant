from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import os
import sys

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar base de datos
try:
    from src.database import db
    print("✅ Base de datos cargada")
except Exception as e:
    print(f"⚠️ Error cargando base de datos: {e}")
    db = None

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mi-clave-secreta')

# ============================================
# CONTEXTO EN MEMORIA
# ============================================

contexto_usuarios = {}

# ============================================
# PROCESADOR DE MENSAJES
# ============================================

def clasificar_mensaje(mensaje, user_id):
    mensaje = mensaje.lower().strip()
    
    # Obtener contexto
    if user_id not in contexto_usuarios:
        contexto_usuarios[user_id] = {
            "ultima_intencion": None,
            "categoria": None,
            "paso": None
        }
    
    ctx = contexto_usuarios[user_id]
    ultima_intencion = ctx.get("ultima_intencion")
    
    print(f"📩 '{mensaje}' | Última intención: {ultima_intencion}")
    
    # ============================================
    # CASO: DESPUÉS DE CATÁLOGO
    # ============================================
    if ultima_intencion == "ventas" and mensaje in ["1", "2", "3", "4"]:
        categorias = {
            "1": "Ropa Deportiva",
            "2": "Accesorios",
            "3": "Calzado",
            "4": "Ofertas Especiales"
        }
        categoria = categorias[mensaje]
        ctx["ultima_intencion"] = "categoria_seleccionada"
        ctx["categoria"] = categoria
        
        return f"✅ Has seleccionado: **{categoria}**\n\n📋 ¿Qué te gustaría hacer?\n\n1️⃣ Ver productos disponibles\n2️⃣ Pedir información sobre precios\n3️⃣ Volver al catálogo principal"
    
    # ============================================
    # CASO: MENÚ DE CATEGORÍA
    # ============================================
    if ultima_intencion == "categoria_seleccionada":
        if mensaje == "1":
            ctx["ultima_intencion"] = None
            return "📦 **Productos:**\n\nPara ver el catálogo completo, visita nuestro sitio web.\n\n🔍 ¿Buscas algo en particular? Dímelo y te ayudo."
        
        elif mensaje == "2":
            ctx["ultima_intencion"] = None
            return "💰 **Información de precios:**\n\nPara cotizaciones específicas, escríbenos el nombre del producto."
        
        elif mensaje == "3":
            ctx["ultima_intencion"] = "ventas"
            return "🔄 Volviendo al catálogo...\n\n" + get_catalogo()
        
        elif "volver" in mensaje or "atras" in mensaje:
            ctx["ultima_intencion"] = "ventas"
            return "🔄 Volviendo al catálogo...\n\n" + get_catalogo()
    
    # ============================================
    # INTENCIÓN: CATÁLOGO
    # ============================================
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|lista|que venden|tienen|catagalo|catgalo)\b', mensaje):
        ctx["ultima_intencion"] = "ventas"
        return get_catalogo()
    
    # ============================================
    # INTENCIÓN: PRECIO
    # ============================================
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion|presio)\b', mensaje):
        ctx["ultima_intencion"] = "precio"
        return "💰 Te ayudo con los precios.\n\n📋 Escribe el **nombre del producto** que te interesa."
    
    # ============================================
    # INTENCIÓN: HORARIO
    # ============================================
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas|horairo|horaro)\b', mensaje):
        return "🕐 **Horario de atención:**\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado"
    
    # ============================================
    # INTENCIÓN: CONTACTO
    # ============================================
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan|contato)\b', mensaje):
        return "📞 **Información de contacto:**\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá"
    
    # ============================================
    # INTENCIÓN: QUEJA
    # ============================================
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje):
        return "📞 Lamento escuchar eso. Voy a escalar tu caso a un agente especializado."
    
    # ============================================
    # INTENCIÓN: AGENTE
    # ============================================
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante|agte)\b', mensaje):
        return "👤 Te voy a conectar con un agente humano. Por favor, espera un momento."
    
    # ============================================
    # INTENCIÓN: SALUDO
    # ============================================
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas|hola que tal)\b', mensaje):
        return "¡Hola! 👋 Bienvenido al asistente.\n\n📋 Escribe **'catalogo'** para ver nuestros productos.\n👤 Escribe **'agente'** para hablar con un asesor."
    
    # ============================================
    # INTENCIÓN: AGRADECIMIENTO
    # ============================================
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido|grasias|graxias)\b', mensaje):
        return "¡De nada! 😊 Es un placer ayudarte."
    
    # ============================================
    # INTENCIÓN: AYUDA
    # ============================================
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu|aydua)\b', mensaje):
        return get_ayuda()
    
    # ============================================
    # INTENCIÓN: DESPEDIDA
    # ============================================
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau|me voy|adio)\b', mensaje):
        if user_id in contexto_usuarios:
            del contexto_usuarios[user_id]
        return "¡Hasta luego! 👋 Que tengas un excelente día."
    
    # ============================================
    # FALLBACK
    # ============================================
    return "🤔 No entendí tu mensaje.\n\n📋 Escribe **'ayuda'** para ver qué puedo hacer.\n👤 Escribe **'agente'** para hablar con un humano."


def get_catalogo():
    return """🛍️ **Catálogo de productos:**

📋 **Categorías disponibles:**

1️⃣ Ropa Deportiva
2️⃣ Accesorios
3️⃣ Calzado
4️⃣ Ofertas Especiales

💡 **Responde con el número** de la categoría que te interesa."""


def get_ayuda():
    return """🤖 **Qué puedo hacer por ti:**

📦 **Catálogo** - Escribe 'catalogo'
💰 **Precios** - Escribe 'precio'
🕐 **Horario** - Escribe 'horario'
📍 **Contacto** - Escribe 'contacto'
👤 **Agente** - Escribe 'agente'
❓ **Ayuda** - Escribe 'ayuda'

💡 **Flujo de catálogo:**
1️⃣ Escribe 'catalogo'
2️⃣ Responde con un número del 1 al 4
3️⃣ Sigue las opciones del menú"""


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
        "database": "connected" if db else "not connected"
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
        <li><a href="/stats">/stats</a> - Estadísticas</li>
        <li>/webhook/twilio - Endpoint para WhatsApp (POST)</li>
    </ul>
    """

@app.route('/webhook/twilio', methods=['POST'])
def webhook_twilio():
    try:
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '').strip()

        print(f"\n📩 Mensaje de {from_number}: '{body}'")

        # Clasificar mensaje
        response_text = clasificar_mensaje(body, from_number)
        
        # Guardar en base de datos
        if db:
            try:
                # Extraer intención del contexto
                intent = contexto_usuarios.get(from_number, {}).get("ultima_intencion", "unknown")
                db.save_conversation(from_number, body, intent, response_text)
            except Exception as e:
                print(f"⚠️ Error guardando en DB: {e}")

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


@app.route('/stats', methods=['GET'])
def get_stats():
    """Endpoint para ver estadísticas"""
    if db:
        stats = db.get_stats()
        return jsonify(stats)
    return jsonify({"error": "Base de datos no disponible"}), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
