// ============================================
// WEBHOOK WHATSAPP - CONTENT FACTORY
// Chat con base de conocimiento + Registro de recibos con IA
// ============================================

const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTjj0x42MkOsXT4a3xsE9oEYLTM-Zynv9pW_GmRVq_vwWKtEwiByHn00S6GzoS95SUwkeVPYT7MBK5Y/pub?gid=0&single=true&output=csv';

const WHATSAPP_TOKEN = process.env.WHATSAPP_TOKEN;
const PHONE_NUMBER_ID = process.env.PHONE_NUMBER_ID;
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || 'content_factory_2026';
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const SHEET_ID_GASTOS = process.env.SHEET_ID_GASTOS;
const NOMBRE_HOJA_GASTOS = process.env.NOMBRE_HOJA_GASTOS || 'GASTOS 2026';
const MENSAJE_DEFECTO = 'Lo siento, no entendí tu mensaje. ¿Puedes reformularlo?';

// ============================================
// UTILIDADES
// ============================================

function parseCSV(text) {
  const lines = text.split('\n').filter(l => l.trim());
  const result = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const matches = line.match(/(".*?"|[^,]+)(?=\s*,|\s*$)/g);
    if (matches && matches.length >= 2) {
      const pregunta = matches[0].replace(/^"|"$/g, '').trim();
      const respuesta = matches[1].replace(/^"|"$/g, '').trim();
      if (pregunta && respuesta) {
        result.push({ pregunta, respuesta });
      }
    }
  }
  return result;
}

function normalizar(texto) {
  return (texto || '').toString().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
}

// ============================================
// CHAT - BÚSQUEDA EN SHEET + GEMINI
// ============================================

async function buscarEnSheet(mensaje) {
  try {
    const response = await fetch(SHEET_CSV_URL);
    const csvText = await response.text();
    const datos = parseCSV(csvText);
    const msgNorm = normalizar(mensaje);

    for (const fila of datos) {
      const preguntaNorm = normalizar(fila.pregunta);
      if (msgNorm === preguntaNorm || msgNorm.includes(preguntaNorm) || preguntaNorm.includes(msgNorm)) {
        return fila.respuesta;
      }
    }
    return null;
  } catch (e) {
    console.error('Error buscando en Sheet:', e);
    return null;
  }
}

async function consultarGemini(mensaje, conocimientoBase) {
  if (!GEMINI_API_KEY) return MENSAJE_DEFECTO;

  const promptSistema = `Eres un asistente virtual de atención al cliente amable, conciso y profesional.
Responde en español basándote en esta base de conocimiento:

--- BASE DE CONOCIMIENTO ---
${conocimientoBase}
---------------------------

REGLAS:
1. Sé cordial, breve y directo (ideal para WhatsApp).
2. Si la consulta se puede responder con la info provista, hazlo naturalmente.
3. Si no hay info relevante, indica amablemente que no tienes esa información.
4. No inventes precios, horarios ni ubicaciones.`;

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: promptSistema }] },
        contents: [{ role: 'user', parts: [{ text: mensaje }] }],
        generationConfig: { temperature: 0.3, maxOutputTokens: 300 }
      })
    });
    const json = await response.json();
    if (json.candidates && json.candidates[0].content.parts[0].text) {
      return json.candidates[0].content.parts[0].text.trim();
    }
    return MENSAJE_DEFECTO;
  } catch (e) {
    console.error('Error Gemini:', e);
    return MENSAJE_DEFECTO;
  }
}

async function obtenerConocimiento() {
  try {
    const response = await fetch(SHEET_CSV_URL);
    const csvText = await response.text();
    const datos = parseCSV(csvText);
    return datos.map(d => `- ${d.pregunta}: ${d.respuesta}`).join('\n');
  } catch (e) {
    return 'Sin datos disponibles.';
  }
}

// ============================================
// WHATSAPP - ENVIAR MENSAJES
// ============================================

async function enviarWhatsApp(numero, mensaje) {
  const url = `https://graph.facebook.com/v18.0/${PHONE_NUMBER_ID}/messages`;
  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${WHATSAPP_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messaging_product: 'whatsapp',
        recipient_type: 'individual',
        to: numero,
        type: 'text',
        text: { preview_url: false, body: mensaje }
      })
    });
  } catch (e) {
    console.error('Error WhatsApp:', e);
  }
}

// ============================================
// RECIBOS - DESCARGA DE IMAGEN DESDE META
// ============================================

async function descargarImagenMeta(imageId) {
  try {
    // 1. Obtener URL temporal de la imagen
    const urlMeta = `https://graph.facebook.com/v18.0/${imageId}`;
    const resMeta = await fetch(urlMeta, {
      headers: { 'Authorization': `Bearer ${WHATSAPP_TOKEN}` }
    });
    const jsonMeta = await resMeta.json();

    if (!jsonMeta.url) {
      console.error('No se obtuvo URL de imagen:', jsonMeta);
      return null;
    }

    // 2. Descargar la imagen
    const resImg = await fetch(jsonMeta.url, {
      headers: { 'Authorization': `Bearer ${WHATSAPP_TOKEN}` }
    });
    const arrayBuffer = await resImg.arrayBuffer();
    const base64 = Buffer.from(arrayBuffer).toString('base64');

    return base64;
  } catch (e) {
    console.error('Error descargando imagen:', e);
    return null;
  }
}

