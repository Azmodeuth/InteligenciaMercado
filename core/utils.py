"""
================================================================================
FUNCIONES DE UTILIDAD - VERSIÓN MEJORADA
================================================================================
"""
from datetime import datetime
import re

def obtener_timestamp() -> str:
    """Retorna el timestamp actual formateado."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_fecha() -> str:
    """Retorna la fecha actual."""
    return datetime.now().strftime("%Y-%m-%d")

def obtener_hora() -> str:
    """Retorna la hora actual."""
    return datetime.now().strftime("%H:%M:%S")

def obtener_id_busqueda() -> str:
    """Genera un ID único para cada búsqueda."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def simplificar_busqueda(producto: str) -> str:
    """Simplifica la búsqueda a 2 palabras clave."""
    palabras = producto.strip().split()
    if len(palabras) > 2:
        return " ".join(palabras[:2])
    return producto

def limpiar_descripcion(descripcion: str, max_caracteres: int = 5000) -> str:
    """
    Normaliza la descripción sin filtrar contenido importante.
    Preserva TODAS las características del producto.
    """
    if not descripcion:
        return ""
    
    # Convertir a string si no lo es
    resultado = str(descripcion)
    
    # Preservar saltos de línea como separadores
    resultado = resultado.replace('\n', ' | ')
    resultado = resultado.replace('\r', '')
    
    # Limpiar HTML pero preservar contenido
    resultado = re.sub(r'<br\s*/?>', ' | ', resultado)
    resultado = re.sub(r'</p>', ' | ', resultado)
    resultado = re.sub(r'<li>', ' | • ', resultado)
    resultado = re.sub(r'</li>', '', resultado)
    resultado = re.sub(r'<[^>]+>', ' ', resultado)
    
    # Normalizar espacios múltiples
    resultado = re.sub(r'[ \t]+', ' ', resultado)
    resultado = re.sub(r'\|\s*\|+', ' | ', resultado)
    
    # Solo truncar si excede el máximo (5000 caracteres por defecto)
    if len(resultado) > max_caracteres:
        # Intentar truncar en un separador lógico
        truncado = resultado[:max_caracteres]
        ultimo_separador = max(
            truncado.rfind(' | '),
            truncado.rfind('. '),
            truncado.rfind(', ')
        )
        if ultimo_separador > max_caracteres * 0.8:
            resultado = truncado[:ultimo_separador + 1]
        else:
            resultado = truncado
    
    return resultado.strip()

def extraer_caracteristicas_especiales(texto: str) -> dict:
    """
    Extrae características especiales de un texto de descripción.
    Útil para enriquecer las descripciones con datos estructurados.
    """
    if not texto:
        return {}
    
    caracteristicas = {}
    texto_lower = texto.lower()
    
    # Patrones comunes de características
    patrones = {
        'marca': r'(?:marca|brand|fabricante)[:\s]*([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+?)(?:\||,|\.|$)',
        'modelo': r'(?:modelo|model)[:\s]*([a-zA-Z0-9\-/\s]+?)(?:\||,|\.|$)',
        'capacidad': r'(?:capacidad|capacity)[:\s]*([\d.,]+\s*(?:l|litros|lb|kg|galones?)?)',
        'potencia': r'(?:potencia|power|watts?)[:\s]*([\d.,]+\s*(?:w|watts?|hp)?)',
        'voltaje': r'(?:voltaje|voltage|voltios?)[:\s]*([\d.,]+\s*(?:v|voltios?)?)',
        'tamaño': r'(?:tamaño|size|dimensiones?)[:\s]*([\d.,\s x]+(?:cm|m|pulgadas?|")?)',
        'color': r'(?:color)[:\s]*([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+?)(?:\||,|\.|$)',
        'garantia': r'(?:garantía|garantia|warranty)[:\s]*([\d.,]+\s*(?:meses?|años?|días?|days?|months?|years?)?)',
        'estado': r'(?:estado|condición|condition)[:\s]*([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+?)(?:\||,|\.|$)',
    }
    
    for nombre, patron in patrones.items():
        match = re.search(patron, texto_lower)
        if match:
            caracteristicas[nombre] = match.group(1).strip()
    
    # Extraer precios mencionados en la descripción
    precios = re.findall(r'[\$]?\s*([\d.,]+)\s*(?:usd|mlc|cup|cuc|eur|€|\$)?', texto, re.I)
    if precios:
        caracteristicas['precios_mencionados'] = precios[:3]  # Hasta 3 precios
    
    return caracteristicas

def formatear_caracteristicas(caracteristicas: dict) -> str:
    """
    Formatea un diccionario de características como string legible.
    """
    if not caracteristicas:
        return ""
    
    partes = []
    for clave, valor in caracteristicas.items():
        if valor and str(valor).strip():
            # Capitalizar la clave
            clave_fmt = clave.replace('_', ' ').title()
            partes.append(f"{clave_fmt}: {valor}")
    
    return " | ".join(partes)
