from django.contrib import admin

# Register your models here.
from .models import Course, Campus, Instructor, Location, Term, Schedule

admin.site.register(Term)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('subject', 'number', 'credit', 'name')
    list_filter = ('subject', )
    ordering = ('subject', 'number')


admin.site.register(Location)
admin.site.register(Instructor)
admin.site.register(Campus)

admin.site.register(Schedule)
