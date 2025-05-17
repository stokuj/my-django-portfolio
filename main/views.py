from django.shortcuts import render, get_object_or_404
from .models import Project, Tag
from .models import PageView

def home(request):
    if not request.session.get('has_visited'):
        view_counter, created = PageView.objects.get_or_create(id=1)
        view_counter.count += 1
        view_counter.save()
        request.session['has_visited'] = True
        
    count = PageView.objects.get(id=1).count
    projects = Project.objects.all().order_by('date')
    return render(request, "main/home.html", {'projects': projects})


def about(request):
    return render(request, "main/about.html", {})

def projects(request):
    projects = Project.objects.all().prefetch_related('tags')  # Przyspiesza ładowanie tagów

    # Pobieramy wszystkie unikalne tagi
    all_tags = Tag.objects.all().order_by('name')

    return render(request, 'main/projects.html', {
        'projects': projects,
        'all_tags': all_tags,
    })


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, "main/project_detail.html", {"project": project})

def analiza_makro_konkurs(request):
    return render(request, "main/blog/analiza_makro_konkurs.html")

def web_scrapper_lubimyczytac(request):
    return render(request, "main/blog/web_scrapper_lubimyczytac.html")

def crypto_currency_pp(request):
    return render(request, "main/blog/crypto_currency_pp.html")

def multidimensional_dashboard(request):
    return render(request, "main/blog/multidimensional_dashboard.html")

def weather_web_scraping(request):
    return render(request, "main/blog/weather_web_scraping.html")

def my_django_portfolio(request):
    return render(request, "main/blog/my_django_portfolio.html")

def granular_data_grouping(request):
    return render(request, "main/blog/granular_data_grouping.html")

def activity_tracker(request):
    return render(request, "main/blog/activity_tracker.html")