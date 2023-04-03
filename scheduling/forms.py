from django import forms
from django.forms import ValidationError

from .models import Course, Schedule, Instructor, Campus, Location
from main.models import Profile

SUBJECTS = [
    "ABDR",
    "ACCT",
    "ACNT",
    "AERO",
    "AGMG",
    "AGRI",
    "ANTH",
    "ARTC",
    "ARTS",
    "BARB",
    "BCIS",
    "BIOL",
    "BMGT",
    "BNKG",
    "BUAD",
    "BUSG",
    "BUSI",
    "CADD",
    "CBFM",
    "CDEC",
    "CETT",
    "CHEF",
    "CHEM",
    "CJCR",
    "CJLE",
    "CJSA",
    "CMSA",
    "CMSD",
    "CNSE",
    "COLL",
    "COMG",
    "CONT",
    "COSC",
    "COSM",
    "CPMT",
    "CRIJ",
    "CSAA",
    "CSAD",
    "CSAR",
    "CSBA",
    "CSBB",
    "CSBC",
    "CSBD",
    "CSBL",
    "CSBM",
    "CSBP",
    "CSBQ",
    "CSBT",
    "CSCA",
    "CSCD",
    "CSCH",
    "CSCJ",
    "CSCK",
    "CSCL",
    "CSCM",
    "CSCO",
    "CSCP",
    "CSCR",
    "CSCS",
    "CSCW",
    "CSCY",
    "CSDF",
    "CSDO",
    "CSEL",
    "CSEM",
    "CSEP",
    "CSES",
    "CSEW",
    "CSFL",
    "CSFW",
    "CSGG",
    "CSGI",
    "CSHP",
    "CSHR",
    "CSHS",
    "CSHV",
    "CSHZ",
    "CSIE",
    "CSIR",
    "CSIT",
    "CSKJ",
    "CSLM",
    "CSLP",
    "CSLS",
    "CSLY",
    "CSMD",
    "CSME",
    "CSMR",
    "CSMT",
    "CSMU",
    "CSNG",
    "CSNO",
    "CSOO",
    "CSOS",
    "CSPA",
    "CSPC",
    "CSPL",
    "CSPM",
    "CSPO",
    "CSPP",
    "CSQG",
    "CSQT",
    "CSRC",
    "CSRG",
    "CSRN",
    "CSRP",
    "CSSC",
    "CSSN",
    "CSSP",
    "CSSS",
    "CSSW",
    "CSTE",
    "CSTO",
    "CSTS",
    "CSTW",
    "CSWC",
    "CSWD",
    "CSWL",
    "CSWS",
    "CSWW",
    "CSYG",
    "CSZD",
    "CVOP",
    "DEMR",
    "DFTG",
    "DITA",
    "DNTA",
    "DRAM",
    "ECON",
    "ECRD",
    "EDTC",
    "EDUC",
    "EECT",
    "EEIR",
    "EHKP",
    "ELCN",
    "ELCT",
    "ELEC",
    "ELPT",
    "ELTN",
    "EMSP",
    "ENGL",
    "ENGR",
    "EPCT",
    "FDST",
    "FIRE",
    "FIRT",
    "FITT",
    "FORS",
    "FPTA",
    "FRNL",
    "FRTS",
    "GEOG",
    "GEOL",
    "GNED",
    "GOVT",
    "HAMG",
    "HART",
    "HESC",
    "HIST",
    "HITT",
    "HLSC",
    "HMSY",
    "HPRO",
    "HPRS",
    "HRGY",
    "HRPO",
    "HSED",
    "HUMA",
    "HYDR",
    "IEIR",
    "IFWA",
    "IMED",
    "IMNT",
    "INCR",
    "INDS",
    "INMT",
    "INRW",
    "INSR",
    "INTC",
    "INTW",
    "ITCC",
    "ITMC",
    "ITNW",
    "ITSC",
    "ITSE",
    "ITSW",
    "ITSY",
    "LEAD",
    "LMGT",
    "MAIR",
    "MATH",
    "MCHN",
    "MDCA",
    "MEMR",
    "METL",
    "MFGT",
    "MLAB",
    "MRKG",
    "MRKT",
    "MRMT",
    "MTEC",
    "MUAP",
    "MUEN",
    "MUSB",
    "MUSC",
    "MUSI",
    "MUSP",
    "NDTE",
    "NUPC",
    "NURA",
    "NURS",
    "OFOC",
    "OPTS",
    "OSHT",
    "PACD",
    "PFPB",
    "PHED",
    "PHIL",
    "PHRA",
    "PHYS",
    "PLAB",
    "PLUM",
    "PMHS",
    "POFI",
    "POFM",
    "POFT",
    "PSTR",
    "PSYC",
    "PSYT",
    "PTAC",
    "QCTC",
    "RADR",
    "RBTC",
    "RNSG",
    "RSTO",
    "SCIT",
    "SCMA",
    "SGNL",
    "SMER",
    "SMFT",
    "SMGT",
    "SOCI",
    "SPAN",
    "SPCH",
    "SPCS",
    "SPNL",
    "SRGT",
    "TCCN",
    "TECA",
    "TECH",
    "TECM",
    "TEST",
    "THEA",
    "TRAN",
    "TRVM",
    "VIEN",
    "VNSG",
    "WKFC",
    "WLDG",
]

