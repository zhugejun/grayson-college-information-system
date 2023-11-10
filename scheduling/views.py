from datetime import datetime
from collections import defaultdict
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Count

import pandas as pd
import numpy as np
import csv
from zoneinfo import ZoneInfo

from .forms import ScheduleForm, SubjectForm, SearchForm, SearchBySubjectForm
from .models import Course, Dates, Schedule, Instructor, Term, Cams
from main.models import Profile

ITEMS_PER_COLUMN = 10
MAX_NUMBER_OF_DELETED_ITEMS = 8

def list_to_lol(items, items_per_list=10):
    """convert list to a list of list, with items_per_list for each"""
    if len(items) <= items_per_list: 
        return [items]
    return [items[(i*items_per_list):min(len(items), (i+1)*items_per_list)] for i in range(len(items)//items_per_list+1)]


# ------------------------ Home --------------------------#
@login_required
def home(request):
    """List all schedules if not login.
    """
    context = {}

    dates_list = Dates.objects.all()
    if dates_list.count() > 0:
        dates = dates_list[0]
    else:
        dates = None
    context["dates"] = dates

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    subject_choices = [(subject, subject) for subject in subject_list]
    form1 = SearchBySubjectForm(subject_choices)
    form1.fields["term"].queryset = Term.objects.filter(active="T")

    course_list = Course.objects.filter(subject__in=subject_list).order_by("subject", "number")

    form = SearchForm()
    form.fields["term"].queryset = Term.objects.filter(active="T")
    form.fields["course"].queryset = course_list

    context["form"] = form
    context["form1"] = form1

    return render(request, "scheduling/home.html", context)


@login_required
def search(request):
    # scheduling/schedules/search/?term=1&course=1&section=A01&page=1

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    hide_add_button = False
    show_course = False
    subject_only = False
    context = {}

    term_pk = request.GET.get("term")
    term = get_object_or_404(Term, pk=term_pk)
    context["term_pk"] = term_pk
    context["term"] = term

    subject = request.GET.get("subject")
    course_pk = request.GET.get("course")
    instructor_pk = request.GET.get("instructor")

    if subject:
        context["subject"] = subject
        hide_add_button = True
        show_course = True
        subject_only = True
        schedule_list = Schedule.objects.filter(
            term=term, course__subject=subject
        ).order_by("course", "section")
    
    if course_pk:
        course = get_object_or_404(Course, pk=course_pk)
        context["course_pk"] = course_pk

        section = request.GET.get("section")
        context["course"] = course
        context["section"] = section

        schedule_list = Schedule.objects.filter(term=term, course=course, is_deleted=False)
        if section:
            schedule_list = schedule_list.filter(section=section)

    if instructor_pk:
        context["instructor_pk"] = instructor_pk
        try:
            instructor = Instructor.objects.get(pk=instructor_pk)
            schedule_list = Schedule.objects.filter(
                term=term, instructor=instructor, course__subject__in=subject_list
            ).order_by("course", "section")
        except Instructor.DoesNotExist:
            schedule_list = Schedule.objects.filter(
                term=term, instructor__isnull=True, course__subject__in=subject_list
            ).order_by("course", "section")
        hide_add_button = True
        show_course = True
    context["hide_add_button"] = hide_add_button
    context["show_course"] = show_course
    context["subject_only"] = subject_only
    context["schedule_list"] = schedule_list

    return render(request, "scheduling/search.html", context)


@login_required
def update_subjects(request):

    profile = get_object_or_404(Profile, user=request.user)

    if profile.subjects:
        profile.subjects = profile.subjects.split(",")
    else:
        profile.subjects = []

    # form for GET method
    form = SubjectForm(instance=profile)

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user_id = request.user.id
            form.save()
            messages.success(request, "Subjects updated successfully.")
            return redirect("scheduling_home")
    return render(request, "scheduling/update_subjects.html", {"form": form})


# ------------------------ Course --------------------------#
@login_required
def courses_with_term(request, term):

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # term
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)
    context = {"course_list": course_list}

    return render(request, "scheduling/courses_with_term.html", context)


# ------------------------ Schedule --------------------------#
@login_required
def duplicate_schedule(request, pk):

    schedule = get_object_or_404(Schedule, pk=pk)
    new_schedule = schedule
    new_schedule.pk = None
    if new_schedule.days:
        new_schedule.days = list(new_schedule.days)
    else:
        schedule.days = []

    schedule = new_schedule

    form = ScheduleForm(instance=new_schedule)

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=new_schedule)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.insert_by = request.user
            schedule.update_by = None
            term_pk = schedule.term.id
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} added.")
            prev_url = request.POST.get("next")
            return HttpResponseRedirect(prev_url)
        else:
            for field_name, _ in form.errors.items():
                form.fields[field_name].widget.attrs["class"] += " is-invalid"

    return render(
        request,
        "scheduling/duplicate_schedule.html",
        context={"schedule": schedule, "form": form},
    )


