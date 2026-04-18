"""
================================================================================
ANÁLISIS DE PRECIOS - VERSIÓN DINÁMICA
================================================================================
"""
import numpy as np
from config.settings import QUANTILE_INFERIOR, QUANTILE_SUPERIOR, PRECIO_MINIMO_VALIDO

def analizar_precios(articulos: list, categoria: str = None, subcategoria: str = None, 
                    tipo_busqueda: str = 'profunda') -> dict:
    """Analiza los precios de una lista de artículos, separando Offline vs Online."""
    if not articulos:
        return {
            "total_extraidos": 0, "validos": 0, "outliers": 0,
            "precio_minimo": 0, "precio_maximo": 0, "precio_promedio": 0,
            "precio_mediana": 0, "precio_mediana_offline": 0, "precio_mediana_online": 0,
            "fuentes_encontradas": {}, "valores_usados": {}
        }
    
    # Separar productos online vs offline (Soporta booleanos e integrales 1/0)
    articulos_online = [a for a in articulos if a.get('es_online') in [True, 1]]
    articulos_offline = [a for a in articulos if a.get('es_online') in [False, 0]]
    
    # Extraer precios USD válidos
    precios_online = [a['precio_usd'] for a in articulos_online if a.get('precio_usd', 0) > PRECIO_MINIMO_VALIDO]
    precios_offline = [a['precio_usd'] for a in articulos_offline if a.get('precio_usd', 0) > PRECIO_MINIMO_VALIDO]
    todos_precios = precios_online + precios_offline
    
    if not todos_precios:
        return {
            "total_extraidos": len(articulos), "validos": 0, "outliers": 0,
            "precio_minimo": 0, "precio_maximo": 0, "precio_promedio": 0,
            "precio_mediana": 0, "precio_mediana_offline": 0, "precio_mediana_online": 0,
            "fuentes_encontradas": {}, "valores_usados": {}
        }
    
    # Filtrar outliers
    precios_array = np.array(todos_precios)
    q_inf = np.quantile(precios_array, QUANTILE_INFERIOR)
    q_sup = np.quantile(precios_array, QUANTILE_SUPERIOR)
    precios_filtrados = [p for p in todos_precios if q_inf <= p <= q_sup]
    
    # Calcular estadísticas generales
    precio_minimo = float(min(precios_filtrados)) if precios_filtrados else 0
    precio_maximo = float(max(precios_filtrados)) if precios_filtrados else 0
    precio_promedio = float(np.mean(precios_filtrados)) if precios_filtrados else 0
    precio_mediana = float(np.median(precios_filtrados)) if precios_filtrados else 0
    
    # Calcular medianas específicas para los indicadores de la página de Electrodomésticos
    precio_mediana_offline = float(np.median(precios_offline)) if precios_offline else 0
    precio_mediana_online = float(np.median(precios_online)) if precios_online else 0
    
    # Contar fuentes
    fuentes = {}
    for art in articulos:
        fuente = art.get('fuente', 'desconocida')
        fuentes[fuente] = fuentes.get(fuente, 0) + 1
    
    return {
        "total_extraidos": len(articulos),
        "validos": len(precios_filtrados),
        "outliers": len(todos_precios) - len(precios_filtrados),
        "precio_minimo": round(precio_minimo, 2),
        "precio_maximo": round(precio_maximo, 2),
        "precio_promedio": round(precio_promedio, 2),
        "precio_mediana": round(precio_mediana, 2),
        "precio_mediana_offline": round(precio_mediana_offline, 2),
        "precio_mediana_online": round(precio_mediana_online, 2),
        "fuentes_encontradas": fuentes,
        "valores_usados": {
            "total_analizado": len(todos_precios),
            "rango_precios_usado": [round(precio_minimo, 2), round(precio_maximo, 2)],
            "outliers_excluidos": len(todos_precios) - len(precios_filtrados),
            "quantiles_usados": [QUANTILE_INFERIOR, QUANTILE_SUPERIOR],
            "productos_offline": len(precios_offline),
            "productos_online": len(precios_online)
        }
    }

def analizar_mercado(articulos: list) -> dict:
    """Análisis completo del mercado con desviación estándar."""
    analisis = analizar_precios(articulos)
    
    if analisis['validos'] > 0:
        precios = [a['precio_usd'] for a in articulos if a.get('precio_usd', 0) > PRECIO_MINIMO_VALIDO]
        if len(precios) >= 2:
            analisis['desviacion_estandar'] = round(float(np.std(precios)), 2)
            analisis['coeficiente_variacion'] = round(float(np.std(precios) / np.mean(precios) * 100), 1) if np.mean(precios) > 0 else 0
    
    return analisis