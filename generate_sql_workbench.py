"""
Script: generate_sql_workbench.py
Descripción:
    Analiza todos los modelos (models.py) del proyecto Django y genera un archivo
    SQL estructurado y optimizado para importar y visualizar en MySQL Workbench
    (Modelado EER, ingeniería inversa, llaves primarias, foráneas, índices y comentarios).

Uso:
    python generate_sql_workbench.py
    python generate_sql_workbench.py --app App --output schema_workbench.sql --db-name monagua_turismo_db
"""

import os
import sys
import argparse
from pathlib import Path

# Configurar entorno de Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"Error inicializando Django: {e}")
    sys.exit(1)

from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField


# Mapeo de tipos de campos Django a MySQL
DJANGO_TO_MYSQL_TYPES = {
    'AutoField': 'INT AUTO_INCREMENT',
    'BigAutoField': 'BIGINT AUTO_INCREMENT',
    'SmallAutoField': 'SMALLINT AUTO_INCREMENT',
    'IntegerField': 'INT',
    'PositiveIntegerField': 'INT UNSIGNED',
    'SmallIntegerField': 'SMALLINT',
    'PositiveSmallIntegerField': 'SMALLINT UNSIGNED',
    'BigIntegerField': 'BIGINT',
    'PositiveBigIntegerField': 'BIGINT UNSIGNED',
    'FloatField': 'DOUBLE',
    'DecimalField': lambda f: f"DECIMAL({f.max_digits or 10}, {f.decimal_places or 2})",
    'CharField': lambda f: f"VARCHAR({f.max_length or 255})",
    'TextField': 'LONGTEXT',
    'BooleanField': 'TINYINT(1)',
    'NullBooleanField': 'TINYINT(1)',
    'DateField': 'DATE',
    'DateTimeField': 'DATETIME',
    'TimeField': 'TIME',
    'EmailField': lambda f: f"VARCHAR({f.max_length or 254})",
    'FileField': lambda f: f"VARCHAR({f.max_length or 100})",
    'ImageField': lambda f: f"VARCHAR({f.max_length or 100})",
    'URLField': lambda f: f"VARCHAR({f.max_length or 200})",
    'SlugField': lambda f: f"VARCHAR({f.max_length or 50})",
    'UUIDField': 'CHAR(32)',
    'JSONField': 'JSON',
    'GenericIPAddressField': 'VARCHAR(39)',
    'BinaryField': 'LONGBLOB',
    'DurationField': 'BIGINT',
}

ON_DELETE_MAP = {
    models.CASCADE: 'CASCADE',
    models.SET_NULL: 'SET NULL',
    models.PROTECT: 'RESTRICT',
    models.RESTRICT: 'RESTRICT',
    models.DO_NOTHING: 'NO ACTION',
    models.SET_DEFAULT: 'SET DEFAULT',
}


def get_column_type(field):
    """Obtiene el tipo de dato SQL compatible con MySQL para un campo Django."""
    if isinstance(field, (ForeignKey, OneToOneField)):
        target_model = field.remote_field.model
        if isinstance(target_model, str):
            if '.' not in target_model:
                target_model = f"{field.model._meta.app_label}.{target_model}"
            target_model = apps.get_model(target_model)
        target_pk = target_model._meta.pk
        pk_internal_type = target_pk.get_internal_type()
        if pk_internal_type == 'BigAutoField':
            return 'BIGINT'
        elif pk_internal_type == 'SmallAutoField':
            return 'SMALLINT'
        elif pk_internal_type == 'AutoField':
            return 'INT'
        else:
            return get_column_type(target_pk).replace(' AUTO_INCREMENT', '')

    internal_type = field.get_internal_type()
    if internal_type in DJANGO_TO_MYSQL_TYPES:
        type_def = DJANGO_TO_MYSQL_TYPES[internal_type]
        if callable(type_def):
            return type_def(field)
        return type_def

    return 'VARCHAR(255)'


def sanitize_comment(text):
    """Limpia textos para usarlos de forma segura en comentarios SQL."""
    if not text:
        return ""
    text = str(text).replace("'", "''").replace('\n', ' ').strip()
    return text[:1024]


def clean_table_name(name):
    """Remueve el prefijo predeterminado 'app_' o 'App_' del nombre de la tabla."""
    if name and name.lower().startswith('app_'):
        return name[4:]
    return name


