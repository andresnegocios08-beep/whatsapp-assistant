"""
Sistema para escalar conversaciones a agentes humanos
"""

import json
from datetime import datetime
import os

class HumanHandoffManager:
    def __init__(self, queue_file="data/escalation_queue.json"):
        self.queue_file = queue_file
        os.makedirs(os.path.dirname(queue_file), exist_ok=True)
        
    def should_escalate(self, intent, message, session_history=None):
        """
        Determina si se debe escalar a un humano
        """
        # Palabras clave para escalamiento inmediato
        keywords = ['problema', 'reclamo', 'queja', 'error', 'falla', 'no funciona', 
                   'insatisfecho', 'devolucion', 'dañado', 'malo', 'pésimo']
        
        # Si la intención es explícitamente "hablar_agente"
        if intent == 'hablar_agente':
            return True, "solicitud_usuario"
        
        # Si la intención es "queja"
        if intent == 'queja':
            return True, "alta_prioridad"
        
        # Si el mensaje contiene palabras clave de frustración
        if any(keyword in message.lower() for keyword in keywords):
            return True, "frustracion_detectada"
        
        return False, None
    
    def create_ticket(self, user_id, reason, message, session_history=None):
        """Crea un ticket para escalamiento"""
        ticket = {
            "ticket_id": f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "reason": reason,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "pendiente",
            "assigned_to": None,
            "session_history": session_history or []
        }
        
        # Guardar ticket
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    tickets = json.load(f)
            else:
                tickets = []
            
            tickets.append(ticket)
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(tickets, f, ensure_ascii=False, indent=2)
            
            print(f"Ticket creado: {ticket['ticket_id']} para {user_id}")
            return ticket
        except Exception as e:
            print(f"Error creando ticket: {e}")
            return None
    
    def get_response(self, ticket):
        """Obtiene el mensaje de respuesta para el usuario"""
        messages = {
            "solicitud_usuario": "Entiendo que quieres hablar con un agente. Te voy a conectar con uno de nuestros asesores. Por favor, espera un momento.",
            "alta_prioridad": "Lamento escuchar sobre tu problema. Este es un asunto prioritario. Un agente especializado te contactara en los proximos minutos.",
            "frustracion_detectada": "Veo que estas teniendo dificultades. Permiteme escalar tu caso a un agente humano que pueda ayudarte mejor."
        }
        return messages.get(ticket.get('reason'), "Te voy a conectar con un agente humano. Por favor, espera un momento.")