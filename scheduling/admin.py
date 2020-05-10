from django.contrib import admin

# Register your models here.
from .models import Course, Campus, Instructor, Location, Term, Schedule
from main.models import Subject

admin.site.register(Term)

admin.site.register(Subject)

admin.site.register(Course)
admin.site.register(Location)
admin.site.register(Instructor)
admin.site.register(Campus)

admin.site.register(Schedule)