def generate_sql_for_model(model):
    """Genera las sentencias SQL de CREATE TABLE, campos, llaves y restricciones para un modelo."""
    table_name = clean_table_name(model._meta.db_table)
    columns_sql = []
    pk_cols = []
    fks_sql = []
    indexes_sql = []
    uniques_sql = []
    processed_cols = set()

    table_doc = model.__doc__ or model._meta.verbose_name.title()
    table_comment = sanitize_comment(table_doc)

    for field in model._meta.fields:
        col_name = field.column
        if col_name in processed_cols:
            continue
        processed_cols.add(col_name)

        col_type = get_column_type(field)
        null_clause = "NULL" if field.null else "NOT NULL"
        
        default_clause = ""
        if field.has_default() and field.default is not models.NOT_PROVIDED and not callable(field.default):
            default_val = field.default
            if isinstance(default_val, bool):
                default_clause = f" DEFAULT {1 if default_val else 0}"
            elif isinstance(default_val, (int, float)):
                default_clause = f" DEFAULT {default_val}"
            elif isinstance(default_val, str):
                default_clause = f" DEFAULT '{default_val}'"

        comment_parts = []
        if getattr(field, 'verbose_name', None):
            comment_parts.append(str(field.verbose_name))
        if getattr(field, 'help_text', None):
            comment_parts.append(str(field.help_text))
        
        comment_text = " - ".join(comment_parts)
        comment_clause = f" COMMENT '{sanitize_comment(comment_text)}'" if comment_text else ""

        col_def = f"    `{col_name}` {col_type} {null_clause}{default_clause}{comment_clause}"
        columns_sql.append(col_def)

        if field.primary_key:
            pk_cols.append(f"`{col_name}`")
        elif field.unique:
            uniques_sql.append(f"    UNIQUE KEY `uk_{table_name}_{col_name}` (`{col_name}`)")

        if field.db_index and not field.primary_key and not field.unique and not isinstance(field, (ForeignKey, OneToOneField)):
            indexes_sql.append(f"    KEY `idx_{table_name}_{col_name}` (`{col_name}`)")

        if isinstance(field, (ForeignKey, OneToOneField)):
            target_model = field.remote_field.model
            if isinstance(target_model, str):
                if '.' not in target_model:
                    target_model = f"{field.model._meta.app_label}.{target_model}"
                target_model = apps.get_model(target_model)
            
            target_table = clean_table_name(target_model._meta.db_table)
            target_col = field.target_field.column

            on_delete = ON_DELETE_MAP.get(field.remote_field.on_delete, 'CASCADE')
            
            fk_name = f"fk_{table_name}_{col_name}"[:64]
            fk_sql = (
                f"    CONSTRAINT `{fk_name}` FOREIGN KEY (`{col_name}`) "
                f"REFERENCES `{target_table}` (`{target_col}`) "
                f"ON DELETE {on_delete} ON UPDATE CASCADE"
            )
            fks_sql.append(fk_sql)
            indexes_sql.append(f"    KEY `idx_{table_name}_{col_name}` (`{col_name}`)")

    if model._meta.unique_together:
        for idx, ut in enumerate(model._meta.unique_together):
            cols = []
            for col_attr in ut:
                try:
                    f = model._meta.get_field(col_attr)
                    cols.append(f"`{f.column}`")
                except Exception:
                    cols.append(f"`{col_attr}`")
            cols_str = ", ".join(cols)
            uniques_sql.append(f"    UNIQUE KEY `uk_{table_name}_ut_{idx+1}` ({cols_str})")

    for constraint in getattr(model._meta, 'constraints', []):
        if isinstance(constraint, models.UniqueConstraint) and constraint.fields:
            cols = []
            for col_attr in constraint.fields:
                try:
                    f = model._meta.get_field(col_attr)
                    cols.append(f"`{f.column}`")
                except Exception:
                    cols.append(f"`{col_attr}`")
            cols_str = ", ".join(cols)
            c_name = constraint.name or f"uk_{table_name}_{'_'.join(constraint.fields)}"
            uniques_sql.append(f"    UNIQUE KEY `{c_name[:64]}` ({cols_str})")

    table_elements = []
    table_elements.extend(columns_sql)
    
    if pk_cols:
        table_elements.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")

    table_elements.extend(uniques_sql)
    table_elements.extend(indexes_sql)
    table_elements.extend(fks_sql)

    body = ",\n".join(table_elements)
    comment_attr = f" COMMENT='{table_comment}'" if table_comment else ""
    
    sql = (
        f"-- -----------------------------------------------------\n"
        f"-- Tabla `{table_name}` ({model.__name__})\n"
        f"-- -----------------------------------------------------\n"
        f"DROP TABLE IF EXISTS `{table_name}`;\n"
        f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n"
        f"{body}\n"
        f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci{comment_attr};\n"
    )

    return sql


def generate_m2m_tables(model):
    """Genera tablas intermedias para relaciones ManyToMany automáticas (sin through manual)."""
    m2m_sqls = []
    for field in model._meta.many_to_many:
        if field.remote_field.through._meta.auto_created:
            through_model = field.remote_field.through
            m2m_sqls.append(generate_sql_for_model(through_model))
    return m2m_sqls


