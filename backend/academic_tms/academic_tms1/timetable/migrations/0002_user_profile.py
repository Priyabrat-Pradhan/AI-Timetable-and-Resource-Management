from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("timetable", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("faculty", "Faculty"), ("student", "Student")], max_length=20)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("institutional_id", models.CharField(max_length=100)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="smarttime_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
