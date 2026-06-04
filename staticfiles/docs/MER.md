erDiagram
    %% Relaciones
    USUARIO ||--o| CLIENTE : "es un"
    USUARIO ||--o| GUIA_TURISTICO : "es un"
    USUARIO ||--o{ RESERVA : "realiza"
    PAQUETE ||--o{ RESERVA : "tiene"
    RESERVA ||--o| CANCELACION : "puede tener"
    CATEGORIA ||--o{ PAQUETE : "agrupa"
    PAQUETE ||--o{ PAQUETE_ACTIVIDAD : "incluye"
    ACTIVIDADES ||--o{ PAQUETE_ACTIVIDAD : "es incluida"
    TEMPORADA ||--o{ TARIFA : "define"
    PAQUETE ||--o{ TARIFA : "tiene"
    CLIENTE ||--o{ CALIFICACION : "deja"
    PAQUETE ||--o{ CALIFICACION : "recibe"
    CLIENTE ||--o{ PQRS : "crea"

    %% Entidades y Atributos

    USUARIO {
        int id PK "ej: 1"
        string username "ej: juanperez"
        string password "ej: pbkdf2_sha256$..."
        string email "ej: juan@email.com"
        string first_name "ej: Juan"
        string last_name "ej: Perez"
        string rol "opciones: ADMIN, CLIENTE, GUIA"
        string tipo_documento "opciones: CC, CE, PASAPORTE"
        string numero_documento "ej: 1234567890"
        string telefono "ej: 3101234567"
        string residencia "ej: Bogotá, Colombia"
        string imagen_perfil "ej: perfiles/juan.jpg"
        bool is_active "ej: true"
    }

    CLIENTE {
        int id PK "ej: 1"
        int usuario_id FK "ej: 1"
        string pais "ej: Colombia"
        string ciudad "ej: Bogotá"
    }

    GUIA_TURISTICO {
        int id PK "ej: 1"
        int usuario_id FK "ej: 2"
        string licencia_turismo "ej: COL-12345"
        int experiencia_anos "ej: 5"
        string biografia "ej: Experto en ecoturismo..."
    }

    RESERVA {
        int id PK "ej: 100"
        int usuario_id FK "ej: 1"
        int paquete_id FK "ej: 5"
        date fecha "ej: 2026-06-15"
        int numero_adultos "ej: 2"
        int numero_menores "ej: 1"
        string estado "opciones: pendiente, confirmada, completada, cancelada"
        int monto_total "ej: 250000"
        datetime fecha_registro "ej: 2026-05-15 08:30:00"
    }

    CANCELACION {
        int id PK "ej: 1"
        int reserva_id FK "ej: 100"
        string motivo "ej: Problemas de salud"
        float penalidad "ej: 25000.00"
    }

    CATEGORIA {
        int id PK "ej: 1"
        string nombre "ej: Ecoturismo"
        string descripcion "ej: Actividades al aire libre..."
        bool estado "ej: true"
    }

    ACTIVIDADES {
        int id PK "ej: 1"
        string nombre "ej: Senderismo"
        string descripcion "ej: Caminata de 5km..."
        string nivel_dificultad "opciones: Alta, Media, Baja"
        string equipo_requerimiento "ej: Botas, hidratación..."
        string recomendacion_salud "ej: Buen estado físico"
        bool estado "ej: true"
        bool apto_para_menores "ej: true"
    }

    PAQUETE {
        int id PK "ej: 1"
        string imagen "ej: destinos/paquete1.jpg"
        string nombre "ej: Aventura en la Montaña"
        string descripcion "ej: Paquete completo de 3 días..."
        int dias_duracion "ej: 3"
        int noches_duracion "ej: 2"
        string punto_encuentro "ej: Plaza Central"
        int categoria_id FK "ej: 1"
        bool estado "ej: true"
    }

    TEMPORADA {
        int id PK "ej: 1"
        string nombre "ej: Temporada Alta"
        date fecha_inicio "ej: 2026-06-01"
        date fecha_fin "ej: 2026-08-31"
    }

    TARIFA {
        int id PK "ej: 1"
        int paquete_id FK "ej: 1"
        int temporada_id FK "ej: 1"
        int precio_adulto "ej: 150000"
        int precio_menor "ej: 75000"
    }

    PAQUETE_ACTIVIDAD {
        int id PK "ej: 1"
        int paquete_id FK "ej: 1"
        int actividad_id FK "ej: 1"
    }

    CALIFICACION {
        int id PK "ej: 1"
        int cliente_id FK "ej: 1"
        int paquete_id FK "ej: 1"
        int puntaje "ej: 5"
        string comentario "ej: Excelente experiencia!"
        datetime fecha "ej: 2026-05-15 10:00:00"
    }

    BLOG {
        int id PK "ej: 1"
        string titulo "ej: Top 5 destinos"
        string contenido "ej: Los mejores lugares para visitar..."
        string imagen "ej: blog/destinos.jpg"
        datetime fecha_publicacion "ej: 2026-05-15 10:00:00"
        bool publicado "ej: true"
    }

    PQRS {
        int id PK "ej: 1"
        int cliente_id FK "ej: 1"
        string tipo "opciones: peticion, queja, reclamo, sugerencia"
        string asunto "ej: Información de paquete"
        string descripcion "ej: Quisiera saber si..."
        string estado "opciones: abierto, en_proceso, cerrado"
        string respuesta "ej: Estimado cliente..."
        datetime fecha "ej: 2026-05-15 10:00:00"
    }
