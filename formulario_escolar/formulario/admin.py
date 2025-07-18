from django.contrib import admin
from .models import Alumno, Materia, Inscripcion, Nota, Profesor, Periodo

class InscripcionInline(admin.TabularInline):
    model = Inscripcion
    extra = 1

class NotaInline(admin.TabularInline):
    model = Nota
    extra = 1

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'profesor', 'nota_minima_aprobatoria')
    search_fields = ('nombre', 'profesor__user__first_name', 'profesor__user__last_name')
    list_filter = ('profesor',)
    inlines = [InscripcionInline]

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'materia', 'periodo', 'fecha_inscripcion')
    search_fields = ('alumno__nombre', 'alumno__apellido', 'materia__nombre')
    list_filter = ('periodo', 'materia')
    inlines = [NotaInline]

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'tipo', 'valor', 'fecha_registro')
    list_filter = ('tipo', 'fecha_registro')
    search_fields = ('inscripcion__alumno__nombre', 'inscripcion__alumno__apellido')

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('user', 'cedula', 'telefono')
    search_fields = ('user__first_name', 'user__last_name', 'cedula')

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año_actual', 'fecha_inicio', 'fecha_fin')
    list_filter = ('año_actual', 'nombre')
    search_fields = ('nombre',)
    ordering = ('-año_actual', 'nombre')
    readonly_fields = ('fecha_inicio', 'fecha_fin')
    
    def fecha_inicio(self, obj):
        return obj.fecha_inicio.strftime('%d/%m/%Y')
    fecha_inicio.short_description = 'Fecha de Inicio'
    
    def fecha_fin(self, obj):
        return obj.fecha_fin.strftime('%d/%m/%Y')
    fecha_fin.short_description = 'Fecha de Fin'
