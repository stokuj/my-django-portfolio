from django.urls import path
from main import views
from main.blog_views import (
    AnalyzaMakroKonkursView, WebScrapperLubimyCzytacView, CryptoCurrencyPPView,
    MultidimensionalDashboardView, WeatherWebScrapingView, MyDjangoPortfolioView,
    GranularDataGroupingView, ActivityTrackerView, ObliczeniaZiarnisteView
)

urlpatterns = [
    path('',views.home, name='home'),
    path('home/',views.home, name='home'),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    # Using Template Method pattern with class-based views for blog posts
    path("blog/analiza_makro_konkurs/", AnalyzaMakroKonkursView.as_view(), name="analiza_makro_konkurs"),
    path("blog/web_scrapper_lubimyczytac/", WebScrapperLubimyCzytacView.as_view(), name="web_scrapper_lubimyczytac"),
    path("blog/crypto_currency_pp/", CryptoCurrencyPPView.as_view(), name="crypto_currency_pp"),
    path("blog/multidimensional_dashboard/", MultidimensionalDashboardView.as_view(), name="multidimensional_dashboard"),
    path("blog/weather_web_scraping/", WeatherWebScrapingView.as_view(), name="weather_web_scraping"),
    path("blog/my_django_portfolio/", MyDjangoPortfolioView.as_view(), name="my_django_portfolio"),
    path("blog/granular_data_grouping/", GranularDataGroupingView.as_view(), name="granular_data_grouping"),
    path("blog/activity_tracker/", ActivityTrackerView.as_view(), name="activity_tracker"),
    path("blog/obliczenia_ziarniste/", ObliczeniaZiarnisteView.as_view(), name="obliczenia_ziarniste"),
]
