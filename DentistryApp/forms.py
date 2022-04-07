from django import forms
from django.forms.widgets import PasswordInput

ADVANCE_RESERVATION_DAYS = 14


class RegisterForm(forms.Form):
    name = forms.CharField(label="Name", max_length=20)
    login = forms.CharField(label="Login", max_length=20)
    password = forms.CharField(
        label="Password", max_length=20, widget=forms.PasswordInput()
    )
    passagain = forms.CharField(
        label="Password again", max_length=20, widget=forms.PasswordInput()
    )


class LoginForm(forms.Form):
    login = forms.CharField(label="Login", max_length=20)
    password = forms.CharField(label="Password", max_length=20, widget=PasswordInput())


class ReserveForm(forms.Form):
    patient = forms.CharField(label="Name", max_length=20)
    doctor = forms.ChoiceField(label="Doctor")
    timeslot = forms.DateField(label="Date")

    def __init__(self, *args, **kwargs):
        doctors = kwargs.pop("doctors")
        patient = kwargs.pop("patient")
        super().__init__(*args, **kwargs)

        self.fields["doctor"].choices = zip(doctors, doctors)
        if patient:
            self.fields["patient"].initial = patient
            self.fields["patient"].widget.attrs["readonly"] = True
