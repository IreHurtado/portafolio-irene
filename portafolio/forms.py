from django import forms

class ContactForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre completo",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre"})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"})
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ej (123) 456-7890"})
        
    )
    mensaje = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(attrs={"placeholder": "Tu mensaje ...", "rows":5})
        
    )