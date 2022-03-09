from django import forms
from django.forms import ValidationError

from .models import Course, Schedule, Instructor, Campus, Location
from main.models import Profile

from dal import autocomplete


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["subject", "number", "credit", "name"]
        labels = {
            "subject": "Subject",
            "number": "Number",
            "credit": "Credits",
            "name": "Name",
        }

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super(CourseForm, self).clean()

        subject = cleaned_data["subject"]
        number = cleaned_data["number"]
        credit = cleaned_data["credit"]

        matching_courses = Course.objects.filter(
            subject=subject, number=number, credit=credit
        )
        if self.instance:
            matching_courses = matching_courses.exclude(pk=self.instance.pk)
        if matching_courses:
            msg = f"Course {subject}{number} already exists."
            self._errors["duplicate"] = msg
            raise ValidationError(msg)
        else:
            return cleaned_data

    def is_valid(self):
        valid = super(CourseForm, self).is_valid()

        if not valid:
            return valid

        if len(self.cleaned_data["number"]) != 4:
            self._errors["number"] = "Invalid course number."
            self.fields["number"].widget.attrs["class"] += " is-invalid"
            valid = False

        if self.cleaned_data["credit"] < 0 or self.cleaned_data["credit"] > 6:
            self._errors["credit"] = "Invalid course credit."
            self.fields["credit"].widget.attrs["class"] += " is-invalid"
            valid = False

        return valid


class ScheduleForm(forms.ModelForm):

    DAYS_CHOICES = [
        ("M", "M"),
        ("T", "T"),
        ("W", "W"),
        ("R", "R"),
        ("F", "F"),
        ("S", "S"),
        ("U", "U"),
    ]

    days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES, required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Schedule
        fields = [
            "term",
            "course",
            "section",
            "instructor",
            "capacity",
            "status",
            "campus",
            "location",
            "days",
            "start_time",
            "stop_time",
            "notes",
        ]
        labels = {
            "term": "Term",
            "course": "Course",
            "section": "Section",
            "instructor": "Instructor",
            "capacity": "Capacity",
            "status": "Status",
            "campus": "Campus",
            "location": "Location",
            "days": "Days",
            "start_time": "Start",
            "stop_time": "Stop",
            "notes": "Notes",
        }

        widgets = {
            "start_time": forms.TimeInput(
                attrs={"class": "timepicker", "placeholder": "8:00 AM"}
            ),
            "stop_time": forms.TimeInput(
                attrs={"class": "timepicker", "placeholder": "10:00 PM"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                if field_name == "days":
                    field.widget.attrs["class"] = ""
                else:
                    field.widget.attrs["class"] = "form-control"

    def clean(self):

        cleaned_data = super(ScheduleForm, self).clean()
        cleaned_data["days"] = "".join(cleaned_data["days"])

        # term = cleaned_data['term']
        # course = cleaned_data['course']
        # section = cleaned_data['section']

        # matching_schedules = Schedule.objects.filter(term=term,
        #                                              course=course, section=section
        #                                              )
        # if self.instance:
        #     matching_schedules = matching_schedules.exclude(
        #         pk=self.instance.pk)
        # if matching_schedules:
        #     msg = f'Schedule {course} {section} already exists.'
        #     self._errors['duplicate'] = msg
        #     raise ValidationError(msg)
        # else:
        #     return cleaned_data

        return cleaned_data

    def is_valid(self):

        valid = super(ScheduleForm, self).is_valid()

        if not valid:
            return valid

        # section with NT, location will be blank, campus will be internet
        if "NT" in self.cleaned_data["section"]:
            if self.cleaned_data["location"] != Location.objects.get(
                building="Inter", room="net"
            ):
                self.fields["location"].widget.attrs["class"] += " is-invalid"
                valid = False
            if self.cleaned_data["campus"] not in Campus.objects.filter(
                name__contains="Internet"
            ):
                self.fields["campus"].widget.attrs["class"] += " is-invalid"
                valid = False

        # stop time > start time
        if (
            self.cleaned_data["start_time"]
            and self.cleaned_data["stop_time"]
            and self.cleaned_data["start_time"] > self.cleaned_data["stop_time"]
        ):
            self._errors["Time"] = "Invalid start and stop time."
            self.fields["start_time"].widget.attrs["class"] += " is-invalid"
            self.fields["stop_time"].widget.attrs["class"] += " is-invalid"
            valid = False

        return valid

    def save(self, commit=True):
        schedule = super(ScheduleForm, self).save(commit=False)

        if commit:
            schedule.save()
        return schedule


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ["first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super(InstructorForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super(InstructorForm, self).clean()

        first_name = cleaned_data["first_name"]
        last_name = cleaned_data["last_name"]

        matching_instructors = Instructor.objects.filter(
            first_name=first_name, last_name=last_name
        )
        if self.instance:
            matching_instructors = matching_instructors.exclude(pk=self.instance.pk)
        if matching_instructors:
            msg = f"Instructor {first_name} {last_name} already exists."
            self._errors["duplicate"] = msg
            raise ValidationError(msg)
        else:
            return cleaned_data


class SubjectForm(forms.ModelForm):

    SUBJECTS = [
        "ABDR",
        "ACCT",
        "ACNT",
        "AGMG",
        "AGRI",
        "ARTS",
        "BARB",
        "BCIS",
        "BIOL",
        "BMGT",
        "BNKG",
        "BUSG",
        "BUSI",
        "CDEC",
        "CHEF",
        "CHEM",
        "CJLE",
        "CJSA",
        "COLL",
        "COSC",
        "CPMT",
        "CRIJ",
        "CSME",
        "DFTG",
        "DNTA",
        "DRAM",
        "ECON",
        "EDUC",
        "EECT",
        "ELPT",
        "ELTN",
        "EMSP",
        "ENGL",
        "ENGR",
        "FDST",
        "GEOG",
        "GEOL",
        "GOVT",
        "HAMG",
        "HART",
        "HIST",
        "HITT",
        "HPRS",
        "HRPO",
        "HUMA",
        "IFWA",
        "IMED",
        "INMT",
        "INRW",
        "INSR",
        "ITNW",
        "ITSC",
        "ITSE",
        "ITSW",
        "ITSY",
        "MATH",
        "MCHN",
        "MLAB",
        "MRKG",
        "MUAP",
        "MUEN",
        "MUSB",
        "MUSC",
        "MUSI",
        "MUSP",
        "NURS",
        "OSHT",
        "PHED",
        "PHIL",
        "PHYS",
        "PLAB",
        "POFI",
        "POFM",
        "POFT",
        "PSTR",
        "PSYC",
        "PTAC",
        "QCTC",
        "RADR",
        "RNSG",
        "RSTO",
        "SOCI",
        "SPAN",
        "SPCH",
        "TECA",
        "TECM",
        "TRVM",
        "VNSG",
        "WLDG",
    ]

    SUBJECT_CHOICES = [(subject, subject) for subject in SUBJECTS]

    class Meta:
        model = Profile
        fields = ["subjects"]

    subjects = forms.MultipleChoiceField(choices=SUBJECT_CHOICES, required=False)

    def clean(self):
        cleaned_data = super(SubjectForm, self).clean()
        cleaned_data["subjects"] = ",".join(cleaned_data["subjects"])
        return cleaned_data


class SearchForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["term", "course", "section"]

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields["section"].required = False

        for _, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                field.widget.attrs["class"] = "form-control"

