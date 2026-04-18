"""
================================================================================
SCRAPER REVOLICO V41.4 - DESCRIPCIONES COMPLETAS (GRAPHQL + HTML FALLBACK)
================================================================================
- Intenta GraphQL primero para descripciones
- Si falla, hace scraping del HTML de la página del anuncio
- Extrae descripción completa, teléfono, ubicación
- Máxima compatibilidad con el negocio
- OPTIMIZACIÓN NUBE: Rotación de User-Agents y Calentamiento de Categoría
"""
from curl_cffi import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re, threading, time, random, json, logging
from config.settings import REVOLICO_API_URL, CATEGORIAS
from config.queries import QUERY_BUSQUEDA, QUERY_DETALLE_ANUNCIO
from core.utils import obtener_timestamp, obtener_fecha, obtener_hora, obtener_id_busqueda, simplificar_busqueda, limpiar_descripcion
from core.currency import normalizar_moneda, convertir_a_usd

# Configuración
MAX_PRODUCTOS = 1000
MAX_HILOS = 12
REQUEST_TIMEOUT = 30

# Lista de agentes para rotar si hay 403
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

# Headers para GraphQL (Apollo) - DINÁMICOS
def obtener_headers_apollo():
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://www.revolico.com",
        "Referer": "https://www.revolico.com/",
        "X-Client-Info": "apollo-client/4.1.6",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

HEADERS_HTML = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Estado global
estado_global = {
    'graphql_fallos': 0,
    'usar_html': False,
    'lock': threading.Lock(),
    'mensaje_impreso': False
}

print_lock = threading.Lock()
contadores = {'exitosos': 0, 'fallidos': 0, 'lock': threading.Lock()}


def obtener_descripcion_graphql(session, anuncio_id):
    """Mejorado para manejar errores de esquema en la API."""
    try:
        payload = [{
            "operationName": "AdDetail",
            "variables": {"id": anuncio_id},
            "extensions": {"clientLibrary": {"name": "@apollo/client", "version": "4.1.6"}},
            "query": QUERY_DETALLE_ANUNCIO
        }]
        
        r = session.post(
            REVOLICO_API_URL, 
            headers=obtener_headers_apollo(), 
            json=payload, 
            impersonate="chrome120", 
            timeout=REQUEST_TIMEOUT
        )
        
        if r.status_code == 200:
            data = r.json()
            res = data[0] if isinstance(data, list) else data
            
            if 'errors' in res:
                return None
            
            ad = res.get('data', {}).get('ad', {})
            
            if ad:
                descripcion = ad.get('body') or ad.get('description') or ""
                phone_info = ad.get('phoneInfo', {})
                first_phone = phone_info.get('firstPhone', {})
                telefono = first_phone.get('number', '')
                
                if descripcion:
                    descripcion = re.sub(r'<[^>]+>', ' ', str(descripcion))
                    descripcion = re.sub(r'\s+', ' ', descripcion).strip()
                
                partes = []
                if descripcion and len(descripcion) > 10:
                    partes.append(descripcion)
                if telefono:
                    partes.append(f"Tel: {telefono}")
                
                if partes:
                    return ' | '.join(partes)
        
        return None
    except:
        return None

