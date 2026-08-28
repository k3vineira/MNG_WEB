-- ============================================================================
-- SCRIPT SQL GENERADO PARA MYSQL WORKBENCH
-- Proyecto: MNG_WEB
-- Base de Datos: monagua_turismo_db
-- Total Tablas de la Aplicación: 19
-- (Excluidas todas las tablas internas/predeterminadas de Django)
-- ============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE DATABASE IF NOT EXISTS `monagua_turismo_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `monagua_turismo_db`;

-- -----------------------------------------------------
-- Tabla `actividades` (Actividades)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `actividades`;
CREATE TABLE IF NOT EXISTS `actividades` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre de la Actividad',
    `descripcion` LONGTEXT NULL COMMENT 'Descripción',
    `equipo_requerimiento` LONGTEXT NULL COMMENT 'Equipo Requerido',
    `recomendaciones` LONGTEXT NULL COMMENT 'Recomendaciones',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    `apto_menores` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Apto para menores?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Actividad turística que puede ser incluida en uno o varios paquetes.';

-- -----------------------------------------------------
-- Tabla `aseguradora` (Aseguradora)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `aseguradora`;
CREATE TABLE IF NOT EXISTS `aseguradora` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NULL COMMENT 'Reserva Asociada',
    `poliza_viaje_id` INT NOT NULL COMMENT 'Póliza de Viaje Asociada',
    `nombre_empresa` VARCHAR(100) NULL COMMENT 'Nombre de la Empresa Aseguradora',
    `numero_poliza` VARCHAR(100) NOT NULL COMMENT 'Número de Póliza Emitida',
    `fecha_emision` DATETIME NOT NULL COMMENT 'Fecha de Emisión',
    `fecha_inicio_cobertura` DATE NULL COMMENT 'Fecha de Inicio de Cobertura',
    `fecha_fin_cobertura` DATE NULL COMMENT 'Fecha de Fin de Cobertura',
    `costo_seguro` DECIMAL(12, 2) NOT NULL COMMENT 'Costo de Seguro',
    `telefono_emergencia` VARCHAR(20) NULL COMMENT 'Teléfono de Emergencia',
    `estado_emision` VARCHAR(20) NOT NULL DEFAULT 'Pendiente' COMMENT 'Estado de Emisión',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_aseguradora_reserva_id` (`reserva_id`),
    UNIQUE KEY `uk_aseguradora_numero_poliza` (`numero_poliza`),
    KEY `idx_aseguradora_reserva_id` (`reserva_id`),
    KEY `idx_aseguradora_poliza_viaje_id` (`poliza_viaje_id`),
    CONSTRAINT `fk_aseguradora_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `reserva` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_aseguradora_poliza_viaje_id` FOREIGN KEY (`poliza_viaje_id`) REFERENCES `polizaviaje` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Representa la adquisición de un seguro para una reserva. (Anteriormente SeguroViaje)';

