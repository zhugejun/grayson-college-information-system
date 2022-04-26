from collections import defaultdict
from itertools import count
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Count

import pandas as pd
import numpy as np
import csv

from .forms import ScheduleForm, SubjectForm, SearchForm, SearchBySubjectForm
from .models import Course, Schedule, Instructor, Term, Cams, Campus, Location
from main.models import Profile

ITEMS_PER_COLUMN = 10

def list_to_lol(items, items_per_list=10):
    """convert list to a list of list, with items_per_list for each"""
    if len(items) <= items_per_list: 
        return [items]
    return [items[(i*items_per_list):min(len(items), (i+1)*items_per_list)] for i in range(len(items)//items_per_list+1)]

def df_to_obj_list(df):

    obj_list = []
    insert_by_list = []
    insert_date_list = []
    updated_by_list = []
    updated_date_list = []
    notes_list = []
    source_list = []

    if len(df) > 0:
        for _, row in df.iterrows():
            term = Term.objects.get(pk=row["term_id"])
            course = Course.objects.get(pk=row["course_id"])
            section = row["section"]
            capacity = row["capacity"]
            instructor = (
                Instructor.objects.get(pk=row["instructor_id"])
                if pd.notnull(row["instructor_id"])
                else None
            )
            status = row["status"]
            campus = (
                Campus.objects.get(pk=row["campus_id"])
                if pd.notnull(row["campus_id"])
                else None
            )
            location = (
                Location.objects.get(pk=row["location_id"])
                if pd.notnull(row["location_id"])
                else None
            )
            days = row["days"] if row["days"] else None
            start_time = row["start_time"]
            stop_time = row["stop_time"]

            user_id = row["insert_by"]
            insert_by = User.objects.get(pk=user_id) if not pd.isna(user_id) else ""
            insert_by_list.append(insert_by)
            insert_date_list.append(row["insert_date"])

            user_id = row["update_by"]
            updated_by = User.objects.get(pk=user_id) if not pd.isna(user_id) else ""
            updated_by_list.append(updated_by)
            updated_date_list.append(row["update_date"])

            notes = row["notes"]
            notes_list.append(notes)

            source = "GCIS" if row["_merge"] == "left_only" else "CAMS"
            source_list.append(source)

            obj_list.append(
                Cams(
                    term=term,
                    course=course,
                    section=section,
                    capacity=capacity,
                    instructor=instructor,
                    status=status,
                    campus=campus,
                    location=location,
                    days=days,
                    start_time=start_time,
                    stop_time=stop_time,
                )
            )

    return (
        obj_list,
        notes_list,
        source_list,
        insert_by_list,
        insert_date_list,
        updated_by_list,
        updated_date_list,
    )


def get_diff_gcis_cams(term, course_list):

    changed = zip([], [], [])
    added = zip([], [], [])
    deleted = zip([], [], [])

    total_changes = 0

    if course_list:

        schedules_gcis = pd.DataFrame.from_records(
            Schedule.objects.filter(course__in=course_list, term=term)
            .all()
            .values(
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
                "insert_by",
                "insert_date",
                "update_by",
                "update_date",
                "notes",
            )
        )
        schedules_gcis.replace("", np.nan, inplace=True)
        # days cannot be float type
        schedules_gcis.days.replace(np.nan, None, inplace=True)

        schedules_cams = pd.DataFrame.from_records(
            Cams.objects.filter(course__in=course_list, term=term)
            .all()
            .values(
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

        if schedules_gcis.empty and schedules_cams.empty:
            return changed, added, deleted, total_changes

        schedules_gcis = schedules_gcis.where(pd.notnull(schedules_gcis), None)
        schedules_cams = schedules_cams.where(pd.notnull(schedules_cams), None)

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

        for col in ["update_by", "insert_by"]:
            schedules_gcis[col] = schedules_gcis[col].astype("Int64")

        # merge two schedules
        schedules = schedules_gcis.merge(
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

        not_in_both = schedules.loc[schedules["_merge"] != "both"]
        not_in_both.reset_index(drop=True, inplace=True)

        # change nan to None
        not_in_both = not_in_both.where(pd.notnull(not_in_both), None)

        # left is GCIS, right is CAMS
        grouped = not_in_both.groupby(["term_id", "course_id", "section"])

        _changed = grouped.filter(lambda x: x["_merge"].count() == 2)

        # if both canceled, these is no need to compare the rest
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

        (
            changed_schedules,
            changed_notes,
            changed_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        ) = df_to_obj_list(_changed)
        changed = zip(
            changed_schedules,
            changed_notes,
            changed_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        )

        # added
        added = not_in_both.loc[not_in_both["_merge"] == "left_only"]
        added = added[
            ~added.index.isin(
                list(_changed.index)
                + list(_both_canceled.index)
                + list(_both_closed.index)
            )
        ]
        # if a course is canceled in the added section, then it was deleted in CAMS
        # it is safe to hide them, but better to reset the database
        # added = added.loc[added['status'] not in ['CANCELED', 'CLOSED']]
        (
            added_schedules,
            added_notes,
            added_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        ) = df_to_obj_list(added)
        added = zip(
            added_schedules,
            added_notes,
            added_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        )

        # deleted
        deleted = not_in_both.loc[not_in_both["_merge"] == "right_only"]
        deleted = deleted[
            ~deleted.index.isin(
                list(_changed.index)
                + list(_both_canceled.index)
                + list(_both_closed.index)
            )
        ]
        (
            deleted_schedules,
            deleted_notes,
            deleted_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        ) = df_to_obj_list(deleted)
        deleted = zip(
            deleted_schedules,
            deleted_notes,
            deleted_sources,
            insert_by_list,
            insert_date_list,
            updated_by_list,
            updated_date_list,
        )

        total_changes = len(not_in_both)

    return changed, added, deleted, total_changes


# ------------------------ Home --------------------------#
@login_required
def home(request):
    """List all schedules if not login.
    """
    context = {}
    form = SearchForm()

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    subject_choices = [(subject, subject) for subject in subject_list]
    form1 = SearchBySubjectForm(subject_choices)

    course_list = Course.objects.filter(subject__in=subject_list)

    form.fields["term"].queryset = Term.objects.filter(active="T")
    form.fields["course"].queryset = course_list

    context["form"] = form
    context["form1"] = form1
    latest_edited = Schedule.objects.filter(
        update_by=request.user, course__in=course_list
    )

    n_edited = min(len(latest_edited), 5)
    latest_edited = latest_edited.order_by("-update_date")[:n_edited]
    context["latest_edited"] = latest_edited

    latest_added = Schedule.objects.filter(
        insert_by=request.user, course__in=course_list
    )
    n_added = min(len(latest_added), 5)
    latest_added = latest_added.order_by("-insert_date")[:n_added]
    context["latest_added"] = latest_added

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
        schedule_list = Schedule.objects.filter(
            term=term, course__subject=subject
        ).order_by("course", "section")
    
    if course_pk:
        course = get_object_or_404(Course, pk=course_pk)
        context["course_pk"] = course_pk

        section = request.GET.get("section")
        context["course"] = course
        context["section"] = section

        schedule_list = Schedule.objects.filter(term=term, course=course)
        if section:
            schedule_list = schedule_list.filter(section__startswith=section)

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

    # paginator = Paginator(schedule_list, 25)
    # page_number = request.GET.get("page")

    # if not page_number and schedule_list:
    #     page_number = 1

    # page = paginator.get_page(page_number)
    # context["page"] = page

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

    search_url = reverse("search")

    schedule = get_object_or_404(Schedule, pk=pk)
    new_schedule = schedule
    new_schedule.pk = None
    if new_schedule.days:
        new_schedule.days = list(new_schedule.days)
    else:
        schedule.days = []

    schedule = new_schedule

    term_pk = schedule.term.id
    course_pk = schedule.course.id

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
            return redirect("scheduling_home"
                # search_url + f"?term={term_pk}&course={course_pk}&section="
            )
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

    search_url = reverse("search")

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
            return redirect(
                "scheduling_home"
                # search_url + f"?term={term_pk}&course={crs_pk}&section="
            )
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
    term_pk = schedule.term.id
    course_pk = schedule.course.id

    search_url = reverse("search")

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
            return redirect(
                "scheduling_home"
                # search_url + f"?term={term_pk}&course={course_pk}&section="
            )
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
    term_pk = schedule.term.id
    course_pk = schedule.course.id

    search_url = reverse("search")

    form = ScheduleForm(instance=schedule)
    context["form"] = form
    for field_name, _ in form.fields.items():
        form.fields[field_name].disabled = True

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        for field_name, _ in form.fields.items():
            form.fields[field_name].disabled = True
        if form.is_valid():
            schedule.delete()
            messages.success(request, f"{schedule}-{schedule.term} deleted.")
            return redirect(
                "scheduling_home"
                # search_url + f"?term={term_pk}&course={course_pk}&section="
            )
    return render(request, "scheduling/delete_schedule.html", context)


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
    context['count_by_course_list'] = list_to_lol(count_by_course, ITEMS_PER_COLUMN)

    count_by_instructor = Instructor.objects.filter(schedule__term=term, schedule__course__in=course_list).annotate(num_sections=Count("schedule")).order_by("-num_sections")
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
    count_by_instructor_start_list = list_to_lol(count_by_instructor_start, ITEMS_PER_COLUMN)

    count_by_location_start = [(key, sections) for key, sections in schedules_by_location_start.items() if len(sections) > 1 and all(key)]
    count_by_location_start_list = list_to_lol(count_by_location_start, ITEMS_PER_COLUMN)

    context['count_by_instructor_start_list'] = count_by_instructor_start_list
    context['count_by_location_start_list'] = count_by_location_start_list

    return render(request, "scheduling/schedule_summary_by_term.html", context)


@login_required
def history(request):
    context = {}

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    course_list = Course.objects.filter(subject__in=subject_list)

    latest_edited = Schedule.objects.filter(
        update_by=request.user, course__in=course_list
    )

    n_edited = min(len(latest_edited), 10)
    latest_edited = latest_edited.order_by("-update_date")[:n_edited]
    context["latest_edited"] = latest_edited

    latest_added = Schedule.objects.filter(
        insert_by=request.user, course__in=course_list, update_by__isnull=True
    )
    n_added = min(len(latest_added), 10)
    latest_added = latest_added.order_by("-insert_date")[:n_added]
    context["latest_added"] = latest_added

    return render(request, "scheduling/history.html", context)


@login_required
def change_summary(request):

    curr_terms = Term.objects.filter(active__exact="T").order_by("-year", "semester")

    return render(request, "scheduling/change_summary.html", {"curr_terms": curr_terms})


@login_required
def change_summary_by_term(request, term):

    # TODO: set changes as as todo list

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

    changed, added, deleted, total_changes = get_diff_gcis_cams(term, course_list)
    context["changed"] = changed
    context["added"] = added
    context["deleted"] = deleted
    context["total_changes"] = total_changes

    return render(request, "scheduling/change_summary_by_term.html", context)


@login_required
def download_change_summary_by_term(request, term):

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="schedule-changes.csv"'

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []

    year = int(term[-4:])  # year
    semester = term[:-4].upper()  # Term
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)

    course_list = Course.objects.filter(subject__in=subject_list)

    changed, added, deleted, _ = get_diff_gcis_cams(term, course_list)

    # write data to csv file so that user can download
    writer = csv.writer(response)

    writer.writerow(
        [
            "Term",
            "Course",
            "Name",
            "Section",
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
            "Insert_by",
            "Insert_date",
            "Updated_by",
            "Updated_date",
            "Action",
        ]
    )
    for s, n, src, inb, ind, udy, udd in added:
        ind = "" if pd.isnull(ind) else str(ind)[:19]
        udd = "" if pd.isnull(udd) else str(udd)[:19]
        writer.writerow(
            [
                s.term,
                s.course,
                s.course.name,
                s.section,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                n,
                src,
                inb,
                ind,
                udy,
                udd,
                "ADD",
            ]
        )

    for s, n, src, inb, ind, udy, udd in deleted:
        ind = "" if pd.isnull(ind) else str(ind)[:19]
        udd = "" if pd.isnull(udd) else str(udd)[:19]
        writer.writerow(
            [
                s.term,
                s.course,
                s.course.name,
                s.section,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                n,
                src,
                inb,
                ind,
                udy,
                udd,
                "DELETE",
            ]
        )

    for s, n, src, inb, ind, udy, udd in changed:
        ind = "" if pd.isnull(ind) else str(ind)[:19]
        udd = "" if pd.isnull(udd) else str(udd)[:19]
        writer.writerow(
            [
                s.term,
                s.course,
                s.course.name,
                s.section,
                s.status,
                s.capacity,
                s.instructor,
                s.campus,
                s.location,
                s.days,
                s.start_time,
                s.stop_time,
                n,
                src,
                inb,
                ind,
                udy,
                udd,
                "CHANGE",
            ]
        )

    return response
