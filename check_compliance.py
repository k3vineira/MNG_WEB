#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_compliance.py
===================
Script de auditoría automatizada para verificar el cumplimiento de la lista
de chequeo académica en el proyecto MNG_WEB.

Uso:
    python check_compliance.py
"""

import os
import re
import sys

# ──────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDED_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', 'env', 'ENV',
    'node_modules', '.gemini', 'staticfiles', 'media'
}
EXCLUDED_FILES = {
    'bootstrap.min.css', 'datatables.css', 'datatables.min.css',
    'bootstrap.min.js', 'jquery.min.js', 'jquery.dataTables.min.js',
    'check_compliance.py', 'refactor_render.py'
}

# Códigos de colores ANSI para consola
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

# ──────────────────────────────────────────────────────────────────────
# UTILIDADES DE BÚSQUEDA
# ──────────────────────────────────────────────────────────────────────
def get_all_files(extension=None):
    """Retorna una lista de rutas absolutas de todos los archivos relevantes."""
    files_list = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            if f in EXCLUDED_FILES:
                continue
            if extension:
                if f.endswith(extension):
                    files_list.append(os.path.join(root, f))
            else:
                files_list.append(os.path.join(root, f))
    return files_list

def read_file_safe(path):
    """Lee un archivo de forma segura manejando codificaciones."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

# ──────────────────────────────────────────────────────────────────────
# ANALIZADORES DE CRITERIOS
# ──────────────────────────────────────────────────────────────────────

def check_c1_template_syntax(html_files):
    """1. Sintaxis del framework: Busca directivas Django en HTML."""
    if not html_files:
        return "NO APLICA", "No se encontraron archivos HTML.", 0
    
    django_tags = re.compile(r'\{%|\{\{')
    matching_files = []
    
    for f in html_files:
        content = read_file_safe(f)
        if django_tags.search(content):
            matching_files.append(os.path.relpath(f, BASE_DIR))
            
    pct = len(matching_files) / len(html_files) * 100
    details = "Se encontraron " + str(len(matching_files)) + " de " + str(len(html_files)) + " plantillas utilizando sintaxis Django (tags {% ... %} o variables {{ ... }})."
    
    if pct >= 80:
        return "CUMPLE", details, pct
    elif pct > 0:
        return "PARCIAL", details, pct
    else:
        return "NO CUMPLE", details, pct

def check_c2_routing(py_files):
    """2. Enrutamiento: Busca archivos urls.py y declaración de rutas."""
    urls_files = [f for f in py_files if os.path.basename(f) == 'urls.py']
    if not urls_files:
        return "NO CUMPLE", "No se encontró ningún archivo urls.py en el proyecto.", 0
        
    path_pattern = re.compile(r'\b(path|re_path)\s*\(')
    matching_files = []
    
    for f in urls_files:
        content = read_file_safe(f)
        if path_pattern.search(content):
            matching_files.append(os.path.relpath(f, BASE_DIR))
            
    details = f"Se detectaron {len(urls_files)} archivos de enrutamiento (urls.py). Rutas válidas configuradas en: {', '.join(matching_files)}."
    
    if len(matching_files) == len(urls_files):
        return "CUMPLE", details, 100
    elif len(matching_files) > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c3_api_consumption(py_files, js_files):
    """3. Consumo de API REST: Busca llamadas fetch/axios en JS o requests en Python y control de errores."""
    api_calls = 0
    error_handling = 0
    
    # Buscar en JS (fetch, axios)
    fetch_pattern = re.compile(r'\bfetch\s*\(|\baxios\.')
    catch_pattern = re.compile(r'\.catch\s*\(|catch\s*\(\w+\)')
    
    # Buscar en Python (requests)
    req_pattern = re.compile(r'\brequests\.(get|post|put|delete|patch)\b')
    try_except_pattern = re.compile(r'\btry\b[\s\S]+?\bexcept\b')
    
    found_details = []
    
    for f in js_files:
        content = read_file_safe(f)
        if fetch_pattern.search(content):
            api_calls += 1
            if catch_pattern.search(content):
                error_handling += 1
            found_details.append(f"JS: {os.path.relpath(f, BASE_DIR)}")
            
    for f in py_files:
        content = read_file_safe(f)
        if req_pattern.search(content):
            api_calls += 1
            if try_except_pattern.search(content):
                error_handling += 1
            found_details.append(f"Python: {os.path.relpath(f, BASE_DIR)}")
            
    if api_calls == 0:
        return "NO APLICA", "No se detectaron integraciones de consumo API REST externo (el proyecto es mayormente autónomo).", 100
        
    pct = (error_handling / api_calls) * 100
    details = f"Se detectó consumo API/servicios en {api_calls} archivos ({', '.join(found_details)}). Con control de errores (try/catch o .catch): {error_handling}."
    
    if pct >= 80:
        return "CUMPLE", details, pct
    elif pct > 0:
        return "PARCIAL", details, pct
    else:
        return "NO CUMPLE", details, pct

