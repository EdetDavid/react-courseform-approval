# courses/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Department, Student, Hod, CourseForm
from .serializers import UserSerializer, DepartmentSerializer, StudentSerializer, HodSerializer, CourseFormSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser
from reportlab.lib.utils import ImageReader



from django.core.files import File
from PIL import Image
from io import BytesIO


from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.files.base import ContentFile


from django.conf import settings
import os


# class RegisterView(APIView):


class RegisterView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        department_name = data.get('department')

        if not department_name:
            return Response({'error': 'Department is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create the department
            department, _ = Department.objects.get_or_create(
                name=department_name)
            data['department_id'] = department.id

            # Create user
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                user = serializer.save()

                # Set password
                user.set_password(data['password'])
                user.save()

                # Create Hod or Student based on is_hod field
                if data.get('is_hod', False):
                    Hod.objects.get_or_create(user=user, department=department)
                else:
                    Student.objects.get_or_create(user=user)

                # Assign a token
                refresh = RefreshToken.for_user(user)

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            return Response({'error': 'User with this username or email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        department_name = request.data.get('department')

        if department_name:
            department, created = Department.objects.get_or_create(
                name=department_name)
            request.data['department'] = department.id

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()  # Create a mutable copy of request data

        department_name = data.get('department')
        if department_name:
            try:
                # Fetch or create the department
                department, created = Department.objects.get_or_create(
                    name=department_name)
                data['department'] = department.id
            except Department.DoesNotExist:
                return Response({"detail": "Department not found."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class UpdateProfileView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()  # Make a mutable copy of the request data

        # Handle department update if provided
        department_name = data.get('department')
        if department_name:
            try:
                # Attempt to find the department by name
                department = Department.objects.get(name=department_name)
                data['department_id'] = department.id
            except Department.DoesNotExist:
                return Response({"error": "Department not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and update the user's profile
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentListView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class HodListView(generics.ListCreateAPIView):
    queryset = Hod.objects.all()
    serializer_class = HodSerializer


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class CourseFormListView(generics.ListCreateAPIView):
    queryset = CourseForm.objects.all()
    serializer_class = CourseFormSerializer


class CourseFormDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CourseForm.objects.all()
    serializer_class = CourseFormSerializer
    permission_classes = [AllowAny]


    def get_queryset(self):
        user = self.request.user
        if user.is_hod:
            return CourseForm.objects.filter(student__user__department=user.department)
        return CourseForm.objects.filter(student__user=user)

    def patch(self, request, *args, **kwargs):
        """Handle partial updates for stamping the form."""
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)





class SubmitCourseFormView(generics.CreateAPIView):
    queryset = CourseForm.objects.all()
    serializer_class = CourseFormSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        student_id = self.request.data.get('student')
        file = self.request.FILES.get('file')

        # Validate that the student exists
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise ValidationError(f"Student with ID {student_id} does not exist.")

        serializer.save(student=student, file=file)





class StampCourseFormView(generics.UpdateAPIView):
    queryset = CourseForm.objects.all()
    serializer_class = CourseFormSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def patch(self, request, *args, **kwargs):
        course_form = self.get_object()
        stamp = request.FILES.get('stamp')

        if not stamp:
            return Response({'error': 'No stamp image provided'}, status=400)

        try:
            # Read the original PDF
            pdf_reader = PdfReader(course_form.file.path)
            pdf_writer = PdfWriter()

            # Create a new PDF with the stamp
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Convert the uploaded stamp file to an ImageReader object
            stamp_image = ImageReader(stamp)

            # Draw the stamp image on the new PDF
            can.drawImage(stamp_image, x=310, y=175, width=1*inch, height=1*inch)  # Adjust position and size
            can.showPage()
            can.save()

            # Move to the beginning of the BytesIO buffer
            packet.seek(0)
            new_pdf = PdfReader(packet)

            # Merge the new PDF with the existing PDF
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                if page_num == len(pdf_reader.pages) - 1:  # Add stamp to the last page
                    page.merge_page(new_pdf.pages[0])
                pdf_writer.add_page(page)

            # Save the modified PDF to a buffer
            output = BytesIO()
            pdf_writer.write(output)
            output.seek(0)

            # Save the new stamped PDF to the CourseForm model
            stamped_pdf_name = f"stamped_{course_form.file.name.split('/')[-1]}"
            course_form.stamp.save(stamped_pdf_name, ContentFile(output.read()))
            course_form.save()

            return Response(CourseFormSerializer(course_form).data)

        except Exception as e:
            # Log the error details for debugging
            import traceback
            error_message = str(e)
            traceback_str = traceback.format_exc()
            print(f"Error: {error_message}")
            print(f"Traceback: {traceback_str}")

            return Response({'error': 'An error occurred while stamping the course form.'}, status=500)
        


class StampedCourseFormListView(generics.ListAPIView):
    queryset = CourseForm.objects.filter(stamp__isnull=False)
    serializer_class = CourseFormSerializer
    permission_classes = [AllowAny]
    

    def get_queryset(self):
        user = self.request.user
        if user:
            return self.queryset.filter(student=user.id)
        return CourseForm.objects.none()
    
