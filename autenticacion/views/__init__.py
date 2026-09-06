from .login.views import login_vista, logout_vista
from .registro.views import (
    registro_vista,
    verificar_otp_registro_vista,
    reenviar_otp_registro_vista,
)
from .recuperar_apodo.views import recuperar_apodo_vista
from .recuperar_clave.views import (
    recuperar_clave_vista,
    verificar_otp_recuperar_vista,
    restablecer_clave_enviado_vista,
    restablecer_clave_confirmar_vista,
    restablecer_clave_guardar_vista,
)
from .ajax.views import verificar_campo_ajax
from .geografia.views import api_paises, api_departamentos, api_ciudades
