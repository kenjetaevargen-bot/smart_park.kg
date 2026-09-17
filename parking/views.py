import random

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Mall, ParkingSpot, Reservation


def index(request):
    return render(request, "index.html")


def mall_payload(mall):
    spots = list(mall.spots.all())
    return {
        "id": mall.id,
        "name": mall.name,
        "address": mall.address,
        "photo_url": mall.photo_url,
        "latitude": float(mall.latitude),
        "longitude": float(mall.longitude),
        "free_count": sum(not spot.is_booked for spot in spots),
        "total_count": len(spots),
        "spots": [{"id": spot.id, "number": spot.number, "floor": spot.floor, "is_booked": spot.is_booked} for spot in spots],
    }


@require_GET
def bootstrap(request):
    malls = Mall.objects.prefetch_related("spots").all()
    return JsonResponse({"malls": [mall_payload(mall) for mall in malls], "profile": request.session.get("profile")})


@require_POST
def profile(request):
    data = request.POST
    required = ("first_name", "last_name", "car_make", "plate_number")
    if any(not data.get(field, "").strip() for field in required):
        return JsonResponse({"error": "Заполните все поля профиля."}, status=400)
    saved = {field: data[field].strip() for field in required}
    request.session["profile"] = saved
    request.session.modified = True
    return JsonResponse({"profile": saved})


@require_GET
def reservations(request):
    plate = (request.GET.get("plate") or request.session.get("profile", {}).get("plate_number", "")).strip().upper()
    items = Reservation.objects.select_related("parking_spot__mall").filter(plate_number__iexact=plate)
    return JsonResponse({"reservations": [{
        "id": item.id,
        "mall": item.parking_spot.mall.name,
        "address": item.parking_spot.mall.address,
        "spot": item.parking_spot.number,
        "floor": item.parking_spot.floor,
        "plate_number": item.plate_number,
        "confirmation_code": f"{item.confirmation_code:04d}",
        "created_at": item.created_at.strftime("%d.%m.%Y, %H:%M"),
    } for item in items]})


def unique_code():
    used = set(Reservation.objects.values_list("confirmation_code", flat=True))
    available = list(set(range(1000, 10000)) - used)
    return random.choice(available)


@require_POST
def create_reservation(request):
    data = request.POST
    profile_data = request.session.get("profile", {})
    values = {field: data.get(field, "").strip() or profile_data.get(field, "").strip() for field in ("first_name", "last_name", "car_make", "plate_number")}
    if any(not value for value in values.values()) or not data.get("spot_id"):
        return JsonResponse({"error": "Сначала заполните профиль и выберите свободное место."}, status=400)
    try:
        with transaction.atomic():
            spot = ParkingSpot.objects.select_for_update().select_related("mall").get(pk=data["spot_id"])
            if spot.is_booked:
                return JsonResponse({"error": "Это место уже заняли. Выберите другое."}, status=409)
            reservation = Reservation.objects.create(parking_spot=spot, confirmation_code=unique_code(), **values)
            spot.is_booked = True
            spot.save(update_fields=["is_booked"])
    except (ParkingSpot.DoesNotExist, IntegrityError):
        return JsonResponse({"error": "Место недоступно. Обновите карту и попробуйте ещё раз."}, status=409)
    return JsonResponse({"reservation": {
        "id": reservation.id,
        "mall": spot.mall.name,
        "spot": spot.number,
        "floor": spot.floor,
        "confirmation_code": f"{reservation.confirmation_code:04d}",
    }}, status=201)


@require_POST
def cancel_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.get(pk=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse({"error": "Бронирование не найдено."}, status=404)
    reservation.parking_spot.is_booked = False
    reservation.parking_spot.save(update_fields=["is_booked"])
    reservation.delete()
    return JsonResponse({"ok": True})