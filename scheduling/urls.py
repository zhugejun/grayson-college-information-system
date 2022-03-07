from django.urls import path, include
from . import views


urlpatterns = [
    path("", views.home, name="scheduling_home"),
    path("subjects/", views.update_subjects, name="update_subjects"),
    path("schedules/<term>", views.schedules_by_term, name="schedules"),
    path(
        "schedules/<term>/courses/", views.courses_with_term, name="courses_with_term"
    ),
    path("schedules/<int:pk>/add/", views.add_schedule, name="add_schedule"),
    path("schedules/<int:pk>/edit/", views.edit_schedule, name="edit_schedule"),
    path("schedules/<int:pk>/delete/", views.delete_schedule, name="delete_schedule",),
    path("change-summary/", views.change_summary, name="change_summary"),
    path(
        "change-summary/<term>",
        views.change_summary_by_term,
        name="change_summary_by_term",
    ),
    path(
        "download-change-summary/<term>",
        views.download_change_summary_by_term,
        name="download_change_summary_by_term",
    ),
    path("schedule-summary/", views.schedule_summary, name="schedule_summary"),
]
