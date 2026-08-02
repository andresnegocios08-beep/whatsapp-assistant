"""
Pruebas del sistema de escalamiento
"""

import sys
import os

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.flows.human_handoff import HumanHandoffManager
from src.nlp.intent_matcher import IntentMatcher

def test_handoff():
    """Prueba que el escalamiento funciona correctamente"""
    
    handoff = HumanHandoffManager()
    matcher = IntentMatcher()
    
    # Casos que deberian escalar
    escalate_cases = [
        ("hablar_agente", "quiero hablar con un agente"),
        ("queja", "tengo un problema grave"),
        ("queja", "esto no funciona bien"),
    ]
    
    # Casos que NO deberian escalar
    no_escalate_cases = [
        ("saludo", "hola"),
        ("horario", "horario"),
        ("ventas", "precio"),
    ]
    
    print("=" * 50)
    print("PRUEBAS DE ESCALAMIENTO")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    # Probar casos que deben escalar
    for expected_intent, message in escalate_cases:
        intent, _ = matcher.get_response(message)
        should_escalate, reason = handoff.should_escalate(intent, message)
        
        if should_escalate:
            print(f"[OK] '{message}' -> Escalado correctamente (razon: {reason})")
            passed += 1
        else:
            print(f"[FAIL] '{message}' -> Deberia escalar pero no lo hizo")
            failed += 1
    
    # Probar casos que NO deben escalar
    for expected_intent, message in no_escalate_cases:
        intent, _ = matcher.get_response(message)
        should_escalate, reason = handoff.should_escalate(intent, message)
        
        if not should_escalate:
            print(f"[OK] '{message}' -> No escalado (correcto)")
            passed += 1
        else:
            print(f"[FAIL] '{message}' -> No deberia escalar pero lo hizo")
            failed += 1
    
    print("=" * 50)
    print(f"RESULTADOS: {passed} pasaron, {failed} fallaron")

if __name__ == "__main__":
    test_handoff()