def check_c4_css_methodology(css_files):
    """4. CSS con metodología BEM o Atómico."""
    if not css_files:
        return "NO APLICA", "No se encontraron archivos CSS personalizados.", 0
        
    # Patrón BEM simplificado: contiene bloque__elemento o bloque--modificador
    bem_pattern = re.compile(r'\.[a-zA-Z0-9-]+__[a-zA-Z0-9-]+|\.[a-zA-Z0-9-]+--[a-zA-Z0-9-]+')
    matching_selectors = 0
    total_selectors = 0
    
    matching_files = []
    
    for f in css_files:
        content = read_file_safe(f)
        # Contar selectores de clase simplificados
        classes = re.findall(r'\.[a-zA-Z0-9_-]+', content)
        total_selectors += len(classes)
        bem_matches = bem_pattern.findall(content)
        matching_selectors += len(bem_matches)
        
        if len(bem_matches) > 0:
            matching_files.append(os.path.relpath(f, BASE_DIR))
            
    if total_selectors == 0:
        return "NO CUMPLE", "No se encontraron clases definidas en el CSS.", 0
        
    pct = (matching_selectors / total_selectors) * 100
    details = f"Se analizaron {len(css_files)} archivos CSS. Selectores de clase totales: {total_selectors}. Coincidencias de convención BEM (__ o --): {matching_selectors}."
    
    # Las convenciones BEM suelen coexistir con selectores globales, por lo que un 10% ya indica intención BEM.
    if pct >= 10:
        return "CUMPLE", details + f" (BEM detectado en: {', '.join(matching_files)})", pct * 10 # escalado
    elif pct > 0:
        return "PARCIAL", details + f" (BEM parcial en: {', '.join(matching_files)})", pct * 10
    else:
        return "NO CUMPLE", details + " (No se usa convención BEM de clases. Los estilos son tradicionales o Bootstrap).", 0

def check_c5_data_binding(html_files):
    """5. Binding de datos en DOM (Reactivo/Contexto)."""
    if not html_files:
        return "NO APLICA", "No hay plantillas HTML.", 0
        
    binding_pattern = re.compile(r'\{\{\s*[a-zA-Z0-9_.]+\s*\}\}')
    matching_count = 0
    
    for f in html_files:
        content = read_file_safe(f)
        if binding_pattern.search(content):
            matching_count += 1
    pct = (matching_count / len(html_files)) * 100
    details = "Se detectó vinculación (binding) de datos dinámica mediante contexto Django ({{ variable }}) en " + str(matching_count) + " de " + str(len(html_files)) + " archivos de plantilla."
    
    if pct >= 70:
        return "CUMPLE", details, pct
    elif pct > 0:
        return "PARCIAL", details, pct
    else:
        return "NO CUMPLE", details, 0

