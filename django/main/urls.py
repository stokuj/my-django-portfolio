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
        "blog/analiza-makro-konkurs/",
        TemplateView.as_view(template_name="main/blog/analiza-makro-konkurs.html"),
        name="analiza_makro_konkurs",
    ),
    path(
        "blog/web-scraping-lubimyczytac/",
        TemplateView.as_view(template_name="main/blog/web-scraping-lubimyczytac.html"),
        name="web_scrapper_lubimyczytac",
    ),
    path(
        "blog/currency-price-prediction/",
        TemplateView.as_view(template_name="main/blog/currency-price-prediction.html"),
        name="crypto_currency_pp",
    ),
    path(
        "blog/multidimensional-dashboard/",
        TemplateView.as_view(template_name="main/blog/multidimensional-dashboard.html"),
        name="multidimensional_dashboard",
    ),
    path(
        "blog/weather-web-scraping/",
        TemplateView.as_view(template_name="main/blog/weather-web-scraping.html"),
        name="weather_web_scraping",
    ),
    path(
        "blog/my-django-portfolio/",
        TemplateView.as_view(template_name="main/blog/my-django-portfolio.html"),
        name="my_django_portfolio",
    ),
    path(
        "blog/granular-data-grouping/",
        TemplateView.as_view(template_name="main/blog/granular-data-grouping.html"),
        name="granular_data_grouping",
    ),
    path(
        "blog/activity-tracker/",
        TemplateView.as_view(template_name="main/blog/activity-tracker.html"),
        name="activity_tracker",
    ),
    path(
        "blog/NTwI-obliczenia-ziarniste/",
        TemplateView.as_view(template_name="main/blog/NTwI-obliczenia-ziarniste.html"),
        name="obliczenia_ziarniste",
    ),
    path("blog/<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
]
