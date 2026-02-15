# main/context_processors.py
from .models import PageView
from .models import Project

def project_count(request):
    # Zliczamy liczbę projektów w bazie danych
    count = Project.objects.count()
    return {'project_count': count}


def visitor_counter(request):
    # Use Singleton pattern to get the PageView instance
    count = PageView.get_instance().count
    return {'visitor_count': count}
