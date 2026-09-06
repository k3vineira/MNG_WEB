import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from App.models import (
    Usuario, Temporada, Categoria, Actividades, Paquete, Tarifa,
    PaqueteActividad, PaquetePromocion, Blog, Reserva, PQRS,
    Seguimiento, Notificacion, PlanGuia, Pago,
    Promocion, PolizaViaje, Aseguradora, Bitacora
)
import random
import shutil
from datetime import timedelta, date, datetime
from django.utils import timezone
from decimal import Decimal
from django.conf import settings


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
    print("Iniciando el poblado de la base de datos...")
    print("0. Limpiando la base de datos...")

    Bitacora.objects.all().delete()
    Pago.objects.all().delete()
    Notificacion.objects.all().delete()
    PlanGuia.objects.all().delete()
    Aseguradora.objects.all().delete()
    PolizaViaje.objects.all().delete()
    PaquetePromocion.objects.all().delete()
    Promocion.objects.all().delete()
    Seguimiento.objects.all().delete()
    PQRS.objects.all().delete()
    Blog.objects.all().delete()
    Reserva.objects.all().delete()
    Tarifa.objects.all().delete()
    Temporada.objects.all().delete()
    PaqueteActividad.objects.all().delete()
    Paquete.objects.all().delete()
    Actividades.objects.all().delete()
    Categoria.objects.all().delete()
    Usuario.objects.all().delete()

    nombres = ['Carlos', 'Ana', 'Luis', 'Marta', 'Pedro',
               'Sofia', 'Jorge', 'Lucia', 'Diego', 'Elena']
    apellidos = ['Gomez', 'Perez', 'Rodriguez', 'Lopez',
                 'Martinez', 'Garcia', 'Sanchez', 'Diaz', 'Torres', 'Ramirez']
    ciudades = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
                'Cúcuta', 'Bucaramanga', 'Pereira', 'Santa Marta', 'Manizales']
    paises = ['COL', 'MEX', 'ARG', 'CHL', 'PER',
              'ESP', 'ECU', 'PAN', 'CRI', 'BRA']
    categorias_nombres = ['Aventura', 'Ecoturismo', 'Cultural', 'Playa', 'Montaña',
                          'Gastronómico', 'Histórico', 'Relajación', 'Deportivo', 'Familiar']
    actividades_nombres = ['Senderismo', 'Buceo', 'Museos', 'Escalada', 'Ciclismo',
                           'Cata de Vinos', 'Surf', 'Avistamiento de Aves', 'Rappel', 'Canotaje']

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

    fechas_temporadas = [
        (date(2026, 6, 4),   date(2026, 7, 15)),
        (date(2026, 7, 16),  date(2026, 8, 15)),
        (date(2026, 8, 16),  date(2026, 8, 31)),
        (date(2026, 9, 1),   date(2026, 9, 30)),
        (date(2026, 10, 1),  date(2026, 10, 15)),
        (date(2026, 10, 16), date(2026, 10, 31)),
        (date(2026, 11, 1),  date(2026, 11, 16)),
        (date(2026, 11, 17), date(2026, 11, 30)),
        (date(2026, 12, 1),  date(2026, 12, 15)),
        (date(2026, 12, 16), date(2026, 12, 31)),
    ]

    print("1. Creando Usuarios (Admin, Clientes, Guías)...")
    admin_user = Usuario.objects.create_superuser(
        username='admin',
        password='adminpassword',
        email='admin@monagua.com',
        first_name='Admin',
        last_name='Monagua',
        rol=Usuario.Roles.ADMIN,
        tipo_documento=Usuario.TipoDocumento.CC,
        numero_documento='12345678',
        telefono='+573000000000',
        residencia='Mongua, Boyacá'
    )

    clientes_creados = []
    guias_creados = []

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
            residencia=f"{ciudades[i]}, {paises[i]}",
            pais=paises[i]
        )
        clientes_creados.append(u)

    biografias_guia = [
        "Guía certificado con más de 5 años de experiencia en senderismo de alta montaña.",
        "Apasionado por la naturaleza. Especialista en avistamiento de aves.",
        "Conocimiento profundo de la historia y tradiciones de Mongua.",
        "Experto en deportes de aventura incluyendo rappel, escalada y canotaje.",
        "Guía bilingüe especializado en turismo gastronómico y experiencias locales.",
        "Fotógrafo naturalista y guía especializado en la Laguna Negra.",
        "Instructor certificado de senderismo nocturno y camping.",
        "Conocedor de rutas ancestrales y caminos reales.",
        "Guía de turismo familiar con experiencia en actividades recreativas.",
        "Especialista en turismo sostenible y comunitario.",
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
            residencia=f"{ciudades[i]}, Boyacá",
            numero_tarjeta_profesional=f"LIC-BOY-{random.randint(10000, 99999)}",
            experiencia_anos=random.randint(1, 15),
            descripcion_experiencia=biografias_guia[i],
            entidad_salud=random.choice(["SURA", "Sanitas", "Compensar", "Nueva EPS"]),
            experiencia_fecha=date.today() - timedelta(days=random.randint(365, 365*5))
        )
        guias_creados.append(u)

    print(f"  -> {len(clientes_creados)} clientes y {len(guias_creados)} guias creados.")

    print("2. Creando Categorías y Actividades...")
    categorias_creadas = []
    descripciones_categorias = [
        "Experiencias llenas de adrenalina y desafíos al aire libre.",
        "Turismo responsable en armonía con la naturaleza.",
        "Inmersión en la cultura, tradiciones y artesanías.",
        "Disfruta del sol, la arena y las aguas cristalinas.",
        "Aventuras en las alturas del páramo y las montañas.",
        "Degusta la riqueza culinaria local y los sabores ancestrales.",
        "Recorre los caminos y monumentos históricos.",
        "Espacios de bienestar y tranquilidad.",
        "Actividades deportivas para los amantes del ejercicio.",
        "Planes diseñados para disfrutar en familia.",
    ]
    for i in range(10):
        cat = Categoria.objects.create(
            nombre=categorias_nombres[i],
            descripcion=descripciones_categorias[i]
        )
        categorias_creadas.append(cat)

    actividades_creadas = []
    descripciones_actividades = [
        "Recorridos guiados por senderos naturales con vistas al páramo.",
        "Inmersión en aguas cristalinas.",
        "Visitas a museos locales con exhibiciones de arte.",
        "Ascenso en paredes rocosas naturales.",
        "Recorridos en bicicleta por rutas rurales.",
        "Degustación de vinos y bebidas artesanales.",
        "Práctica de surf en las olas.",
        "Observación de aves endémicas en su hábitat.",
        "Descenso por cascadas y formaciones rocosas.",
        "Navegación en canoas por ríos de corriente moderada.",
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
            equipo_requerimiento=equipos[i],
            recomendaciones="Buena condición física general. Consultar con médico en caso de condiciones especiales.",
            apto_menores=random.choice([True, False])
        )
        actividades_creadas.append(act)

    print("3. Creando Paquetes, Temporadas y Tarifas...")
    paquetes_creados = []
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

    destinos_media_dir = os.path.join(settings.MEDIA_ROOT, 'destinos')
    os.makedirs(destinos_media_dir, exist_ok=True)

    for nombre, descripcion, img_name in paquetes_config:
        src_path = os.path.join(settings.BASE_DIR, 'static', 'img', img_name)
        dst_path = os.path.join(destinos_media_dir, img_name)
        imagen_path = f"destinos/{img_name}"
        if os.path.exists(src_path):
            try:
                shutil.copy(src_path, dst_path)
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
        sample_acts = random.sample(actividades_creadas, random.randint(2, 4))
        for act in sample_acts:
            PaqueteActividad.objects.create(
                paquete=p,
                actividad=act,
                dificultad_nivel=random.choice(['Alta', 'Media', 'Baja'])
            )
        paquetes_creados.append(p)

    temporada_estandar = Temporada.objects.create(
        nombre="Temporada Estándar 2026",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        estado=True
    )

    temporadas_creadas = []
    for i in range(len(nombres_temporadas)):
        t = Temporada.objects.create(
            nombre=f"{nombres_temporadas[i]} 2026",
            fecha_inicio=fechas_temporadas[i][0],
            fecha_fin=fechas_temporadas[i][1],
            estado=True
        )
        temporadas_creadas.append(t)

    tarifas_creadas = []
    for i in range(10):
        tarifa_especial = Tarifa.objects.create(
            paquete=paquetes_creados[i],
            temporada=temporadas_creadas[i],
            precio_adulto=Decimal(str(random.randint(350000, 600000))),
            precio_menor=Decimal(str(random.randint(200000, 300000))),
            estado=True
        )
        tarifas_creadas.append(tarifa_especial)

        tarifa_base = Tarifa.objects.create(
            paquete=paquetes_creados[i],
            temporada=temporada_estandar,
            precio_adulto=Decimal(str(random.randint(150000, 300000))),
            precio_menor=Decimal(str(random.randint(80000, 140000))),
            estado=True
        )
        tarifas_creadas.append(tarifa_base)

    print("4. Creando Reservas...")
    reservas_creadas = []
    estados_reserva = ['pendiente', 'confirmada', 'cancelada']
    combinaciones_unicas = set()

    for tarifa_asociada in tarifas_creadas:
        fecha_reserva = tarifa_asociada.temporada.fecha_inicio + timedelta(days=2)
        usuario_aleatorio = random.choice(clientes_creados)
        paquete_asociado = tarifa_asociada.paquete

        identificador = (usuario_aleatorio.id, paquete_asociado.id, fecha_reserva)
        if identificador in combinaciones_unicas:
            continue

        combinaciones_unicas.add(identificador)
        estado = random.choice(estados_reserva)
        motivo = ""
        if estado == 'cancelada':
            motivo = random.choice([
                "Imprevisto de última hora, no podré asistir al viaje.",
                "Cambio en las fechas laborales, necesito reprogramar.",
                "Motivos de salud me impiden viajar en esta fecha.",
                "Surgió un compromiso familiar inesperado.",
            ])

        r = Reserva.objects.create(
            usuario=usuario_aleatorio,
            paquete=paquete_asociado,
            fecha_inicio=fecha_reserva,
            numero_adultos=random.randint(1, 4),
            numero_menores=random.randint(0, 3),
            estado_reserva=estado,
            motivo_cancelacion=motivo
        )

        dias_antes = random.randint(5, 60)
        fake_registro_date = fecha_reserva - timedelta(days=dias_antes)
        fake_registro = timezone.make_aware(datetime.combine(fake_registro_date, datetime.min.time())) + timedelta(hours=random.randint(8, 20))
        Reserva.objects.filter(id=r.id).update(fecha_registro=fake_registro)
        r.fecha_registro = fake_registro
        reservas_creadas.append(r)

    print(f"  -> {len(reservas_creadas)} reservas creadas.")

    print("5. Creando Pagos...")
    bancos = [
        'Bancolombia', 'Banco de Bogotá', 'Davivienda', 'BBVA Colombia',
        'Nequi', 'Daviplata', 'Banco Popular', 'Banco de Occidente'
    ]
    comprobantes_creados = 0
    reservas_con_comprobante = random.sample(reservas_creadas, min(12, len(reservas_creadas)))

    for r in reservas_con_comprobante:
        estado_comprobante = random.choice(['pendiente', 'aprobado', 'rechazado'])
        fake_envio = r.fecha_registro + timedelta(hours=random.randint(1, 48))

        Pago.objects.create(
            reserva=r,
            referencia=f"REF-{random.randint(100000, 999999)}",
            banco_origen=random.choice(bancos),
            metodo_pago="Transferencia",
            monto=Decimal(str(r.monto_total)) if r.monto_total else Decimal('150000'),
            imagen_comprobante='comprobantes/placeholder.jpg',
            estado_transaccion=estado_comprobante,
            nota_admin="Revisado por administración." if estado_comprobante != 'pendiente' else "Pendiente de revisión",
            fecha_pago=fake_envio
        )
        comprobantes_creados += 1

    print(f"  -> {comprobantes_creados} pagos creados.")

    print("6. Creando Comunidad (Blogs, PQRS, Seguimiento)...")
    blogs_reales = [
        {
            "titulo": "Laguna Negra",
            "contenido": "La Laguna Negra de Mongua es uno de los destinos más enigmáticos del departamento de Boyacá. Ubicada a más de 3.500 metros de altura, esta laguna de aguas oscuras está rodeada de páramo y envuelta en leyendas ancestrales.",
            "informacion_adicional": "El misterio natural de Mongua"
        },
        {
            "titulo": "Legado Ancestral",
            "contenido": "Mongua conserva un legado cultural invaluable que se remonta a las comunidades muiscas que habitaron estas tierras.",
            "informacion_adicional": "Iconografía de una cultura milenaria"
        },
        {
            "titulo": "Rutas de Aventura",
            "contenido": "Los senderos de Mongua ofrecen experiencias únicas para los amantes del senderismo y la fotografía de naturaleza.",
            "informacion_adicional": "Senderismo en las montañas"
        },
        {
            "titulo": "Vivencias",
            "contenido": "Mongua no es solo un destino turístico, es una experiencia que se vive con todos los sentidos.",
            "informacion_adicional": "Gastronomía local y artesanías"
        }
    ]

    for data in blogs_reales:
        Blog.objects.create(
            usuario=admin_user,
            titulo=data["titulo"],
            contenido=data["contenido"],
            informacion_adicional=data["informacion_adicional"],
            estado=True
        )

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
        "Quisiera saber si hay paquetes disponibles para el próximo fin de semana.",
        "Solicito amablemente el reembolso de mi reserva cancelada.",
        "Han pasado 5 días hábiles y aún no recibo confirmación.",
        "Recomiendo instalar más puntos de hidratación en las rutas largas.",
        "Se realizó un doble cobro en mi tarjeta de crédito.",
        "Quisiera saber si los senderos son accesibles para personas con movilidad reducida.",
        "En mi última visita noté que varios senderos carecen de señalización.",
        "Sería genial contar con paquetes que incluyan actividades para niños.",
        "Necesito conocer las condiciones y porcentajes de penalidad por cancelación.",
        "Mi comprobante de pago fue rechazado sin explicación.",
    ]

    for i in range(10):
        est = random.choice(['abierto', 'en_proceso', 'cerrado'])
        pqr_obj = PQRS.objects.create(
            usuario=random.choice(clientes_creados),
            tipo=random.choice(['peticion', 'queja', 'reclamo', 'sugerencia']),
            asunto=asuntos_pqrs[i],
            descripcion=descripciones_pqrs[i],
            estado=est
        )
        if est in ['en_proceso', 'cerrado']:
            Seguimiento.objects.create(
                pqrs=pqr_obj,
                usuario=admin_user,
                respuesta="Hemos recibido tu solicitud y se encuentra en revisión por el equipo de Monagua."
            )

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
    promociones_creadas = []
    for i in range(10):
        f_fin = date(2026, 12, 31) - timedelta(days=random.randint(0, 180))
        f_inicio = f_fin - timedelta(days=random.randint(15, 60))
        promo = Promocion.objects.create(
            nombre=nombres_promociones[i],
            descripcion=descripciones_promociones[i],
            porcentaje_descuento=random.choice([10, 15, 20, 25, 30]),
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
            codigo_promocion=f"PROM-{random.randint(1000, 9999)}-{i}",
            activa=True
        )
        promociones_creadas.append(promo)

    for i in range(min(10, len(paquetes_creados))):
        PaquetePromocion.objects.create(
            paquete=paquetes_creados[i],
            promocion=promociones_creadas[i % len(promociones_creadas)],
            valor_adulto_condescuento=Decimal('100000'),
            valor_menor_condescuento=Decimal('50000')
        )

    print("8. Creando Bitácoras...")
    auditoria_data = [
        ("LOGIN", "usuarios_usuario", "El cliente inició sesión desde la web."),
        ("INSERT", "reservas_reserva", "Se registró una nueva reserva para paquete turístico."),
        ("INSERT", "pago", "El usuario adjuntó comprobante de pago."),
        ("INSERT", "pqrs", "Se generó una solicitud de PQRS en la plataforma."),
        ("UPDATE", "usuarios_usuario", "El usuario actualizó sus datos de contacto."),
        ("UPDATE", "reservas_reserva", "El cliente solicitó la cancelación de su reserva."),
        ("INSERT", "calificacion", "El usuario valoró una actividad turística."),
        ("INSERT", "blog", "Se agregó un nuevo post en la sección del blog."),
        ("INSERT", "usuarios_usuario", "Creación de cuenta en la plataforma Monagua."),
        ("ACCESO", "catalogo_paquete", "Búsqueda y visualización de paquetes turísticos.")
    ]

    for accion, modulo, descripcion in auditoria_data:
        cliente_random = random.choice(clientes_creados)
        Bitacora.objects.create(
            usuario=cliente_random,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion
        )

    print("\n" + "=" * 60)
    print("[OK] Poblado de base de datos finalizado con éxito!")
    print(f"   • {len(clientes_creados)} Clientes")
    print(f"   • {len(guias_creados)} Guías Turísticos")
    print(f"   • {len(categorias_creadas)} Categorías")
    print(f"   • {len(actividades_creadas)} Actividades")
    print(f"   • {len(paquetes_creados)} Paquetes")
    print(f"   • {len(temporadas_creadas) + 1} Temporadas")
    print(f"   • {len(tarifas_creadas)} Tarifas")
    print(f"   • {len(reservas_creadas)} Reservas")
    print(f"   • {comprobantes_creados} Pagos")
    print(f"   • 4 Blogs")
    print(f"   • 10 PQRS")
    print(f"   • 10 Promociones")
    print(f"   • 10 Registros de Bitácora")
    print("=" * 60)


if __name__ == '__main__':
    poblar_base_datos()