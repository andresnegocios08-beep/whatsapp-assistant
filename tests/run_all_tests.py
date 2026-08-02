"""
Ejecuta todas las pruebas del sistema
"""

import subprocess
import os

def run_all_tests():
    print("=" * 50)
    print("🚀 EJECUTANDO TODAS LAS PRUEBAS")
    print("=" * 50)
    
    test_files = [
        "test_intent_matcher.py",
        "test_responses.py",
        "test_handoff.py"
    ]
    
    for test_file in test_files:
        print(f"\n📝 Ejecutando: {test_file}")
        print("-" * 40)
        
        result = subprocess.run(
            ["python", test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errores:")
            print(result.stderr)
    
    print("\n" + "=" * 50)
    print("✅ PRUEBAS FINALIZADAS")

if __name__ == "__main__":
    run_all_tests()