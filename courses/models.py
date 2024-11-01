# courses/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, null=True, blank=True
    )
    is_hod = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If the user is a superuser and has no department, assign a default department
        if not self.department and self.is_superuser:
            self.department, created = Department.objects.get_or_create(
                name="Default Department"
            )
        super().save(*args, **kwargs)


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    

    def __str__(self):
        return self.user.username


class Hod(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.OneToOneField(
        Department, on_delete=models.CASCADE, unique=True)

    def save(self, *args, **kwargs):
        # Ensure that the user associated with this HOD is marked as HOD
        if not self.user.is_hod:
            raise ValidationError(
                "The user assigned as HOD must have 'is_hod=True'.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.department.name}"


class CourseForm(models.Model):
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    file = models.FileField(upload_to="course_forms/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    stamp = models.FileField(
        upload_to="course_forms/stamped/", null=True, blank=True)

    class Meta:
        verbose_name = "Course Form"
        verbose_name_plural = "Course Forms"


