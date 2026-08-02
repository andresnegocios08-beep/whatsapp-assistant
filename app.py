from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar gestor de contexto
try:
    from context_manager import ContextManager
    context_manager = ContextManager()
    print("✅ ContextManager cargado correctamente")
except Exception as e:
    print(f"⚠️ Error cargando ContextManager: {e}")
    context_manager = None

app = Flask(__name__)

# ============================================
# CLASIFICADOR DE INTENCIONES CON CONTEXTO
# ============================================

def clasificar_mensaje(mensaje, user_id=None):
    mensaje = mensaje.lower().strip()
    
    # Obtener contexto si existe
    last_intent = None
    if user_id and context_manager:
        session = context_manager.get(user_id)
        last_intent = session.get("last_intent")
        print(f"🔍 Contexto de {user_id}: última intención = {last_intent}")
    
    # ============================================
    # CONTEXTO: RESPUESTA A SELECCIÓN DE CATEGORÍA
    # ============================================
    if last_intent == "ventas":
        if re.match(r'^[1-4]$', mensaje):
            categorias = {
                "1": "Ropa Deportiva",
                "2": "Accesorios",
                "3": "Calzado",
                "4": "Ofertas Especiales"
            }
            categoria = categorias.get(mensaje, "Categoría no válida")
            if categoria != "Categoría no válida":
                if context_manager:
                    context_manager.set(user_id, "last_intent", "categoria_seleccionada")
                    context_manager.set(user_id, "categoria", categoria)
                return "categoria_seleccionada", f"✅ Has seleccionado: **{categoria}**\n\n📋 ¿Qué te gustaría hacer?\n\n1️⃣ Ver productos disponibles\n2️⃣ Pedir información sobre precios\n3️⃣ Volver al catálogo principal\n\n💡 Responde con el número de tu opción."
        # Si no es un número del 1-4, verificar si es otro comando
        if re.search(r'\b(catalogo|producto|menu|volver|inicio)\b', mensaje):
            return "ventas", get_ventas_response()
    
    # ============================================
    # CONTEXTO: MENÚ DE CATEGORÍA
    # ============================================
    if last_intent == "categoria_seleccionada":
        if re.match(r'^[1-3]$', mensaje):
            if mensaje == "1":
                if context_manager:
                    context_manager.set(user_id, "last_intent", None)
                    categoria = context_manager.get(user_id).get("context", {}).get("categoria", "")
                return "ver_productos", f"📦 **Productos en {categoria or 'esta categoría'}:**\n\nPara ver el catálogo completo, visita nuestro sitio web.\n\n🔍 ¿Buscas algo en particular? Dímelo y te ayudo.\n\n💡 Escribe 'volver' para regresar al catálogo."
            elif mensaje == "2":
                return "info_precios", "💰 **Información de precios:**\n\nNuestros precios varían según el producto.\n\n📋 Para cotizaciones específicas, escríbenos el nombre del producto que te interesa.\n\n💡 ¿Qué producto te gustaría cotizar?"
            elif mensaje == "3":
                if context_manager:
                    context_manager.set(user_id, "last_intent", "ventas")
                return "volver", "🔄 Volviendo al catálogo principal...\n\n" + get_ventas_response()
        
        # Si el usuario escribe "volver" desde este contexto
        if re.search(r'\b(volver|atras|inicio|catalogo)\b', mensaje):
            if context_manager:
                context_manager.set(user_id, "last_intent", "ventas")
            return "volver", "🔄 Volviendo al catálogo principal...\n\n" + get_ventas_response()
    
    # ============================================
    # INTENCIONES PRINCIPALES
    # ============================================
    
    # Saludo
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas|hola que tal)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "saludo")
        return "saludo", "¡Hola! 👋 Bienvenido al asistente. ¿En qué puedo ayudarte hoy?\n\n📋 Escribe **'catalogo'** para ver nuestros productos.\n💡 Escribe **'ayuda'** para ver qué puedo hacer."
    
    # Ventas/Catálogo
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|comprar|lista|que venden|tienen)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "ventas")
        return "ventas", get_ventas_response()
    
    # Precio/Cotización
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "precio")
        return "precio", "💰 Te ayudo con los precios.\n\n📋 Escribe el **nombre del producto** que te interesa y te daré la información.\n\n💡 Ejemplo: 'precio de la camisa deportiva'"
    
    # Horario
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "horario")
        return "horario", "🕐 **Horario de atención:**\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado\n\n📞 ¿Necesitas algo más?"
    
    # Queja/Problema
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "queja")
        return "queja", "📞 Lamento escuchar eso. Voy a escalar tu caso a un agente especializado que te ayudará personalmente.\n\n⏳ Por favor, espera un momento. Te contactaremos a la brevedad."
    
    # Agente humano
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante|atencion personal)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "agente")
        return "agente", "👤 Te voy a conectar con un agente humano.\n\n⏳ Por favor, espera un momento mientras te asignamos al mejor asesor para ti."
    
    # Contacto
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "contacto")
        return "contacto", "📞 **Información de contacto:**\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá\n\n🌐 WhatsApp: +57 301 234 5678"
    
    # Agradecimiento
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido|excelente servicio)\b', mensaje):
        return "agradecimiento", "¡De nada! 😊 Es un placer ayudarte.\n\n💡 Si necesitas algo más, aquí estoy.\n👋 Escribe **'agente'** para hablar con un asesor."
    
    # Ayuda
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu)\b', mensaje):
        if context_manager:
            context_manager.set(user_id, "last_intent", "ayuda")
        return "ayuda", get_ayuda_response()
    
    # Fallback
    return "fallback", "🤔 No entendí tu mensaje.\n\n📋 Escribe **'ayuda'** para ver qué puedo hacer.\n👤 Escribe **'agente'** para hablar con un humano.\n\n💡 Ejemplos de lo que puedes preguntar:\n- 'catalogo'\n- 'precio de la camisa'\n- 'horario'\n- 'contacto'"


def get_ventas_response():
    return """🛍️ **¡Bienvenido a nuestro catálogo!**

📋 **Categorías disponibles:**

1️⃣ Ropa Deportiva
2️⃣ Accesorios
3️⃣ Calzado
4️⃣ Ofertas Especiales

💡 **Responde con el número** de la categoría que te interesa.
🔍 O escribe el nombre de lo que buscas.
👤 Escribe **'agente'** para hablar con un asesor.

📞 ¿Quieres atención personalizada? Escribe **'agente'**."""


def get_ayuda_response():
    return """🤖 **Qué puedo hacer por ti:**

📦 **Catálogo** - Ver productos y categorías
💰 **Precios** - Consultar precios y cotizaciones
🕐 **Horario** - Conocer nuestra atención
📍 **Contacto** - Teléfono, email y dirección
👤 **Agente** - Hablar con un asesor humano
❓ **Preguntas** - Resolver dudas comunes

💡 **Cómo usar el asistente:**

1️⃣ Escribe **'catalogo'** para ver categorías
2️⃣ Responde con el **número** de la categoría
3️⃣ Sigue las opciones del menú

👋 Escribe **'agente'** para hablar con un humano."""


# ============================================
# ENDPOINTS DE FLASK
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    sessions_count = len(context_manager.sessions) if context_manager else 0
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
        "message": "Servidor funcionando correctamente",
        "sessions": sessions_count,
        "context_manager": "activo" if context_manager else "inactivo"
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

        # Guardar historial
        if context_manager:
            context_manager.add_history(from_number, body, intent, response_text)

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
    app.run(host='0.0.0.0', port=5000, debug=True)