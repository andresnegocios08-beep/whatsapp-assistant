const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTjj0x42MkOsXT4a3xsE9oEYLTM-Zynv9pW_GmRVq_vwWKtEwiByHn00S6GzoS95SUwkeVPYT7MBK5Y/pub?gid=0&single=true&output=csv';

const WHATSAPP_TOKEN = process.env.WHATSAPP_TOKEN;
const PHONE_NUMBER_ID = process.env.PHONE_NUMBER_ID;
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || 'content_factory_2026';
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const MENSAJE_DEFECTO = 'Lo siento, no entendí tu mensaje. ¿Puedes reformularlo?';

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

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

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
        if (msg.type === 'text') {
          const remitente = msg.from;
          const texto = msg.text.body;

          let respuesta = await buscarEnSheet(texto);

          if (!respuesta) {
            const conocimiento = await obtenerConocimiento();
            respuesta = await consultarGemini(texto, conocimiento);
          }

          await enviarWhatsApp(remitente, respuesta);
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
