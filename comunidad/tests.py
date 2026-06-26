from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from usuarios.models import Cliente
from catalogo.models import Categoria, Paquete
from comunidad.models import PQRS, Calificacion
from notificaciones.models import Notificacion
from django.urls import reverse

Usuario = get_user_model()

class ComunidadTestCase(TestCase):
    def setUp(self):
        # Crear usuario turista
        self.user_turista = Usuario.objects.create_user(
            username='turista_comunidad',
            email='turista@comunidad.com',
            password='password123'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.user_turista,
            pais='Colombia',
            ciudad='Mongua'
        )

        # Crear categoría y paquete
        self.categoria = Categoria.objects.create(
            nombre='Senderismo',
            descripcion='Tours a pie'
        )
        self.paquete = Paquete.objects.create(
            nombre='Laguna Negra Tour',
            descripcion='Maravilla natural de Mongua',
            dias_duracion=1,
            noches_duracion=0,
            punto_encuentro='Plaza Principal',
            hora_encuentro='08:00:00',
            categoria=self.categoria
        )

    def test_creacion_pqrs_exito(self):
        pqr = PQRS.objects.create(
            cliente=self.cliente,
            tipo='queja',
            asunto='Retraso en salida',
            descripcion='El guía llegó tarde a la salida del tour.',
            estado='abierto'
        )
        self.assertEqual(pqr.estado, 'abierto')
        self.assertEqual(pqr.tipo, 'queja')

    def test_responder_pqrs_y_notificar(self):
        pqr = PQRS.objects.create(
            cliente=self.cliente,
            tipo='reclamo',
            asunto='Reclamo reembolso',
            descripcion='Solicito reembolso de penalidad.',
            estado='abierto'
        )

        # Simular respuesta del admin mediante la vista contestar_pqrs
        # Iniciamos sesión
        self.client.force_login(self.user_turista)
        
        # Realizar el POST a la vista contestar_pqrs
        url = reverse('contestar_pqrs', kwargs={'pqrs_id': pqr.id})
        response = self.client.post(url, {'respuesta': 'Se ha procesado tu devolución con éxito.'})
        
        # Debe redireccionar al listado de PQRS del admin
        self.assertEqual(response.status_code, 302)
        
        pqr.refresh_from_db()
        self.assertEqual(pqr.estado, 'cerrado')
        self.assertEqual(pqr.respuesta, 'Se ha procesado tu devolución con éxito.')
        
        # Verificar que se creó la notificación para el usuario
        notificaciones = Notificacion.objects.filter(cliente=self.user_turista)
        self.assertEqual(notificaciones.count(), 1)
        self.assertEqual(notificaciones.first().titulo, 'PQRS Respondida')

    def test_calificacion_unica_por_cliente_y_paquete(self):
        # Crear la primera calificación
        Calificacion.objects.create(
            cliente=self.cliente,
            paquete=self.paquete,
            puntaje=5,
            comentario='¡Excelente tour!'
        )

        # Intentar duplicar la calificación para el mismo cliente y paquete
        with self.assertRaises(IntegrityError):
            Calificacion.objects.create(
                cliente=self.cliente,
                paquete=self.paquete,
                puntaje=4,
                comentario='Otro comentario diferente'
            )
