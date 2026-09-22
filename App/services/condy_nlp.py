import re
import unicodedata

# Definir FAQs relacionadas con el negocio (Ecoturismo/Reservas)
FAQS = [
    {
        "keywords": ["horario", "horarios", "hora", "horas", "abren", "cierran", "apertura", "cierre", "atencion", "disponibilidad", "jornada"],
        "answer": "Nuestro horario de atención es de Lunes a Domingo de 8:00 AM a 6:00 PM."
    },
    {
        "keywords": ["ubicacion", "donde", "direccion", "llegar", "ubicado", "ubicados", "sitio", "lugar", "encuentran", "queda"],
        "answer": "Nos encontramos ubicados en el centro de la ciudad, en la dirección principal. ¡Esperamos tu visita!"
    },
    {
        "keywords": ["servicio", "servicios", "ofrecen", "hacen", "actividad", "actividades", "tour", "tours", "paquete", "paquetes", "planes", "plan", "experiencias", "excursiones"],
        "answer": "Ofrecemos reservas de tours, paquetes turísticos, actividades al aire libre y servicios con guías especializados."
    },
    {
        "keywords": ["precio", "precios", "costo", "costos", "valor", "valores", "tarifa", "tarifas", "cuanto", "vale", "cuesta", "cobran", "dinero"],
        "answer": "Nuestros precios varían según el paquete o la actividad. Puedes consultar las tarifas detalladas en la sección de 'Tours' de nuestra página."
    },
    {
        "keywords": ["reserva", "reservas", "reservar", "agendar", "apartar", "cupo", "cupos", "booking", "separar", "programar"],
        "answer": "Puedes reservar directamente a través de nuestra plataforma web ingresando a la sección de 'Tours' o añadiendo un paquete a tu carrito."
    },
    {
        "keywords": ["pago", "pagos", "pagar", "metodo", "tarjeta", "efectivo", "transferencia", "nequi", "daviplata", "consignacion", "credito", "debito"],
        "answer": "Aceptamos pagos con tarjeta de crédito, débito y transferencias. Debes enviar el comprobante de pago en el módulo correspondiente."
    },
    {
        "keywords": ["cancelar", "reembolso", "devolucion", "cancelacion", "retracto", "cancelado", "reembolsar"],
        "answer": "Las cancelaciones deben realizarse con al menos 48 horas de anticipación para ser elegibles para un reembolso total. Puedes gestionar tus cancelaciones en tu perfil."
    },
    {
        "keywords": ["mascota", "mascotas", "perro", "perros", "gato", "gatos", "animal", "animales", "pet", "petfriendly"],
        "answer": "¡Sí! Somos un lugar pet-friendly. Tus mascotas son bienvenidas en la mayoría de nuestras actividades."
    },
    {
        "keywords": ["contacto", "telefono", "celular", "email", "correo", "llamar", "whatsapp", "comunicarse", "numero", "escribir"],
        "answer": "Puedes contactarnos al teléfono +57 322 3465191 o al correo contacto@monagua.com. También puedes dejar un ticket en nuestra sección de Contacto."
    },
    {
        "keywords": ["guia", "guias", "personas", "acompañante", "acompañantes", "orientador", "asesor", "instructor"],
        "answer": "Nuestros tours incluyen guías turísticos certificados que te acompañarán durante toda la experiencia."
    },
    {
        "keywords": ["comida", "comidas", "restaurante", "almuerzo", "desayuno", "cena", "hambre", "alimentacion", "bebida", "bebidas", "snacks", "refrigerio", "alimentos"],
        "answer": "Durante nuestras actividades recomendamos llevar hidratación y snacks. También puedes consultar por los restaurantes aliados del pueblo."
    }
]

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def procesar_mensaje(mensaje, request):
    if 'condy_fallos' not in request.session:
        request.session['condy_fallos'] = 0

    # 1. Regulación: Normalizar espaciados nulos o dobles (eliminar espacios múltiples y al inicio/final)
    mensaje = re.sub(r'\s+', ' ', mensaje).strip()

    # 2. Convertir a minúsculas y quitar tildes
    mensaje_lower = remove_accents(mensaje.lower())
    
    # 3. Regulación: Evitar falsos positivos como "perros calientes" cambiándolo a una palabra relacionada con comida
    mensaje_lower = mensaje_lower.replace("perros calientes", "comida").replace("perro caliente", "comida")
    
    mejor_coincidencia = None
    max_coincidencias = 0
    
    for faq in FAQS:
        # Usar SOLO coincidencias de palabras completas (\b) para evitar alucinaciones por subcadenas
        coincidencias = sum(1 for keyword in faq['keywords'] if re.search(r'\b' + re.escape(keyword) + r'\b', mensaje_lower))
            
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_coincidencia = faq

    if mejor_coincidencia and max_coincidencias > 0:
        request.session['condy_fallos'] = 0
        return {
            "response": mejor_coincidencia['answer'],
            "options": []
        }
    
    request.session['condy_fallos'] += 1
    
    if request.session['condy_fallos'] >= 2:
        request.session['condy_fallos'] = 0
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
