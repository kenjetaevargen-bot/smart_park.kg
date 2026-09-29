from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("parking", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("surname", models.CharField(max_length=80)),
                ("phone", models.CharField(max_length=32, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("car_model", models.CharField(blank=True, max_length=80)),
                ("plate_number", models.CharField(blank=True, max_length=20)),
                ("car_color", models.CharField(blank=True, max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]