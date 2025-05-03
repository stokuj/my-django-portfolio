from django.urls import path
from main import views

urlpatterns = [
    path('',views.home, name='home'),
    path('test/',views.test, name='test'),
    path('home/',views.home, name='home'),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    #path('projects/', project_list, name='projects'),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("blog/analiza_makro_konkurs/", views.analiza_makro_konkurs, name="analiza_makro_konkurs"),
    path("blog/web_scrapper_lubimyczytac/", views.web_scrapper_lubimyczytac, name="web_scrapper_lubimyczytac"),
        path("blog/CryptoCurrencyPP/", views.CryptoCurrencyPP, name="CryptoCurrencyPP"),
]

