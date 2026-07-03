"""
Modelos de datos para reservas y cancelaciones de paquetes turísticos.
"""

from django.db import models
from django.conf import settings
from catalogo.models import Paquete
from django.core.exceptions import ValidationError
from django.utils import timezone


class Reserva(models.Model):
    """
    Reserva realizada por un usuario para un paquete turístico en una fecha específica.
    Calcula automáticamente el monto total según las tarifas y temporadas activas.
    """
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
        Paquete,  
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


    monto_total = models.IntegerField(
        verbose_name='Monto Total', editable=False)

    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'paquete', 'fecha'],
                name='unique_usuario_paquete_fecha'
            )
        ]

    def clean(self):
        """
        Valida que el usuario no tenga dos reservas duplicadas para el mismo paquete y fecha.

        Raises:
            ValidationError: Si ya existe una reserva para el mismo usuario, paquete y fecha.
        """
        super().clean()
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
        """
        Calcula el monto_total de la reserva según la temporada y tarifa vigente antes de guardar.

        Args:
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de clave-valor adicionales.
        """
       
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

        super().save(*args, **kwargs)

    @property
    def tiene_cancelacion_activa(self):
        """
        Verifica si la reserva tiene una solicitud de cancelación activa.

        Returns:
            bool: True si hay alguna cancelación en estado 'pendiente' o 'revision'.
        """
        return self.cancelaciones.filter(estado__in=['pendiente', 'revision']).exists()

    def __str__(self):
        """Retorna el ID, usuario y paquete de la reserva como representación textual."""
        nombre_usuario = self.usuario.get_full_name() or self.usuario.username
        return f"Reserva {self.id} - {nombre_usuario} ({self.paquete.nombre})"
   
   

class Cancelacion(models.Model):
    """
    Solicitud de cancelación de una reserva realizada por un usuario.
    Calcula automáticamente la penalidad según los días de antelación.
    """
     
    ESTADOS_CANCELACION = [
        ('pendiente', 'Pendiente'),  
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='cancelaciones')
    motivo = models.TextField()
    penalidad = models.IntegerField(default=0, verbose_name='Penalidad Aplicada')
    estado = models.CharField( max_length=20, choices=ESTADOS_CANCELACION, default='pendiente', verbose_name='Estado')
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Solicitud')

    class Meta:
        verbose_name = 'Cancelación'
        verbose_name_plural = 'Cancelaciones'

    def save(self, *args, **kwargs):
        """
        Calcula la penalidad económica y actualiza el estado de la reserva al guardar.

        La penalidad es del 10% si se cancela con más de 15 días, del 50% entre 5-15 días,
        y del 100% si quedan menos de 5 días para el viaje.

        Args:
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de clave-valor adicionales.
        """
        
        if not self.pk:
            fecha_viaje = self.reserva.fecha
            fecha_actual = timezone.now().date()
    
            diferencia = fecha_viaje - fecha_actual
            dias_antelacion = diferencia.days
            valor_reserva = self.reserva.monto_total
            
            if dias_antelacion > 15:
                self.penalidad = int(valor_reserva * 0.10)  
                
            elif 5 <= dias_antelacion <= 15:
                self.penalidad = int(valor_reserva * 0.50)  
                
            else:
                self.penalidad = valor_reserva              
        if self.estado == 'aceptada':
            self.reserva.estado = 'cancelada'
            self.reserva.save()
        elif self.estado == 'rechazada':
            self.reserva.estado = 'confirmada'
            self.reserva.save()

        super().save(*args, **kwargs)

    def __str__(self):
        """Retorna el ID de la reserva cancelada y el estado de la cancelación."""
        return f"Cancelación de Reserva #{self.reserva.id} - {self.get_estado_display()}"