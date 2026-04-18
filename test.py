import sys
sys.path.insert(0, '.')
from scrapers.revolico import obtener_precios_revolico

articulos = obtener_precios_revolico(producto_original='televisor', paginas=1)

print(f'Total: {len(articulos)}')
con_desc = sum(1 for a in articulos if a.get('descripcion') and len(a.get('descripcion', '')) > 10)
print(f'Con descripcion: {con_desc}')

if articulos:
    print(f'Primero: {articulos[0].get("titulo")}')
    desc = articulos[0].get('descripcion', 'SIN')
    print(f'Descripcion: {desc[:100]}')