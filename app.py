"""
================================================================================
REVOLICO PRICE INTELLIGENCE - PUNTO DE ENTRADA PRINCIPAL V7.0
================================================================================
Este archivo importa y reexporta todo desde los módulos organizados.
Para uso directo como librería o entry point.
"""

# Configuración
from config.settings import (
    TASAS_DE_CAMBIO, TASA_CAMBIO_CUP, TASA_CAMBIO_MLC, TASA_CAMBIO_EUR,
    QUANTILE_INFERIOR, QUANTILE_SUPERIOR, PRECIO_MINIMO_VALIDO,
    DB_NAME, DB_TABLE, CATEGORIAS, actualizar_tasas_cambio, logger
)

# Utilidades
from core.utils import (
    obtener_timestamp, obtener_fecha, obtener_hora, obtener_id_busqueda,
    simplificar_busqueda, limpiar_descripcion
)

# Moneda
from core.currency import normalizar_moneda, convertir_a_usd

# Análisis
from core.analysis import analizar_precios, analizar_mercado

# Base de datos
from database.db import (
    crear_base_datos, guardar_en_bd, guardar_historial_busqueda,
    guardar_fluctuacion, buscar_en_bd_local, obtener_articulos_por_busqueda,
    obtener_historial_por_fechas, obtener_fechas_con_busquedas,
    obtener_busquedas_por_fecha, obtener_fluctuacion_historica
)

# Scrapers
from scrapers.revolico import obtener_precios_revolico
from scrapers.multi_fuente import AgregadorMultiFuente

# ==============================================================================
# MAIN (para pruebas directas)
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "═" * 65)
    print("║" + " 🔧 REVOLICO SCRAPER V7.0 - MODULAR ".center(63) + "║")
    print("═" * 65)
    print("║  ✅ Código desacoplado en módulos                        ║")
    print("║  ✅ config/ - Configuración y constantes                 ║")
    print("║  ✅ core/ - Utilidades y análisis                        ║")
    print("║  ✅ database/ - Operaciones BD                           ║")
    print("║  ✅ scrapers/ - Revolico y multi-fuente                  ║")
    print("║  ✅ services/ - Servicios de búsqueda                    ║")
    print("║  ✅ ui/ - Componentes de interfaz                        ║")
    print("═" * 65 + "\n")
    
    crear_base_datos()
    
    termino = input("Ingresa término de búsqueda (Enter para salir): ").strip()
    if termino:
        articulos = obtener_precios_revolico(producto_original=termino, categoria="electrodomesticos")
        
        if articulos:
            analisis = analizar_precios(articulos, "electrodomesticos")
            print(f"\n📊 Resultados:")
            print(f"   Total: {analisis['total_extraidos']}")
            print(f"   Mediana: ${analisis['precio_mediana']:.2f}")
            
            guardar_en_bd(articulos, 'profunda')
            guardar_historial_busqueda(
                obtener_id_busqueda(), termino, "electrodomesticos", None, 'profunda', analisis
            )