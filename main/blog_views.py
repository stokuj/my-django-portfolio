# main/blog_views.py
"""
Implementation of the Template Method pattern for blog post views.
"""
from django.views import View
from django.shortcuts import render

class BlogPostView(View):
    """
    Base class for blog post views implementing the Template Method pattern.
    The template_name attribute must be defined in subclasses.
    """
    template_name = None
    
    def get(self, request):
        """Template method for handling GET requests"""
        return render(request, self.template_name)

# Concrete implementations for each blog post
class AnalyzaMakroKonkursView(BlogPostView):
    """View for the 'Analiza Makro Konkurs' blog post"""
    template_name = "main/blog/analiza_makro_konkurs.html"

class WebScrapperLubimyCzytacView(BlogPostView):
    """View for the 'Web Scrapper Lubimy Czytac' blog post"""
    template_name = "main/blog/web_scrapper_lubimyczytac.html"

class CryptoCurrencyPPView(BlogPostView):
    """View for the 'Crypto Currency PP' blog post"""
    template_name = "main/blog/crypto_currency_pp.html"

class MultidimensionalDashboardView(BlogPostView):
    """View for the 'Multidimensional Dashboard' blog post"""
    template_name = "main/blog/multidimensional_dashboard.html"

class WeatherWebScrapingView(BlogPostView):
    """View for the 'Weather Web Scraping' blog post"""
    template_name = "main/blog/weather_web_scraping.html"

class MyDjangoPortfolioView(BlogPostView):
    """View for the 'My Django Portfolio' blog post"""
    template_name = "main/blog/my_django_portfolio.html"

class GranularDataGroupingView(BlogPostView):
    """View for the 'Granular Data Grouping' blog post"""
    template_name = "main/blog/granular_data_grouping.html"

class ActivityTrackerView(BlogPostView):
    """View for the 'Activity Tracker' blog post"""
    template_name = "main/blog/activity_tracker.html"

class ObliczeniaZiarnisteView(BlogPostView):
    """View for the 'Obliczenia Ziarniste' blog post"""
    template_name = "main/blog/obliczenia_ziarniste.html"