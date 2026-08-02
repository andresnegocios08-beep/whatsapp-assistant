"""
Pruebas de respuestas del asistente
Verifica que las respuestas sean apropiadas
"""

import sys
import os

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp.intent_matcher import IntentMatcher

def test_responses():
    """Prueba que las respuestas sean coherentes"""
    
    matcher = IntentMatcher()
    
    # Casos de prueba con respuestas esperadas
    test_cases = [
        ("hola", "Hola"),
        ("gracias", "nada"),
        ("adios", "Hasta luego"),
        ("horario", "horario"),
        ("problema", "Lamento"),
        ("agente", "conectar"),
        ("telefono", "telefono"),
        ("catalogo", "selección"),
    ]
    
    print("=" * 50)
    print("PRUEBAS DE RESPUESTAS")
    print("=" * 50)
    
    all_passed = True
    
    for message, expected_phrase in test_cases:
        intent, response = matcher.get_response(message)
        
        if expected_phrase.lower() in response.lower():
            print(f"[OK] '{message}' -> '{response[:40]}...'")
        else:
            print(f"[FAIL] '{message}' -> '{response[:40]}...' (no contiene '{expected_phrase}')")
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("TODAS LAS RESPUESTAS SON APROPIADAS!")
    else:
        print("Algunas respuestas no contienen el texto esperado.")

if __name__ == "__main__":
    test_responses()