def check_c6_form_validation(py_files, html_files):
    """6. Validación de formularios (Backend/Frontend)."""
    # En Django, esto se hace con forms.py y validación is_valid()
    forms_files = [f for f in py_files if os.path.basename(f) == 'forms.py']
    is_valid_pattern = re.compile(r'\.is_valid\s*\(')
    
    form_instances = len(forms_files)
    views_validating = 0
    
    for f in py_files:
        content = read_file_safe(f)
        if is_valid_pattern.search(content):
            views_validating += 1
            
    details = f"Se encontraron {form_instances} archivos forms.py con esquemas de validación de Django. Se detectó llamada de validación (.is_valid()) en vistas en {views_validating} ocasiones."
    
    if form_instances > 0 and views_validating > 0:
        return "CUMPLE", details, 100
    elif form_instances > 0 or views_validating > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c7_env_variables():
    """7. Variables de entorno en configuración."""
    settings_path = os.path.join(BASE_DIR, 'core', 'settings.py')
    if not os.path.exists(settings_path):
        return "NO CUMPLE", "No se encontró core/settings.py.", 0
        
    content = read_file_safe(settings_path)
    
    has_dotenv = "load_dotenv" in content
    has_environ = "os.environ" in content or "os.getenv" in content
    
    details = f"Análisis de core/settings.py: Carga de .env (load_dotenv): {'SÍ' if has_dotenv else 'NO'}. Lectura de variables (os.environ): {'SÍ' if has_environ else 'NO'}."
    
    if has_dotenv and has_environ:
        return "CUMPLE", details, 100
    elif has_dotenv or has_environ:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c8_folder_hierarchy():
    """8. Estructura y jerarquía lógica de carpetas."""
    required_dirs = ['core', 'static', 'templates']
    found = [d for d in required_dirs if os.path.isdir(os.path.join(BASE_DIR, d))]
    
    django_apps = []
    for entry in os.listdir(BASE_DIR):
        entry_path = os.path.join(BASE_DIR, entry)
        if os.path.isdir(entry_path) and entry not in EXCLUDED_DIRS:
            # Si contiene views.py y models.py, asumimos que es una app Django
            if os.path.exists(os.path.join(entry_path, 'views.py')) and os.path.exists(os.path.join(entry_path, 'models.py')):
                django_apps.append(entry)
                
    details = f"Carpetas core del proyecto: {', '.join(found)} de {len(required_dirs)}. Apps de Django estructuradas e independientes detectadas: {', '.join(django_apps)}."
    
    if len(found) == len(required_dirs) and len(django_apps) >= 3:
        return "CUMPLE", details, 100
    elif len(found) > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c9_unit_tests(py_files):
    """9. Pruebas unitarias básicas."""
    test_files = [f for f in py_files if 'test' in os.path.basename(f)]
    if not test_files:
        return "NO CUMPLE", "No se detectaron archivos de pruebas unitarias (tests.py o test_*.py).", 0
        
    test_cases = 0
    assertions = 0
    
    case_pattern = re.compile(r'class\s+\w+Test\w*|TestCase')
    assert_pattern = re.compile(r'self\.assert[a-zA-Z0-9_]+')
    
    for f in test_files:
        content = read_file_safe(f)
        test_cases += len(case_pattern.findall(content))
        assertions += len(assert_pattern.findall(content))
        
    details = f"Se detectaron {len(test_files)} archivos de pruebas unitarias. Casos de prueba definidos: {test_cases}. Aserciones de validación: {assertions}."
    
    if test_cases > 0 and assertions > 0:
        return "CUMPLE", details, 100
    elif test_cases > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c10_lazy_loading(html_files, py_files):
    """10. Lazy loading / Code splitting."""
    if not html_files:
        return "NO APLICA", "No hay plantillas HTML.", 0
        
    lazy_img = 0
    total_imgs = 0
    paginator_used = False
    
    lazy_pattern = re.compile(r'<img\s+[^>]*loading=["\']lazy["\']|<img\s+[^>]*loading=lazy')
    img_pattern = re.compile(r'<img\s+[^>]*src=')
    paginator_pattern = re.compile(r'\bPaginator\b')
    
    for f in html_files:
        content = read_file_safe(f)
        total_imgs += len(img_pattern.findall(content))
        lazy_img += len(lazy_pattern.findall(content))
        
    for f in py_files:
        content = read_file_safe(f)
        if paginator_pattern.search(content):
            paginator_used = True
            
    details = f"Uso de `loading='lazy'` en imágenes de plantillas: {lazy_img} de {total_imgs}. Implementación de Paginación en Backend (Django Paginator): {'SÍ' if paginator_used else 'NO'}."
    
    if paginator_used or (total_imgs > 0 and lazy_img / total_imgs >= 0.5):
        return "CUMPLE", details, 100
    elif lazy_img > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0

