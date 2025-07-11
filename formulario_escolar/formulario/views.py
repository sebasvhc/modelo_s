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
    profesores = Profesor.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    return render(request, 'formulario/lista_profesores.html', {
        'profesores': profesores,
        'profesores_sin_usuario': Profesor.objects.filter(user__isnull=True).count()
    })

@login_required
def registrar_profesor(request):
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        if form.is_valid():
            try:
                profesor = form.save()
                messages.success(request, 
                    f'Profesor {profesor.nombre_completo} registrado exitosamente!',
                    extra_tags='success'
                )
                return redirect('formulario:lista_profesores')
            except Exception as e:
                messages.error(request, 
                    f'Error al registrar profesor: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(request, 
                'Por favor corrige los errores en el formulario',
                extra_tags='warning'
            )
    else:
        form = ProfesorForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Profesor',
        'active_tab': 'profesores'
    }
    return render(request, 'formulario/registrar_profesor.html', context)

@login_required
def editar_profesor(request, id):
    profesor = get_object_or_404(Profesor, id=id)
    
    if not hasattr(profesor, 'user'):
        # Crear usuario si no existe
        username = profesor.cedula
        user = User.objects.create_user(
            username=username,
            password=username,
            first_name="Nombre",
            last_name="Apellido",
            email=f"{username}@escuela.com"
        )
        profesor.user = user
        profesor.save()
        messages.warning(request, 'Se creó un usuario automático para este profesor. Por favor complete los datos correctamente.')
    
    if request.method == 'POST':
        form = ProfesorForm(request.POST, instance=profesor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor actualizado correctamente')
            return redirect('formulario:lista_profesores')
    else:
        form = ProfesorForm(instance=profesor)
    
    return render(request, 'formulario/editar_profesor.html', {
        'form': form,
        'titulo': 'Editar Profesor'
    })

@login_required
@require_POST
def eliminar_profesor(request, id):
    profesor = get_object_or_404(Profesor, id=id)
    profesor.delete()
    messages.success(request, 'Profesor eliminado correctamente')
    return redirect('formulario:lista_profesores')
    

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
    profesores = Profesor.objects.all().order_by('user__last_name')
    
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            materia = form.save()
            messages.success(request, 'Materia creada exitosamente')
            return redirect('formulario:lista_materias')
    else:
        form = MateriaForm()
    
    return render(request, 'formulario/crear_materia.html', {
        'form': form,
        'profesores': profesores
    })

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
    periodos = Periodo.obtener_periodos_actuales()
    
    if request.method == 'POST':
        # Manejo simplificado del período
        periodo_id = request.POST.get('periodo')
        try:
            periodo = next(p for p in periodos if str(p.id) == periodo_id)
        except (StopIteration, ValueError):
            messages.error(request, "Seleccione un período válido")
            return redirect('formulario:asignar_materias', alumno_id=alumno.id)
        
        # Procesar materias seleccionadas
        materias_ids = request.POST.getlist('materias')
        materias = Materia.objects.filter(id__in=materias_ids)
        
        # Crear inscripciones
        for materia in materias:
            Inscripcion.objects.get_or_create(
                alumno=alumno,
                materia=materia,
                periodo=periodo
            )
        
        messages.success(request, 'Materias asignadas correctamente')
        return redirect('formulario:asignar_materias', alumno_id=alumno.id)
    
    # Obtener materias no asignadas en ningún período
    materias_asignadas_ids = Inscripcion.objects.filter(
        alumno=alumno
    ).values_list('materia_id', flat=True)
    
    materias_disponibles = Materia.objects.exclude(
        id__in=materias_asignadas_ids
    ).order_by('nombre')
    
    materias_asignadas = Inscripcion.objects.filter(
        alumno=alumno
    ).select_related('materia', 'periodo')
    
    return render(request, 'formulario/asignar_materias.html', {
        'alumno': alumno,
        'periodos': periodos,
        'materias_disponibles': materias_disponibles,
        'materias_asignadas': materias_asignadas,
        'periodo_actual': periodos[0]  # Periodo I por defecto
    })


@login_required
def lista_notas_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    inscripciones = Inscripcion.objects.filter(alumno=alumno).select_related('materia', 'periodo').prefetch_related('notas')
    
    # Preparamos datos adicionales para cada inscripción
    for inscripcion in inscripciones:
        inscripcion.datos_extra = {
            'es_proyecto': inscripcion.es_materia_proyecto(),
            'nota_minima': inscripcion.nota_minima_aprobatoria,
            'estado_aprobacion': inscripcion.aprobada
        }
    
    return render(request, 'formulario/lista_notas.html', {
        'alumno': alumno,
        'inscripciones': inscripciones
    })

@login_required
def registrar_nota(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    es_proyecto = inscripcion.es_materia_proyecto()
    alumno = inscripcion.alumno
    
    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.inscripcion = inscripcion
            nota.save()
            
            # Actualizar estado de aprobación
            inscripcion.actualizar_estado()
            
            messages.success(request, 'Nota registrada correctamente')
            return redirect('formulario:lista_notas_alumno', alumno_id=inscripcion.alumno.id)
    else:
        form = NotaForm()
    
    return render(request, 'formulario/registrar_nota.html', {
        'form': form,
        'inscripcion': inscripcion,
        'es_proyecto': es_proyecto,
        'nota_minima': 16 if es_proyecto else 12
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

def buscar_profesor(request):
    query = request.GET.get('q', '')
    
    # Buscar por nombre o apellido (insensible a mayúsculas)
    profesores = Profesor.objects.filter(
        Q(user__first_name__icontains=query) | 
        Q(user__last_name__icontains=query)
    ).distinct()[:10]
    
    results = []
    for profesor in profesores:
        results.append({
            'id': profesor.user.get_full_name(),  # Usamos el nombre completo como ID
            'text': f"{profesor.user.get_full_name()} (C.I.: {profesor.cedula})"
        })
    
    return JsonResponse({'results': results}, safe=False)