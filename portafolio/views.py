from django.shortcuts import render

def index(request):
    return render(request, 'portafolio/index.html')

def about(request):
    return render(request, 'portafolio/about.html')

def projects(request):
    return render(request, 'portafolio/projects.html')

def contact(request):
    return render(request, 'portafolio/contact.html')