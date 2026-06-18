from django.db import models
from django.conf import settings
from catalogo.models import Paquete
from django.core.exceptions import ValidationError
from django.utils import timezone


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservas_realizadas',
        verbose_name='Cliente'
    )
    paquete = models.ForeignKey(
        Paquete,  # Asegúrate de que este modelo esté importado arriba
        on_delete=models.PROTECT,
        related_name='reserva',
        verbose_name='Paquete Reservado'
    )
    fecha = models.DateField(verbose_name='Fecha de Reserva')
    numero_adultos = models.PositiveIntegerField(
        verbose_name='Número de Adultos', default=1)
    numero_menores = models.PositiveIntegerField(
        verbose_name='Número de Menores', default=0)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')

    # Monto total (se calculará automáticamente)
    monto_total = models.IntegerField(
        verbose_name='Monto Total', editable=False)

    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        # Blindaje absoluto a nivel Base de Datos
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'paquete', 'fecha'],
                name='unique_usuario_paquete_fecha'
            )
        ]

    def clean(self):
        super().clean()

        # Validación inteligente para los formularios del Front-End y Admin
        if self.usuario and self.paquete and self.fecha:
            query = Reserva.objects.filter(
                usuario=self.usuario,
                paquete=self.paquete,
                fecha=self.fecha
            )
            if self.pk:
                query = query.exclude(pk=self.pk)

            if query.exists():
                raise ValidationError(
                    f"Ya tienes una reserva registrada para el paquete '{self.paquete.nombre}' en la fecha {self.fecha}."
                )

    def save(self, *args, **kwargs):
        # NOTA: Se removió self.full_clean() de aquí para que el script corra sin problemas.
        # Tus vistas con CreateView/ModelForm se encargan de validar automáticamente a través de clean().

        if self.paquete and self.fecha:
            try:
                from catalogo.models import Temporada, Tarifa
                temporada = Temporada.objects.filter(
                    fecha_inicio__lte=self.fecha, fecha_fin__gte=self.fecha).first()

                if temporada:
                    tarifa = Tarifa.objects.filter(
                        paquete=self.paquete, temporada=temporada).first()
                    if tarifa:
                        self.monto_total = int(
                            (tarifa.precio_adulto * self.numero_adultos) + (tarifa.precio_menor * self.numero_menores))
                    else:
                        self.monto_total = 0
                else:
                    self.monto_total = 0

            except Exception:
                self.monto_total = 0
        elif not getattr(self, 'monto_total', None):
            self.monto_total = 0

        # Corregida la sangría para que siempre se ejecute el guardado real
        super().save(*args, **kwargs)

    def __str__(self):
        nombre_usuario = self.usuario.get_full_name() or self.usuario.username
        return f"Reserva {self.id} - {nombre_usuario} ({self.paquete.nombre})"

class Cancelacion(models.Model):
    ESTADOS_CANCELACION = [
        ('revision', 'En Revisión por Admin'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    reserva = models.ForeignKey(
        'Reserva', on_delete=models.CASCADE, related_name='cancelaciones')
    motivo = models.TextField()
    penalidad = models.IntegerField(
        default=0, verbose_name='Penalidad Aplicada', editable=False)
    reembolso_sugerido = models.IntegerField(
        default=0, verbose_name='Reembolso Sugerido', editable=False)

    estado = models.CharField(
        max_length=20, choices=ESTADOS_CANCELACION, default='revision', verbose_name='Estado')
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de Solicitud')

    class Meta:
        verbose_name = 'Cancelación'
        verbose_name_plural = 'Cancelaciones'

    def save(self, *args, **kwargs):
        if not self.pk:
            fecha_viaje = self.reserva.fecha
            fecha_actual = timezone.now().date()
            diferencia = fecha_viaje - fecha_actual
            dias_antelacion = diferencia.days
            valor_reserva = self.reserva.monto_total
            if dias_antelacion > 15:
                self.reembolso_sugerido = int(valor_reserva * 0.90)
                self.penalidad = int(valor_reserva * 0.10)
                
            elif dias_antelacion >= 2: 
                self.reembolso_sugerido = int(valor_reserva * 0.50)
                self.penalidad = int(valor_reserva * 0.50)
                
            else:
                self.reembolso_sugerido = 0
                self.penalidad = valor_reserva

        
        if self.estado == 'aceptada':
            self.reserva.estado = 'cancelada'
            self.reserva.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cancelación de Reserva #{self.reserva.id} - {self.get_estado_display()}"