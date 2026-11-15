from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("timetable", "0002_user_profile")]

    operations = [
        migrations.AddField(model_name="userprofile", name="batch", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="userprofile", name="section", field=models.CharField(blank=True, default="", max_length=30)),
        migrations.AddField(model_name="userprofile", name="student_group", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="userprofile", name="course", field=models.CharField(blank=True, default="", max_length=150)),
        migrations.AddField(model_name="userprofile", name="year", field=models.CharField(blank=True, default="", max_length=30)),
    ]
