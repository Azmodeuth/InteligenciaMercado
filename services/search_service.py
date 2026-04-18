"""
================================================================================
SERVICIO DE BÚSQUEDA - VERSIÓN 11.2 (SESIÓN UNIFICADA)
================================================================================
"""
import streamlit as st
from datetime import datetime
from typing import Tuple, List, Dict

from config.settings import CATEGORIAS, PRECIO_MINIMO_VALIDO, logger
from scrapers.revolico import obtener_precios_revolico
from scrapers.multi_fuente import AgregadorMultiFuente
from services.google_search import buscar_google_directo, convertir_google_a_articulo
from database.db import guardar_en_bd, guardar_historial_busqueda, guardar_fluctuacion, buscar_en_bd_local
from core.analysis import analizar_precios

_agregador = None

def obtener_agregador():
    global _agregador
    if _agregador is None: _agregador = AgregadorMultiFuente()
    return _agregador

def busqueda_rapida(subcategoria: str, termino: str, categoria: str = "electrodomesticos") -> Tuple[bool, List, Dict]:
    subcats = CATEGORIAS.get(categoria, {}).get("subcategorias", {})
    productos_predefinidos = subcats.get(subcategoria, {}).get('productos') if subcategoria in subcats else None
    
    # Determinar el término de búsqueda real
    termino_final = termino if (termino and termino.strip() != "") else (productos_predefinidos[0] if productos_predefinidos else "electrodomestico")
    
    # BUSQUEDA LOCAL: Pasamos subcategoría para asegurar que encuentre la sesión de la búsqueda profunda
    articulos_bd = buscar_en_bd_local(termino_final, categoria, subcategoria, dias_maximos=30)
    
    # UMBRAL: Si hay datos en la BD, se muestran inmediatamente
    MIN_PRODUCTOS = 1 
    id_sesion = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if len(articulos_bd) >= MIN_PRODUCTOS:
        st.success(f"⚡ Datos locales recuperados al instante ({len(articulos_bd)} anuncios).")
        todos = articulos_bd
        analisis = analizar_precios(todos, categoria, subcategoria, 'rapida')
        
        # Guardamos el historial de esta consulta rápida
        guardar_historial_busqueda(id_sesion, termino_final, categoria, subcategoria, 'rapida', analisis)
        guardar_fluctuacion(termino_final, categoria, subcategoria, analisis)
        return True, todos, analisis
    
    # Si de verdad no hay NADA en la base de datos, entonces scraping
    else:
        st.info(f"📊 No hay registros previos de '{subcategoria}'. Sincronizando...")
        with st.spinner("🌐 Sincronizando con fuentes online..."):
            articulos_revolico = obtener_precios_revolico(producto_original=termino_final, categoria=categoria, subcategoria=subcategoria)
            for art in articulos_revolico: art['es_online'] = True
            
            extras = []
            try:
                agregador = obtener_agregador()
                resultados_multi = agregador.buscar_todos(termino_final, categoria, exhaustivo=True)
                extras = agregador.consolidar_resultados(resultados_multi)
                for art in extras: art['es_online'] = True
            except Exception as e:
                logger.error(f"Error en fuentes externas: {e}")
        
        articulos_online = articulos_revolico + extras
        todos = articulos_online
        
        if articulos_online: 
            # Inyectar metadata antes de guardar para asegurar recuperación
            for art in todos:
                art['id_busqueda'] = id_sesion
                art['producto_buscado'] = termino_final
                art['categoria'] = categoria
                art['subcategoria'] = subcategoria
            guardar_en_bd(todos, 'rapida')
        
        analisis = analizar_precios(todos, categoria, subcategoria, 'rapida')
        guardar_historial_busqueda(id_sesion, termino_final, categoria, subcategoria, 'rapida', analisis)
        guardar_fluctuacion(termino_final, categoria, subcategoria, analisis)
        
        if todos: return True, todos, analisis
        return False, [], {}

def busqueda_profunda(subcategoria: str, termino: str, categoria: str = "electrodomesticos") -> Tuple[bool, List, Dict]:
    subcats = CATEGORIAS.get(categoria, {}).get("subcategorias", {})
    productos_predefinidos = subcats.get(subcategoria, {}).get('productos') if subcategoria in subcats else None
    termino_final = termino if (termino and termino.strip() != "") else (productos_predefinidos[0] if productos_predefinidos else "electrodomestico")
    
    # ID DE SESIÓN UNIFICADO PARA TODO EL LOTE (Evita el problema de los 1000 items)
    id_sesion = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with st.spinner("🌐 Ejecutando Inteligencia Profunda de Mercado..."):
        articulos_revolico = obtener_precios_revolico(producto_original=termino_final, categoria=categoria, subcategoria=subcategoria, paginas=15)
        for art in articulos_revolico: art['es_online'] = True
        if articulos_revolico: st.info(f"📦 Revolico: {len(articulos_revolico)} anuncios extraídos.")
        
        extras =[]
        try:
            agregador = obtener_agregador()
            resultados_multi = agregador.buscar_todos(termino_final, categoria, exhaustivo=True)
            extras = agregador.consolidar_resultados(resultados_multi)
            for art in extras: art['es_online'] = True
            if extras: st.info(f"📦 Multi-fuente: {len(extras)} anuncios consolidados.")
        except Exception: pass
        
        articulos_google =[]
        try:
            resultados_google = buscar_google_directo(termino_final, num_resultados=12)
            articulos_google =[convertir_google_a_articulo(r, termino_final, categoria) for r in resultados_google if r]
            if articulos_google: st.success(f"✅ Google/Bing: {len(articulos_google)} referencias web encontradas.")
        except Exception: pass
    
    pool_online = articulos_revolico + extras + articulos_google
    if pool_online:
        # SINCRONIZACIÓN DE METADATOS: Aseguramos que todos los 1000+ items compartan el ID y la subcategoría
        for art in pool_online:
            art['id_busqueda'] = id_sesion
            art['producto_buscado'] = termino_final
            art['categoria'] = categoria
            art['subcategoria'] = subcategoria

        articulos_offline = buscar_en_bd_local(termino_final, categoria, subcategoria)
        con_precio =[a for a in pool_online if a.get('precio_usd', 0) > PRECIO_MINIMO_VALIDO]
        
        if con_precio: 
            guardar_en_bd(con_precio, 'profunda')
        
        todos_para_analizar = pool_online + articulos_offline
        analisis = analizar_precios(todos_para_analizar, categoria, subcategoria, 'profunda')
        
        guardar_historial_busqueda(id_sesion, termino_final, categoria, subcategoria, 'profunda', analisis)
        guardar_fluctuacion(termino_final, categoria, subcategoria, analisis)
        return True, todos_para_analizar, analisis
    
    return False, [], {}