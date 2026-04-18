"""
================================================================================
REVOLICO PRICE INTELLIGENCE - DASHBOARD PRINCIPAL V3.5
================================================================================
Dashboard con:
- Soporte completo de monedas (CUP, MLC, EUR, USD)
- Búsquedas independientes (sin solapar)
- Configuración de tasas de cambio
- Históricos de búsquedas
- Búsquedas por día
- Fluctuación de precios
- Multi-fuente (Revolico, Voypati, ElYerro, Fadiar, Porlalivre)
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

import app
from database.db import (
    crear_base_datos, obtener_historial_por_fechas, obtener_fechas_con_busquedas,
    obtener_busquedas_por_fecha, obtener_fluctuacion_historica,
    obtener_todas_fechas_busquedas, obtener_busquedas_completas_por_fecha,
    obtener_estadisticas_por_fecha
)

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(
    page_title="Inteligencia de Mercado - Revolico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .category-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
    .day-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    .day-card:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar BD
crear_base_datos()

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.header("🔍 Búsqueda Rápida")
    
    nuevo_producto = st.text_input(
        "Buscar producto",
        placeholder="Ej. nevera, iPhone, moto..."
    )
    
    # Selector de categoría
    categoria_rapida = st.selectbox(
        "Categoría",
        [""] + list(app.CATEGORIAS.keys()),
        format_func=lambda x: "Todas" if x == "" else f"{app.CATEGORIAS[x]['icono']} {app.CATEGORIAS[x]['nombre']}"
    )
    
    # Configuración de tasas
    with st.expander("💱 Tasas de Cambio", expanded=False):
        st.markdown("**Configura las tasas actuales:**")
        
        tasa_cup = st.number_input(
            "CUP → USD",
            min_value=100.0,
            max_value=500.0,
            value=float(app.TASAS_DE_CAMBIO["CUP"]),
            step=5.0
        )
        tasa_mlc = st.number_input(
            "MLC → USD",
            min_value=0.5,
            max_value=2.0,
            value=float(app.TASAS_DE_CAMBIO["MLC"]),
            step=0.1
        )
        tasa_eur = st.number_input(
            "EUR → USD",
            min_value=0.8,
            max_value=1.5,
            value=float(app.TASAS_DE_CAMBIO["EUR"]),
            step=0.05
        )
        
        if st.button("Actualizar Tasas"):
            app.actualizar_tasas_cambio(cup=tasa_cup, mlc=tasa_mlc, eur=tasa_eur)
            st.success("✅ Tasas actualizadas")
    
    # Botón de búsqueda
    if st.button("🚀 Extraer y Analizar", type="primary", use_container_width=True):
        if nuevo_producto:
            with st.spinner(f"Buscando '{nuevo_producto}' en múltiples fuentes..."):
                cat = categoria_rapida if categoria_rapida else None
                articulos = app.obtener_precios_revolico(
                    producto_original=nuevo_producto,
                    categoria=cat
                )
                if articulos:
                    app.analizar_mercado(articulos, cat)
                    st.success(f"✅ {len(articulos)} anuncios procesados")
                    st.rerun()
                else:
                    st.error("No se encontraron resultados")
        else:
            st.warning("Escribe un producto")
    
    st.markdown("---")
    
    # Estadísticas
    st.header("📈 Estadísticas")
    try:
        conexion = sqlite3.connect(app.DB_NAME)
        total = pd.read_sql_query("SELECT COUNT(*) as n FROM anuncios_revolico", conexion)['n'][0]
        productos = pd.read_sql_query("SELECT COUNT(DISTINCT producto_buscado) as n FROM anuncios_revolico", conexion)['n'][0]
        busquedas = pd.read_sql_query("SELECT COUNT(*) as n FROM historial_busquedas", conexion)['n'][0]
        
        # Conteo por fuente
        fuentes_df = pd.read_sql_query("""
            SELECT fuente, COUNT(*) as cantidad 
            FROM anuncios_revolico 
            WHERE fuente IS NOT NULL 
            GROUP BY fuente 
            ORDER BY cantidad DESC
        """, conexion)
        conexion.close()
        
        st.metric("Total Anuncios", total)
        st.metric("Productos", productos)
        st.metric("Búsquedas", busquedas)
        
        if not fuentes_df.empty:
            st.markdown("**📦 Por Fuente:**")
            for _, row in fuentes_df.iterrows():
                st.caption(f"• {row['fuente']}: {row['cantidad']}")
                
    except:
        st.info("Iniciando sistema...")
    
    # Tasas actuales
    st.markdown("---")
    st.markdown("**💱 Tasas Actuales:**")
    st.caption(f"• 1 USD = {app.TASAS_DE_CAMBIO['CUP']:.0f} CUP")
    st.caption(f"• 1 MLC = {app.TASAS_DE_CAMBIO['MLC']:.2f} USD")
    st.caption(f"• 1 EUR = {app.TASAS_DE_CAMBIO['EUR']:.2f} USD")

# ==============================================================================
# CONTENIDO PRINCIPAL
# ==============================================================================
st.markdown('<h1 class="main-header">📊 Panel de Inteligencia de Mercado</h1>', 
            unsafe_allow_html=True)
st.markdown("**Sistema de análisis de precios para el mercado cubano**")
st.markdown("*Soporta: USD, MLC, EUR, CUP - Todo convertido automáticamente a USD*")
st.markdown("*Fuentes: Revolico, Voypati, ElYerro, Fadiar, Porlalivre*")
st.markdown("---")

# ==============================================================================
# TARJETAS DE CATEGORÍAS
# ==============================================================================
st.markdown("### 📂 Categorías Disponibles")

cols = st.columns(4)

for i, (cat_key, cat_data) in enumerate(app.CATEGORIAS.items()):
    with cols[i % 4]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.2rem; border-radius: 0.8rem; color: white; text-align: center;
                    margin-bottom: 1rem;">
            <h2 style="margin:0; color:white;">{cat_data['icono']}</h2>
            <h4 style="margin:0.5rem 0 0 0; color:white;">{cat_data['nombre']}</h4>
            <p style="margin:0.3rem 0 0 0; font-size:0.8rem; opacity:0.8;">
                {len(cat_data['subcategorias'])} subcategorías
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# TABS: ÚLTIMAS BÚSQUEDAS | POR DÍA | HISTÓRICOS | FLUCTUACIÓN
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Últimas Búsquedas", 
    "📅 Búsquedas por Día", 
    "📊 Histórico Completo",
    "📈 Fluctuación de Precios"
])

# ==============================================================================
# TAB 1: ÚLTIMAS BÚSQUEDAS
# ==============================================================================
with tab1:
    st.markdown("### 🔍 Últimas Búsquedas Realizadas")
    
    try:
        conexion = sqlite3.connect(app.DB_NAME)
        df_busquedas = pd.read_sql_query("""
            SELECT 
                id as ID,
                termino as Producto,
                categoria as Categoría,
                subcategoria as Subcategoría,
                total_resultados as Anuncios,
                precio_mediana as Mediana,
                precio_minimo as Mínimo,
                precio_maximo as Máximo,
                fecha as Fecha,
                hora as Hora
            FROM historial_busquedas
            ORDER BY fecha DESC, hora DESC
            LIMIT 15
        """, conexion)
        conexion.close()
        
        if not df_busquedas.empty:
            # Formatear columnas
            for col in ['Mediana', 'Mínimo', 'Máximo']:
                df_busquedas[col] = df_busquedas[col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
            
            st.dataframe(
                df_busquedas,
                hide_index=True,
                use_container_width=True
            )
            
            st.info("💡 Cada fila representa una búsqueda independiente. Los resultados no se mezclan.")
        else:
            st.info("¡Realiza tu primera búsqueda para ver los resultados aquí!")
            
    except Exception as e:
        st.info("Base de datos vacía. ¡Realiza tu primera búsqueda!")

# ==============================================================================
# TAB 2: BÚSQUEDAS POR DÍA
# ==============================================================================
with tab2:
    st.markdown("### 📅 Búsquedas por Día")
    
    # Obtener fechas con búsquedas
    fechas = obtener_todas_fechas_busquedas()
    
    if fechas:
        # Selector de fecha
        col_fecha, col_info = st.columns([1, 2])
        
        with col_fecha:
            fecha_seleccionada = st.selectbox(
                "Selecciona una fecha:",
                options=fechas,
                format_func=lambda x: datetime.strptime(x, '%Y-%m-%d').strftime('%A %d de %B, %Y') if '-' in str(x) else str(x)
            )
        
        if fecha_seleccionada:
            # Estadísticas del día
            stats = obtener_estadisticas_por_fecha(fecha_seleccionada)
            
            if stats:
                with col_info:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Búsquedas", stats.get('total_busquedas', 0))
                    with col2:
                        st.metric("Productos", stats.get('total_productos', 0))
                    with col3:
                        st.metric("Precio Mediana", f"${stats.get('precio_mediana_dia', 0):.2f}")
                    with col4:
                        st.metric("Rango", f"${stats.get('precio_minimo_dia', 0):.0f} - ${stats.get('precio_maximo_dia', 0):.0f}")
            
            # Detalle de búsquedas del día
            st.markdown("#### Detalle de búsquedas:")
            df_dia = obtener_busquedas_completas_por_fecha(fecha_seleccionada)
            
            if not df_dia.empty:
                st.dataframe(
                    df_dia[['termino', 'categoria', 'subcategoria', 'tipo_busqueda', 'total_resultados', 'precio_mediana', 'hora']],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        'termino': 'Producto',
                        'categoria': 'Categoría',
                        'subcategoria': 'Subcategoría',
                        'tipo_busqueda': 'Tipo',
                        'total_resultados': 'Resultados',
                        'precio_mediana': st.column_config.NumberColumn('Precio Mediana', format='$%.2f'),
                        'hora': 'Hora'
                    }
                )
            else:
                st.info("No hay búsquedas en esta fecha.")
        
        # Resumen de actividad
        st.markdown("---")
        st.markdown("#### 📊 Resumen de Actividad por Día")
        
        df_resumen = pd.DataFrame({
            'fecha': fechas[:10],  # Últimos 10 días con actividad
        })
        
        # Obtener conteo por fecha
        conteos = []
        conexion = sqlite3.connect(app.DB_NAME)
        for f in fechas[:10]:
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM historial_busquedas WHERE fecha = ?", (f,))
                conteos.append(cursor.fetchone()[0])
            except:
                conteos.append(0)
        conexion.close()
        
        df_resumen['busquedas'] = conteos
        
        fig_actividad = px.bar(
            df_resumen, 
            x='fecha', 
            y='busquedas',
            title="Actividad de Búsquedas por Día",
            labels={'fecha': 'Fecha', 'busquedas': 'Número de Búsquedas'},
            color='busquedas',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_actividad, use_container_width=True)
        
    else:
        st.info("No hay búsquedas registradas aún. ¡Realiza tu primera búsqueda!")

# ==============================================================================
# TAB 3: HISTÓRICO COMPLETO
# ==============================================================================
with tab3:
    st.markdown("### 📊 Historial Completo de Búsquedas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        termino_filtro = st.text_input("Filtrar por producto:", placeholder="Ej. nevera, televisor...")
    
    with col2:
        conexion = sqlite3.connect(app.DB_NAME)
        categorias_disp = pd.read_sql_query("SELECT DISTINCT categoria FROM historial_busquedas WHERE categoria IS NOT NULL", conexion)
        conexion.close()
        cat_lista = ["Todas"] + categorias_disp['categoria'].tolist() if not categorias_disp.empty else ["Todas"]
        categoria_filtro = st.selectbox("Categoría:", cat_lista)
    
    with col3:
        dias_filtro = st.slider("Últimos días:", min_value=1, max_value=90, value=30)
    
    # Construir query
    conexion = sqlite3.connect(app.DB_NAME)
    
    query = """
        SELECT 
            fecha as Fecha,
            hora as Hora,
            termino as Producto,
            categoria as Categoría,
            subcategoria as Subcategoría,
            tipo_busqueda as Tipo,
            total_resultados as Resultados,
            precio_mediana as Mediana,
            precio_minimo as Mínimo,
            precio_maximo as Máximo,
            productos_validos as Válidos,
            outliers as Outliers
        FROM historial_busquedas
        WHERE 1=1
    """
    params = []
    
    if termino_filtro:
        query += " AND termino LIKE ?"
        params.append(f"%{termino_filtro}%")
    
    if categoria_filtro != "Todas":
        query += " AND categoria = ?"
        params.append(categoria_filtro)
    
    fecha_limite = (datetime.now() - timedelta(days=dias_filtro)).strftime('%Y-%m-%d')
    query += f" AND fecha >= '{fecha_limite}'"
    
    query += " ORDER BY fecha DESC, hora DESC"
    
    df_historial = pd.read_sql_query(query, conexion, params=params)
    conexion.close()
    
    if not df_historial.empty:
        # Formatear columnas de precio
        for col in ['Mediana', 'Mínimo', 'Máximo']:
            df_historial[col] = df_historial[col].apply(lambda x: f"${x:.2f}" if pd.notna(x) and x > 0 else "N/A")
        
        st.dataframe(df_historial, hide_index=True, use_container_width=True)
        
        # Estadísticas del filtro
        st.markdown("#### 📈 Estadísticas del Período")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Búsquedas", len(df_historial))
        with col2:
            st.metric("Productos Únicos", df_historial['Producto'].nunique())
        with col3:
            st.metric("Período", f"Últimos {dias_filtro} días")
    else:
        st.info("No hay resultados para los filtros seleccionados.")

# ==============================================================================
# TAB 4: FLUCTUACIÓN DE PRECIOS
# ==============================================================================
with tab4:
    st.markdown("### 📈 Fluctuación de Precios en el Tiempo")
    
    # Selector de producto
    conexion = sqlite3.connect(app.DB_NAME)
    productos_populares = pd.read_sql_query("""
        SELECT producto_buscado, COUNT(*) as veces
        FROM fluctuacion_precios
        GROUP BY producto_buscado
        ORDER BY veces DESC
        LIMIT 20
    """, conexion)
    conexion.close()
    
    if not productos_populares.empty:
        producto_seleccionado = st.selectbox(
            "Selecciona un producto para ver su historial de precios:",
            productos_populares['producto_buscado'].tolist()
        )
        
        if producto_seleccionado:
            df_fluctuacion = obtener_fluctuacion_historica(producto_seleccionado, dias=90)
            
            if not df_fluctuacion.empty:
                # Gráfico de evolución
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_fluctuacion['fecha'],
                    y=df_fluctuacion['precio_mediana'],
                    mode='lines+markers',
                    name='Precio Mediana',
                    line=dict(color='#1E88E5', width=2),
                    marker=dict(size=8)
                ))
                
                # Banda de precios
                fig.add_trace(go.Scatter(
                    x=df_fluctuacion['fecha'].tolist() + df_fluctuacion['fecha'].tolist()[::-1],
                    y=df_fluctuacion['precio_maximo'].tolist() + df_fluctuacion['precio_minimo'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(30, 136, 229, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    showlegend=True,
                    name='Rango (Min-Max)'
                ))
                
                fig.update_layout(
                    title=f"Evolución de Precios: {producto_seleccionado}",
                    xaxis_title="Fecha",
                    yaxis_title="Precio (USD)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla de datos
                st.markdown("#### Datos Detallados")
                df_fluctuacion['precio_mediana'] = df_fluctuacion['precio_mediana'].apply(lambda x: f"${x:.2f}")
                df_fluctuacion['precio_promedio'] = df_fluctuacion['precio_promedio'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                df_fluctuacion['precio_minimo'] = df_fluctuacion['precio_minimo'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                df_fluctuacion['precio_maximo'] = df_fluctuacion['precio_maximo'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                
                df_fluctuacion.columns = ['Fecha', 'Producto', 'Mediana', 'Promedio', 'Mínimo', 'Máximo']
                st.dataframe(df_fluctuacion, hide_index=True, use_container_width=True)
                
            else:
                st.info("No hay suficientes datos históricos para este producto.")
        
        # Top productos con más variación
        st.markdown("---")
        st.markdown("#### 📊 Productos con Mayor Variación de Precio")
        
        conexion = sqlite3.connect(app.DB_NAME)
        df_variacion = pd.read_sql_query("""
            SELECT 
                producto_buscado as Producto,
                COUNT(*) as Registros,
                AVG(precio_mediana) as Promedio,
                MIN(precio_mediana) as Mínimo,
                MAX(precio_mediana) as Máximo,
                (MAX(precio_mediana) - MIN(precio_mediana)) as Variación
            FROM fluctuacion_precios
            GROUP BY producto_buscado
            HAVING COUNT(*) > 1
            ORDER BY Variación DESC
            LIMIT 10
        """, conexion)
        conexion.close()
        
        if not df_variacion.empty:
            for col in ['Promedio', 'Mínimo', 'Máximo', 'Variación']:
                df_variacion[col] = df_variacion[col].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(df_variacion, hide_index=True, use_container_width=True)
    else:
        st.info("No hay datos de fluctuación aún. Realiza búsquedas del mismo producto en diferentes días.")

st.markdown("---")

# ==============================================================================
# DISTRIBUCIÓN POR MONEDAS Y FUENTES
# ==============================================================================
st.markdown("### 💱 Distribución por Moneda y Fuente")

col_moneda, col_fuente = st.columns(2)

with col_moneda:
    try:
        conexion = sqlite3.connect(app.DB_NAME)
        df_monedas = pd.read_sql_query("""
            SELECT 
                moneda_normalizada as Moneda,
                COUNT(*) as Cantidad,
                AVG(precio_usd) as Promedio_USD
            FROM anuncios_revolico
            WHERE moneda_normalizada IS NOT NULL
            GROUP BY moneda_normalizada
            ORDER BY Cantidad DESC
        """, conexion)
        conexion.close()
        
        if not df_monedas.empty:
            fig_pie = px.pie(
                df_monedas, 
                values='Cantidad', 
                names='Moneda',
                title="Anuncios por Moneda",
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos de monedas aún")
    except:
        st.info("Sin datos disponibles")

with col_fuente:
    try:
        conexion = sqlite3.connect(app.DB_NAME)
        df_fuentes = pd.read_sql_query("""
            SELECT 
                fuente as Fuente,
                COUNT(*) as Cantidad,
                AVG(precio_usd) as Promedio_USD
            FROM anuncios_revolico
            WHERE fuente IS NOT NULL
            GROUP BY fuente
            ORDER BY Cantidad DESC
        """, conexion)
        conexion.close()
        
        if not df_fuentes.empty:
            fig_bar = px.bar(
                df_fuentes,
                x='Fuente',
                y='Cantidad',
                title="Anuncios por Fuente",
                color='Fuente',
                text='Cantidad'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos de fuentes aún")
    except:
        st.info("Sin datos disponibles")

st.markdown("---")

# ==============================================================================
# INFORMACIÓN ADICIONAL
# ==============================================================================
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.markdown("""
    ### 📌 Cómo usar
    
    1. **Búsqueda rápida**: Usa el sidebar izquierdo
    2. **Por categoría**: Haz clic en una página de categoría
    3. **Por día**: Ve a la pestaña "Búsquedas por Día"
    4. **Histórico**: Filtra por producto y fecha
    """)

with col_info2:
    st.markdown("""
    ### 💱 Monedas Soportadas
    
    - **USD**: Dólar estadounidense (base)
    - **MLC**: Moneda libremente convertible
    - **EUR**: Euro
    - **CUP**: Peso cubano
    
    *Todo se convierte automáticamente a USD*
    """)

with col_info3:
    st.markdown("""
    ### 🌐 Fuentes de Datos
    
    - **Revolico**: API GraphQL
    - **Voypati**: API Proxy
    - **El Yerro**: API Search
    - **Fadiar**: Inventario
    - **Porlalivre**: HTML Scraping
    
    *Búsqueda exhaustiva con términos relacionadosd*
    """)
