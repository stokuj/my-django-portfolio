from django.shortcuts import render, get_object_or_404
from .models import Project, Tag
from .models import PageView
from .observers import VisitorEvent

def handler404(request, exception):
    return render(request, 'main/404.html', status=404)

def handler500(request):
    return render(request, 'main/500.html', status=500)

def home(request):
    if not request.session.get('has_visited'):
        # Use Observer pattern to notify about new visit
        VisitorEvent.notify_new_visit(request)
        request.session['has_visited'] = True

    count = PageView.get_instance().count
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

# Blog post views have been moved to blog_views.py using the Template Method pattern
