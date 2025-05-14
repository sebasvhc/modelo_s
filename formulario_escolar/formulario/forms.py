from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Alumno, Materia, Inscripcion, Nota
from django.contrib.auth.models import User
import re

class AlumnoForm(forms.ModelForm):
    confirmar_email = forms.EmailField(
        label="Confirmar Email",
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Repite tu email'})
    )

    class Meta:
        model = Alumno
        fields = '__all__'
        exclude = ['fecha_inscripcion']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Pedro',
                'class': 'form-control'
            }),
            'edad': forms.NumberInput(attrs={
                'min': '15',
                'max': '100',
                'class': 'form-control'
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '04123456789',
                'class': 'form-control'
            }),
            'fecha_inscripcion': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'foto': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        
        labels = {
            'nombre': 'Nombre Completo',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
            'foto': 'Foto del alumno',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if any(char.isdigit() for char in nombre):
            raise ValidationError("El nombre no puede contener números.")
        return nombre.strip()

    def clean_edad(self):
        edad = self.cleaned_data['edad']
        if edad < 18:
            raise ValidationError("La edad mínima es 18 años.")
        return edad

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirmar_email = cleaned_data.get('confirmar_email')

        if email and confirmar_email and email != confirmar_email:
            self.add_error('confirmar_email', "Los emails no coinciden.")

        if not self.instance.pk and Alumno.objects.filter(email=email).exists():
            self.add_error('email', "Este email ya está registrado.")

        return cleaned_data

class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'creditos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profesor': forms.Select(attrs={'class': 'form-control'}),
        }

class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['alumno', 'materia', 'ciclo_escolar']
        widgets = {
            'alumno': forms.Select(attrs={'class': 'form-control'}),
            'materia': forms.Select(attrs={'class': 'form-control'}),
            'ciclo_escolar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2024-1'
            }),
        }

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['inscripcion', 'tipo', 'valor', 'comentario']
        widgets = {
            'inscripcion': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones sobre la evaluación'
            }),
        }

class AsignarMateriasForm(forms.Form):
    ciclo_escolar = forms.ChoiceField(
        choices=[
            ('2023-1', '2023-1'),
            ('2023-2', '2023-2'), 
            ('2024-1', '2024-1'),
            ('2024-2', '2024-2'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, alumno=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.alumno = alumno
        if alumno:
            # Mostrar todas las materias, la validación de duplicados se hará después
            self.fields['materias'] = forms.ModelMultipleChoiceField(
                queryset=Materia.objects.all(),
                widget=forms.CheckboxSelectMultiple,
                required=True,
                label="Seleccione materias"
            )