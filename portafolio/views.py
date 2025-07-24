from django.shortcuts import render, redirect
import os
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from decouple import config
from .models import MensajeContacto

def index(request):
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
                messages.success(request, "Tu mensaje ha sido enviado con éxito!")
                return redirect("contact")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al enviar el mensaje: {str(e)}")
                
            MensajeContacto.objects.create(
                nombre=nombre,
                email=email,
                telefono=telefono,
                mensaje=mensaje
                )
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
    
    