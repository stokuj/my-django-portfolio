from django.urls import path
from main import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("blog/<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
]
