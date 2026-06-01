import os
from pathlib import Path

def gestionar_limpieza():
    # Directorio actual donde se encuentra este script
    directorio_raiz = Path(__file__).parent.resolve()
    
    # Carpetas que el script ignorará por completo
    carpetas_ignoradas = {'.venv', 'venv', '.git', '__pycache__'}
    
    archivos_encontrados = []
    
    print(f"Escaneando proyecto en: {directorio_raiz}...")

    # os.walk permite modificar 'dirs' para saltar carpetas antes de entrar en ellas
    for raiz, dirs, archivos in os.walk(directorio_raiz):
        # Filtramos las carpetas ignoradas
        dirs[:] = [d for d in dirs if d not in carpetas_ignoradas]

        for nombre_archivo in archivos:
            # Filtro: inicia con 000 y es archivo .py
            if nombre_archivo.startswith('000') and nombre_archivo.endswith('.py'):
                # Evitar que el script se auto-seleccione si coincide con el patrón
                if nombre_archivo != Path(__file__).name:
                    ruta_completa = Path(raiz) / nombre_archivo
                    archivos_encontrados.append(ruta_completa)

    total = len(archivos_encontrados)

    if total == 0:
        print("\nNo se encontraron archivos que coincidan (fuera de entornos virtuales).")
        return

    # Listado de archivos encontrados
    print(f"\n--- {total} ARCHIVOS IDENTIFICADOS ---")
    for idx, archivo in enumerate(archivos_encontrados, 1):
        # Mostramos la ruta relativa para mayor claridad
        print(f"{idx}. {archivo.relative_to(directorio_raiz)}")
    
    print("-" * 50)

    # Proceso de purga
    confirmacion = input(f"\n¿Confirmas la eliminación de estos {total} archivos? (s/n): ")
    
    if confirmacion.lower() == 's':
        eliminados = 0
        for archivo in archivos_encontrados:
            try:
                archivo.unlink()
                eliminados += 1
            except Exception as e:
                print(f"Error al eliminar {archivo.name}: {e}")
        
        print(f"\nOperación finalizada. Se eliminaron {eliminados} archivos.")
    else:
        print("\nOperación cancelada. Tus archivos están intactos.")

if __name__ == "__main__":
    gestionar_limpieza()