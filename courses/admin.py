# courses/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, CourseForm, Student, Hod

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_hod', 'department')}),
    )
    list_display = ('username', 'email', 'is_hod', 'department')
    list_filter = ('is_hod', 'department')

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class CourseFormAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_file_name', 'uploaded_at')
    search_fields = ('student__username',)
    list_filter = ('uploaded_at',)

    def get_file_name(self, obj):
        return obj.file.name
    get_file_name.short_description = 'File Name'

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
    list_filter = ('user__is_active',)

    def save_model(self, request, obj, form, change):
        # Ensure that if a user is created as a student, they should have a default department
        if not obj.user.department:
            obj.user.department, created = Department.objects.get_or_create(name='Default Department')
        super().save_model(request, obj, form, change)

class HodAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'department__name')
    list_filter = ('department',)

    def save_model(self, request, obj, form, change):
        # Ensure that if a user is created as an HOD, they are assigned correctly
        if not obj.user.is_hod:
            obj.user.is_hod = True
            obj.user.save()
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(CourseForm, CourseFormAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Hod, HodAdmin)
