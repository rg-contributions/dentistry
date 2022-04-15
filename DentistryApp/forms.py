from django import forms
from django.forms.widgets import PasswordInput

ADVANCE_RESERVATION_DAYS = 14


class RegisterForm(forms.Form):
    name = forms.CharField(label="Name", max_length=20)
    reg_login = forms.CharField(label="Login", max_length=20)
    reg_password = forms.CharField(
        label="Password", max_length=20, widget=forms.PasswordInput()
    )
    passagain = forms.CharField(
        label="Password again", max_length=20, widget=forms.PasswordInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reg_login"].widget.attrs["onchange"] = "form.requestSubmit();"
        self.fields["reg_password"].widget.attrs["onchange"] = "form.requestSubmit();"
        self.fields["passagain"].widget.attrs["onchange"] = "form.requestSubmit();"


class LoginForm(forms.Form):
    login = forms.CharField(label="Login", max_length=20)
    password = forms.CharField(label="Password", max_length=20, widget=PasswordInput())


class DateInput(forms.DateInput):
    input_type = "date"


class ReserveForm(forms.Form):
    patient = forms.CharField(label="Name", max_length=20)
    doctor = forms.ChoiceField(label="Doctor")
    timeslot = forms.DateField(
        label="Date", widget=DateInput(attrs={"onchange": "form.requestSubmit();"})
    )

    def __init__(self, *args, **kwargs):
        doctors = kwargs.pop("doctors")
        patient = kwargs.pop("patient")
        super().__init__(*args, **kwargs)

        self.fields["doctor"].choices = zip(doctors, doctors)
        self.fields["doctor"].widget.attrs["onchange"] = "form.requestSubmit();"
        if patient:
            self.fields["patient"].initial = patient
            self.fields["patient"].widget.attrs["readonly"] = True
