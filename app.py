from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse
import re
<<<<<<< HEAD
=======
import os
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce

app = Flask(__name__)

# ============================================
<<<<<<< HEAD
# GESTOR DE CONVERSACIONES (MÁS ROBUSTO)
# ============================================

conversaciones = {}

def obtener_estado(user_id):
    """Obtiene el estado de la conversación de un usuario"""
    if user_id not in conversaciones:
        conversaciones[user_id] = {
            "ultimo_mensaje": None,
            "intencion_actual": None,
            "categoria": None,
            "esperando": None
        }
    return conversaciones[user_id]

def guardar_estado(user_id, clave, valor):
    estado = obtener_estado(user_id)
    estado[clave] = valor
    print(f"💾 {user_id}: {clave} = {valor}")

def limpiar_estado(user_id):
    conversaciones[user_id] = {
        "ultimo_mensaje": None,
        "intencion_actual": None,
        "categoria": None,
        "esperando": None
    }
    print(f"🧹 Estado limpiado para {user_id}")

# ============================================
# PROCESADOR DE MENSAJES
# ============================================

def procesar_mensaje(mensaje, user_id):
    mensaje = mensaje.strip()
    mensaje_lower = mensaje.lower()
    
    # Obtener estado actual
    estado = obtener_estado(user_id)
    esperando = estado.get("esperando")
    intencion_actual = estado.get("intencion_actual")
    
    print(f"\n📩 '{mensaje}' | Esperando: {esperando} | Intención: {intencion_actual}")
    
    # ============================================
    # CASO 1: ESPERANDO RESPUESTA DE CATEGORÍA
    # ============================================
    if esperando == "categoria":
        if mensaje in ["1", "2", "3", "4"]:
            categorias = {
                "1": "Ropa Deportiva",
                "2": "Accesorios",
                "3": "Calzado",
                "4": "Ofertas Especiales"
            }
            categoria = categorias[mensaje]
            guardar_estado(user_id, "categoria", categoria)
            guardar_estado(user_id, "esperando", "menu_categoria")
            guardar_estado(user_id, "intencion_actual", "categoria_seleccionada")
            
            return f"✅ Has seleccionado: **{categoria}**\n\n📋 ¿Qué te gustaría hacer?\n\n1️⃣ Ver productos disponibles\n2️⃣ Pedir información sobre precios\n3️⃣ Volver al catálogo principal\n\n💡 Responde con el número de tu opción."
        else:
            return "⚠️ Por favor, responde con un **número del 1 al 4** para seleccionar la categoría."
    
    # ============================================
    # CASO 2: ESPERANDO OPCIÓN DEL MENÚ DE CATEGORÍA
    # ============================================
    if esperando == "menu_categoria":
        if mensaje == "1":
            categoria = estado.get("categoria", "esta categoría")
            guardar_estado(user_id, "esperando", None)
            return f"📦 **Productos en {categoria}:**\n\nActualmente no tenemos el listado completo disponible por WhatsApp.\n\n🔍 ¿Buscas algo en particular? Escríbelo y te ayudo.\n\n💡 Escribe **'volver'** para regresar al catálogo."
        
        elif mensaje == "2":
            guardar_estado(user_id, "esperando", None)
            return "💰 **Información de precios:**\n\nPara obtener una cotización exacta, escríbenos el **nombre del producto** que te interesa.\n\n📋 Ejemplo: 'precio de la camisa deportiva'"
        
        elif mensaje == "3":
            guardar_estado(user_id, "esperando", "categoria")
            guardar_estado(user_id, "intencion_actual", "ventas")
            return "🔄 Volviendo al catálogo...\n\n" + get_catalogo()
        
        elif "volver" in mensaje_lower or "atras" in mensaje_lower:
            guardar_estado(user_id, "esperando", "categoria")
            guardar_estado(user_id, "intencion_actual", "ventas")
            return "🔄 Volviendo al catálogo...\n\n" + get_catalogo()
        
        else:
            return "⚠️ Opción no válida.\n\n📋 Escribe:\n1️⃣ Para ver productos\n2️⃣ Para información de precios\n3️⃣ Para volver al catálogo"
    
    # ============================================
    # CASO 3: ESPERANDO PRODUCTO PARA PRECIO
    # ============================================
    if esperando == "precio":
        guardar_estado(user_id, "esperando", None)
        return f"💰 **Cotización para '{mensaje}':**\n\nPara obtener el precio exacto, por favor contáctanos directamente:\n📱 WhatsApp: +57 301 234 5678\n📧 Email: info@tienda.com\n\n💡 ¿Necesitas algo más?"
    
    # ============================================
    # INTENCIÓN: CATÁLOGO
    # ============================================
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|lista|que venden|tienen)\b', mensaje_lower):
        guardar_estado(user_id, "intencion_actual", "ventas")
        guardar_estado(user_id, "esperando", "categoria")
        guardar_estado(user_id, "categoria", None)
        return get_catalogo()
    
    # ============================================
    # INTENCIÓN: PRECIO
    # ============================================
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion)\b', mensaje_lower):
        guardar_estado(user_id, "esperando", "precio")
        return "💰 **Cotizaciones:**\n\n📋 Escríbenos el **nombre del producto** que deseas cotizar.\n\nEjemplo: 'camisa deportiva'"
    
    # ============================================
    # INTENCIÓN: HORARIO
    # ============================================
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas)\b', mensaje_lower):
        return "🕐 **Horario de atención:**\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado"
    
    # ============================================
    # INTENCIÓN: CONTACTO
    # ============================================
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan)\b', mensaje_lower):
        return "📞 **Información de contacto:**\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá"
    
    # ============================================
    # INTENCIÓN: QUEJA
    # ============================================
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje_lower):
        return "📞 Lamento escuchar eso. Voy a escalar tu caso a un agente especializado.\n\n⏳ Por favor, espera un momento."
    
    # ============================================
    # INTENCIÓN: AGENTE
    # ============================================
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante)\b', mensaje_lower):
        return "👤 Te voy a conectar con un agente humano.\n\n⏳ Por favor, espera un momento."
    
    # ============================================
    # INTENCIÓN: SALUDO
    # ============================================
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas)\b', mensaje_lower):
        return "¡Hola! 👋 Bienvenido al asistente.\n\n📋 Escribe **'catalogo'** para ver nuestros productos.\n💰 Escribe **'precio'** para cotizaciones.\n👤 Escribe **'agente'** para hablar con un asesor."
    
    # ============================================
    # INTENCIÓN: AGRADECIMIENTO
    # ============================================
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido)\b', mensaje_lower):
        return "¡De nada! 😊 Es un placer ayudarte.\n\n💡 Si necesitas algo más, aquí estoy."
    
    # ============================================
    # INTENCIÓN: AYUDA
    # ============================================
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu)\b', mensaje_lower):
        return get_ayuda()
    
    # ============================================
    # INTENCIÓN: DESPEDIDA
    # ============================================
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau|me voy)\b', mensaje_lower):
        limpiar_estado(user_id)
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
3️⃣ Sigue las opciones del menú

👋 Escribe 'adios' para salir."""


# ============================================
# ENDPOINTS DE FLASK
=======
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
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
<<<<<<< HEAD
        "message": "Servidor funcionando correctamente",
        "conversaciones": len(conversaciones)
=======
        "message": "Servidor funcionando correctamente"
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce
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

<<<<<<< HEAD
        print(f"\n{'='*60}")
        print(f"📩 Mensaje de {from_number}: '{body}'")
        print(f"{'='*60}")

        response_text = procesar_mensaje(body, from_number)
=======
        print(f"📩 Mensaje de {from_number}: {body}")

        intent, response_text = clasificar_mensaje(body)
        print(f"🧠 Intención: {intent}")
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce

        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response_text)

<<<<<<< HEAD
        print(f"✅ Respondiendo a {from_number}")
=======
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce
        return str(resp)

    except Exception as e:
        print(f"❌ Error: {e}")
        resp = MessagingResponse()
        msg = resp.message()
<<<<<<< HEAD
        msg.body("⚠️ Ocurrió un error. Por favor, intenta de nuevo.")
        return str(resp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
=======
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
>>>>>>> 78e66f68f01fd62456385f727dca9e7918acc7ce
