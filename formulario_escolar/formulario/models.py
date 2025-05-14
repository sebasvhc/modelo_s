from django.db import models
from django.contrib.auth.models import User  # Para relacionar profesores
from django.core.validators import MinValueValidator, MaxValueValidator


class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    direccion = models.TextField()  
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    foto = models.ImageField(upload_to='estudiantes/', blank=True, null=True, verbose_name="Foto del alumno")
    matricula = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Nuevo campo para matrícula

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    creditos = models.PositiveIntegerField()
    profesor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='materias_impartidas')
    descripcion = models.TextField(blank=True, null=True)
    alumnos = models.ManyToManyField(Alumno, through='Inscripcion', related_name='materias')
    
    def __str__(self):
        return self.nombre

class Inscripcion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    ciclo_escolar = models.CharField(max_length=20)  # Ej: "2024-1", "2024-2"
    
    class Meta:
        unique_together = ('alumno', 'materia', 'ciclo_escolar')
        verbose_name_plural = 'Inscripciones'
    
    def __str__(self):
        return f"{self.alumno} en {self.materia} ({self.ciclo_escolar})"

class Nota(models.Model):
    TIPOS_EVALUACION = [
        ('P1', 'Parcial 1'),
        ('P2', 'Parcial 2'),
        ('P3', 'Parcial 3'),
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
    
    def __str__(self):
        return f"{self.inscripcion.alumno} - {self.inscripcion.materia}: {self.valor} ({self.get_tipo_display()})"