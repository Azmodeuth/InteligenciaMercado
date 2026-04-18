"""
================================================================================
OPERACIONES DE BASE DE DATOS - VERSIÓN COMPLETA CON FECHAS CORREGIDAS
================================================================================
"""
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from config.settings import DB_NAME, DB_TABLE, logger
from core.utils import obtener_hora, obtener_fecha

# ==============================================================================
# FUNCIONES DE UTILIDAD LOCAL
# ==============================================================================

def obtener_id_busqueda():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def obtener_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==============================================================================
# CREACIÓN Y MIGRACIÓN
# ==============================================================================

def crear_base_datos():
    """Crea la base de datos con todas las tablas y columnas necesarias."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Tabla principal
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_busqueda TEXT, producto_buscado TEXT NOT NULL, titulo TEXT NOT NULL,
            descripcion TEXT, precio_original REAL, moneda_original TEXT,
            moneda_normalizada TEXT, precio_usd REAL, enlace TEXT, imagen TEXT,
            fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP, hora_extraccion TEXT,
            fecha_busqueda TEXT, categoria TEXT DEFAULT 'general',
            subcategoria TEXT DEFAULT 'general', fuente TEXT DEFAULT 'revolico',
            tipo_busqueda TEXT DEFAULT 'profunda', es_online INTEGER DEFAULT 1,
            tipo_enlace TEXT DEFAULT 'directo',
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP, anuncio_id TEXT
        )
    """)
    
    # Migración de columnas - INCLUYE tipo_enlace
    cursor.execute(f"PRAGMA table_info({DB_TABLE})")
    columnas_existentes = {row[1] for row in cursor.fetchall()}
    columnas_nuevas = {
        'descripcion': 'TEXT', 
        'hora_extraccion': 'TEXT', 
        'fecha_busqueda': 'TEXT',
        'categoria': "TEXT DEFAULT 'general'", 
        'subcategoria': "TEXT DEFAULT 'general'",
        'fuente': "TEXT DEFAULT 'revolico'", 
        'tipo_busqueda': "TEXT DEFAULT 'profunda'",
        'es_online': 'INTEGER DEFAULT 1', 
        'moneda_normalizada': 'TEXT', 
        'anuncio_id': 'TEXT',
        'tipo_enlace': "TEXT DEFAULT 'directo'"
    }
    
    for columna, definicion in columnas_nuevas.items():
        if columna not in columnas_existentes:
            try:
                cursor.execute(f"ALTER TABLE {DB_TABLE} ADD COLUMN {columna} {definicion}")
                logger.info(f"✅ Columna agregada: {columna}")
            except Exception as e:
                logger.warning(f"⚠️ Columna {columna} ya existe o error: {e}")
    
    # Índices
    for idx, col in [("idx_id_busqueda","id_busqueda"),("idx_categoria","categoria"),
                     ("idx_producto","producto_buscado"),("idx_fecha","fecha_extraccion"),
                     ("idx_fecha_busqueda","fecha_busqueda"),("idx_fuente","fuente")]:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx} ON {DB_TABLE}({col})")
        except: pass
    
    # Tabla de historial
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_busquedas (
            id TEXT PRIMARY KEY, termino TEXT NOT NULL, categoria TEXT, subcategoria TEXT,
            tipo_busqueda TEXT DEFAULT 'profunda', total_resultados INTEGER DEFAULT 0,
            precio_minimo REAL, precio_maximo REAL, precio_promedio REAL, precio_mediana REAL,
            precio_mediana_offline REAL DEFAULT 0, precio_mediana_online REAL DEFAULT 0,
            productos_validos INTEGER, outliers INTEGER, fecha TEXT, hora TEXT,
            fuentes_encontradas TEXT,
            fecha_completa DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Índices para historial
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_busquedas(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_termino ON historial_busquedas(termino)")
    
    # Migración de columnas en historial_busquedas
    cursor.execute("PRAGMA table_info(historial_busquedas)")
    columnas_historial = {row[1] for row in cursor.fetchall()}
    if 'fuentes_encontradas' not in columnas_historial:
        try:
            cursor.execute("ALTER TABLE historial_busquedas ADD COLUMN fuentes_encontradas TEXT")
        except: pass
    
    # Tabla de fluctuación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fluctuacion_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, producto_buscado TEXT NOT NULL,
            categoria TEXT, subcategoria TEXT, precio_mediana REAL, precio_promedio REAL,
            precio_minimo REAL, precio_maximo REAL, total_productos INTEGER,
            fecha TEXT, hora TEXT, fuentes TEXT
        )
    """)
    
    # Índices para fluctuación
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fluctuacion_fecha ON fluctuacion_precios(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fluctuacion_producto ON fluctuacion_precios(producto_buscado)")
    
    conexion.commit()
    conexion.close()
    logger.info(f"💾 Base de datos lista: {DB_NAME}")

# ==============================================================================
# OPERACIONES CRUD
# ==============================================================================

def guardar_en_bd(articulos: list, tipo_busqueda: str = 'profunda') -> bool:
    """Guarda los artículos en la base de datos con ID de sesión unificado."""
    if not articulos:
        return False
    
    crear_base_datos()
    
    # Usar funciones de Python para fecha/hora
    fecha_actual = obtener_fecha()
    hora_actual = obtener_hora()
    
    # UNIFICACIÓN DE ID: Generamos un ID de lote para evitar que cambie durante el procesamiento de 1000+ items
    id_lote_unificado = obtener_id_busqueda()
    
    # Para guardado incremental, verificar duplicados
    if tipo_busqueda == 'incremental':
        conexion = sqlite3.connect(DB_NAME)
        try:
            cursor = conexion.cursor()
            # Obtener IDs ya existentes
            ids_existentes = set()
            anuncios_ids = [a.get('anuncio_id') for a in articulos if a.get('anuncio_id')]
            if anuncios_ids:
                placeholders = ','.join(['?' for _ in anuncios_ids])
                cursor.execute(f"SELECT DISTINCT anuncio_id FROM {DB_TABLE} WHERE anuncio_id IN ({placeholders})", anuncios_ids)
                ids_existentes = {row[0] for row in cursor.fetchall()}
            
            # Filtrar artículos ya existentes
            articulos = [a for a in articulos if a.get('anuncio_id') not in ids_existentes]
            
            if not articulos:
                logger.info(f"✅ Guardado incremental: todos los artículos ya existían")
                return True
        finally:
            conexion.close()
    
    # Normalizar artículos
    articulos_limpios = []
    for art in articulos:
        # Asegurar que descripción no esté vacía
        descripcion = art.get('descripcion', '')
        if not descripcion or descripcion.strip() == '':
            descripcion = art.get('titulo', 'Sin descripción')
        
        # PRIORIDAD DE ID: Si el artículo ya trae un ID de sesión lo respetamos, sino usamos el del lote
        id_final = art.get('id_busqueda') if art.get('id_busqueda') else id_lote_unificado

        art_limpio = {
            'id_busqueda': id_final,
            'producto_buscado': art.get('producto_buscado', 'desconocido'),
            'titulo': art.get('titulo', 'Sin título'),
            'descripcion': descripcion,
            'precio_original': art.get('precio_original', 0),
            'moneda_original': art.get('moneda_original', 'USD'),
            'moneda_normalizada': art.get('moneda_normalizada', 'USD'),
            'precio_usd': art.get('precio_usd', 0),
            'enlace': art.get('enlace', ''),
            'imagen': art.get('imagen', ''),
            'fecha_extraccion': art.get('fecha_extraccion', obtener_timestamp()),
            'hora_extraccion': art.get('hora_extraccion', hora_actual),
            'fecha_busqueda': art.get('fecha_busqueda', fecha_actual),
            'categoria': art.get('categoria', 'general'),
            'subcategoria': art.get('subcategoria', 'general'),
            'fuente': art.get('fuente', 'revolico'),
            'tipo_busqueda': tipo_busqueda if tipo_busqueda != 'incremental' else 'profunda',
            'es_online': 1 if art.get('es_online', True) else 0,
            'tipo_enlace': art.get('tipo_enlace', 'directo'),
            'anuncio_id': art.get('anuncio_id', '')
        }
        articulos_limpios.append(art_limpio)
    
    df = pd.DataFrame(articulos_limpios)
    conexion = sqlite3.connect(DB_NAME)
    try:
        df.to_sql(DB_TABLE, con=conexion, if_exists="append", index=False)
        logger.info(f"✅ {len(articulos_limpios)} artículos guardados bajo la sesión {id_lote_unificado}")
        return True
    except Exception as e:
        logger.error(f"❌ Error guardando: {e}")
        return False
    finally:
        conexion.close()

def guardar_historial_busqueda(id_busqueda: str, termino: str, categoria: str, subcategoria: str, 
                                tipo_busqueda: str, analisis: dict):
    """Guarda el historial de una búsqueda."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        cursor = conexion.cursor()
        # Usar funciones de Python para fecha/hora
        fecha_actual = obtener_fecha()
        hora_actual = obtener_hora()
        
        cursor.execute("""
            INSERT INTO historial_busquedas 
            (id, termino, categoria, subcategoria, tipo_busqueda, total_resultados,
             precio_minimo, precio_maximo, precio_promedio, precio_mediana,
             precio_mediana_offline, precio_mediana_online, productos_validos, outliers, 
             fecha, hora, fuentes_encontradas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_busqueda, termino, categoria, subcategoria, tipo_busqueda,
              analisis.get('total_extraidos', 0), analisis.get('precio_minimo', 0),
              analisis.get('precio_maximo', 0), analisis.get('precio_promedio', 0),
              analisis.get('precio_mediana', 0), analisis.get('precio_mediana_offline', 0),
              analisis.get('precio_mediana_online', 0), analisis.get('validos', 0), 
              analisis.get('outliers', 0),
              fecha_actual, hora_actual,
              json.dumps(analisis.get('fuentes_encontradas', {}))))
        conexion.commit()
        logger.info(f"📝 Historial guardado: {termino} - {fecha_actual}")
    except Exception as e:
        logger.error(f"Error guardando historial: {e}")
    finally:
        conexion.close()

def guardar_fluctuacion(termino: str, categoria: str, subcategoria: str, analisis: dict):
    """Guarda registro de fluctuación de precios."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        cursor = conexion.cursor()
        # Usar funciones de Python para fecha/hora
        fecha_actual = obtener_fecha()
        hora_actual = obtener_hora()
        
        cursor.execute("""
            INSERT INTO fluctuacion_precios
            (producto_buscado, categoria, subcategoria, precio_mediana, precio_promedio,
             precio_minimo, precio_maximo, total_productos, fecha, hora, fuentes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (termino, categoria, subcategoria, analisis.get('precio_mediana', 0),
              analisis.get('precio_promedio', 0), analisis.get('precio_minimo', 0),
              analisis.get('precio_maximo', 0), analisis.get('total_extraidos', 0),
              fecha_actual, hora_actual,
              json.dumps(analisis.get('fuentes_encontradas', {}))))
        conexion.commit()
    except Exception as e:
        logger.error(f"Error guardando fluctuación: {e}")
    finally:
        conexion.close()

# ==============================================================================
# CONSULTAS (MODIFICADO: AHORA BUSCA LA ÚLTIMA SESIÓN REAL PARA EVITAR DATOS VIEJOS)
# ==============================================================================

def buscar_en_bd_local(termino: str, categoria: str = None, subcategoria: str = None,
                       dias_maximos: int = 30) -> list:
    """Busca productos en la base de datos local priorizando la subcategoría para asegurar sesión completa."""
    if not (termino or subcategoria):
        return []

    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    
    try:
        cursor = conexion.cursor()
        
        # PASO 1: Encontrar el ID de búsqueda más reciente que coincida con la subcategoría o término.
        # Esto garantiza que la búsqueda rápida recupere TODO lo de la última búsqueda profunda.
        query_id = f"""
            SELECT id_busqueda FROM {DB_TABLE} 
            WHERE (subcategoria = ? OR producto_buscado LIKE ? OR titulo LIKE ?) 
            AND (categoria = ? OR ? IS NULL)
            ORDER BY fecha_extraccion DESC LIMIT 1
        """
        
        term_like = f"%{termino}%" if termino else "%"
        cursor.execute(query_id, (subcategoria, term_like, term_like, categoria, categoria))
        res = cursor.fetchone()
        
        if not res:
            # Intento de rescate: Buscar lo más reciente de la categoría general
            query_rescate = f"SELECT id_busqueda FROM {DB_TABLE} WHERE categoria = ? ORDER BY fecha_extraccion DESC LIMIT 1"
            cursor.execute(query_rescate, (categoria,))
            res = cursor.fetchone()
            
        if not res:
            return []
            
        ultimo_id = res[0]
        
        # PASO 2: Traer todos los productos que pertenecen a esa sesión exacta (sin perder ni uno)
        query = f"SELECT * FROM {DB_TABLE} WHERE id_busqueda = ?"
        df = pd.read_sql_query(query, conexion, params=[ultimo_id])
        
        if df.empty:
            return []
        
        articulos = df.to_dict('records')
        for art in articulos:
            art['es_online'] = False
        
        logger.info(f"✅ Recuperados {len(articulos)} anuncios de la sesión: {ultimo_id}")
        return articulos
    except Exception as e:
        logger.error(f"❌ Error en búsqueda local: {e}")
        return []
    finally:
        conexion.close()

def obtener_articulos_por_busqueda(id_busqueda: str) -> pd.DataFrame:
    """Obtiene los artículos de una búsqueda específica."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query(
            f"SELECT * FROM {DB_TABLE} WHERE id_busqueda = ? ORDER BY precio_usd", 
            conexion, params=[id_busqueda]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_articulos_por_termino_fecha(termino: str, fecha: str) -> pd.DataFrame:
    """Obtiene artículos por término y fecha."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query(
            f"""SELECT * FROM {DB_TABLE} 
                WHERE producto_buscado LIKE ? AND fecha_busqueda = ?
                ORDER BY precio_usd""",
            conexion, params=[f"%{termino}%", fecha]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_historial_por_fechas(dias: int = 30) -> pd.DataFrame:
    """Obtiene el historial de búsquedas organizadas por fecha."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        return pd.read_sql_query(
            "SELECT fecha, hora, termino, categoria, subcategoria, tipo_busqueda, total_resultados, precio_mediana FROM historial_busquedas WHERE fecha >= ? ORDER BY fecha DESC, hora DESC",
            conexion, params=[fecha_limite]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_fechas_con_busquedas() -> list:
    """Obtiene lista de fechas con búsquedas."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT DISTINCT fecha FROM historial_busquedas WHERE fecha IS NOT NULL ORDER BY fecha DESC")
        return [row[0] for row in cursor.fetchall()]
    except:
        return []
    finally:
        conexion.close()

def obtener_busquedas_por_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene búsquedas de una fecha específica."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query(
            "SELECT * FROM historial_busquedas WHERE fecha = ? ORDER BY hora DESC",
            conexion, params=[fecha]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_fluctuacion_historica(termino: str = None, dias: int = 30) -> pd.DataFrame:
    """Obtiene historial de fluctuación de precios."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        if termino:
            return pd.read_sql_query(
                "SELECT fecha, producto_buscado as termino, precio_mediana, precio_promedio, precio_minimo, precio_maximo FROM fluctuacion_precios WHERE producto_buscado LIKE ? AND fecha >= ? ORDER BY fecha DESC",
                conexion, params=[f"%{termino}%", fecha_limite]
            )
        return pd.read_sql_query(
            "SELECT fecha, producto_buscado as termino, precio_mediana, precio_promedio FROM fluctuacion_precios WHERE fecha >= ? ORDER BY fecha DESC",
            conexion, params=[fecha_limite]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_estadisticas_por_fecha(fecha: str) -> dict:
    """Obtiene estadísticas resumidas de una fecha específica."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_busquedas, SUM(total_resultados) as total_productos,
                   AVG(precio_mediana) as precio_mediana_dia, MIN(precio_minimo) as precio_minimo_dia,
                   MAX(precio_maximo) as precio_maximo_dia
            FROM historial_busquedas WHERE fecha = ?
        """, (fecha,))
        row = cursor.fetchone()
        if row:
            return {
                "fecha": fecha,
                "total_busquedas": row[0] or 0,
                "total_productos": row[1] or 0,
                "precio_mediana_dia": round(row[2], 2) if row[2] else 0,
                "precio_minimo_dia": round(row[3], 2) if row[3] else 0,
                "precio_maximo_dia": round(row[4], 2) if row[4] else 0
            }
        return {}
    except:
        return {}
    finally:
        conexion.close()

def obtener_todas_fechas_busquedas() -> list:
    """Obtiene TODAS las fechas con búsquedas de todas las tablas."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        fechas = set()
        for tabla, columna in [("historial_busquedas", "fecha"), ("fluctuacion_precios", "fecha"), (DB_TABLE, "fecha_busqueda")]:
            try:
                cursor = conexion.cursor()
                cursor.execute(f"SELECT DISTINCT {columna} FROM {tabla} WHERE {columna} IS NOT NULL")
                for row in cursor.fetchall():
                    if row[0]: fechas.add(row[0])
            except: pass
        return sorted(list(fechas), reverse=True)
    except:
        return []
    finally:
        conexion.close()

def obtener_busquedas_completas_por_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene búsquedas de múltiples tablas para una fecha específica."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        # Primero buscar en historial_busquedas
        df_historial = pd.read_sql_query(
            "SELECT id, termino, categoria, subcategoria, tipo_busqueda, total_resultados, precio_mediana, hora, fecha FROM historial_busquedas WHERE fecha = ? ORDER BY hora DESC",
            conexion, params=[fecha]
        )
        
        if not df_historial.empty:
            return df_historial
        
        # Si no hay en historial, buscar en anuncios directamente
        df_anuncios = pd.read_sql_query(
            f"""
            SELECT 
                id_busqueda as id, 
                producto_buscado as termino, 
                categoria, 
                subcategoria, 
                tipo_busqueda,
                COUNT(*) as total_resultados,
                AVG(precio_usd) as precio_mediana,
                hora_extraccion as hora,
                fecha_busqueda as fecha
            FROM {DB_TABLE} 
            WHERE fecha_busqueda = ?
            GROUP BY id_busqueda
            ORDER BY hora_extraccion DESC
            """,
            conexion, params=[fecha]
        )
        
        return df_anuncios
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_productos_por_fuente(termino: str = None, fecha: str = None) -> pd.DataFrame:
    """Obtiene conteo de productos por fuente."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        query = f"SELECT fuente, COUNT(*) as cantidad, AVG(precio_usd) as promedio FROM {DB_TABLE} WHERE 1=1"
        params = []
        
        if termino:
            query += " AND producto_buscado LIKE ?"
            params.append(f"%{termino}%")
        if fecha:
            query += " AND fecha_busqueda = ?"
            params.append(fecha)
        
        query += " GROUP BY fuente ORDER BY cantidad DESC"
        
        return pd.read_sql_query(query, conexion, params=params)
    except:
        return pd.DataFrame()
    finally:
        conexion.close()

def obtener_resumen_comparativo(termino: str) -> dict:
    """Obtiene resumen comparativo de un producto a través del tiempo."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query(
            """SELECT fecha, precio_mediana, precio_minimo, precio_maximo, total_productos, fuentes
               FROM fluctuacion_precios 
               WHERE producto_buscado LIKE ?
               ORDER BY fecha DESC LIMIT 10""",
            conexion, params=[f"%{termino}%"]
        )
        
        if df.empty:
            return {}
        
        return {
            'historial': df.to_dict('records'),
            'tendencia': 'subiendo' if len(df) > 1 and df.iloc[0]['precio_mediana'] > df.iloc[-1]['precio_mediana'] else 'bajando',
            'variacion': round(df.iloc[0]['precio_mediana'] - df.iloc[-1]['precio_mediana'], 2) if len(df) > 1 else 0
        }
    except:
        return {}
    finally:
        conexion.close()

def obtener_productos_por_fecha(fecha: str, limite: int = 100) -> pd.DataFrame:
    """Obtiene productos de una fecha específica directamente de anuncios."""
    crear_base_datos()
    conexion = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query(
            f"""
            SELECT titulo, descripcion, precio_usd, precio_original, moneda_original, 
                   fuente, enlace, hora_extraccion, categoria, subcategoria
            FROM {DB_TABLE} 
            WHERE fecha_busqueda = ?
            ORDER BY hora_extraccion DESC
            LIMIT ?
            """,
            conexion, params=[fecha, limite]
        )
    except:
        return pd.DataFrame()
    finally:
        conexion.close()