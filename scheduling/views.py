from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.db.models.query import EmptyQuerySet

import pandas as pd
import csv

from .forms import CourseForm, ScheduleForm, InstructorForm, SubjectForm
from .models import Course, Schedule, Instructor, Term, Cams, Campus, Location
from main.models import Profile, Subject

from datetime import datetime


def get_curr_and_past_terms():

    curr_terms = Term.objects.filter(
        active__exact="T").order_by('-year', 'semester')
    past_terms = Term.objects.filter(year__gte=datetime.now(
    ).year - 2, active__exact="F").order_by('-year', 'semester')

    return past_terms, curr_terms


def df_to_obj_list(df):

    obj_list = []
    notes_list = []
    source_list = []

    if len(df) > 0:
        for _, row in df.iterrows():
            term = Term.objects.get(pk=row['term_id'])
            course = Course.objects.get(pk=row['course_id'])
            section = row['section']
            capacity = row['capacity']
            instructor = Instructor.objects.get(
                pk=row['instructor_id']) if row['instructor_id'] else None
            status = row['status']
            campus = Campus.objects.get(
                pk=row['campus_id']) if row['campus_id'] else None
            location = Location.objects.get(
                pk=row['location_id']) if row['location_id'] else None
            days = row['days']
            start_time = row['start_time']
            stop_time = row['stop_time']

            notes = row['notes']
            notes_list.append(notes)

            source = 'GCIS' if row['_merge'] == 'left_only' else 'CAMS'
            source_list.append(source)

            obj_list.append(Cams(term=term, course=course, section=section, capacity=capacity, instructor=instructor,
                                 status=status, campus=campus, location=location, days=days, start_time=start_time, stop_time=stop_time))

    return obj_list, notes_list, source_list


def get_diff_gcis_cams(course_list):

    changed = zip([], [], [])
    added = zip([], [], [])
    deleted = zip([], [], [])

    total_changes = 0

    if course_list:

        schedules_gcis = pd.DataFrame.from_records(Schedule.objects.filter(course__in=course_list).all().values(
            'term_id', 'course_id', 'section', 'capacity', 'instructor_id', 'status', 'campus_id', 'location_id', 'days', 'start_time', 'stop_time', 'notes'))

        schedules_cams = pd.DataFrame.from_records(Cams.objects.filter(course__in=course_list).all().values(
            'term_id', 'course_id', 'section', 'capacity', 'instructor_id', 'status', 'campus_id', 'location_id', 'days', 'start_time', 'stop_time'))

        # merge two schedules
        schedules = schedules_gcis.merge(
            schedules_cams, how='outer', on=['term_id', 'course_id', 'section', 'capacity', 'instructor_id',
                                             'status', 'campus_id', 'location_id', 'days', 'start_time', 'stop_time'], indicator=True)

        not_in_both = schedules.loc[schedules['_merge'] != 'both']
        not_in_both.reset_index(drop=True, inplace=True)
        # change nan to None
        not_in_both = not_in_both.where(pd.notnull(not_in_both), None)

        # left is GCIS, right is CAMS
        grouped = not_in_both.groupby(['term_id', 'course_id', 'section'])

        _changed = grouped.filter(lambda x: x['_merge'].count() == 2)
        changed_schedules, changed_notes, changed_sources = df_to_obj_list(
            _changed)
        changed = zip(changed_schedules, changed_notes, changed_sources)

        added = not_in_both.loc[not_in_both['_merge'] == 'left_only']
        added = added[~added.index.isin(list(_changed.index))]
        added_schedules, added_notes, added_sources = df_to_obj_list(added)
        added = zip(added_schedules, added_notes, added_sources)

        deleted = not_in_both.loc[not_in_both['_merge'] == 'right_only']
        deleted = deleted[~deleted.index.isin(list(_changed.index))]
        deleted_schedules, deleted_notes, deleted_sources = df_to_obj_list(
            deleted)
        deleted = zip(deleted_schedules, deleted_notes, deleted_sources)

        total_changes = len(not_in_both)

    return changed, added, deleted, total_changes


