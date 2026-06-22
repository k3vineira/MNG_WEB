"""
refactor_render.py
==================
Herramienta de auditoría de calidad de código para proyectos Django.

Escanea todos los archivos views.py del proyecto y detecta llamadas a
render() que usan un diccionario literal inline en lugar de una variable
`context` separada.

Uso:
    python .\refactor_render.py

Modos:
    Solo lectura (por defecto): reporta problemas sin modificar archivos.
    Automático (--fix):         corrige automáticamente los renders detectados.
"""

import os
import re
import sys
import ast
import textwrap

# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────

# Directorio raíz del proyecto (donde está este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpetas que NO se deben escanear
EXCLUDED_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', 'env',
    'node_modules', 'migrations', 'static', 'media',
    '.gemini', 'staticfiles',
}

# Patrón: return render(request, '...', { ...
#   Detecta dict literal directamente en el tercer argumento del render
RENDER_DICT_PATTERN = re.compile(
    r'return\s+render\s*\(\s*\w+\s*,\s*[\'"][^\'"]+[\'"]\s*,\s*\{'
)

# Separador visual
SEP = '-' * 50


# ──────────────────────────────────────────────
# Funciones principales
# ──────────────────────────────────────────────

def encontrar_views(base_dir: str) -> list[str]:
    """Recorre recursivamente el proyecto y retorna rutas de archivos views.py."""
    archivos = []
    for raiz, dirs, ficheros in os.walk(base_dir):
        # Excluir carpetas no deseadas (modificar dirs in-place para que os.walk las omita)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fichero in ficheros:
            if fichero == 'views.py':
                archivos.append(os.path.join(raiz, fichero))
    return sorted(archivos)


def auditar_archivo(ruta: str) -> list[int]:
    """
    Analiza un archivo views.py línea por línea.
    Retorna una lista con los números de línea que tienen render() con dict literal.
    """
    lineas_problema = []
    try:
        with open(ruta, encoding='utf-8') as f:
            for num, linea in enumerate(f, start=1):
                if RENDER_DICT_PATTERN.search(linea):
                    lineas_problema.append(num)
    except (OSError, UnicodeDecodeError) as e:
        print(f'  [ERROR] No se pudo leer {ruta}: {e}')
    return lineas_problema


def ruta_relativa(ruta: str) -> str:
    """Retorna la ruta relativa al BASE_DIR con prefijo .\\"""
    rel = os.path.relpath(ruta, BASE_DIR)
    return f'.\\{rel}'


def contar_renders(ruta: str) -> tuple[int, int]:
    """
    Cuenta el total de 'return render' en el archivo y cuántos usan diccionario.
    Retorna (total_renders, renders_con_dict).
    """
    total = 0
    con_dict = 0
    patron_total = re.compile(r'return\s+render\s*\(')
    try:
        with open(ruta, encoding='utf-8') as f:
            for linea in f:
                if patron_total.search(linea):
                    total += 1
                    if RENDER_DICT_PATTERN.search(linea):
                        con_dict += 1
    except (OSError, UnicodeDecodeError):
        pass
    return total, con_dict


# ──────────────────────────────────────────────
# Modo --fix (corrección automática)
# ──────────────────────────────────────────────

def corregir_archivo(ruta: str, lineas_problema: list[int]) -> int:
    """
    Corrige automáticamente las líneas detectadas reemplazando el dict literal
    por una variable `context` definida antes del return.
    Retorna la cantidad de correcciones realizadas.
    """
    try:
        with open(ruta, encoding='utf-8') as f:
            contenido = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f'  [ERROR] No se pudo leer {ruta}: {e}')
        return 0

    # Patrón completo para capturar render con dict multilínea
    patron = re.compile(
        r'(\s*)(return\s+render\s*\(\s*(\w+)\s*,\s*([\'"][^\'"]+[\'"])\s*,\s*)(\{[^}]*\})\s*(\))',
        re.DOTALL
    )

    correcciones = 0

    def reemplazar(m):
        nonlocal correcciones
        indentacion = m.group(1)
        request_var = m.group(3)
        template = m.group(4)
        dict_literal = m.group(5)
        correcciones += 1
        return (
            f'{indentacion}context = {dict_literal}\n'
            f'{indentacion}return render({request_var}, {template}, context)'
        )

    nuevo_contenido = patron.sub(reemplazar, contenido)

    if correcciones > 0:
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(nuevo_contenido)
        except OSError as e:
            print(f'  [ERROR] No se pudo escribir {ruta}: {e}')
            return 0

    return correcciones


# ──────────────────────────────────────────────
# Ejecución principal
# ──────────────────────────────────────────────

def main():
    modo_fix = '--fix' in sys.argv

    print(SEP)

    archivos = encontrar_views(BASE_DIR)

    total_archivos = len(archivos)
    total_renders = 0
    renders_dict = 0        # con dict literal (ALERTA)
    renders_variable = 0    # con variable context (OK)
    archivos_alerta = 0
    correcciones_totales = 0

    for ruta in archivos:
        rel = ruta_relativa(ruta)
        lineas = auditar_archivo(ruta)
        t_renders, t_dict = contar_renders(ruta)

        total_renders += t_renders
        renders_dict += t_dict
        renders_variable += (t_renders - t_dict)

        if lineas:
            archivos_alerta += 1
            print(f'[ALERTA] {rel}: Tiene {len(lineas)} render(s) en las líneas {lineas}.')
            if modo_fix:
                n = corregir_archivo(ruta, lineas)
                correcciones_totales += n
                if n:
                    print(f'         ✔ {n} corrección(es) aplicadas automáticamente.')
        else:
            print(f'[OK]     {rel}: {t_renders} render(s) correctos.')

    print(SEP)
    print()

    modo_label = '(CORREGIDO)' if modo_fix else '(SOLO LECTURA)'
    print(f'REPORTE FINAL {modo_label}:')
    print(f'  Archivos Python escaneados  : {total_archivos}')
    print(f"  Total de 'return render'    : {total_renders}")
    print(f'  Renders usando diccionario  : {renders_dict}')
    print(f'  Renders correctos (variable): {renders_variable}')

    if modo_fix and correcciones_totales:
        print(f'  Correcciones aplicadas      : {correcciones_totales}')

    print()

    if archivos_alerta == 0:
        print('[LISTO] Todo en orden. No hay renders con dict literal.')
    else:
        if modo_fix:
            print(f'[CORREGIDO] Se corrigieron {archivos_alerta} archivo(s) automaticamente.')
        else:
            print(
                f'[ATENCION] Se encontraron {archivos_alerta} archivo(s) con renders a corregir.\n'
                f'   Ejecuta  python .\\refactor_render.py --fix  para corregirlos automaticamente.'
            )


if __name__ == '__main__':
    main()
