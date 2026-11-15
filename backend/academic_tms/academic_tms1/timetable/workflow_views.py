from django.db import models
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LeaveRequest, SubstituteRequest, Notification, NotificationRead, TimetableEntry, Teacher
from .serializers import LeaveRequestSerializer, SubstituteRequestSerializer, NotificationSerializer


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def notify_user(user, title, message, category):
    return Notification.objects.create(recipient=user, audience="all", title=title, message=message, category=category)


def notify_role(role, title, message, category):
    return Notification.objects.create(audience=role, title=title, message=message, category=category)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related("faculty", "reviewed_by")
        return qs if is_admin(self.request.user) else qs.filter(faculty=self.request.user)

    def create(self, request, *args, **kwargs):
        if is_admin(request.user):
            return Response({"error": "Only faculty can submit leave requests."}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = request.user.smarttime_profile
        except Exception:
            profile = None
        if not profile or profile.role != "faculty":
            return Response({"error": "Faculty account required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["to_date"] < serializer.validated_data["from_date"]:
            return Response({"error": "End date cannot be before start date."}, status=status.HTTP_400_BAD_REQUEST)
        item = serializer.save(faculty=request.user)
        notify_role("admin", "Faculty leave request", f"{request.user.get_full_name()} requested leave from {item.from_date} to {item.to_date}.", "leave")
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response({"error": "Leave requests cannot be edited after submission."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"error": "Leave requests are retained in the audit history."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        return self._decide(request, "Approved")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        return self._decide(request, "Rejected")

    def _decide(self, request, outcome):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        item = self.get_object()
        if item.status != "Pending":
            return Response({"error": "This leave request has already been reviewed."}, status=status.HTTP_409_CONFLICT)
        item.status = outcome
        item.admin_note = str(request.data.get("admin_note", ""))[:2000]
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save(update_fields=["status", "admin_note", "reviewed_by", "reviewed_at"])
        notify_user(item.faculty, f"Leave request {outcome.lower()}", f"Your leave request from {item.from_date} to {item.to_date} was {outcome.lower()}.", "leave")
        return Response(self.get_serializer(item).data)


class SubstituteRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SubstituteRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = SubstituteRequest.objects.select_related("faculty", "substitute", "reviewed_by")
        if is_admin(self.request.user):
            return qs
        return qs.filter(faculty=self.request.user) | qs.filter(substitute=self.request.user)

    def create(self, request, *args, **kwargs):
        if is_admin(request.user):
            return Response({"error": "Only faculty can submit substitute requests."}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = request.user.smarttime_profile
        except Exception:
            profile = None
        if not profile or profile.role != "faculty":
            return Response({"error": "Faculty account required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if values["end_time"] <= values["start_time"]:
            return Response({"error": "End time must be later than start time."}, status=status.HTTP_400_BAD_REQUEST)
        substitute = values.get("substitute")
        substitute_profile = getattr(substitute, "smarttime_profile", None) if substitute else None
        if not substitute_profile or substitute_profile.role != "faculty":
            return Response({"error": "Choose a registered faculty account as the substitute."}, status=status.HTTP_400_BAD_REQUEST)
        from .models import Teacher
        substitute_teacher = Teacher.objects.filter(email__iexact=substitute.email).first()
        if not substitute_teacher:
            return Response({"error": "The selected faculty account must have a timetable faculty record before availability can be checked."}, status=status.HTTP_400_BAD_REQUEST)
        if substitute_teacher.status != "Active":
            return Response({"error": "Choose an active faculty member as the substitute."}, status=status.HTTP_400_BAD_REQUEST)
        item = serializer.save(faculty=request.user)
        notify_role("admin", "Substitute request", f"{request.user.get_full_name()} requested a substitute for {item.subject} on {item.class_date}.", "substitute")
        if item.substitute_id:
            notify_user(item.substitute, "Substitute request received", f"You were asked to substitute {item.subject} on {item.class_date}.", "substitute")
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response({"error": "Substitute requests cannot be edited after submission."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"error": "Substitute requests are retained in the audit history."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def check_availability(self, request, pk=None):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        item = self.get_object()
        if not item.substitute_id:
            item.availability = "Not Available"
        else:
            profile = getattr(item.substitute, "smarttime_profile", None)
            teacher = None
            if profile:
                teacher = item.substitute  # Teacher calendar is matched by registered faculty account below.
            teacher_row = Teacher.objects.filter(email__iexact=item.substitute.email).first() if teacher else None
            clashes = TimetableEntry.objects.none()
            if teacher_row:
                clashes = TimetableEntry.objects.filter(teacher=teacher_row, day=item.class_date.strftime("%A"), start_time__lt=item.end_time, end_time__gt=item.start_time)
            item.availability = "Available" if teacher_row and teacher_row.status == "Active" and not clashes.exists() else "Not Available"
        item.save(update_fields=["availability"])
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, "Approved")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, "Rejected")

    def _decide(self, request, outcome):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        item = self.get_object()
        if item.status != "Pending":
            return Response({"error": "This substitute request has already been reviewed."}, status=status.HTTP_409_CONFLICT)
        if outcome == "Approved" and item.availability != "Available":
            return Response({"error": "Check substitute availability before approving."}, status=status.HTTP_400_BAD_REQUEST)
        item.status = outcome
        item.admin_note = str(request.data.get("admin_note", ""))[:2000]
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save(update_fields=["status", "admin_note", "reviewed_by", "reviewed_at"])
        notify_user(item.faculty, f"Substitute request {outcome.lower()}", f"Your substitute request for {item.subject} on {item.class_date} was {outcome.lower()}.", "substitute")
        if item.substitute_id:
            notify_user(item.substitute, f"Substitute request {outcome.lower()}", f"The request for you to cover {item.subject} on {item.class_date} was {outcome.lower()}.", "substitute")
        if outcome == "Approved" and item.substitute_id:
            notify_role("student", "Class substitution approved", f"{item.subject} on {item.class_date} ({item.start_time:%H:%M}-{item.end_time:%H:%M}) will be covered by {item.substitute.get_full_name() or item.substitute.email}.", "substitute")
        return Response(self.get_serializer(item).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = "admin" if is_admin(user) else getattr(getattr(user, "smarttime_profile", None), "role", "")
        return Notification.objects.filter(models.Q(recipient=user) | models.Q(recipient__isnull=True, audience__in=[role, "all"])).distinct()

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        item = self.get_object()
        NotificationRead.objects.get_or_create(notification=item, user=request.user)
        return Response({"id": item.pk, "is_read": True})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        items = self.get_queryset()
        NotificationRead.objects.bulk_create([NotificationRead(notification=item, user=request.user) for item in items if not item.read_receipts.filter(user=request.user).exists()], ignore_conflicts=True)
        return Response({"message": "Notifications marked as read."})

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        audience = str(request.data.get("audience", "all"))
        if audience not in {"all", "faculty", "student"}:
            return Response({"error": "Choose a valid notification audience."}, status=status.HTTP_400_BAD_REQUEST)
        title = str(request.data.get("title", "")).strip()
        message = str(request.data.get("message", "")).strip()
        if not title or not message:
            return Response({"error": "A title and message are required."}, status=status.HTTP_400_BAD_REQUEST)
        item = Notification.objects.create(audience=audience, title=title[:200], message=message, category="admin")
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)



class FacultyDirectoryView(APIView):
    permission_classes = [IsAuthenticated]

    def _serialize_profile(self, profile):
        from .models import Teacher
        teacher, _ = Teacher.objects.get_or_create(
            email=profile.user.email,
            defaults={
                "name": profile.user.get_full_name() or profile.user.email,
                "phone": profile.phone,
            },
        )
        return {
            "id": profile.user_id,
            "faculty_id": profile.institutional_id,
            "name": profile.user.get_full_name() or profile.user.email,
            "email": profile.user.email,
            "phone": profile.phone,
            "teacher_id": teacher.pk,
            "department": teacher.department.name if teacher.department_id else "",
            "department_id": teacher.department_id,
            "status": teacher.status,
        }

    def get(self, request, user_id=None):
        from .models import UserProfile
        if not is_admin(request.user) and getattr(getattr(request.user, "smarttime_profile", None), "role", "") != "faculty":
            return Response({"error": "Faculty or administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        if user_id is not None:
            if not is_admin(request.user):
                return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
            try:
                profile = UserProfile.objects.select_related("user").get(user_id=user_id, role="faculty")
            except UserProfile.DoesNotExist:
                return Response({"error": "Registered faculty account not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(self._serialize_profile(profile))
        profiles = UserProfile.objects.filter(role="faculty", user__is_active=True).select_related("user").order_by("user__first_name")
        return Response([self._serialize_profile(profile) for profile in profiles])

    def patch(self, request, user_id):
        from .models import Department, Teacher, UserProfile
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = UserProfile.objects.select_related("user").get(user_id=user_id, role="faculty")
        except UserProfile.DoesNotExist:
            return Response({"error": "Registered faculty account not found."}, status=status.HTTP_404_NOT_FOUND)

        name = str(request.data.get("name", profile.user.get_full_name() or profile.user.email)).strip()
        phone = str(request.data.get("phone", profile.phone)).strip()
        if not name or len(name) > 150:
            return Response({"error": "Enter a name of 1 to 150 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if len(phone) > 20:
            return Response({"error": "Phone number must be 20 characters or fewer."}, status=status.HTTP_400_BAD_REQUEST)

        teacher = Teacher.objects.filter(email__iexact=profile.user.email).first()
        department = None
        if "department" in request.data:
            department_value = str(request.data.get("department", "")).strip()
            if department_value:
                department = Department.objects.filter(name__iexact=department_value).first()
                if department is None:
                    return Response({"error": "Add this department to Department Management before assigning faculty to it."}, status=status.HTTP_400_BAD_REQUEST)
        teacher_status = str(request.data.get("status", teacher.status if teacher else "Active"))
        if teacher_status not in {"Active", "On Leave", "Inactive"}:
            return Response({"error": "Choose a valid faculty status."}, status=status.HTTP_400_BAD_REQUEST)

        profile.user.first_name = name
        profile.user.save(update_fields=["first_name"])
        profile.phone = phone
        profile.save(update_fields=["phone"])
        if teacher is None:
            teacher = Teacher.objects.create(email=profile.user.email, name=name, phone=phone)
        teacher.name = name
        teacher.phone = phone
        teacher.status = teacher_status
        update_fields = ["name", "phone", "status"]
        if "department" in request.data:
            teacher.department = department
            update_fields.append("department")
        teacher.save(update_fields=update_fields)
        profile = UserProfile.objects.select_related("user").get(pk=profile.pk)
        return Response(self._serialize_profile(profile))
