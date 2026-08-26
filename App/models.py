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
        
# ==============================================================================
# AUDITORIA
# ==============================================================================
"""
Modelo de datos para la auditoría del sistema registrada para los usuarios.
"""
from django.conf import settings
from django.db import models

class Auditoria(models.Model):
    """
    Registro de auditoría del sistema sobre acciones realizadas por los usuarios.
    """
    id = models.AutoField(primary_key=True)
    acciones_realizada = models.CharField(max_length=255)
    tabla_afectada = models.CharField(max_length=100)
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    valor_anterior = models.TextField(blank=True, null=True)
    nuevo_valor = models.TextField(blank=True, null=True)
    codigo_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auditorias')

    class Meta:
        ordering = ['-fecha', '-hora']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.acciones_realizada} - {self.codigo_usuario.username}'


# ==============================================================================
# AUTENTICACION
# ==============================================================================
"""
Modelos de datos para la aplicación de autenticación.
Actualmente no define modelos propios, ya que utiliza el modelo de usuario personalizado de la aplicación 'usuarios'.
"""
from django.db import models


# ==============================================================================
# CATALOGO
# ==============================================================================
"""
Modelos de datos para el catálogo de paquetes turísticos.
Incluye Temporada, Categoría, Actividades, Paquete, Tarifa y PaqueteActividad.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import re

def validar_punto_encuentro(value):
    val_str = str(value).strip()
    if val_str.isdigit():
        raise ValidationError('El punto de encuentro no puede ser solo números. Ingresa un lugar o dirección válida.')
    if not re.search('[a-zA-ZáéíóúÁÉÍÓÚñÑ]', val_str):
        raise ValidationError('El punto de encuentro debe incluir texto o el nombre de un lugar.')


# ==============================================================================
# COMUNIDAD
# ==============================================================================
"""
Modelos de datos para la comunidad: Calificaciones, Blog, PQRS y Seguimiento.
"""
from django.db import models
from django.urls import reverse
from django.conf import settings

class Calificacion(models.Model):
    """
    Calificación y reseña de una experiencia o reserva de un paquete turístico
    realizada por un cliente o usuario registrado.
    """
    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey('Reserva', on_delete=models.SET_NULL, related_name='calificaciones', verbose_name='Reserva Calificada', null=True, blank=True)
    tipo = models.CharField(max_length=20, default='experiencia', verbose_name='Tipo', help_text='Tipo de reseña: experiencia, pregunta, etc.')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    puntaje_estrellas = models.PositiveSmallIntegerField(default=5, verbose_name='Puntaje / Estrellas')
    comentario = models.TextField(verbose_name='Comentario / Reseña')
    visible = models.BooleanField(default=True, verbose_name='¿Visible?')
    admin_respuesta = models.TextField(blank=True, null=True, verbose_name='Respuesta del Admin')
    fecha_calificacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Calificación')

    @property
    def valoracion(self):
        """Alias para puntaje_estrellas."""
        return self.puntaje_estrellas

    @valoracion.setter
    def valoracion(self, value):
        self.puntaje_estrellas = value

    @property
    def mensaje(self):
        """Alias para comentario."""
        return self.comentario

    @mensaje.setter
    def mensaje(self, value):
        self.comentario = value

    @property
    def fecha_creacion(self):
        """Alias para fecha_calificacion."""
        return self.fecha_calificacion

    class Meta:
        db_table = 'comunidad_calificacion'
        ordering = ['-fecha_calificacion']
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'

    def __str__(self):
        """Retorna el título de la calificación y el puntaje en estrellas."""
        return f'{self.titulo} - {self.puntaje_estrellas} estrellas'
Resena = Calificacion
Comentario = Calificacion


# ==============================================================================
# GUIAS
# ==============================================================================
from django.db import models

class PlanGuia(models.Model):
    """
    Modelo que representa la entidad 'plan_guia' del MER.
    Permite asignar un guía turístico a un paquete específico con fechas e idioma de servicio.
    """
    id = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [('activo', 'Activo'), ('inactivo', 'Inactivo'), ('completado', 'Completado')]
    idioma_servicio = models.CharField(max_length=50, verbose_name='Idioma del Servicio')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_inicio_plan = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin_plan = models.DateField(verbose_name='Fecha de Fin')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name='Estado')
    guia = models.ForeignKey('GuiaTuristico', on_delete=models.CASCADE, related_name='planes_guia', db_column='codigo_guia_turistico', verbose_name='Guía Turístico')
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='planes_guia', db_column='codigo_paquete', verbose_name='Paquete')

    class Meta:
        db_table = 'plan_guia'
        verbose_name = 'Plan Guía'
        verbose_name_plural = 'Planes Guía'

    def __str__(self):
        nombre_guia = self.guia.usuario.nombre_completo
        return f'Guía: {nombre_guia} - Paquete: {self.paquete.nombre} ({self.fecha_inicio_plan} a {self.fecha_fin_plan})'


# ==============================================================================
# IA
# ==============================================================================
from django.db import models


# ==============================================================================
# PAGOS
# ==============================================================================
"""
Modelo de datos para los comprobantes de pago enviados por los usuarios.
"""
import os
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

class Pago(models.Model):
    """
    Pago subido por un usuario para verificar el pago de una reserva o multa.
    El administrador puede aprobarlo o rechazarlo.
    """
    id = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [('pendiente', 'Pendiente de revisión'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')]
    reserva = models.OneToOneField('Reserva', on_delete=models.SET_NULL, null=True, blank=True, related_name='pago', verbose_name='Reserva')
    referencia = models.CharField(max_length=100, verbose_name='Número de referencia / transacción', help_text='Número de comprobante, transacción o referencia bancaria')
    banco_origen = models.CharField(max_length=100, verbose_name='Banco / medio de pago')
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, verbose_name='Monto pagado')
    imagen_comprobante = models.ImageField(upload_to='comprobantes/%Y/%m/', verbose_name='Imagen del comprobante')
    descripcion = models.TextField(blank=True, verbose_name='Descripción / nota adicional')
    estado_transaccion = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    nota_admin = models.TextField(blank=True, verbose_name='Nota del administrador')
    fecha_pago = models.DateTimeField(default=timezone.now, verbose_name='Fecha exacta del pago bancario')
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de envío')
    fecha_revision = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de revisión')

    class Meta:
        db_table = 'pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_envio']

    def __str__(self):
        """Retorna el ID, usuario y estado del pago como representación textual."""
        return f'Pago #{self.pk} — {self.usuario.username} — {self.get_estado_transaccion_display()}'

    def clean(self):
        super().clean()
        if self.estado_transaccion == 'aprobado':
            if not self.banco_origen:
                raise ValidationError({'banco_origen': 'Debe especificar el banco de origen para aprobar el comprobante.'})
            if not self.monto:
                raise ValidationError({'monto': 'Debe especificar el monto pagado para aprobar el comprobante.'})
            if self.reserva and self.monto < self.reserva.monto_total:
                raise ValidationError({'monto': 'El monto pagado no puede ser menor al monto total de la reserva.'})
        elif self.estado_transaccion == 'rechazado':
            if not self.nota_admin:
                raise ValidationError({'nota_admin': 'Debe justificar el rechazo añadiendo una nota del administrador.'})

    def save(self, *args, **kwargs):
        self.clean()
        if self.estado_transaccion == 'aprobado' and self.reserva:
            self.reserva.estado = 'confirmada'
            self.reserva.save()
        elif self.estado_transaccion == 'rechazado' and self.reserva and (self.reserva.estado == 'pendiente'):
            pass
        super().save(*args, **kwargs)

    def nombre_archivo(self):
        """
        Retorna el nombre del archivo de imagen del comprobante.

        Returns:
             str: El nombre base del archivo, o '—' si no hay imagen.
        """
        return os.path.basename(self.imagen_comprobante.name) if self.imagen_comprobante else '—'

class Factura(models.Model):
    """
    Modelo que representa la entidad 'factura' del MER.
    Registra los datos de facturación formal vinculados a una reserva y a su respectivo pago.
    """
    id = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [('emitida', 'Emitida'), ('anulada', 'Anulada'), ('pagada', 'Pagada')]
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Emisión')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='emitida', verbose_name='Estado')
    valor_subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor Subtotal')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor Total')
    reserva = models.OneToOneField('Reserva', on_delete=models.CASCADE, related_name='factura', db_column='codigo_reserva', verbose_name='Reserva')
    pago = models.ForeignKey(Pago, on_delete=models.SET_NULL, null=True, blank=True, related_name='facturas', db_column='codigo_pago', verbose_name='Pago')

    class Meta:
        db_table = 'factura'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return f'Factura #{self.pk} — Reserva #{self.reserva.id} — Total: ${self.valor_total}'


# ==============================================================================
# PROMOCIONES
# ==============================================================================
"""
Modelos de datos para las promociones y banners publicitarios del sitio.
"""
from django.db import models

class Promocion(models.Model):
    """Promoción o descuento aplicado a un paquete turístico durante un período determinado."""
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name='Nombre de la promoción')
    descripcion = models.TextField(verbose_name='Descripción')
    descuento = models.PositiveIntegerField(verbose_name='Porcentaje de descuento')
    fecha_fin = models.DateField(verbose_name='Fecha de fin')
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    codigo_promocion = models.CharField(max_length=20, unique=True, verbose_name='Código de promoción')
    condiciones = models.TextField(blank=True, null=True, verbose_name='Condiciones')
    codigo_cupon = models.CharField(max_length=30, blank=True, null=True, verbose_name='Código de cupón')
    activa = models.BooleanField(default=True, verbose_name='¿Activa?')

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'

    def __str__(self):
        """Retorna el nombre y porcentaje de descuento de la promoción."""
        return f'{self.nombre} ({self.descuento}%)'

class PaquetePromocion(models.Model):
    """
    Entidad intermedia que asocia un Paquete, una Promocion y una Tarifa.
    Equivale a la tabla intermedia 'paquete_promociones' del MER.
    """
    id = models.AutoField(primary_key=True)
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='paquete_promociones', verbose_name='Paquete')
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, related_name='paquete_promociones', verbose_name='Promoción')

    class Meta:
        db_table = 'paquete_promociones'
        verbose_name = 'Paquete Promoción'
        verbose_name_plural = 'Paquetes Promociones'

    def __str__(self):
        return f'{self.paquete.nombre} - {self.promocion.nombre}'


# ==============================================================================
# RESERVAS
# ==============================================================================
"""
Modelos de datos para reservas y cancelaciones de paquetes turísticos.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Cancelacion(models.Model):
    """
    Solicitud de cancelación de una reserva realizada por un usuario.
    Calcula automáticamente la penalidad según los días de antelación.
    """
    id = models.AutoField(primary_key=True)
    ESTADOS_CANCELACION = [('pendiente', 'Pendiente'), ('aceptada', 'Aceptada'), ('rechazada', 'Rechazada')]
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='cancelaciones')
    motivo = models.TextField()
    penalidad = models.IntegerField(default=0, verbose_name='Penalidad Aplicada')
    estado = models.CharField(max_length=20, choices=ESTADOS_CANCELACION, default='pendiente', verbose_name='Estado')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Solicitud')
    fecha_reembolso = models.DateField(null=True, blank=True, verbose_name='Fecha de Reembolso')
    valor_reembolsado = models.IntegerField(null=True, blank=True, default=0, verbose_name='Valor Reembolsado')
    imagen_comprobante = models.ImageField(upload_to='cancelaciones/', null=True, blank=True, verbose_name='Imagen del Comprobante')

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
                self.penalidad = int(valor_reserva * 0.1)
            elif 5 <= dias_antelacion <= 15:
                self.penalidad = int(valor_reserva * 0.5)
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
        return f'Cancelación de Reserva #{self.reserva.id} - {self.get_estado_display()}'


