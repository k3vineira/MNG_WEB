from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
import os
import json
import urllib.request
import logging
import ssl
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class PositiveTinyIntegerField(models.PositiveSmallIntegerField):
    def get_internal_type(self):
        return 'PositiveTinyIntegerField'

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'tinyint unsigned'
        return 'integer'

logger = logging.getLogger(__name__)

# ==============================================================================
# RESOLVEDOR DE UBICACIONES
# ==============================================================================
class LocationResolver:
    _cache_file = None
    _countries = {}
    _departments = {}
    _cities = {}
    _loaded = False

    @classmethod
    def _get_cache_path(cls):
        if cls._cache_file is None:
            cls._cache_file = os.path.join(settings.BASE_DIR, 'location_cache.json')
        return cls._cache_file

    @classmethod
    def load_data(cls):
        if cls._loaded:
            return

        cache_path = cls._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cls._countries = data.get('countries', {})
                    cls._departments = data.get('departments', {})
                    cls._cities = data.get('cities', {})
                    cls._loaded = True
                    return
            except Exception:
                pass

        cls._fetch_and_cache()

    @classmethod
    def _fetch_and_cache(cls):
        # 1. Fetch countries
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                'https://countriesnow.space/api/v0.1/countries',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                cls._countries = {}
                for item in res_data.get('data', []):
                    iso3 = item.get('iso3')
                    country = item.get('country')
                    if iso3 and country:
                        cls._countries[str(iso3).upper()] = country
        except Exception as e:
            logger.error("Error loading countries: %s", e)
            cls._countries = {'COL': 'Colombia'}

        # 2. Fetch Colombia departments and municipalities
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                'https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=1500',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                cls._departments = {}
                cls._cities = {}
                for item in res_data:
                    dept_code = item.get('cod_dpto')
                    dept_name = item.get('dpto')
                    muni_code = item.get('cod_mpio')
                    muni_name = item.get('nom_mpio')
                    if dept_code and dept_name:
                        cls._departments[str(dept_code)] = dept_name.title().strip()
                    if muni_code and muni_name:
                        cls._cities[str(muni_code)] = muni_name.title().strip()
        except Exception as e:
            logger.error("Error loading Colombia DANE data: %s", e)
            cls._departments = {}
            cls._cities = {}

        # Save to cache file
        cache_path = cls._get_cache_path()
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'countries': cls._countries,
                    'departments': cls._departments,
                    'cities': cls._cities
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error("Error writing location cache file: %s", e)

        cls._loaded = True

    @classmethod
    def resolve_country(cls, iso3):
        if not iso3:
            return ""
        cls.load_data()
        return cls._countries.get(str(iso3).upper(), str(iso3))

    @classmethod
    def resolve_department(cls, code):
        if code is None or code == "":
            return ""
        cls.load_data()
        return cls._departments.get(str(code), str(code))

    @classmethod
    def resolve_city(cls, code):
        if code is None or code == "":
            return ""
        cls.load_data()
        return cls._cities.get(str(code), str(code))

