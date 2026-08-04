
from flask import Flask, jsonify, request, render_template_string
from twilio.twiml.messaging_response import MessagingResponse
import re
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mi-clave-secreta')

# ============================================
# BASE DE DATOS SQLITE
# ============================================

def init_db():
    conn = sqlite3.connect('conversaciones.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            intent TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id TEXT PRIMARY KEY,
            phone_number TEXT,
            first_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_messages INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite inicializada")

def save_conversation(user_id, message, intent, response):
    try:
        conn = sqlite3.connect('conversaciones.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversaciones (user_id, message, intent, response, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, message, intent, response))
        cursor.execute('''
            INSERT OR REPLACE INTO usuarios (user_id, phone_number, last_interaction, total_messages)
            VALUES (?, ?, CURRENT_TIMESTAMP, COALESCE((SELECT total_messages + 1 FROM usuarios WHERE user_id = ?), 1))
        ''', (user_id, user_id, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error guardando conversación: {e}")
        return False

def get_stats():
    try:
        conn = sqlite3.connect('conversaciones.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversaciones")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        users = cursor.fetchone()[0]
        cursor.execute("""
            SELECT intent, COUNT(*) as count 
            FROM conversaciones 
            WHERE intent IS NOT NULL 
            GROUP BY intent 
            ORDER BY count DESC
        """)
        intents = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {
            "total_conversaciones": total,
            "usuarios_unicos": users,
            "intenciones": intents,
            "tickets_pendientes": 0
        }
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {}

init_db()

# ============================================
# CONTEXTO EN MEMORIA
# ============================================

contexto_usuarios = {}

def clasificar_mensaje(mensaje, user_id):
    mensaje = mensaje.lower().strip()
    if user_id not in contexto_usuarios:
        contexto_usuarios[user_id] = {"ultima_intencion": None, "categoria": None}
    ctx = contexto_usuarios[user_id]
    ultima_intencion = ctx.get("ultima_intencion")
    
    if ultima_intencion == "ventas" and mensaje in ["1", "2", "3", "4"]:
        categorias = {"1": "Ropa Deportiva", "2": "Accesorios", "3": "Calzado", "4": "Ofertas Especiales"}
        categoria = categorias[mensaje]
        ctx["ultima_intencion"] = "categoria_seleccionada"
        ctx["categoria"] = categoria
        return f"✅ Has seleccionado: **{categoria}**\n\n📋 ¿Qué te gustaría hacer?\n\n1️⃣ Ver productos disponibles\n2️⃣ Pedir información sobre precios\n3️⃣ Volver al catálogo principal"
    
    if ultima_intencion == "categoria_seleccionada":
        if mensaje == "1":
            ctx["ultima_intencion"] = None
            return "📦 **Productos:**\n\nPara ver el catálogo completo, visita nuestro sitio web."
        elif mensaje == "2":
            ctx["ultima_intencion"] = None
            return "💰 **Información de precios:**\n\nPara cotizaciones, escríbenos el nombre del producto."
        elif mensaje == "3" or "volver" in mensaje:
            ctx["ultima_intencion"] = "ventas"
            return "🔄 Volviendo al catálogo...\n\n" + get_catalogo()
    
    if re.search(r'\b(catalogo|catálogo|producto|menu|muestrame|enseñar|ver productos|quiero comprar|lista|que venden|tienen|catagalo|catgalo)\b', mensaje):
        ctx["ultima_intencion"] = "ventas"
        return get_catalogo()
    
    if re.search(r'\b(precio|costo|valor|cuanto cuesta|precios|cotizar|cotizacion|presio)\b', mensaje):
        ctx["ultima_intencion"] = "precio"
        return "💰 Te ayudo con los precios.\n\n📋 Escribe el **nombre del producto** que te interesa."
    
    if re.search(r'\b(horario|abren|cierran|atencion|hora|cuando abren|disponibilidad|horas|horairo|horaro)\b', mensaje):
        return "🕐 **Horario de atención:**\n\n📅 Lunes a Viernes: 8:00 AM - 6:00 PM\n📅 Sábados: 9:00 AM - 2:00 PM\n📅 Domingos: Cerrado"
    
    if re.search(r'\b(telefono|correo|email|direccion|ubicacion|contacto|whatsapp|llamar|donde estan|contato)\b', mensaje):
        return "📞 **Información de contacto:**\n\n📱 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá"
    
    if re.search(r'\b(problema|reclamo|queja|error|falla|no funciona|devolucion|dañado|insatisfecho|malo)\b', mensaje):
        return "📞 Lamento escuchar eso. Voy a escalar tu caso a un agente especializado."
    
    if re.search(r'\b(agente|asesor|persona|humano|hablar con alguien|representante|agte)\b', mensaje):
        return "👤 Te voy a conectar con un agente humano. Por favor, espera un momento."
    
    if re.search(r'\b(hola|buenos|hey|saludos|holi|que tal|buenas|hola que tal)\b', mensaje):
        return "¡Hola! 👋 Bienvenido al asistente.\n\n📋 Escribe **'catalogo'** para ver nuestros productos.\n👤 Escribe **'agente'** para hablar con un asesor."
    
    if re.search(r'\b(gracias|muchas gracias|te agradezco|mil gracias|agradecido|grasias|graxias)\b', mensaje):
        return "¡De nada! 😊 Es un placer ayudarte."
    
    if re.search(r'\b(ayuda|que puedes hacer|comandos|opciones|menu|aydua)\b', mensaje):
        return get_ayuda()
    
    if re.search(r'\b(adios|chao|bye|hasta luego|nos vemos|chau|me voy|adio)\b', mensaje):
        if user_id in contexto_usuarios:
            del contexto_usuarios[user_id]
        return "¡Hasta luego! 👋 Que tengas un excelente día."
    
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
# DASHBOARD HTML (NUEVO)
# ============================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Asistente WhatsApp - Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; }
        .header { background: #25D366; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .header small { font-size: 14px; opacity: 0.9; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 32px; font-weight: bold; color: #25D366; }
        .stat-label { color: #666; font-size: 14px; margin-top: 5px; }
        .intents { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .intent-bar { display: flex; align-items: center; margin: 8px 0; }
        .intent-name { width: 150px; font-weight: 500; }
        .intent-bar-fill { height: 24px; background: #25D366; border-radius: 5px; transition: width 0.5s; }
        .intent-count { margin-left: 10px; font-weight: 500; color: #555; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 20px; }
        .refresh-btn { background: #25D366; color: white; border: none; padding: 10px 25px; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .refresh-btn:hover { background: #1da851; }
        .last-update { color: #999; font-size: 13px; }
    </style>
</head>
<body>

<div class="header">
    <div>
        <h1>🤖 Asistente WhatsApp</h1>
        <small>Dashboard de administración</small>
    </div>
    <div>
        <span class="last-update" id="last-update">Cargando...</span>
    </div>
</div>

<div class="stats" id="stats">
    <div class="stat-card">
        <div class="stat-number" id="total-conversations">0</div>
        <div class="stat-label">Total Conversaciones</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="unique-users">0</div>
        <div class="stat-label">Usuarios Únicos</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="pending-tickets">0</div>
        <div class="stat-label">Tickets Pendientes</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" id="sessions-active">0</div>
        <div class="stat-label">Sesiones Activas</div>
    </div>
</div>

<div class="intents">
    <h3>📊 Intenciones Detectadas</h3>
    <div id="intents-list"></div>
</div>

<div style="text-align: center; margin-top: 20px;">
    <button class="refresh-btn" onclick="loadData()">🔄 Actualizar</button>
</div>

<div class="footer">
    <p>Actualizado automáticamente cada 30 segundos</p>
</div>

<script>
    async function loadData() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            
            document.getElementById('total-conversations').textContent = data.total_conversaciones || 0;
            document.getElementById('unique-users').textContent = data.usuarios_unicos || 0;
            document.getElementById('pending-tickets').textContent = data.tickets_pendientes || 0;
            
            // Sesiones activas (contexto en memoria)
            const sessions = await fetch('/sessions');
            const sessionData = await sessions.json();
            document.getElementById('sessions-active').textContent = sessionData.sessions || 0;
            
            const intentsList = document.getElementById('intents-list');
            intentsList.innerHTML = '';
            const intents = data.intenciones || {};
            const maxCount = Math.max(...Object.values(intents), 1);
            
            if (Object.keys(intents).length === 0) {
                intentsList.innerHTML = '<p style="color: #999; text-align: center;">No hay datos aún. Envía un mensaje por WhatsApp.</p>';
            } else {
                for (const [intent, count] of Object.entries(intents)) {
                    const percentage = maxCount > 0 ? (count / maxCount * 100) : 0;
                    intentsList.innerHTML += `
                        <div class="intent-bar">
                            <span class="intent-name">${intent}</span>
                            <div class="intent-bar-fill" style="width: ${percentage}%"></div>
                            <span class="intent-count">${count}</span>
                        </div>
                    `;
                }
            }
            
            document.getElementById('last-update').textContent = 'Última actualización: ' + new Date().toLocaleString();
        } catch (error) {
            console.error('Error cargando datos:', error);
        }
    }
    
    loadData();
    setInterval(loadData, 30000);
</script>
</body>
</html>
"""


# ============================================
# ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "whatsapp-assistant",
        "version": "1.0.0",
        "message": "Servidor funcionando correctamente",
        "database": "sqlite"
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
        <li><a href="/dashboard/">/dashboard/</a> - Panel de administración</li>
        <li>/webhook/twilio - Endpoint para WhatsApp (POST)</li>
    </ul>
    """

@app.route('/webhook/twilio', methods=['POST'])
def webhook_twilio():
    try:
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '').strip()

        print(f"\n📩 Mensaje de {from_number}: '{body}'")

        response_text = clasificar_mensaje(body, from_number)
        intent = contexto_usuarios.get(from_number, {}).get("ultima_intencion", "unknown")
        save_conversation(from_number, body, intent, response_text)

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
def get_stats_endpoint():
    stats = get_stats()
    return jsonify(stats)


@app.route('/sessions', methods=['GET'])
def get_sessions():
    return jsonify({"sessions": len(contexto_usuarios)})


@app.route('/dashboard/', methods=['GET'])
def dashboard():
    """Dashboard de administración - HTML"""
    return render_template_string(DASHBOARD_HTML)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
