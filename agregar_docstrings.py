import os
import re

# Carpeta raíz del proyecto
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Expresión regular para detectar funciones
DEF_PATTERN = re.compile(r'^(\s*)def\s+(\w+)\((.*?)\):\s*$')


def tiene_docstring(lineas, indice):
    """
    Verifica si la línea siguiente a un def ya contiene un docstring.
    """
    i = indice + 1

    while i < len(lineas):
        texto = lineas[i].strip()

        if texto == "":
            i += 1
            continue

        return texto.startswith('"""') or texto.startswith("'''")

    return False


def crear_docstring(indentacion, nombre_funcion, parametros):
    """
    Genera un docstring básico.
    """
    espacios = indentacion + "    "

    doc = []
    doc.append(f'{espacios}"""')
    doc.append(f'{espacios}{nombre_funcion}.')

    if parametros.strip():
        for parametro in parametros.split(","):
            parametro = parametro.strip()

            if parametro in ("self", "cls"):
                continue

            if parametro.startswith("**"):
                parametro = parametro[2:]
            elif parametro.startswith("*"):
                parametro = parametro[1:]

            doc.append(f'{espacios}')
            doc.append(f'{espacios}:param {parametro}: Descripción del parámetro.')

    doc.append(f'{espacios}')
    doc.append(f'{espacios}:return: Respuesta de la función.')
    doc.append(f'{espacios}"""')

    return doc


def procesar_archivo(ruta):
    """
    procesar_archivo.
    
    :param ruta: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas = []
    cambios = 0

    i = 0
    while i < len(lineas):
        linea = lineas[i]
        nuevas.append(linea)

        coincidencia = DEF_PATTERN.match(linea)

        if coincidencia:
            indentacion = coincidencia.group(1)
            nombre = coincidencia.group(2)
            parametros = coincidencia.group(3)

            if not tiene_docstring(lineas, i):
                nuevas.extend(
                    x + "\n"
                    for x in crear_docstring(indentacion, nombre, parametros)
                )
                cambios += 1

        i += 1

    if cambios:
        with open(ruta, "w", encoding="utf-8") as f:
            f.writelines(nuevas)

    return cambios


total = 0

for carpeta, _, archivos in os.walk(ROOT_DIR):

    # Ignorar carpetas
    if any(x in carpeta for x in [
        "venv",
        ".venv",
        "__pycache__",
        "migrations",
        ".git"
    ]):
        continue

    for archivo in archivos:
        if archivo.endswith(".py"):
            ruta = os.path.join(carpeta, archivo)
            agregados = procesar_archivo(ruta)

            if agregados:
                print(f"{ruta} -> {agregados} docstrings agregados")
                total += agregados

print(f"\nProceso terminado.")
print(f"Total de docstrings agregados: {total}")