"""
================================================================================
COMPONENTES DE UI - VERSIÓN CON 3 BARRAS SIEMPRE VISIBLES
================================================================================
Las 3 barras se muestran SIEMPRE:
1. Indicadores ONLINE
2. Indicadores OFFLINE  
3. Comparativa Offline vs Online
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def mostrar_indicadores(analisis: dict, cantidad_articulos: int):
    """Muestra los indicadores de precio principales."""
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("📊 Anuncios", cantidad_articulos, f"Válidos: {analisis.get('validos', 0)}")
    with col2: st.metric("🟢 Mínimo", f"${analisis.get('precio_minimo', 0):.2f}", "Venta rápida")
    with col3: st.metric("🔴 Máximo", f"${analisis.get('precio_maximo', 0):.2f}", "Techo")
    with col4: st.metric("📈 Promedio", f"${analisis.get('precio_promedio', 0):.2f}", "Media")
    with col5: st.metric("🎯 SUGERIDO", f"${analisis.get('precio_mediana', 0):.2f}", "MEDIANA")


def mostrar_indicadores_completos(analisis: dict, articulos: list):
    """
    Muestra SIEMPRE las 3 barras de indicadores:
    =============================================
    BARRA 1: Indicadores ONLINE (SIEMPRE visible)
    BARRA 2: Indicadores OFFLINE (SIEMPRE visible)
    BARRA 3: Comparativa Offline vs Online (SIEMPRE visible)
    
    Aunque no haya datos offline, las barras se muestran.
    """
    
    # Separar artículos online y offline
    articulos_online = [a for a in articulos if a.get('es_online', True)]
    articulos_offline = [a for a in articulos if not a.get('es_online', True)]
    
    # Calcular análisis para online
    precios_online = [a.get('precio_usd', 0) for a in articulos_online if a.get('precio_usd', 0) > 0]
    analisis_online = {
        'validos': len(precios_online),
        'precio_minimo': min(precios_online) if precios_online else 0,
        'precio_maximo': max(precios_online) if precios_online else 0,
        'precio_promedio': sum(precios_online) / len(precios_online) if precios_online else 0,
        'precio_mediana': sorted(precios_online)[len(precios_online)//2] if precios_online else 0
    }
    
    # Calcular análisis para offline
    precios_offline = [a.get('precio_usd', 0) for a in articulos_offline if a.get('precio_usd', 0) > 0]
    analisis_offline = {
        'validos': len(precios_offline),
        'precio_minimo': min(precios_offline) if precios_offline else 0,
        'precio_maximo': max(precios_offline) if precios_offline else 0,
        'precio_promedio': sum(precios_offline) / len(precios_offline) if precios_offline else 0,
        'precio_mediana': sorted(precios_offline)[len(precios_offline)//2] if precios_offline else 0
    }
    
    # ========================================
    # CONTENEDOR PRINCIPAL CON BORDE
    # ========================================
    st.markdown("""
    <style>
    .indicadores-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .barra-header {
        background: #495057;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .barra-online { border-left: 5px solid #28a745; }
    .barra-offline { border-left: 5px solid #007bff; }
    .barra-comparativa { border-left: 5px solid #6f42c1; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="indicadores-container">', unsafe_allow_html=True)
    
    # ========================================
    # BARRA 1: INDICADORES ONLINE (SIEMPRE)
    # ========================================
    st.markdown('<div class="barra-header barra-online">🌐 INDICADORES ONLINE (Búsqueda Actual)</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if articulos_online:
        with col1: 
            st.metric("🌐 Anuncios", len(articulos_online), f"Válidos: {analisis_online['validos']}")
        with col2: 
            st.metric("🟢 Mínimo", f"${analisis_online['precio_minimo']:.2f}", "Venta rápida")
        with col3: 
            st.metric("🔴 Máximo", f"${analisis_online['precio_maximo']:.2f}", "Techo")
        with col4: 
            st.metric("📈 Promedio", f"${analisis_online['precio_promedio']:.2f}", "Media")
        with col5: 
            st.metric("🎯 SUGERIDO", f"${analisis_online['precio_mediana']:.2f}", "MEDIANA")
    else:
        with col1: 
            st.metric("🌐 Anuncios", "0", "Sin datos online")
        with col2: 
            st.metric("🟢 Mínimo", "$0.00", "Sin datos")
        with col3: 
            st.metric("🔴 Máximo", "$0.00", "Sin datos")
        with col4: 
            st.metric("📈 Promedio", "$0.00", "Sin datos")
        with col5: 
            st.metric("🎯 SUGERIDO", "$0.00", "Sin datos")
    
    st.markdown("---")
    
    # ========================================
    # BARRA 2: INDICADORES OFFLINE (SIEMPRE)
    # ========================================
    st.markdown('<div class="barra-header barra-offline">💾 INDICADORES OFFLINE (Histórico)</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if articulos_offline:
        with col1: 
            st.metric("💾 Anuncios", len(articulos_offline), f"Válidos: {analisis_offline['validos']}")
        with col2: 
            st.metric("🟢 Mínimo", f"${analisis_offline['precio_minimo']:.2f}", "Venta rápida")
        with col3: 
            st.metric("🔴 Máximo", f"${analisis_offline['precio_maximo']:.2f}", "Techo")
        with col4: 
            st.metric("📈 Promedio", f"${analisis_offline['precio_promedio']:.2f}", "Media")
        with col5: 
            st.metric("🎯 SUGERIDO", f"${analisis_offline['precio_mediana']:.2f}", "MEDIANA")
    else:
        with col1: 
            st.metric("💾 Anuncios", "0", "Sin histórico")
        with col2: 
            st.metric("🟢 Mínimo", "$0.00", "Sin datos")
        with col3: 
            st.metric("🔴 Máximo", "$0.00", "Sin datos")
        with col4: 
            st.metric("📈 Promedio", "$0.00", "Sin datos")
        with col5: 
            st.metric("🎯 SUGERIDO", "$0.00", "Sin datos")
    
    st.markdown("---")
    
    # ========================================
    # BARRA 3: COMPARATIVA OFFLINE VS ONLINE (SIEMPRE)
    # ========================================
    st.markdown('<div class="barra-header barra-comparativa">📊 COMPARATIVA: Offline vs Online</div>', unsafe_allow_html=True)
    
    mostrar_comparativa_offline_online(analisis, articulos, analisis_online, analisis_offline)
    
    st.markdown('</div>', unsafe_allow_html=True)


def mostrar_comparativa_offline_online(analisis: dict, articulos: list, analisis_online: dict = None, analisis_offline: dict = None):
    """Muestra la comparativa offline vs online con gráfico."""
    
    if analisis_online is None:
        articulos_online = [a for a in articulos if a.get('es_online', True)]
        precios_online = [a.get('precio_usd', 0) for a in articulos_online if a.get('precio_usd', 0) > 0]
        med_online = sorted(precios_online)[len(precios_online)//2] if precios_online else 0
        prod_online = len(articulos_online)
    else:
        med_online = analisis_online.get('precio_mediana', 0)
        prod_online = analisis_online.get('validos', 0)
    
    if analisis_offline is None:
        articulos_offline = [a for a in articulos if not a.get('es_online', True)]
        precios_offline = [a.get('precio_usd', 0) for a in articulos_offline if a.get('precio_usd', 0) > 0]
        med_offline = sorted(precios_offline)[len(precios_offline)//2] if precios_offline else 0
        prod_offline = len(articulos_offline)
    else:
        med_offline = analisis_offline.get('precio_mediana', 0)
        prod_offline = analisis_offline.get('validos', 0)
    
    # Métricas comparativas
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("💾 OFFLINE", f"${med_offline:.2f}", f"{prod_offline} productos")
    with col2: 
        st.metric("🌐 ONLINE", f"${med_online:.2f}", f"{prod_online} productos")
    with col3:
        if med_offline > 0 and med_online > 0:
            diff = med_online - med_offline
            pct = (diff / med_offline * 100) if med_offline > 0 else 0
            st.metric("📊 Diferencia", f"${diff:.2f}", f"{pct:+.1f}%")
        else:
            st.metric("📊 Diferencia", "N/A", "Sin comparación")
    
    # Gráfico de barras comparativo SIEMPRE visible
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=(f'💾 Offline ({prod_offline} productos)', f'🌐 Online ({prod_online} productos)')
    )
    
    # Valores para el gráfico (usar 0.01 como mínimo para mostrar barra)
    val_offline = med_offline if med_offline > 0 else 0.01
    val_online = med_online if med_online > 0 else 0.01
    
    # Barra Offline
    fig.add_trace(go.Bar(
        x=['Mediana'], 
        y=[val_offline], 
        marker_color='#007bff', 
        text=f'${med_offline:.2f}' if med_offline > 0 else 'Sin datos',
        textposition='outside',
        name='Offline'
    ), row=1, col=1)
    
    # Barra Online
    fig.add_trace(go.Bar(
        x=['Mediana'], 
        y=[val_online], 
        marker_color='#28a745', 
        text=f'${med_online:.2f}' if med_online > 0 else 'Sin datos',
        textposition='outside',
        name='Online'
    ), row=1, col=2)
    
    # Ajustar escala
    max_val = max(med_offline, med_online, 100) if max(med_offline, med_online) > 0 else 100
    fig.update_yaxes(range=[0, max_val * 1.4])
    fig.update_layout(
        height=350, 
        showlegend=False, 
        title_text="Comparativa Mediana de Precios", 
        title_x=0.5
    )
    st.plotly_chart(fig, use_container_width=True)


def mostrar_fuentes(analisis: dict):
    """Muestra la distribución por fuente."""
    fuentes = analisis.get('fuentes_encontradas', {})
    if not fuentes:
        st.info("📊 No hay información de fuentes disponible")
        return
    
    iconos = {'revolico': '🔵', 'voypati': '🟢', 'elyerromenu': '🟠', 'fadiar': '🟡', 'google': '🔍'}
    colores = {'revolico': '#1565C0', 'voypati': '#2E7D32', 'elyerromenu': '#E65100', 'fadiar': '#7B1FA2', 'google': '#9b59b6'}
    
    cols = st.columns(len(fuentes))
    for i, (fuente, count) in enumerate(fuentes.items()):
        with cols[i]:
            icono = iconos.get(fuente, '⚪')
            color = colores.get(fuente, '#666666')
            st.markdown(f"""
            <div style="background: {color}; padding: 1rem; border-radius: 0.5rem; text-align: center; color: white;">
                <span style="font-size: 1.5rem;">{icono}</span>
                <h4 style="margin: 0.3rem 0; color: white;">{fuente.title()}</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold;">{count}</p>
            </div>
            """, unsafe_allow_html=True)


def clasificar_productos(articulos: list, precio_promedio: float) -> dict:
    """Clasifica productos según su precio relativo al promedio."""
    if not articulos or precio_promedio <= 0:
        return {"nuevos": [], "de_uso": [], "umbral": 0}
    
    umbral = precio_promedio * 0.50
    nuevos, de_uso = [], []
    
    for art in articulos:
        precio = art.get('precio_usd', 0)
        if precio <= 1: continue
        
        art_c = art.copy()
        if precio < umbral:
            art_c['condicion'] = 'De uso'
            de_uso.append(art_c)
        else:
            art_c['condicion'] = 'Nuevo'
            nuevos.append(art_c)
    
    return {"nuevos": nuevos, "de_uso": de_uso, "umbral": round(umbral, 2)}


def mostrar_tabla_articulos(articulos: list, analisis: dict, precio_minimo_valido: float = 1.0):
    """Muestra la tabla de artículos."""
    df = pd.DataFrame(articulos)
    if df.empty:
        st.info("📋 No hay artículos para mostrar")
        return
    
    precio_prom = analisis.get('precio_promedio', 0)
    umbral = precio_prom * 0.50 if precio_prom > 0 else 0
    
    def get_condicion(row):
        if row.get('fuente') == 'google': return '🔍 Referencia'
        precio = row.get('precio_usd', 0)
        if precio <= 0: return '⏳ Sin precio'
        return '🔧 De uso' if precio < umbral else '🆕 Nuevo'
    
    df['condicion'] = df.apply(get_condicion, axis=1)
    df['porcentaje'] = df['precio_usd'].apply(lambda x: f"{(x/precio_prom*100):.0f}%" if x > 0 and precio_prom > 0 else "-")
    df['tipo'] = df['es_online'].apply(lambda x: '🌐 Online' if x else '💾 Offline')
    
    if 'fecha_extraccion' in df.columns and 'hora_extraccion' in df.columns:
        df['fecha_hora'] = df.apply(lambda x: f"{x['fecha_extraccion']} {str(x['hora_extraccion'])[:8]}" if pd.notna(x.get('fecha_extraccion')) else '', axis=1)
    
    columnas = ['titulo', 'descripcion', 'fecha_hora', 'tipo', 'condicion', 'fuente', 'precio_original', 'moneda_original', 'precio_usd', 'porcentaje', 'enlace']
    cols_reales = [c for c in columnas if c in df.columns]
    
    st.dataframe(
        df[cols_reales],
        column_config={
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "fecha_hora": st.column_config.TextColumn("Fecha/Hora", width="medium"),
            "tipo": st.column_config.TextColumn("Tipo", width="small"),
            "condicion": st.column_config.TextColumn("Condición", width="small"),
            "fuente": st.column_config.TextColumn("Fuente", width="small"),
            "precio_original": st.column_config.NumberColumn("Precio", format="%.2f"),
            "moneda_original": st.column_config.TextColumn("Moneda", width="small"),
            "precio_usd": st.column_config.NumberColumn("USD", format="$%.2f"),
            "porcentaje": st.column_config.TextColumn("% Prom", width="small"),
            "enlace": st.column_config.LinkColumn("Enlace", display_text="Ver 🔗")
        },
        hide_index=True, use_container_width=True, height=450
    )
