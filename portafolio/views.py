from django.shortcuts import render, redirect
import os
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from decouple import config
from .models import MensajeContacto
from openai import OpenAI
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt


def index(request):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        pregunta = request.POST.get("pregunta", "")
        if not pregunta:
            return JsonResponse({"respuesta": "Por favor, escribe una pregunta.", "restantes": 3})
        
        ip = request.META.get('REMOTE_ADDR')
        uso_actual = cache.get(ip, 0)

        LIMITE_DIARIO = 3
        RESTANTES = LIMITE_DIARIO - uso_actual

        if uso_actual >= LIMITE_DIARIO:
            return JsonResponse({"respuesta": "Has alcanzado el límite diario de preguntas 😅. ", "restantes": 0})
        

        prompt = (
            "Responde como si fueras Irene, una desarrolladora empática que explica conceptos técnicos "
            "con claridad, sin tecnicismos y de forma divertida. Pregunta: " + pregunta
        )

        try:
            
            client = OpenAI(api_key=config("OPENAI_API_KEY"))

            respuesta = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres Irene, una desarrolladora full stack experta, especializándose en IA. Tu objetivo es ayudar con explicaciones claras y cercanas."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=200
            )

            texto = respuesta.choices[0].message.content.strip()
            cache.set(ip, uso_actual + 1, 86400)  
            return JsonResponse({"respuesta": texto, "restantes": RESTANTES - 1})
        
        except Exception as e:
            return JsonResponse({"respuesta": f"Error al conectar con la IA: {str(e)}", "restantes": RESTANTES})
        
    
    return render(request, 'portafolio/index.html')

def about(request):
    return render(request, 'portafolio/about.html')

def projects(request):
    return render(request, 'portafolio/projects.html')

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            email = form.cleaned_data['email']
            telefono = form.cleaned_data['telefono']
            mensaje = form.cleaned_data['mensaje']

            contenido = (
                f"Nombre: {nombre}\n"
                f"Correo electrónico: {email}\n"
                f"Teléfono: {telefono if telefono else 'No proporcionado'}\n"
                f"Mensaje:\n{mensaje}"
            )

            subject = f"Nuevo mensaje de {nombre}"
            from_email = config("EMAIL_HOST_USER")
            recipient_list = ["irenehurtadoguerrero@gmail.com"]

            try:
                send_mail(subject, contenido, from_email, recipient_list)
                
                MensajeContacto.objects.create(
                nombre=nombre,
                email=email,
                telefono=telefono,
                mensaje=mensaje
                )
                            
                messages.success(request, "Tu mensaje ha sido enviado con éxito!")
                return redirect("contact")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al enviar el mensaje: {str(e)}")
                

    else:
        form = ContactForm()

    return render(request, "portafolio/contact.html", {"form": form})

def certificados_categoria(request, categoria):
    categorias_validas = ['frontend', 'backend', 'frameworks']
    if categoria not in categorias_validas:
        return render(request, '404.html', status=404)
    
    ruta_base = os.path.join(settings.STATICFILES_DIRS[0], 'certificados', categoria)
    archivos = []
    if os.path.exists(ruta_base):
        archivos = os.listdir(ruta_base)
    
    return render(request, 'portafolio/certificados.html', {
        'categoria': categoria.capitalize(),
        'archivos': archivos,
        'ruta': f'certificados/{categoria}/'
    })
    
