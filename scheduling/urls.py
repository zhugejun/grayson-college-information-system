from django.urls import path, include
from . import views


urlpatterns = [
    path("home", views.home, name="scheduling_home"),
    path("update-subjects/", views.update_subjects, name="update_subjects"),
    path("schedules/search/", views.search, name="search"),
    path(
        "schedules/term/<int:term_pk>/course/<int:crs_pk>/add/",
        views.add_new_schedule,
        name="add_new_schedule",
    ),
    path(
        "schedules/<int:pk>/add/", views.duplicate_schedule, name="duplicate_schedule"
    ),
    path("schedules/<int:pk>/edit/", views.edit_schedule, name="edit_schedule"),
    path("schedules/<int:pk>/delete/", views.delete_schedule, name="delete_schedule"),
    path("schedules/<int:pk>/restore/", views.restore_schedule, name="restore_schedule"),
    path("schedules/recent/", views.history, name="recent"),
    path("change-summary/", views.change_summary, name="change_summary"),
    path(
        "change-summary/<term>/",
        views.change_summary_by_term,
        name="change_summary_by_term",
    ),
    path(
        "download-change-summary/<term>/",
        views.download_change_summary_by_term,
        name="download_change_summary_by_term",
    ),
    path("schedule-summary/", views.schedule_summary, name="schedule_summary"),
    path(
        "schedule-summary/<term>/",
        views.schedule_summary_by_term,
        name="schedule_summary_by_term",
    ),
]
