from django.db import models
from usuarios.models import Usuario

class ConversacionIA(models.Model):
    usuario    = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    sesion_id  = models.CharField(max_length=100)
    creada_en  = models.DateTimeField(auto_now_add=True)

class MensajeIA(models.Model):
    ROL_CHOICES = [('user','Usuario'), ('assistant','Asistente')]
    conversacion = models.ForeignKey(ConversacionIA, on_delete=models.CASCADE, related_name='mensajes')
    rol          = models.CharField(max_length=10, choices=ROL_CHOICES)
    contenido    = models.TextField()
    creado_en    = models.DateTimeField(auto_now_add=True)