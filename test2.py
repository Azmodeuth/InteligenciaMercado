import requests
import json

print("=" * 60)
print("DIAGNOSTICO DE CONEXION A REVOLICO")
print("=" * 60)

# Test 1: Conexion a API GraphQL
print("\n1. PROBANDO API GRAPHQL...")

url = "https://graphql-api.revolico.app/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.revolico.com",
}

query = """
query AdsSearch($contains: String, $page: Int, $pageLength: Int) {
  adsPerPage(contains: $contains, page: $page, pageLength: $pageLength) {
    edges {
      node {
        id
        title
        price
        currency
        permalink
      }
    }
  }
}
"""

payload = [{
    "operationName": "AdsSearch",
    "variables": {"contains": "televisor", "page": 1, "pageLength": 10},
    "query": query
}]

try:
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Respuesta: {json.dumps(data, indent=2)[:500]}")
        
        # Verificar si hay errores
        if 'errors' in str(data):
            print("ERRORES detectados en la respuesta")
        
        # Verificar si hay datos
        try:
            edges = data[0]['data']['adsPerPage']['edges']
            print(f"\nArticulos encontrados: {len(edges)}")
            if edges:
                print(f"Primero: {edges[0]['node']['title']}")
        except:
            print("No se pudieron extraer los articulos")
    else:
        print(f"Error HTTP: {r.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)