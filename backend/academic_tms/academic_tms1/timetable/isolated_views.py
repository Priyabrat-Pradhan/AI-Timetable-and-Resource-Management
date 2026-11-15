from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import sqlite3

from .isolated_timetable import archive_subject, catalog, generate, generate_all, list_subjects, load_schedule, published_for_user, save, save_draft, save_subject


def is_admin(user):
    if user.is_staff or user.is_superuser:
        return True
    try:
        return user.smarttime_profile.role == "admin"
    except Exception:
        return False


class TimetableCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        department = request.query_params.get("department", "Computer Science and Engineering")
        year = request.query_params.get("year", "3rd Year")
        semester = request.query_params.get("semester", "5th Semester")
        return Response({"subjects": catalog(department, year, semester), "database": "isolated SQLite timetable store"})


class SchedulingSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        return Response(list_subjects())

    def post(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        try:
            return Response(save_subject(request.data), status=status.HTTP_201_CREATED)
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except sqlite3.IntegrityError as error:
            return Response({"error": f"Subject, faculty, or room record conflicts with saved data: {error}"}, status=status.HTTP_409_CONFLICT)


class SchedulingSubjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, subject_id):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        try:
            return Response(save_subject(request.data, subject_id))
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except sqlite3.IntegrityError as error:
            return Response({"error": f"Subject, faculty, or room record conflicts with saved data: {error}"}, status=status.HTTP_409_CONFLICT)

    def delete(self, request, subject_id):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        if not archive_subject(subject_id):
            return Response({"error": "Subject record not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateIsolatedTimetableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        values = [request.data.get(key) for key in ("department", "year", "semester")]
        if not all(values):
            return Response({"error": "department, year, and semester are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            schedule = generate(*values)
            schedule["recordId"] = save_draft(schedule)
            schedule["status"] = "Draft"
            return Response(schedule)
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class GenerateAllTimetablesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        try:
            schedules = generate_all()
            return Response({"count": len(schedules), "schedules": schedules, "status": "Draft"})
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class StoredTimetableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        values = [request.query_params.get(key) for key in ("department", "year", "semester")]
        if not all(values):
            return Response({"error": "department, year, and semester are required."}, status=status.HTTP_400_BAD_REQUEST)
        schedule = load_schedule(*values)
        if not schedule:
            return Response({"error": "No saved schedule exists for this selection."}, status=status.HTTP_404_NOT_FOUND)
        return Response(schedule)


class SaveIsolatedTimetableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_admin(request.user):
            return Response({"error": "Administrator account required."}, status=status.HTTP_403_FORBIDDEN)
        schedule = request.data.get("schedule")
        if not isinstance(schedule, dict) or not schedule.get("sessions"):
            return Response({"error": "A generated schedule is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            row_id = save(schedule)
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({"error": "The isolated timetable database could not save this schedule."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"id": row_id, "status": "Published", "storage": "isolated SQLite timetable store"}, status=status.HTTP_201_CREATED)


class PublishedIsolatedTimetablesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(published_for_user(request.user))
