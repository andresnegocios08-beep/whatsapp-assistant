"""
Normalizador de texto para mensajes de WhatsApp
Limpia y prepara el texto para el procesamiento NLP
"""

import re
import unicodedata
from typing import List, Dict

class TextNormalizer:
    """Clase para normalizar texto de mensajes de WhatsApp"""
    
    def __init__(self):
        # Diccionario de contracciones y abreviaturas comunes
        self.contracciones = {
            'xq': 'porque', 'pq': 'porque', 'pk': 'porque',
            'k': 'que', 'q': 'que', 'x': 'por',
            'tmb': 'tambien', 'tb': 'tambien',
            'mñn': 'manana', 'mñna': 'manana',
            'dp': 'despues', 'dsps': 'despues',
            'ps': 'pues', 'pa': 'para'
        }
        
        # Palabras vacías (stop words)
        self.stop_words = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'en', 'y', 'a', 'que', 'se', 'del', 'las', 'por',
            'con', 'para', 'como', 'esta', 'estoy', 'estas',
            'me', 'te', 'le', 'lo', 'la', 'mi', 'tu', 'su',
            'este', 'ese', 'aquel', 'esta', 'esa', 'aquella',
            'yo', 'tu', 'el', 'ella', 'nosotros', 'ustedes',
            'ellos', 'ellas', 'muy', 'mas', 'menos', 'tan'
        }
    
    def normalize(self, text: str) -> str:
        """Normaliza el texto de entrada"""
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar emojis
        text = self._remove_emojis(text)
        
        # Eliminar caracteres especiales
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Eliminar acentos
        text = self._remove_accents(text)
        
        # Expandir contracciones
        text = self._expand_contractions(text)
        
        # Eliminar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _remove_emojis(self, text: str) -> str:
        """Elimina emojis del texto"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)
    
    def _remove_accents(self, text: str) -> str:
        """Elimina acentos"""
        text = unicodedata.normalize('NFD', text)
        return ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    def _expand_contractions(self, text: str) -> str:
        """Expande contracciones"""
        words = text.split()
        expanded = []
        for word in words:
            expanded.append(self.contracciones.get(word, word))
        return ' '.join(expanded)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave del texto"""
        words = text.split()
        keywords = []
        for word in words:
            if len(word) > 2 and word not in self.stop_words:
                keywords.append(word)
        return keywords
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extrae entidades básicas (números, emails, fechas)"""
        entities = {}
        
        # Números de orden
        order_match = re.search(r'#?(\d{5,})', text)
        if order_match:
            entities['numero_orden'] = order_match.group(1)
        
        # Emails
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            entities['email'] = email_match.group()
        
        # Fechas (dd/mm/yyyy)
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if date_match:
            entities['fecha'] = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        
        return entities