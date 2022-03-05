from django.contrib import admin

# Register your models here.
from .models import Course, Campus, Instructor, Location, Term, Schedule, Cams

admin.site.register(Term)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('subject', 'number', 'credit', 'name')
    list_filter = ('subject', )
    ordering = ('subject', 'number')
    search_fields = ('subject', 'number')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'section', 'term', 'update_date', 'update_by',)
    list_filter = ('update_date', 'update_by', )
    ordering = ('-update_date',)


admin.site.register(Location)
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')
    ordering = ('last_name',)
    search_fields = ('first_name', 'last_name')


admin.site.register(Campus)

admin.site.register(Cams)
