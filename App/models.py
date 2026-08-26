from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# ==============================================================================
# USUARIO
# ==============================================================================

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
        verbose_name='Tipo de Documento'
    )
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Documento'
    )
    telefono = models.CharField(
        max_length=15,
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
        """Validación limpia del modelo."""
        super().clean()

    def save(self, *args, **kwargs):
        """
        Asigna automáticamente el rol ADMIN a superusuarios.

        Args:
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de clave-valor adicionales.
        """
        # Garantiza que si es superusuario de Django, tome automáticamente el rol ADMIN
        if self.is_superuser and self.rol != self.Roles.ADMIN:
            self.rol = self.Roles.ADMIN

        super().save(*args, **kwargs)

    # --- ALIAS EN ESPAÑOL LATAM ---
    @property
    def nombre_usuario(self):
        """Alias en español LATAM para username."""
        return self.username

    @nombre_usuario.setter
    def nombre_usuario(self, value):
        self.username = value

    @property
    def nombres(self):
        """Alias en español LATAM para first_name."""
        return self.first_name

    @nombres.setter
    def nombres(self, value):
        self.first_name = value

    @property
    def apellidos(self):
        """Alias en español LATAM para last_name."""
        return self.last_name

    @apellidos.setter
    def apellidos(self, value):
        self.last_name = value

    @property
    def es_activo(self):
        """Alias en español LATAM para is_active."""
        return self.is_active

    @es_activo.setter
    def es_activo(self, value):
        self.is_active = value

    @property
    def es_personal(self):
        """Alias en español LATAM para is_staff."""
        return self.is_staff

    @es_personal.setter
    def es_personal(self, value):
        self.is_staff = value

    @property
    def es_superusuario(self):
        """Alias en español LATAM para is_superuser."""
        return self.is_superuser

    @es_superusuario.setter
    def es_superusuario(self, value):
        self.is_superuser = value

    @property
    def fecha_registro(self):
        """Alias en español LATAM para date_joined."""
        return self.date_joined

    @property
    def ultimo_login(self):
        """Alias en español LATAM para last_login."""
        return self.last_login

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

# ==============================================================================
# TEMPORADA
# ==============================================================================
class Temporada(models.Model):
    """
    Representa una temporada turística con fechas de inicio y fin.
    """
    id = models.AutoField(primary_key=True)
    ESTADOS = [
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
    ]

    nombre = models.CharField(max_length=50, verbose_name='Nombre de la Temporada')
    descripcion = models.TextField(verbose_name='Descripción de la Temporada')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')

    class Meta:
        verbose_name = 'Temporada'
        verbose_name_plural = 'Temporadas'

    def __str__(self):
        """Retorna el nombre de la temporada como representación textual."""
        return self.nombre
    
# ==============================================================================
# CATEGORIA
# ==============================================================================


class Categoria(models.Model):
    """
    Categoría que agrupa paquetes turísticos similares (ej. Aventura, Cultura).
    """
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Categoría')
    descripcion = models.TextField(verbose_name='Descripción')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        """Retorna el nombre de la categoría como representación textual."""
        return self.nombre
# ==============================================================================
#  ACTIVIDADES
# ==============================================================================

class Actividades(models.Model):
    """
    Actividad turística que puede ser incluida en uno o varios paquetes.
    """
    id = models.AutoField(primary_key=True)
    NIVEL_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baja', 'Baja'),
    ]
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel_dificultad = models.CharField(max_length=10, choices=NIVEL_CHOICES, verbose_name='Nivel de Dificultad')
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido')
    recomendaciones = models.TextField(verbose_name='Recomendaciones')
    estado = models.BooleanField(default=True, blank=True, verbose_name='¿Está Activa?')
    apto_menores = models.BooleanField(default=True, verbose_name='¿Apto para menores?')

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        """Retorna el nombre de la actividad como representación textual."""
        return self.nombre

def validar_punto_encuentro(value):
    val_str = str(value).strip()
    if val_str.isdigit():
        raise ValidationError("El punto de encuentro no puede ser solo números. Ingresa un lugar o dirección válida.")
    if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', val_str):
        raise ValidationError("El punto de encuentro debe incluir texto o el nombre de un lugar.")
    
# ==============================================================================
# PAQUETE
# ==============================================================================
class Paquete(models.Model):
    """
    Paquete turístico ofrecido por Monagua, conformado por actividades y con tarifas por temporada.
    """
    id = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to='destinos/', verbose_name='Imagen del Destino')
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Paquete')
    descripcion = models.TextField(verbose_name='Descripción')
    dias_duracion = models.PositiveIntegerField(verbose_name='Días de Duración', default=1,validators=[MinValueValidator(1, message="Los días de duración deben ser al menos 1.")])
    noches_duracion = models.PositiveIntegerField(verbose_name='Noches de Duración', default=1,validators=[MinValueValidator(1, message="Las noches de duración deben ser al menos 1.")])
    punto_encuentro = models.CharField(max_length=200, validators=[validar_punto_encuentro])
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
            return not any(not getattr(a, 'apto_menores', True) for a in all_actividades)
        return True

# ==============================================================================
# TARIFA
# ==============================================================================

class Tarifa(models.Model):
    """
    Tarifa de precio para un paquete en una temporada específica.
    """
    id = models.AutoField(primary_key=True)
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

