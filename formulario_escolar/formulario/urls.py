from django.urls import path
from . import views

app_name = 'formulario'

urlpatterns = [
    path('', views.lista_alumnos, name='lista_alumnos'),
    path('registrar/', views.registrar_alumno, name='registrar_alumno'),
    path('editar/<int:id>/', views.editar_alumno, name='editar_alumno'),
    path('eliminar/<int:id>/', views.eliminar_alumno, name='eliminar_alumno'),
    
    # URLs para materias
    path('materias/nueva/', views.crear_materia, name='crear_materia'),
    path('materias/', views.lista_materias, name='lista_materias'),
    path('alumno/<int:alumno_id>/asignar-materias/', views.asignar_materias_alumno, name='asignar_materias_alumno'),
     path('inscripcion/<int:inscripcion_id>/eliminar/', views.eliminar_inscripcion, name='eliminar_inscripcion'),
    
    # URLs para notas
    path('inscripcion/<int:inscripcion_id>/registrar-nota/', views.registrar_nota, name='registrar_nota'),
    path('alumno/<int:alumno_id>/notas/', views.lista_notas_alumno, name='lista_notas_alumno'),
]