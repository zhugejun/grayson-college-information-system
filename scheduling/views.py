from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.urls import reverse

import pandas as pd
import numpy as np
import csv

from .forms import ScheduleForm, SubjectForm, SearchForm
from .models import Course, Schedule, Instructor, Term, Cams, Campus, Location
from main.models import Profile


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

        unique_cols = [
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
        ]

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

    course_list = Course.objects.filter(subject__in=subject_list)

    form.fields["term"].queryset = Term.objects.filter(active="T")
    form.fields["course"].queryset = course_list

    context["form"] = form

    latest_edited_5 = Schedule.objects.filter(
        update_by=request.user, course__in=course_list
    )
    latest_edited_5 = latest_edited_5.order_by("-update_date")[:5]
    context["latest_edited_5"] = latest_edited_5

    latest_added_5 = Schedule.objects.filter(
        insert_by=request.user, course__in=course_list
    )
    latest_added_5 = latest_added_5.order_by("-insert_date")[:5]
    context["latest_added_5"] = latest_added_5

    return render(request, "scheduling/home.html", context)


@login_required
def search(request):
    # scheduling/schedules/search/?term=?&course=1&section=A01&page=1

    context = {}

    term_pk = request.GET.get("term")
    term = get_object_or_404(Term, pk=term_pk)
    context["term_pk"] = term_pk

    course_pk = request.GET.get("course")
    course = get_object_or_404(Course, pk=course_pk)
    context["course_pk"] = course_pk

    section = request.GET.get("section")
    context["term"] = term
    context["course"] = course
    context["section"] = section

    schedule_list = Schedule.objects.filter(term=term, course=course)
    if section:
        schedule_list = schedule_list.filter(section__startswith=section)

    paginator = Paginator(schedule_list, 25)
    page_number = request.GET.get("page")

    if not page_number and schedule_list:
        page_number = 1

    page = paginator.get_page(page_number)
    context["page"] = page

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

    context = {}
    search_url = reverse("search")

    schedule = get_object_or_404(Schedule, pk=pk)
    new_schedule = schedule
    new_schedule.pk = None
    if new_schedule.days:
        new_schedule.days = list(new_schedule.days)
    else:
        schedule.days = []

    context["schedule"] = new_schedule

    term_pk = new_schedule.term.id
    course_pk = new_schedule.course.id

    form = ScheduleForm(instance=new_schedule)
    context["form"] = form

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=new_schedule)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.insert_by = request.user
            schedule.update_by = None
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} added.")
            return redirect(
                search_url + f"?page=1&term={term_pk}&course={course_pk}&section="
            )
        else:
            for _, error in form._errors.items():
                messages.error(request, error)

    return render(request, "scheduling/duplicate_schedule.html", context)


@login_required
def add_new_schedule(request, term_pk, crs_pk):
    context = {}

    search_url = reverse("search")

    term = get_object_or_404(Term, pk=term_pk)
    course = get_object_or_404(Course, pk=crs_pk)
    context["term"] = term
    context["course"] = course

    form = ScheduleForm()
    form.fields["term"].initial = term
    form.fields["course"].initial = course
    form.fields["days"].initial = []
    form.fields["capacity"].initial = 1

    context["form"] = form
    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.insert_by = request.user
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} added.")
            return redirect(
                search_url + f"?page=1&term={term_pk}&course={crs_pk}&section="
            )
        else:
            for _, error in form._errors.items():
                messages.error(request, error)

    return render(request, "scheduling/add_new_schedule.html", context)


@login_required
def edit_schedule(request, pk):

    context = {}

    schedule = get_object_or_404(Schedule, pk=pk)
    context["schedule"] = schedule
    term_pk = schedule.term.id
    course_pk = schedule.course.id

    search_url = reverse("search")
    source = request.GET.get("source")
    print(source)

    if schedule.days:
        schedule.days = list(schedule.days)
    else:
        schedule.days = []

    form = ScheduleForm(instance=schedule)
    context["form"] = form

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.update_by = request.user
            schedule.save()
            messages.success(request, f"{schedule}-{schedule.term} updated.")
            return redirect(
                search_url + f"?page=1&term={term_pk}&course={course_pk}&section="
            )
        else:
            for _, error in form._errors.items():
                messages.error(request, error)
    return render(request, "scheduling/edit_schedule.html", context)


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
                search_url + f"?page=1&term={term_pk}&course={course_pk}&section="
            )
    return render(request, "scheduling/delete_schedule.html", context)


@login_required
def schedules_by_term(request, term):

    context = {}

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    year = int(term[-4:])
    semester = term[:-4].upper()
    term = get_object_or_404(Term, year__exact=year, semester__exact=semester)
    context["term"] = term

    schedule_list = Schedule.objects.filter(term=term, course__in=course_list)
    context["schedule_list"] = schedule_list
    return render(request, "scheduling/schedules.html", context)


@login_required
def schedule_summary(request):

    # TODO: add dashboard or summary statistics or weekly view

    profile = get_object_or_404(Profile, user=request.user)
    if profile.subjects:
        subject_list = profile.subjects.split(",")
    else:
        subject_list = []
    course_list = Course.objects.filter(subject__in=subject_list)

    # selected subjects
    # by Term
    # return a schedule list too

    return render(request, "scheduling/schedule_summary.html")


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
