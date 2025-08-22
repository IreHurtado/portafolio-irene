from django.shortcuts import render, redirect
import os
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.core.cache import cache
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


TZ = ZoneInfo("Europe/Madrid")
DAILY_LIMIT = 3            
DUP_WINDOW_SEC = 60        

def _today_str():
    return datetime.now(TZ).strftime("%Y-%m-%d")

def _seconds_until_midnight():
    now = datetime.now(TZ)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())

def _norm_hash(text: str) -> str:
    norm = " ".join((text or "").strip().lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()

def index(request):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        pregunta = (request.POST.get("pregunta") or "").strip()
        if not pregunta:
            return JsonResponse({"respuesta": "Por favor, escribe una pregunta.", "restantes": DAILY_LIMIT})

        user_id = request.META.get("REMOTE_ADDR", "unknown-ip")
        today = _today_str()
        base_key = f"qa:{user_id}:{today}"
        count_key = f"{base_key}:count"
        last_h_key = f"{base_key}:last_h"
        last_ts_key = f"{base_key}:last_ts"

        # Estado actual
        uso_actual = cache.get(count_key, 0)
        last_h = cache.get(last_h_key, "")
        last_ts = float(cache.get(last_ts_key, 0) or 0)
        now_ts = datetime.now(TZ).timestamp()
        exp = _seconds_until_midnight()  

        # Límite alcanzado 
        if uso_actual >= DAILY_LIMIT:
            return JsonResponse({
                "respuesta": "Has alcanzado el límite diario de preguntas 😅.",
                "restantes": 0
            }, status=429)

        # Anti‑duplicado rápido
        h = _norm_hash(pregunta)
        is_dup_recent = (h == last_h) and ((now_ts - last_ts) < DUP_WINDOW_SEC)

        try:
            client = OpenAI(api_key=config("OPENAI_API_KEY"))
            respuesta = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres Irene, una desarrolladora full stack experta, especializándose en IA. Tu objetivo es ayudar con explicaciones claras y cercanas."},
                    {"role": "user", "content":
                        "Responde como si fueras Irene, una desarrolladora empática que explica conceptos técnicos con claridad y sin tecnicismos. "
                        "No respondas sobre política, religión, violencia o personas reales; si la pregunta no está relacionada con tecnología, proyectos o portafolio, "
                        "responde exactamente: 'Solo respondo dudas sobre mi portafolio y el mundo tech. ¿Algo sobre eso?'. "
                        f"Pregunta: {pregunta}"
                    },
                ],
                temperature=0.0,
                max_tokens=200
            )
            texto = (respuesta.choices[0].message.content or "").strip()
        except Exception as e:
            texto = f"Error al conectar con la IA: {str(e)}"

        # Solo consumimos 1 si NO es duplicado reciente y hubo texto de respuesta
        nuevo_uso = uso_actual
        if not is_dup_recent and texto:
            nuevo_uso = uso_actual + 1
            cache.set(count_key, nuevo_uso, exp)

        # Guarda huella y timestamp 
        cache.set_many({
            last_h_key: h,
            last_ts_key: now_ts,
        }, exp)

        restantes = max(DAILY_LIMIT - nuevo_uso, 0)
        return JsonResponse({"respuesta": texto, "restantes": restantes})

    return render(request, "portafolio/index.html")

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
    
