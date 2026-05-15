import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from usuarios.models import Usuario, Cliente, GuiaTuristico
from catalogo.models import Categoria, Actividades, Paquete, Temporada, Tarifa
from reservas.models import Reserva, Cancelacion
from comunidad.models import Calificacion, Blog, PQRS

def poblar_base_datos():
    print("Iniciando el poblado de la base de datos...")
    print("0. Limpiando la base de datos...")
    PQRS.objects.all().delete()
    Blog.objects.all().delete()
    Calificacion.objects.all().delete()
    Cancelacion.objects.all().delete()
    Reserva.objects.all().delete()
    Tarifa.objects.all().delete()
    Temporada.objects.all().delete()
    Paquete.objects.all().delete()
    Actividades.objects.all().delete()
    Categoria.objects.all().delete()
    GuiaTuristico.objects.all().delete()
    Cliente.objects.all().delete()
    Usuario.objects.exclude(is_superuser=True).delete()

    # Listas de datos falsos
    nombres = ['Carlos', 'Ana', 'Luis', 'Marta', 'Pedro', 'Sofia', 'Jorge', 'Lucia', 'Diego', 'Elena']
    apellidos = ['Gomez', 'Perez', 'Rodriguez', 'Lopez', 'Martinez', 'Garcia', 'Sanchez', 'Diaz', 'Torres', 'Ramirez']
    ciudades = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Cúcuta', 'Bucaramanga', 'Pereira', 'Santa Marta', 'Manizales']
    paises = ['Colombia', 'México', 'Argentina', 'Chile', 'Perú', 'España', 'Ecuador', 'Panamá', 'Costa Rica', 'Brasil']
    categorias_nombres = ['Aventura', 'Ecoturismo', 'Cultural', 'Playa', 'Montaña', 'Gastronómico', 'Histórico', 'Relajación', 'Deportivo', 'Familiar']
    actividades_nombres = ['Senderismo', 'Buceo', 'Museos', 'Escalada', 'Ciclismo', 'Cata de Vinos', 'Surf', 'Avistamiento de Aves', 'Rappel', 'Canotaje']
    
    print("1. Creando Usuarios, Clientes y Guías...")
    clientes_creados = []
    guias_creados = []
    
    # Crear 10 Clientes
    for i in range(10):
        username = f"cliente_{i}_{random.randint(1000, 9999)}"
        u = Usuario.objects.create_user(
            username=username,
            password='password123',
            first_name=nombres[i],
            last_name=apellidos[i],
            email=f"{username}@ejemplo.com",
            rol=Usuario.Roles.CLIENTE,
            tipo_documento=Usuario.TipoDocumento.CC,
            numero_documento=f"1000{i}{random.randint(100,999)}",
            residencia=f"{ciudades[i]}, {paises[i]}"
        )
        c = Cliente.objects.create(usuario=u, pais=paises[i], ciudad=ciudades[i])
        clientes_creados.append(c)

    # Crear 10 Guías
    for i in range(10):
        username = f"guia_{i}_{random.randint(1000, 9999)}"
        u = Usuario.objects.create_user(
            username=username,
            password='password123',
            first_name=nombres[9-i],
            last_name=apellidos[9-i],
            email=f"{username}@ejemplo.com",
            rol=Usuario.Roles.GUIA,
            tipo_documento=Usuario.TipoDocumento.CC,
            numero_documento=f"2000{i}{random.randint(100,999)}",
            residencia=f"{ciudades[i]}, {paises[i]}"
        )
        g = GuiaTuristico.objects.create(
            usuario=u, 
            licencia_turismo=f"LIC-{random.randint(10000, 99999)}",
            experiencia_anos=random.randint(1, 15),
            biografia="Guía profesional con amplia experiencia."
        )
        guias_creados.append(g)

    print("2. Creando Categorías y Actividades...")
    categorias_creadas = []
    for i in range(10):
        cat = Categoria.objects.create(
            nombre=categorias_nombres[i],
            descripcion=f"Descripción para la categoría {categorias_nombres[i]}"
        )
        categorias_creadas.append(cat)

    actividades_creadas = []
    niveles = ['Alta', 'Media', 'Baja']
    for i in range(10):
        act = Actividades.objects.create(
            nombre=actividades_nombres[i],
            descripcion=f"Descripción de la actividad {actividades_nombres[i]}",
            nivel_dificultad=random.choice(niveles),
            equipo_requerimiento="Ropa cómoda e hidratación",
            recomendacion_salud="Buena condición física",
            apto_para_menores=random.choice([True, False])
        )
        actividades_creadas.append(act)

    print("3. Creando Paquetes, Temporadas y Tarifas...")
    paquetes_creados = []
    for i in range(10):
        p = Paquete.objects.create(
            nombre=f"Paquete {ciudades[i]} Mágico",
            descripcion=f"Un increíble viaje por {ciudades[i]}.",
            dias_duracion=random.randint(2, 7),
            noches_duracion=random.randint(1, 6),
            punto_encuentro="Plaza principal",
            categoria=random.choice(categorias_creadas)
        )
        # Asignar 2 actividades aleatorias al paquete
        p.actividades.add(*random.sample(actividades_creadas, 2))
        paquetes_creados.append(p)

    temporadas_creadas = []
    for i in range(10):
        t = Temporada.objects.create(
            nombre=f"Temporada {i+1} 2026",
            fecha_inicio=timezone.now().date() + timedelta(days=i*30),
            fecha_fin=timezone.now().date() + timedelta(days=(i*30)+25)
        )
        temporadas_creadas.append(t)

    tarifas_creadas = []
    for i in range(10):
        tarifa = Tarifa.objects.create(
            paquete=paquetes_creados[i],
            temporada=temporadas_creadas[i],
            precio_adulto=random.randint(100000, 500000),
            precio_menor=random.randint(50000, 250000)
        )
        tarifas_creadas.append(tarifa)

    print("4. Creando Reservas y Cancelaciones...")
    reservas_creadas = []
    estados_reserva = ['pendiente', 'confirmada', 'completada', 'cancelada']
    for i in range(10):
        tarifa_asociada = tarifas_creadas[i]
        # Crear reserva que coincida con la fecha de la tarifa
        fecha_reserva = tarifa_asociada.temporada.fecha_inicio + timedelta(days=2)
        estado = random.choice(estados_reserva)
        
        r = Reserva(
            usuario=random.choice(clientes_creados).usuario,
            paquete=tarifa_asociada.paquete,
            fecha=fecha_reserva,
            numero_adultos=random.randint(1, 4),
            numero_menores=random.randint(0, 3),
            estado=estado
        )
        r.save() # El save() calculará el monto_total automáticamente
        reservas_creadas.append(r)

        if estado == 'cancelada':
            Cancelacion.objects.create(
                reserva=r,
                motivo="Imprevisto de última hora",
                penalidad=random.randint(0, 50000)
            )

    # Asegurar al menos 10 cancelaciones
    cancelaciones_actuales = Cancelacion.objects.count()
    if cancelaciones_actuales < 10:
        for _ in range(10 - cancelaciones_actuales):
            r = random.choice(reservas_creadas)
            # Solo crear si no tiene ya una cancelación
            if not hasattr(r, 'cancelacion'):
                r.estado = 'cancelada'
                r.save()
                Cancelacion.objects.create(
                    reserva=r,
                    motivo="Cancelación generada automáticamente",
                    penalidad=random.randint(10000, 30000)
                )

    print("5. Creando Comunidad (Calificaciones, Blog y PQRS)...")
    for i in range(10):
        # Blog
        Blog.objects.create(
            titulo=f"Artículo de interés {i+1}",
            contenido="Este es el contenido de un artículo muy interesante sobre turismo y viajes.",
            publicado=True
        )

        # PQRS
        PQRS.objects.create(
            cliente=random.choice(clientes_creados),
            tipo=random.choice(['peticion', 'queja', 'reclamo', 'sugerencia']),
            asunto=f"Asunto de prueba {i+1}",
            descripcion="Esta es una descripción detallada de la solicitud del cliente.",
            estado=random.choice(['abierto', 'en_proceso', 'cerrado'])
        )

    # Para calificaciones, usaremos combinaciones únicas de cliente-paquete
    combinaciones_calificacion = set()
    while len(combinaciones_calificacion) < 10:
        c = random.choice(clientes_creados)
        p = random.choice(paquetes_creados)
        if (c.id, p.id) not in combinaciones_calificacion:
            combinaciones_calificacion.add((c.id, p.id))
            Calificacion.objects.create(
                cliente=c,
                paquete=p,
                puntaje=random.randint(1, 5),
                comentario="¡Excelente experiencia, recomendada!"
            )

    print("¡Poblado de base de datos finalizado con éxito! Se han creado al menos 10 registros de cada entidad.")

if __name__ == '__main__':
    poblar_base_datos()
