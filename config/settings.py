"""
================================================================================
CONFIGURACIÓN Y CONSTANTES
================================================================================
"""
import logging
import sys

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# TASAS DE CAMBIO
# ==============================================================================
TASAS_DE_CAMBIO = {
    "USD": 1.0,
    "MLC": 1.0,
    "EUR": 1.08,
    "CUP": 320.0,
}

TASA_CAMBIO_CUP = 320.0
TASA_CAMBIO_MLC = 1.0
TASA_CAMBIO_EUR = 1.08

# ==============================================================================
# CONFIGURACIÓN DE ANÁLISIS
# ==============================================================================
QUANTILE_INFERIOR = 0.15
QUANTILE_SUPERIOR = 0.85
PRECIO_MINIMO_VALIDO = 1.0  # Productos ≤$1 se excluyen

# ==============================================================================
# BASE DE DATOS - RUTA ABSOLUTA
# ==============================================================================
import os
# Usar ruta absoluta para evitar problemas de directorio de trabajo
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(_PROJECT_DIR, "inteligencia_mercado.db")
DB_TABLE = "anuncios_revolico"
MIN_PRODUCTOS_BUSQUEDA_RAPIDA = 10

# ==============================================================================
# CATÁLOGO DE CATEGORÍAS
# ==============================================================================
CATEGORIAS = {
    "electrodomesticos": {
        "nombre": "Electrodomésticos",
        "icono": "🔌",
        "subcategorias": {
            "neveras": {"nombre": "Neveras y Refrigeradores", "productos": ["nevera", "refrigerador", "frigorifico", "nevera samsung", "nevera lg"]},
            "lavadoras": {"nombre": "Lavadoras y Secadoras", "productos": ["lavadora", "secadora", "lavadora samsung", "lavadora lg", "lavaseca"]},
            "aires": {"nombre": "Aires Acondicionados", "productos": ["aire acondicionado", "aire 12000", "aire 18000", "split", "minisplit"]},
            "cocinas": {"nombre": "Cocinas y Hornos", "productos": ["cocina", "hornilla", "estufa electrica", "cocina de gas"]},
            "televisores": {"nombre": "Televisores", "productos": ["televisor", "tv samsung", "tv lg", "smart tv", "televisor 55"]},
            "microondas": {"nombre": "Microondas", "productos": ["microondas", "horno microondas"]},
            "ventiladores": {"nombre": "Ventiladores", "productos": ["ventilador", "ventilador pedestal", "ventilador techo"]},
            "freidoras": {"nombre": "Freidoras de Aire", "productos": ["freidora aire", "air fryer", "freidora sin aceite"]},
            "licuadoras": {"nombre": "Licuadoras y Batidoras", "productos": ["licuadora", "batidora", "procesador comida"]},
            "cafeteras": {"nombre": "Cafeteras", "productos": ["cafetera", "cafetera electrica"]},
            "hornos_electricos": {"nombre": "Hornos Eléctricos", "productos": ["horno electrico", "horno de mesa"]},
            "planchas": {"nombre": "Planchas", "productos": ["plancha", "plancha vapor"]},
            "aspiradoras": {"nombre": "Aspiradoras", "productos": ["aspiradora", "aspiradora vertical"]},
            "estufas": {"nombre": "Estufas y Cocinetas", "productos": ["estufa", "cocineta", "hornilla"]},
            "calentadores": {"nombre": "Calentadores de Agua", "productos": ["calentador agua", "termo electrico"]},
            "congeladores": {"nombre": "Congeladores", "productos": ["congelador", "nevera horizontal"]},
        }
    },
    "tecnologia": {
        "nombre": "Tecnología",
        "icono": "📱",
        "subcategorias": {
            "celulares": {"nombre": "Celulares y Smartphones", "productos": ["celular", "iphone", "samsung", "xiaomi", "smartphone"]},
            "laptops": {"nombre": "Laptops y Computadoras", "productos": ["laptop", "computadora", "notebook", "macbook", "pc"]},
            "tablets": {"nombre": "Tablets", "productos": ["tablet", "ipad", "tablet samsung"]},
            "audifonos": {"nombre": "Audífonos y Headsets", "productos": ["audifonos", "headset", "airpods", "auriculares"]},
            "smartwatches": {"nombre": "Smartwatches", "productos": ["smartwatch", "reloj inteligente", "apple watch"]},
            "camaras": {"nombre": "Cámaras", "productos": ["camara", "camara digital"]},
            "consolas": {"nombre": "Consolas de Videojuegos", "productos": ["playstation", "xbox", "nintendo", "consola", "ps4", "ps5"]},
            "impresoras": {"nombre": "Impresoras", "productos": ["impresora", "impresora laser", "multifuncional"]},
            "monitores": {"nombre": "Monitores", "productos": ["monitor", "pantalla", "monitor gaming"]},
            "accesorios": {"nombre": "Accesorios Tecnológicos", "productos": ["cargador", "cable", "funda", "mouse", "teclado"]},
        }
    },
    "vehiculos": {
        "nombre": "Vehículos",
        "icono": "🚗",
        "subcategorias": {
            "carros": {"nombre": "Carros", "productos": ["carro", "auto", "mazda", "toyota", "honda", "nissan"]},
            "motos": {"nombre": "Motocicletas", "productos": ["moto", "motocicleta", "scooter", "moto yamaha", "moto honda"]},
            "bicicletas": {"nombre": "Bicicletas", "productos": ["bicicleta", "bici", "bicicleta electrica"]},
            "camiones": {"nombre": "Camiones y Camionetas", "productos": ["camion", "camioneta", "pickup"]},
            "repuestos": {"nombre": "Repuestos y Piezas", "productos": ["repuesto", "pieza", "motor", "neumatico"]},
        }
    }
}

# ==============================================================================
# HEADERS HTTP
# ==============================================================================
HEADERS_CHROME = {
    "sec-ch-ua-platform": '"Windows"',
    "Referer": "https://www.revolico.com/",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "accept": "application/graphql-response+json,application/json;q=0.9",
    "content-type": "application/json",
    "origin": "https://www.revolico.com",
    "rid": "anti-csrf",
    "st-auth-mode": "header"
}

# ==============================================================================
# API URLs
# ==============================================================================
REVOLICO_API_URL = "https://graphql-api.revolico.app/"

def actualizar_tasas_cambio(cup=None, mlc=None, eur=None):
    """Actualiza las tasas de cambio globales."""
    global TASAS_DE_CAMBIO, TASA_CAMBIO_CUP, TASA_CAMBIO_MLC, TASA_CAMBIO_EUR
    
    if cup is not None:
        TASAS_DE_CAMBIO["CUP"] = cup
        TASA_CAMBIO_CUP = cup
    if mlc is not None:
        TASAS_DE_CAMBIO["MLC"] = mlc
        TASA_CAMBIO_MLC = mlc
    if eur is not None:
        TASAS_DE_CAMBIO["EUR"] = eur
        TASA_CAMBIO_EUR = eur
    
    logger.info(f"💱 Tasas actualizadas: CUP={TASAS_DE_CAMBIO['CUP']}, MLC={TASAS_DE_CAMBIO['MLC']}, EUR={TASAS_DE_CAMBIO['EUR']}")