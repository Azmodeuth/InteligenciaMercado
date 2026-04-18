"""
================================================================================
FUNCIONES DE MONEDA
================================================================================
"""
from config.settings import TASAS_DE_CAMBIO, logger

def normalizar_moneda(moneda_raw) -> str:
    """Normaliza el código de moneda a formato estándar."""
    if moneda_raw is None:
        return "DESCONOCIDA"
    
    moneda = str(moneda_raw).upper().strip()
    mapeo = {
        "USD": "USD", "US": "USD", "DOLAR": "USD", "DÓLAR": "USD", "$": "USD",
        "MLC": "MLC", "EUR": "EUR", "EURO": "EUR", "€": "EUR",
        "CUP": "CUP", "PESO": "CUP", "PESOS": "CUP", "MN": "CUP", "CUC": "CUP",
    }
    return mapeo.get(moneda, moneda)

def convertir_a_usd(precio: float, moneda: str) -> float:
    """Convierte un precio a USD usando las tasas configuradas."""
    moneda = normalizar_moneda(moneda)
    
    if moneda in ["USD", "MLC"]:
        return round(precio, 2)
    elif moneda == "EUR":
        return round(precio * TASAS_DE_CAMBIO["EUR"], 2)
    elif moneda == "CUP":
        return round(precio / TASAS_DE_CAMBIO["CUP"], 2)
    else:
        logger.warning(f"⚠️ Moneda desconocida '{moneda}', tratando como USD")
        return round(precio, 2)