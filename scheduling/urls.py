from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name="scheduling"),
    path('subjects/', views.update_subjects, name="update_subjects"),

    path('courses/', views.courses, name="courses"),
    path('course/add/', views.add_course, name="add_course"),
    # path('course/<int:pk>/edit/', views.edit_course, name="edit_course"),
    # path('course/<int:pk>/delete/', views.delete_course, name="delete_course"),


    path('schedules/<term>', views.schedules, name="schedules"),
    path('schedules/<term>/courses/',
         views.courses_with_term, name="courses_with_term"),
    path('schedules/<term>/<int:pk>/add/',
         views.add_schedule, name="add_schedule"),
    path('schedules/<term>/<int:pk>/edit/',
         views.edit_schedule, name="edit_schedule"),
    #     path('schedules/<term>/<int:pk>/delete/',
    #          views.delete_schedule, name="delete_schedule"),

    path('instructors/', views.instructors, name="instructors"),

    path('change-summary/', views.change_summary, name='change_summary'),
    path('change-summary/<term>', views.change_summary_by_term,
         name='change_summary_by_term'),
    path('download-change-summary/<term>', views.download_change_summary_by_term,
         name='download_change_summary_by_term'),

    path('schedule-summary/', views.schedule_summary, name='schedule_summary'),

]
