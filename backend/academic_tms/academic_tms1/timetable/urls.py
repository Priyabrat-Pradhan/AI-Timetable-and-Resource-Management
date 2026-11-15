from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views, workflow_views
from . import isolated_views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'semesters', views.AcademicSemesterViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'classrooms', views.ClassroomViewSet)
router.register(r'timetable', views.TimetableEntryViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'leave-requests', workflow_views.LeaveRequestViewSet, basename='leave-request')
router.register(r'substitute-requests', workflow_views.SubstituteRequestViewSet, basename='substitute-request')
router.register(r'notifications', workflow_views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('ai-timetable/catalog/', isolated_views.TimetableCatalogView.as_view(), name='ai-timetable-catalog'),
    path('ai-timetable/subjects/', isolated_views.SchedulingSubjectsView.as_view(), name='ai-timetable-subjects'),
    path('ai-timetable/subjects/<int:subject_id>/', isolated_views.SchedulingSubjectDetailView.as_view(), name='ai-timetable-subject-detail'),
    path('ai-timetable/generate/', isolated_views.GenerateIsolatedTimetableView.as_view(), name='ai-timetable-generate'),
    path('ai-timetable/generate-all/', isolated_views.GenerateAllTimetablesView.as_view(), name='ai-timetable-generate-all'),
    path('ai-timetable/schedule/', isolated_views.StoredTimetableView.as_view(), name='ai-timetable-schedule'),
    path('ai-timetable/save/', isolated_views.SaveIsolatedTimetableView.as_view(), name='ai-timetable-save'),
    path('ai-timetable/published/', isolated_views.PublishedIsolatedTimetablesView.as_view(), name='ai-timetable-published'),
    path('faculty-directory/', workflow_views.FacultyDirectoryView.as_view(), name='faculty-directory'),
    path('faculty-directory/<int:user_id>/', workflow_views.FacultyDirectoryView.as_view(), name='faculty-directory-detail'),
    path('auth/register/', auth_views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', auth_views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='auth-logout'),
    path('auth/student-profile/', auth_views.StudentProfileView.as_view(), name='student-profile'),
    path('admin/students/', auth_views.AdminStudentDirectoryView.as_view(), name='admin-students'),
    path('admin/students/<int:user_id>/', auth_views.AdminStudentDirectoryView.as_view(), name='admin-student-detail'),
    path('auth/change-password/', auth_views.AdminChangePasswordView.as_view(), name='admin-change-password'),
    path('', include(router.urls)),
]
