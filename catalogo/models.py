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

    nombre = models.CharField(
        max_length=50, verbose_name='Nombre de la Temporada')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')

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
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre de la Categoría')
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
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel_dificultad = models.CharField(
        max_length=10, choices=NIVEL_CHOICES, verbose_name='Nivel de Dificultad')
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido')
    recomendacion_salud = models.TextField(
        verbose_name='Recomendaciones de Salud')
    estado = models.BooleanField(
        default=True, blank=True, verbose_name='¿Está Activa?')
    apto_para_menores = models.BooleanField(
        default=True, verbose_name='¿Apto para menores?')

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
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre del Paquete')
    descripcion = models.TextField(verbose_name='Descripción')
    dias_duracion = models.PositiveIntegerField(
        verbose_name='Días de Duración', default=1)
    noches_duracion = models.PositiveIntegerField(
        verbose_name='Noches de Duración', default=0)
    punto_encuentro = models.CharField(max_length=200)
    hora_encuentro = models.TimeField()
    categoria = models.ForeignKey(
        Categoria, models.CASCADE, related_name='paquetes')
    actividades = models.ManyToManyField(
        Actividades, through='PaqueteActividad')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activo?')

    def __str__(self):
        """Retorna el nombre del paquete como representación textual."""
        return self.nombre

    @property
    def precio_minimo(self):
        """
        Calcula el precio mínimo del paquete basado en las tarifas activas de la temporada actual.

        Returns:
            int: El precio mínimo por adulto para la temporada vigente, o 0 si no hay tarifas activas.
        """
        fecha_hoy = timezone.now().date()

        tarifas_validas = self.tarifas.filter(
            estado='activa',
            temporada__estado='activa',
            temporada__fecha_inicio__lte=fecha_hoy,
            temporada__fecha_fin__gte=fecha_hoy
        )

        if tarifas_validas.exists():
            return min(t.precio_adulto for t in tarifas_validas)

        tarifa_estandar = self.tarifas.filter(
            estado='activa',
            temporada__nombre__icontains="Estándar"
        ).first()

        if tarifa_estandar:
            return tarifa_estandar.precio_adulto

        return 0

    @property
    def apto_para_menores(self):
        """
        Determina si el paquete es apto para menores de edad.

        Returns:
            bool: True si todas las actividades son aptas para menores, False si alguna no lo es.
        """
        # Si tiene al menos una actividad no apta, el paquete no es apto para menores
        return not self.actividades.filter(apto_para_menores=False).exists()


class Tarifa(models.Model):
    """
    Tarifa de precio para un paquete en una temporada específica.
    """
    paquete = models.ForeignKey(
        Paquete, on_delete=models.CASCADE, related_name='tarifas')
    temporada = models.ForeignKey(
        Temporada, on_delete=models.CASCADE, related_name='tarifas')
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

    
    ESTADOS = [
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
    ]

    nombre = models.CharField(
        max_length=50, verbose_name='Nombre de la Temporada')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')

    class Meta:
        verbose_name = 'Temporada'
        verbose_name_plural = 'Temporadas'

    def __str__(self):
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre de la Categoría')
    descripcion = models.TextField(verbose_name='Descripción')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return self.nombre


class Actividades(models.Model):
    NIVEL_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baja', 'Baja'),
    ]
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel_dificultad = models.CharField(
        max_length=10, choices=NIVEL_CHOICES, verbose_name='Nivel de Dificultad')
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido')
    recomendacion_salud = models.TextField(
        verbose_name='Recomendaciones de Salud')
    estado = models.BooleanField(
        default=True, blank=True, verbose_name='¿Está Activa?')
    apto_para_menores = models.BooleanField(
        default=True, verbose_name='¿Apto para menores?')

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return self.nombre


class Paquete(models.Model):
    imagen = models.ImageField(upload_to='destinos/', null=True, blank=True)
    nombre = models.CharField(
        max_length=100, verbose_name='Nombre del Paquete')
    descripcion = models.TextField(verbose_name='Descripción')
    dias_duracion = models.PositiveIntegerField(
        verbose_name='Días de Duración', default=1)
    noches_duracion = models.PositiveIntegerField(
        verbose_name='Noches de Duración', default=0)
    punto_encuentro = models.CharField(max_length=200)
    hora_encuentro = models.TimeField()
    categoria = models.ForeignKey(
        Categoria, models.CASCADE, related_name='paquetes')
    actividades = models.ManyToManyField(
        Actividades, through='PaqueteActividad')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activo?')

    def __str__(self):
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return self.nombre

    @property
    def precio_minimo(self):
        """
        precio_minimo.
        
        :return: Respuesta de la función.
        """
        fecha_hoy = timezone.now().date()

        tarifas_validas = self.tarifas.filter(
            estado='activa',
            temporada__estado='activa',
            temporada__fecha_inicio__lte=fecha_hoy,
            temporada__fecha_fin__gte=fecha_hoy
        )

        if tarifas_validas.exists():
            return min(t.precio_adulto for t in tarifas_validas)

        tarifa_estandar = self.tarifas.filter(
            estado='activa',
            temporada__nombre__icontains="Estándar"
        ).first()

        if tarifa_estandar:
            return tarifa_estandar.precio_adulto

        return 0

    @property
    def apto_para_menores(self):
        """
        apto_para_menores.
        
        :return: Respuesta de la función.
        """
        # Si tiene al menos una actividad no apta, el paquete no es apto para menores
        return not self.actividades.filter(apto_para_menores=False).exists()


class Tarifa(models.Model):
    paquete = models.ForeignKey(
        Paquete, on_delete=models.CASCADE, related_name='tarifas')
    temporada = models.ForeignKey(
        Temporada, on_delete=models.CASCADE, related_name='tarifas')
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
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return f"{self.paquete.nombre} - {self.temporada.nombre}"


class PaqueteActividad(models.Model):
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE)

    class Meta:
        db_table = 'paquete_actividades'
        verbose_name = 'Actividad del Paquete'
        verbose_name_plural = 'Actividades del Paquete'