# ==============================================================================
# SEGUROS
# ==============================================================================
from django.db import models
from django.conf import settings

class Poliza(models.Model):
    """
    Define los tipos de planes de seguros disponibles (ej: Plan Básico, Plan Premium).
    Equivale a la entidad 'poliza' del MER de draw.io.
    """
    id = models.AutoField(primary_key=True)
    nombre_aseguradora = models.CharField(max_length=100, verbose_name='Nombre de la Aseguradora / Plan')
    descripcion = models.TextField(verbose_name='Descripción de Coberturas')
    precio_diario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio por Día')
    estado = models.BooleanField(default=True, verbose_name='¿Póliza Activa?')

    class Meta:
        verbose_name = 'Póliza / Plan de Seguro'
        verbose_name_plural = 'Pólizas / Planes de Seguro'

    def __str__(self):
        return f'{self.nombre_aseguradora} (${self.precio_diario}/día)'

class SeguroViaje(models.Model):
    """
    Representa la adquisición de un seguro por parte de un usuario para una reserva específica.
    Equivale a la entidad 'seguro_viaje' del MER de draw.io.
    """
    id = models.AutoField(primary_key=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='seguro_viaje', verbose_name='Reserva Asociada', null=True, blank=True)
    poliza = models.ForeignKey(Poliza, on_delete=models.PROTECT, related_name='seguros_viaje', verbose_name='Póliza Asociada')
    numero_poliza = models.CharField(max_length=50, unique=True, verbose_name='Número de Póliza')
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Emisión')
    costo_seguro = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name='Costo de Seguro')

    class Meta:
        verbose_name = 'Seguro de Viaje Emitido'
        verbose_name_plural = 'Seguros de Viaje Emitidos'

    def save(self, *args, **kwargs):
        if self.reserva and self.poliza:
            dias = self.reserva.paquete.dias_duracion
            self.costo_seguro = self.poliza.precio_diario * dias
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Seguro {self.poliza.nombre_aseguradora} para Reserva {(self.reserva.id if self.reserva else 'N/A')}"


