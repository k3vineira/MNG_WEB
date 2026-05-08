from django.db import models

class Categoria(models.Model):
    nombre_categoria    = models.CharField(max_length=100)
    descripcion_categoria = models.TextField(blank=True)
    icono               = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.nombre_categoria

class Paquete(models.Model):
    categoria           = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    nombre_paquete      = models.CharField(max_length=150)
    descripcion_paquete = models.TextField()
    precio_base         = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada   = models.CharField(max_length=50)   # ej: "3 días / 2 noches"
    capacidad_maxima    = models.PositiveIntegerField(default=20)
    imagen              = models.ImageField(upload_to='paquetes/', blank=True, null=True)
    activo              = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_paquete

class Actividad(models.Model):
    nombre_actividad      = models.CharField(max_length=150)
    descripcion_actividad = models.TextField(blank=True)
    duracion_horas        = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.nombre_actividad

class PaqueteActividad(models.Model):
    paquete   = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='actividades')
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    orden     = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('paquete', 'actividad')

class Horario(models.Model):
    paquete      = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='horarios')
    fecha_salida = models.DateField()
    fecha_regreso= models.DateField()
    cupos_disponibles = models.PositiveIntegerField()
    activo       = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.paquete} | {self.fecha_salida}"