# ==============================================================================
# USUARIO
# ==============================================================================

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser con campos adicionales
    como rol, tipo de documento, teléfono e imagen de perfil.
    """
    id = models.BigAutoField(primary_key=True)

    class Roles(models.IntegerChoices):
        ADMIN = 1, 'Administrador'
        CLIENTE = 2, 'Cliente'
        GUIA = 3, 'Guía Turístico'

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de Ciudadanía'
        CE = 'CE', 'Cédula de Extranjería'
        PASAPORTE = 'PASAPORTE', 'Pasaporte'

    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nombre de Usuario'
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        error_messages={
            'unique': 'Ya existe un usuario registrado con este correo electrónico.',
        },
        verbose_name='Correo Electrónico'
    )

    last_login = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Último inicio de sesión'
    )

    rol = models.PositiveSmallIntegerField(
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

    # --- CAMPOS DE CLIENTE (FUSIONADOS) ---
    pais = models.CharField(
        max_length=3,
        blank=True,
        verbose_name='País'
    )
    departamento = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Departamento'
    )
    ciudad = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Ciudad'
    )

    # --- CAMPOS DE GUÍA TURÍSTICO (FUSIONADOS) ---
    numero_tarjeta_profesional = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Licencia de Turismo'
    )
    experiencia_anos = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Años de Experiencia'
    )
    experiencia_fecha = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio de Experiencia'
    )
    descripcion_experiencia = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción de la Experiencia'
    )
    entidad_salud = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Entidad de Salud'
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
    def pais_nombre(self):
        """Retorna el nombre completo del país."""
        return LocationResolver.resolve_country(self.pais)

    @property
    def departamento_nombre(self):
        """Retorna el nombre completo del departamento."""
        return LocationResolver.resolve_department(self.departamento)

    @property
    def ciudad_nombre(self):
        """Retorna el nombre completo de la ciudad/municipio."""
        return LocationResolver.resolve_city(self.ciudad)

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

    nombre = models.CharField(max_length=50, verbose_name='Nombre de la Temporada')
    descripcion = models.TextField(verbose_name='Descripción de la Temporada', null=True, blank=True)
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

    class Meta:
        verbose_name = 'Temporada'
        verbose_name_plural = 'Temporadas'

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'
                })

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
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la Categoría')
    descripcion = models.TextField(verbose_name='Descripción', null=True, blank=True)
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
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción', null=True, blank=True)
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido', null=True, blank=True)
    recomendaciones = models.TextField(verbose_name='Recomendaciones', null=True, blank=True)
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
    punto_encuentro = models.CharField(max_length=150, validators=[validar_punto_encuentro], verbose_name='Punto de Encuentro')
    hora_encuentro = models.TimeField()
    categoria = models.ForeignKey(Categoria, models.CASCADE, related_name='paquetes')
    actividades = models.ManyToManyField('Actividades', through='PaqueteActividad')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activo?')
    promociones = models.ManyToManyField('Promocion', through='PaquetePromocion', blank=True, verbose_name='Promociones')

    def __str__(self):
        return self.nombre

    @property
    def precio_minimo(self):
        fecha_hoy = timezone.now().date()
        all_tarifas = list(self.tarifas.all())

        validas = [
            t for t in all_tarifas
            if getattr(t, 'estado', False)
            and getattr(t, 'temporada', None)
            and t.temporada.estado
            and t.temporada.fecha_inicio <= fecha_hoy <= t.temporada.fecha_fin
        ]

        if validas:
            return min(t.precio_adulto for t in validas)

        estandar = next(
            (
                t for t in all_tarifas
                if getattr(t, 'estado', False)
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
    precio_adulto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio por Adulto')
    precio_menor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio por Menor')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

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
        unique_together = ('paquete', 'actividad')

    def __str__(self):
        return f"{self.paquete.nombre} - {self.actividad.nombre}"

# ==============================================================================
# PAQUETE PROMOCION
# ==============================================================================
class PaquetePromocion(models.Model):
    """
    Relación intermedia entre Paquete y Promocion (tabla many-to-many explícita).
    """
    id = models.AutoField(primary_key=True)
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    promocion = models.ForeignKey('Promocion', on_delete=models.CASCADE)
    valor_adulto_condescuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Valor Adulto con Descuento')
    valor_menor_condescuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Valor Menor con Descuento')

    class Meta:
        db_table = 'paquete_promocion'
        verbose_name = 'Promoción del Paquete'
        verbose_name_plural = 'Promociones del Paquete'
        unique_together = ('paquete', 'promocion')

    def __str__(self):
        return f"{self.paquete.nombre} - {self.promocion}"

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
    informacion_adicional = models.TextField(blank=True, null=True, verbose_name='Información Adicional')
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
        related_name='pqrs'
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=150)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='abierto'
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
    reserva = models.ForeignKey(
        'Reserva',
        on_delete=models.CASCADE,
        related_name='seguimientos',
        verbose_name='Reserva'
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
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    numero_adultos = models.PositiveSmallIntegerField(verbose_name='Número de Adultos', default=1)
    numero_menores = models.PositiveSmallIntegerField(verbose_name='Número de Menores', default=0)
    estado_reserva = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    motivo_cancelacion = models.TextField(null=True, blank=True, verbose_name='Motivo de Cancelación')
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto Total', editable=False)
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'paquete', 'fecha_inicio'],
                name='unique_usuario_paquete_fecha_inicio'
            )
        ]

    def save(self, *args, **kwargs):
        if self.paquete and self.fecha_inicio:
            try:
                # Búsqueda directa sin imports
                temporada = Temporada.objects.filter(
                    fecha_inicio__lte=self.fecha_inicio, 
                    fecha_fin__gte=self.fecha_inicio
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

                        if descuento > 0:
                            self.monto_total = base_monto * (100 - descuento) / 100
                        else:
                            self.monto_total = base_monto
                    else:
                        self.monto_total = 0.00
                else:
                    self.monto_total = 0.00

            except Exception:
                self.monto_total = 0.00

        elif not getattr(self, 'monto_total', None):
            self.monto_total = 0.00

        super().save(*args, **kwargs)
        



class Notificacion(models.Model):
    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='notificaciones', verbose_name='Reserva')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    mensaje = models.TextField(verbose_name='Mensaje de la Notificación')
    leido = models.BooleanField(default=False, verbose_name='¿Leído?')
    tipo = models.CharField(max_length=50, verbose_name='Tipo de Notificación')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'Notificación {self.id} - {self.usuario}'


class Calificacion(models.Model):
    """
    Calificación y reseña de una experiencia o reserva de un paquete turístico
    realizada por un cliente o usuario registrado.
    """
    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey('Reserva', on_delete=models.SET_NULL, related_name='calificaciones', verbose_name='Reserva Calificada', null=True, blank=True)
    tipo = models.CharField(max_length=20, default='experiencia', verbose_name='Tipo', help_text='Tipo de reseña: experiencia, pregunta, etc.')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    puntaje_estrellas = PositiveTinyIntegerField(default=5, validators=[MinValueValidator(1, message="La calificación mínima es 1 estrella."), MaxValueValidator(5, message="La calificación máxima es 5 estrellas.")], verbose_name='Puntaje / Estrellas')
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



# ==============================================================================
# GUIAS
# ==============================================================================


class PlanGuia(models.Model):
    """
    Modelo que representa la entidad 'plan_guia' del MER.
    Permite asignar un guía turístico a un paquete específico con fechas e idioma de servicio.
    """
    id = models.AutoField(primary_key=True)
    idioma_servicio = models.CharField(max_length=50, verbose_name='Idioma del Servicio')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_inicio_plan = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin_plan = models.DateField(verbose_name='Fecha de Fin')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activo?')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planes_guia', verbose_name='Usuario / Guía')
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='planes_guia', verbose_name='Paquete')

    class Meta:
        db_table = 'plan_guia'
        verbose_name = 'Plan Guía'
        verbose_name_plural = 'Planes Guía'

    def __str__(self):
        nombre_guia = self.usuario.get_full_name()
        return f'Plan Guía #{self.pk} — {nombre_guia} — {self.paquete.nombre}'


# ==============================================================================
# PAGOS
# ==============================================================================

class Pago(models.Model):
    """
    Pago subido por un usuario para verificar el pago de una reserva o multa.
    El administrador puede aprobarlo o rechazarlo.
    """
    id = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [('pendiente', 'Pendiente de revisión'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')]
    reserva = models.OneToOneField('Reserva', on_delete=models.CASCADE, related_name='pago', verbose_name='Reserva')
    referencia = models.CharField(max_length=100, verbose_name='Número de referencia / transacción', help_text='Número de comprobante, transacción o referencia bancaria')
    banco_origen = models.CharField(max_length=100, verbose_name='Banco / medio de pago')
    metodo_pago = models.CharField(max_length=50, verbose_name='Método de Pago')
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

    @property
    def usuario(self):
        """Retorna el usuario de la reserva asociada."""
        return self.reserva.usuario if self.reserva else None

    def __str__(self):
        """Retorna el ID, usuario y estado del pago como representación textual."""
        username = self.usuario.username if self.usuario else "N/A"
        return f'Pago #{self.pk} — {username} — {self.get_estado_transaccion_display()}'

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
            self.reserva.estado_reserva = 'confirmada'
            self.reserva.save()
        elif self.estado_transaccion == 'rechazado' and self.reserva and (self.reserva.estado_reserva == 'pendiente'):
            pass
        super().save(*args, **kwargs)

    def nombre_archivo(self):
        """
        Retorna el nombre del archivo de imagen del comprobante.

        Returns:
             str: El nombre base del archivo, o '—' si no hay imagen.
        """
        return os.path.basename(self.imagen_comprobante.name) if self.imagen_comprobante else '—'



# ==============================================================================
# PROMOCIONES
# ==============================================================================


class Promocion(models.Model):
    """Promoción o descuento aplicado a un paquete turístico durante un período determinado."""
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name='Nombre de la promoción')
    descripcion = models.TextField(verbose_name='Descripción')
    porcentaje_descuento = models.PositiveIntegerField(verbose_name='Porcentaje de descuento')
    fecha_fin = models.DateField(verbose_name='Fecha de fin')
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    codigo_promocion = models.CharField(max_length=20, unique=True, verbose_name='Código de promoción')
    condiciones = models.TextField(blank=True, null=True, verbose_name='Condiciones')
    codigo_cupon = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name='Código de cupón')
    activa = models.BooleanField(default=True, verbose_name='¿Activa?')

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'

    def __str__(self):
        """Retorna el nombre y porcentaje de descuento de la promoción."""
        return f'{self.nombre} ({self.porcentaje_descuento}%)'





class PolizaViaje(models.Model):
    """
    Catálogo de seguros ofrecidos.
    """
    id = models.AutoField(primary_key=True)
    nombre_poliza = models.CharField(max_length=150, verbose_name='Nombre de la Póliza')
    descripcion = models.TextField(verbose_name='Descripción de Coberturas')
    cobertura_medica_max = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, verbose_name='Monto máximo de cobertura médica')
    cubre_perdida_equipaje = models.BooleanField(default=False, verbose_name='¿Cubre pérdida de equipaje?')
    cubre_cancelacion_vuelo = models.BooleanField(default=False, verbose_name='¿Cubre cancelación de vuelo?')
    precio_diario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio por Día')
    condiciones_generales = models.TextField(blank=True, null=True, verbose_name='Condiciones Generales')
    estado = models.BooleanField(default=True, verbose_name='¿Póliza Activa?')

    class Meta:
        verbose_name = 'Póliza de Viaje'
        verbose_name_plural = 'Pólizas de Viaje'

    def __str__(self):
        return f'{self.nombre_poliza} (${self.precio_diario}/día)'

class Aseguradora(models.Model):
    """
    Representa la adquisición de un seguro para una reserva. (Anteriormente SeguroViaje)
    """
    id = models.AutoField(primary_key=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='aseguradora', verbose_name='Reserva Asociada', null=True, blank=True)
    poliza_viaje = models.ForeignKey(PolizaViaje, on_delete=models.PROTECT, related_name='aseguradoras', verbose_name='Póliza de Viaje Asociada')
    nombre_empresa = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre de la Empresa Aseguradora')
    numero_poliza = models.CharField(max_length=100, unique=True, verbose_name='Número de Póliza Emitida')
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Emisión')
    fecha_inicio_cobertura = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio de Cobertura')
    fecha_fin_cobertura = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin de Cobertura')
    costo_seguro = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name='Costo de Seguro')
    telefono_emergencia = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono de Emergencia')
    estado_emision = models.CharField(max_length=20, default='Pendiente', verbose_name='Estado de Emisión')

    class Meta:
        verbose_name = 'Seguro Emitido (Aseguradora)'
        verbose_name_plural = 'Seguros Emitidos (Aseguradoras)'

    def save(self, *args, **kwargs):
        if self.reserva and self.poliza_viaje:
            dias = self.reserva.paquete.dias_duracion
            self.costo_seguro = self.poliza_viaje.precio_diario * dias
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Seguro {self.numero_poliza} para Reserva {(self.reserva.id if self.reserva else 'N/A')}"


# ==============================================================================
# USUARIOS
# ==============================================================================
"""
Modelos de datos para la gestión de usuarios: Usuario personalizado.
(Los perfiles de Cliente y Guía Turístico fueron consolidados directamente en el modelo de Usuario).
"""

