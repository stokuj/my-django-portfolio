from django.urls import path
from django.views.generic import TemplateView
from main import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path(
        "blog/analiza_makro_konkurs/",
        TemplateView.as_view(template_name="main/blog/analiza_makro_konkurs.html"),
        name="analiza_makro_konkurs",
    ),
    path(
        "blog/web_scrapper_lubimyczytac/",
        TemplateView.as_view(template_name="main/blog/web_scrapper_lubimyczytac.html"),
        name="web_scrapper_lubimyczytac",
    ),
    path(
        "blog/crypto_currency_pp/",
        TemplateView.as_view(template_name="main/blog/crypto_currency_pp.html"),
        name="crypto_currency_pp",
    ),
    path(
        "blog/multidimensional_dashboard/",
        TemplateView.as_view(template_name="main/blog/multidimensional_dashboard.html"),
        name="multidimensional_dashboard",
    ),
    path(
        "blog/weather_web_scraping/",
        TemplateView.as_view(template_name="main/blog/weather_web_scraping.html"),
        name="weather_web_scraping",
    ),
    path(
        "blog/my_django_portfolio/",
        TemplateView.as_view(template_name="main/blog/my_django_portfolio.html"),
        name="my_django_portfolio",
    ),
    path(
        "blog/granular_data_grouping/",
        TemplateView.as_view(template_name="main/blog/granular_data_grouping.html"),
        name="granular_data_grouping",
    ),
    path(
        "blog/activity_tracker/",
        TemplateView.as_view(template_name="main/blog/activity_tracker.html"),
        name="activity_tracker",
    ),
    path(
        "blog/obliczenia_ziarniste/",
        TemplateView.as_view(template_name="main/blog/obliczenia_ziarniste.html"),
        name="obliczenia_ziarniste",
    ),
]
