"""
Pruebas unitarias para el clasificador de intenciones
"""

import sys
import os

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp.intent_matcher import IntentMatcher

def test_intent_matcher():
    """Prueba todas las intenciones del clasificador"""
    
    matcher = IntentMatcher()
    
    # Casos de prueba: (mensaje, intención esperada)
    test_cases = [
        # Saludos
        ("hola", "saludo"),
        ("buenos dias", "saludo"),
        ("hey", "saludo"),
        ("holi", "saludo"),
        
        # Despedidas
        ("adios", "despedida"),
        ("hasta luego", "despedida"),
        ("chao", "despedida"),
        ("bye", "despedida"),
        
        # Estado de pedido
        ("estado de mi pedido", "consulta_estado"),
        ("numero de orden", "consulta_estado"),
        ("seguimiento", "consulta_estado"),
        
        # Horarios
        ("horario de atencion", "horario"),
        ("a que hora abren", "horario"),
        ("cuando cierran", "horario"),
        
        # Ventas/Catálogo
        ("catalogo", "ventas"),
        ("quiero comprar", "ventas"),
        ("precio", "ventas"),
        ("muestrame los productos", "ventas"),
        
        # Quejas
        ("tengo un problema", "queja"),
        ("reclamo", "queja"),
        ("no funciona", "queja"),
        ("devolucion", "queja"),
        
        # Agente
        ("quiero hablar con un agente", "hablar_agente"),
        ("persona", "hablar_agente"),
        ("asesor", "hablar_agente"),
        
        # Contacto
        ("telefono", "contacto"),
        ("direccion", "contacto"),
        ("email", "contacto"),
        
        # Agradecimiento
        ("gracias", "agradecimiento"),
        ("muchas gracias", "agradecimiento"),
        
        # Fallback (mensajes no reconocidos)
        ("xyz123", "fallback"),
        ("asdfghjkl", "fallback"),
    ]
    
    print("=" * 50)
    print("PRUEBAS DEL CLASIFICADOR DE INTENCIONES")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for message, expected_intent in test_cases:
        intent, response = matcher.get_response(message)
        
        if intent == expected_intent:
            print(f"[OK] '{message}' -> {intent}")
            passed += 1
        else:
            print(f"[FAIL] '{message}' -> {intent} (esperado: {expected_intent})")
            failed += 1
    
    print("=" * 50)
    print(f"RESULTADOS: {passed} pasaron, {failed} fallaron")
    print("=" * 50)
    
    if failed == 0:
        print("TODAS LAS PRUEBAS PASARON!")
    else:
        print("Algunas pruebas fallaron. Revisa el clasificador.")

if __name__ == "__main__":
    test_intent_matcher()