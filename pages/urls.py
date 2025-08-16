from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/pages/", views.page_list, name="page_list"),
    path("dashboard/pages/create/", views.page_create, name="page_create"),
    path("dashboard/pages/edit/<int:pk>/", views.page_edit, name="page_edit"),
    path("dashboard/pages/delete/<int:pk>/", views.page_delete, name="page_delete"),
    path("<slug:slug>/", views.page_detail, name="page_detail"),
]
