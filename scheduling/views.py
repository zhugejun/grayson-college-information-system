from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import Q
from django.utils import timezone
from django.db.models.query import EmptyQuerySet

from .forms import CourseForm, ScheduleForm, InstructorForm, SubjectForm
from .models import Course, Schedule, Instructor, Term
from main.models import Profile, Subject

from datetime import datetime


def get_curr_and_past_terms():

    curr_terms = Term.objects.filter(
        active__exact="T").order_by('-year', 'semester')
    past_terms = Term.objects.filter(year__gte=datetime.now(
    ).year - 2, active__exact="F").order_by('-year', 'semester')

    return past_terms, curr_terms


#------------------------ Home --------------------------#

@login_required(login_url='/login')
def home(request):
    """List all schedules if not login.
    """

    curr_user = request.user

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=curr_user)
    if profile.subjects:
        subject_names = [x for x in profile.subjects.split(',')]
        subject_ids = [s.id for s in Subject.objects.filter(
            name__in=subject_names)]
        course_list = Course.objects.filter(pk__in=subject_ids)
    else:
        course_list = []

    schedule_dict = {}

    for term in curr_terms:
        schedules = Schedule.objects.filter(
            term=term, course__in=course_list)
        if len(schedules) > 0:
            schedule_dict[str(term)] = schedules
    return render(request, 'scheduling/home.html', {'curr_terms': curr_terms, 'past_terms': past_terms, 'schedule_dict': schedule_dict})


@login_required(login_url='/login')
def update_subjects(request):

    past_terms, curr_terms = get_curr_and_past_terms()

    curr_user = request.user
    profile = get_object_or_404(Profile, user=request.user)

    if profile.subjects:
        subjects = Subject.objects.filter(
            name__in=profile.subjects.split(','))
        profile.subjects = [s.id for s in subjects]
    else:
        profile.subjects = []

    form = SubjectForm(instance=profile)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)

            _subjects = Subject.objects.filter(
                pk__in=[int(i) for i in request.POST.getlist('subjects')])

            profile.user_id = request.user.id
            profile.subjects = ','.join([s.name for s in _subjects])
            form.save()
            messages.success(request,
                             'You have successfully updated your subjects for scheduling.')
            return redirect('scheduling')
    return render(request, 'scheduling/update_subjects.html',
                  {'form': form, 'curr_terms': curr_terms, 'past_terms': past_terms})


