from django.urls import path
from . import views


urlpatterns = [

    # 1. RUTAS PÚBLICAS Y AUTENTICACIÓN
    path('', views.index_turista, name='inicio'), # Home / Landing
    path('login/', views.UsuarioLoginView.as_view(), name='login'),
    path('logout/', views.UsuarioLogoutView.as_view(), name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('terminos/', views.terminos_view, name='terminos'),
    path('nosotros/', views.nosotros_view, name='nosotros'),
    
    # 2. MÓDULO DEL TURISTA (CLIENTE)
    path('panel_inicio/', views.index_turista, name='index_turista'),
    path('mi-dashboard/', views.index_turista, name='dashboard_turista'),
    path('mi-perfil/', views.perfil_detalles, name='perfil_detalles'),
    path('mis-resenas/', views.mis_resenas_view, name='mis_resenas'),
    path('mis-estadisticas/', views.estadisticas_turista, name='mis_estadisticas'),
    

    # 3. MÓDULO DEL ADMINISTRADOR
    path('admin-dashboard/', views.dashboard_admin, name='dashboard'),
    path('perfil-administrador/', views.perfil_detalles, name='perfil_administrador'),
    path('comentarios/', views.listar_comentarios, name='listar_comentarios'),
    path('comentarios/toggle/<int:pk>/', views.toggle_visible, name='toggle_visible'),
    path('comentarios/responder/<int:pk>/', views.responder_comentario, name='responder_comentario'),
    path('gestion-usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('gestion-usuarios/guardar/', views.usuarios_guardar, name='usuarios_guardar'),
    path('gestion-usuarios/toggle/<int:user_id>/', views.usuarios_toggle_estado, name='usuarios_toggle_estado'),

    # 4. GESTIÓN DE GUÍAS (PERSONAL)
    path('gestion-guias/', views.gestion_guias, name='gestion_guias'),
    path('gestion-guias/<int:id>/', views.gestion_guias, name='gestion_guias_sel'),
    path('asignar-rol-guia/<int:user_id>/', views.asignar_rol_guia, name='asignar_rol_guia'),
    path('guias-guardar/', views.guias_guardar, name='guias_guardar'),

]