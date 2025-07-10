from django.urls import path
from . import views

app_name = 'formulario'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Alumnos
    path('', views.lista_alumnos, name='lista_alumnos'),
    path('registrar/', views.registrar_alumno, name='registrar_alumno'),
    path('editar/<int:id>/', views.editar_alumno, name='editar_alumno'),
    path('eliminar/<int:id>/', views.eliminar_alumno, name='eliminar_alumno'),
    
    # Profesores
    path('profesores/', views.lista_profesores, name='lista_profesores'),
    path('profesores/registrar/', views.registrar_profesor, name='registrar_profesor'),
    
    # Períodos
    path('periodos/', views.lista_periodos, name='lista_periodos'),
    path('periodos/nuevo/', views.crear_periodo, name='crear_periodo'),
    
    # Materias
    path('materias/', views.lista_materias, name='lista_materias'),
    path('materias/nueva/', views.crear_materia, name='crear_materia'),
    path('materias/<int:materia_id>/', views.detalle_materia, name='detalle_materia'),
    path('materias/editar/<int:id>/', views.editar_materia, name='editar_materia'),
    path('materias/eliminar/<int:id>/', views.eliminar_materia, name='eliminar_materia'),
    
    # Inscripciones
    path('alumno/<int:alumno_id>/asignar-materias/', views.asignar_materias, name='asignar_materias'),
    path('inscripcion/<int:inscripcion_id>/eliminar/', views.eliminar_inscripcion, name='eliminar_inscripcion'),
    
    # Notas
    path('inscripcion/<int:inscripcion_id>/registrar-nota/', views.registrar_nota, name='registrar_nota'),
    path('alumno/<int:alumno_id>/notas/', views.lista_notas_alumno, name='lista_notas_alumno'),
    path('nota/<int:nota_id>/eliminar/', views.eliminar_nota, name='eliminar_nota'),
]