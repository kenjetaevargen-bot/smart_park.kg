from django.db import migrations, models
import django.db.models.deletion


def seed_data(apps, schema_editor):
    Mall = apps.get_model("parking", "Mall")
    ParkingSpot = apps.get_model("parking", "ParkingSpot")
    malls = [
        ("Bishkek Park", "ул. Киевская, 148", "42.874350", "74.603200", "https://images.unsplash.com/photo-1519567241046-7f570eee3ce6?auto=format&fit=crop&w=900&q=85"),
        ("Asia Mall", "ул. Юнусалиева, 177", "42.844800", "74.606500", "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=900&q=85"),
        ("Dordoi Plaza", "ул. Ибраимова, 115", "42.882800", "74.626400", "https://images.unsplash.com/photo-1567449303078-57ad995bd17a?auto=format&fit=crop&w=900&q=85"),
        ("Beta Stores", "ул. Токтогула, 87", "42.874900", "74.589400", "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&q=85"),
        ("Bishkek City", "ул. Байтик Баатыра, 17", "42.837900", "74.596000", "https://images.unsplash.com/photo-1515169067868-5387ec356754?auto=format&fit=crop&w=900&q=85"),
        ("Vefa Center", "ул. Горького, 27/1", "42.862700", "74.607100", "https://images.unsplash.com/photo-1601598851547-4302969d7c71?auto=format&fit=crop&w=900&q=85"),
        ("Cosmopark", "ул. Тыныстанова, 98", "42.870100", "74.617000", "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=900&q=85"),
    ]
    for name, address, latitude, longitude, photo_url in malls:
        mall = Mall.objects.create(name=name, address=address, latitude=latitude, longitude=longitude, photo_url=photo_url)
        for index in range(1, 13):
            ParkingSpot.objects.create(mall=mall, number=f"{chr(64 + ((index - 1) // 6) + 1)}-{((index - 1) % 6) + 1}", floor=1 if index <= 6 else 2, is_booked=index in (3, 9))


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Mall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("address", models.CharField(max_length=255)),
                ("photo_url", models.URLField()),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ParkingSpot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(max_length=20)),
                ("floor", models.PositiveSmallIntegerField(default=1)),
                ("is_booked", models.BooleanField(default=False)),
                ("mall", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="spots", to="parking.mall")),
            ],
            options={"ordering": ["floor", "number"]},
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=80)),
                ("last_name", models.CharField(max_length=80)),
                ("car_make", models.CharField(max_length=80)),
                ("plate_number", models.CharField(max_length=20)),
                ("confirmation_code", models.PositiveSmallIntegerField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("parking_spot", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reservation", to="parking.parkingspot")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(model_name="parkingspot", constraint=models.UniqueConstraint(fields=("mall", "number"), name="unique_spot_per_mall")),
        migrations.RunPython(seed_data, migrations.RunPython.noop),
    ]