#------------------------ Home --------------------------#
@login_required(login_url='/login')
def home(request):
    """List all schedules if not login.
    """

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

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
def instructors(request):

    instructor_list = Instructor.objects.all()

    past_terms, curr_terms = get_curr_and_past_terms()

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


# @login_required(login_url='/login')
# def edit_course(request, pk):

#     past_terms, curr_terms = get_curr_and_past_terms()

#     course = get_object_or_404(Course, pk=pk)
#     form = CourseForm(instance=course)
#     if request.method == 'POST':
#         form = CourseForm(request.POST, instance=course)
#         if form.is_valid():
#             subject = form.cleaned_data['subject']
#             number = form.cleaned_data['number']
#             credit = form.cleaned_data['credit']
#             name = form.cleaned_data['name']

#             course = form.save(commit=False)
#             course.subject = subject
#             course.number = number
#             course.credit = credit
#             course.name = name.upper()
#             course.save()
#             messages.success(
#                 request, f"You've updated {subject}{number} successfully!")
#             return redirect('courses')
#         else:
#             for code, error in form._errors.items():
#                 if code == 'duplicate':
#                     messages.error(request, error)
#     return render(request, 'scheduling/edit_course.html',
#                   {'form': form, 'course': course, 'curr_terms': curr_terms, 'past_terms': past_terms})


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
    form.fields['term'].initial = term

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

    course = schedule.course
    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []

    form = ScheduleForm(instance=schedule)

    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)

        if form.is_valid():
            section = form.cleaned_data['section']

            schedule = form.save(commit=False)
            schedule.update_by = request.user
            schedule.save()
            messages.success(
                request, f"You've updated {course} {section} successfully!")
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
            section = form.cleaned_data['section']
            schedule.delete()
            messages.success(
                request, f"You've deleted {course} {section} successfully!")
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
def schedule_summary(request):

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    # selected subjects
    # by Term
    # return a schedule list too

    past_terms, curr_terms = get_curr_and_past_terms()

    return render(request, 'scheduling/schedule_summary.html', {'curr_terms': curr_terms, 'past_terms': past_terms})


@login_required(login_url='/login')
def change_summary(request):

    past_terms, curr_terms = get_curr_and_past_terms()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

    changed, added, deleted, total_changes = get_diff_gcis_cams(course_list)

    return render(request, 'scheduling/change_summary.html', {'curr_terms': curr_terms, 'past_terms': past_terms,
                                                              'changed': changed, 'added': added, 'deleted': deleted,
                                                              'total_changes': total_changes
                                                              })


@login_required(login_url='/login')
def download_change_summary(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="schedule-changes.csv"'

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = Subject.objects.filter(
            name__in=[x for x in profile.subjects.split(',')])
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

    changed, added, deleted, _ = get_diff_gcis_cams(course_list)

    # write data to csv file so that user can download
    writer = csv.writer(response)

    writer.writerow(['Term', 'Course', 'Name', 'Section', 'Status', 'Capacity', 'Instructor',
                     'Campus', 'Location', 'Days', 'Start', 'Stop', 'Note', 'Source', 'Action'])
    for s, n, src in added:
        writer.writerow([s.term, s.course, s.course.name, s.section, s.status, s.capacity, s.instructor,
                         s.campus, s.location, s.days, s.start_time, s.stop_time, n, src, 'ADD'])

    for s, n, src in deleted:
        writer.writerow([s.term, s.course, s.course.name, s.section, s.status, s.capacity, s.instructor,
                         s.campus, s.location, s.days, s.start_time, s.stop_time, n, src, 'DELETE'])

    for s, n, src in changed:
        writer.writerow([s.term, s.course, s.course.name, s.section, s.status, s.capacity, s.instructor,
                         s.campus, s.location, s.days, s.start_time, s.stop_time, n, src, 'CHANGE'])

    return response
