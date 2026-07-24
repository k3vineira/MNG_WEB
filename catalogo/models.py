"""
Modelos de datos para el catálogo de paquetes turísticos.
Incluye Temporada, Categoría, Actividades, Paquete, Tarifa y PaqueteActividad.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Temporada(models.Model):
    """
    Representa una temporada turística con fechas de inicio y fin.
    """
    ESTADOS = [
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
    ]

    nombre = models.CharField(max_length=50, verbose_name='Nombre de la Temporada')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')

    class Meta:
        verbose_name = 'Temporada'
        verbose_name_plural = 'Temporadas'

    def __str__(self):
        """Retorna el nombre de la temporada como representación textual."""
        return self.nombre


class Categoria(models.Model):
    """
    Categoría que agrupa paquetes turísticos similares (ej. Aventura, Cultura).
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Categoría')
    descripcion = models.TextField(verbose_name='Descripción')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        """Retorna el nombre de la categoría como representación textual."""
        return self.nombre


class Actividades(models.Model):
    """
    Actividad turística que puede ser incluida en uno o varios paquetes.
    """
    NIVEL_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baja', 'Baja'),
    ]
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel_dificultad = models.CharField(max_length=10, choices=NIVEL_CHOICES, verbose_name='Nivel de Dificultad')
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido')
    recomendacion_salud = models.TextField(verbose_name='Recomendaciones de Salud')
    estado = models.BooleanField(default=True, blank=True, verbose_name='¿Está Activa?')
    apto_para_menores = models.BooleanField(default=True, verbose_name='¿Apto para menores?')

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        """Retorna el nombre de la actividad como representación textual."""
        return self.nombre


class Paquete(models.Model):
    """
    Paquete turístico ofrecido por Monagua, conformado por actividades y con tarifas por temporada.
    """
    imagen = models.ImageField(upload_to='destinos/', null=True, blank=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Paquete')
    descripcion = models.TextField(verbose_name='Descripción')
    dias_duracion = models.PositiveIntegerField(verbose_name='Días de Duración', default=1)
    noches_duracion = models.PositiveIntegerField(verbose_name='Noches de Duración', default=0)
    punto_encuentro = models.CharField(max_length=200)
    hora_encuentro = models.TimeField()
    categoria = models.ForeignKey(Categoria, models.CASCADE, related_name='paquetes')
    actividades = models.ManyToManyField('Actividades', through='PaqueteActividad')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activo?')

    def __str__(self):
        return self.nombre

    @property
    def precio_minimo(self):
        fecha_hoy = timezone.now().date()
        all_tarifas = list(self.tarifas.all())

        validas = [
            t for t in all_tarifas
            if getattr(t, 'estado', '') == 'activa'
            and getattr(t, 'temporada', None)
            and t.temporada.estado == 'activa'
            and t.temporada.fecha_inicio <= fecha_hoy <= t.temporada.fecha_fin
        ]

        if validas:
            return min(t.precio_adulto for t in validas)

        estandar = next(
            (
                t for t in all_tarifas
                if getattr(t, 'estado', '') == 'activa'
                and t.temporada
                and "estándar" in (t.temporada.nombre.lower() if t.temporada.nombre else "")
            ),
            None
        )

        if estandar:
            return estandar.precio_adulto

        return 0

    @property
    def apto_para_menores(self):
        all_actividades = list(self.actividades.all())
        if all_actividades:
            return not any(not getattr(a, 'apto_para_menores', True) for a in all_actividades)
        return True


class Tarifa(models.Model):
    """
    Tarifa de precio para un paquete en una temporada específica.
    """
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='tarifas')
    temporada = models.ForeignKey(Temporada, on_delete=models.CASCADE, related_name='tarifas')
    precio_adulto = models.IntegerField(verbose_name='Precio por Adulto')
    precio_menor = models.IntegerField(verbose_name='Precio por Menor')
    ESTADOS = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activa')

    class Meta:
        verbose_name = 'Tarifa'
        verbose_name_plural = 'Tarifas'
        unique_together = ('paquete', 'temporada')

    def __str__(self):
        """Retorna el nombre del paquete y la temporada como representación textual."""
        return f"{self.paquete.nombre} - {self.temporada.nombre}"


class PaqueteActividad(models.Model):
    """
    Relación intermedia entre Paquete y Actividades (tabla many-to-many explícita).
    """
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE)

    class Meta:
        db_table = 'paquete_actividades'
        verbose_name = 'Actividad del Paquete'
        verbose_name_plural = 'Actividades del Paquete'

    def __str__(self):
        return f"{self.paquete.nombre} - {self.actividad.nombre}"