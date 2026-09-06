import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

_STATIC_DATA_DIR = os.path.join(settings.BASE_DIR, 'static', 'data')

_PAISES = None
_DEPARTAMENTOS = None
_CIUDADES = None

# Mapeos inversos para resolución de nombres
_MAPA_PAISES = None
_MAPA_DEPARTAMENTOS = None
_MAPA_CIUDADES = None


def _cargar_datos():
    global _PAISES, _DEPARTAMENTOS, _CIUDADES, _MAPA_PAISES, _MAPA_DEPARTAMENTOS, _MAPA_CIUDADES

    if _PAISES is not None:
        return

    paises_path = os.path.join(_STATIC_DATA_DIR, 'paises.json')
    deps_path = os.path.join(_STATIC_DATA_DIR, 'departamentos_por_pais.json')
    ciudades_path = os.path.join(_STATIC_DATA_DIR, 'ciudades_por_departamento.json')

    if os.path.exists(paises_path):
        with open(paises_path, 'r', encoding='utf-8') as f:
            _PAISES = json.load(f)
    else:
        _PAISES = []

    if os.path.exists(deps_path):
        with open(deps_path, 'r', encoding='utf-8') as f:
            _DEPARTAMENTOS = json.load(f)
    else:
        _DEPARTAMENTOS = {}

    if os.path.exists(ciudades_path):
        with open(ciudades_path, 'r', encoding='utf-8') as f:
            _CIUDADES = json.load(f)
    else:
        _CIUDADES = {}

    # Construir mapas para resolución ultrarrápida de nombres
    _MAPA_PAISES = {}
    for p in _PAISES:
        nombre = p.get('name', '')
        if p.get('iso3'):
            _MAPA_PAISES[str(p['iso3']).upper()] = nombre
        if p.get('iso2'):
            _MAPA_PAISES[str(p['iso2']).upper()] = nombre
        if p.get('id'):
            _MAPA_PAISES[str(p['id'])] = nombre

    _MAPA_DEPARTAMENTOS = {}
    for dep_list in _DEPARTAMENTOS.values():
        for d in dep_list:
            d_id = str(d.get('id'))
            if d_id and d_id not in _MAPA_DEPARTAMENTOS:
                _MAPA_DEPARTAMENTOS[d_id] = d.get('name', '')

    _MAPA_CIUDADES = {}
    for c_list in _CIUDADES.values():
        for c in c_list:
            c_id = str(c.get('id'))
            if c_id and c_id not in _MAPA_CIUDADES:
                _MAPA_CIUDADES[c_id] = c.get('name', '')


def get_paises():
    """Retorna la lista completa de países."""
    _cargar_datos()
    return _PAISES


def get_departamentos(pais_codigo_o_id):
    """
    Retorna la lista de departamentos para un país dado.
    Acepta código ISO3 (ej. 'COL'), ISO2 (ej. 'CO') o ID numérico.
    """
    _cargar_datos()
    if not pais_codigo_o_id:
        return []
    key = str(pais_codigo_o_id).strip().upper()
    return _DEPARTAMENTOS.get(key, [])


def get_ciudades(departamento_id):
    """
    Retorna la lista de ciudades o municipios para un departamento dado por su ID.
    """
    _cargar_datos()
    if not departamento_id:
        return []
    key = str(departamento_id).strip()
    return _CIUDADES.get(key, [])


def get_nombre_pais(pais_codigo_o_id):
    """Resuelve el nombre legible del país."""
    if not pais_codigo_o_id:
        return ""
    _cargar_datos()
    key = str(pais_codigo_o_id).strip().upper()
    return _MAPA_PAISES.get(key, str(pais_codigo_o_id))


def get_nombre_departamento(departamento_id):
    """Resuelve el nombre legible del departamento según su ID."""
    if not departamento_id:
        return ""
    _cargar_datos()
    key = str(departamento_id).strip()
    return _MAPA_DEPARTAMENTOS.get(key, str(departamento_id))


def get_nombre_ciudad(ciudad_id):
    """Resuelve el nombre legible de la ciudad/municipio según su ID."""
    if not ciudad_id:
        return ""
    _cargar_datos()
    key = str(ciudad_id).strip()
    return _MAPA_CIUDADES.get(key, str(ciudad_id))


# ==============================================================================
# ENDPOINTS REST / AJAX
# ==============================================================================

@require_GET
def api_paises(request):
    """
    Retorna la lista de países disponibles en el dataset local dr5hn.
    """
    paises = get_paises()
    return JsonResponse(paises, safe=False)


@require_GET
def api_departamentos(request, pais_id):
    """
    Retorna los departamentos o estados de un país (por ISO3, ISO2 o ID).
    """
    departamentos = get_departamentos(pais_id)
    return JsonResponse(departamentos, safe=False)


@require_GET
def api_ciudades(request, departamento_id):
    """
    Retorna los municipios o ciudades de un departamento dado por su ID.
    """
    ciudades = get_ciudades(departamento_id)
    return JsonResponse(ciudades, safe=False)
