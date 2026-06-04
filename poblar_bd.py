import os
import django
import random
from datetime import timedelta, date
from django.utils import timezone
from decimal import Decimal
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
    
    # Nombres de temporadas reales y turísticas para Mongua
    nombres_temporadas = [
        "Vacaciones de Mitad de Año",
        "Temporada Eco-Verano",
        "Puentes de Agosto",
        "Aventura de Septiembre",
        "Semana de Receso Escolar",
        "Ecoturismo de Fin de Otoño",
        "Puentes de Noviembre",
        "Pre-Navidad Turística",
        "Inicio de Temporada Decembrina",
        "Fiestas de Fin de Año"
    ]

    # Fechas consecutivas fijas desde junio hasta diciembre de 2026
    fechas_temporadas = [
        (date(2026, 6, 4),   date(2026, 7, 15)),   # Vacaciones de Mitad de Año (Empieza Hoy)
        (date(2026, 7, 16),  date(2026, 8, 15)),   # Temporada Eco-Verano
        (date(2026, 8, 16),  date(2026, 8, 31)),   # Puentes de Agosto
        (date(2026, 9, 1),   date(2026, 9, 30)),   # Aventura de Septiembre
        (date(2026, 10, 1),  date(2026, 10, 15)),  # Semana de Receso Escolar
        (date(2026, 10, 16), date(2026, 10, 31)),  # Ecoturismo de Fin de Otoño
        (date(2026, 11, 1),  date(2026, 11, 16)),  # Puentes de Noviembre
        (date(2026, 11, 17), date(2026, 11, 30)),  # Pre-Navidad Turística
        (date(2026, 12, 1),  date(2026, 12, 15)),  # Inicio de Temporada Decembrina
        (date(2026, 12, 16), date(2026, 12, 31)),  # Fiestas de Fin de Año
    ]

    print("1. Creando Usuarios, Clientes y Guías...")
    # Crear usuario administrador solicitado
    try:
        user, created = Usuario.objects.get_or_create(
            username='a@b.com',
            defaults={
                'email': 'a@b.com',
                'first_name': 'Administrador',
                'last_name': 'Monagua',
                'is_staff': True,
                'is_superuser': True,
                'rol': Usuario.Roles.ADMIN
            }
        )
        if created:
            user.set_password('@dmin123')
            user.save()
            print("Administrador a@b.com creado con éxito.")
        else:
            # Si ya existe, actualizamos la contraseña por si acaso
            user.set_password('@dmin123')
            user.is_staff = True
            user.is_superuser = True
            user.rol = Usuario.Roles.ADMIN
            user.save()
            print("Administrador a@b.com actualizado con éxito.")
    except Exception as e:
        print(f"Error al crear/actualizar administrador: {e}")

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
            hora_encuentro=timezone.now().time(),
            categoria=random.choice(categorias_creadas)
        )
        p.actividades.add(*random.sample(actividades_creadas, 2))
        paquetes_creados.append(p)


    temporada_estandar = Temporada.objects.create(
        nombre="Temporada Estándar 2026",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        estado='activa'
    )

    temporadas_creadas = []
    for i in range(len(nombres_temporadas)):
        estado_inicial = 'activa' if i == 0 else 'programada'
        t = Temporada.objects.create(
            nombre=f"{nombres_temporadas[i]} 2026",
            fecha_inicio=fechas_temporadas[i][0],
            fecha_fin=fechas_temporadas[i][1],
            estado=estado_inicial
        )
        temporadas_creadas.append(t)


    tarifas_creadas = []
    for i in range(10):
      
        tarifa_especial = Tarifa.objects.create(
            paquete=paquetes_creados[i],
            temporada=temporadas_creadas[i],
            precio_adulto=Decimal(str(random.randint(350000, 600000))), 
            precio_menor=Decimal(str(random.randint(200000, 300000))),
            estado='activa'
        )
        tarifas_creadas.append(tarifa_especial)

        tarifa_base = Tarifa.objects.create(
            paquete=paquetes_creados[i],
            temporada=temporada_estandar, 
            precio_adulto=Decimal(str(random.randint(150000, 300000))), 
            precio_menor=Decimal(str(random.randint(80000, 140000))),
            estado='activa'
        )
        tarifas_creadas.append(tarifa_base)


    print("4. Creando Reservas y Cancelaciones...")
    reservas_creadas = []
    estados_reserva = ['pendiente', 'confirmada', 'cancelada']
    combinaciones_unicas = set()

    for tarifa_asociada in tarifas_creadas:
       
        fecha_reserva = tarifa_asociada.temporada.fecha_inicio + timedelta(days=2)
        usuario_aleatorio = random.choice(clientes_creados).usuario
        paquete_asociado = tarifa_asociada.paquete

        identificador = (usuario_aleatorio.id, paquete_asociado.id, fecha_reserva)

        if identificador in combinaciones_unicas:
            continue
            
        combinaciones_unicas.add(identificador)
        estado = random.choice(estados_reserva)
        
        r = Reserva.objects.create(
            usuario=usuario_aleatorio,
            paquete=paquete_asociado,
            fecha=fecha_reserva,
            numero_adultos=random.randint(1, 4),
            numero_menores=random.randint(0, 3),
            estado=estado
        )
        reservas_creadas.append(r)

        if estado == 'cancelada':
            Cancelacion.objects.create(
                reserva=r,
                motivo="Imprevisto de última hora",
                penalidad=Decimal(str(random.randint(0, 50000)))
            )

    print("5. Creando Comunidad (Calificaciones, Blog y PQRS)...")
    for i in range(10):
        Blog.objects.create(
            titulo=f"Artículo de interés {i+1}",
            contenido="Este es el contenido de un artículo muy interesante sobre turismo y viajes.",
            publicado=True
        )

        PQRS.objects.create(
            cliente=random.choice(clientes_creados),
            tipo=random.choice(['peticion', 'queja', 'reclamo', 'sugerencia']),
            asunto=f"Asunto de prueba {i+1}",
            descripcion="Esta es una descripción detallada de la solicitud del cliente.",
            estado=random.choice(['abierto', 'en_proceso', 'cerrado'])
        )

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