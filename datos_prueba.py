import os
import django

# 1. Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importamos los modelos necesarios
from catalogo.models import Categoria, Actividades, Paquete, PaqueteActividad
from comunidad.models import Blog  # Asegúrate de que tu app se llame 'comunidad'

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

    # --- 3. PAQUETES TURÍSTICOS ---
    paquete, created = Paquete.objects.get_or_create(
        nombre="Expedición Páramo de Mongua",
        defaults={
            'descripcion': 'Un viaje inolvidable al corazón de Boyacá.',
            'precio': 180000,
            'duracion_estimada': '8 horas',
            'punto_encuentro': 'Plaza Principal de Mongua',
            'categoria': cat_eco
        }
    )

    if created:
        PaqueteActividad.objects.get_or_create(paquete=paquete, actividad=act1)
        print(f"✅ Paquete '{paquete.nombre}' creado.")

    # --- 4. BLOGS (NUEVA SECCIÓN) ---
    print("\n📝 Cargando artículos del Blog...")
    
    # Artículo 1: Publicado
    blog1, created1 = Blog.objects.get_or_create(
        titulo="Laguna Negra: El espejo de Mongua",
        defaults={
            'contenido': 'La Laguna Negra es un destino místico en el Páramo de Ocetá. Sus aguas oscuras reflejan la paz de la montaña...',
            'publicado': True  # Aparecerá en la web
        }
    )
    if created1: print(f"✅ Blog '{blog1.titulo}' creado como PUBLICADO.")

    # Artículo 2: Borrador (No publicado)
    blog2, created2 = Blog.objects.get_or_create(
        titulo="Tips para visitar el Páramo",
        defaults={
            'contenido': 'Contenido en desarrollo sobre qué ropa llevar y cómo cuidar el ecosistema de frailejones.',
            'publicado': False  # Aparecerá como "Borrado" en tu panel
        }
    )
    if created2: print(f"✅ Blog '{blog2.titulo}' creado como BORRADOR (No publicado).")

    print("\n✨ Proceso finalizado con éxito.")

if __name__ == '__main__':
    cargar_datos_mongua()
