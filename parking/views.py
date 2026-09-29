import random

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Mall, ParkingSpot, Reservation, UserProfile


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
    account = None
    user_id = request.session.get("user_profile_id")
    if user_id:
        account = UserProfile.objects.filter(id=user_id).values(
            "id", "name", "surname", "phone", "email", "car_model", "plate_number", "car_color"
        ).first()
        if not account:
            request.session.pop("user_profile_id", None)
            request.session.pop("profile", None)
            request.session.modified = True
    return JsonResponse({"malls": [mall_payload(mall) for mall in malls], "profile": request.session.get("profile"), "account": account})


def account_payload(account):
    return {
        "id": account.id,
        "name": account.name,
        "surname": account.surname,
        "phone": account.phone,
        "email": account.email,
        "car_model": account.car_model,
        "plate_number": account.plate_number,
        "car_color": account.car_color,
    }


def set_session_profile(request, account):
    request.session["user_profile_id"] = account.id
    request.session["profile"] = {
        "first_name": account.name,
        "last_name": account.surname,
        "car_make": account.car_model,
        "plate_number": account.plate_number,
    }
    request.session.modified = True


@require_POST
def login(request):
    phone_or_email = (request.POST.get("phone_or_email") or "").strip()
    if not phone_or_email:
        return JsonResponse({"error": "Введите номер телефона или email."}, status=400)

    query = phone_or_email.strip()
    account = UserProfile.objects.filter(phone__iexact=query).first()
    if not account:
        account = UserProfile.objects.filter(email__iexact=query.lower()).first()
    if not account:
        return JsonResponse({"error": "Пользователь не найден. Зарегистрируйтесь или проверьте данные."}, status=404)

    set_session_profile(request, account)
    return JsonResponse({"account": account_payload(account), "profile": request.session["profile"]})


@require_POST
def logout(request):
    request.session.pop("user_profile_id", None)
    request.session.pop("profile", None)
    request.session.modified = True
    return JsonResponse({"ok": True})


@require_POST
def register(request):
    data = request.POST
    values = {field: data.get(field, "").strip() for field in ("name", "surname", "phone", "email")}
    if any(not value for value in values.values()):
        return JsonResponse({"error": "Заполните все поля регистрации."}, status=400)
    values["email"] = values["email"].lower()
    existing = UserProfile.objects.filter(phone=values["phone"], email=values["email"]).first()
    if existing or UserProfile.objects.filter(phone=values["phone"]).exists() or UserProfile.objects.filter(email=values["email"]).exists():
        if existing:
            request.session["user_profile_id"] = existing.id
            request.session["profile"] = {"first_name": existing.name, "last_name": existing.surname, "car_make": existing.car_model, "plate_number": existing.plate_number}
            return JsonResponse({"error": "Этот пользователь уже зарегистрирован. Открываем личный кабинет.", "account": account_payload(existing)}, status=409)
        return JsonResponse({"error": "Этот пользователь уже зарегистрирован. Откройте личный кабинет."}, status=409)
    try:
        account = UserProfile.objects.create(**values)
    except IntegrityError:
        return JsonResponse({"error": "Этот пользователь уже зарегистрирован. Откройте личный кабинет."}, status=409)
    set_session_profile(request, account)
    request.session["profile"] = {"first_name": account.name, "last_name": account.surname, "car_make": account.car_model, "plate_number": account.plate_number}
    return JsonResponse({"account": account_payload(account)}, status=201)


@require_POST
def update_account(request):
    account_id = request.session.get("user_profile_id")
    account = UserProfile.objects.filter(id=account_id).first()
    if not account:
        return JsonResponse({"error": "Сначала пройдите регистрацию."}, status=401)
    data = request.POST
    values = {field: data.get(field, "").strip() for field in ("name", "surname", "phone", "email", "car_model", "plate_number", "car_color")}
    if any(not values[field] for field in ("name", "surname", "phone", "email")):
        return JsonResponse({"error": "Имя, фамилия, телефон и email обязательны."}, status=400)
    values["email"] = values["email"].lower()
    if UserProfile.objects.filter(phone=values["phone"]).exclude(id=account.id).exists() or UserProfile.objects.filter(email=values["email"]).exclude(id=account.id).exists():
        return JsonResponse({"error": "Телефон или email уже принадлежат другому пользователю."}, status=409)
    for field, value in values.items():
        setattr(account, field, value)
    try:
        account.save()
    except IntegrityError:
        return JsonResponse({"error": "Телефон или email уже принадлежат другому пользователю."}, status=409)
    request.session["profile"] = {"first_name": account.name, "last_name": account.surname, "car_make": account.car_model, "plate_number": account.plate_number}
    return JsonResponse({"account": account_payload(account)})


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