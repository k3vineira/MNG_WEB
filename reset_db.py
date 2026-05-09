import os

# --- CONFIGURACIÓN ---
# ¡ATENCIÓN APRENDIZ! Verifica que el nombre de tu entorno virtual sea exactamente este.
# Si le pusiste otro nombre (ej. 'env', 'entorno'), cámbialo en la variable de abajo.
VENV_DIR = '.venv'
DB_FILE = 'db.sqlite3'
archivos_a_borrar = []

print("\n=== HERRAMIENTA DE RESETEO DE MIGRACIONES Y BASE DE DATOS ===")
print(f"Nota: Se ignorará la carpeta del entorno virtual: '{VENV_DIR}'")

# 1. Buscar archivos de migración recursivamente
for root, dirs, files in os.walk('.'):
    # Ignorar la carpeta del entorno virtual para no dañarlo
    if VENV_DIR in dirs:
        dirs.remove(VENV_DIR)
    
    # Buscar solo dentro de carpetas llamadas 'migrations'
    if 'migrations' in root:
        for file in files:
            # Seleccionar archivos que empiecen con '000' y terminen en '.py'
            if file.startswith('000') and file.endswith('.py'):
                archivos_a_borrar.append(os.path.join(root, file))

# 2. Verificar si existe la base de datos
db_existe = os.path.exists(DB_FILE)

# 3. Mostrar resumen al usuario
print(f"\nSe encontraron {len(archivos_a_borrar)} archivos de migración:")
for archivo in archivos_a_borrar:
    print(f" - {archivo}")

if db_existe:
    print(f"\nTambién se encontró la base de datos: {DB_FILE}")
else:
    print(f"\nNo se encontró la base de datos '{DB_FILE}' (ya fue borrada o no existe).")

if len(archivos_a_borrar) == 0 and not db_existe:
    print("\nNo hay nada que borrar. ¡El proyecto ya está limpio!")
    exit()

# 4. Pedir confirmación por seguridad
respuesta = input("\n¿Estás seguro de que deseas ELIMINAR estos archivos? Esta acción NO se puede deshacer. (s/n): ")

if respuesta.lower() == 's':
    # Borrar migraciones
    for archivo in archivos_a_borrar:
        os.remove(archivo)
        print(f"Borrado: {archivo}")
    
    # Borrar base de datos
    if db_existe:
        os.remove(DB_FILE)
        print(f"Borrado: {DB_FILE}")
    
    print("\n✅ ¡Limpieza completada exitosamente! Tu proyecto está listo para el nuevo AbstractUser.")
else:
    print("\n🚫 Operación cancelada. No se borró ningún archivo.")