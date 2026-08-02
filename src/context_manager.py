"""
Gestor de contexto para conversaciones
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class ContextManager:
    """Maneja el contexto de las conversaciones por usuario"""
    
    def __init__(self, session_file="data/sessions.json"):
        self.session_file = session_file
        self.sessions = {}
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        self._load_sessions()
    
    def _load_sessions(self):
        """Carga las sesiones desde archivo"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando sesiones: {e}")
            self.sessions = {}
    
    def _save_sessions(self):
        """Guarda las sesiones en archivo"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error guardando sesiones: {e}")
    
    def get(self, user_id: str) -> Dict[str, Any]:
        """Obtiene la sesión de un usuario"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "last_intent": None,
                "context": {},
                "history": [],
                "last_activity": datetime.now().isoformat()
            }
            self._save_sessions()
        return self.sessions[user_id]
    
    def set(self, user_id: str, key: str, value: Any):
        """Establece un valor en la sesión"""
        session = self.get(user_id)
        if key == "last_intent":
            session["last_intent"] = value
        elif key == "context":
            session["context"].update(value)
        else:
            session["context"][key] = value
        session["last_activity"] = datetime.now().isoformat()
        self._save_sessions()
    
    def add_history(self, user_id: str, message: str, intent: str, response: str):
        """Agrega un mensaje al historial"""
        session = self.get(user_id)
        session["history"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "intent": intent,
            "response": response
        })
        if len(session["history"]) > 50:
            session["history"] = session["history"][-50:]
        self._save_sessions()
    
    def clear(self, user_id: str):
        """Limpia la sesión de un usuario"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            self._save_sessions()