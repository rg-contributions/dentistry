from django.shortcuts import render
from django.http import HttpResponse

MAX_DAILY_RESERVATIONS = 10

import datetime
from DentistryApp.models import Patient, Doctor, Reservation


def main(request):
    return HttpResponse("main")


def register(request):
    return HttpResponse("register")


def do_register(request):
    return HttpResponse("do_register")


def do_reserve(request):
    return HttpResponse("do_reserve")


def do_login(request):
    return HttpResponse("do_login")


def do_logout(request):
    return HttpResponse("do_logout")


def past_reservations(request):
    # use a hardcoded login for now
    user_login = "maxim"

    p = Patient.objects.filter(login=user_login).get()
    r_list = Reservation.objects.filter(patient=p).order_by("-timeslot")

    response = "Patient: {}<br>".format(p)
    for r in r_list:
        response += "Timeslot: {}, Doctor: {}<br>".format(r.timeslot, r.doctor)

    return HttpResponse(response)


def check_date(request):
    # use hardcoded doctor and date values for now
    doc_name = "Brenda Richards"
    date_str = "01.06.2019"

    doc_obj = Doctor.objects.filter(name=doc_name).get()
    date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")

    r = (
        "Free"
        if len(Reservation.objects.filter(timeslot=date_obj, doctor=doc_obj))
        < MAX_DAILY_RESERVATIONS
        else "Booked"
    )
    return HttpResponse(r)
