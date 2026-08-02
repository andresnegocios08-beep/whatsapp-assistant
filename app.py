from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re

app = Flask(__name__)

# ============================================
# CONTEXTO EN MEMORIA (SIMPLIFICADO)
# ============================================

# Diccionario global para guardar el contexto de cada usuario
contexto_usuarios = {}

def obtener_contexto(user_id):
    """Obtiene el contexto de un usuario, o lo crea si no existe"""
    if user_id not in contexto_usuarios:
        contexto_usuarios[user_id] = {
            "ultima_intencion": None,
            "categoria": None,
            "paso": None
        }
    return contexto_usuarios[user_id]

def guardar_contexto(user_id, clave, valor):
    """Guarda un valor en el contexto del usuario"""
    contexto = obtener_contexto(user_id)
    contexto[clave] = valor
    print(f"📝 Contexto guardado - {user_id}: {clave} = {valor}")

def limpiar_contexto(user_id):
    """Limpia el contexto del usuario"""
    if user_id in contexto_usuarios:
        contexto_usuarios[user_id] = {
            "ultima_intencion": None,
            "categoria": None,
            "paso": None
        }
        print(f"🧹 Contexto limpiado para {user_id}")

# ============================================
# CLASIFICADOR DE INTENCIONES
# ============================================

def clasificar_mensaje(mensaje, user_id):
    mensaje = mensaje.lower().strip()
    
    # Obtener contexto del usuario
    ctx = obtener_contexto(user_id)
    ultima_intencion = ctx.get("ultima_intencion")
    categoria_actual = ctx.get("categoria")
    paso = ctx.get("paso")
    
    print(f"🔍 Contexto de {user_id}:")
    print(f"   - Última intención: {ultima_intencion}")
    print(f"   - Categoría actual: {categoria_actual}")
    print(f"   - Paso: {paso}")
    
    # ============================================
    # CONTEXTO: DESPUÉS DE SELECCIONAR CATEGORÍA
    # ============================================
    if ultima_intencion == "ventas" and mensaje in ["1", "2", "3", "4"]:
        categorias = {
            "1": "Ropa Deportiva",
            "2": "Accesorios",
            "3": "Calzado",
            "4": "Ofertas Especiales"
        }
        categoria = categorias[mensaje]
        
        # Guardar en contexto
        guardar_contexto(user_id, "ultima_intencion", "categoria_seleccionada")
        guardar_contexto(user_id, "categoria", categoria)
        
        return f"✅ Has seleccionado: **{categoria}**\n\n📋 ¿Qué te gustaría hacer?\n\n1️⃣ Ver productos disponibles\n2️⃣ Pedir información sobre precios\n3️⃣ Volver al catálogo principal\n\n💡 Responde con el número de tu opción."
    
    # ============================================
    # CONTEXTO: MENÚ DE CATEGORÍA
    # ============================================
    if ultima_intencion == "categoria_seleccionada":
        if mensaje == "1":
            categoria = ctx.get("categoria", "esta categoría")
            guardar_contexto(user_id, "ultima_intencion", "ver_productos")
            return f"📦 **Productos en {categoria}:**\n\nPara ver el catálogo completo, visita nuestro sitio web.\n\n🔍 ¿Buscas algo en particular? Dímelo y te ayudo.\n\n💡 Escribe 'volver' para regresar al catálogo."
        
        elif mensaje == "2":
            guardar_contexto(user_id, "ultima_intencion", "info_precios")
            return "💰 **Información de precios:**\n\nNuestros precios varían según el producto.\n\n📋 Para cotizaciones específicas, escríbenos el nombre del producto que te interesa.\n\n💡 ¿Qué producto te gustaría cotizar?"
        
        elif mensaje == "3":
            guardar_contexto(user_id, "ultima_intencion", "ventas")
            return "🔄 Volviendo al catálogo principal...\n\n" + get_catalogo()
        
        elif "volver" in mensaje or "atras" in mensaje or "catalogo" in mensaje:
            guardar_contexto(user_id, "ultima_intencion", "ventas")
            return "🔄 Volviendo al catálogo principal...\n\n" + get_catalogo()
    
    # ============================================
    # INTENCIONES PRINCIPALES
    # ============================================
    
    # SALUDO
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "saludo")
        return "¡Hola! 👋 Bienvenido al asistente.\n\n📋 Escribe **'catalogo'** para ver nuestros productos.\n💡 Escribe **'ayuda'** para ver qué puedo hacer."
    
    # CATÁLOGO
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|lista|que venden|tienen)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "ventas")
        return get_catalogo()
    
    # PRECIO
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "precio")
        return "💰 Te ayudo con los precios.\n\n📋 Escribe el **nombre del producto** que te interesa y te daré la información."
    
    # HORARIO
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "horario")
        return "🕐 **Horario de atención:**\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado"
    
    # QUEJA
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "queja")
        return "📞 Lamento escuchar eso. Voy a escalar tu caso a un agente especializado.\n\n⏳ Por favor, espera un momento."
    
    # AGENTE
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "agente")
        return "👤 Te voy a conectar con un agente humano.\n\n⏳ Por favor, espera un momento."
    
    # CONTACTO
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan)\b', mensaje):
        guardar_contexto(user_id, "ultima_intencion", "contacto")
        return "📞 **Información de contacto:**\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá"
    
    # AGRADECIMIENTO
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido)\b', mensaje):
        return "¡De nada! 😊 Es un placer ayudarte.\n\n💡 Si necesitas algo más, aquí estoy."
    
    # AYUDA
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu)\b', mensaje):
        return get_ayuda()
    
    # DESPEDIDA
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau|me voy)\b', mensaje):
        limpiar_contexto(user_id)
        return "¡Hasta luego! 👋 Que tengas un excelente día."
    
    # FALLBACK
    return "🤔 No entendí tu mensaje.\n\n📋 Escribe **'ayuda'** para ver qué puedo hacer.\n👤 Escribe **'agente'** para hablar con un humano."


def get_catalogo():
    return """🛍️ **¡Bienvenido a nuestro catálogo!**

📋 **Categorías disponibles:**

1️⃣ Ropa Deportiva
2️⃣ Accesorios
3️⃣ Calzado
4️⃣ Ofertas Especiales

💡 **Responde con el número** de la categoría que te interesa.
👤 Escribe **'agente'** para hablar con un asesor."""


def get_ayuda():
    return """🤖 **Qué puedo hacer por ti:**

📦 **Catálogo** - Ver productos y categorías
💰 **Precios** - Consultar precios y cotizaciones
🕐 **Horario** - Conocer nuestra atención
📍 **Contacto** - Teléfono, email y dirección
👤 **Agente** - Hablar con un asesor humano

💡 **Cómo usar el asistente:**

1️⃣ Escribe **'catalogo'** para ver categorías
2️⃣ Responde con el **número** de la categoría
3️⃣ Sigue las opciones del menú

👋 Escribe **'adios'** para salir."""


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
        "sessions_activas": len(contexto_usuarios)
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

        # Clasificar con contexto
        response_text = clasificar_mensaje(body, from_number)

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