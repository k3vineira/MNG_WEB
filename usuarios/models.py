from django.db import models
from django.contrib.auth.models import AbstractUser

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