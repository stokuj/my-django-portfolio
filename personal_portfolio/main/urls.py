from django.urls import path
from main import views
from .views import project_list

urlpatterns = [
    path('',views.home, name='home'),
    path('test/',views.test, name='test'),
    path('home/',views.home, name='home'),
    path("about/", views.about, name="about"),
    #path("projects/", views.projects, name="projects"),
    path('projects/', project_list, name='projects'),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),

]