@login_required
def add_new_schedule(request, term_pk, crs_pk):

    term = get_object_or_404(Term, pk=term_pk)
    course = get_object_or_404(Course, pk=crs_pk)

    form = ScheduleForm()
    form.fields["term"].initial = term
    form.fields["course"].initial = course
    form.fields["days"].initial = []
    form.fields["capacity"].initial = 1

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            term_pk = schedule.term.id
            schedule.insert_by = request.user
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} added.")
            prev_url = request.POST.get("next")
            return HttpResponseRedirect(prev_url)
        else:
            for field_name, _ in form.errors.items():
                form.fields[field_name].widget.attrs["class"] += " is-invalid"

    return render(
        request,
        "scheduling/add_new_schedule.html",
        context={"term": term, "course": course, "form": form},
    )


@login_required
def edit_schedule(request, pk):

    schedule = get_object_or_404(Schedule, pk=pk)

    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []

    form = ScheduleForm(instance=schedule)

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.update_by = request.user
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} updated.")
            prev_url = request.POST.get("next")
            return HttpResponseRedirect(prev_url)
        else:
            for field_name, _ in form.errors.items():
                form.fields[field_name].widget.attrs["class"] += " is-invalid"
    return render(
        request,
        "scheduling/edit_schedule.html",
        context={"schedule": schedule, "form": form},
    )


@login_required
def delete_schedule(request, pk):

    context = {}

    schedule = get_object_or_404(Schedule, pk=pk)
    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []
    context["schedule"] = schedule

    form = ScheduleForm(instance=schedule)
    context["form"] = form
    for field_name, _ in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        for field_name, _ in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            schedule.deleted_by = request.user
            schedule.soft_delete()
            messages.success(request, f"{schedule}-{schedule.term} deleted.")
            prev_url = request.POST.get("next")
            return HttpResponseRedirect(prev_url)
    return render(request, "scheduling/delete_schedule.html", context)


@login_required
def restore_schedule(request, pk):

    context = {}
    schedule = get_object_or_404(Schedule, pk=pk)

    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []
    context["schedule"] = schedule

    form = ScheduleForm(instance=schedule)
    context["form"] = form
    for field_name, _ in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        for field_name, _ in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            schedule.update_by = request.user
            schedule.update_date = datetime.now()
            schedule.deleted_by = None
            schedule.restore()
            messages.success(request, f"{schedule}-{schedule.term} restored.")
            prev_url = request.POST.get("next")
            return HttpResponseRedirect(prev_url)
    return render(request, "scheduling/restore_schedule.html", context)


@login_required
def schedule_summary(request):

    curr_terms = Term.objects.filter(active__exact="T").order_by("-year", "semester")
    return render(request, "scheduling/schedule_summary.html", {"curr_terms": curr_terms})


