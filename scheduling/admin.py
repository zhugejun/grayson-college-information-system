from django.contrib import admin

# Register your models here.
from .models import Course, Campus, Instructor, Location, Term, Schedule, Cams

admin.site.register(Term)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("__str__", "credit", "name")
    list_filter = ("subject",)
    ordering = ("subject", "number")
    search_fields = ("subject", "number")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "term",
        "insert_date",
        "insert_by",
        "update_date",
        "update_by",
    )
    list_filter = (
        "update_date",
        "update_by",
    )
    search_fields = ["course__subject", "course__number", "section"]
    ordering = ("-update_date",)


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name")
    ordering = ("last_name",)
    search_fields = ("first_name", "last_name")


admin.site.register(Campus)

admin.site.register(Cams)

admin.site.register(Location)