# ==============================================================================
# PAQUETE ACTIVIDADES
# ==============================================================================
class PaqueteActividad(models.Model):
    """
    Relación intermedia entre Paquete y Actividades (tabla many-to-many explícita).
    """
    id = models.AutoField(primary_key=True)
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE)
    DIFICULTAD_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baja', 'Baja'),
    ]
    dificultad_nivel = models.CharField(
        max_length=10,
        choices=DIFICULTAD_CHOICES,
        default='Media',
        verbose_name='Nivel de Dificultad'
    )

    class Meta:
        db_table = 'paquete_actividades'
        verbose_name = 'Actividad del Paquete'
        verbose_name_plural = 'Actividades del Paquete'

    def __str__(self):
        return f"{self.paquete.nombre} - {self.actividad.nombre}"

# ==============================================================================
# BLOG
# ==============================================================================
class Blog(models.Model):
    """Entrada de blog publicada por un administrador o autor en Mongua Turismo."""
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blogs_publicados",
        verbose_name="Autor / Administrador",
    )
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    informacion_adicional = models.TextField(blank=True)
    imagen_destacada = models.ImageField(upload_to="blog/", blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(
        default=True, verbose_name="¿Está Publicado?"
    )

    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"

    def get_absolute_url(self):
        """Retorna la URL de detalle de este post del blog."""
        return reverse("detalle_blog", kwargs={"id": self.id})

    def __str__(self):
        """Retorna el título y el autor del blog."""
        return f"{self.titulo} - Por: {self.usuario.get_full_name() or self.usuario.username}"

# ==============================================================================
# PQRS
# ==============================================================================

class PQRS(models.Model):
    """Solicitud de Petición, Queja, Reclamo o Sugerencia enviada por un usuario."""
    id = models.AutoField(primary_key=True)
    TIPO_CHOICES = [
        ('peticion', 'Petición'),
        ('queja', 'Queja'),
        ('reclamo', 'Reclamo'),
        ('sugerencia', 'Sugerencia'),
    ]
    ESTADO_CHOICES = [
        ('abierto', 'Abierto'),
        ('en_proceso', 'En Proceso'),
        ('cerrado', 'Cerrado'),
    ]
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pqrs',
        null=True,
        blank=True
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default='abierto'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'PQRS'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.asunto}'

# ==============================================================================
# SEGUIMIENTO
# ==============================================================================

class Seguimiento(models.Model):
    """Registro de seguimiento y respuestas a una solicitud PQRS por parte de un usuario o administrador."""
    
    id = models.AutoField(primary_key=True)
    pqrs = models.ForeignKey(PQRS, on_delete=models.CASCADE, related_name='seguimientos')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seguimientos',
        null=True,
        blank=True,
        verbose_name='Usuario / Administrador'
    )
    respuesta = models.TextField(verbose_name='Mensaje / Respuesta')
    fecha_respuesta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Respuesta')

    class Meta:
        db_table = 'seguimiento'
        ordering = ['fecha_respuesta']
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'

    def __str__(self):
        return f'Seguimiento de {self.pqrs} - {self.fecha_respuesta.strftime("%Y-%m-%d %H:%M:%S")}'

# ==============================================================================
# RESERVA
# ==============================================================================
class Reserva(models.Model):
    id = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    # Relaciones apuntando a los modelos dentro del mismo archivo
    paquete = models.ForeignKey(
        'Paquete',
        on_delete=models.PROTECT,
        related_name='reservas',
        verbose_name='Paquete Reservado'
    )
    usuario = models.ForeignKey(
        'Usuario', # O settings.AUTH_USER_MODEL si usas el modelo de Django
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Usuario',
        null=True,
        blank=True,
    )
    fecha = models.DateField(verbose_name='Fecha de Reserva')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    numero_adultos = models.PositiveIntegerField(verbose_name='Número de Adultos', default=1)
    numero_menores = models.PositiveIntegerField(verbose_name='Número de Menores', default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    motivo_cancelacion = models.TextField(null=True, blank=True, verbose_name='Motivo de Cancelación')
    monto_total = models.IntegerField(verbose_name='Monto Total', editable=False)
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'paquete', 'fecha'],
                name='unique_usuario_paquete_fecha'
            )
        ]

    def save(self, *args, **kwargs):
        if self.paquete and self.fecha:
            try:
                # Búsqueda directa sin imports
                temporada = Temporada.objects.filter(
                    fecha_inicio__lte=self.fecha, 
                    fecha_fin__gte=self.fecha
                ).first()

                if temporada:
                    tarifa = Tarifa.objects.filter(
                        paquete=self.paquete, 
                        temporada=temporada
                    ).first()

                    if tarifa:
                        num_adultos = self.numero_adultos or 0
                        num_menores = self.numero_menores or 0
                        base_monto = (tarifa.precio_adulto * num_adultos) + (tarifa.precio_menor * num_menores)

                        descuento = 0
                        try:
                            paquete_promo = self.paquete.paquetepromociones_set.filter(
                                promocion__estado=True
                            ).first()

                            if paquete_promo and paquete_promo.promocion:
                                descuento = getattr(paquete_promo.promocion, 'porcentaje_descuento', 0) or getattr(paquete_promo.promocion, 'descuento', 0)
                        except Exception:
                            descuento = 0

                        if descuento > 0:
                            self.monto_total = int(base_monto * (100 - descuento) / 100)
                        else:
                            self.monto_total = int(base_monto)
                    else:
                        self.monto_total = 0
                else:
                    self.monto_total = 0

            except Exception:
                self.monto_total = 0

        elif not getattr(self, 'monto_total', None):
            self.monto_total = 0

        super().save(*args, **kwargs)
        
    