@login_required
def schedule_summary_by_term(request, term):

    context = {}
    search_url = reverse("search")
    context['search_url'] = search_url

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    year = int(term[-4:])
    semester = term[:-4].upper()
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)
    schedules = Schedule.objects.filter(term=term, course__in=course_list)
    context["term"] = term

    count_by_course = Course.objects.filter(schedule__term=term, schedule__course__in=course_list).annotate(num_sections=Count("schedule")).order_by("-num_sections")
    if count_by_course.count() < 1:
        context['count_by_course_list'] = None
    else:
        context['count_by_course_list'] = list_to_lol(count_by_course, ITEMS_PER_COLUMN)

    count_by_instructor = Instructor.objects.filter(schedule__term=term, schedule__course__in=course_list).annotate(num_sections=Count("schedule")).order_by("-num_sections")
    if count_by_instructor.count() < 1:
        context['count_by_instructor_list'] = None
    else:
        context['count_by_instructor_list'] = list_to_lol(count_by_instructor, ITEMS_PER_COLUMN)

    instructor_not_assigned_count = schedules.filter(instructor__isnull=True).count()
    context['instructor_not_assigned_count'] = instructor_not_assigned_count

    # schedules grouped by instructor and start time
    schedules_by_instructor_start = defaultdict(set)
    # schedules grouped by location and start time
    schedules_by_location_start = defaultdict(set)
    for s in schedules:
        for d in "MTWRFSU":
            if s.days and d in list(s.days):
                schedules_by_instructor_start[(s.instructor, d, s.start_time)].add(s)
                if "NT" not in s.section:
                    schedules_by_location_start[(s.location, d, s.start_time)].add(s)

    count_by_instructor_start = [(key, sections) for key, sections in schedules_by_instructor_start.items() if len(sections) > 1 and all(key)]
    if not count_by_instructor_start:
        context['count_by_instructor_start_list'] = None
    else:
        count_by_instructor_start_list = list_to_lol(count_by_instructor_start, ITEMS_PER_COLUMN)
        context['count_by_instructor_start_list'] = count_by_instructor_start_list
        


    count_by_location_start = [(key, sections) for key, sections in schedules_by_location_start.items() if len(sections) > 1 and all(key)]
    if not count_by_instructor_start:
        context['count_by_location_start_list'] = None
    else:
        count_by_location_start_list = list_to_lol(count_by_location_start, ITEMS_PER_COLUMN)
        context['count_by_location_start_list'] = count_by_location_start_list

    return render(request, "scheduling/schedule_summary_by_term.html", context)


@login_required
def recent(request):
    context = {}

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

    latest_edited = Schedule.objects.filter(
        update_by=request.user, course__in=course_list
    ).exclude(deleted_by=request.user)
    n_edited = min(len(latest_edited), MAX_NUMBER_OF_DELETED_ITEMS)
    latest_edited = latest_edited.order_by("-update_date")[:n_edited]
    context["latest_edited"] = latest_edited

    latest_added = Schedule.objects.filter(
        insert_by=request.user, course__in=course_list
    ).exclude(update_by=request.user).exclude(deleted_by=request.user)
    n_added = min(len(latest_added), MAX_NUMBER_OF_DELETED_ITEMS)
    latest_added = latest_added.order_by("-insert_date")[:n_added]
    context["latest_added"] = latest_added

    latest_deleted = Schedule.objects.filter(
        is_deleted=True, deleted_by=request.user, course__in=course_list
    )
    n_deleted = min(len(latest_deleted), MAX_NUMBER_OF_DELETED_ITEMS)
    latest_deleted = latest_deleted.order_by("-deleted_at")[:n_deleted]
    context["latest_deleted"] = latest_deleted

    return render(request, "scheduling/recent.html", context)


@login_required
def change_summary(request):

    curr_terms = Term.objects.filter(active__exact="T").order_by("-year", "semester")

    academic_years = defaultdict(list)
    for term in curr_terms:
        yr = term.year
        sm = term.semester
        if sm == "FALL":
            academic_year = f"{yr}-{yr+1}"
            academic_years[academic_year].append(term)
        else:
            academic_year = f"{yr-1}-{yr}"
            academic_years[academic_year].append(term)
    
    for ay in academic_years:
        academic_years[ay].sort(key=lambda t: t.semester)

    return render(request, "scheduling/change_summary.html", {"academic_years": dict(academic_years)})


