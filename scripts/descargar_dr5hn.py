import os
import json
import urllib.request
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DATA_DIR = os.path.join(BASE_DIR, 'static', 'data')
DR5HN_DIR = os.path.join(STATIC_DATA_DIR, 'dr5hn')
CITIES_DIR = os.path.join(STATIC_DATA_DIR, 'ciudades')

os.makedirs(DR5HN_DIR, exist_ok=True)
os.makedirs(CITIES_DIR, exist_ok=True)

GITHUB_BASE = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/"

FILES_TO_DOWNLOAD = [
    ("countries.json", os.path.join(DR5HN_DIR, "countries.json")),
    ("states.json", os.path.join(DR5HN_DIR, "states.json")),
    ("countries+states+cities.json", os.path.join(DR5HN_DIR, "countries+states+cities.json")),
]

def download_file(filename, destination):
    url = GITHUB_BASE + filename
    print(f"Descargando {filename} desde GitHub...")
    t0 = time.time()
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    with open(destination, 'wb') as f:
        f.write(content)
    elapsed = round(time.time() - t0, 2)
    print(f"-> Guardado en {destination} ({len(content) / 1024 / 1024:.2f} MB en {elapsed}s)")

def process_and_optimize():
    print("\nOptimizando y generando índices locales rápidos...")
    full_path = os.path.join(DR5HN_DIR, "countries+states+cities.json")
    with open(full_path, 'r', encoding='utf-8') as f:
        countries_data = json.load(f)

    # 1. Lista compacta de Países (paises.json)
    paises_compactos = []
    # 2. Mapeo de departamentos por país (ISO3, ISO2 e ID)
    departamentos_por_pais = {}
    # 3. Mapeo de ciudades por departamento ID
    ciudades_por_departamento = {}

    for c in countries_data:
        c_id = c.get('id')
        c_name = c.get('name')
        c_iso2 = c.get('iso2', '')
        c_iso3 = c.get('iso3', '')
        c_emoji = c.get('emoji', '')
        c_phone = c.get('phonecode', '')
        
        # Nombre en español si está disponible en translations
        translations = c.get('translations', {}) or {}
        nombre_es = translations.get('es') or c_name

        pais_info = {
            'id': c_id,
            'name': nombre_es,
            'name_en': c_name,
            'iso2': c_iso2,
            'iso3': c_iso3,
            'emoji': c_emoji,
            'phonecode': c_phone
        }
        paises_compactos.append(pais_info)

        states_list = []
        for s in c.get('states', []):
            s_id = s.get('id')
            s_name = s.get('name')
            s_code = s.get('state_code', '')
            state_info = {
                'id': s_id,
                'name': s_name,
                'code': s_code,
                'country_id': c_id,
                'country_code': c_iso2,
                'country_iso3': c_iso3
            }
            states_list.append(state_info)

            # Ciudades para este estado
            cities_list = []
            for city in s.get('cities', []):
                cities_list.append({
                    'id': city.get('id'),
                    'name': city.get('name'),
                    'state_id': s_id,
                    'country_id': c_id
                })
            ciudades_por_departamento[str(s_id)] = cities_list

        departamentos_por_pais[c_iso3.upper()] = states_list
        if c_iso2:
            departamentos_por_pais[c_iso2.upper()] = states_list
        if c_id:
            departamentos_por_pais[str(c_id)] = states_list

    # Ordenar países alfabéticamente por nombre en español
    # Poniendo Colombia primero si se desea una experiencia de usuario estelar
    paises_compactos.sort(key=lambda x: x['name'])
    co = next((p for p in paises_compactos if p['iso3'] == 'COL'), None)
    if co:
        paises_compactos.remove(co)
        paises_compactos.insert(0, co)

    # Guardar paises.json
    paises_path = os.path.join(STATIC_DATA_DIR, "paises.json")
    with open(paises_path, 'w', encoding='utf-8') as f:
        json.dump(paises_compactos, f, ensure_ascii=False, indent=2)
    print(f"-> paises.json generado con {len(paises_compactos)} países.")

    # Guardar departamentos_por_pais.json
    deps_path = os.path.join(STATIC_DATA_DIR, "departamentos_por_pais.json")
    with open(deps_path, 'w', encoding='utf-8') as f:
        json.dump(departamentos_por_pais, f, ensure_ascii=False)
    print(f"-> departamentos_por_pais.json generado.")

    # Guardar ciudades_por_departamento.json
    ciudades_path = os.path.join(STATIC_DATA_DIR, "ciudades_por_departamento.json")
    with open(ciudades_path, 'w', encoding='utf-8') as f:
        json.dump(ciudades_por_departamento, f, ensure_ascii=False)
    print(f"-> ciudades_por_departamento.json generado con {len(ciudades_por_departamento)} departamentos con municipios.")

if __name__ == '__main__':
    for fname, dest in FILES_TO_DOWNLOAD:
        if not os.path.exists(dest) or os.path.getsize(dest) == 0:
            download_file(fname, dest)
        else:
            print(f"El archivo {fname} ya existe localmente ({os.path.getsize(dest) / 1024 / 1024:.2f} MB).")
    process_and_optimize()
    print("\n¡Descarga y optimización del dataset dr5hn completada con éxito!")