def obtener_descripcion_html(session, anuncio_id, permalink):
    """Scrapea el HTML con triple validación para asegurar descripción al 100%."""
    try:
        url = f"https://www.revolico.com{permalink}" if permalink.startswith('/') else (permalink if permalink else f"https://www.revolico.com/anuncio/{anuncio_id}")
        
        r = session.get(url, headers=HEADERS_HTML, impersonate="chrome120", timeout=REQUEST_TIMEOUT)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        descripcion_final = ""
        extras = []

        script_ld = soup.find('script', type='application/ld+json')
        if script_ld:
            try:
                data_ld = json.loads(script_ld.string)
                if isinstance(data_ld, list): data_ld = data_ld[0]
                descripcion_final = data_ld.get('description', '')
            except: pass

        if not descripcion_final:
            next_script = soup.find('script', id='__NEXT_DATA__')
            if next_script:
                try:
                    data = json.loads(next_script.string)
                    def buscar_en_json(obj):
                        if isinstance(obj, dict):
                            for k in ['body', 'description', 'content']:
                                if k in obj and isinstance(obj[k], str) and len(obj[k]) > 20:
                                    return obj[k]
                            for v in obj.values():
                                res = buscar_en_json(v)
                                if res: return res
                        elif isinstance(obj, list):
                            for i in obj:
                                res = buscar_en_json(i)
                                if res: return res
                        return None
                    descripcion_final = buscar_en_json(data)
                except: pass

        if not descripcion_final:
            sel_css = ['div[class*="DescriptionText"]', 'div[class*="AdDescription"]', 'section[class*="description"]', 'pre']
            for selector in sel_css:
                found = soup.select_one(selector)
                if found and len(found.get_text()) > 20:
                    descripcion_final = found.get_text(separator=" ", strip=True)
                    break

        if "Tel:" not in descripcion_final:
            tels = re.findall(r'5\d{7}|6\d{7}', r.text)
            if tels: extras.append(f"Tel: {tels[0]}")
        
        ubi = soup.select_one('span[class*="Location"], div[class*="location"]')
        if ubi: extras.append(f"Ubicación: {ubi.get_text(strip=True)}")

        if descripcion_final:
            descripcion_final = re.sub(r'<[^>]+>', ' ', str(descripcion_final))
            descripcion_final = re.sub(r'\s+', ' ', descripcion_final).strip()
            
            resultado = descripcion_final
            if extras:
                resultado += " | " + " | ".join(list(set(extras)))
            return resultado[:2000]

        return None
    except Exception:
        return None

def obtener_descripcion_completa(session, anuncio_id, permalink):
    """Obtiene descripción: GraphQL primero, HTML fallback."""
    with estado_global['lock']:
        usar_html = estado_global['usar_html']
    
    if not usar_html:
        desc = obtener_descripcion_graphql(session, anuncio_id)
        if desc:
            return (anuncio_id, desc, "graphql")
        
        with estado_global['lock']:
            estado_global['graphql_fallos'] += 1
            if estado_global['graphql_fallos'] >= 5 and not estado_global['mensaje_impreso']:
                estado_global['usar_html'] = True
                estado_global['mensaje_impreso'] = True
                with print_lock:
                    print(f"\n   ⚠️ GraphQL bloqueado → Usando HTML para descripciones\n")
    
    desc = obtener_descripcion_html(session, anuncio_id, permalink)
    if desc:
        return (anuncio_id, desc, "html")
    
    return (anuncio_id, None, None)


def obtener_descripciones_batch(session, articulos):
    """Procesa descripciones en paralelo."""
    if not articulos:
        return {}
    
    descripciones = {}
    total = len(articulos)
    
    print(f"\n   📝 EXTRAYENDO DESCRIPCIONES ({MAX_HILOS} hilos)")
    
    contadores['exitosos'] = 0
    contadores['fallidos'] = 0
    metodos = {'graphql': 0, 'html': 0}
    procesados = 0
    
    def procesar_uno(art):
        aid = art['anuncio_id']
        permalink = art.get('permalink', '')
        return obtener_descripcion_completa(session, aid, permalink)
    
    with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
        futuros = {executor.submit(procesar_uno, art): art for art in articulos}
        
        for futuro in as_completed(futuros):
            procesados += 1
            try:
                aid, desc, metodo = futuro.result()
                if desc:
                    descripciones[aid] = desc
                    with contadores['lock']:
                        contadores['exitosos'] += 1
                    if metodo:
                        metodos[metodo] = metodos.get(metodo, 0) + 1
                else:
                    with contadores['lock']:
                        contadores['fallidos'] += 1
            except:
                with contadores['lock']:
                    contadores['fallidos'] += 1
    
    return descripciones


