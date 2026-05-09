from django.db import models

class Reserva(models.Model):
    cliente = models.ForeignKey('usuarios.Cliente', on_delete=models.CASCADE)
    paquete = models.ForeignKey('catalogo.Paquete', on_delete=models.CASCADE)
    horario = models.CharField(max_length=100) # O el tipo que prefieras
    num_personas = models.PositiveIntegerField()
    estado = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Reserva {self.id} - {self.cliente}"

class Cancelacion(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    motivo = models.TextField()
    penalidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