@login_required
def change_summary_by_term(request, term):

    context = {}

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    year = int(term[-4:])
    semester = term[:-4].upper()
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)

    context["term"] = term
    course_list = Course.objects.filter(subject__in=subject_list)

    gcis_changed, cams_changed, added, deleted, total_changes = get_diff_gcis_cams(term, course_list)
    
    if added:
        added.sort(key=lambda s: (s.course.__str__(), s.course.name, s.section))
    if deleted:
        deleted.sort(key=lambda s: (s.course.__str__(), s.course.name, s.section))
    

    # it has to be a dict for changed_combined, otherwise it will be shown in the template
    changed_combined = {}
    for s in gcis_changed:
        if (s.course, s.section) not in changed_combined:
            changed_combined[(s.course, s.section)] = defaultdict(list)
        changed_combined[(s.course, s.section)]["gcis"].append(s)

    for s in cams_changed:
        changed_combined[(s.course, s.section)]["cams"].append(s)

    
    gcis_changed_cols = defaultdict(list) 
    cams_changed_cols = defaultdict(list)

    for _, val_dict in changed_combined.items():
        for gcis in val_dict["gcis"]:
            for cams in val_dict["cams"]:
                if gcis.status != cams.status:
                    gcis_changed_cols['status'].append(gcis.id)
                    cams_changed_cols['status'].append(cams.id)
                if gcis.status not in ["CANCELED", "CLOSED"]:
                    if gcis.capacity != cams.capacity:
                        gcis_changed_cols['capacity'].append(gcis.id)
                        cams_changed_cols['capacity'].append(cams.id)
                    if gcis.instructor != cams.instructor:
                        gcis_changed_cols['instructor'].append(gcis.id)
                        cams_changed_cols['instructor'].append(cams.id)
                    if gcis.campus != cams.campus:
                        gcis_changed_cols['campus'].append(gcis.id)
                        cams_changed_cols['campus'].append(cams.id)
                    if gcis.location != cams.location:
                        gcis_changed_cols['location'].append(gcis.id)
                        cams_changed_cols['location'].append(cams.id)
                    if cams.days and cams.days and gcis.days != cams.days:
                        gcis_changed_cols['days'].append(gcis.id)
                        cams_changed_cols['days'].append(cams.id)
                    if gcis.start_time != cams.start_time:
                        gcis_changed_cols['start_time'].append(gcis.id)
                        cams_changed_cols['start_time'].append(cams.id)
                    if gcis.stop_time != cams.stop_time:
                        gcis_changed_cols['stop_time'].append(gcis.id)
                        cams_changed_cols['stop_time'].append(cams.id)

    context['gcis_changed_cols'] = gcis_changed_cols 
    context['cams_changed_cols'] = cams_changed_cols 
    context["changed_combined"] = changed_combined
    context["added"] = added
    context["deleted"] = deleted
    context["total_changes"] = total_changes

    return render(request, "scheduling/change_summary_by_term.html", context)


