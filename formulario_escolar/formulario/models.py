from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.db.models import Avg

def obtener_año_actual():
    """Función para obtener el año actual (serializable para migraciones)"""
    return datetime.datetime.now().year

# 1. Primero define Alumno
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

# 2. Luego define Profesor
class Profesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profesor')
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_contratacion = models.DateField(auto_now_add=True)
    
    def __str__(self):
        try:
            return f"{self.user.first_name} {self.user.last_name}"
        except (ObjectDoesNotExist, AttributeError):
            return f"Profesor {self.cedula} (sin usuario)"
    
    @property
    def nombre_completo(self):
        try:
            return f"{self.user.first_name} {self.user.last_name}"
        except (ObjectDoesNotExist, AttributeError):
            return "Nombre no disponible"

# 3. Luego define Periodo
class Periodo(models.Model):
    PERIODO_CHOICES = [
        ('I', 'Periodo I (Enero-Junio)'),
        ('II', 'Periodo II (Julio-Diciembre)'),
    ]
    
    nombre = models.CharField(max_length=2, choices=PERIODO_CHOICES, unique=True)
    año_actual = models.PositiveIntegerField(
        default=obtener_año_actual,  # Usamos la función definida arriba
        verbose_name="Año"
    )
    
    class Meta:
        verbose_name = "Período"
        verbose_name_plural = "Períodos"
        ordering = ['-año_actual', 'nombre']
    
    def __str__(self):
        return f"{self.get_nombre_display()} - {self.año_actual}"
    
    @property
    def fecha_inicio(self):
        return datetime.date(self.año_actual, 1, 1) if self.nombre == 'I' else datetime.date(self.año_actual, 7, 1)
    
    @property
    def fecha_fin(self):
        return datetime.date(self.año_actual, 6, 30) if self.nombre == 'I' else datetime.date(self.año_actual, 12, 15)
    
    @classmethod
    def obtener_periodos_actuales(cls):
        """Obtiene o crea los períodos del año actual"""
        year = obtener_año_actual()  # Usamos la función auxiliar
        periodo_i, _ = cls.objects.get_or_create(nombre='I', defaults={'año_actual': year})
        periodo_ii, _ = cls.objects.get_or_create(nombre='II', defaults={'año_actual': year})
        return [periodo_i, periodo_ii]

# 4. Luego define Materia (que depende de Profesor)
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
        if 'proyecto' or 'Proyecto' in self.nombre.lower():
            self.nota_minima_aprobatoria = 16
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nombre

# 5. Finalmente define Inscripcion (que depende de Alumno, Materia y Periodo)
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

    def calcular_promedio_general(self):
        """
        Calcula el promedio para materias regulares (nota mínima 12)
        Retorna el promedio o 0 si no hay notas
        """
        from django.db.models import Avg
        resultado = self.notas.aggregate(promedio=Avg('valor'))
        return resultado['promedio'] if resultado['promedio'] is not None else 0

    def calcular_promedio_proyecto(self):
        """
        Calcula el promedio para materias de proyecto (nota mínima 16)
        Retorna el promedio o 0 si no hay notas
        """
        # Mismo cálculo pero con diferente lógica de aprobación
        return self.calcular_promedio_general()  # El cálculo es igual, cambia el mínimo

    def es_materia_proyecto(self):
        """
        Determina si esta inscripción es para una materia de proyecto
        """
        return 'proyecto' in self.materia.nombre.lower()

    @property
    def promedio(self):
        """
        Propiedad que selecciona el cálculo adecuado según el tipo de materia
        """
        if self.es_materia_proyecto():
            return self.calcular_promedio_proyecto()
        return self.calcular_promedio_general()

    @property
    def nota_minima_aprobatoria(self):
        """
        Retorna la nota mínima requerida según el tipo de materia
        """
        return 16 if self.es_materia_proyecto() else 12

    @property
    def aprobada(self):
        """
        Determina si el alumno aprobó la materia según el tipo
        """
        return self.promedio >= self.nota_minima_aprobatoria if self.notas.exists() else False

    def actualizar_estado(self):
        """
        Método para forzar la actualización del estado
        """
        self.save(update_fields=[])

# 6. Define Nota (que depende de Inscripcion)
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