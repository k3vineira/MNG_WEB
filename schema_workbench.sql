-- ============================================================================
-- SCRIPT SQL GENERADO PARA MYSQL WORKBENCH
-- Proyecto: MNG_WEB
-- Base de Datos: monagua_turismo_db
-- Total Tablas de la Aplicación: 21
-- (Excluidas todas las tablas internas/predeterminadas de Django)
-- ============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE DATABASE IF NOT EXISTS `monagua_turismo_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `monagua_turismo_db`;

-- -----------------------------------------------------
-- Tabla `App_actividades` (Actividades)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_actividades`;
CREATE TABLE IF NOT EXISTS `App_actividades` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre de la Actividad',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `nivel_dificultad` VARCHAR(10) NOT NULL COMMENT 'Nivel de Dificultad',
    `equipo_requerimiento` LONGTEXT NOT NULL COMMENT 'Equipo Requerido',
    `recomendaciones` LONGTEXT NOT NULL COMMENT 'Recomendaciones',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    `apto_menores` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Apto para menores?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Actividad turística que puede ser incluida en uno o varios paquetes.';

-- -----------------------------------------------------
-- Tabla `App_auditoria` (Auditoria)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_auditoria`;
CREATE TABLE IF NOT EXISTS `App_auditoria` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `acciones_realizada` VARCHAR(255) NOT NULL COMMENT 'acciones realizada',
    `tabla_afectada` VARCHAR(100) NOT NULL COMMENT 'tabla afectada',
    `fecha` DATE NOT NULL COMMENT 'fecha',
    `hora` TIME NOT NULL COMMENT 'hora',
    `observacion` LONGTEXT NULL COMMENT 'observacion',
    `valor_anterior` LONGTEXT NULL COMMENT 'valor anterior',
    `nuevo_valor` LONGTEXT NULL COMMENT 'nuevo valor',
    `codigo_usuario_id` BIGINT NOT NULL COMMENT 'codigo usuario',
    PRIMARY KEY (`id`),
    KEY `idx_App_auditoria_codigo_usuario_id` (`codigo_usuario_id`),
    CONSTRAINT `fk_App_auditoria_codigo_usuario_id` FOREIGN KEY (`codigo_usuario_id`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro de auditoría del sistema sobre acciones realizadas por los usuarios.';

-- -----------------------------------------------------
-- Tabla `App_blog` (Blog)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_blog`;
CREATE TABLE IF NOT EXISTS `App_blog` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `usuario_id` BIGINT NOT NULL COMMENT 'Autor / Administrador',
    `titulo` VARCHAR(200) NOT NULL COMMENT 'titulo',
    `contenido` LONGTEXT NOT NULL COMMENT 'contenido',
    `informacion_adicional` LONGTEXT NOT NULL COMMENT 'informacion adicional',
    `imagen_destacada` VARCHAR(100) NULL COMMENT 'imagen destacada',
    `fecha_publicacion` DATETIME NOT NULL COMMENT 'fecha publicacion',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Publicado?',
    PRIMARY KEY (`id`),
    KEY `idx_App_blog_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_App_blog_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Entrada de blog publicada por un administrador o autor en Mongua Turismo.';

-- -----------------------------------------------------
-- Tabla `App_cancelacion` (Cancelacion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_cancelacion`;
CREATE TABLE IF NOT EXISTS `App_cancelacion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NOT NULL COMMENT 'reserva',
    `motivo` LONGTEXT NOT NULL COMMENT 'motivo',
    `penalidad` INT NOT NULL DEFAULT 0 COMMENT 'Penalidad Aplicada',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'pendiente' COMMENT 'Estado',
    `fecha` DATETIME NOT NULL COMMENT 'Fecha de Solicitud',
    `fecha_reembolso` DATE NULL COMMENT 'Fecha de Reembolso',
    `valor_reembolsado` INT NULL DEFAULT 0 COMMENT 'Valor Reembolsado',
    `imagen_comprobante` VARCHAR(100) NULL COMMENT 'Imagen del Comprobante',
    PRIMARY KEY (`id`),
    KEY `idx_App_cancelacion_reserva_id` (`reserva_id`),
    CONSTRAINT `fk_App_cancelacion_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `App_reserva` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Solicitud de cancelación de una reserva realizada por un usuario. Calcula automáticamente la penalidad según los días de antelación.';

