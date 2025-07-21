from django.shortcuts import render
import os
from django.conf import settings

def index(request):
    return render(request, 'portafolio/index.html')

def about(request):
    return render(request, 'portafolio/about.html')

def projects(request):
    return render(request, 'portafolio/projects.html')

def contact(request):
    return render(request, 'portafolio/contact.html')

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
    
    