from django.shortcuts import render, get_object_or_404
from .models import Project, Tag

def home(request):
    return render(request, "main/home.html", {})

def test(request):
    return render(request, "main/test.html", {})

def about(request):
    return render(request, "main/about.html", {})

def projects(request):

    projects_qs = Project.objects.all()
    context = {'projects': projects_qs}
    return render(request, 'main/projects.html', context)

def project_list(request):
    query = request.GET.get('q', '')  # Pobieramy parametr q z URL
    tag_name = request.GET.get('tag', '')  # Pobieramy tag z URL
    print(f"Szukana fraza: {query}")  # Debugowanie
    print(f"Szukany tag: {tag_name}")  # Debugowanie

    projects = Project.objects.all()

    # Filtrowanie po tytule lub opisie
    if query:
        projects = projects.filter(title__icontains=query) | projects.filter(description__icontains=query)
    
    # Filtrowanie po tagu
    if tag_name:
        projects = projects.filter(tags__name=tag_name)

    # Pobranie wszystkich tagów do kontekstu
    tags = Tag.objects.all()

    return render(request, 'main/projects.html', {'projects': projects, 'query': query, 'tags': tags, 'tag_name': tag_name})

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, "main/project_detail.html", {"project": project})