def obtener_precios_revolico(producto_original=None, categoria=None, subcategoria=None, productos_predefinidos=None, paginas=15) -> list:
    """Función principal - V41.4 con descripciones completas (Bypass 403)."""
    
    estado_global['graphql_fallos'] = 0
    estado_global['usar_html'] = False
    estado_global['mensaje_impreso'] = False
    
    id_busqueda = obtener_id_busqueda()
    timestamp_busqueda = obtener_timestamp()
    fecha_busqueda = obtener_fecha()
    hora_busqueda = obtener_hora()
    
    termino = simplificar_busqueda(producto_original) if producto_original else ""
    articulos_base = []
    ids_vistos = set()
    
    print("\n" + "═" * 80)
    print(f"║ ⚡ REVOLICO V41.4 - DESCRIPCIONES COMPLETAS (BYPASS CLOUDFLARE) ".center(78) + "║")
    print("═" * 80 + "\n")
    
    with requests.Session() as session:
        # --- CALENTAMIENTO DE CATEGORÍA (Vital para saltar el 403) ---
        try:
            cat_url = f"https://www.revolico.com/busqueda?q={termino}"
            session.get(cat_url, headers=HEADERS_HTML, impersonate="chrome120", timeout=15)
            time.sleep(random.uniform(2.0, 4.0)) 
        except: pass

        for p_num in range(1, paginas + 1):
            if len(articulos_base) >= MAX_PRODUCTOS:
                break
            
            payload = [{
                "operationName": "AdsSearch",
                "variables": {
                    "contains": termino,
                    "page": p_num,
                    "pageLength": 100,
                    "sort": [{"order": "desc", "field": "relevance"}]
                },
                "extensions": {"clientLibrary": {"name": "@apollo/client", "version": "4.1.6"}},
                "query": QUERY_BUSQUEDA
            }]
            
            try:
                # Rotar headers en cada página para evitar detección
                r = session.post(
                    REVOLICO_API_URL,
                    headers=obtener_headers_apollo(),
                    json=payload,
                    impersonate="chrome120",
                    timeout=REQUEST_TIMEOUT
                )
                
                print(f"   [DEBUG] Revolico Pág {p_num} Status: {r.status_code}")

                if r.status_code != 200:
                    # Intento de rescate: Si hay 403, esperar más tiempo y reintentar una vez
                    if r.status_code == 403:
                        time.sleep(5)
                        continue
                    continue
                
                data = r.json()
                res_json = data[0] if isinstance(data, list) else data
                
                if 'errors' in res_json:
                    continue
                
                ads = res_json.get('data', {}).get('adsPerPage', {}).get('edges', [])
                
                if not ads:
                    break
                
                for ad in ads:
                    nodo = ad.get('node', {})
                    aid = nodo.get('id')
                    precio = nodo.get('price')
                    
                    if not aid or aid in ids_vistos: continue
                    if not precio or precio <= 0: continue
                    
                    ids_vistos.add(aid)
                    
                    desc_listado = nodo.get('description') or ""
                    if desc_listado:
                        desc_listado = re.sub(r'<[^>]+>', ' ', str(desc_listado))
                        desc_listado = re.sub(r'\s+', ' ', desc_listado).strip()
                    
                    articulos_base.append({
                        "id_busqueda": id_busqueda,
                        "producto_buscado": termino,
                        "titulo": nodo.get('title', 'Sin título'),
                        "descripcion": desc_listado or nodo.get('title', ''),
                        "precio_original": float(precio),
                        "moneda_original": nodo.get('currency') or "USD",
                        "moneda_normalizada": normalizar_moneda(nodo.get('currency')),
                        "precio_usd": convertir_a_usd(float(precio), normalizar_moneda(nodo.get('currency'))),
                        "enlace": f"https://www.revolico.com{nodo.get('permalink', '')}",
                        "fecha_extraccion": timestamp_busqueda,
                        "hora_extraccion": hora_busqueda,
                        "fecha_busqueda": fecha_busqueda,
                        "categoria": categoria or "general",
                        "subcategoria": subcategoria or "general",
                        "fuente": "revolico",
                        "es_online": True,
                        "anuncio_id": aid,
                        "permalink": nodo.get('permalink', '')
                    })
                
                print(f"   📥 Pág {p_num}: {len(ads)} ads | Total: {len(articulos_base)}")
                time.sleep(random.uniform(1.0, 2.5))
                
            except Exception:
                continue
        
        if articulos_base:
            descripciones = obtener_descripciones_batch(session, articulos_base)
            for art in articulos_base:
                aid = art['anuncio_id']
                if aid in descripciones and descripciones[aid]:
                    art['descripcion'] = descripciones[aid]
                if 'permalink' in art:
                    del art['permalink']
    
    return articulos_base