def build_full_sql(app_label='App', include_django_auth=False, db_name="monagua_turismo_db"):
    """
    Construye el script SQL completo exclusivamente para los modelos de la aplicación
    sin incluir tablas internas o predeterminadas de Django.
    """
    if app_label:
        target_apps = [apps.get_app_config(app_label)]
    else:
        # Solo aplicaciones del usuario (excluyendo todas las de django.contrib)
        target_apps = [
            app for app in apps.get_app_configs()
            if not app.name.startswith('django.')
        ]

    # Obtener modelos de las apps objetivo
    models_list = []
    seen_tables = set()

    for app_config in target_apps:
        for model in app_config.get_models():
            table_name = clean_table_name(model._meta.db_table)
            # Ignorar si es una tabla interna predeterminada de django
            if table_name.startswith(('django_', 'auth_')) and not include_django_auth:
                continue
            if table_name not in seen_tables:
                seen_tables.add(table_name)
                models_list.append(model)

    # Ordenar alfabéticamente por nombre de tabla
    models_list.sort(key=lambda m: clean_table_name(m._meta.db_table))

    lines = [
        "-- ============================================================================",
        f"-- SCRIPT SQL GENERADO PARA MYSQL WORKBENCH",
        f"-- Proyecto: {os.path.basename(BASE_DIR)}",
        f"-- Base de Datos: {db_name}",
        f"-- Total Tablas de la Aplicación: {len(models_list)}",
        "-- (Excluidas todas las tablas internas/predeterminadas de Django)",
        "-- ============================================================================",
        "",
        "SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;",
        "SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;",
        "SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';",
        "",
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        f"USE `{db_name}`;",
        "",
    ]

    exported_tables = set()

    for model in models_list:
        table_name = clean_table_name(model._meta.db_table)
        if table_name not in exported_tables:
            lines.append(generate_sql_for_model(model))
            exported_tables.add(table_name)

    # Tablas intermedias M2M personalizadas (excluyendo grupos y permisos de Django)
    for model in models_list:
        for field in model._meta.many_to_many:
            if field.name in ('groups', 'user_permissions'):
                continue
            if field.remote_field.through and field.remote_field.through._meta.auto_created:
                through_model = field.remote_field.through
                through_table = clean_table_name(through_model._meta.db_table)
                if through_table not in exported_tables:
                    lines.append(generate_sql_for_model(through_model))
                    exported_tables.add(through_table)

    lines.extend([
        "SET SQL_MODE=@OLD_SQL_MODE;",
        "SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;",
        "SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;",
        "",
        "-- ============================================================================",
        "-- FIN DEL SCRIPT",
        "-- ============================================================================"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analiza los models.py de Django y genera un script SQL para MySQL Workbench sin tablas predeterminadas de Django."
    )
    parser.add_argument(
        '--app',
        type=str,
        default='App',
        help='Nombre de la app específica a procesar (por defecto: App).'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='schema_workbench.sql',
        help='Ruta/nombre del archivo .sql de salida (por defecto: schema_workbench.sql)'
    )
    parser.add_argument(
        '--db-name',
        type=str,
        default='monagua_turismo_db',
        help='Nombre de la base de datos a crear y usar en el script SQL.'
    )
    parser.add_argument(
        '--include-auth',
        action='store_true',
        help='Incluir modelos de autenticación internos de Django (desactivado por defecto).'
    )

    args = parser.parse_args()

    output_path = BASE_DIR / args.output
    print("=" * 60)
    print(" ANALIZADOR DE MODELOS DJANGO -> SQL MYSQL WORKBENCH")
    print(" (Solo modelos de la aplicación, sin tablas internas Django)")
    print("=" * 60)
    print(f"-> Directorio base: {BASE_DIR}")
    print(f"-> App objetivo: {args.app}")
    print(f"-> Base de datos objetivo: {args.db_name}")
    print(f"-> Archivo de salida: {output_path}")
    print("=" * 60)

    sql_content = build_full_sql(
        app_label=args.app,
        include_django_auth=args.include_auth,
        db_name=args.db_name
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)

    print(f"\n[OK] Script SQL generado con exito en:\n   {output_path}")
    print("\nInstrucciones para visualizar en MySQL Workbench:")
    print(" 1. Abre MySQL Workbench.")
    print(" 2. Ve a 'File' -> 'Open SQL Script...' y selecciona este archivo .sql.")
    print(" 3. Ejecuta el script para crear la base de datos y todas las tablas.")
    print(" 4. Para ver el DIAGRAMA EER:")
    print("    - Ve a 'Database' -> 'Reverse Engineer...'")
    print(f"    - Selecciona tu conexion y la base de datos '{args.db_name}'.")
    print("    - Sigue el asistente y Workbench generara el diagrama EER completo.")
    print("    - O tambien: 'File' -> 'Import' -> 'Reverse Engineer MySQL Create Script...'")
    print("      y selecciona el archivo .sql directamente sin necesidad de conexion activa.")
    print("=" * 60)


if __name__ == '__main__':
    main()
