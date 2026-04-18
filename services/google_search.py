"""
================================================================================
BÚSQUEDA WEB - VERSIÓN V7.10 - SCRAPER NATIVO (REPARADO Y COMPLETO) 
================================================================================
- MANTIENE TODAS LAS LISTAS ORIGINALES (SITIOS_CUBANOS, SITIOS_BAJA_CALIDAD)
- Corregido SyntaxError en el filtro de palabras de venta
- Calentamiento de sesión para Bing en servidores AWS/Streamlit
"""
import subprocess
import json
import logging
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests
from typing import List, Dict, Optional
from datetime import datetime
import re
import shutil
import time
import random

logger = logging.getLogger(__name__)

# Sitios de clasificados cubanos para priorizar
SITIOS_CUBANOS =[
    'voypati.com', 'elyerromenu.com', 'fadiar.com', 
    'porlalivre.com', '1cuc.com', 'cubisima.com', 'baches.com',
    'merolico.com', 'timbirichi.com', 'ringcompra.com', 'tulibreta.com',
    'babalarket.com', 'ktienda.com', 'cubarush.com', 'ofertas.cu',
    'revolucionycuba.com', 'compraenvio.com', 'cubashopping.com',
    'bachecubano.com', 'porlamer.es', 'reventadecuba.com'
]

SITIOS_EXCLUIDOS =['revolico.com', 'www.revolico.com', 'revo']

SITIOS_BAJA_CALIDAD =[
    'spanishdict.com', 'dictionary.com', 'wordreference.com', 'linguee.com',
    'translate.google.com', 'deepl.com', 'reverso.net', 'wikipedia.org',
    'pinterest.com/pin/', 'instagram.com/p/', 'tiktok.com/', 
    'facebook.com/posts', 'medium.com', 'quora.com', 'reddit.com/r/',
    'amazon.com', 'play.google.com'
]

PALABRAS_NO_VENTA =[
    'translate', 'translation', 'dictionary', 'definition', 'meaning',
    'what is', 'how to', 'tutorial', 'guide', 'learn', 'course',
    'wikipedia', 'encyclopedia', 'wiki', 'about', 'history of'
]

PALABRAS_VENTA =[
    'precio', 'price', 'comprar', 'buy', 'venta', 'sale', 'sell',
    'oferta', 'offer', 'descuento', 'usd', 'mlc', 'cup',
    'envío', 'disponible', 'nuevo', 'usado', 'garantía',
    'tienda', 'clasificado', 'anuncio', 'producto', 'modelo',
    'vendo', 'se vende', 'en venta', 'whatsapp'
]

def es_resultado_de_venta(titulo: str, descripcion: str, dominio: str) -> tuple:
    """Analiza si un resultado de búsqueda realmente parece una oferta de venta."""
    texto_combinado = f"{titulo} {descripcion}".lower()
    dominio_lower = dominio.lower()
    
    for sitio_bajo in SITIOS_BAJA_CALIDAD:
        if sitio_bajo in dominio_lower:
            return (False, f"Sitio no comercial: {sitio_bajo}")
            
    for palabra in PALABRAS_NO_VENTA:
        if palabra in texto_combinado:
            tiene_venta = any(pv in texto_combinado for pv in PALABRAS_VENTA)
            if not tiene_venta:
                return (False, f"No es venta: '{palabra}'")
                
    for sitio in SITIOS_CUBANOS:
        if sitio in dominio_lower: return (True, "Sitio clasificado")
        
    # LÍNEA CORREGIDA (Sin error de sintaxis)
    palabras_venta_encontradas = [pv for pv in PALABRAS_VENTA if pv in texto_combinado]
    if len(palabras_venta_encontradas) >= 2: return (True, "Múltiples palabras venta")
    
    if re.search(r'\$[\d,.]+|\d+[\d,.]*\s*(?:usd|mlc|cup|eur)', texto_combinado, re.I):
        return (True, "Contiene precio textual")
        
    if re.search(r'(se vende|en venta|for sale|vendo)', texto_combinado, re.I):
        return (True, "Indica venta directa")
        
    return (False, "Sin indicadores claros")