#------------------------ Instructor --------------------------#
@login_required(login_url='/login')
def add_instructor(request):

    past_terms, curr_terms = get_curr_and_past_terms()

    form = InstructorForm()

    if request.method == 'POST':
        form = InstructorForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            hiring_status = form.cleaned_data['hiring_status']

            instructor = form.save(commit=False)
            instructor.first_name = instructor.first_name.title()
            instructor.last_name = instructor.last_name.title()
            instructor.save()
            messages.success(
                request, f"You've added {first_name} {last_name} successfully!")
            return redirect('instructors')
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)

    return render(request, 'scheduling/add_instructor.html',
                  {'form': form, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def edit_instructor(request, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    instructor = get_object_or_404(Instructor, pk=pk)
    form = InstructorForm(instance=instructor)
    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            hiring_status = form.cleaned_data['hiring_status']

            form.save()
            messages.success(
                request, f"You've updated {first_name} {last_name} successfully!")
            return redirect('instructors')
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)

    return render(request, 'scheduling/edit_instructor.html',
                  {'form': form, 'instructor': instructor, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def delete_instructor(request, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    instructor = get_object_or_404(Instructor, pk=pk)
    form = InstructorForm(instance=instructor)
    for field_name, field in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        for field_name, field in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            instructor.delete()
            messages.success(request, f"You've deleted {form.cleaned_data['first_name']} \
                    {form.cleaned_data['last_name']} successfully!")
            return redirect('instructors')
    return render(request, 'scheduling/delete_instructor.html',
                  {'form': form, 'instructor': instructor, 'curr_terms': curr_terms, 'past_terms': past_terms})


def instructors(request):

    instructor_list = Instructor.objects.all()
    curr_terms = Term.objects.filter(
        active__exact="T").order_by('-year', 'semester')
    past_terms = Term.objects.filter(year__gte=datetime.now(
    ).year - 2, active__exact="F").order_by('-year', 'semester')

    return render(request, 'scheduling/instructors.html',
                  {'instructor_list': instructor_list, 'curr_terms': curr_terms, 'past_terms': past_terms})


#------------------- Course ---------------------#
@login_required(login_url='/login')
def add_course(request):
    """Courses to be scheduled
    """
    form = CourseForm()

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []
    subject_ids = [s.id for s in subject_list]

    if request.method == 'POST':
        form = CourseForm(request.POST)
        form.fields['subject'].queryset = Subject.objects.filter(
            pk__in=subject_ids)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            number = form.cleaned_data['number']
            credit = form.cleaned_data['credit']
            name = form.cleaned_data['name']

            course = form.save(commit=False)
            course.subject = subject
            course.number = number
            course.credit = credit
            course.name = name.upper()
            course.save()
            messages.success(
                request, f"You've added {subject}{number} {name} successfully!")
            return redirect('courses')
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)
    form.fields['subject'].queryset = Subject.objects.filter(
        pk__in=subject_ids)
    return render(request, 'scheduling/add_course.html',
                  {'form': form, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def edit_course(request, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(instance=course)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            number = form.cleaned_data['number']
            credit = form.cleaned_data['credit']
            name = form.cleaned_data['name']

            course = form.save(commit=False)
            course.subject = subject
            course.number = number
            course.credit = credit
            course.name = name.upper()
            course.save()
            messages.success(
                request, f"You've updated {subject}{number} successfully!")
            return redirect('courses')
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)
    return render(request, 'scheduling/edit_course.html',
                  {'form': form, 'course': course, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def delete_course(request, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(instance=course)
    for field_name, field in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        for field_name, field in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            course.delete()
            messages.success(request, f"You've deleted {form.cleaned_data['subject']}\
                    {form.cleaned_data['number']}\
                    {form.cleaned_data['name']} successfully!")
            return redirect('courses')
    return render(request, 'scheduling/delete_course.html',
                  {'form': form, 'course': course, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def courses(request):

    past_terms, curr_terms = get_curr_and_past_terms()

    current_user = request.user
    profile = get_object_or_404(Profile, user=current_user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    return render(request, 'scheduling/courses.html',
                  {'course_list': course_list, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def courses_with_term(request, term):

    past_terms, curr_terms = get_curr_and_past_terms()

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # term
    term = get_object_or_404(Term, year__exact=year,
                             semester__exact=semester)

    current_user = request.user
    profile = get_object_or_404(Profile, user=current_user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

    return render(request, 'scheduling/courses_with_term.html',
                  {'course_list': course_list, 'curr_terms': curr_terms, 'past_terms': past_terms, 'term': term})


#------------------------ Schedule --------------------------#
@login_required(login_url='/login')
def add_schedule(request, term, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # term
    term = get_object_or_404(Term, year__exact=year,
                             semester__exact=semester)

    course = get_object_or_404(Course, pk=pk)

    form = ScheduleForm()
    form.fields['course'].initial = course

    try:
        schedule_list = Schedule.objects.filter(
            term=term, course=course)
    except Schedule.DoesNotExist:
        schedule_list = []

    if request.method == 'POST':
        form = ScheduleForm(request.POST)

        if form.is_valid():
            section = form.cleaned_data['section']

            schedule = form.save(commit=False)
            schedule.course_id = course.id
            schedule.term_id = term.id
            schedule.insert_by = request.user
            schedule.save()
            messages.success(
                request, f"You've added {schedule.course} {section} successfully!")
            return redirect('schedules', term=term)
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)

    return render(request, 'scheduling/add_schedule.html',
                  {'form': form, 'course': course, 'schedule_list': schedule_list,
                   'curr_terms': curr_terms, 'past_terms': past_terms, 'term': term})


@login_required(login_url='/login')
def edit_schedule(request, term, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # term
    term = get_object_or_404(Term, year__exact=year,
                             semester__exact=semester)

    schedule = get_object_or_404(Schedule, pk=pk)
    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []
    form = ScheduleForm(instance=schedule)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.update_by = request.user
            schedule.save()
            messages.success(
                request, f"You've updated {str(schedule.course).split(' - ')[0]} {form.cleaned_data['section']} successfully!")
            return redirect('schedules', term=term)
        else:
            for code, error in form._errors.items():
                if code == 'duplicate':
                    messages.error(request, error)
    return render(request, 'scheduling/edit_schedule.html', {'form': form, 'schedule': schedule, 'curr_terms': curr_terms, 'past_terms': past_terms, 'term': term})


@login_required(login_url='/login')
def delete_schedule(request, term, pk):

    past_terms, curr_terms = get_curr_and_past_terms()

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # term
    term = get_object_or_404(Term, year__exact=year,
                             semester__exact=semester)

    schedule = get_object_or_404(Schedule, pk=pk)
    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []
    course = get_object_or_404(Course, pk=schedule.course_id)

    form = ScheduleForm(instance=schedule)
    for field_name, field in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        for field_name, field in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            schedule.delete()
            messages.success(request, f"You've deleted {course.subject}{course.number}\
                    {form.cleaned_data['section']} successfully!")
            return redirect('schedules', term=term)
    return render(request, 'scheduling/delete_schedule.html', {'form': form, 'course': course, 'schedule': schedule, 'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def schedules(request, term):

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # Term
    term = get_object_or_404(Term, year__exact=year,
                             semester__exact=semester)
    schedule_list = Schedule.objects.filter(
        term=term, course__in=course_list)

    return render(request, 'scheduling/schedules.html', {'schedule_list': schedule_list, 'curr_terms': curr_terms, 'past_terms': past_terms, 'term': term})


@login_required(login_url='/login')
def change_summary(request):

    # selected subjects
    # by Term
    # return a schedule list too

    # addition - list
    # deletion - list
    # changes - list, two rows for each schedule

    past_terms, curr_terms = get_curr_and_past_terms()

    return render(request, 'scheduling/change_summary.html', {'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def schedule_summary(request):

    # selected subjects
    # by Term
    # return a schedule list too

    # addition - list
    # deletion - list
    # changes - list, two rows for each schedule

    past_terms, curr_terms = get_curr_and_past_terms()

    return render(request, 'scheduling/schedule_summary.html', {'curr_terms': curr_terms, 'past_terms': past_terms})
