from django.urls import path

from . import views

urlpatterns = [
    path("job/dashboard/", views.job_dashboard_stats, name="job_dashboard_stats"),
    path("job/list/", views.job_list, name="job_list"),
    path("job/detail/<str:job_id>/", views.job_detail, name="job_detail"),
]
