from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponse
from DentistryApp.forms import LoginForm, RegisterForm, ReserveForm
from django.contrib.auth.hashers import make_password, check_password

MAX_DAILY_RESERVATIONS = 10

import datetime
from DentistryApp.models import Patient, Doctor, Reservation


def main(request):
    user_login = request.session.get("authorized_user_login", None)
    user_name = (
        None if not user_login else Patient.objects.filter(login=user_login).get().name
    )
    doctor_names = [d.name for d in Doctor.objects.all()]
    reserve_form = ReserveForm(doctors=doctor_names, patient=user_name)

    return render(
        request,
        "main.html",
        {"user": user_login, "login_form": LoginForm(), "reserve_form": reserve_form},
    )


def register(request):
    return render(request, "register.html", {"register_form": RegisterForm()})


def register_patient_data(f):
    if not f.is_valid():
        raise RuntimeError("Error: " + str(f.errors))

    login = f.cleaned_data["login"]
    name = f.cleaned_data["name"]
    password = f.cleaned_data["password"]
    passagain = f.cleaned_data["passagain"]

    if len(Patient.objects.filter(login=login)) > 0:
        raise RuntimeError(f"A patient with the login {login} already exists.")

    if password != passagain:
        raise RuntimeError("Passwords do not match.")

    Patient.objects.create(name=name, login=login, password=make_password(password))


def do_register(request):
    try:
        register_patient_data(RegisterForm(request.POST))
    except RuntimeError as e:
        return HttpResponse(str(e) + "<p><a href=register>Go back</a>.")

    return redirect("view-main")


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
    except RuntimeError as e:
        return HttpResponse(str(e) + "<p><a href=main>Go back</a>.")

    return render(
        request,
        "reservation_ok.html",
        {
            "patient_name": f.cleaned_data["patient"],
            "doctor_name": f.cleaned_data["doctor"],
            "timeslot": f.cleaned_data["timeslot"],
        },
    )


def do_login(request):
    f = LoginForm(request.POST)
    try:
        if not f.is_valid():
            raise RuntimeError("Error: " + str(f.errors))

        p = Patient.objects.filter(login=f.cleaned_data["login"])
        if len(p) == 0 or not check_password(f.cleaned_data["password"], p[0].password):
            raise RuntimeError("Wrong username or password.")

        request.session["authorized_user_login"] = p[0].login

    except RuntimeError as e:
        return HttpResponse(str(e) + "<p><a href=main>Go back</a>.")

    return redirect("view-main")


def do_logout(request):
    request.session["authorized_user_login"] = None
    return redirect("view-main")


def past_reservations(request):
    user_login = request.session.get("authorized_user_login", None)
    if user_login is None:
        return HttpResponse("Error: user not logged in.<p><a href=main>Go back</a>.")

    p = Patient.objects.filter(login=user_login).get()
    r_list = Reservation.objects.filter(patient=p).order_by("-timeslot")

    return render(
        request, "past_reservations.html", {"user_name": p.name, "reservations": r_list}
    )


def check_date(request):
    doc_name = request.POST.get("doctor")
    date_str = request.POST.get("date_str")

    doc_obj = Doctor.objects.filter(name=doc_name).get()
    date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")

    r = (
        "Free"
        if len(Reservation.objects.filter(timeslot=date_obj, doctor=doc_obj))
        < MAX_DAILY_RESERVATIONS
        else "Booked"
    )
    return HttpResponse(r)
