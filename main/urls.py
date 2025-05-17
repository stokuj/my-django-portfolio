from django.urls import path
from main import views

urlpatterns = [
    path('',views.home, name='home'),
    path('home/',views.home, name='home'),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("blog/analiza_makro_konkurs/", views.analiza_makro_konkurs, name="analiza_makro_konkurs"),
    path("blog/web_scrapper_lubimyczytac/", views.web_scrapper_lubimyczytac, name="web_scrapper_lubimyczytac"),
    path("blog/crypto_currency_pp/", views.crypto_currency_pp, name="crypto_currency_pp"),
    path("blog/multidimensional_dashboard/", views.multidimensional_dashboard, name="multidimensional_dashboard"),
    path("blog/weather_web_scraping/", views.weather_web_scraping, name="weather_web_scraping"),
    path("blog/my_django_portfolio/", views.my_django_portfolio, name="my_django_portfolio"),
    path("blog/granular_data_grouping/", views.granular_data_grouping, name="granular_data_grouping"),
    path("blog/activity_tracker/", views.activity_tracker, name="activity_tracker"),
]

