from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from main.models import Subject


class Course(models.Model):

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE)
    number = models.CharField(max_length=4)
    credit = models.IntegerField()
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.subject.name + self.number


class Location(models.Model):
    """Location for schedules"""

    building = models.CharField(max_length=10)
    room = models.CharField(max_length=20)

    def __str__(self):
        return self.building + self.room


class Term(models.Model):

    SEMESTER_CHOICES = [
        ('FALL', 'Fall'),
        ('SPRING', 'Spring'),
        ('SUMMER', 'Summer'),
    ]

    ACTIVE_CHOICES = [
        ('T', 'True'),
        ('F', 'False')
    ]

    year = models.IntegerField(default=int(datetime.now().year), validators=[
                               MinValueValidator(datetime.now().year - 2), MaxValueValidator(datetime.now().year + 2)])
    semester = models.CharField(max_length=6, choices=SEMESTER_CHOICES)
    active = models.CharField(max_length=1, choices=ACTIVE_CHOICES)

    def __str__(self):
        return self.semester + str(self.year)


class Instructor(models.Model):
    """Instructor for each schedule"""

    HIRE_STATUSES = (
        ('F', 'Full-Time'),
        ('P', 'Part-Time'),
    )

    employee_id = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    hiring_status = models.CharField(max_length=1, choices=HIRE_STATUSES)

    def __str__(self):
        if self.last_name and self.first_name:
            return self.last_name + ", " + self.first_name
        else:
            return ""


class Campus(models.Model):
    """Campus for each schedule"""

    name = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = "campuses"

    def __str__(self):
        return self.name


class Schedule(models.Model):

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELED', 'Canceled')
    ]

    # term
    term = models.ForeignKey(
        Term, on_delete=models.SET_NULL, null=True)

    # course to schedule
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # section A01, A01NT, A01HY...
    section = models.CharField(max_length=5)

    # max enrollment
    capacity = models.IntegerField()

    # instructor
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, null=True)

    status = models.CharField(
        max_length=9, choices=STATUS_CHOICES, default='OPEN')

    # Main, south, high school
    campus = models.ForeignKey(
        Campus, on_delete=models.SET_NULL, null=True, blank=True)

    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True)

    days = models.CharField(max_length=7, null=True, blank=True)

    start_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True)
    stop_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True)

    # insert by who and when
    insert_date = models.DateTimeField(auto_now=False, auto_now_add=True)
    insert_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='insert')

    # update by who and when
    update_date = models.DateTimeField(auto_now=True, auto_now_add=False)
    update_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='update')

    notes = models.CharField(default='', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.course.__str__() + self.section


class Cams(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELED', 'Canceled')
    ]

    # term
    term = models.ForeignKey(
        Term, on_delete=models.SET_NULL, null=True)

    # course to schedule
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # section A01, A01NT, A01HY...
    section = models.CharField(max_length=5)

    # max enrollment
    capacity = models.IntegerField()

    # instructor
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, null=True)

    status = models.CharField(
        max_length=9, choices=STATUS_CHOICES, default='OPEN')

    # Main, south, high school
    campus = models.ForeignKey(
        Campus, on_delete=models.SET_NULL, null=True, blank=True)

    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True)

    days = models.CharField(max_length=7, null=True, blank=True)

    start_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True)
    stop_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True)