-- -----------------------------------------------------
-- Tabla `auditoria` (Auditoria)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `auditoria`;
CREATE TABLE IF NOT EXISTS `auditoria` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `acciones_realizada` VARCHAR(255) NOT NULL COMMENT 'acciones realizada',
    `tabla_afectada` VARCHAR(100) NOT NULL COMMENT 'tabla afectada',
    `fecha_accion` DATETIME NOT NULL COMMENT 'Fecha y Hora de Acción',
    `observacion` LONGTEXT NULL COMMENT 'observacion',
    `valor_anterior` LONGTEXT NULL COMMENT 'valor anterior',
    `nuevo_valor` LONGTEXT NULL COMMENT 'nuevo valor',
    `registro_afectado_id` INT NULL COMMENT 'ID del Registro Afectado - ID del registro que fue modificado, creado o eliminado',
    `codigo_usuario_id` BIGINT NOT NULL COMMENT 'codigo usuario',
    PRIMARY KEY (`id`),
    KEY `idx_auditoria_codigo_usuario_id` (`codigo_usuario_id`),
    CONSTRAINT `fk_auditoria_codigo_usuario_id` FOREIGN KEY (`codigo_usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro de auditoría del sistema sobre acciones realizadas por los usuarios.';

-- -----------------------------------------------------
-- Tabla `blog` (Blog)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `blog`;
CREATE TABLE IF NOT EXISTS `blog` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `usuario_id` BIGINT NOT NULL COMMENT 'Autor / Administrador',
    `titulo` VARCHAR(200) NOT NULL COMMENT 'titulo',
    `contenido` LONGTEXT NOT NULL COMMENT 'contenido',
    `informacion_adicional` LONGTEXT NULL COMMENT 'Información Adicional',
    `imagen_destacada` VARCHAR(100) NULL COMMENT 'imagen destacada',
    `fecha_publicacion` DATETIME NOT NULL COMMENT 'fecha publicacion',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Publicado?',
    PRIMARY KEY (`id`),
    KEY `idx_blog_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_blog_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Entrada de blog publicada por un administrador o autor en Mongua Turismo.';

-- -----------------------------------------------------
-- Tabla `categoria` (Categoria)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `categoria`;
CREATE TABLE IF NOT EXISTS `categoria` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre de la Categoría',
    `descripcion` LONGTEXT NULL COMMENT 'Descripción',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_categoria_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Categoría que agrupa paquetes turísticos similares (ej. Aventura, Cultura).';

-- -----------------------------------------------------
-- Tabla `comunidad_calificacion` (Calificacion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `comunidad_calificacion`;
CREATE TABLE IF NOT EXISTS `comunidad_calificacion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NULL COMMENT 'Reserva Calificada',
    `tipo` VARCHAR(20) NOT NULL DEFAULT 'experiencia' COMMENT 'Tipo - Tipo de reseña: experiencia, pregunta, etc.',
    `titulo` VARCHAR(255) NOT NULL COMMENT 'Título',
    `puntaje_estrellas` TINYINT UNSIGNED NOT NULL DEFAULT 5 COMMENT 'Puntaje / Estrellas',
    `comentario` LONGTEXT NOT NULL COMMENT 'Comentario / Reseña',
    `visible` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Visible?',
    `admin_respuesta` LONGTEXT NULL COMMENT 'Respuesta del Admin',
    `fecha_calificacion` DATETIME NOT NULL COMMENT 'Fecha de Calificación',
    PRIMARY KEY (`id`),
    KEY `idx_comunidad_calificacion_reserva_id` (`reserva_id`),
    CONSTRAINT `fk_comunidad_calificacion_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `reserva` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Calificación y reseña de una experiencia o reserva de un paquete turístico realizada por un cliente o usuario registrado.';

-- -----------------------------------------------------
-- Tabla `pago` (Pago)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `pago`;
CREATE TABLE IF NOT EXISTS `pago` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `reserva_id` INT NOT NULL COMMENT 'Reserva',
    `referencia` VARCHAR(100) NOT NULL COMMENT 'Número de referencia / transacción - Número de comprobante, transacción o referencia bancaria',
    `banco_origen` VARCHAR(100) NOT NULL COMMENT 'Banco / medio de pago',
    `metodo_pago` VARCHAR(50) NOT NULL COMMENT 'Método de Pago',
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
    CONSTRAINT `fk_pago_reserva_id` FOREIGN KEY (`reserva_id`) REFERENCES `reserva` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Pago subido por un usuario para verificar el pago de una reserva o multa. El administrador puede aprobarlo o rechazarlo.';

-- -----------------------------------------------------
-- Tabla `paquete` (Paquete)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `paquete`;
CREATE TABLE IF NOT EXISTS `paquete` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `imagen` VARCHAR(100) NOT NULL COMMENT 'Imagen del Destino',
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre del Paquete',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `dias_duracion` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Días de Duración',
    `noches_duracion` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Noches de Duración',
    `punto_encuentro` VARCHAR(150) NOT NULL COMMENT 'Punto de Encuentro',
    `hora_encuentro` TIME NOT NULL COMMENT 'hora encuentro',
    `categoria_id` INT NOT NULL COMMENT 'categoria',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activo?',
    PRIMARY KEY (`id`),
    KEY `idx_paquete_categoria_id` (`categoria_id`),
    CONSTRAINT `fk_paquete_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `categoria` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Paquete turístico ofrecido por Monagua, conformado por actividades y con tarifas por temporada.';

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
    UNIQUE KEY `uk_paquete_actividades_ut_1` (`paquete_id`, `actividad_id`),
    KEY `idx_paquete_actividades_paquete_id` (`paquete_id`),
    KEY `idx_paquete_actividades_actividad_id` (`actividad_id`),
    CONSTRAINT `fk_paquete_actividades_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_paquete_actividades_actividad_id` FOREIGN KEY (`actividad_id`) REFERENCES `actividades` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Relación intermedia entre Paquete y Actividades (tabla many-to-many explícita).';

-- -----------------------------------------------------
-- Tabla `paquete_promocion` (PaquetePromocion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `paquete_promocion`;
CREATE TABLE IF NOT EXISTS `paquete_promocion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'paquete',
    `promocion_id` INT NOT NULL COMMENT 'promocion',
    `valor_adulto_condescuento` DECIMAL(12, 2) NOT NULL DEFAULT 0.0 COMMENT 'Valor Adulto con Descuento',
    `valor_menor_condescuento` DECIMAL(12, 2) NOT NULL DEFAULT 0.0 COMMENT 'Valor Menor con Descuento',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_paquete_promocion_ut_1` (`paquete_id`, `promocion_id`),
    KEY `idx_paquete_promocion_paquete_id` (`paquete_id`),
    KEY `idx_paquete_promocion_promocion_id` (`promocion_id`),
    CONSTRAINT `fk_paquete_promocion_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_paquete_promocion_promocion_id` FOREIGN KEY (`promocion_id`) REFERENCES `promocion` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Relación intermedia entre Paquete y Promocion (tabla many-to-many explícita).';

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
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activo?',
    `usuario_id` BIGINT NOT NULL COMMENT 'Usuario / Guía',
    `paquete_id` INT NOT NULL COMMENT 'Paquete',
    PRIMARY KEY (`id`),
    KEY `idx_plan_guia_usuario_id` (`usuario_id`),
    KEY `idx_plan_guia_paquete_id` (`paquete_id`),
    CONSTRAINT `fk_plan_guia_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_plan_guia_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo que representa la entidad ''plan_guia'' del MER. Permite asignar un guía turístico a un paquete específico con fechas e idioma de servicio.';

-- -----------------------------------------------------
-- Tabla `polizaviaje` (PolizaViaje)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `polizaviaje`;
CREATE TABLE IF NOT EXISTS `polizaviaje` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre_poliza` VARCHAR(150) NOT NULL COMMENT 'Nombre de la Póliza',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción de Coberturas',
    `cobertura_medica_max` DECIMAL(12, 2) NOT NULL DEFAULT 0.0 COMMENT 'Monto máximo de cobertura médica',
    `cubre_perdida_equipaje` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '¿Cubre pérdida de equipaje?',
    `cubre_cancelacion_vuelo` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '¿Cubre cancelación de vuelo?',
    `precio_diario` DECIMAL(10, 2) NOT NULL COMMENT 'Precio por Día',
    `condiciones_generales` LONGTEXT NULL COMMENT 'Condiciones Generales',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Póliza Activa?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Catálogo de seguros ofrecidos.';

-- -----------------------------------------------------
-- Tabla `pqrs` (PQRS)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `pqrs`;
CREATE TABLE IF NOT EXISTS `pqrs` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `usuario_id` BIGINT NOT NULL COMMENT 'usuario',
    `tipo` VARCHAR(15) NOT NULL COMMENT 'tipo',
    `asunto` VARCHAR(150) NOT NULL COMMENT 'asunto',
    `descripcion` LONGTEXT NOT NULL COMMENT 'descripcion',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'abierto' COMMENT 'estado',
    `fecha` DATETIME NOT NULL COMMENT 'fecha',
    PRIMARY KEY (`id`),
    KEY `idx_pqrs_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_pqrs_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Solicitud de Petición, Queja, Reclamo o Sugerencia enviada por un usuario.';

-- -----------------------------------------------------
-- Tabla `promocion` (Promocion)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `promocion`;
CREATE TABLE IF NOT EXISTS `promocion` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(150) NOT NULL COMMENT 'Nombre de la promoción',
    `descripcion` LONGTEXT NOT NULL COMMENT 'Descripción',
    `porcentaje_descuento` INT UNSIGNED NOT NULL COMMENT 'Porcentaje de descuento',
    `fecha_fin` DATE NOT NULL COMMENT 'Fecha de fin',
    `fecha_inicio` DATE NOT NULL COMMENT 'Fecha de inicio',
    `codigo_promocion` VARCHAR(20) NOT NULL COMMENT 'Código de promoción',
    `condiciones` LONGTEXT NULL COMMENT 'Condiciones',
    `codigo_cupon` VARCHAR(30) NULL COMMENT 'Código de cupón',
    `activa` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Activa?',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_promocion_codigo_promocion` (`codigo_promocion`),
    UNIQUE KEY `uk_promocion_codigo_cupon` (`codigo_cupon`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Promoción o descuento aplicado a un paquete turístico durante un período determinado.';

-- -----------------------------------------------------
-- Tabla `reserva` (Reserva)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `reserva`;
CREATE TABLE IF NOT EXISTS `reserva` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'Paquete Reservado',
    `usuario_id` BIGINT NULL COMMENT 'Usuario',
    `fecha_inicio` DATE NULL COMMENT 'Fecha de inicio',
    `numero_adultos` SMALLINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Número de Adultos',
    `numero_menores` SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Número de Menores',
    `estado_reserva` VARCHAR(20) NOT NULL DEFAULT 'pendiente' COMMENT 'Estado',
    `motivo_cancelacion` LONGTEXT NULL COMMENT 'Motivo de Cancelación',
    `monto_total` DECIMAL(12, 2) NOT NULL COMMENT 'Monto Total',
    `fecha_registro` DATETIME NOT NULL COMMENT 'Fecha de Registro',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_usuario_paquete_fecha_inicio` (`usuario_id`, `paquete_id`, `fecha_inicio`),
    KEY `idx_reserva_paquete_id` (`paquete_id`),
    KEY `idx_reserva_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_reserva_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `paquete` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_reserva_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Reserva(id, paquete, usuario, fecha_inicio, numero_adultos, numero_menores, estado_reserva, motivo_cancelacion, monto_total, fecha_registro)';

-- -----------------------------------------------------
-- Tabla `seguimiento` (Seguimiento)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `seguimiento`;
CREATE TABLE IF NOT EXISTS `seguimiento` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `pqrs_id` INT NOT NULL COMMENT 'pqrs',
    `usuario_id` BIGINT NOT NULL COMMENT 'Usuario / Administrador',
    `respuesta` LONGTEXT NOT NULL COMMENT 'Mensaje / Respuesta',
    `fecha_respuesta` DATETIME NOT NULL COMMENT 'Fecha de Respuesta',
    PRIMARY KEY (`id`),
    KEY `idx_seguimiento_pqrs_id` (`pqrs_id`),
    KEY `idx_seguimiento_usuario_id` (`usuario_id`),
    CONSTRAINT `fk_seguimiento_pqrs_id` FOREIGN KEY (`pqrs_id`) REFERENCES `pqrs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_seguimiento_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro de seguimiento y respuestas a una solicitud PQRS por parte de un usuario o administrador.';

-- -----------------------------------------------------
-- Tabla `tarifa` (Tarifa)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tarifa`;
CREATE TABLE IF NOT EXISTS `tarifa` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `paquete_id` INT NOT NULL COMMENT 'paquete',
    `temporada_id` INT NOT NULL COMMENT 'temporada',
    `precio_adulto` DECIMAL(12, 2) NOT NULL COMMENT 'Precio por Adulto',
    `precio_menor` DECIMAL(12, 2) NOT NULL COMMENT 'Precio por Menor',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tarifa_ut_1` (`paquete_id`, `temporada_id`),
    KEY `idx_tarifa_paquete_id` (`paquete_id`),
    KEY `idx_tarifa_temporada_id` (`temporada_id`),
    CONSTRAINT `fk_tarifa_paquete_id` FOREIGN KEY (`paquete_id`) REFERENCES `paquete` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_tarifa_temporada_id` FOREIGN KEY (`temporada_id`) REFERENCES `temporada` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tarifa de precio para un paquete en una temporada específica.';

-- -----------------------------------------------------
-- Tabla `temporada` (Temporada)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `temporada`;
CREATE TABLE IF NOT EXISTS `temporada` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `nombre` VARCHAR(50) NOT NULL COMMENT 'Nombre de la Temporada',
    `descripcion` LONGTEXT NULL COMMENT 'Descripción de la Temporada',
    `fecha_inicio` DATE NOT NULL COMMENT 'Fecha de Inicio',
    `fecha_fin` DATE NOT NULL COMMENT 'Fecha de Fin',
    `estado` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '¿Está Activa?',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Representa una temporada turística con fechas de inicio y fin.';

-- -----------------------------------------------------
-- Tabla `usuario` (Usuario)
-- -----------------------------------------------------
DROP TABLE IF EXISTS `usuario`;
CREATE TABLE IF NOT EXISTS `usuario` (
    `password` VARCHAR(128) NOT NULL COMMENT 'password',
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'superuser status - Designates that this user has all permissions without explicitly assigning them.',
    `first_name` VARCHAR(150) NOT NULL COMMENT 'first name',
    `last_name` VARCHAR(150) NOT NULL COMMENT 'last name',
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'staff status - Designates whether the user can log into this admin site.',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'active - Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
    `date_joined` DATETIME NOT NULL COMMENT 'date joined',
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT 'id',
    `username` VARCHAR(50) NOT NULL COMMENT 'Nombre de Usuario',
    `email` VARCHAR(254) NOT NULL COMMENT 'Correo Electrónico',
    `last_login` DATETIME NULL COMMENT 'Último inicio de sesión',
    `rol` SMALLINT UNSIGNED NOT NULL DEFAULT 2 COMMENT 'Rol',
    `tipo_documento` VARCHAR(20) NOT NULL COMMENT 'Tipo de Documento',
    `numero_documento` VARCHAR(20) NOT NULL COMMENT 'Número de Documento',
    `telefono` VARCHAR(15) NOT NULL COMMENT 'Teléfono',
    `residencia` VARCHAR(100) NOT NULL COMMENT 'Residencia de Origen',
    `imagen_perfil` VARCHAR(100) NULL COMMENT 'Imagen de Perfil',
    `pais` VARCHAR(3) NOT NULL COMMENT 'País',
    `departamento` INT NULL COMMENT 'Departamento',
    `ciudad` INT NULL COMMENT 'Ciudad',
    `numero_tarjeta_profesional` VARCHAR(50) NULL COMMENT 'Licencia de Turismo',
    `experiencia_anos` INT UNSIGNED NULL COMMENT 'Años de Experiencia',
    `experiencia_fecha` DATE NULL COMMENT 'Fecha de Inicio de Experiencia',
    `descripcion_experiencia` LONGTEXT NULL COMMENT 'Descripción de la Experiencia',
    `entidad_salud` VARCHAR(100) NULL COMMENT 'Entidad de Salud',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_usuario_username` (`username`),
    UNIQUE KEY `uk_usuario_email` (`email`),
    UNIQUE KEY `uk_usuario_numero_documento` (`numero_documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo de usuario personalizado que extiende AbstractUser con campos adicionales como rol, tipo de documento, teléfono e imagen de perfil.';

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================