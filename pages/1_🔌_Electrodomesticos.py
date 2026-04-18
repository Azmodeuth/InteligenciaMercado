"""
================================================================================
PÁGINA: ELECTRODOMÉSTICOS V10.2 - ARQUITECTURA ASÍNCRONA + TODAS LAS FUNCIONES
================================================================================
- Inyección inversa mediante st.empty() (Anti-Congelamiento).
- Componentes HTML crudo (Anti-Traductor de Google).
- RESTAURADO: Tasas de Cambio, Gráfica de Fluctuación, Clasificación, Exportar CSV y Accesos Rápidos.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Asegurar que el sistema reconozca la raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CATEGORIAS, TASAS_DE_CAMBIO, PRECIO_MINIMO_VALIDO, actualizar_tasas_cambio
from database.db import crear_base_datos, buscar_en_bd_local, obtener_fluctuacion_historica
from services.search_service import busqueda_rapida, busqueda_profunda
from ui.styles import CSS

# ==============================================================================
# CONFIGURACIÓN E INICIALIZACIÓN
# ==============================================================================
st.set_page_config(page_title="Electrodomésticos - Inteligencia de Mercado", page_icon="🔌", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

CATEGORIA = "electrodomesticos"
SUBCATEGORIAS = CATEGORIAS[CATEGORIA]["subcategorias"]
crear_base_datos()

# Inicializar todo el estado
for key, default in [
    ('articulos', []), ('tipo_busqueda_actual', None), ('termino_actual', ''),
    ('articulos_online',[]), ('articulos_offline',[])
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==============================================================================
# FUNCIONES AUXILIARES Y COMPONENTES HTML
# ==============================================================================
def calcular_analisis_lista(articulos: list) -> dict:
    default_stats = {'validos': 0, 'precio_minimo': 0.0, 'precio_maximo': 0.0, 'precio_promedio': 0.0, 'precio_mediana': 0.0, 'fuentes_encontradas': {}}
    if not articulos: return default_stats
    
    fuentes = {}
    precios_brutos =[]
    try: min_val = float(PRECIO_MINIMO_VALIDO)
    except: min_val = 1.0

    for a in articulos:
        f = a.get('fuente', 'desconocida')
        fuentes[f] = fuentes.get(f, 0) + 1
        
        try:
            p = float(a.get('precio_usd', 0))
            if p > min_val: precios_brutos.append(p)
        except: continue
            
    if not precios_brutos: 
        default_stats['fuentes_encontradas'] = fuentes
        return default_stats
    
    s_precios = pd.Series(precios_brutos)
    if len(s_precios) >= 4:
        s_filtrado = s_precios[(s_precios >= s_precios.quantile(0.15)) & (s_precios <= s_precios.quantile(0.85))]
    else:
        s_filtrado = s_precios
        
    if s_filtrado.empty: s_filtrado = s_precios
        
    return {
        'validos': int(len(s_filtrado)), 'precio_minimo': float(s_filtrado.min()),
        'precio_maximo': float(s_filtrado.max()), 'precio_promedio': float(s_filtrado.mean()),
        'precio_mediana': float(s_filtrado.median()), 'fuentes_encontradas': fuentes
    }

def generar_html_indicadores(titulo: str, analisis: dict, cantidad: int, color: str, icono: str):
    return f"""
    <div class="notranslate" translate="no" style="margin-top: 1rem; margin-bottom: 1rem; font-family: sans-serif;">
        <div style="background: {color}; color: white; padding: 0.6rem 1rem; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 1.1rem; text-transform: uppercase;">
            {icono} {titulo}
        </div>
        <div style="display: flex; gap: 10px; background: rgba(30, 30, 30, 0.5); padding: 1rem; border-radius: 0 0 8px 8px; border: 1px solid rgba(255,255,255,0.1); flex-wrap: wrap;">
            <div style="flex: 1; min-width: 130px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                <p style="color: #a0a0a0; font-size: 0.85rem; margin: 0; font-weight: bold;">{icono} Anuncios</p>
                <p style="color: white; margin: 5px 0; font-size: 1.8rem; font-weight: bold;">{cantidad}</p>
                <p style="color: {color}; font-size: 0.8rem; margin: 0; font-weight: bold;">↑ Válidos: {analisis['validos']}</p>
            </div>
            <div style="flex: 1; min-width: 130px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                <p style="color: #a0a0a0; font-size: 0.85rem; margin: 0; font-weight: bold;">🟢 Mínimo</p>
                <p style="color: white; margin: 5px 0; font-size: 1.8rem; font-weight: bold;">${analisis['precio_minimo']:.2f}</p>
                <p style="color: {color}; font-size: 0.8rem; margin: 0; font-weight: bold;">↑ Venta rápida</p>
            </div>
            <div style="flex: 1; min-width: 130px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                <p style="color: #a0a0a0; font-size: 0.85rem; margin: 0; font-weight: bold;">🔴 Máximo</p>
                <p style="color: white; margin: 5px 0; font-size: 1.8rem; font-weight: bold;">${analisis['precio_maximo']:.2f}</p>
                <p style="color: {color}; font-size: 0.8rem; margin: 0; font-weight: bold;">↑ Techo</p>
            </div>
            <div style="flex: 1; min-width: 130px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                <p style="color: #a0a0a0; font-size: 0.85rem; margin: 0; font-weight: bold;">📈 Promedio</p>
                <p style="color: white; margin: 5px 0; font-size: 1.8rem; font-weight: bold;">${analisis['precio_promedio']:.2f}</p>
                <p style="color: {color}; font-size: 0.8rem; margin: 0; font-weight: bold;">↑ Media</p>
            </div>
            <div style="flex: 1; min-width: 130px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                <p style="color: #a0a0a0; font-size: 0.85rem; margin: 0; font-weight: bold;">🎯 SUGERIDO</p>
                <p style="color: white; margin: 5px 0; font-size: 1.8rem; font-weight: bold;">${analisis['precio_mediana']:.2f}</p>
                <p style="color: {color}; font-size: 0.8rem; margin: 0; font-weight: bold;">↑ Mediana</p>
            </div>
        </div>
    </div>
    """

def generar_html_comparativa(analisis_online, analisis_offline, cant_online, cant_offline):
    diff, pct = 0, 0
    if analisis_offline['precio_mediana'] > 0 and analisis_online['precio_mediana'] > 0:
        diff = analisis_online['precio_mediana'] - analisis_offline['precio_mediana']
        pct = (diff / analisis_offline['precio_mediana'] * 100)
        
    color_diff = "#28a745" if pct >= 0 else "#dc3545"
    signo = "+" if pct >= 0 else ""
    
    return f"""
    <div class="notranslate" translate="no" style="display: flex; gap: 15px; margin-top: 1rem; margin-bottom: 2rem; flex-wrap: wrap; font-family: sans-serif;">
        <div style="flex: 1; min-width: 200px; background: rgba(0, 123, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; border: 1px solid rgba(255,255,255,0.05); border-left-width: 5px;">
            <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0; font-weight: bold;">💾 OFFLINE (Histórico)</p>
            <p style="color: white; margin: 5px 0; font-size: 2rem; font-weight: bold;">${analisis_offline['precio_mediana']:.2f}</p>
            <p style="color: #007bff; font-size: 0.85rem; margin: 0; font-weight: bold;">↑ {cant_offline} productos</p>
        </div>
        <div style="flex: 1; min-width: 200px; background: rgba(40, 167, 69, 0.05); padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; border: 1px solid rgba(255,255,255,0.05); border-left-width: 5px;">
            <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0; font-weight: bold;">🌐 ONLINE (Tiempo Real)</p>
            <p style="color: white; margin: 5px 0; font-size: 2rem; font-weight: bold;">${analisis_online['precio_mediana']:.2f}</p>
            <p style="color: #28a745; font-size: 0.85rem; margin: 0; font-weight: bold;">↑ {cant_online} productos</p>
        </div>
        <div style="flex: 1; min-width: 200px; background: rgba(255, 255, 255, 0.02); padding: 15px; border-radius: 8px; border-left: 5px solid {color_diff}; border: 1px solid rgba(255,255,255,0.05); border-left-width: 5px;">
            <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0; font-weight: bold;">📊 Diferencia</p>
            <p style="color: white; margin: 5px 0; font-size: 2rem; font-weight: bold;">${diff:.2f}</p>
            <p style="color: {color_diff}; font-size: 0.85rem; margin: 0; font-weight: bold;">↑ {signo}{pct:.1f}%</p>
        </div>
    </div>
    """

def mostrar_grafico_comparativa(analisis_online, analisis_offline, cant_online, cant_offline):
    fig = make_subplots(rows=1, cols=2, subplot_titles=(f'💾 Offline ({cant_offline} prod)', f'🌐 Online ({cant_online} prod)'))
    v_off = analisis_offline['precio_mediana'] if analisis_offline['precio_mediana'] > 0 else 0.01
    v_on = analisis_online['precio_mediana'] if analisis_online['precio_mediana'] > 0 else 0.01
    
    fig.add_trace(go.Bar(x=['Mediana'], y=[v_off], marker_color='#007bff', text=f"${analisis_offline['precio_mediana']:.2f}", textposition='outside'), row=1, col=1)
    fig.add_trace(go.Bar(x=['Mediana'], y=[v_on], marker_color='#28a745', text=f"${analisis_online['precio_mediana']:.2f}", textposition='outside'), row=1, col=2)
    
    fig.update_yaxes(range=[0, max(v_off, v_on, 100) * 1.4])
    fig.update_layout(height=350, showlegend=False, title_text="Comparativa Mediana de Precios", title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)

def mostrar_fuentes(analisis: dict):
    fuentes = analisis.get('fuentes_encontradas', {})
    if not fuentes: return
    iconos = {'revolico': '🔵', 'voypati': '🟢', 'elyerromenu': '🟠', 'fadiar': '🟡', 'google': '🔍'}
    colores = {'revolico': '#1565C0', 'voypati': '#2E7D32', 'elyerromenu': '#E65100', 'fadiar': '#7B1FA2', 'google': '#9b59b6'}
    cols = st.columns(len(fuentes))
    for i, (fuente, count) in enumerate(fuentes.items()):
        with cols[i]:
            icono = iconos.get(fuente, '⚪')
            color = colores.get(fuente, '#666666')
            st.markdown(f"""
            <div class="notranslate" translate="no" style="background: {color}; padding: 1rem; border-radius: 0.5rem; text-align: center; color: white;">
                <span style="font-size: 1.5rem;">{icono}</span>
                <h4 style="margin: 0.3rem 0; color: white;">{fuente.title()}</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold;">{count}</p>
            </div>
            """, unsafe_allow_html=True)

def clasificar_productos(articulos: list, precio_promedio: float) -> dict:
    if not articulos or precio_promedio <= 0: return {"nuevos": [], "de_uso":[], "umbral": 0}
    umbral = precio_promedio * 0.50
    nuevos, de_uso = [],[]
    for art in articulos:
        try: precio = float(art.get('precio_usd', 0))
        except: precio = 0.0
        if precio <= 1: continue
        
        art_c = art.copy()
        if precio < umbral:
            art_c['condicion'] = 'De uso'
            de_uso.append(art_c)
        else:
            art_c['condicion'] = 'Nuevo'
            nuevos.append(art_c)
    return {"nuevos": nuevos, "de_uso": de_uso, "umbral": round(umbral, 2)}

# ==============================================================================
# HEADER Y TASAS DE CAMBIO (RESTAURADO)
# ==============================================================================
st.markdown("# 🔌 Electrodomésticos")
st.markdown("### Sistema de Inteligencia de Precios v10.2")
st.markdown("---")

with st.expander("💱 Configurar Tasas de Cambio", expanded=False):
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1: tasa_cup = st.number_input("CUP → USD", min_value=100.0, max_value=500.0, value=float(TASAS_DE_CAMBIO["CUP"]), step=5.0)
    with col_t2: tasa_mlc = st.number_input("MLC → USD", min_value=0.5, max_value=2.0, value=float(TASAS_DE_CAMBIO["MLC"]), step=0.1)
    with col_t3: tasa_eur = st.number_input("EUR → USD", min_value=0.8, max_value=1.5, value=float(TASAS_DE_CAMBIO["EUR"]), step=0.05)
    with col_t4: st.metric("USD", "1.00", "Moneda base")
    
    if st.button("💾 Guardar Tasas", type="secondary"):
        actualizar_tasas_cambio(cup=tasa_cup, mlc=tasa_mlc, eur=tasa_eur)
        st.success("✅ Tasas actualizadas")

# ==============================================================================
# ESPACIO DE INYECCIÓN INVERSA (INDICADORES ARRIBA)
# ==============================================================================
contenedor_indicadores = st.empty()

st.markdown("---")
# ==============================================================================
# BUSCADOR
# ==============================================================================
st.markdown("## 🔍 Buscar Productos")

col_subcat, col_info = st.columns([2, 1])
with col_subcat:
    subcategoria_seleccionada = st.selectbox(
        "Subcategoría", options=[""] + list(SUBCATEGORIAS.keys()),
        format_func=lambda x: "🎯 Selecciona una categoría..." if x == "" else f"{SUBCATEGORIAS[x]['nombre']}"
    )

termino_busqueda = st.text_input("Búsqueda específica (opcional)", placeholder="Ej: nevera samsung, aire 12000 btu...")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
btn_rapida = col_btn1.button("⚡ BÚSQUEDA RÁPIDA", type="primary", use_container_width=True)
btn_profunda = col_btn2.button("🌐 BÚSQUEDA PROFUNDA", type="secondary", use_container_width=True)
btn_limpiar = col_btn3.button("🔄 Limpiar", use_container_width=True)

if btn_limpiar:
    st.session_state.articulos =[]
    st.session_state.tipo_busqueda_actual = None
    st.session_state.termino_actual = ''

# ==============================================================================
# LÓGICA DE EXTRACCIÓN
# ==============================================================================
if btn_rapida or btn_profunda:
    if subcategoria_seleccionada or termino_busqueda:
        subcat = subcategoria_seleccionada if subcategoria_seleccionada else "general"
        term = termino_busqueda if termino_busqueda else None
        
        msg = "⚡ Consultando BD Local..." if btn_rapida else "🌐 Extracción Profunda Multi-fuente..."
        with st.spinner(msg):
            if btn_rapida:
                exito, articulos, analisis = busqueda_rapida(subcat, term, CATEGORIA)
            else:
                exito, articulos, analisis = busqueda_profunda(subcat, term, CATEGORIA)
                
            if exito:
                st.session_state.articulos = articulos
                st.session_state.tipo_busqueda_actual = "rapida" if btn_rapida else "profunda"
                st.session_state.termino_actual = term or subcat
            else:
                st.error("❌ No se encontraron resultados.")
    else:
        st.warning("⚠️ Selecciona una categoría o escribe un término")

# ==============================================================================
# PROCESAMIENTO MATEMÁTICO INMEDIATO
# ==============================================================================
articulos_memoria = st.session_state.articulos
art_online =[a for a in articulos_memoria if a.get('es_online', True)]
art_offline =[a for a in articulos_memoria if not a.get('es_online', True)]

if st.session_state.tipo_busqueda_actual == 'profunda' and st.session_state.termino_actual:
    art_offline = buscar_en_bd_local(st.session_state.termino_actual, CATEGORIA)

analisis_on = calcular_analisis_lista(art_online)
analisis_off = calcular_analisis_lista(art_offline)

# ==============================================================================
# INYECCIÓN HTML DE LAS BARRAS (HACIA ARRIBA)
# ==============================================================================
with contenedor_indicadores.container():
    st.markdown("## 📊 Indicadores de Precio")
    st.markdown(generar_html_indicadores("INDICADORES ONLINE (Resultados de Búsqueda)", analisis_on, len(art_online), "#28a745", "🌐"), unsafe_allow_html=True)
    st.markdown(generar_html_indicadores("INDICADORES OFFLINE (Base Histórica Local)", analisis_off, len(art_offline), "#007bff", "💾"), unsafe_allow_html=True)
    
    st.markdown("### 📊 Comparativa Directa")
    st.markdown(generar_html_comparativa(analisis_on, analisis_off, len(art_online), len(art_offline)), unsafe_allow_html=True)
    mostrar_grafico_comparativa(analisis_on, analisis_off, len(art_online), len(art_offline))

# ==============================================================================
# RESULTADOS INFERIORES: FUENTES, GRAFICAS Y TABLAS (RESTAURADO)
# ==============================================================================
if st.session_state.articulos:
    # 1. Banner Info
    tipo = st.session_state.tipo_busqueda_actual
    banner_class = "info-profunda" if tipo == 'profunda' else "info-rapida"
    st.markdown(f"""
    <div class="{banner_class}">
        <strong>{"🌐 Búsqueda Profunda" if tipo == 'profunda' else "⚡ Búsqueda Rápida"}:</strong>
        {len(articulos_memoria)} anuncios procesados para <strong>{st.session_state.termino_actual.upper()}</strong>
    </div>
    """, unsafe_allow_html=True)

    # 2. Fuentes
    st.markdown("---")
    st.markdown("### 📡 Productos por Fuente")
    mostrar_fuentes(analisis_on)

    # 3. Gráfica de Fluctuación (RESTAURADA)
    st.markdown("---")
    st.markdown("### 📈 Historial de Fluctuación (30 días)")
    termino_hist = st.session_state.termino_actual
    if termino_hist:
        df_fluct = obtener_fluctuacion_historica(termino_hist, dias=30)
        if not df_fluct.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_fluct['fecha'], y=df_fluct['precio_mediana'], mode='lines+markers', name='Mediana', line=dict(color='#2ecc71', width=3)))
            fig.update_layout(title=f"Tendencia de Precios: {termino_hist.title()}", xaxis_title="Fecha", yaxis_title="Precio USD", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"📊 No hay historial previo guardado para '{termino_hist}'")

    # 4. Tabla Maestra
    st.markdown("---")
    st.markdown("### 📋 Tabla Maestra de Anuncios")
    df = pd.DataFrame(articulos_memoria)
    df['precio_usd'] = pd.to_numeric(df['precio_usd'], errors='coerce').fillna(0.0)
    
    umbral = analisis_on['precio_promedio'] * 0.50
    df['condicion'] = df.apply(lambda r: '🔍 Referencia' if r.get('fuente') == 'google' else ('⏳ Sin precio' if r.get('precio_usd',0)<=0 else ('🔧 De uso' if r.get('precio_usd',0)<umbral else '🆕 Nuevo')), axis=1)
    df['tipo'] = df.get('es_online', True).apply(lambda x: '🌐 Online' if x else '💾 Offline')
    
    if 'fecha_extraccion' in df.columns and 'hora_extraccion' in df.columns:
        df['fecha_hora'] = df.apply(lambda x: f"{x['fecha_extraccion']} {str(x['hora_extraccion'])[:8]}" if pd.notna(x.get('fecha_extraccion')) else '', axis=1)
    
    columnas_mostrar =['titulo', 'descripcion', 'fecha_hora', 'tipo', 'condicion', 'fuente', 'precio_original', 'precio_usd', 'enlace']
    cols_existentes =[c for c in columnas_mostrar if c in df.columns]
    
    st.dataframe(
        df[cols_existentes],
        column_config={
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "precio_usd": st.column_config.NumberColumn("USD", format="$%.2f"),
            "enlace": st.column_config.LinkColumn("Enlace", display_text="Ver 🔗")
        }, hide_index=True, use_container_width=True, height=500
    )

    # 5. Clasificación Nuevos vs Usados (RESTAURADA)
    st.markdown("---")
    st.markdown("### 🏷️ Clasificación de Productos")
    clasif = clasificar_productos(articulos_memoria, analisis_on.get('precio_promedio', 0))
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.metric("🆕 Probablemente Nuevos", len(clasif['nuevos']))
    with col_c2: st.metric("🔧 Probablemente De Uso", len(clasif['de_uso']))
    with col_c3: st.metric("📏 Umbral de Condición", f"$ {clasif['umbral']:.2f}")

    # 6. Botón Descargar CSV (RESTAURADO)
    st.markdown("---")
    df_exp = pd.DataFrame([a for a in articulos_memoria if float(a.get('precio_usd', 0)) > float(PRECIO_MINIMO_VALIDO)])
    if not df_exp.empty:
        csv = df_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, f"resultados_{termino_hist}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# ==============================================================================
# ACCESOS RÁPIDOS (RESTAURADOS)
# ==============================================================================
st.markdown("---")
st.markdown("### ⚡ Accesos Rápidos")
cols = st.columns(4)
rapidas =[("❄️ Neveras", "neveras"), ("🌬️ Aires", "aires"), ("📺 Televisores", "televisores"), ("🧺 Lavadoras", "lavadoras")]
for i, (nombre, key) in enumerate(rapidas):
    with cols[i % 4]:
        if st.button(nombre, key=f"btn_rap_{key}", use_container_width=True):
            exito, articulos, analisis = busqueda_rapida(key, None, CATEGORIA)
            if exito:
                st.session_state.articulos = articulos
                st.session_state.tipo_busqueda_actual = 'rapida'
                st.session_state.termino_actual = key
                st.rerun() # Aquí sí es válido un rerun porque es un cambio de página completo forzado por el usuario

st.markdown("---")
st.markdown("💡 **Arquitectura de Inteligencia v10.2 - Mercado Cuba**")