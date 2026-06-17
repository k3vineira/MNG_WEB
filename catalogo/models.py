from django.db import models
from django.conf import settings
from django.utils import timezone


class Temporada(models.Model):
    # Definimos las opciones
    ESTADOS = [
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
    ]

    nombre = models.CharField(
        max_length=50, verbose_name='Nombre de la Temporada')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    # Agregamos el campo estado
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')

    class Meta:
        verbose_name = 'Temporada'
        verbose_name_plural = 'Temporadas'

    def __str__(self):
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
        return self.nombre

    @property
    def precio_minimo(self):
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
        return f"{self.paquete.nombre} - {self.temporada.nombre}"


class PaqueteActividad(models.Model):
    # Dejamos únicamente estas dos relaciones. Django creará de forma interna
    # las columnas 'paquete_id' y 'actividad_id' en la base de datos.
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE)

    class Meta:
        db_table = 'paquete_actividades'
        verbose_name = 'Actividad del Paquete'
        verbose_name_plural = 'Actividades del Paquete'
