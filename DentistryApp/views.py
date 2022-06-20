from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from turbo.shortcuts import render_frame, render_frame_string
from DentistryApp.forms import LoginForm, RegisterForm, ReserveForm
from DentistryApp.models import Patient, Doctor, Reservation
from DentistryApp.streams import AppStream

MAX_DAILY_RESERVATIONS = 5


def main(request, reset_home=False):
    login = request.session.get("authorized_user_login", None)
    user_name = None if not login else Patient.objects.filter(login=login).get().name
    doctor_names = [d.name for d in Doctor.objects.all()]
    reserve_form = ReserveForm(doctors=doctor_names, patient=user_name)

    if reset_home:
        r = render_frame(
            request,
            "reserve_form_frame.html",
            {"reserve_form": reserve_form},
        ).update(id="main_box")
        AppStream().stream(r)

    return render(
        request,
        "base.html",
        {
            "user_login": login,
            "login_form": LoginForm(),
            "reserve_form": reserve_form,
        },
    )


def refresh_header_frames(login):
    c = {"user_login": login}
    AppStream().update("register_frame.html", c, id="register_frame")
    AppStream().update("reservations_frame.html", c, id="reservations_frame")


def home(request):
    return main(request, True)


def do_login(request):
    f = LoginForm(request.POST)
    result = ""
    try:
        if not f.is_valid():
            raise RuntimeError()

        p = Patient.objects.filter(login=f.cleaned_data["login"])
        if len(p) == 0 or not check_password(f.cleaned_data["password"], p[0].password):
            raise RuntimeError()

        request.session["authorized_user_login"] = p[0].login
        refresh_header_frames(p[0].login)

    except RuntimeError:
        result = "Wrong username or password."

    main(request, True)  # refresh "new reservations"
    login = request.session.get("authorized_user_login", None)

    return (
        render_frame(
            request,
            "login_logout_frame.html",
            {"login_form": f, "user_login": login, "login_result": result},
        )
        .replace(id="login_logout_frame")
        .response
    )


def do_logout(request):
    request.session["authorized_user_login"] = None
    refresh_header_frames(None)
    return home(request)


def register(request):
    r = render_frame(
        request,
        "register_form_frame.html",
        {"register_form": RegisterForm()},
    ).update(id="main_box")

    AppStream().stream(r)

    return HttpResponse("")


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


def do_register(request):
    f = RegisterForm(request.POST)
    try:
        register_patient_data(f)
        r = "Registration successful!"
    except RuntimeError as e:
        r = str(e)

    AppStream().update(text=r, id="main_box")

    return (
        render_frame(request, "register_form_frame.html", {"register_form": f})
        .update(id="register_form_frame")
        .response
    )


def check_login(request):
    f = RegisterForm(request.POST)
    r = " "

    p = Patient.objects.filter(login=f.data["reg_login"])
    if len(p) != 0:
        r = "Login already used!"

    if f.data["reg_password"] != f.data["passagain"]:
        r = "Passwords don't match!"

    AppStream().update(text=r, id="login_check_result")

    return HttpResponse("")


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
        result = render_frame(
            request,
            "reservation_ok.html",
            {
                "patient_name": f.cleaned_data["patient"],
                "doctor_name": f.cleaned_data["doctor"],
                "timeslot": f.cleaned_data["timeslot"],
            },
        )
    except RuntimeError as e:
        result = render_frame_string(e)

    return result.update(id="reserve_form_frame").response


def past_reservations(request):
    user_login = request.session.get("authorized_user_login", None)
    p = Patient.objects.filter(login=user_login).get()
    r_list = Reservation.objects.filter(patient=p).order_by("-timeslot")

    AppStream().update(
        id="main_box",
        template="past_reservations.html",
        context={
            "user_login": user_login,
            "user_name": p.name,
            "reservations": r_list,
        },
    )

    return HttpResponse("")


def check_date(request):
    doctor_names = [d.name for d in Doctor.objects.all()]
    f = ReserveForm(request.POST, doctors=doctor_names, patient="")

    if f.is_valid():
        doc_obj = Doctor.objects.filter(name=f.cleaned_data["doctor"]).get()
        date_obj = f.cleaned_data["timeslot"]
        bookings = len(Reservation.objects.filter(timeslot=date_obj, doctor=doc_obj))
        r = " " if bookings < MAX_DAILY_RESERVATIONS else "This day is fully booked"

        AppStream().update(text=r, id="check_date_result")

    return HttpResponse("")
