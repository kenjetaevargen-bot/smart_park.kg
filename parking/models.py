from django.db import models


class Mall(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    photo_url = models.URLField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def free_spots_count(self):
        return self.spots.filter(is_booked=False).count()


class ParkingSpot(models.Model):
    mall = models.ForeignKey(Mall, related_name="spots", on_delete=models.CASCADE)
    number = models.CharField(max_length=20)
    floor = models.PositiveSmallIntegerField(default=1)
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["floor", "number"]
        constraints = [models.UniqueConstraint(fields=["mall", "number"], name="unique_spot_per_mall")]

    def __str__(self):
        return f"{self.mall.name} · {self.number}"


class Reservation(models.Model):
    parking_spot = models.OneToOneField(ParkingSpot, related_name="reservation", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    car_make = models.CharField(max_length=80)
    plate_number = models.CharField(max_length=20)
    confirmation_code = models.PositiveSmallIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.plate_number} · {self.confirmation_code}"