
"""
Conexión a base de datos PostgreSQL (Supabase)
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con la base de datos"""
        try:
            database_url = os.getenv('DATABASE_URL', '')
            if not database_url:
                print("⚠️ DATABASE_URL no configurado")
                return
            
            self.connection = psycopg2.connect(database_url)
            print("✅ Conexión a base de datos establecida")
        except Exception as e:
            print(f"❌ Error conectando a base de datos: {e}")
    
    def save_conversation(self, user_id: str, message: str, intent: str, response: str):
        """Guarda una conversación en la base de datos"""
        try:
            if not self.connection:
                self._connect()
            
            cursor = self.connection.cursor()
            
            # Insertar conversación
            cursor.execute("""
                INSERT INTO conversaciones (user_id, message, intent, response, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, message, intent, response))
            
            # Actualizar usuario
            cursor.execute("""
                INSERT INTO usuarios (user_id, phone_number, first_interaction, last_interaction, total_messages)
                VALUES (%s, %s, NOW(), NOW(), 1)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    last_interaction = NOW(),
                    total_messages = usuarios.total_messages + 1
            """, (user_id, user_id))
            
            self.connection.commit()
            cursor.close()
            print(f"📝 Conversación guardada para {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error guardando conversación: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_stats(self):
        """Obtiene estadísticas de la base de datos"""
        try:
            if not self.connection:
                self._connect()
            
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Total conversaciones
            cursor.execute("SELECT COUNT(*) as total FROM conversaciones")
            total = cursor.fetchone()['total']
            
            # Usuarios únicos
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            users = cursor.fetchone()['total']
            
            # Intenciones
            cursor.execute("""
                SELECT intent, COUNT(*) as count 
                FROM conversaciones 
                WHERE intent IS NOT NULL 
                GROUP BY intent 
                ORDER BY count DESC
            """)
            intents = {row['intent']: row['count'] for row in cursor.fetchall()}
            
            cursor.close()
            
            return {
                "total_conversaciones": total,
                "usuarios_unicos": users,
                "intenciones": intents,
                "tickets_pendientes": 0
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}

# Singleton
db = DatabaseManager()
