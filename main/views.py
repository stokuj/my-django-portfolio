from django.shortcuts import render, get_object_or_404
from .models import Project, Tag

def home(request):
    return render(request, "main/home.html", {})

def test(request):
    return render(request, "main/test.html", {})

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

def CryptoCurrencyPP(request):
    return render(request, "main/blog/CryptoCurrencyPP.html")

def multidimensional_dashboard(request):
    return render(request, "main/blog/multidimensional_dashboard.html")