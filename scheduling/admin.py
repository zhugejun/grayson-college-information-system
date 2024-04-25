from django.contrib import admin
from django import forms
from django.db import models
from django.db.models.functions import Concat

# Register your models here.
from .models import Course, Campus, Dates, Instructor, Location, Term, Schedule, Cams

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
        "is_deleted",
        "deleted_at",
        "deleted_by"
    )
    list_filter = (
        "update_date",
        "update_by",
    )
    search_fields = ["course__subject", "course__number", "section"]
    ordering = ("-update_date",)


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs['widget'] = forms.Select(attrs={
                'style': 'width: 250px;'
            })
            kwargs['queryset'] = Course.objects.annotate(
                display_name=Concat(
                    'subject', models.Value(' '),
                    'number', models.Value(' - '),
                    'name',
                    output_field=models.CharField()
                )
            )
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label_from_instance = lambda obj: getattr(obj, 'display_name', str(obj))
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name")
    ordering = ("last_name",)
    search_fields = ("first_name", "last_name")


admin.site.register(Campus)

admin.site.register(Cams)

admin.site.register(Location)

admin.site.register(Dates)