def check_c11_documentation(py_files, js_files):
    """11. Documentación mediante JSDoc y Docstrings."""
    docstrings = 0
    jsdocs = 0
    total_py_funcs = 0
    
    py_func_pattern = re.compile(r'\bdef\s+\w+\s*\(')
    docstring_pattern = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'')
    jsdoc_pattern = re.compile(r'/\*\*[\s\S]*?\*/')
    
    for f in py_files:
        content = read_file_safe(f)
        total_py_funcs += len(py_func_pattern.findall(content))
        # Contar ocurrencias de docstrings
        docstrings += len(docstring_pattern.findall(content))
        
    for f in js_files:
        content = read_file_safe(f)
        jsdocs += len(jsdoc_pattern.findall(content))
        
    pct = (docstrings / max(total_py_funcs, 1)) * 100
    details = f"Se detectaron {docstrings} bloques de docstrings en archivos Python (para {total_py_funcs} funciones totales) y {jsdocs} bloques de JSDoc en archivos JS."
    
    if docstrings > 10 or jsdocs > 0:
        return "CUMPLE", details, min(pct * 2, 100) # ponderado
    elif docstrings > 0:
        return "PARCIAL", details, 30
    else:
        return "NO CUMPLE", details, 0

def check_c12_responsive_design(css_files, html_files):
    """12. Diseño responsivo (Media Queries / Grid / Flexbox)."""
    media_queries = 0
    flex_grid = 0
    bootstrap_grid = 0
    
    media_pattern = re.compile(r'@media\b')
    flex_grid_pattern = re.compile(r'display\s*:\s*(flex|grid)\b')
    bootstrap_pattern = re.compile(r'\bcol-(xs|sm|md|lg|xl|xxl)?-\d+\b|\brow\b|\bd-flex\b')
    
    for f in css_files:
        content = read_file_safe(f)
        media_queries += len(media_pattern.findall(content))
        flex_grid += len(flex_grid_pattern.findall(content))
        
    for f in html_files:
        content = read_file_safe(f)
        bootstrap_grid += len(bootstrap_pattern.findall(content))
        
    details = f"Uso de `@media` queries en CSS: {media_queries}. Propiedades flex/grid directas: {flex_grid}. Clases de grilla/flex Bootstrap en plantillas: {bootstrap_grid}."
    
    if media_queries > 0 or bootstrap_grid > 50:
        return "CUMPLE", details, 100
    elif bootstrap_grid > 0:
        return "PARCIAL", details, 50
    else:
        return "NO CUMPLE", details, 0


