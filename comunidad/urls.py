# En cada app: urls/__init__.py  ← vacío

# urls/public.py o urls/cliente.py o urls/admin.py
from django.urls import path
from comunidad import views   # o: from nombre_app import views

app_name = 'comunidad'   # ← cambia por cada app

urlpatterns = [
    path('blog/', views.blog, name='blog'), 
    path('pqrs/', views.pqrs, name='pqrs'), 
    path('pqrs/guardar/', views.guardar_pqrs, name='guardar_pqrs'),
    #PQRS
    path('admin/pqrs/', views.PQRSListView.as_view(), name='listar_pqrs'),
    path('admin/pqrs/contestar/<int:pqrs_id>/', views.contestar_pqrs, name='contestar_pqrs'),
    path('admin/pqrs/guardar/', views.guardar_pqrs, name='guardar_pqrs'),
    
    #BLOG
    path('admin/blog/', views.BlogListView.as_view(), name='listar_blog'),
    path('admin/blog/nuevo/', views.BlogCreateView.as_view(), name='crear_blog'),
    path('admin/blog/editar/<int:pk>/', views.BlogUpdateView.as_view(), name='editar_blog'),
    path('admin/blog/eliminar/<int:pk>/', views.BlogDeleteView.as_view(), name='eliminar_blog'),
    path('blog/usuario/', views.blog_usuario, name='blog_usuario'),
    
    
    
]