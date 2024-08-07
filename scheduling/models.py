from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Course(models.Model):

    subject = models.CharField(max_length=4)
    number = models.CharField(max_length=4)
    credit = models.IntegerField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.subject + self.number


class Location(models.Model):
    """Location for schedules"""

    building = models.CharField(max_length=10)
    room = models.CharField(max_length=20)

    def __str__(self):
        return self.building + self.room


class Term(models.Model):

    SEMESTER_CHOICES = [
        ("FALL", "Fall"),
        ("SPRING", "Spring"),
        ("SUMMER", "Summer"),
    ]

    ACTIVE_CHOICES = [("T", "True"), ("F", "False")]

    year = models.IntegerField(
        default=int(datetime.now().year),
        validators=[
            MinValueValidator(datetime.now().year - 2),
            MaxValueValidator(datetime.now().year + 2),
        ],
    )
    semester = models.CharField(max_length=6, choices=SEMESTER_CHOICES)
    active = models.CharField(max_length=1, choices=ACTIVE_CHOICES)

    def __str__(self):
        return self.semester + str(self.year)


class Instructor(models.Model):
    """Instructor for each schedule"""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        if self.first_name and self.last_name:
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

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="delete"
    )

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    class Meta:
        abstract = True

class Schedule(SoftDeleteModel):

    STATUS_CHOICES = [("OPEN", "Open"), ("CLOSED", "Closed"), ("CANCELED", "Canceled")]

    # term
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True)

    # course to schedule
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # section A01, A01NT, A01HY...
    section = models.CharField(max_length=5)

    # max enrollment
    capacity = models.IntegerField()

    # instructor
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, null=True, blank=True
    )

    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="OPEN")

    # Main, south, high school
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True)

    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )

    days = models.CharField(max_length=7, null=True, blank=True)

    start_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )
    stop_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )

    # insert by who and when
    insert_date = models.DateTimeField(auto_now=False, auto_now_add=True)
    insert_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="insert"
    )

    # update by who and when
    update_date = models.DateTimeField(auto_now=True, auto_now_add=False)
    update_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="update"
    )

    notes = models.CharField(default="", max_length=100, blank=True, null=True)

    def __str__(self):
        return self.course.__str__() + self.section

    class Meta:
        ordering = ["term", "course", "section"]


class Cams(models.Model):
    """Schedule model for cams data
    """

    STATUS_CHOICES = [("OPEN", "Open"), ("CLOSED", "Closed"), ("CANCELED", "Canceled")]

    # term
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True)

    # course to schedule
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # section A01, A01NT, A01HY...
    section = models.CharField(max_length=5)

    # max enrollment
    capacity = models.IntegerField()

    # instructor
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, null=True, blank=True
    )

    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="OPEN")

    # Main, south, high school
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True)

    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )

    days = models.CharField(max_length=7, null=True, blank=True)

    start_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )
    stop_time = models.TimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )

    def __str__(self):
        return self.course.__str__() + self.section

    class Meta:
        verbose_name = "CAMS"
        verbose_name_plural = "CAMS"


class Dates(models.Model):
    cams_update_at = models.DateTimeField()

    def __str__(self):
        return "Important Dates"

    class Meta:
        verbose_name = "Dates"
        verbose_name_plural = "Dates"