# ==============================================================================
# USUARIOS
# ==============================================================================
"""
Modelos de datos para la gestión de usuarios: Usuario personalizado, Cliente y Guía Turístico.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Cliente(models.Model):
    """
    Perfil extendido para usuarios con rol de Cliente/Turista.
    Asociado mediante una relación uno-a-uno con el modelo Usuario.
    """
    id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente', verbose_name='Cuenta de Usuario')
    pais = models.CharField(max_length=100, blank=True, verbose_name='País')
    departamento = models.CharField(max_length=100, blank=True, verbose_name='Departamento')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')

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
    id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='guia', verbose_name='Cuenta de Usuario')
    numero_tarjeta_profesional = models.CharField(max_length=50, blank=True, verbose_name='Licencia de Turismo')
    experiencia_anos = models.PositiveIntegerField(default=0, verbose_name='Años de Experiencia')
    experiencia_fecha = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio de Experiencia')
    descripcion_experiencia = models.TextField(blank=True, verbose_name='Descripción de la Experiencia')
    entidad_salud = models.CharField(max_length=100, blank=True, null=True, verbose_name='Entidad de Salud')

    class Meta:
        verbose_name = 'Guía Turístico'
        verbose_name_plural = 'Guías Turísticos'

    def __str__(self):
        """Retorna 'Guía:' seguido del nombre completo del usuario."""
        return f'Guía: {self.usuario.nombre_completo}'