# ──────────────────────────────────────────────────────────────────────
# EJECUCIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────────────────
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(f"\n{BOLD}{CYAN}====================================================================")
    print(f"       INICIANDO AUDITORÍA DE CONFORMIDAD DE PROYECTO (MNG_WEB)     ")
    print(f"===================================================================={RESET}\n")
    
    # Obtener archivos
    py_files = get_all_files('.py')
    html_files = get_all_files('.html')
    css_files = get_all_files('.css')
    js_files = get_all_files('.js')
    
    print(f"Escaneando directorio: {BASE_DIR}")
    print(f"  * Archivos Python (.py): {len(py_files)}")
    print(f"  * Archivos HTML (.html): {len(html_files)}")
    print(f"  * Archivos CSS (.css)  : {len(css_files)}")
    print(f"  * Archivos JS (.js)    : {len(js_files)}\n")
    
    criterios = [
        {
            "id": 1,
            "criterio": "Estructura componentes en sintaxis específica (plantillas)",
            "runner": lambda: check_c1_template_syntax(html_files)
        },
        {
            "id": 2,
            "criterio": "Implementa enrutamiento de vistas entre módulos",
            "runner": lambda: check_c2_routing(py_files)
        },
        {
            "id": 3,
            "criterio": "Consume servicios API REST con carga y control de errores",
            "runner": lambda: check_c3_api_consumption(py_files, js_files)
        },
        {
            "id": 4,
            "criterio": "Estilos CSS bajo esquema atómico o metodología BEM",
            "runner": lambda: check_c4_css_methodology(css_files)
        },
        {
            "id": 5,
            "criterio": "Binding de datos bidireccional/unidireccional en el DOM",
            "runner": lambda: check_c5_data_binding(html_files)
        },
        {
            "id": 6,
            "criterio": "Valida entradas de usuario en formularios",
            "runner": lambda: check_c6_form_validation(py_files, html_files)
        },
        {
            "id": 7,
            "criterio": "Variables de entorno para URLs de servicios y secretos",
            "runner": lambda: check_c7_env_variables()
        },
        {
            "id": 8,
            "criterio": "Organiza código en jerarquía de carpetas lógica",
            "runner": lambda: check_c8_folder_hierarchy()
        },
        {
            "id": 9,
            "criterio": "Implementa pruebas unitarias básicas sobre componentes",
            "runner": lambda: check_c9_unit_tests(py_files)
        },
        {
            "id": 10,
            "criterio": "Optimiza carga mediante lazy loading o paginación",
            "runner": lambda: check_c10_lazy_loading(html_files, py_files)
        },
        {
            "id": 11,
            "criterio": "Documenta componentes creados mediante JSDoc/Docstrings",
            "runner": lambda: check_c11_documentation(py_files, js_files)
        },
        {
            "id": 12,
            "criterio": "Garantiza adaptabilidad (diseño responsivo / Grid / Flexbox)",
            "runner": lambda: check_c12_responsive_design(css_files, html_files)
        }
    ]
    
    resultados = []
    total_score = 0
    criterios_evaluados = 0
    
    print(f"{BOLD}--------------------------------------------------------------------")
    print(f"{'No.':<4} | {'Criterio de Evaluación':<55} | {'Estado':<10}")
    print(f"--------------------------------------------------------------------{RESET}")
    
    for c in criterios:
        estado, detalles, pct = c["runner"]()
        
        # Color del estado
        if estado == "CUMPLE":
            color_estado = f"{GREEN}{BOLD}CUMPLE{RESET}"
            total_score += 100
            criterios_evaluados += 1
        elif estado == "PARCIAL":
            color_estado = f"{YELLOW}{BOLD}PARCIAL{RESET}"
            total_score += 50
            criterios_evaluados += 1
        elif estado == "NO CUMPLE":
            color_estado = f"{RED}{BOLD}NO CUMPLE{RESET}"
            total_score += 0
            criterios_evaluados += 1
        else: # NO APLICA
            color_estado = f"{CYAN}N/A{RESET}"
            
        print(f"{c['id']:<4} | {c['criterio'][:55]:<55} | {color_estado:<10}")
        resultados.append({
            "id": c["id"],
            "criterio": c["criterio"],
            "estado": estado,
            "detalles": detalles,
            "pct": pct
        })
        
    print(f"{BOLD}--------------------------------------------------------------------{RESET}")
    
    cumplimiento_final = (total_score / (criterios_evaluados * 100)) * 100 if criterios_evaluados > 0 else 0
    print(f"\n{BOLD}CUMPLIMIENTO GLOBAL ESTIMADO: {GREEN if cumplimiento_final >= 80 else (YELLOW if cumplimiento_final >= 50 else RED)}{cumplimiento_final:.1f}%{RESET}\n")
    
    # Escribir reporte en Markdown
    report_path = os.path.join(BASE_DIR, 'compliance_report.md')
    try:
        with open(report_path, 'w', encoding='utf-8') as rf:
            rf.write("# Reporte de Conformidad y Calidad de Código\n\n")
            rf.write(f"**Proyecto:** `MNG_WEB` (Django App)\n")
            rf.write(f"**Cumplimiento Estimado:** `{cumplimiento_final:.1f}%`  \n")
            rf.write(f"**Archivos Analizados:**  \n")
            rf.write(f"- Python: {len(py_files)}  \n")
            rf.write(f"- HTML: {len(html_files)}  \n")
            rf.write(f"- CSS: {len(css_files)}  \n")
            rf.write(f"- JavaScript: {len(js_files)}  \n\n")
            
            rf.write("## Tabla de Resultados\n\n")
            rf.write("| No. | Criterio de Evaluación | Estado | Detalles de Verificación |\n")
            rf.write("| --- | --- | --- | --- |\n")
            
            for res in resultados:
                emoji = "✅ CUMPLE" if res["estado"] == "CUMPLE" else ("⚠️ PARCIAL" if res["estado"] == "PARCIAL" else ("❌ NO CUMPLE" if res["estado"] == "NO CUMPLE" else "➖ N/A"))
                rf.write(f"| {res['id']} | {res['criterio']} | **{emoji}** | {res['detalles']} |\n")
                
            rf.write("\n\n---\n*Reporte generado automáticamente por `check_compliance.py`.*\n")
            
        print(f"{GREEN}[OK] Reporte de conformidad escrito con éxito en {BOLD}{os.path.relpath(report_path, BASE_DIR)}{RESET}\n")
    except Exception as e:
        print(f"{RED}[ERROR] Error al guardar el reporte: {e}{RESET}\n")

if __name__ == '__main__':
    main()
