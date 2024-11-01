# src/serializers.py
from rest_framework import serializers
from rest_framework import generics, permissions
from .models import User, Department, Student, Hod, CourseForm


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password',
                  'department', 'department_id', 'is_hod']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # Handle password update
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Update the department if present
        department = validated_data.pop('department', None)
        if department:
            instance.department = department

        instance = super().update(instance, validated_data)
        instance.save()
        return instance


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student


class HodSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Hod
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        department_data = validated_data.pop('department')

        department, created = Department.objects.get_or_create(
            **department_data)
        user = User.objects.create_user(
            **user_data, department=department, is_hod=True)
        hod = Hod.objects.create(
            user=user, department=department, **validated_data)
        return hod


class CourseFormSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()

    class Meta:
        model = CourseForm
        fields = ['id', 'student', 'file', 'uploaded_at', 'stamp']

    def get_student(self, obj):
        return UserSerializer(obj.student.user).data