-- -----------------------------------------------------
-- Tabla `App_categoria` (Categoria)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_categoria`;
CREATE TABLE IF NOT EXISTS `App_categoria` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre de la Categoría',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Categoría que agrupa paquetes turísticos similares (ej. Aventura, Cultura).';

-- -----------------------------------------------------
-- Tabla `App_paquete` (Paquete)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_paquete`;
CREATE TABLE IF NOT EXISTS `App_paquete` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `imagen` VARCHAR(100) NOT NULL COMMENT 'Imagen del Destino',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre del Paquete',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `dias_duracion` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Días de Duración',
    `noches_duracion` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Noches de Duración',
    `punto_encuentro` VARCHAR(200) NOT NULL COMMENT 'punto encuentro',
    `hora_encuentro` TIME NOT NULL COMMENT 'hora encuentro',
    `categoria_id` INT NOT NULL COMMENT 'categoria',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activo?',
    PRIMARY KEY (`id`),
    KEY `idx_App_paquete_categoria_id` (`categoria_id`),
    CONSTRAINT `fk_App_paquete_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `App_categoria` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Paquete turístico ofrecido por Monagua, conformado por actividades y con tarifas por temporada.';

-- -----------------------------------------------------
-- Tabla `App_poliza` (Poliza)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_poliza`;
CREATE TABLE IF NOT EXISTS `App_poliza` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre_aseguradora` VARCHAR(100) NOT NULL COMMENT 'Nombre de la Aseguradora / Plan',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción de Coberturas',
    `precio_diario` DECIMAL(10, 2) NOT NULL COMMENT 'Precio por Día',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Póliza Activa?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Define los tipos de planes de seguros disponibles (ej: Plan Básico, Plan Premium). Equivale a la entidad ''poliza'' del MER de draw.io.';

-- -----------------------------------------------------
-- Tabla `App_pqrs` (PQRS)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_pqrs`;
CREATE TABLE IF NOT EXISTS `App_pqrs` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `usuario_id` BIGINT NULL COMMENT 'usuario',
    `tipo` VARCHAR(15) NOT NULL COMMENT 'tipo',
    `asunto` VARCHAR(200) NOT NULL COMMENT 'asunto',
    `descripcion` LONGTEXT NOT NULL COMMENT 'descripcion',
    `estado` VARCHAR(15) NOT NULL DEFAULT 'abierto' COMMENT 'estado',
    `fecha` DATETIME NOT NULL COMMENT 'fecha',
    PRIMARY KEY (`id`),
    KEY `idx_App_pqrs_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_App_pqrs_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Solicitud de Petición, Queja, Reclamo o Sugerencia enviada por un usuario.';

-- -----------------------------------------------------
-- Tabla `App_promocion` (Promocion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_promocion`;
CREATE TABLE IF NOT EXISTS `App_promocion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(150) NOT NULL COMMENT 'Nombre de la promoción',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `descuento` INT UNSIGNED NOT NULL COMMENT 'Porcentaje de descuento',
    `fecha_fin` DATE NOT NULL COMMENT 'Fecha de fin',
    `fecha_inicio` DATE NOT NULL COMMENT 'Fecha de inicio',
    `codigo_promocion` VARCHAR(20) NOT NULL COMMENT 'Código de promoción',
    `condiciones` LONGTEXT NULL COMMENT 'Condiciones',
    `codigo_cupon` VARCHAR(30) NULL COMMENT 'Código de cupón',
    `activa` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Activa?',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_App_promocion_codigo_promocion` (`codigo_promocion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Promoción o descuento aplicado a un paquete turístico durante un período determinado.';

-- -----------------------------------------------------
-- Tabla `App_reserva` (Reserva)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_reserva`;
CREATE TABLE IF NOT EXISTS `App_reserva` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'Paquete Reservado',
    `usuario_id` BIGINT NULL COMMENT 'Usuario',
    `fecha` DATE NOT NULL COMMENT 'Fecha de Reserva',
    `fecha_inicio` DATE NULL COMMENT 'Fecha de inicio',
    `numero_adultos` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Número de Adultos',
    `numero_menores` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Número de Menores',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'pendiente' COMMENT 'Estado',
    `motivo_cancelacion` LONGTEXT NULL COMMENT 'Motivo de Cancelación',
    `monto_total` INT NOT NULL COMMENT 'Monto Total',
    `fecha_registro` DATETIME NOT NULL COMMENT 'Fecha de Registro',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_usuario_paquete_fecha` (`usuario_id`, `paquete_id`, `fecha`),
    KEY `idx_App_reserva_paquete_id` (`paquete_id`),
    KEY `idx_App_reserva_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_App_reserva_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `App_paquete` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_App_reserva_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Reserva(id, paquete, usuario, fecha, fecha_inicio, numero_adultos, numero_menores, estado, motivo_cancelacion, monto_total, fecha_registro)';

-- -----------------------------------------------------
-- Tabla `App_seguroviaje` (SeguroViaje)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_seguroviaje`;
CREATE TABLE IF NOT EXISTS `App_seguroviaje` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NULL COMMENT 'Reserva Asociada',
    `poliza_id` INT NOT NULL COMMENT 'Póliza Asociada',
    `numero_poliza` VARCHAR(50) NOT NULL COMMENT 'Número de Póliza',
    `fecha_emision` DATETIME NOT NULL COMMENT 'Fecha de Emisión',
    `costo_seguro` DECIMAL(12, 2) NOT NULL COMMENT 'Costo de Seguro',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_App_seguroviaje_reserva_id` (`reserva_id`),
    UNIQUE KEY `uk_App_seguroviaje_numero_poliza` (`numero_poliza`),
    KEY `idx_App_seguroviaje_reserva_id` (`reserva_id`),
    KEY `idx_App_seguroviaje_poliza_id` (`poliza_id`),
    CONSTRAINT `fk_App_seguroviaje_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `App_reserva` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_App_seguroviaje_poliza_id` FOREIGN KEY (`poliza_id`) REFERENCES `App_poliza` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Representa la adquisición de un seguro por parte de un usuario para una reserva específica. Equivale a la entidad ''seguro_viaje'' del MER de draw.io.';

-- -----------------------------------------------------
-- Tabla `App_tarifa` (Tarifa)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_tarifa`;
CREATE TABLE IF NOT EXISTS `App_tarifa` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'paquete',
    `temporada_id` INT NOT NULL COMMENT 'temporada',
    `precio_adulto` INT NOT NULL COMMENT 'Precio por Adulto',
    `precio_menor` INT NOT NULL COMMENT 'Precio por Menor',
    `estado` VARCHAR(10) NOT NULL DEFAULT 'activa' COMMENT 'estado',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_App_tarifa_ut_1` (`paquete_id`, `temporada_id`),
    KEY `idx_App_tarifa_paquete_id` (`paquete_id`),
    KEY `idx_App_tarifa_temporada_id` (`temporada_id`),
    CONSTRAINT `fk_App_tarifa_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `App_paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_App_tarifa_temporada_id` FOREIGN KEY (`temporada_id`) REFERENCES `App_temporada` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tarifa de precio para un paquete en una temporada específica.';

-- -----------------------------------------------------
-- Tabla `App_temporada` (Temporada)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_temporada`;
CREATE TABLE IF NOT EXISTS `App_temporada` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(50) NOT NULL COMMENT 'Nombre de la Temporada',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción de la Temporada',
    `fecha_inicio` DATE NOT NULL COMMENT 'Fecha de Inicio',
    `fecha_fin` DATE NOT NULL COMMENT 'Fecha de Fin',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'programada' COMMENT 'Estado',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Representa una temporada turística con fechas de inicio y fin.';

-- -----------------------------------------------------
-- Tabla `App_usuario` (Usuario)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `App_usuario`;
CREATE TABLE IF NOT EXISTS `App_usuario` (
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT 'ID',
    `password` VARCHAR(128) NOT NULL COMMENT 'password',
    `last_login` DATETIME NULL COMMENT 'last login',
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'superuser status - Designates that this user has all permissions without explicitly assigning them.',
    `username` VARCHAR(150) NOT NULL COMMENT 'username - Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
    `first_name` VARCHAR(150) NOT NULL COMMENT 'first name',
    `last_name` VARCHAR(150) NOT NULL COMMENT 'last name',
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'staff status - Designates whether the user can log into this admin site.',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'active - Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
    `date_joined` DATETIME NOT NULL COMMENT 'date joined',
    `email` VARCHAR(254) NOT NULL COMMENT 'Correo Electrónico',
    `rol` VARCHAR(20) NOT NULL DEFAULT 'CLIENTE' COMMENT 'Rol',
    `tipo_documento` VARCHAR(20) NOT NULL COMMENT 'Tipo de Documento',
    `numero_documento` VARCHAR(20) NOT NULL COMMENT 'Número de Documento',
    `telefono` VARCHAR(15) NOT NULL COMMENT 'Teléfono',
    `residencia` VARCHAR(100) NOT NULL COMMENT 'Residencia de Origen',
    `imagen_perfil` VARCHAR(100) NULL COMMENT 'Imagen de Perfil',
    `pais` VARCHAR(100) NOT NULL COMMENT 'País',
    `departamento` VARCHAR(100) NOT NULL COMMENT 'Departamento',
    `ciudad` VARCHAR(100) NOT NULL COMMENT 'Ciudad',
    `numero_tarjeta_profesional` VARCHAR(50) NOT NULL COMMENT 'Licencia de Turismo',
    `experiencia_anos` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Años de Experiencia',
    `experiencia_fecha` DATE NULL COMMENT 'Fecha de Inicio de Experiencia',
    `descripcion_experiencia` LONGTEXT NOT NULL COMMENT 'Descripción de la Experiencia',
    `entidad_salud` VARCHAR(100) NULL COMMENT 'Entidad de Salud',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_App_usuario_username` (`username`),
    UNIQUE KEY `uk_App_usuario_email` (`email`),
    UNIQUE KEY `uk_App_usuario_numero_documento` (`numero_documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo de usuario personalizado que extiende AbstractUser con campos adicionales como rol, tipo de documento, teléfono e imagen de perfil.';

-- -----------------------------------------------------
-- Tabla `comunidad_calificacion` (Calificacion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `comunidad_calificacion`;
CREATE TABLE IF NOT EXISTS `comunidad_calificacion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NULL COMMENT 'Reserva Calificada',
    `tipo` VARCHAR(20) NOT NULL DEFAULT 'experiencia' COMMENT 'Tipo - Tipo de reseña: experiencia, pregunta, etc.',
    `titulo` VARCHAR(255) NOT NULL COMMENT 'Título',
    `puntaje_estrellas` SMALLINT UNSIGNED NOT NULL DEFAULT 5 COMMENT 'Puntaje / Estrellas',
    `comentario` LONGTEXT NOT NULL COMMENT 'Comentario / Reseña',
    `visible` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Visible?',
    `admin_respuesta` LONGTEXT NULL COMMENT 'Respuesta del Admin',
    `fecha_calificacion` DATETIME NOT NULL COMMENT 'Fecha de Calificación',
    PRIMARY KEY (`id`),
    KEY `idx_comunidad_calificacion_reserva_id` (`reserva_id`),
    CONSTRAINT `fk_comunidad_calificacion_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `App_reserva` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Calificación y reseña de una experiencia o reserva de un paquete turístico realizada por un cliente o usuario registrado.';

-- -----------------------------------------------------
-- Tabla `factura` (Factura)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `factura`;
CREATE TABLE IF NOT EXISTS `factura` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `fecha_emision` DATETIME NOT NULL COMMENT 'Fecha de Emisión',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'emitida' COMMENT 'Estado',
    `valor_subtotal` DECIMAL(12, 2) NOT NULL COMMENT 'Valor Subtotal',
    `valor_total` DECIMAL(12, 2) NOT NULL COMMENT 'Valor Total',
    `codigo_reserva` INT NOT NULL COMMENT 'Reserva',
    `codigo_pago` INT NULL COMMENT 'Pago',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_factura_codigo_reserva` (`codigo_reserva`),
    KEY `idx_factura_codigo_reserva` (`codigo_reserva`),
    KEY `idx_factura_codigo_pago` (`codigo_pago`),
    CONSTRAINT `fk_factura_codigo_reserva` FOREIGN KEY (`codigo_reserva`) REFERENCES `App_reserva` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_factura_codigo_pago` FOREIGN KEY (`codigo_pago`) REFERENCES `pago` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo que representa la entidad ''factura'' del MER. Registra los datos de facturación formal vinculados a una reserva y a su respectivo pago.';

-- -----------------------------------------------------
-- Tabla `pago` (Pago)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `pago`;
CREATE TABLE IF NOT EXISTS `pago` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NULL COMMENT 'Reserva',
    `referencia` VARCHAR(100) NOT NULL COMMENT 'Número de referencia / transacción - Número de comprobante, transacción o referencia bancaria',
    `banco_origen` VARCHAR(100) NOT NULL COMMENT 'Banco / medio de pago',
    `monto` DECIMAL(12, 2) NOT NULL DEFAULT 0.0 COMMENT 'Monto pagado',
    `imagen_comprobante` VARCHAR(100) NOT NULL COMMENT 'Imagen del comprobante',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción / nota adicional',
    `estado_transaccion` VARCHAR(20) NOT NULL DEFAULT 'pendiente' COMMENT 'Estado',
    `nota_admin` LONGTEXT NOT NULL COMMENT 'Nota del administrador',
    `fecha_pago` DATETIME NOT NULL COMMENT 'Fecha exacta del pago bancario',
    `fecha_envio` DATETIME NOT NULL COMMENT 'Fecha de envío',
    `fecha_revision` DATETIME NULL COMMENT 'Fecha de revisión',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pago_reserva_id` (`reserva_id`),
    KEY `idx_pago_reserva_id` (`reserva_id`),
    CONSTRAINT `fk_pago_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `App_reserva` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Pago subido por un usuario para verificar el pago de una reserva o multa. El administrador puede aprobarlo o rechazarlo.';

-- -----------------------------------------------------
-- Tabla `paquete_actividades` (PaqueteActividad)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `paquete_actividades`;
CREATE TABLE IF NOT EXISTS `paquete_actividades` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'paquete',
    `actividad_id` INT NOT NULL COMMENT 'actividad',
    `dificultad_nivel` VARCHAR(10) NOT NULL DEFAULT 'Media' COMMENT 'Nivel de Dificultad',
    PRIMARY KEY (`id`),
    KEY `idx_paquete_actividades_paquete_id` (`paquete_id`),
    KEY `idx_paquete_actividades_actividad_id` (`actividad_id`),
    CONSTRAINT `fk_paquete_actividades_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `App_paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_paquete_actividades_actividad_id` FOREIGN KEY (`actividad_id`) REFERENCES `App_actividades` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Relación intermedia entre Paquete y Actividades (tabla many-to-many explícita).';

-- -----------------------------------------------------
-- Tabla `paquete_promociones` (PaquetePromocion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `paquete_promociones`;
CREATE TABLE IF NOT EXISTS `paquete_promociones` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'Paquete',
    `promocion_id` INT NOT NULL COMMENT 'Promoción',
    PRIMARY KEY (`id`),
    KEY `idx_paquete_promociones_paquete_id` (`paquete_id`),
    KEY `idx_paquete_promociones_promocion_id` (`promocion_id`),
    CONSTRAINT `fk_paquete_promociones_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `App_paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_paquete_promociones_promocion_id` FOREIGN KEY (`promocion_id`) REFERENCES `App_promocion` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Entidad intermedia que asocia un Paquete, una Promocion y una Tarifa. Equivale a la tabla intermedia ''paquete_promociones'' del MER.';

-- -----------------------------------------------------
-- Tabla `plan_guia` (PlanGuia)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `plan_guia`;
CREATE TABLE IF NOT EXISTS `plan_guia` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `idioma_servicio` VARCHAR(50) NOT NULL COMMENT 'Idioma del Servicio',
    `fecha_creacion` DATETIME NOT NULL COMMENT 'Fecha de Creación',
    `fecha_inicio_plan` DATE NOT NULL COMMENT 'Fecha de Inicio',
    `fecha_fin_plan` DATE NOT NULL COMMENT 'Fecha de Fin',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'activo' COMMENT 'Estado',
    `codigo_guia_turistico` BIGINT NOT NULL COMMENT 'Guía Turístico',
    `codigo_paquete` INT NOT NULL COMMENT 'Paquete',
    PRIMARY KEY (`id`),
    KEY `idx_plan_guia_codigo_guia_turistico` (`codigo_guia_turistico`),
    KEY `idx_plan_guia_codigo_paquete` (`codigo_paquete`),
    CONSTRAINT `fk_plan_guia_codigo_guia_turistico` FOREIGN KEY (`codigo_guia_turistico`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_plan_guia_codigo_paquete` FOREIGN KEY (`codigo_paquete`) REFERENCES `App_paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo que representa la entidad ''plan_guia'' del MER. Permite asignar un guía turístico a un paquete específico con fechas e idioma de servicio.';

-- -----------------------------------------------------
-- Tabla `seguimiento` (Seguimiento)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `seguimiento`;
CREATE TABLE IF NOT EXISTS `seguimiento` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `pqrs_id` INT NOT NULL COMMENT 'pqrs',
    `usuario_id` BIGINT NULL COMMENT 'Usuario / Administrador',
    `respuesta` LONGTEXT NOT NULL COMMENT 'Mensaje / Respuesta',
    `fecha_respuesta` DATETIME NOT NULL COMMENT 'Fecha de Respuesta',
    PRIMARY KEY (`id`),
    KEY `idx_seguimiento_pqrs_id` (`pqrs_id`),
    KEY `idx_seguimiento_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_seguimiento_pqrs_id` FOREIGN KEY (`pqrs_id`) REFERENCES `App_pqrs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_seguimiento_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `App_usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro de seguimiento y respuestas a una solicitud PQRS por parte de un usuario o administrador.';

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================