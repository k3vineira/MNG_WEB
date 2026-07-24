import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from comunidad.models import Calificacion, Blog, PQRS, Comentario
from reservas.models import Reserva, Cancelacion
from catalogo.models import Categoria, Actividades, Paquete, Temporada, Tarifa
from usuarios.models import Usuario, Cliente, GuiaTuristico
from pagos.models import ComprobantePago
from promociones.models import Promocion
from notificaciones.models import Notificacion
import random
from datetime import timedelta, date, datetime
from django.utils import timezone
from decimal import Decimal

def generar_documento_unico(prefijo):
    while True:
        doc = f"{prefijo}{random.randint(100000, 999999)}"
        if not Usuario.objects.filter(numero_documento=doc).exists():
            return doc


def generar_email_unico(username):
    email = f"{username}@ejemplo.com"
    if not Usuario.objects.filter(email__iexact=email).exists():
        return email
    while True:
        email = f"{username}_{random.randint(10, 99)}@ejemplo.com"
        if not Usuario.objects.filter(email__iexact=email).exists():
            return email


def poblar_base_datos():
    """
    poblar_base_datos.
    
    :return: Respuesta de la función.
    """
    print("Iniciando el poblado de la base de datos...")
    print("0. Limpiando la base de datos...")
    
    Notificacion.objects.all().delete()
    ComprobantePago.objects.all().delete()
    Promocion.objects.all().delete()
    Comentario.objects.all().delete()
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
    Usuario.objects.all().delete()

    # Listas de datos falsos
    nombres = ['Carlos', 'Ana', 'Luis', 'Marta', 'Pedro',
               'Sofia', 'Jorge', 'Lucia', 'Diego', 'Elena']
    apellidos = ['Gomez', 'Perez', 'Rodriguez', 'Lopez',
                 'Martinez', 'Garcia', 'Sanchez', 'Diaz', 'Torres', 'Ramirez']
    ciudades = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
                'Cúcuta', 'Bucaramanga', 'Pereira', 'Santa Marta', 'Manizales']
    paises = ['Colombia', 'México', 'Argentina', 'Chile', 'Perú',
              'España', 'Ecuador', 'Panamá', 'Costa Rica', 'Brasil']
    departamentos = ['Bogotá D.C.', 'Estado de México', 'Buenos Aires', 'Santiago', 'Lima',
                    'Madrid', 'Pichincha', 'Panamá', 'San José', 'Río de Janeiro']
    categorias_nombres = ['Aventura', 'Ecoturismo', 'Cultural', 'Playa', 'Montaña',
                          'Gastronómico', 'Histórico', 'Relajación', 'Deportivo', 'Familiar']
    actividades_nombres = ['Senderismo', 'Buceo', 'Museos', 'Escalada', 'Ciclismo',
                           'Cata de Vinos', 'Surf', 'Avistamiento de Aves', 'Rappel', 'Canotaje']

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
        (date(2026, 6, 4),   date(2026, 7, 15)),   # Vacaciones de Mitad de Año
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

    # ─────────────────────────────────────────────
    # 1. USUARIOS, CLIENTES Y GUÍAS
    # ─────────────────────────────────────────────
    print("1. Creando Usuarios, Clientes y Guías...")

    clientes_creados = []
    guias_creados = []

    # Crear 10 Clientes
    telefonos_clientes = [
        '+573152345678', '+573201112233', '+573004567890',
        '+573129876543', '+573182223344', '+573015556677',
        '+573168889900', '+573223334455', '+573056667788',
        '+573194445566'
    ]
    for i in range(10):
        username = f"cliente_{i}_{random.randint(1000, 9999)}"
        u = Usuario.objects.create_user(
            username=username,
            password='password123',
            first_name=nombres[i],
            last_name=apellidos[i],
            email=generar_email_unico(username),
            rol=Usuario.Roles.CLIENTE,
            tipo_documento=Usuario.TipoDocumento.CC,
            numero_documento=generar_documento_unico(f"1000{i}"),
            telefono=telefonos_clientes[i],
            residencia=f"{ciudades[i]}, {paises[i]}"
        )
        c = Cliente.objects.create(
            usuario=u, pais=paises[i], departamento=departamentos[i], ciudad=ciudades[i])
        clientes_creados.append(c)

    # Crear 10 Guías (sin duplicados)
    biografias_guia = [
        "Guía certificado con más de 5 años de experiencia en senderismo de alta montaña y ecoturismo en la región de Boyacá.",
        "Apasionado por la naturaleza y la conservación ambiental. Especialista en avistamiento de aves y flora nativa.",
        "Profesional del turismo cultural con conocimiento profundo de la historia y tradiciones de Mongua.",
        "Experto en deportes de aventura incluyendo rappel, escalada y canotaje en ríos de montaña.",
        "Guía bilingüe (español-inglés) especializado en turismo gastronómico y experiencias culinarias locales.",
        "Fotógrafo naturalista y guía especializado en recorridos por la Laguna Negra y senderos ecológicos.",
        "Instructor certificado de senderismo nocturno y camping de alta montaña en el páramo de Mongua.",
        "Conocedor de rutas ancestrales y caminos reales. Especialista en turismo histórico y arqueológico.",
        "Guía de turismo familiar con experiencia en actividades recreativas para todas las edades.",
        "Especialista en turismo sostenible y comunitario, vinculando a los visitantes con las comunidades locales.",
    ]
    for i in range(10):
        username = f"guia_{i}_{random.randint(1000, 9999)}"
        u = Usuario.objects.create_user(
            username=username,
            password='password123',
            first_name=nombres[9 - i],
            last_name=apellidos[9 - i],
            email=generar_email_unico(username),
            rol=Usuario.Roles.GUIA,
            tipo_documento=Usuario.TipoDocumento.CC,
            numero_documento=generar_documento_unico(f"2000{i}"),
            telefono=f"+5731{random.randint(0,9)}{random.randint(1000000,9999999)}",
            residencia=f"{ciudades[i]}, Boyacá"
        )
        g = GuiaTuristico.objects.create(
            usuario=u,
            licencia_turismo=f"LIC-BOY-{random.randint(10000, 99999)}",
            experiencia_anos=random.randint(1, 15),
            biografia=biografias_guia[i]
        )
        guias_creados.append(g)

    print(f"  -> {len(clientes_creados)} clientes y {len(guias_creados)} guias creados.")

    # ─────────────────────────────────────────────
    # 2. CATEGORÍAS Y ACTIVIDADES
    # ─────────────────────────────────────────────
    print("2. Creando Categorías y Actividades...")
    categorias_creadas = []
    descripciones_categorias = [
        "Experiencias llenas de adrenalina y desafíos al aire libre.",
        "Turismo responsable en armonía con la naturaleza y el medio ambiente.",
        "Inmersión en la cultura, tradiciones y artesanías de la región.",
        "Disfruta del sol, la arena y las aguas cristalinas.",
        "Aventuras en las alturas del páramo y las montañas boyacenses.",
        "Degusta la riqueza culinaria local y los sabores ancestrales.",
        "Recorre los caminos y monumentos que cuentan la historia de Mongua.",
        "Espacios de bienestar, tranquilidad y conexión consigo mismo.",
        "Actividades deportivas para los amantes del ejercicio al aire libre.",
        "Planes diseñados para disfrutar en familia con actividades para todos.",
    ]
    for i in range(10):
        cat = Categoria.objects.create(
            nombre=categorias_nombres[i],
            descripcion=descripciones_categorias[i]
        )
        categorias_creadas.append(cat)

    actividades_creadas = []
    niveles = ['Alta', 'Media', 'Baja']
    descripciones_actividades = [
        "Recorridos guiados por senderos naturales con vistas panorámicas del páramo.",
        "Inmersión en aguas cristalinas para explorar la vida marina local.",
        "Visitas a museos locales con exhibiciones de arte e historia regional.",
        "Ascenso en paredes rocosas naturales con equipamiento profesional.",
        "Recorridos en bicicleta por rutas rurales y caminos de montaña.",
        "Degustación de vinos y bebidas artesanales de la región.",
        "Práctica de surf en las mejores olas de la costa colombiana.",
        "Observación de aves endémicas y migratorias en su hábitat natural.",
        "Descenso por cascadas y formaciones rocosas con cuerdas y arneses.",
        "Navegación en canoas por ríos de corriente moderada y rápidos suaves.",
    ]
    equipos = [
        "Botas de senderismo, bastones, hidratación",
        "Traje de neopreno, gafas, snorkel",
        "Ropa cómoda, cámara fotográfica",
        "Arnés, casco, guantes de escalada",
        "Bicicleta, casco, guantes, protecciones",
        "Ninguno especial",
        "Tabla de surf, lycra, protector solar",
        "Binoculares, guía de aves, ropa camuflada",
        "Arnés de rappel, casco, guantes",
        "Chaleco salvavidas, ropa impermeable",
    ]
    for i in range(10):
        act = Actividades.objects.create(
            nombre=actividades_nombres[i],
            descripcion=descripciones_actividades[i],
            nivel_dificultad=random.choice(niveles),
            equipo_requerimiento=equipos[i],
            recomendacion_salud="Buena condición física general. Consultar con médico en caso de condiciones especiales.",
            apto_para_menores=random.choice([True, False])
        )
        actividades_creadas.append(act)

    # ─────────────────────────────────────────────
    # 3. PAQUETES, TEMPORADAS Y TARIFAS
    # ─────────────────────────────────────────────
    print("3. Creando Paquetes, Temporadas y Tarifas...")
    paquetes_creados = []
    
    # Paquetes mapeados exactamente con sus imágenes correspondientes
    paquetes_config = [
        ("Mongua Mágico", "Un recorrido completo por los sitios más emblemáticos de Mongua, ideal para conocer la esencia del pueblo.", "img_Iglesia.webp"),
        ("Ruta del Páramo", "Expedición al páramo de Mongua con vistas panorámicas y flora endémica única en el mundo.", "paramo.webp"),
        ("Aventura Laguna Negra", "Aventura hacia la misteriosa Laguna Negra, un ecosistema único rodeado de leyendas y biodiversidad.", "lagunanegra.webp"),
        ("Senderos Ancestrales", "Caminata por los caminos reales que conectaban pueblos ancestrales, cargados de historia y misterio.", "img_rutas.webp"),
        ("Eco-Aventura Boyacense", "Experiencia de ecoturismo con actividades de bajo impacto ambiental en los bosques de Boyacá.", "paramo_oseta.webp"),
        ("Caminata del Amanecer", "Salida temprana para contemplar el amanecer desde los miradores naturales del páramo.", "miradorcumbre.webp"),
        ("Tour Gastronómico Mongua", "Descubre los sabores típicos de Mongua: arepas boyacenses, cuchuco, mazamorra y más.", "artesanias.webp"),
        ("Explorador de Montaña", "Programa de escalada y rappel en las formaciones rocosas naturales de la región.", "estatua_piedra.webp"),
        ("Relajación en la Naturaleza", "Jornada de bienestar y meditación en medio de los paisajes naturales más tranquilos.", "img_rio.webp"),
        ("Mongua en Familia", "Plan diseñado para familias con actividades recreativas, educativas y culturales para todos.", "iglesia.webp"),
    ]

    import shutil
    from django.conf import settings
    destinos_media_dir = os.path.join(settings.MEDIA_ROOT, 'destinos')
    os.makedirs(destinos_media_dir, exist_ok=True)

    for nombre, descripcion, img_name in paquetes_config:
        src_path = os.path.join(settings.BASE_DIR, 'static', 'img', img_name)
        dst_path = os.path.join(destinos_media_dir, img_name)
        imagen_path = None
        if os.path.exists(src_path):
            try:
                shutil.copy(src_path, dst_path)
                imagen_path = f"destinos/{img_name}"
            except Exception as e:
                print(f"Error al copiar imagen: {e}")

        p = Paquete.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            dias_duracion=random.randint(2, 7),
            noches_duracion=random.randint(1, 6),
            punto_encuentro="Plaza principal de Mongua",
            hora_encuentro=timezone.now().time(),
            categoria=random.choice(categorias_creadas),
            imagen=imagen_path
        )
        p.actividades.add(*random.sample(actividades_creadas, random.randint(2, 4)))
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

    # ─────────────────────────────────────────────
    # 4. RESERVAS Y CANCELACIONES
    # ─────────────────────────────────────────────
    print("4. Creando Reservas y Cancelaciones...")
    reservas_creadas = []
    estados_reserva = ['pendiente', 'confirmada', 'cancelada']
    combinaciones_unicas = set()

    for tarifa_asociada in tarifas_creadas:
        fecha_reserva = tarifa_asociada.temporada.fecha_inicio + \
            timedelta(days=2)
        usuario_aleatorio = random.choice(clientes_creados).usuario
        paquete_asociado = tarifa_asociada.paquete

        identificador = (usuario_aleatorio.id,
                         paquete_asociado.id, fecha_reserva)

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
        
        # Asignar fecha realista (auto_now_add no deja hacerlo en create)
        dias_antes = random.randint(5, 60)
        fake_registro_date = fecha_reserva - timedelta(days=dias_antes)
        fake_registro = timezone.make_aware(datetime.combine(fake_registro_date, datetime.min.time())) + timedelta(hours=random.randint(8, 20))
        Reserva.objects.filter(id=r.id).update(fecha_registro=fake_registro)
        r.fecha_registro = fake_registro
        reservas_creadas.append(r)

        if estado == 'cancelada':
            c = Cancelacion.objects.create(
                reserva=r,
                motivo=random.choice([
                    "Imprevisto de última hora, no podré asistir al viaje.",
                    "Cambio en las fechas laborales, necesito reprogramar.",
                    "Motivos de salud me impiden viajar en esta fecha.",
                    "Surgió un compromiso familiar inesperado.",
                    "Cambio de planes por condiciones climáticas adversas.",
                ]),
                penalidad=Decimal(str(random.randint(0, 50000)))
            )
            dias_diff = (fecha_reserva - fake_registro_date).days
            if dias_diff > 1:
                fake_solicitud = fake_registro + timedelta(days=random.randint(1, dias_diff - 1))
            else:
                fake_solicitud = fake_registro + timedelta(hours=5)
            Cancelacion.objects.filter(id=c.id).update(fecha_solicitud=fake_solicitud)

    print(f"  -> {len(reservas_creadas)} reservas creadas.")

    # ─────────────────────────────────────────────
    # 5. COMPROBANTES DE PAGO
    # ─────────────────────────────────────────────
    print("5. Creando Comprobantes de Pago...")
    bancos = [
        'Bancolombia', 'Banco de Bogotá', 'Davivienda', 'BBVA Colombia',
        'Nequi', 'Daviplata', 'Banco Popular', 'Banco de Occidente'
    ]
    comprobantes_creados = 0
    reservas_con_comprobante = random.sample(
        reservas_creadas, min(12, len(reservas_creadas)))

    for r in reservas_con_comprobante:
        estado_comprobante = random.choice(['pendiente', 'aprobado', 'rechazado'])
        cp = ComprobantePago.objects.create(
            usuario=r.usuario,
            reserva=r,
            referencia=f"REF-{random.randint(100000, 999999)}",
            banco_origen=random.choice(bancos),
            monto=Decimal(str(r.monto_total)) if r.monto_total else Decimal('150000'),
            imagen='comprobantes/placeholder.jpg',
            descripcion=random.choice([
                "Transferencia bancaria realizada exitosamente.",
                "Pago mediante aplicación móvil.",
                "Consignación en efectivo en sucursal bancaria.",
                "Pago con tarjeta de débito.",
            ]),
            estado=estado_comprobante,
            nota_admin="Revisado por administración." if estado_comprobante != 'pendiente' else "",
        )
        fake_envio = r.fecha_registro + timedelta(hours=random.randint(1, 48))
        ComprobantePago.objects.filter(id=cp.id).update(fecha_envio=fake_envio)
        comprobantes_creados += 1

    print(f"  -> {comprobantes_creados} comprobantes de pago creados.")

    # ─────────────────────────────────────────────
    # 6. COMUNIDAD (CALIFICACIONES, BLOG, PQRS, COMENTARIOS)
    # ─────────────────────────────────────────────
    print("6. Creando Comunidad (Calificaciones, Blog, PQRS, Comentarios)...")

    # 6.1 Blogs
    blogs_reales = [
        {
            "titulo": "Laguna Negra",
            "contenido": "La Laguna Negra de Mongua es uno de los destinos más enigmáticos del departamento de Boyacá. Ubicada a más de 3.500 metros de altura, esta laguna de aguas oscuras está rodeada de páramo y envuelta en leyendas ancestrales que hablan de dioses y espíritus guardianes.",
            "informacion_adicional": "El misterio natural de Mongua"
        },
        {
            "titulo": "Legado Ancestral",
            "contenido": "Mongua conserva un legado cultural invaluable que se remonta a las comunidades muiscas que habitaron estas tierras. La iconografía rupestre, las tradiciones orales y la gastronomía típica son testimonio vivo de una cultura milenaria que resiste el paso del tiempo.",
            "informacion_adicional": "Iconografía de una cultura milenaria"
        },
        {
            "titulo": "Rutas de Aventura",
            "contenido": "Los senderos de Mongua ofrecen experiencias únicas para los amantes del senderismo y la fotografía de naturaleza. Desde caminatas suaves por los campos verdes hasta ascensos exigentes al páramo, hay opciones para todos los niveles de experiencia.",
            "informacion_adicional": "Senderismo en las montañas\nFotografía de naturaleza"
        },
        {
            "titulo": "Vivencias",
            "contenido": "Mongua no es solo un destino turístico, es una experiencia que se vive con todos los sentidos. Desde la gastronomía local con platos como el cuchuco de trigo y las arepas boyacenses, hasta los talleres de artesanías donde se trabaja la lana virgen.",
            "informacion_adicional": "Gastronomía local\nTalleres de artesanías\nHospedaje tradicional"
        }
    ]

    for data in blogs_reales:
        Blog.objects.create(
            titulo=data["titulo"],
            contenido=data["contenido"],
            informacion_adicional=data["informacion_adicional"],
            publicado=True
        )

    # 6.2 PQRS
    asuntos_pqrs = [
        "Consulta sobre disponibilidad de paquetes",
        "Solicitud de reembolso por cancelación",
        "Queja por demora en la confirmación de reserva",
        "Sugerencia para mejorar la experiencia de senderismo",
        "Reclamo por cobro duplicado en mi cuenta",
        "Petición de información sobre accesibilidad",
        "Queja por falta de señalización en los senderos",
        "Sugerencia de nuevos paquetes familiares",
        "Consulta sobre políticas de cancelación",
        "Reclamo por comprobante rechazado sin justificación",
    ]
    descripciones_pqrs = [
        "Quisiera saber si hay paquetes disponibles para el próximo fin de semana, somos un grupo de 6 personas.",
        "Solicito amablemente el reembolso de mi reserva cancelada hace más de 15 días según su política.",
        "Han pasado 5 días hábiles y aún no recibo confirmación de mi reserva. Agradezco su pronta respuesta.",
        "Recomiendo instalar más puntos de hidratación en las rutas largas de senderismo.",
        "Se realizó un doble cobro en mi tarjeta de crédito por la misma reserva. Adjunto comprobantes.",
        "Quisiera saber si los senderos son accesibles para personas con movilidad reducida.",
        "En mi última visita noté que varios senderos carecen de señalización adecuada, lo cual puede ser peligroso.",
        "Sería genial contar con paquetes que incluyan actividades para niños menores de 5 años.",
        "Necesito conocer las condiciones y porcentajes de penalidad por cancelación anticipada.",
        "Mi comprobante de pago fue rechazado sin explicación. Solicito una revisión detallada.",
    ]
    for i in range(10):
        PQRS.objects.create(
            cliente=random.choice(clientes_creados),
            tipo=random.choice(['peticion', 'queja', 'reclamo', 'sugerencia']),
            asunto=asuntos_pqrs[i],
            descripcion=descripciones_pqrs[i],
            estado=random.choice(['abierto', 'en_proceso', 'cerrado'])
        )

    # 6.3 Calificaciones
    combinaciones_calificacion = set()
    comentarios_calificacion = [
        "¡Excelente experiencia! Los guías fueron muy profesionales y amables.",
        "Un viaje inolvidable. Los paisajes de Mongua son espectaculares.",
        "Muy buena organización. Recomiendo este paquete sin duda.",
        "La comida típica fue lo mejor de todo el viaje. ¡Delicioso!",
        "El sendero hacia la Laguna Negra fue desafiante pero muy gratificante.",
        "Perfecto para ir en familia. Los niños disfrutaron mucho las actividades.",
        "El guía tenía un conocimiento increíble sobre la historia de la región.",
        "La relación calidad-precio es muy buena. Volvería sin dudarlo.",
        "La naturaleza del páramo de Mongua es simplemente impresionante.",
        "Buena experiencia en general, aunque las condiciones climáticas nos afectaron un poco.",
    ]
    while len(combinaciones_calificacion) < 10:
        c = random.choice(clientes_creados)
        p = random.choice(paquetes_creados)
        if (c.id, p.id) not in combinaciones_calificacion:
            combinaciones_calificacion.add((c.id, p.id))
            Calificacion.objects.create(
                cliente=c,
                paquete=p,
                puntaje=random.randint(3, 5),
                comentario=comentarios_calificacion[len(combinaciones_calificacion) - 1]
            )

    # 6.4 Comentarios
    titulos_comentarios = [
        "Mi experiencia en Mongua", "¡Increíble aventura!", "Recomendado al 100%",
        "Un paraíso escondido", "Vacaciones perfectas", "Naturaleza pura",
        "Excelente servicio", "Viaje memorable", "Mejor de lo esperado",
        "Un destino imperdible",
    ]
    mensajes_comentarios = [
        "Mongua superó todas mis expectativas. Los paisajes del páramo son de otro mundo y la gente es muy acogedora.",
        "La aventura hacia la Laguna Negra fue lo mejor que he hecho en mis vacaciones. ¡Totalmente recomendado!",
        "Recomiendo este destino para cualquier amante de la naturaleza. Los senderos están bien mantenidos.",
        "No sabía que existía un lugar tan hermoso en Boyacá. Mongua es un paraíso que merece ser conocido.",
        "Pasamos unas vacaciones increíbles en familia. Las actividades son variadas y para todas las edades.",
        "La conexión con la naturaleza que ofrece Mongua es única. El aire puro del páramo es revitalizante.",
        "El equipo de guías fue excepcional. Siempre atentos y con un conocimiento profundo de la región.",
        "Un viaje que quedará grabado en mi memoria por siempre. La hospitalidad de la gente es admirable.",
        "Vine sin muchas expectativas y me llevo una experiencia que superó todo lo que imaginé.",
        "Si buscan un destino auténtico, lejos del turismo masivo, Mongua es el lugar perfecto.",
    ]
    for i in range(10):
        Comentario.objects.create(
            usuario=random.choice(clientes_creados).usuario,
            tipo='experiencia',
            titulo=titulos_comentarios[i],
            mensaje=mensajes_comentarios[i],
            valoracion=random.randint(3, 5),
            paquete=random.choice(paquetes_creados),
            visible=True
        )

    # ─────────────────────────────────────────────
    # 7. PROMOCIONES
    # ─────────────────────────────────────────────
    print("7. Creando Promociones...")
    nombres_promociones = [
        "Descuento de Temporada", "Oferta Flash de Verano", "Promo Familiar",
        "Aventura 2x1", "Descuento para Grupos", "Early Bird Navideño",
        "Especial Puente Festivo", "Mongua Lover", "Eco-Descuento",
        "Última Hora"
    ]
    descripciones_promociones = [
        "Aprovecha el descuento especial de temporada en este paquete turístico.",
        "Oferta relámpago por tiempo limitado. ¡No te la pierdas!",
        "Descuento especial para familias con niños menores de 12 años.",
        "Lleva a tu acompañante gratis en este paquete de aventura.",
        "Descuento exclusivo para grupos de 5 o más personas.",
        "Reserva con anticipación y obtén un descuento especial para Navidad.",
        "Aprovecha el puente festivo con esta promoción increíble.",
        "Para los verdaderos amantes de Mongua, un descuento de fidelidad.",
        "Descuento especial en paquetes de ecoturismo sostenible.",
        "¿Aún no has reservado? Esta oferta de última hora te conviene.",
    ]
    for i in range(10):
        Promocion.objects.create(
            paquete=paquetes_creados[i],
            nombre=nombres_promociones[i],
            descripcion=descripciones_promociones[i],
            descuento=random.choice([10, 15, 20, 25, 30]),
            fecha_fin=date(2026, 12, 31) - timedelta(days=random.randint(0, 180)),
            activa=random.choice([True, True, True, False])
        )

    # ─────────────────────────────────────────────
    # 8. NOTIFICACIONES
    # ─────────────────────────────────────────────
    print("8. Creando Notificaciones...")
    notificaciones_data = [
        ("Reserva confirmada", "Tu reserva ha sido confirmada exitosamente. ¡Prepárate para tu aventura!", "reserva"),
        ("Nuevo paquete disponible", "Se ha agregado un nuevo paquete turístico que te puede interesar.", "sistema"),
        ("Comprobante aprobado", "Tu comprobante de pago ha sido revisado y aprobado por la administración.", "reserva"),
        ("Respuesta a tu PQRS", "Hemos respondido a tu solicitud PQRS. Revisa tu bandeja.", "pqrs"),
        ("Promoción especial", "¡Hay una nueva promoción disponible! Aprovecha el descuento antes de que termine.", "sistema"),
        ("Recordatorio de viaje", "Tu viaje está programado para los próximos días. No olvides preparar tu equipaje.", "reserva"),
        ("Cancelación procesada", "Tu solicitud de cancelación ha sido procesada. Revisa los detalles.", "reserva"),
        ("Bienvenido a Monagua", "¡Gracias por registrarte! Explora nuestros paquetes turísticos.", "sistema"),
        ("Califica tu experiencia", "¿Ya regresaste de tu viaje? Cuéntanos cómo te fue.", "sistema"),
        ("Actualización del sistema", "Hemos mejorado nuestra plataforma para brindarte una mejor experiencia.", "sistema"),
    ]
    for titulo, mensaje, tipo in notificaciones_data:
        usuario_destino = random.choice(clientes_creados).usuario
        Notificacion.objects.create(
            cliente=usuario_destino,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            leida=random.choice([True, False])
        )

    # ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[OK] Poblado de base de datos finalizado con exito!")
    print(f"   • {len(clientes_creados)} Clientes")
    print(f"   • {len(guias_creados)} Guías Turísticos")
    print(f"   • {len(categorias_creadas)} Categorías")
    print(f"   • {len(actividades_creadas)} Actividades")
    print(f"   • {len(paquetes_creados)} Paquetes")
    print(f"   • {len(temporadas_creadas) + 1} Temporadas")
    print(f"   • {len(tarifas_creadas)} Tarifas")
    print(f"   • {len(reservas_creadas)} Reservas")
    print(f"   • {comprobantes_creados} Comprobantes de Pago")
    print(f"   • 4 Blogs")
    print(f"   • 10 PQRS")
    print(f"   • 10 Calificaciones")
    print(f"   • 10 Comentarios")
    print(f"   • 10 Promociones")
    print(f"   • 10 Notificaciones")
    print("=" * 60)


if __name__ == '__main__':
    poblar_base_datos()
