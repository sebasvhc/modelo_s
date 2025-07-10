from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
from .models import Alumno, Inscripcion, Materia, Nota, Periodo, Profesor
from .forms import (
    AlumnoForm, MateriaForm, AsignarMateriasForm, NotaForm,
    CustomUserCreationForm, ProfesorForm, PeriodoForm
)
import datetime
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User

# Vistas para Alumnos
@login_required
def lista_alumnos(request):
    query = request.GET.get('q')
    alumnos = Alumno.objects.all().order_by('apellido', 'nombre')
    
    if query:
        alumnos = alumnos.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(matricula__icontains=query)
        ).distinct()
    
    return render(request, 'alumnos/lista.html', {'alumnos': alumnos})

@login_required
def registrar_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                alumno = form.save()
                messages.success(request, 'Alumno registrado exitosamente')
                return redirect('formulario:lista_alumnos')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
    else:
        form = AlumnoForm(initial={'fecha_inscripcion': datetime.date.today()})
    
    return render(request, 'alumnos/registrar.html', {'form': form})

@login_required
def editar_alumno(request, id):
    alumno = get_object_or_404(Alumno, id=id)
    if request.method == 'POST':
        form = AlumnoForm(request.POST, request.FILES, instance=alumno)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alumno actualizado correctamente')
            return redirect('formulario:lista_alumnos')
    else:
        form = AlumnoForm(instance=alumno)
    return render(request, 'alumnos/editar.html', {'form': form})

@login_required
@require_POST
def eliminar_alumno(request, id):
    alumno = get_object_or_404(Alumno, id=id)
    try:
        alumno.delete()
        messages.success(request, 'Alumno eliminado correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar alumno: {str(e)}')
    return redirect('formulario:lista_alumnos')

# Vistas para Profesores
@login_required
def lista_profesores(request):
    profesores = Profesor.objects.all().order_by('user__last_name', 'user__first_name')
    return render(request, 'formulario/lista_profesores.html', {'profesores': profesores})

@login_required
@permission_required('formulario.add_profesor')
def registrar_profesor(request):
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        if form.is_valid():
            try:
                profesor = form.save()
                messages.success(request, 'Profesor registrado exitosamente')
                return redirect('formulario:lista_profesores')
            except Exception as e:
                messages.error(request, f'Error al registrar profesor: {str(e)}')
    else:
        form = ProfesorForm()
    
    return render(request, 'formulario/registrar_profesor.html', {'form': form})

# Vistas para Períodos
@login_required
def lista_periodos(request):
    periodos = Periodo.objects.all().order_by('-año', 'nombre')
    return render(request, 'formulario/lista_periodos.html', {'periodos': periodos})

@login_required
@permission_required('formulario.add_periodo')
def crear_periodo(request):
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            try:
                periodo = form.save()
                messages.success(request, 'Período creado exitosamente')
                return redirect('formulario:lista_periodos')
            except Exception as e:
                messages.error(request, f'Error al crear período: {str(e)}')
    else:
        form = PeriodoForm()
    
    return render(request, 'formulario/crear_periodo.html', {'form': form})

# Vistas para Materias
@login_required
def lista_materias(request):
    materias = Materia.objects.all().order_by('nombre')
    return render(request, 'formulario/lista_materias.html', {'materias': materias})

@login_required
def crear_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            try:
                materia = form.save()
                messages.success(request, 'Materia creada exitosamente')
                return redirect('formulario:lista_materias')
            except Exception as e:
                messages.error(request, f'Error al crear materia: {str(e)}')
    else:
        form = MateriaForm()
    
    return render(request, 'formulario/crear_materia.html', {'form': form})

@login_required
def detalle_materia(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)
    inscripciones = Inscripcion.objects.filter(materia=materia).select_related('alumno', 'periodo')
    
    return render(request, 'formulario/detalle_materia.html', {
        'materia': materia,
        'inscripciones': inscripciones,
        'profesor': materia.profesor
    })

@login_required
def editar_materia(request, id):
    materia = get_object_or_404(Materia, id=id)
    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada correctamente')
            return redirect('formulario:lista_materias')
    else:
        form = MateriaForm(instance=materia)
    return render(request, 'formulario/editar_materia.html', {'form': form})

@login_required
@require_POST
def eliminar_materia(request, id):
    materia = get_object_or_404(Materia, id=id)
    try:
        materia.delete()
        messages.success(request, 'Materia eliminada correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar materia: {str(e)}')
    return redirect('formulario:lista_materias')

# Vistas para Inscripciones y Notas
@login_required
def asignar_materias(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    materias_asignadas = Inscripcion.objects.filter(alumno=alumno).select_related('materia', 'periodo')
    
    if request.method == 'POST':
        form = AsignarMateriasForm(request.POST, alumno=alumno)
        if form.is_valid():
            periodo = form.cleaned_data['periodo']
            materias = form.cleaned_data['materias']
            
            inscripciones = [
                Inscripcion(
                    alumno=alumno,
                    materia=materia,
                    periodo=periodo
                ) for materia in materias
                if not Inscripcion.objects.filter(
                    alumno=alumno,
                    materia=materia,
                    periodo=periodo
                ).exists()
            ]
            
            if inscripciones:
                Inscripcion.objects.bulk_create(inscripciones)
                messages.success(request, f'{len(inscripciones)} materias asignadas correctamente')
            else:
                messages.warning(request, 'Todas las materias seleccionadas ya estaban asignadas para este período')
            
            return redirect('formulario:asignar_materias', alumno_id=alumno.id)
    else:
        form = AsignarMateriasForm(alumno=alumno)
    
    return render(request, 'formulario/asignar_materias.html', {
        'form': form,
        'alumno': alumno,
        'materias_asignadas': materias_asignadas,
    })

@login_required
@require_POST
def eliminar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    alumno_id = inscripcion.alumno.id
    try:
        inscripcion.delete()
        messages.success(request, 'Inscripción eliminada correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar inscripción: {str(e)}')
    return redirect('formulario:asignar_materias', alumno_id=alumno_id)

@login_required
def registrar_nota(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    
    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.inscripcion = inscripcion
            nota.save()
            messages.success(request, 'Nota registrada correctamente')
            return redirect('formulario:lista_notas_alumno', alumno_id=inscripcion.alumno.id)
    else:
        form = NotaForm()
    
    return render(request, 'formulario/registrar_nota.html', {
        'form': form,
        'inscripcion': inscripcion,
        'alumno': inscripcion.alumno,
        'materia': inscripcion.materia
    })

@login_required
def lista_notas_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    inscripciones = Inscripcion.objects.filter(alumno=alumno).select_related('materia', 'periodo').prefetch_related('notas')
    
    return render(request, 'formulario/lista_notas.html', {
        'alumno': alumno,
        'inscripciones': inscripciones
    })

@login_required
@require_POST
def eliminar_nota(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    alumno_id = nota.inscripcion.alumno.id
    try:
        nota.delete()
        messages.success(request, 'Nota eliminada correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar nota: {str(e)}')
    return redirect('formulario:lista_notas_alumno', alumno_id=alumno_id)

# Vistas de Autenticación
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('formulario:lista_alumnos')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('formulario:lista_alumnos')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'registration/login.html')

@login_required
def custom_logout(request):
    logout(request)
    return redirect('formulario:login_view')