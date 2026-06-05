from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 

class Usuario(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        CLIENTE = 'CLIENTE', 'Cliente'
        GUIA = 'GUIA', 'Guía Turístico'

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de Ciudadanía'
        CE = 'CE', 'Cédula de Extranjería'
        PASAPORTE = 'PAS', 'Pasaporte'

    rol = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CLIENTE, verbose_name='Rol')
    tipo_documento = models.CharField(max_length=20, choices=TipoDocumento.choices, blank=True)
    numero_documento = models.CharField(max_length=20, unique=True, null=True)
    telefono = models.CharField(max_length=15, blank=True)
    residencia = models.CharField(max_length=100, blank=True)
    imagen_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True, verbose_name='Imagen de Perfil')
    es_guia = models.BooleanField(default=False)

    @property
    def es_turista(self):
        return self.rol == self.Roles.CLIENTE and not self.es_guia and not self.is_staff and not self.is_superuser

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente')
    pais = models.CharField(max_length=50, blank=True)
    ciudad = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"
    
class GuiaTuristico(models.Model): 
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='guia')
    licencia_turismo = models.CharField(max_length=50, blank=True)
    experiencia_anos = models.PositiveIntegerField(default=0)
    biografia = models.TextField(blank=True)
    
    def __str__(self):
        return f"Guía: {self.usuario.username}"


class Comentario(models.Model):
    TIPO_CHOICES = [
        ('experiencia', 'Experiencia de viaje'),
        ('sugerencia', 'Sugerencia'),
        ('felicitacion', 'Felicitación'),
        ('queja', 'Queja'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Usuario'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='experiencia')
    paquete = models.ForeignKey(
        'catalogo.Paquete',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Paquete Turístico'
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    admin_respuesta = models.TextField(blank=True, verbose_name='Respuesta del Administrador')
    valoracion = models.IntegerField(default=5)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.usuario.get_full_name()} — {self.titulo}"

    def estrellas(self):
        return range(self.valoracion)

    def estrellas_vacias(self):
        return range(5 - self.valoracion)