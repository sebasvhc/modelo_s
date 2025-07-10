from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Alumno, Materia, Inscripcion, Nota, Periodo, Profesor
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class ProfesorForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", required=True)
    last_name = forms.CharField(label="Apellido", required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Profesor
        fields = ['cedula', 'telefono', 'direccion']
        widgets = {
            'cedula': forms.TextInput(attrs={'placeholder': 'V-12345678'}),
            'telefono': forms.TextInput(attrs={'placeholder': '0412-1234567'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dirección completa...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        if not self.instance.pk:  # Creando nuevo profesor
            username = self.cleaned_data['cedula']
            user = User.objects.create_user(
                username=username,
                email=self.cleaned_data['email'],
                password=username,  # La cédula como contraseña inicial
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            self.instance.user = user
        else:  # Actualizando profesor existente
            self.instance.user.first_name = self.cleaned_data['first_name']
            self.instance.user.last_name = self.cleaned_data['last_name']
            self.instance.user.email = self.cleaned_data['email']
            self.instance.user.save()
        
        return super().save(commit)

class PeriodoForm(forms.ModelForm):
    class Meta:
        model = Periodo
        fields = '__all__'
        widgets = {
            'nombre': forms.Select(attrs={'class': 'form-control'}),
            'año': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2030}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        help_texts = {
            'fecha_fin': 'La fecha debe ser posterior a la fecha de inicio',
        }

class MateriaForm(forms.ModelForm):
    profesor_nombre = forms.CharField(
        required=False,
        label="Nombre del Profesor",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar profesor existente o escribir nuevo',
            'id': 'profesor-buscar'
        })
    )

    class Meta:
        model = Materia
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas Básicas'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.profesor:
            self.fields['profesor_nombre'].initial = self.instance.profesor.user.get_full_name()

    def save(self, commit=True):
        materia = super().save(commit=False)
        profesor_nombre = self.cleaned_data.get('profesor_nombre')
        
        if profesor_nombre:
            # Buscar profesor existente sin crear uno nuevo
            nombres = profesor_nombre.split()
            first_name = nombres[0] if nombres else ''
            last_name = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            # Buscar cualquier profesor que coincida con el nombre
            profesores = Profesor.objects.filter(
                user__first_name__iexact=first_name,
                user__last_name__iexact=last_name
            )
            
            if profesores.exists():
                # Usar el primer profesor encontrado
                materia.profesor = profesores.first()
            else:
                # Crear nuevo profesor solo si no existe
                username = f"{first_name.lower()}_{last_name.lower()}" if last_name else first_name.lower()
                
                user = User.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}@escuela.com",
                    password='passwordtemporal'  # Debe cambiarse después
                )
                
                materia.profesor = Profesor.objects.create(
                    user=user,
                    cedula=f"V-{user.id}0000",  # Cédula temporal
                    telefono='00000000000',
                    direccion='Por definir'
                )
        
        if commit:
            materia.save()
        
        return materia

class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['alumno', 'materia', 'periodo']
        widgets = {
            'alumno': forms.Select(attrs={'class': 'form-control'}),
            'materia': forms.Select(attrs={'class': 'form-control'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
        }

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['tipo', 'valor', 'comentario']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Comentarios sobre la evaluación...'
            }),
        }

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor < 0 or valor > 100:
            raise forms.ValidationError("La nota debe estar entre 0 y 100.")
        return valor

class AsignarMateriasForm(forms.Form):
    periodo = forms.ModelChoiceField(
        queryset=Periodo.objects.filter(nombre__in=['I', 'II']).order_by('-año'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Período Académico"
    )
    
    def __init__(self, *args, alumno=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.alumno = alumno
        if alumno:
            self.fields['materias'] = forms.ModelMultipleChoiceField(
                queryset=Materia.objects.all().order_by('nombre'),
                widget=forms.CheckboxSelectMultiple,
                required=True,
                label="Seleccione materias"
            )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

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
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Pérez',
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