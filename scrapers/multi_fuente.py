"""
================================================================================
SCRAPERS MULTI-FUENTE PARA CUBA - VERSIÓN 8.3 (CORRECCIÓN DE ENLACES)
================================================================================
- Voypati (HTTPS Forzado)
- El Yerro (Corregido: Enlace directo a Producto /p/ en lugar de /b/)
- Fadiar (Timeout 60s)
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time
import warnings
import json

from config.settings import TASAS_DE_CAMBIO, logger

warnings.filterwarnings('ignore')

MAX_PRODUCTOS_POR_FUENTE = 1000
MAX_REINTENTOS = 3  
TIMEOUT_CORTO = 25  
TIMEOUT_LARGO = 60  

# ==============================================================================
# FUNCIONES DE UTILIDAD BASE
# ==============================================================================

def obtener_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_hora() -> str:
    return datetime.now().strftime("%H:%M:%S")

def obtener_fecha() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def obtener_id_busqueda() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def normalizar_moneda(moneda_raw) -> str:
    if moneda_raw is None:
        return "USD"
    moneda = str(moneda_raw).upper().strip()
    mapeo = {
        "USD": "USD", "US": "USD", "DOLAR": "USD", "$": "USD",
        "MLC": "MLC", "EUR": "EUR", "EURO": "EUR", "€": "EUR",
        "CUP": "CUP", "PESO": "CUP", "PESOS": "CUP", "MN": "CUP",
        "ZELLE": "USD",
    }
    return mapeo.get(moneda, "USD")

def convertir_a_usd(precio: float, moneda: str) -> float:
    moneda = normalizar_moneda(moneda)
    if moneda in ["USD", "MLC"]:
        return round(precio, 2)
    elif moneda == "EUR":
        return round(precio * TASAS_DE_CAMBIO.get("EUR", 1.1), 2)
    elif moneda == "CUP":
        return round(precio / TASAS_DE_CAMBIO.get("CUP", 120), 2)
    return round(precio, 2)

def limpiar_descripcion(desc: str, max_caracteres: int = 2000) -> str:
    if not desc:
        return ""
    desc = re.sub(r'<br\s*/?>', ' | ', str(desc))
    desc = re.sub(r'<[^>]+>', ' ', desc)
    desc = re.sub(r'[ \t]+', ' ', desc)
    desc = desc.strip()
    if len(desc) > max_caracteres:
        desc = desc[:max_caracteres]
    return desc

TERMINOS_RELACIONADOS = {
    "nevera":["nevera", "refrigerador", "frigorifico"],
    "televisor": ["televisor", "tv", "smart tv", "television"],
    "aire": ["aire acondicionado", "split", "minisplit"],
    "lavadora":["lavadora", "lavaseca"],
    "celular": ["celular", "telefono", "smartphone"],
    "laptop": ["laptop", "notebook", "computadora"],
}

def obtener_terminos_relacionados(termino: str) -> list:
    termino_lower = termino.lower()
    for clave, lista in TERMINOS_RELACIONADOS.items():
        if clave in termino_lower or termino_lower in clave:
            return lista[:3]
    return [termino]

def encontrar_lista_items(datos):
    if isinstance(datos, list): return datos
    if isinstance(datos, dict):
        for key in['data', 'items', 'results', 'products', 'list', 'inventory']:
            if key in datos and isinstance(datos[key], list): return datos[key]
        for k, v in datos.items():
            if isinstance(v, dict):
                for subkey in ['list', 'items', 'results', 'data', 'products']:
                    if subkey in v and isinstance(v[subkey], list): return v[subkey]
    return[]

def extraer_valor_recursivo(item, claves_posibles):
    if isinstance(item, dict):
        # Añadimos claves comunes de descripciones en APIs de e-commerce
        claves_extendidas = claves_posibles + ['body', 'content', 'summary', 'details', 'short_description', 'seo_description']
        for k in claves_extendidas:
            if k in item and item[k] and str(item[k]).strip() != "":
                return item[k]
        for v in item.values():
            res = extraer_valor_recursivo(v, claves_posibles)
            if res is not None: return res
    elif isinstance(item, list):
        for i in item:
            res = extraer_valor_recursivo(i, claves_posibles)
            if res is not None: return res
    return None
    if isinstance(item, dict):
        for k in claves_posibles:
            if k in item and item[k] is not None and str(item[k]).strip() != "":
                return item[k]
        for v in item.values():
            res = extraer_valor_recursivo(v, claves_posibles)
            if res is not None: return res
    elif isinstance(item, list):
        for i in item:
            res = extraer_valor_recursivo(i, claves_posibles)
            if res is not None: return res
    return None

def parsear_precio_seguro(precio_raw) -> float:
    if isinstance(precio_raw, (int, float)): return float(precio_raw)
    if isinstance(precio_raw, str):
        nums = re.findall(r'[\d.,]+', precio_raw)
        if nums:
            try: return float(nums[0].replace(',', '').strip())
            except: pass
    return 0.0

# ==============================================================================
# SCRAPERS
# ==============================================================================

class ScraperVoypati:
    BASE_URL = "https://voypati.com"
    def __init__(self):
        self.session = requests.Session()
    
    def obtener_productos(self, categoria=None, termino=None, exhaustivo=True) -> List[Dict]:
        productos =[]
        id_busqueda = obtener_id_busqueda()
        terminos = obtener_terminos_relacionados(termino) if termino else [""]
        print(f"\n📡 Voypati: '{termino}'")
        
        for t in terminos:
            if len(productos) >= MAX_PRODUCTOS_POR_FUENTE: break
            for pagina in range(1, 3):
                url = f"https://voypati.com/api/proxy?target=products&page={pagina}&page_size=100&search={t.replace(' ', '+')}"
                for intento in range(MAX_REINTENTOS):
                    try:
                        resp = self.session.get(url, impersonate="chrome", timeout=TIMEOUT_CORTO, verify=False)
                        if resp.status_code != 200: raise Exception(f"HTTP {resp.status_code}")
                        items = encontrar_lista_items(resp.json())
                        if not items: break
                        for item in items:
                            titulo = extraer_valor_recursivo(item, ['name', 'title'])
                            precio = parsear_precio_seguro(extraer_valor_recursivo(item, ['price', 'sellPrice']))
                            if not titulo or precio <= 0: continue
                            
                            item_id = extraer_valor_recursivo(item, ['id', 'uuid'])
                            # Enlace optimizado
                            enlace = f"{self.BASE_URL}/product/details/{item_id}?presale=false" if item_id else self.BASE_URL
                            
                            productos.append({
                                "id_busqueda": id_busqueda, "producto_buscado": termino, "titulo": titulo,
                                "descripcion": limpiar_descripcion(extraer_valor_recursivo(item, ['description']) or titulo),
                                "precio_original": precio, "moneda_original": "USD", "moneda_normalizada": "USD",
                                "precio_usd": precio, "enlace": enlace, "fecha_extraccion": obtener_timestamp(),
                                "hora_extraccion": obtener_hora(), "fecha_busqueda": obtener_fecha(),
                                "categoria": categoria or "general", "fuente": "voypati", "es_online": True
                            })
                        break
                    except: time.sleep(1)
        return productos

class ScraperElYerro:
    BASE_URL = "https://elyerromenu.com"
    def __init__(self):
        self.session = requests.Session()
    
    def obtener_productos(self, termino=None, categoria=None, exhaustivo=True) -> List[Dict]:
        productos =[]
        id_busqueda = obtener_id_busqueda()
        terminos = obtener_terminos_relacionados(termino) if exhaustivo else [termino]
        print(f"\n📡 El Yerro: '{termino}'")
        
        for t in terminos:
            for pagina in range(1, 3):
                url = f"{self.BASE_URL}/api/search/text/{t.replace(' ', '%20')}?page={pagina}"
                for intento in range(MAX_REINTENTOS):
                    try:
                        resp = self.session.get(url, impersonate="chrome", timeout=TIMEOUT_CORTO, verify=False)
                        items = encontrar_lista_items(resp.json())
                        if not items: break
                        for item in items:
                            titulo = extraer_valor_recursivo(item,['name', 'title'])
                            precio = parsear_precio_seguro(extraer_valor_recursivo(item, ['price', 'amount']))
                            if not titulo or precio <= 0: continue
                            
                            # CORRECCIÓN CLAVE: El path /p/ es para productos, /b/ era para bazares/tiendas
                            slug = extraer_valor_recursivo(item, ['slug', 'id'])
                            enlace = f"{self.BASE_URL}/p/{slug}" if slug else self.BASE_URL
                            
                            productos.append({
                                "id_busqueda": id_busqueda, "producto_buscado": termino, "titulo": titulo,
                                "descripcion": limpiar_descripcion(extraer_valor_recursivo(item, ['description']) or titulo),
                                "precio_original": precio, "moneda_original": "USD", "moneda_normalizada": "USD",
                                "precio_usd": precio, "enlace": enlace, "fecha_extraccion": obtener_timestamp(),
                                "hora_extraccion": obtener_hora(), "fecha_busqueda": obtener_fecha(),
                                "categoria": categoria or "general", "fuente": "elyerromenu", "es_online": True
                            })
                        break
                    except: time.sleep(1)
        return productos

class ScraperFadiar:
    API_URL = "https://app.fadiar.com/api/inventory"
    def __init__(self):
        self.session = requests.Session()
    
    def obtener_productos(self, termino: str, categoria=None, exhaustivo=True) -> List[Dict]:
        productos =[]
        id_busqueda = obtener_id_busqueda()
        print(f"\n📡 Fadiar: '{termino}'")
        for intento in range(MAX_REINTENTOS):
            try:
                resp = self.session.get(self.API_URL, impersonate="chrome", timeout=TIMEOUT_LARGO, verify=False)
                items = resp.json().get('products',[])
                terminos = obtener_terminos_relacionados(termino)
                for item in items:
                    titulo = item.get('name', '')
                    if not any(t.lower() in titulo.lower() for t in terminos): continue
                    
                    precios = item.get('prices', [[]])[0]
                    if len(precios) < 2: continue
                    precio = float(precios[1])
                    if precio <= 0: continue
                    
                    productos.append({
                        "id_busqueda": id_busqueda, "producto_buscado": termino, "titulo": titulo,
                        "descripcion": limpiar_descripcion(item.get('description') or titulo),
                        "precio_original": precio, "moneda_original": "USD", "moneda_normalizada": "USD",
                        "precio_usd": precio, "enlace": "https://fadiar.com/products/",
                        "fecha_extraccion": obtener_timestamp(), "hora_extraccion": obtener_hora(),
                        "fecha_busqueda": obtener_fecha(), "categoria": categoria or "general",
                        "fuente": "fadiar", "es_online": True
                    })
                break
            except: time.sleep(2)
        return productos

class AgregadorMultiFuente:
    def __init__(self):
        self.voypati = ScraperVoypati()
        self.elyerro = ScraperElYerro()
        self.fadiar = ScraperFadiar()
    
    def buscar_todos(self, termino, categoria=None, exhaustivo=True) -> Dict[str, List[Dict]]:
        resultados = {"voypati": [], "elyerromenu": [], "fadiar": []}
        try: resultados["voypati"] = self.voypati.obtener_productos(categoria, termino, exhaustivo)
        except: pass
        try: resultados["elyerromenu"] = self.elyerro.obtener_productos(termino, categoria, exhaustivo)
        except: pass
        try: resultados["fadiar"] = self.fadiar.obtener_productos(termino, categoria, exhaustivo)
        except: pass
        return resultados
    
    def consolidar_resultados(self, resultados: Dict[str, List[Dict]]) -> List[Dict]:
        todos, vistos = [], set()
        for items in resultados.values():
            for item in items:
                key = (item.get('titulo', '')[:50].lower(), item.get('precio_usd', 0))
                if key not in vistos:
                    vistos.add(key)
                    todos.append(item)
        return todos