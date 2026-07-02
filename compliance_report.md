# Reporte de Conformidad y Calidad de Código

**Proyecto:** `MNG_WEB` (Django App)
**Cumplimiento Estimado:** `95.8%`  
**Archivos Analizados:**  
- Python: 114  
- HTML: 128  
- CSS: 2  
- JavaScript: 14  

## Tabla de Resultados

| No. | Criterio de Evaluación | Estado | Detalles de Verificación |
| --- | --- | --- | --- |
| 1 | Estructura componentes en sintaxis específica (plantillas) | **✅ CUMPLE** | Se encontraron 113 de 128 plantillas utilizando sintaxis Django (tags {% ... %} o variables {{ ... }}). |
| 2 | Implementa enrutamiento de vistas entre módulos | **✅ CUMPLE** | Se detectaron 9 archivos de enrutamiento (urls.py). Rutas válidas configuradas en: autenticacion\urls.py, catalogo\urls.py, comunidad\urls.py, core\urls.py, notificaciones\urls.py, pagos\urls.py, promociones\urls.py, reservas\urls.py, usuarios\urls.py. |
| 3 | Consume servicios API REST con carga y control de errores | **✅ CUMPLE** | Se detectó consumo API/servicios en 1 archivos (JS: static\js\auth\paises_ciudades.js). Con control de errores (try/catch o .catch): 1. |
| 4 | Estilos CSS bajo esquema atómico o metodología BEM | **✅ CUMPLE** | Se analizaron 2 archivos CSS. Selectores de clase totales: 485. Coincidencias de convención BEM (__ o --): 56. (BEM detectado en: static\css\styles.css) |
| 5 | Binding de datos bidireccional/unidireccional en el DOM | **⚠️ PARCIAL** | Se detectó vinculación (binding) de datos dinámica mediante contexto Django ({{ variable }}) en 86 de 128 archivos de plantilla. |
| 6 | Valida entradas de usuario en formularios | **✅ CUMPLE** | Se encontraron 5 archivos forms.py con esquemas de validación de Django. Se detectó llamada de validación (.is_valid()) en vistas en 5 ocasiones. |
| 7 | Variables de entorno para URLs de servicios y secretos | **✅ CUMPLE** | Análisis de core/settings.py: Carga de .env (load_dotenv): SÍ. Lectura de variables (os.environ): SÍ. |
| 8 | Organiza código en jerarquía de carpetas lógica | **✅ CUMPLE** | Carpetas core del proyecto: core, static, templates de 3. Apps de Django estructuradas e independientes detectadas: autenticacion, catalogo, comunidad, guias, IA, notificaciones, pagos, promociones, reservas, usuarios. |
| 9 | Implementa pruebas unitarias básicas sobre componentes | **✅ CUMPLE** | Se detectaron 11 archivos de pruebas unitarias. Casos de prueba definidos: 45. Aserciones de validación: 150. |
| 10 | Optimiza carga mediante lazy loading o paginación | **✅ CUMPLE** | Uso de `loading='lazy'` en imágenes de plantillas: 6 de 99. Implementación de Paginación en Backend (Django Paginator): SÍ. |
| 11 | Documenta componentes creados mediante JSDoc/Docstrings | **✅ CUMPLE** | Se detectaron 80 bloques de docstrings en archivos Python (para 252 funciones totales) y 4 bloques de JSDoc en archivos JS. |
| 12 | Garantiza adaptabilidad (diseño responsivo / Grid / Flexbox) | **✅ CUMPLE** | Uso de `@media` queries en CSS: 8. Propiedades flex/grid directas: 9. Clases de grilla/flex Bootstrap en plantillas: 1092. |


---
*Reporte generado automáticamente por `check_compliance.py`.*
