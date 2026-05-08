# En cada app: urls/__init__.py  ← vacío

# urls/public.py o urls/cliente.py o urls/admin.py
from django.urls import path
from comunidad import views   # o: from nombre_app import views

app_name = 'comunidad'   # ← cambia por cada app

urlpatterns = [
    #PQRS
    path('pqrs/', views.PQRSListView.as_view(), name='listar_pqrs'),
    path('pqrs/nueva/', views.PQRSCreateView.as_view(), name='crear_pqrs'),
    path('pqrs/editar/<int:pk>/', views.PQRSUpdateView.as_view(), name='editar_pqrs'),
    path('pqrs/eliminar/<int:pk>/', views.PQRSDeleteView.as_view(), name='eliminar_pqrs'),
    #BLOG
    path('blog/', views.BlogListView.as_view(), name='listar_blog'),
    path('blog/nuevo/', views.BlogCreateView.as_view(), name='crear_blog'),
    path('blog/editar/<int:pk>/', views.BlogUpdateView.as_view(), name='editar_blog'),
    path('blog/eliminar/<int:pk>/', views.BlogDeleteView.as_view(), name='eliminar_blog'),
    
]