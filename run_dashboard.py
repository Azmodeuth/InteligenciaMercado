#!/usr/bin/env python3
"""
================================================================================
REVOLICO PRICE INTELLIGENCE - DASHBOARD LAUNCHER
================================================================================
Inicia el dashboard de Streamlit.

Uso:
    python run_dashboard.py
    O directamente: streamlit run dashboard.py
"""

import subprocess
import sys
import os

def main():
    """Ejecuta el dashboard de Streamlit."""
    
    # Cambiar al directorio del proyecto
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("\n" + "="*60)
    print("🚀 INICIANDO DASHBOARD DE INTELIGENCIA DE MERCADO")
    print("="*60)
    print("\n📡 Fuentes disponibles:")
    print("   🔵 Revolico.com (API GraphQL)")
    print("   🟢 Voypati.com (E-commerce)")
    print("   🟠 ElYerroMenu.com (Catálogos)")
    print("   🟡 Fadiar.com (Inventario)")
    print("   🟣 Porlalivre.com (Clasificados)")
    print("\n💡 Cada producto mostrará su fuente de origen")
    print("="*60 + "\n")
    
    # Ejecutar Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard.py",
            "--server.port=8501",
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard cerrado por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nEjecuta manualmente: streamlit run dashboard.py") 

if __name__ == "__main__":
    main()