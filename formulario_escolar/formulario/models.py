from django.db import models
from django.contrib.auth.models import User  
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profesor')
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_contratacion = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Periodo(models.Model):
    PERIODO_CHOICES = [
        ('I', 'Periodo I'),
        ('II', 'Periodo II'),
    ]
    
    nombre = models.CharField(max_length=2, choices=PERIODO_CHOICES)
    año = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    class Meta:
        unique_together = ('nombre', 'año')
        ordering = ['-año', 'nombre']
    
    def __str__(self):
        return f"{self.get_nombre_display()} - {self.año}"

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    direccion = models.TextField()  
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    foto = models.ImageField(upload_to='estudiantes/', blank=True, null=True, verbose_name="Foto del alumno")
    matricula = models.CharField(max_length=20, unique=True, blank=True, null=True)  

    class Meta:
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True, related_name='materias_impartidas')
    nota_minima_aprobatoria = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    
    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'Materias'
    
    def save(self, *args, **kwargs):
        # Si el nombre contiene "proyecto" (case insensitive), establecer nota mínima en 16
        if 'proyecto' in self.nombre.lower():
            self.nota_minima_aprobatoria = 16
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nombre

class Inscripcion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ('alumno', 'materia', 'periodo')
        verbose_name_plural = 'Inscripciones'
        ordering = ['-fecha_inscripcion']
    
    def __str__(self):
        return f"{self.alumno} en {self.materia} ({self.periodo})"

    @property
    def promedio(self):
        notas = self.notas.all()
        if notas.exists():
            return sum(nota.valor for nota in notas) / notas.count()
        return 0
    
    @property
    def aprobada(self):
        promedio = self.promedio
        return promedio >= self.materia.nota_minima_aprobatoria if promedio else False

class Nota(models.Model):
    TIPOS_EVALUACION = [
        ('P1', 'Examen'),
        ('P2', 'Taller'),
        ('P3', 'Exposición'),
        ('EX', 'Examen Final'),
        ('TA', 'Tarea'),
        ('PR', 'Proyecto'),
        ('OT', 'Otro'),
    ]
    
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name='notas')
    tipo = models.CharField(max_length=2, choices=TIPOS_EVALUACION, default='P1')
    valor = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[
            MinValueValidator(0), 
            MaxValueValidator(100)
        ]
    )
    fecha_registro = models.DateField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['fecha_registro']
        verbose_name_plural = 'Notas'
    
    def __str__(self):
        return f"{self.inscripcion.alumno} - {self.inscripcion.materia}: {self.valor} ({self.get_tipo_display()})"



def asignar_periodo_default(apps, schema_editor):
    Periodo = apps.get_model('formulario', 'Periodo')
    Inscripcion = apps.get_model('formulario', 'Inscripcion')
    
    # Crear un período por defecto si no existe
    periodo, created = Periodo.objects.get_or_create(
        nombre='I',
        año=2025,
        defaults={
            'fecha_inicio': '2025-01-01',
            'fecha_fin': '2025-06-30'
        }
    )
    

