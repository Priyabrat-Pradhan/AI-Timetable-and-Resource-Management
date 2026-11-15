from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.db import transaction
from .models import Department, AcademicSemester, Teacher, Subject, Classroom, TimetableEntry, Task
from .serializers import (
    DepartmentSerializer, AcademicSemesterSerializer, TeacherSerializer,
    SubjectSerializer, ClassroomSerializer, TimetableEntrySerializer, TaskSerializer
)
from . import ai_services


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class AcademicSemesterViewSet(viewsets.ModelViewSet):
    queryset = AcademicSemester.objects.all()
    serializer_class = AcademicSemesterSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related('department').all()
    serializer_class = TeacherSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        status_ = self.request.query_params.get('status')
        if dept:
            qs = qs.filter(department__id=dept)
        if status_:
            qs = qs.filter(status=status_)
        return qs

    @action(detail=False, methods=['get'])
    def availability_gaps(self, request):
        """AI: Find teachers with scheduling gaps."""
        teachers_data = []
        for t in Teacher.objects.filter(status='Active'):
            teachers_data.append({
                'name': t.name,
                'available_days': t.available_days,
                'max_weekly_hours': t.max_weekly_hours,
                'scheduled_hours': t.timetable_entries.count()
            })
        result = ai_services.get_availability_gaps(teachers_data, [])
        return Response(result)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.select_related('department', 'semester').prefetch_related('teachers').all()
    serializer_class = SubjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        year = self.request.query_params.get('year')
        semester = self.request.query_params.get('semester')
        if dept:
            qs = qs.filter(department__id=dept)
        if year:
            qs = qs.filter(year=year)
        if semester:
            qs = qs.filter(semester__id=semester)
        return qs


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        room_type = self.request.query_params.get('room_type')
        avail = self.request.query_params.get('availability')
        if room_type:
            qs = qs.filter(room_type=room_type)
        if avail:
            qs = qs.filter(availability=avail)
        return qs


