from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, StudentListView, HodListView, 
    CourseFormListView, CourseFormDetailView, SubmitCourseFormView, 
    DepartmentListView, UpdateProfileView, StampCourseFormView, 
    StampedCourseFormListView  # Import the new view
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('students/', StudentListView.as_view(), name='students'),
    path('hods/', HodListView.as_view(), name='hods'),
    path('courseforms/', CourseFormListView.as_view(), name='courseforms'),
    path('courseforms/<int:pk>/', CourseFormDetailView.as_view(), name='courseform-detail'),
    path('courseform/', SubmitCourseFormView.as_view(), name='submit-courseform'),
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('courseforms/<int:pk>/stamp/', StampCourseFormView.as_view(), name='stamp-courseform'),
    path('stampedforms/', StampedCourseFormListView.as_view(), name='stamped-courseforms'),  # New URL
]
