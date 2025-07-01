from django.urls import path
from . import views

urlpatterns = [
     path('category/<slug:category_slug>/', views.posts_by_category, name="posts_by_category"),
]