class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.select_related('subject', 'teacher', 'room', 'semester').all()
    serializer_class = TimetableEntrySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not (user.is_staff or user.is_superuser):
            profile = getattr(user, 'smarttime_profile', None)
            if profile and profile.role == 'faculty':
                qs = qs.filter(teacher__email__iexact=user.email)
            elif profile and profile.role == 'student':
                if profile.year:
                    qs = qs.filter(year=profile.year)
                if profile.section:
                    qs = qs.filter(Q(batch_section__icontains=profile.section) | Q(batch_section__exact=''))
                if profile.course:
                    qs = qs.filter(Q(subject__department__name__icontains=profile.course) | Q(subject__department__code__icontains=profile.course))
                if not (profile.year or profile.section or profile.course):
                    return qs.none()
            else:
                return qs.none()
        semester = self.request.query_params.get('semester')
        day = self.request.query_params.get('day')
        teacher = self.request.query_params.get('teacher')
        year = self.request.query_params.get('year')
        if semester:
            qs = qs.filter(semester__id=semester)
        if day:
            qs = qs.filter(day=day)
        if teacher:
            qs = qs.filter(teacher__id=teacher)
        if year:
            qs = qs.filter(year=year)
        return qs

    def _publish_timetable_change(self, entry, created):
        from .models import Notification
        verb = 'published' if created else 'updated'
        message = f"{entry.subject.name} was {verb}: {entry.day} {entry.start_time.strftime('%H:%M')}-{entry.end_time.strftime('%H:%M')}, {entry.room.room_number}."
        Notification.objects.create(audience='faculty', title='Timetable update', message=message, category='timetable')
        Notification.objects.create(audience='student', title='Timetable update', message=message, category='timetable')

    def perform_create(self, serializer):
        entry = serializer.save()
        self._publish_timetable_change(entry, True)

    def perform_update(self, serializer):
        entry = serializer.save()
        self._publish_timetable_change(entry, False)

    def perform_destroy(self, instance):
        from .models import Notification
        message = f"{instance.subject.name} on {instance.day} at {instance.start_time.strftime('%H:%M')} was removed from the timetable."
        Notification.objects.create(audience='faculty', title='Timetable change', message=message, category='timetable')
        Notification.objects.create(audience='student', title='Timetable change', message=message, category='timetable')
        instance.delete()

    @action(detail=False, methods=['post'], url_path='publish')
    def publish(self, request):
        user = request.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            return Response({'error': 'Administrator account required.'}, status=status.HTTP_403_FORBIDDEN)
        rows = request.data.get('entries')
        if not isinstance(rows, list) or not rows:
            return Response({'error': 'Provide at least one timetable entry.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=rows, many=True)
        serializer.is_valid(raise_exception=True)
        saved = []
        with transaction.atomic():
            for values in serializer.validated_data:
                entry, created = TimetableEntry.objects.update_or_create(
                    semester=values['semester'], subject=values['subject'], day=values['day'],
                    start_time=values['start_time'], batch_section=values.get('batch_section', ''),
                    defaults={key: value for key, value in values.items() if key not in {'semester', 'subject', 'day', 'start_time', 'batch_section'}},
                )
                self._publish_timetable_change(entry, created)
                saved.append(entry)
        return Response(self.get_serializer(saved, many=True).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def substitute_availability(self, request):
        user = request.user
        profile = getattr(user, 'smarttime_profile', None)
        if not (user.is_staff or user.is_superuser or (profile and profile.role == 'faculty')):
            return Response({'error': 'Faculty or administrator account required.'}, status=status.HTTP_403_FORBIDDEN)
        teacher_id = request.query_params.get('teacher_id')
        class_date = request.query_params.get('date')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        if not all([teacher_id, class_date, start_time, end_time]):
            return Response({'error': 'teacher_id, date, start_time, and end_time are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except (Teacher.DoesNotExist, ValueError):
            return Response({'available': False, 'error': 'This faculty account is not linked to a timetable teacher record.'}, status=status.HTTP_404_NOT_FOUND)
        if teacher.status != 'Active':
            return Response({'available': False, 'conflict_count': 0, 'error': 'This faculty member is not marked Active by the administrator.'})
        clashes = TimetableEntry.objects.filter(
            teacher=teacher, day=__import__('datetime').date.fromisoformat(class_date).strftime('%A'),
            start_time__lt=end_time, end_time__gt=start_time,
        )
        return Response({'available': not clashes.exists(), 'conflict_count': clashes.count()})

    @action(detail=False, methods=['get'])
    def detect_conflicts(self, request):
        """AI: Detect teacher & room conflicts in current timetable."""
        semester_id = request.query_params.get('semester')
        entries = self.get_queryset()
        if semester_id:
            entries = entries.filter(semester__id=semester_id)

        data = [{
            'day': e.day,
            'start_time': str(e.start_time),
            'end_time': str(e.end_time),
            'subject_name': e.subject.name,
            'teacher_name': e.teacher.name,
            'room_number': e.room.room_number,
        } for e in entries]

        result = ai_services.detect_conflicts(data)

        # Auto-tag entries with conflict status
        for conflict in result.get('conflicts', []):
            conflict_type = conflict.get('type', 'Needs Review')
            for desc in conflict.get('affected_entries', []):
                entries_to_update = entries.filter(
                    Q(teacher__name__icontains=desc) | Q(room__room_number__icontains=desc)
                )
                entries_to_update.update(conflict_status=conflict_type)

        return Response(result)

    @action(detail=False, methods=['post'])
    def generate_ai_timetable(self, request):
        """AI: Generate a conflict-free timetable for a semester."""
        semester_id = request.data.get('semester_id')
        if not semester_id:
            return Response({'error': 'semester_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            semester = AcademicSemester.objects.get(id=semester_id)
        except AcademicSemester.DoesNotExist:
            return Response({'error': 'Semester not found'}, status=status.HTTP_404_NOT_FOUND)

        subjects = Subject.objects.filter(semester=semester, status='Active').prefetch_related('teachers')
        teachers = Teacher.objects.filter(status='Active')
        rooms = Classroom.objects.filter(availability='Available')

        subjects_data = [{
            'name': s.name, 'code': s.code,
            'weekly_hours': s.weekly_hours,
            'room_requirement': s.room_requirement,
            'teachers': ', '.join([t.name for t in s.teachers.all()])
        } for s in subjects]

        teachers_data = [{
            'name': t.name,
            'available_days': t.available_days,
            'max_weekly_hours': t.max_weekly_hours
        } for t in teachers]

        rooms_data = [{
            'room_number': r.room_number,
            'room_type': r.room_type,
            'capacity': r.capacity
        } for r in rooms]

        suggestions = ai_services.generate_timetable_suggestions(
            subjects_data, teachers_data, rooms_data, semester.name
        )
        return Response({'semester': semester.name, 'suggested_schedule': suggestions})


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('subject', 'semester').all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        semester = self.request.query_params.get('semester')
        status_ = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        if semester:
            qs = qs.filter(semester__id=semester)
        if status_:
            qs = qs.filter(status=status_)
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    @action(detail=False, methods=['get'])
    def progress_report(self, request):
        """AI: Generate an academic progress summary."""
        semester_id = request.query_params.get('semester')
        qs = self.get_queryset()
        if semester_id:
            qs = qs.filter(semester__id=semester_id)
            semester_name = AcademicSemester.objects.get(id=semester_id).name
        else:
            semester_name = 'All Semesters'

        tasks_data = [{
            'title': t.title,
            'subject': t.subject.name if t.subject else 'N/A',
            'status': t.status,
            'due_date': str(t.due_date) if t.due_date else 'N/A',
            'marks_scored': t.marks_scored,
            'max_marks': t.max_marks
        } for t in qs]

        result = ai_services.generate_progress_report(tasks_data, semester_name)
        return Response(result)
