from django.shortcuts import render, get_object_or_404
from .models import Project, Tag


def handler404(request, exception):
    return render(request, 'main/404.html', status=404)


def handler500(request):
    return render(request, 'main/500.html', status=500)


def home(request):
    projects = Project.objects.prefetch_related('tags').order_by('-date')
    status_labels = {
        'planned': 'Planned',
        'ongoing': 'Ongoing',
        'finished': 'Finished',
    }
    status_order = ['planned', 'ongoing', 'finished']

    projects_by_status = {status: [] for status in status_order}
    for project in projects:
        if project.status in projects_by_status:
            projects_by_status[project.status].append(project)

    timeline_sections = [
        {
            'status': status,
            'title': status_labels[status],
            'checked': status == 'finished',
            'projects': projects_by_status[status],
        }
        for status in status_order
    ]

    return render(request, "main/home.html", {'timeline_sections': timeline_sections})


def about(request):
    return render(request, "main/about.html", {})


def projects(request):
    projects = Project.objects.all().prefetch_related('tags')  # Faster tag loading

    # Pobieramy wszystkie unikalne tagi
    all_tags = Tag.objects.all().order_by('name')

    return render(request, 'main/projects.html', {
        'projects': projects,
        'all_tags': all_tags,
    })


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, "main/project_detail.html", {"project": project})


# Blog post routes are configured directly in urls.py with TemplateView