// ============================================
// RECIBOS - ANÁLISIS CON GEMINI VISION
// ============================================

async function analizarReciboConGemini(imagenBase64) {
  try {
    const prompt = `Analiza esta imagen de un recibo o factura.
Extrae la información y responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown.
Formato exacto:
{
  "fecha": "YYYY-MM-DD",
  "monto": "numero sin simbolos ni comas",
  "categoria": "una de: Alimentacion, Transporte, Servicios, Entretenimiento, Salud, Compras, Otros",
  "comercio": "nombre del negocio"
}
Si algún dato no se puede leer, usa "No legible". Si no es un recibo, responde: {"error": "no es recibo"}`;

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{
          parts: [
            { text: prompt },
            { inline_data: { mime_type: 'image/jpeg', data: imagenBase64 } }
          ]
        }],
        generationConfig: { temperature: 0.1, maxOutputTokens: 200 }
      })
    });

    const json = await response.json();
    if (!json.candidates || !json.candidates[0]) {
      console.error('Gemini no respondió:', json);
      return null;
    }

    let texto = json.candidates[0].content.parts[0].text;
    texto = texto.replace(/```json/g, '').replace(/```/g, '').trim();

    const datos = JSON.parse(texto);
    if (datos.error) return null;

    return {
      fecha: datos.fecha || new Date().toISOString().split('T')[0],
      monto: datos.monto || '',
      categoria: datos.categoria || 'Otros',
      comercio: datos.comercio || 'No identificado'
    };
  } catch (e) {
    console.error('Error analizando recibo:', e);
    return null;
  }
}

// ============================================
// RECIBOS - ESCRIBIR EN GOOGLE SHEETS (vía Apps Script)
// ============================================

async function escribirGastoEnSheet(datos) {
  try {
    const APPS_SCRIPT_URL = process.env.APPS_SCRIPT_URL;
    if (!APPS_SCRIPT_URL) {
      console.error('Falta APPS_SCRIPT_URL');
      return false;
    }

    const res = await fetch(APPS_SCRIPT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'escribirGasto',
        sheetId: SHEET_ID_GASTOS,
        nombreHoja: NOMBRE_HOJA_GASTOS,
        datos: datos
      })
    });

    const json = await res.json();
    return json.exito === true;
  } catch (e) {
    console.error('Error escribiendo en Sheets:', e);
    return false;
  }
}

// ============================================
// RECIBOS - PROCESAR IMAGEN COMPLETA
// ============================================

async function procesarImagen(remitente, imageId) {
  try {
    await enviarWhatsApp(remitente, '📸 Recibí tu recibo. Analizando...');

    const imagenBase64 = await descargarImagenMeta(imageId);
    if (!imagenBase64) {
      await enviarWhatsApp(remitente, '❌ No pude descargar la imagen. Intenta de nuevo.');
      return;
    }

    const datos = await analizarReciboConGemini(imagenBase64);
    if (!datos) {
      await enviarWhatsApp(remitente, '❌ No pude leer el recibo. Asegúrate de que sea claro.');
      return;
    }

    const exito = await escribirGastoEnSheet(datos);

    if (exito) {
      const mensaje = `✅ Gasto registrado:\n\n📅 Fecha: ${datos.fecha}\n💰 Monto: ${datos.monto}\n🏷️ Categoría: ${datos.categoria}\n🏪 Comercio: ${datos.comercio}`;
      await enviarWhatsApp(remitente, mensaje);
    } else {
      await enviarWhatsApp(remitente, '❌ No pude guardar el gasto. Intenta de nuevo.');
    }
  } catch (e) {
    console.error('Error procesando imagen:', e);
    await enviarWhatsApp(remitente, '❌ Hubo un error procesando la imagen.');
  }
}

// ============================================
// HANDLER PRINCIPAL
// ============================================

export default async function handler(req, res) {
  if (req.method === 'GET') {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];

    if (mode === 'subscribe' && token === VERIFY_TOKEN) {
      return res.status(200).send(challenge);
    }
    return res.status(403).send('Forbidden');
  }

  if (req.method === 'POST') {
    try {
      const body = req.body;
      if (body.entry && body.entry[0].changes && body.entry[0].changes[0].value.messages) {
        const msg = body.entry[0].changes[0].value.messages[0];
        const remitente = msg.from;

        if (msg.type === 'text') {
          // CHAT: responder con base de conocimiento + Gemini
          const texto = msg.text.body;
          let respuesta = await buscarEnSheet(texto);

          if (!respuesta) {
            const conocimiento = await obtenerConocimiento();
            respuesta = await consultarGemini(texto, conocimiento);
          }

          await enviarWhatsApp(remitente, respuesta);

        } else if (msg.type === 'image') {
          // RECIBOS: procesar imagen con Gemini Vision
          await procesarImagen(remitente, msg.image.id);

        } else {
          await enviarWhatsApp(remitente, 'Por ahora solo entiendo texto y fotos de recibos.');
        }
      }
      return res.status(200).json({ status: 'success' });
    } catch (error) {
      console.error('Error:', error);
      return res.status(200).json({ status: 'error', message: error.message });
    }
  }

  return res.status(405).send('Method not allowed');
}