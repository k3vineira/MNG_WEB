"""
Modelos de datos para la gestión de usuarios: Usuario personalizado, Cliente y Guía Turístico.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser con campos adicionales
    como rol, tipo de documento, teléfono e imagen de perfil.
    """
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        CLIENTE = 'CLIENTE', 'Cliente'
        GUIA = 'GUIA', 'Guía Turístico'

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de Ciudadanía'
        CE = 'CE', 'Cédula de Extranjería'
        PASAPORTE = 'PASAPORTE', 'Pasaporte'

    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'Ya existe un usuario registrado con este correo electrónico.',
        },
        verbose_name='Correo Electrónico'
    )

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CLIENTE,
        verbose_name='Rol'
    )
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        blank=True,
        null=True,
        verbose_name='Tipo de Documento'
    )
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Número de Documento'
    )
    telefono = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='Teléfono'
    )
    residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Residencia de Origen'
    )
    imagen_perfil = models.ImageField(
        upload_to='perfiles/',
        null=True,
        blank=True,
        verbose_name='Imagen de Perfil'
    )

    def clean(self):
        """
        Normaliza el número de documento vacío a None para evitar errores de integridad.
        """
        super().clean()
        # Evita errores de IntegrityError si se guarda como string vacío ("")
        if self.numero_documento == "":
            self.numero_documento = None

    def save(self, *args, **kwargs):
        """
        Asigna automáticamente el rol ADMIN a superusuarios y normaliza el número de documento.

        Args:
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de clave-valor adicionales.
        """
        # Garantiza que si es superusuario de Django, tome automáticamente el rol ADMIN
        if self.is_superuser and self.rol != self.Roles.ADMIN:
            self.rol = self.Roles.ADMIN

        # También limpiar en el save() en caso de que no se llame a clean()
        if self.numero_documento == "":
            self.numero_documento = None

        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def avatar_url(self):
        """Retorna la URL de la imagen o una por defecto si no existe."""
        if self.imagen_perfil and hasattr(self.imagen_perfil, 'url'):
            return self.imagen_perfil.url
        return f"{settings.STATIC_URL}img/avatar_pred.webp"

    @property
    def es_guia(self):
        """Retorna si el usuario tiene el rol de Guía Turístico."""
        return self.rol == self.Roles.GUIA

    @property
    def es_turista(self):
        """Retorna si el usuario tiene el rol de Cliente / Turista."""
        return self.rol == self.Roles.CLIENTE

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        """Retorna el nombre de usuario y su rol como representación textual."""
        return f"{self.username} - {self.rol}"


class Cliente(models.Model):
    """
    Perfil extendido para usuarios con rol de Cliente/Turista.
    Asociado mediante una relación uno-a-uno con el modelo Usuario.
    """
    # Relación uno a uno que mapea "USUARIO es un CLIENTE"
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='cliente',
        verbose_name='Cuenta de Usuario'
    )
    pais = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='País'
    )
    departamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departamento'
    )
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad'
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        """Retorna el nombre completo del cliente como representación textual."""
        return self.usuario.nombre_completo


class GuiaTuristico(models.Model):
    """
    Perfil extendido para usuarios con rol de Guía Turístico.
    Asociado mediante una relación uno-a-uno con el modelo Usuario.
    """
    # Relación uno a uno que mapea "USUARIO es un GUIA_TURISTICO"
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='guia',
        verbose_name='Cuenta de Usuario'
    )
    licencia_turismo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Licencia de Turismo'
    )
    experiencia_anos = models.PositiveIntegerField(
        default=0,
        verbose_name='Años de Experiencia'
    )
    biografia = models.TextField(
        blank=True,
        verbose_name='Biografía'
    )

    class Meta:
        verbose_name = 'Guía Turístico'
        verbose_name_plural = 'Guías Turísticos'

    def __str__(self):
        """Retorna 'Guía:' seguido del nombre completo del usuario."""
        return f"Guía: {self.usuario.nombre_completo}"