def get_diff_gcis_cams(term, course_list):

    total_changes = 0
    gcis_changed, cams_changed, added, deleted = [], [], [], []
    
    if term and course_list:

        # get active schedules from GCIS
        schedules_gcis = pd.DataFrame.from_records(
            Schedule.objects.filter(course__in=course_list, term=term, is_deleted=False)
            .all()
            .values(
                "id",
                "term_id",
                "course_id",
                "section",
                "capacity",
                "instructor_id",
                "status",
                "campus_id",
                "location_id",
                "days",
                "start_time",
                "stop_time",
            )
        )
        schedules_gcis.rename(columns={"id": "gcis_id"}, inplace=True)

        # get all schedules from CAMS
        schedules_cams = pd.DataFrame.from_records(
            Cams.objects.filter(course__in=course_list, term=term)
            .all()
            .values(
                "id",
                "term_id",
                "course_id",
                "section",
                "capacity",
                "instructor_id",
                "status",
                "campus_id",
                "location_id",
                "days",
                "start_time",
                "stop_time",
            )
        )
        schedules_cams.rename(columns={"id": "cams_id"}, inplace=True)

        # if both empty, no changes
        if schedules_gcis.empty and schedules_cams.empty:
            return gcis_changed, cams_changed, added, deleted, total_changes

        # if gcis is empty, delete all schedules in CAMS
        if schedules_gcis.empty:
            for _id in schedules_cams["cams_id"].values:
                deleted.append(Cams.objects.get(pk=_id))
            return gcis_changed, cams_changed, added, deleted, total_changes        

        # clean up and get ready to merge
        schedules_gcis.replace("", np.nan, inplace=True)
        # days cannot be float type
        schedules_gcis.days.replace(np.nan, None, inplace=True)

        # change null to None, replace values where condition is False
        schedules_gcis = schedules_gcis.where(pd.notnull(schedules_gcis), None)
        schedules_cams = schedules_cams.where(pd.notnull(schedules_cams), None)

        # make id an int64
        schedules_gcis["gcis_id"] = schedules_gcis["gcis_id"].astype("Int64")
        schedules_cams["cams_id"] = schedules_cams["cams_id"].astype("Int64")


        # fix the error casused by N/A in a character column
        for col in [
            "term_id",
            "course_id",
            "capacity",
            "instructor_id",
            "campus_id",
            "location_id",
        ]:
            schedules_cams[col] = schedules_cams[col].astype("Int64")
            schedules_gcis[col] = schedules_gcis[col].astype("Int64")

        
        # merge two schedules
        merged = schedules_gcis.merge(
            schedules_cams,
            how="outer",
            on=[
                "term_id",
                "course_id",
                "section",
                "capacity",
                "instructor_id",
                "status",
                "campus_id",
                "location_id",
                "days",
                "start_time",
                "stop_time",
            ],
            indicator=True,
        )


        not_in_both = merged.loc[merged["_merge"] != "both"]
        not_in_both.reset_index(drop=True, inplace=True)
        total_changes = len(not_in_both)

        # change nan to None
        not_in_both = not_in_both.where(pd.notnull(not_in_both), None)

        # left is GCIS, right is CAMS
        grouped = not_in_both.groupby(["term_id", "course_id", "section"])

        # changed, there could be duplicated sections for one schedule
        _changed = grouped.filter(lambda x: x["_merge"].count() >= 2)

        # if both canceled or closed, these is no need to compare the rest
        _both_canceled = (
            _changed.loc[_changed["status"] == "CANCELED"]
            .groupby(["term_id", "course_id", "section"])
            .filter(lambda x: x["section"].count() == 2)
        )

        _both_closed = (
            _changed.loc[_changed["status"] == "CLOSED"]
            .groupby(["term_id", "course_id", "section"])
            .filter(lambda x: x["section"].count() == 2)
        )

        _changed = _changed[~_changed.index.isin(list(_both_canceled.index))]
        _changed = _changed[~_changed.index.isin(list(_both_closed.index))]
        gcis_cids = _changed.loc[_changed["_merge"] == "left_only"]["gcis_id"].values
        cams_cids = _changed.loc[_changed["_merge"] == "right_only"]["cams_id"].values
        
        for _id in gcis_cids:
            gcis_changed.append(Schedule.objects.get(pk=_id))
        for _id in cams_cids:
            cams_changed.append(Cams.objects.get(pk=_id))

        # added
        _added = not_in_both.loc[not_in_both["_merge"] == "left_only"]
        _added = _added[
            ~_added.index.isin(
                list(_changed.index)
                + list(_both_canceled.index)
                + list(_both_closed.index)
            )
        ]

        added = []
        for _id in _added["gcis_id"].values:
            added.append(Schedule.objects.get(pk=_id))

        # if a course is canceled in the added section, then it was deleted in CAMS
        # it is safe to hide them, but better to reset the database
        # added = added.loc[added['status'] not in ['CANCELED', 'CLOSED']]


        # deleted
        _deleted = not_in_both.loc[not_in_both["_merge"] == "right_only"]
        _deleted = _deleted[
            ~_deleted.index.isin(
                list(_changed.index)
                + list(_both_canceled.index)
                + list(_both_closed.index)
            )
        ]

        # marked as deleted in GCIS
        deleted = Schedule.objects.filter(term=term, course__in=course_list, is_deleted=True, status__in=["OPEN"])

        schedule_not_existing_in_CAMS = []
        for schedule in deleted:
            term = schedule.term
            course = schedule.course
            section = schedule.section
            in_cams = Cams.objects.filter(term=term, course=course, section=section)
            if not in_cams:
                schedule_not_existing_in_CAMS.append(schedule.pk)
        deleted = list(deleted.exclude(pk__in=schedule_not_existing_in_CAMS))

        for _id in _deleted["cams_id"].values:
            sch = Cams.objects.get(pk=_id)
            deleted.append(Cams.objects.get(pk=_id))

    return gcis_changed, cams_changed, added, deleted, total_changes


