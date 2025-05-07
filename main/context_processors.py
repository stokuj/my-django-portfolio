# main/context_processors.py
from .models import PageView
from .models import Project

def project_count(request):
    # Zliczamy liczbę projektów w bazie danych
    count = Project.objects.count()
    return {'project_count': count}


def visitor_counter(request):
    count = PageView.objects.get(id=1).count if PageView.objects.filter(id=1).exists() else 0
    return {'visitor_count': count}