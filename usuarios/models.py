from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('admin',  'Administrador'),
        ('guia',   'Guía Turístico'),
        ('cliente','Cliente'),
    ]
    rol      = models.CharField(max_length=10, choices=ROL_CHOICES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True)
    foto     = models.ImageField(upload_to='perfiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"

class Cliente(models.Model):
    usuario      = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_cliente')
    documento    = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion    = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.usuario)

class GuiaTuristico(models.Model):
    usuario      = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_guia')
    licencia     = models.CharField(max_length=50, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    activo       = models.BooleanField(default=True)

    def __str__(self):
        return str(self.usuario)

class Auditoria(models.Model):
    usuario  = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion   = models.CharField(max_length=200)
    modulo   = models.CharField(max_length=50)
    fecha    = models.DateTimeField(auto_now_add=True)
    ip       = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']