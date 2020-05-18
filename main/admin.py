from django.contrib import admin

from .models import Profile, Subject
# Register your models here.

admin.site.register(Subject)
admin.site.register(Profile)
