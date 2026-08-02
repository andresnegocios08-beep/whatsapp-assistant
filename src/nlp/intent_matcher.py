"""
Clasificador de intenciones para mensajes de WhatsApp
Detecta qué quiere el usuario basado en el texto
"""

import re
from typing import Dict, Tuple, Optional
from .normalizer import TextNormalizer

class IntentMatcher:
    """Clasifica la intención de los mensajes de usuario"""
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        
        # Definición de intenciones con palabras clave
        self.intents = {
            'saludo': {
                'keywords': ['hola', 'buenos', 'dias', 'tardes', 'noches', 'hey', 'que tal', 'buenas', 'saludos', 'holi'],
                'response': '¡Hola! Bienvenido al asistente. ¿En qué puedo ayudarte?'
            },
            'despedida': {
                'keywords': ['adios', 'hasta luego', 'chao', 'nos vemos', 'bye', 'chau'],
                'response': '¡Hasta luego! Que tengas un excelente día.'
            },
            'consulta_estado': {
                'keywords': ['estado', 'pedido', 'orden', 'seguimiento', 'numero de orden', 'tracking'],
                'response': 'Claro, te ayudo con el estado de tu pedido. Por favor, escríbeme tu número de orden.'
            },
            'horario': {
                'keywords': ['horario', 'abren', 'cierran', 'atencion', 'hora', 'cuando abren', 'disponibilidad'],
                'response': 'Nuestro horario de atención es de Lunes a Viernes de 8:00 AM a 6:00 PM.'
            },
            'ventas': {
                'keywords': ['precio', 'costo', 'comprar', 'producto', 'catalogo', 'catálogo', 'menu', 'cotizar', 'valor', 'cuanto cuesta', 'quiero comprar', 'enseñar', 'muestrame', 'productos', 'servicios', 'lista', 'carta', 'ofertas', 'promociones', 'venta', 'vender', 'precios'],
                'response': '¡Genial! Te ayudo con nuestra selección de productos. Tenemos:\n\n1️⃣ Ropa Deportiva\n2️⃣ Accesorios\n3️⃣ Calzado\n4️⃣ Ofertas Especiales\n\nResponde con el número de la categoría que te interesa.'
            },
            'queja': {
                'keywords': ['problema', 'reclamo', 'queja', 'error', 'falla', 'no funciona', 'insatisfecho', 'devolucion', 'dañado', 'malo'],
                'response': 'Lamento escuchar que tienes un problema. Voy a escalar tu caso a un agente especializado.'
            },
            'hablar_agente': {
                'keywords': ['agente', 'humano', 'persona', 'asesor', 'hablar con alguien', 'ejecutivo', 'representante'],
                'response': 'Entiendo, te voy a conectar con un agente humano. Por favor, espera un momento.'
            },
            'contacto': {
                'keywords': ['telefono', 'correo', 'email', 'direccion', 'ubicacion', 'contacto', 'whatsapp', 'llamar'],
                'response': 'Puedes contactarnos a través de:\n\n📞 Teléfono: +57 301 234 5678\n📧 Email: info@tienda.com\n📍 Dirección: Calle 123 #45-67, Bogotá'
            },
            'agradecimiento': {
                'keywords': ['gracias', 'muchas gracias', 'te agradezco', 'excelente servicio', 'agradecido', 'mil gracias'],
                'response': '¡De nada! Es un placer ayudarte. Si necesitas algo más, aquí estoy.'
            }
        }
    
    def classify(self, message: str) -> Dict[str, any]:
    """
    Clasifica la intención del mensaje
    """
    # Normalizar mensaje
    normalized = self.normalizer.normalize(message)
    keywords = self.normalizer.extract_keywords(normalized)
    
    # Debug
    print(f"🔍 Mensaje normalizado: '{normalized}'")
    print(f"🔍 Palabras clave extraídas: {keywords}")
    
    # Buscar coincidencias DIRECTAS
    for intent_name, intent_data in self.intents.items():
        for keyword in intent_data['keywords']:
            if keyword in normalized:
                print(f"✅ Coincidencia encontrada: '{keyword}' -> {intent_name}")
                return {
                    'intent': intent_name,
                    'confidence': 1.0,
                    'entities': {},
                    'normalized': normalized
                }
    
    # Si no hay coincidencia directa, buscar coincidencia parcial
    best_intent = 'fallback'
    max_score = 0
    
    for intent_name, intent_data in self.intents.items():
        score = 0
        for keyword in intent_data['keywords']:
            # Buscar coincidencia parcial
            for word in keywords:
                if keyword in word or word in keyword:
                    score += 1
                    print(f"🔍 Coincidencia parcial: '{keyword}' en '{word}' -> {intent_name}")
        
        if score > max_score:
            max_score = score
            best_intent = intent_name
    
    # Si score es muy bajo, usar fallback
    if max_score < 0.1:
        best_intent = 'fallback'
    
    print(f"📊 Intención final: {best_intent} (score: {max_score})")
    
    return {
        'intent': best_intent,
        'confidence': max_score / 10 if max_score > 0 else 0.1,
        'entities': {},
        'normalized': normalized
    }
        
        best_intent = 'fallback'
        max_score = 0
        
        for intent_name, intent_data in self.intents.items():
            score = 0
            for keyword in intent_data['keywords']:
                if keyword in normalized:
                    score += 2
                for word in keywords:
                    if keyword in word or word in keyword:
                        score += 1
            
            max_possible = len(intent_data['keywords']) * 2 + len(keywords)
            if max_possible > 0:
                confidence = min(score / max_possible, 1.0)
            else:
                confidence = 0
            
            if confidence > max_score:
                max_score = confidence
                best_intent = intent_name
        
        if max_score < 0.15:
            best_intent = 'fallback'
            max_score = 0.15
        
        return {
            'intent': best_intent,
            'confidence': max_score,
            'entities': entities,
            'normalized': normalized
        }
    
    def get_response(self, message: str) -> Tuple[str, str]:
        """Obtiene la respuesta para un mensaje"""
        # CASOS ESPECIALES
        special_cases = {
            'catalogo': 'ventas',
            'catálogo': 'ventas',
            'precio': 'ventas',
            'precios': 'ventas',
            'productos': 'ventas'
        }
        
        normalized = self.normalizer.normalize(message)
        for key, intent in special_cases.items():
            if key in normalized or key in message.lower():
                return intent, self.intents[intent]['response']
        
        result = self.classify(message)
        intent = result['intent']
        
        if intent == 'fallback':
            response = "No entendí tu mensaje. ¿Podrías reformularlo? O escribe 'agente' para hablar con un humano."
        else:
            response = self.intents.get(intent, {}).get(
                'response',
                "No tengo una respuesta para eso. ¿Puedes intentar de nuevo?"
            )
        
        return intent, response
