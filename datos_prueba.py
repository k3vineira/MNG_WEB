import os
import django

# 1. Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from catalogo.models import Categoria, Actividades, Paquete, PaqueteActividad
# Si tienes Blog y PQRS en 'comunidad', asegúrate de que los nombres de campos coincidan
# from comunidad.models import Blog, PQRS 

def cargar_datos_mongua():
    print("🚀 Iniciando carga de datos para la Agencia Mongua...")

    # --- 1. CATEGORÍAS ---
    cat_eco, _ = Categoria.objects.get_or_create(
        nombre="Ecoturismo", 
        defaults={'descripcion': 'Contacto directo con la naturaleza de Mongua.', 'estado': True}
    )
    cat_cul, _ = Categoria.objects.get_or_create(
        nombre="Cultura y Fe", 
        defaults={'descripcion': 'Recorridos por iglesias y sitios históricos.', 'estado': True}
    )

    # --- 2. ACTIVIDADES ---
    act1, _ = Actividades.objects.get_or_create(
        nombre="Senderismo Laguna Negra",
        defaults={
            'descripcion': 'Caminata por el ecosistema de páramo.',
            'nivel_dificultad': 'Media',
            'equipo_requerimiento': 'Botas pantaneras, impermeable',
            'recomendacion_salud': 'No apto para personas con problemas respiratorios graves.'
        }
    )
    act2, _ = Actividades.objects.get_or_create(
        nombre="Avistamiento de Cóndores",
        defaults={
            'descripcion': 'Observación de aves en los riscos.',
            'nivel_dificultad': 'Baja',
            'equipo_requerimiento': 'Binoculares',
            'recomendacion_salud': 'Ninguna especial.'
        }
    )

    # --- 3. PAQUETES TURÍSTICOS ---
    paquete, created = Paquete.objects.get_or_create(
        nombre="Expedición Páramo de Mongua",
        defaults={
            'descripcion': 'Un viaje inolvidable al corazón de Boyacá.',
            'precio': 180000,
            'duracion_estimada': '8 horas',
            'punto_encuentro': 'Plaza Principal de Mongua',
            'codigo_categoria': cat_eco
        }
    )

    # --- 4. ASIGNAR ACTIVIDADES (Uso de la tabla through) ---
    if created:
        # Al usar 'through', creamos las relaciones en la tabla intermedia
        PaqueteActividad.objects.get_or_create(codigo_paquete=paquete, codigo_actividad=act1)
        PaqueteActividad.objects.get_or_create(codigo_paquete=paquete, codigo_actividad=act2)
        print(f"✅ Paquete '{paquete.nombre}' creado con sus actividades.")
    else:
        print(f"ℹ️ El paquete '{paquete.nombre}' ya existía.")

    print("\n✨ Proceso finalizado. Ahora tienes datos reales para probar tu panel admin.")

if __name__ == '__main__':
    cargar_datos_mongua()
