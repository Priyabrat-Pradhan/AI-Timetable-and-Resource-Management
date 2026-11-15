from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Teacher, UserProfile

User = get_user_model()


def user_payload(user, role):
    profile = getattr(user, "smarttime_profile", None)
    return {
        "id": user.pk,
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "role": role,
        "phone": profile.phone if profile else "",
        "user_id": profile.institutional_id if profile else "",
        "batch": profile.batch if profile else "",
        "section": profile.section if profile else "",
        "group": profile.student_group if profile else "",
        "course": profile.course if profile else "",
        "year": profile.year if profile else "",
    }


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        role = str(data.get("role", "")).strip().lower()
        phone = str(data.get("phone", "")).strip()
        institutional_id = str(data.get("user_id", "")).strip()
        password = str(data.get("password", ""))

        if not name or len(name) > 150:
            return Response({"error": "Enter a name of 1 to 150 characters."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Enter a valid email address."}, status=status.HTTP_400_BAD_REQUEST)
        if role not in {"faculty", "student"}:
            return Response({"error": "Choose Faculty or Student to register."}, status=status.HTTP_400_BAD_REQUEST)
        if not institutional_id:
            return Response({"error": "Enter your student or faculty ID."}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response({"error": "Password must contain at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            return Response({"error": "This email is already registered."}, status=status.HTTP_409_CONFLICT)
        if UserProfile.objects.filter(role=role, institutional_id__iexact=institutional_id).exists():
            return Response({"error": "This ID is already registered for that role."}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
                UserProfile.objects.create(
                    user=user, role=role, phone=phone, institutional_id=institutional_id
                )
                if role == "faculty":
                    Teacher.objects.get_or_create(
                        email=email,
                        defaults={"name": name, "phone": phone},
                    )
        except Exception:
            return Response(
                {"error": "Registration failed. Ensure database migrations are applied and MySQL is available."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"message": "Account created. You can now log in."}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        requested_role = str(request.data.get("role", "")).strip().lower()
        if not email or not password or requested_role not in {"admin", "faculty", "student"}:
            return Response({"error": "Enter email, password, and role."}, status=status.HTTP_400_BAD_REQUEST)

        account = User.objects.filter(email__iexact=email).first()
        user = authenticate(request, username=account.username, password=password) if account else None
        if not user or not user.is_active:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        profile = getattr(user, "smarttime_profile", None)
        actual_role = profile.role if profile else ("admin" if user.is_staff or user.is_superuser else "")
        if actual_role != requested_role:
            return Response({"error": "This account does not have the selected role."}, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": user_payload(user, actual_role)})


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class StudentProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _profile(self, request):
        profile = getattr(request.user, "smarttime_profile", None)
        return profile if profile and profile.role == "student" else None

    def _payload(self, request, profile):
        return {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "registration_number": profile.institutional_id,
            "phone": profile.phone,
            "batch": profile.batch,
            "section": profile.section,
            "group": profile.student_group,
            "course": profile.course,
            "year": profile.year,
        }

    def get(self, request):
        profile = self._profile(request)
        if profile is None:
            return Response({"error": "Student account required."}, status=status.HTTP_403_FORBIDDEN)
        return Response(self._payload(request, profile))

    def patch(self, request):
        profile = self._profile(request)
        if profile is None:
            return Response({"error": "Student account required."}, status=status.HTTP_403_FORBIDDEN)
        data = request.data
        name = str(data.get("name", request.user.first_name)).strip()
        reg_no = str(data.get("registration_number", profile.institutional_id)).strip()
        if not name or len(name) > 150:
            return Response({"error": "Enter a name of 1 to 150 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if not reg_no or len(reg_no) > 100:
            return Response({"error": "Enter a valid registration number."}, status=status.HTTP_400_BAD_REQUEST)
        if UserProfile.objects.filter(role="student", institutional_id__iexact=reg_no).exclude(pk=profile.pk).exists():
            return Response({"error": "That registration number is already assigned."}, status=status.HTTP_409_CONFLICT)
        limits = {
            "phone": (20, profile.phone), "batch": (100, profile.batch),
            "section": (30, profile.section), "group": (100, profile.student_group),
            "course": (150, profile.course), "year": (30, profile.year),
        }
        values = {}
        for key, (limit, current) in limits.items():
            value = str(data.get(key, current)).strip()
            if len(value) > limit:
                return Response({"error": f"{key.title()} is too long."}, status=status.HTTP_400_BAD_REQUEST)
            values[key] = value
        request.user.first_name = name
        request.user.save(update_fields=["first_name"])
        profile.institutional_id = reg_no
        profile.phone = values["phone"]
        profile.batch = values["batch"]
        profile.section = values["section"]
        profile.student_group = values["group"]
        profile.course = values["course"]
        profile.year = values["year"]
        profile.save(update_fields=["institutional_id", "phone", "batch", "section", "student_group", "course", "year"])
        return Response(self._payload(request, profile))


class AdminStudentDirectoryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _is_admin(self, request):
        return request.user.is_staff or request.user.is_superuser

    def _payload(self, profile):
        user = profile.user
        return {
            "id": user.pk,
            "regd": profile.institutional_id,
            "name": user.get_full_name() or user.email,
            "email": user.email,
            "phone": profile.phone,
            "department": profile.course,
            "year": profile.year.removesuffix(" Year"),
            "batch": profile.batch,
            "section": profile.section,
            "group": profile.student_group,
        }

    def get(self, request):
        if not self._is_admin(request):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        profiles = UserProfile.objects.filter(role="student").select_related("user").order_by("user__last_name", "user__first_name")
        return Response([self._payload(profile) for profile in profiles])

    def patch(self, request, user_id):
        if not self._is_admin(request):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = UserProfile.objects.select_related("user").get(user_id=user_id, role="student")
        except UserProfile.DoesNotExist:
            return Response({"error": "Student account not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        fields = {
            "regd": ("institutional_id", 100), "phone": ("phone", 20),
            "department": ("course", 150), "year": ("year", 30),
            "batch": ("batch", 100), "section": ("section", 30),
            "group": ("student_group", 100),
        }
        for key, (field, max_length) in fields.items():
            if key in data:
                value = str(data[key]).strip()
                if len(value) > max_length:
                    return Response({"error": f"{key.title()} exceeds {max_length} characters."}, status=status.HTTP_400_BAD_REQUEST)
                if key == "year" and value in {"1st", "2nd", "3rd", "4th"}:
                    value = f"{value} Year"
                setattr(profile, field, value)

        if "name" in data:
            name = str(data["name"]).strip()
            if not name or len(name) > 150:
                return Response({"error": "Enter a name of 1 to 150 characters."}, status=status.HTTP_400_BAD_REQUEST)
            profile.user.first_name = name
            profile.user.save(update_fields=["first_name"])

        if "regd" in data and UserProfile.objects.filter(role="student", institutional_id__iexact=profile.institutional_id).exclude(pk=profile.pk).exists():
            return Response({"error": "That registration number is already assigned."}, status=status.HTTP_409_CONFLICT)
        profile.save()
        return Response(self._payload(profile))



class AdminChangePasswordView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)

        current_password = str(request.data.get("current_password", ""))
        new_password = str(request.data.get("new_password", ""))
        confirm_password = str(request.data.get("confirm_password", ""))

        if not request.user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response({"error": "New password must contain at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return Response({"error": "New password and confirmation do not match."}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.check_password(new_password):
            return Response({"error": "Choose a password different from your current password."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user=request.user)
        except ValidationError as exc:
            return Response({"error": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        Token.objects.filter(user=request.user).delete()
        new_token = Token.objects.create(user=request.user)
        return Response({"message": "Password changed successfully.", "token": new_token.key})
