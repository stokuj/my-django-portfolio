# main/context_processors.py
from .models import Project

def project_count(request):
    # Zliczamy liczbę projektów w bazie danych
    count = Project.objects.count()
    return {'project_count': count}
