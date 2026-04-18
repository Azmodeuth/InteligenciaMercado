"""
================================================================================
SCRAPERS ADICIONALES - COMPATIBILIDAD V5.0
================================================================================
Importa desde el módulo scrapers actualizado con búsqueda exhaustiva.

Este archivo existe para compatibilidad con código que importa:
    from scrapers_adicionales import ...

NOTA: Porlalivre fue eliminado - sitio no disponible
"""

from scrapers.multi_fuente import (
    AgregadorMultiFuente,
    ScraperVoypati,
    ScraperElYerro,
    ScraperFadiar,
    TERMINOS_RELACIONADOS,
    obtener_terminos_relacionados,
    normalizar_moneda,
    convertir_a_usd,
    limpiar_precio
)
