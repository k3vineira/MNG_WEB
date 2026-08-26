-- ============================================================================
-- SCRIPT SQL GENERADO PARA MYSQL WORKBENCH
-- Proyecto: MNG_WEB
-- Base de Datos: monagua_turismo_db
-- Total Tablas de la Aplicación: 11
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
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_App_usuario_username` (`username`),
    UNIQUE KEY `uk_App_usuario_email` (`email`),
    UNIQUE KEY `uk_App_usuario_numero_documento` (`numero_documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelo de usuario personalizado que extiende AbstractUser con campos adicionales como rol, tipo de documento, teléfono e imagen de perfil.';

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