def _scraper_nativo_bing(termino: str, num_resultados: int) -> List[Dict]:
    """Scraper Directo a Bing HTML optimizado para saltar bloqueos en nube."""
    logger.info("📡 Ejecutando Scraper HTML Nativo Bing (Bypass Nube)")
    resultados =[]
    urls_vistas = set()
    
    headers_bing = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.bing.com/",
        "Connection": "keep-alive"
    }

    terminos_busqueda =[
        f"{termino} Cuba precio venta",
        f"{termino} comprar se vende site:voypati.com OR site:elyerromenu.com"
    ]
    
    with crequests.Session() as session:
        # Calentamiento Bing
        try:
            session.get("https://www.bing.com/", headers=headers_bing, impersonate="chrome120", timeout=15)
            time.sleep(2.0)
        except: pass

        for term in terminos_busqueda:
            for intento in range(2): 
                try:
                    url = f"https://www.bing.com/search?q={urllib.parse.quote(term)}"
                    r = session.get(url, headers=headers_bing, impersonate="chrome120", timeout=45)
                    
                    if r.status_code != 200:
                        continue

                    soup = BeautifulSoup(r.text, 'html.parser')
                    for li in soup.find_all('li', class_='b_algo'):
                        h2 = li.find('h2')
                        if not h2: continue
                        a = h2.find('a')
                        if not a: continue
                        
                        link = a.get('href', '')
                        titulo = a.get_text(strip=True)
                        p = li.find('p')
                        descripcion = p.get_text(strip=True) if p else ""
                        
                        if link and link not in urls_vistas:
                            try: dominio = urllib.parse.urlparse(link).netloc.lower()
                            except: dominio = ""
                            if any(exc in dominio or exc in link.lower() for exc in SITIOS_EXCLUIDOS): continue
                            
                            es_venta, motivo = es_resultado_de_venta(titulo, descripcion, dominio)
                            if es_venta:
                                urls_vistas.add(link)
                                es_cubano = any(site in dominio for site in SITIOS_CUBANOS)
                                resultados.append({
                                    "titulo": titulo, "url": link, "descripcion": descripcion,
                                    "dominio": dominio, "fecha": "", "es_cubano": es_cubano,
                                    "prioridad": 3 if es_cubano else 2
                                })
                    break 
                except Exception:
                    time.sleep(random.uniform(2.0, 4.0))
            
    return resultados

def buscar_en_google(termino: str, num_resultados: int = 15) -> List[Dict]:
    """Busca en Google/Bing SOLO productos de venta en Cuba."""
    num_resultados = max(num_resultados, 10)
    todos_resultados =[]
    urls_vistas = set()
    
    if shutil.which('z-ai'):
        try:
            cmd =["z-ai", "function", "-n", "web_search", "-a", json.dumps({"query": f"{termino} Cuba venta precio", "num": 15})]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                for item in data:
                    url = item.get("url", "")
                    if url and url not in urls_vistas:
                        urls_vistas.add(url)
                        todos_resultados.append({
                            "titulo": item.get("name", ""),
                            "url": url,
                            "descripcion": item.get("snippet", ""),
                            "dominio": item.get("host_name", "").lower(),
                            "prioridad": 2
                        })
        except Exception: pass
            
    if not todos_resultados:
        todos_resultados = _scraper_nativo_bing(termino, num_resultados)
        
    todos_resultados.sort(key=lambda x: x.get('prioridad', 0), reverse=True)
    return todos_resultados[:max(num_resultados, 10)]

def buscar_google_directo(termino: str, num_resultados: int = 15) -> List[Dict]:
    return buscar_en_google(termino, num_resultados)

def convertir_google_a_articulo(resultado: dict, termino: str, categoria: str = "electrodomesticos") -> dict:
    descripcion = resultado.get("descripcion", "")
    titulo = resultado.get("titulo", "Sin título")
    dominio = resultado.get("dominio", "")
    if not descripcion: descripcion = f"{titulo} - Fuente: {dominio}" if dominio else titulo
    elif dominio: descripcion = f"{descripcion} | Fuente: {dominio}"
    
    return {
        "id_busqueda": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "producto_buscado": termino, "titulo": titulo, "descripcion": descripcion,
        "precio_original": 0, "moneda_original": "N/A", "moneda_normalizada": "N/A",
        "precio_usd": 0, "enlace": resultado.get("url", ""), "imagen": "",
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hora_extraccion": datetime.now().strftime("%H:%M:%S"),
        "fecha_busqueda": datetime.now().strftime("%Y-%m-%d"),
        "categoria": categoria, "subcategoria": "general", "fuente": "google",
        "es_online": True, "tipo_enlace": "directo", "anuncio_id": None,
        "dominio": dominio, "es_cubano": resultado.get("es_cubano", False)
    }