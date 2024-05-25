from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django_htmx.http import trigger_client_event

from DentistryApp.forms import LoginForm, RegisterForm, ReserveForm
from DentistryApp.models import Patient, Doctor, Reservation

MAX_DAILY_RESERVATIONS = 4


def main(request):
    return render(request, "base.html")


def login_frame(request, error=""):
    login = request.session.get("authorized_user_login", None)
    # error = request.session.get("last_login_error", "")

    return render(
        request,
        "login_logout_frame.html",
        {"login_form": LoginForm(), "user_login": login, "login_error": error},
    )


def register_frame(request):
    login = request.session.get("authorized_user_login", None)
    return render(request, "register_frame.html", {"user_login": login})


def reservations_frame(request):
    login = request.session.get("authorized_user_login", None)
    return render(request, "reservations_frame.html", {"user_login": login})


def register_form_frame(request, registered_ok=False, reg_error=""):
    return render(
        request,
        "register_form_frame.html",
        {
            "registered_ok": registered_ok,
            "reg_error": reg_error,
            "register_form": RegisterForm(),
        },
    )


def register_patient_data(f):
    if not f.is_valid():
        raise RuntimeError("Error: " + str(f.errors))

    login = f.cleaned_data["reg_login"]
    name = f.cleaned_data["name"]
    password = f.cleaned_data["reg_password"]
    passagain = f.cleaned_data["passagain"]

    if len(Patient.objects.filter(login=login)) > 0:
        raise RuntimeError(f"A patient with the login {login} already exists.")

    if password != passagain:
        raise RuntimeError("Passwords do not match.")

    Patient.objects.create(name=name, login=login, password=make_password(password))
    return login


def do_register(request):
    reg_error = None
    f = RegisterForm(request.POST)
    evt = ""

    try:
        login = register_patient_data(f)
        evt = "evt_login"
        do_login_user(request, login)

    except RuntimeError as e:
        reg_error = str(e)

    response = register_form_frame(request, reg_error is None, reg_error)
    return trigger_client_event(response, evt)


def do_check_regform(request):
    f = RegisterForm(request.POST)
    r = ""

    p = Patient.objects.filter(login=f.data["reg_login"])
    if len(p) != 0:
        r = "Login already used!"

    if f.data["reg_password"] != f.data["passagain"]:
        r = "Passwords don't match!"

    return HttpResponse(r)


def do_login_user(request, login):
    request.session["authorized_user_login"] = login


def do_login(request):
    f = LoginForm(request.POST)
    error = ""
    evt = ""
    try:
        if not f.is_valid():
            raise RuntimeError()

        p = Patient.objects.filter(login=f.cleaned_data["login"])
        if len(p) == 0 or not check_password(f.cleaned_data["password"], p[0].password):
            raise RuntimeError()

        do_login_user(request, p[0].login)
        evt = "evt_login"

    except RuntimeError:
        error = "Wrong username or password."

    return trigger_client_event(login_frame(request, error), evt)


def load_login_logout_frame(request):
    return render(request, "test-form.html", {"counter": None})


def do_logout(request):
    request.session["authorized_user_login"] = None
    return trigger_client_event(login_frame(request), "evt_login")


def reserve_form_frame(request):
    login = request.session.get("authorized_user_login", None)
    user_name = None if not login else Patient.objects.filter(login=login).get().name
    doctor_names = [d.name for d in Doctor.objects.all()]
    reserve_form = ReserveForm(doctors=doctor_names, patient=user_name)

    return render(request, "reserve_form_frame.html", {"reserve_form": reserve_form})


def reserve_appointment(f, user_login):
    if not f.is_valid():
        raise RuntimeError("Error: " + str(f.errors))

    with transaction.atomic():
        values = f.cleaned_data
        p = (
            Patient.objects.create(name=values["patient"], login="", password="")
            if user_login is None
            else Patient.objects.filter(login=user_login).get()
        )
        d = Doctor.objects.filter(name=values["doctor"]).get()
        Reservation.objects.create(timeslot=values["timeslot"], doctor=d, patient=p)

        r_count = len(Reservation.objects.filter(timeslot=values["timeslot"], doctor=d))
        if r_count > MAX_DAILY_RESERVATIONS:
            raise RuntimeError("The doctor has too many patients on this day.")


def do_reserve(request):
    user_login = request.session.get("authorized_user_login", None)
    doctor_names = [d.name for d in Doctor.objects.all()]
    f = ReserveForm(request.POST, doctors=doctor_names, patient=None)

    try:
        reserve_appointment(f, user_login)
        result = render(
            request,
            "reservation_result.html",
            {
                "patient_name": f.cleaned_data["patient"],
                "doctor_name": f.cleaned_data["doctor"],
                "timeslot": f.cleaned_data["timeslot"],
            },
        )
    except RuntimeError as e:
        result = render(request, "reservation_result.html", {"error": str(e)})

    return result


def past_reservations(request):
    user_login = request.session.get("authorized_user_login", None)
    p = Patient.objects.filter(login=user_login).get()
    r_list = Reservation.objects.filter(patient=p).order_by("-timeslot")

    return render(
        request,
        "past_reservations.html",
        {
            "user_login": user_login,
            "user_name": p.name,
            "reservations": r_list,
        },
    )


def do_check_reserve(request):
    doctor_names = [d.name for d in Doctor.objects.all()]
    f = ReserveForm(request.POST, doctors=doctor_names, patient="")

    if f.is_valid():
        # print(f)
        doc_obj = Doctor.objects.filter(name=f.cleaned_data["doctor"]).get()
        date_obj = f.cleaned_data["timeslot"]
        bookings = len(Reservation.objects.filter(timeslot=date_obj, doctor=doc_obj))
        r = " " if bookings < MAX_DAILY_RESERVATIONS else "This day is fully booked"
        return HttpResponse(r)

    return HttpResponse("")
