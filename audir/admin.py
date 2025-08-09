from django.contrib import admin
from audir.models import Project, Image, Result, User
from django.contrib.auth.admin import UserAdmin


admin.site.register(Project)
admin.site.register(User, UserAdmin)

admin.site.register(Image)
admin.site.register(Result)