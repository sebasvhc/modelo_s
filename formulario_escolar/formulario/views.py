from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Alumno, Inscripcion, Materia, Nota
from .forms import AlumnoForm, MateriaForm, AsignarMateriasForm, NotaForm, CustomUserCreationForm  
import datetime
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth import login, authenticate, logout
#from django.contrib.auth.forms import UserCreationForm


@login_required
def lista_alumnos(request):
    alumnos = Alumno.objects.all().order_by('-fecha_inscripcion')
    return render(request, 'alumnos/lista.html', {'alumnos': alumnos})

def registrar_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST, request.FILES)
        print("Formulario recibido:", request.POST)  # Debug 1
        if form.is_valid():
            print("Formulario válido, guardando...")  # Debug 2
            try:
                alumno = form.save()
                print("Alumno guardado:", alumno.id)  # Debug 3
                return redirect('formulario:lista_alumnos')
            except Exception as e:
                print("Error al guardar:", str(e))  # Debug 4
                form.add_error(None, f"Error al guardar: {str(e)}")
        else:
            print("Errores en el formulario:", form.errors)  # Debug 5
    else:
        form = AlumnoForm(initial={'fecha_inscripcion': datetime.date.today()})
    
    return render(request, 'alumnos/registrar.html', {'form': form})

# (Las vistas editar y eliminar se mantienen igual que antes)

# Asegúrate de tener estas funciones
def editar_alumno(request, id):
    alumno = get_object_or_404(Alumno, id=id)
    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            return redirect('formulario:lista_alumnos')  # Asegúrate del namespace
    else:
        form = AlumnoForm(instance=alumno)
    return render(request, 'alumnos/editar.html', {'form': form})

def eliminar_alumno(request, id):
    alumno = get_object_or_404(Alumno, id=id)
    if request.method == 'POST':
        alumno.delete()
        return redirect('formulario:lista_alumnos')  # Namespace aquí también
    return render(request, 'alumnos/confirmar_eliminar.html', {'alumno': alumno})


#----------------------------------------------

def asignar_materias(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    
    # Obtener materias ya asignadas (para mostrar en template)
    materias_asignadas = Inscripcion.objects.filter(alumno=alumno).select_related('materia')
    
    if request.method == 'POST':
        form = AsignarMateriasForm(request.POST, alumno=alumno)
        if form.is_valid():
            try:
                materias = form.cleaned_data['materias']
                ciclo = form.cleaned_data['ciclo_escolar']
                
                # Crear inscripciones
                inscripciones = [
                    Inscripcion(
                        alumno=alumno,
                        materia=materia,
                        ciclo_escolar=ciclo
                    ) for materia in materias
                ]
                Inscripcion.objects.bulk_create(inscripciones)
                
                messages.success(request, 'Materias asignadas correctamente')
                return redirect('formulario:asignar_materias', alumno_id=alumno.id)
                
            except Exception as e:
                messages.error(request, f'Error al asignar materias: {str(e)}')
    else:
        form = AsignarMateriasForm(alumno=alumno)
    
    return render(request, 'formulario/asignar_materias.html', {
        'form': form,
        'alumno': alumno,
        'materias_asignadas': materias_asignadas,
        'materias_disponibles': Materia.objects.exclude(
            id__in=Inscripcion.objects.filter(alumno=alumno).values_list('materia_id', flat=True)
        )
    })


#----------------------------------

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



def crear_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            try:
                nueva_materia = form.save()
                messages.success(request, f'Materia "{nueva_materia.nombre}" creada exitosamente!')
                return redirect('formulario:lista_materias')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = MateriaForm()
    
    return render(request, 'formulario/crear_materia.html', {'form': form})


def lista_materias(request):
    try:
        materias = Materia.objects.all().order_by('nombre')
        context = {
            'materias': materias,
            'titulo': 'Listado de Materias'
        }
        return render(request, 'formulario/lista_materias.html', context)
    except Exception as e:
        # Manejo de errores para desarrollo
        print(f"Error: {str(e)}")
        return render(request, 'formulario/error.html', {'error': str(e)})


def asignar_materias_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    
    if request.method == 'POST':
        ciclo_escolar = request.POST.get('ciclo_escolar')
        materias_seleccionadas = request.POST.getlist('materias')
        
        if not ciclo_escolar:
            messages.error(request, 'Debe seleccionar un ciclo escolar')
        elif not materias_seleccionadas:
            messages.error(request, 'Debe seleccionar al menos una materia')
        else:
            try:
                # Crear las inscripciones
                inscripciones = []
                for materia_id in materias_seleccionadas:
                    # Verificar que no exista ya la asignación
                    if not Inscripcion.objects.filter(
                        alumno=alumno,
                        materia_id=materia_id,
                        ciclo_escolar=ciclo_escolar
                    ).exists():
                        inscripciones.append(
                            Inscripcion(
                                alumno=alumno,
                                materia_id=materia_id,
                                ciclo_escolar=ciclo_escolar
                            )
                        )
                
                if inscripciones:
                    Inscripcion.objects.bulk_create(inscripciones)
                    messages.success(request, f'{len(inscripciones)} materias asignadas correctamente')
                else:
                    messages.warning(request, 'Todas las materias seleccionadas ya estaban asignadas')
                
                return redirect('formulario:asignar_materias_alumno', alumno_id=alumno.id)
                
            except Exception as e:
                messages.error(request, f'Error al asignar materias: {str(e)}')
    
    # Obtener materias asignadas (para mostrar)
    materias_asignadas = Inscripcion.objects.filter(alumno=alumno).select_related('materia')
    
    # Obtener materias disponibles (no asignadas en ningún ciclo)
    materias_asignadas_ids = materias_asignadas.values_list('materia_id', flat=True)
    materias_disponibles = Materia.objects.exclude(id__in=materias_asignadas_ids)
    
    return render(request, 'formulario/asignar_materias.html', {
        'alumno': alumno,
        'materias_asignadas': materias_asignadas,
        'materias_disponibles': materias_disponibles,
    })

def lista_notas_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    inscripciones = Inscripcion.objects.filter(alumno=alumno).prefetch_related('notas')
    return render(request, 'formulario/lista_notas.html', {
        'alumno': alumno,
        'inscripciones': inscripciones
    })

#@permission_required('formulario.delete_nota')
@require_POST  # Asegura que solo se acepten peticiones POST
def eliminar_nota(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    alumno_id = nota.inscripcion.alumno.id  # Para redirigir al perfil del alumno
    nota.delete()
    messages.success(request, 'Nota eliminada correctamente.')
    return redirect('formulario:lista_notas_alumno', alumno_id=alumno_id)


def eliminar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    alumno_id = inscripcion.alumno.id
    inscripcion.delete()
    messages.success(request, 'Asignación eliminada')
    return redirect('formulario:asignar_materias_alumno', alumno_id=alumno_id)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        print("Formulario recibido:", request.POST)  # Debug 1
        if form.is_valid():
            print("Formulario válido")  # Debug 2
            user = form.save()
            print("Usuario guardado:", user.username)  # Debug 3
            login(request, user)
            return redirect('formulario:lista_alumnos')
        else:
            print("Errores en el formulario:", form.errors)  # Debug 4
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})



def login_view(request):  # Si tienes una vista personalizada
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print(f"Usuario autenticado: {user}")  # Ver en consola
        if user is not None:
            login(request, user)
            return redirect('home')


def custom_logout(request):
    logout(request)
    return redirect('login')  # Redirige a donde prefieras