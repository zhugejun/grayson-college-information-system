from django import forms
from django.contrib.admin import widgets
from django.utils.encoding import force_text
from django.forms import ValidationError

from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget

from .models import Course, Schedule, Instructor, Campus, Location
from main.models import Profile, Subject


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['subject', 'number', 'credit', 'name']
        labels = {
            'subject': 'Subject',
            'number': 'Number',
            'credit': 'Credits',
            'name': 'Name'
        }

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(CourseForm, self).clean()

        subject = cleaned_data['subject']
        number = cleaned_data['number']
        credit = cleaned_data['credit']

        matching_courses = Course.objects.filter(
            subject=subject, number=number, credit=credit
        )
        if self.instance:
            matching_courses = matching_courses.exclude(
                pk=self.instance.pk)
        if matching_courses:
            msg = f'Course {subject}{number} already exists.'
            self._errors['duplicate'] = msg
            raise ValidationError(msg)
        else:
            return cleaned_data

    def is_valid(self):
        valid = super(CourseForm, self).is_valid()

        if not valid:
            return valid

        if len(self.cleaned_data['number']) != 4:
            self._errors['number'] = 'Invalid course number.'
            self.fields['number'].widget.attrs['class'] += ' is-invalid'
            valid = False

        if self.cleaned_data['credit'] < 0 or self.cleaned_data['credit'] > 6:
            self._errors['credit'] = 'Invalid course credit.'
            self.fields['credit'].widget.attrs['class'] += ' is-invalid'
            valid = False

        return valid


class ScheduleForm(forms.ModelForm):

    DAYS_CHOICES = [
        ('M', 'Monday'),
        ('T', 'Tuesday'),
        ('W', 'Wednesday'),
        ('R', 'Thursday'),
        ('F', 'Friday'),
        ('S', 'Saturday'),
    ]

    days = forms.MultipleChoiceField(choices=DAYS_CHOICES, required=False)

    class Meta:
        model = Schedule
        fields = ['course', 'section', 'instructor', 'capacity', 'status', 'campus', 'location', 'days',
                  'start_time', 'stop_time', 'notes']
        labels = {
            'course': 'Course',
            'section': 'Section',
            'instructor': 'Instructor',
            'capacity': 'Capacity',
            'status': 'Status',
            'campus': 'Campus',
            'location': 'Location',
            'days': 'Days',
            'start_time': 'Start',
            'stop_time': 'Stop',
            'notes': 'Notes'}

        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'timepicker', 'placeholder': '8:00 AM'}),
            'stop_time': forms.TimeInput(attrs={'class': 'timepicker', 'placeholder': '10:00 PM'}),
        }

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):

        cleaned_data = super(ScheduleForm, self).clean()
        cleaned_data['days'] = ''.join(cleaned_data['days'])

        course = cleaned_data['course']
        section = cleaned_data['section']

        matching_schedules = Schedule.objects.filter(
            course=course, section=section
        )
        if self.instance:
            matching_schedules = matching_schedules.exclude(
                pk=self.instance.pk)
        if matching_schedules:
            msg = f'Schedule {course} {section} already exists.'
            self._errors['duplicate'] = msg
            raise ValidationError(msg)
        else:
            return cleaned_data

        return cleaned_data

    def is_valid(self):

        valid = super(ScheduleForm, self).is_valid()

        if not valid:
            return valid

        # section with NT, location will be blank, campus will be internet
        if 'NT' in self.cleaned_data['section']:
            if self.cleaned_data['location'] != Location.objects.get(building='Inter', room='net'):
                self.fields['location'].widget.attrs['class'] += ' is-invalid'
                valid = False
            if self.cleaned_data['campus'] != Campus.objects.get(name='Internet'):
                self.fields['campus'].widget.attrs['class'] += ' is-invalid'
                valid = False

        # stop time > start time
        if self.cleaned_data['start_time'] > self.cleaned_data['stop_time']:
            self._errors['Time'] = 'Invalid start and stop time.'
            self.fields['start_time'].widget.attrs['class'] += ' is-invalid'
            self.fields['stop_time'].widget.attrs['class'] += ' is-invalid'
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
        fields = ['first_name', 'last_name', 'hiring_status']

    def __init__(self, *args, **kwargs):
        super(InstructorForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(InstructorForm, self).clean()

        first_name = cleaned_data['first_name']
        last_name = cleaned_data['last_name']
        hiring_status = cleaned_data['hiring_status']

        matching_instructors = Instructor.objects.filter(
            first_name=first_name, last_name=last_name, hiring_status=hiring_status
        )
        if self.instance:
            matching_instructors = matching_instructors.exclude(
                pk=self.instance.pk)
        if matching_instructors:
            msg = f'Instructor {first_name} {last_name} already exists.'
            self._errors['duplicate'] = msg
            raise ValidationError(msg)
        else:
            return cleaned_data


class SubjectForm(forms.ModelForm):

    SUBJECT_CHOICES = [(str(s.id), s.name) for s in Subject.objects.all()]

    subjects = forms.MultipleChoiceField(choices=SUBJECT_CHOICES,
                                         widget=ModelSelect2MultipleWidget(
                                             queryset=Subject.objects.all(),
                                             search_fields=['name__icontains'],
                                         ), required=False)

    class Meta:
        model = Profile
        fields = ('subjects',)