SUBJECT_CHOICES = [(subject, subject) for subject in SUBJECTS]


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
            self.add_error("number", "Invalid course number.")
            self.fields["number"].widget.attrs["class"] += " is-invalid"
            valid = False

        if self.cleaned_data["credit"] < 0 or self.cleaned_data["credit"] > 6:
            self.add_error("credit", "Invalid course credit.")
            self.fields["credit"].widget.attrs["class"] += " is-invalid"
            valid = False

        return valid


class ScheduleForm(forms.ModelForm):

    error_css_class = "is-invalid"

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
        choices=DAYS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"display": "inline-block"}),
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

    def clean_days(self):
        days = "".join(self.cleaned_data.get("days"))
        return days

    def clean_section(self):
        section = self.cleaned_data.get("section").upper()
        return section

    def clean(self):
        cleaned_data = super(ScheduleForm, self).clean()

        # section with NT, location will be blank, campus will be internet
        if "NT" in self.cleaned_data["section"]:
            if self.cleaned_data["location"] != Location.objects.get(
                building="Inter", room="net"
            ):
                self.add_error("location", "Location should be Internet.")
            if self.cleaned_data["campus"] not in Campus.objects.filter(
                name__contains="Internet"
            ):
                self.add_error("campus", "Campus should be Internet.")

        # stop time > start time
        if (
            self.cleaned_data["start_time"]
            and self.cleaned_data["stop_time"]
            and self.cleaned_data["start_time"] > self.cleaned_data["stop_time"]
        ) or (
            bool(self.cleaned_data["start_time"])
            != bool(self.cleaned_data["stop_time"])
        ):
            self.add_error("start_time", "Invalid start time.")
            self.add_error("stop_time", "Invalid stop time.")

        return cleaned_data

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
        self.fields["section"].widget.attrs["placeholder"] = "<Optional>"
        self.fields["term"].widget.attrs["id"] = "id_term_c"
        self.fields["course"].widget.attrs["id"] = "id_course_c"
        self.fields["section"].widget.attrs["id"] = "id_section_c"

        for _, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                field.widget.attrs["class"] = "form-control"


class SearchBySubjectForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["term"]

    def __init__(self, choices, *args, **kwargs):
        super(SearchBySubjectForm, self).__init__(*args, **kwargs)
        self.fields["subject"] = forms.ChoiceField(choices=choices, required=True)
        self.fields["term"].widget.attrs["id"] = "id_term_d"

        for _, field in self.fields.items():
            if field.widget.attrs.get("class"):
                field.widget.attrs["class"] += " form-control"
            else:
                field.widget.attrs["class"] = "form-control"