def reformat_datetime(dt: datetime):
    if not dt:
        return ""
    dt = dt.astimezone(ZoneInfo("America/Chicago"))
    return dt.strftime("%m/%d/%Y, %H:%M:%S")


@login_required
def download_change_summary_by_term(request, term):

    now = datetime.now().strftime("%m%d%Y")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{term.lower()}-schedule-changes-{now}.csv"'

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # Term
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)

    course_list = Course.objects.filter(subject__in=subject_list)

    gcis_changed, cams_changed, added, deleted, _ = get_diff_gcis_cams(term, course_list)

    # write data to csv file so that user can download
    writer = csv.writer(response)

    writer.writerow(
        [
            "Term",
            "Course",
            "Section",
            "Name",
            "Status",
            "Capacity",
            "Instructor",
            "Campus",
            "Location",
            "Days",
            "Start",
            "Stop",
            "Note",
            "source",
            "Inserted_by",
            "Inserted_date",
            "Updated_by",
            "Updated_date",
            "Deleted_by",
            "Deleted_date",
            "Action",
        ]
    )
    for s in gcis_changed:
        writer.writerow(
            [
                s.term,
                s.course,
                s.section,
                s.course.name,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                s.notes,
                "GCIS",
                s.insert_by,
                reformat_datetime(s.insert_date),
                s.update_by,
                reformat_datetime(s.update_date),
                s.deleted_by,
                reformat_datetime(s.deleted_at),
                "CHANGE"
            ]
        )
    for c in cams_changed:
        writer.writerow(
            [
                c.term,
                c.course,
                c.section,
                c.course.name,
                c.status,
                c.capacity,
                c.instructor,
                c.campus,
                c.location,
                c.days,
                c.start_time,
                c.stop_time,
                "",
                "CAMS",
                "",
                "",
                "",
                "",
                "",
                "",
                "CHANGE"
            ]
        )

    for s in deleted:
        writer.writerow(
            [
                s.term,
                s.course,
                s.section,
                s.course.name,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                s.notes,
                "GCIS",
                s.insert_by,
                reformat_datetime(s.insert_date),
                s.update_by,
                reformat_datetime(s.update_date),
                s.deleted_by,
                reformat_datetime(s.deleted_at),                
                "DELETE",
            ]
        )

    for s in added:
        writer.writerow(
            [
                s.term,
                s.course,
                s.section,
                s.course.name,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                s.notes,
                "GCIS",
                s.insert_by,
                reformat_datetime(s.insert_date),
                s.update_by,
                reformat_datetime(s.update_date),
                s.deleted_by,
                reformat_datetime(s.deleted_at),  
                "ADD",
            ]
        )

    return response
