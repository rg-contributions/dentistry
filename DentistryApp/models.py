from django.db import models


class Doctor(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Patient(models.Model):
    name = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Reservation(models.Model):
    timeslot = models.DateField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.patient.name} -> {self.doctor.name} ({self.timeslot})"
