#!/usr/bin/env python
"""
Script para agregar datos de prueba a la base de datos
para verificar que la página de estadísticas funciona correctamente.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from usuarios.models import Cliente
from comunidad.models import PQRS, Comentario
from pagos.models import ComprobantePago
from catalogo.models import Paquete
from reservas.models import Reserva
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

Usuario = get_user_model()


def crear_datos_prueba():
    """Crea datos de prueba para la página de estadísticas"""

    print("[INFO] Iniciando creacion de datos de prueba...")

    # 1. Obtener o crear usuario de prueba
    usuario, creado = Usuario.objects.get_or_create(
        username='vitococo',
        defaults={
            'email': 'vitococo@test.com',
            'first_name': 'Vito',
            'last_name': 'Coco',
            'is_active': True,
        }
    )
    if creado:
        usuario.set_password('123456')
        usuario.save()
        print(f"[OK] Usuario creado: {usuario.username}")
    else:
        print(f"[INFO] Usuario ya existe: {usuario.username}")

    # 2. Obtener o crear cliente asociado
    cliente, creado = Cliente.objects.get_or_create(
        usuario=usuario,
        defaults={'pais': 'Colombia', 'ciudad': 'Bogota'}
    )
    if creado:
        print(f"[OK] Cliente creado para {usuario.username}")

    # 3. Obtener paquetes
    paquetes = Paquete.objects.filter(estado=True)[:5]
    if not paquetes.exists():
        print("[WARN] No hay paquetes activos. Crea algunos primero.")
        return

    print(f"[INFO] Paquetes disponibles: {paquetes.count()}")

    # 4. Crear reservas de prueba (últimos 12 meses)
    now = timezone.now()
    estados = ['confirmada', 'pendiente', 'cancelada', 'confirmada']  # 'confirmada' represents completed too

    for mes in range(12):
        fecha = now - timedelta(days=30*mes)

        # 2-4 reservas por mes
        for i in range(2):
            paquete = paquetes[i % len(paquetes)]
            estado = estados[(mes + i) % len(estados)]

            reserva, creado = Reserva.objects.get_or_create(
                usuario=usuario,
                paquete=paquete,
                fecha=fecha.date() - timedelta(days=i*5),
                defaults={
                    'estado': estado,
                    'numero_adultos': 1 + (i % 2),
                    'numero_menores': i % 2,
                }
            )
            if creado:
                print(
                    f"[OK] Reserva creada: {paquete.nombre} ({estado}) - {fecha.date()}")

    # 5. Crear comprobantes de pago
    reservas = Reserva.objects.filter(usuario=usuario, estado='confirmada')
    for reserva in reservas[:5]:
        comprobante, creado = ComprobantePago.objects.get_or_create(
            usuario=usuario,
            reserva=reserva,
            defaults={
                'monto': 150000.0,
                'banco_origen': 'Bancolombia',
                'estado': 'aprobado',
                'fecha_envio': reserva.fecha_registro + timedelta(days=1),
            }
        )
        if creado:
            print(
                f"[OK] Comprobante de pago creado para {reserva.paquete.nombre}")

    # 6. Crear PQRS de prueba
    estados_pqrs = ['abierto', 'en_proceso', 'cerrado']
    tipos_pqrs = ['peticion', 'queja', 'reclamo', 'sugerencia']

    for i in range(3):
        pqrs, creado = PQRS.objects.get_or_create(
            cliente=cliente,
            asunto=f"PQRS de prueba #{i+1}",
            defaults={
                'tipo': tipos_pqrs[i % len(tipos_pqrs)],
                'descripcion': f"Descripcion de prueba para PQRS #{i+1}",
                'estado': estados_pqrs[i % len(estados_pqrs)],
                'respuesta': 'Respuesta de prueba' if i % 2 == 0 else '',
            }
        )
        if creado:
            print(
                f"[OK] PQRS creada: {pqrs.get_tipo_display()} - {pqrs.get_estado_display()}")

    # 7. Crear comentarios/reseñas
    for i, paquete in enumerate(paquetes[:3]):
        comentario, creado = Comentario.objects.get_or_create(
            usuario=usuario,
            paquete=paquete,
            defaults={
                'titulo': f'Excelente experiencia en {paquete.nombre}',
                'mensaje': 'Este fue un viaje increible, los guias fueron muy profesionales.',
                'valoracion': 5 - (i % 2),
                'visible': True,
                'fecha_creacion': now - timedelta(days=i*10),
            }
        )
        if creado:
            print(
                f"[OK] Resena creada: {comentario.titulo} ({comentario.valoracion}*)")

    print("\n[OK] Datos de prueba creados exitosamente!")
    print(f"Usuario: {usuario.username}")
    print(f"Accede a: http://127.0.0.1:8000/usuarios/mis-estadisticas/")


if __name__ == '__main__':
    crear_datos_prueba()
