import re

# Definir 10 FAQs relacionadas con el negocio (Ecoturismo/Reservas) basadas en las vistas
FAQS = [
    {
        "keywords": ["horario", "hora", "abren", "cierran"],
        "answer": "Nuestro horario de atención es de Lunes a Domingo de 8:00 AM a 6:00 PM."
    },
    {
        "keywords": ["ubicacion", "donde", "direccion", "llegar"],
        "answer": "Nos encontramos ubicados en el centro de la ciudad, en la dirección principal. ¡Esperamos tu visita!"
    },
    {
        "keywords": ["servicio", "ofrecen", "que hacen", "actividad", "tour", "paquete"],
        "answer": "Ofrecemos reservas de tours, paquetes turísticos, actividades al aire libre y servicios con guías especializados."
    },
    {
        "keywords": ["precio", "costo", "valor", "tarifa", "cuanto vale"],
        "answer": "Nuestros precios varían según el paquete o la actividad. Puedes consultar las tarifas detalladas en la sección de 'Tours' de nuestra página."
    },
    {
        "keywords": ["reserva", "reservar", "como", "agendar"],
        "answer": "Puedes reservar directamente a través de nuestra plataforma web ingresando a la sección de 'Tours' o añadiendo un paquete a tu carrito."
    },
    {
        "keywords": ["pago", "pagar", "metodo", "tarjeta", "efectivo"],
        "answer": "Aceptamos pagos con tarjeta de crédito, débito y transferencias. Debes enviar el comprobante de pago en el módulo correspondiente."
    },
    {
        "keywords": ["cancelar", "reembolso", "devolucion", "cancelacion"],
        "answer": "Las cancelaciones deben realizarse con al menos 48 horas de anticipación para ser elegibles para un reembolso total. Puedes gestionar tus cancelaciones en tu perfil."
    },
    {
        "keywords": ["mascota", "perro", "gato", "animales"],
        "answer": "¡Sí! Somos un lugar pet-friendly. Tus mascotas son bienvenidas en la mayoría de nuestras actividades."
    },
    {
        "keywords": ["contacto", "telefono", "email", "correo", "llamar"],
        "answer": "Puedes contactarnos al teléfono +123456789 o al correo contacto@monagua.com. También puedes dejar un ticket en nuestra sección de Contacto."
    },
    {
        "keywords": ["guia", "personas", "acompañante"],
        "answer": "Nuestros tours incluyen guías turísticos certificados que te acompañarán durante toda la experiencia."
    }
]

def procesar_mensaje(mensaje, request):
    # Inicializar conteo de fallos en la sesión si no existe
    if 'condy_fallos' not in request.session:
        request.session['condy_fallos'] = 0

    mensaje_lower = mensaje.lower()
    
    # Buscar coincidencia simple
    mejor_coincidencia = None
    max_coincidencias = 0
    
    for faq in FAQS:
        # Contar cuántas keywords de esta FAQ están en el mensaje
        coincidencias = sum(1 for keyword in faq['keywords'] if re.search(r'\b' + re.escape(keyword) + r'\b', mensaje_lower))
        
        # También buscar subcadenas si no hay coincidencia exacta de palabra (útil para español sin tildes)
        if coincidencias == 0:
            coincidencias = sum(1 for keyword in faq['keywords'] if keyword in mensaje_lower)
            
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_coincidencia = faq

    # Si hay una coincidencia clara
    if mejor_coincidencia and max_coincidencias > 0:
        request.session['condy_fallos'] = 0 # Reiniciar fallos
        return {
            "response": mejor_coincidencia['answer'],
            "options": []
        }
    
    # Si no se entiende el mensaje (Fallback - CA4)
    request.session['condy_fallos'] += 1
    
    if request.session['condy_fallos'] >= 2:
        # Ofrecer handover / ticket
        request.session['condy_fallos'] = 0 # Reiniciar después de ofrecer
        return {
            "response": "Lo siento, no he podido entenderte después de varios intentos. ¿Te gustaría dejar un ticket para que un agente de nuestro equipo te contacte?",
            "fallback_action": "ticket",
            "options": []
        }
    else:
        return {
            "response": "Lo siento, no he entendido tu pregunta. ¿Podrías reformularla o usar otras palabras?",
            "options": ["¿Cuáles son sus horarios?", "¿Qué servicios ofrecen?"]
        }
