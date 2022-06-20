from datetime import date
import pytest
from django.contrib.auth.hashers import make_password
from DentistryApp.models import Patient, Doctor, Reservation
from DentistryApp.views import reserve_appointment, MAX_DAILY_RESERVATIONS
from DentistryApp.forms import ReserveForm


@pytest.mark.django_db
def test_create_data():
    p = Patient(name="John", login="jonny", password=make_password("jpass"))
    p.save()

    d = Doctor(name="Mr Doctor")
    d.save()

    Reservation.objects.create(timeslot=date(2022, 4, 5), doctor=d, patient=p)

    assert len(Patient.objects.all()) == 1
    assert len(Doctor.objects.all()) == 1
    assert len(Reservation.objects.all()) == 1


@pytest.mark.django_db
def test_reserve_appointment():
    Patient.objects.create(name="John", login="jonny", password=make_password("jpass"))
    Doctor.objects.create(name="Mr Doctor")
    f = ReserveForm(
        {"patient": "John", "doctor": "Mr Doctor", "timeslot": date(2022, 4, 5)},
        doctors=["Mr Doctor"],
        patient="John",
    )

    reserve_appointment(f, "jonny")
    assert len(Reservation.objects.all()) == 1

    with pytest.raises(RuntimeError):
        for _ in range(MAX_DAILY_RESERVATIONS):
            reserve_appointment(f, "jonny")
