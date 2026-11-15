from rest_framework import serializers
from .models import Department, AcademicSemester, Teacher, Subject, Classroom, TimetableEntry, Task, LeaveRequest, SubstituteRequest, Notification


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class AcademicSemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSemester
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    scheduled_hours = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = '__all__'

    def get_scheduled_hours(self, obj):
        return obj.timetable_entries.count()  # each entry = 1 hour approx


class SubjectSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    teachers_list = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = '__all__'

    def get_teachers_list(self, obj):
        return [t.name for t in obj.teachers.all()]


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class TimetableEntrySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.first_name", read_only=True)
    faculty_email = serializers.EmailField(source="faculty.email", read_only=True)
    faculty_id = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["faculty", "status", "admin_note", "reviewed_by", "reviewed_at", "created_at"]

    def get_faculty_id(self, obj):
        try:
            return obj.faculty.smarttime_profile.institutional_id
        except Exception:
            return ""


class SubstituteRequestSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.first_name", read_only=True)
    faculty_email = serializers.EmailField(source="faculty.email", read_only=True)
    faculty_id = serializers.SerializerMethodField()
    substitute_name = serializers.CharField(source="substitute.first_name", read_only=True)
    substitute_email = serializers.EmailField(source="substitute.email", read_only=True)

    class Meta:
        model = SubstituteRequest
        fields = "__all__"
        read_only_fields = ["faculty", "availability", "status", "admin_note", "reviewed_by", "reviewed_at", "created_at"]

    def get_faculty_id(self, obj):
        try:
            return obj.faculty.smarttime_profile.institutional_id
        except Exception:
            return ""


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "recipient", "audience", "title", "message", "category", "created_at", "is_read"]
        read_only_fields = fields

    def get_is_read(self, obj):
        user = self.context["request"].user
        return obj.read_receipts.filter(user=user).exists()
