# main/context_processors.py
from django.conf import settings

from .models import PageView, Project

def project_count(request):
    # Zliczamy liczbę projektów w bazie danych
    count = Project.objects.count()
    return {'project_count': count}


def visitor_counter(request):
    # Pobieramy globalny licznik odwiedzin
    count = PageView.get_instance().count
    return {'visitor_count': count}


def portfolio_profile(request):
    profile = getattr(settings, 'PORTFOLIO_PROFILE', {})
    email = profile.get('email', '')
    github_url = profile.get('github_url', '#')
    github_base = github_url.rstrip('/') if github_url and github_url != '#' else '#'

    return {
        'site_name': profile.get('site_name', 'My Portfolio'),
        'profile_full_name': profile.get('full_name', ''),
        'profile_email': email,
        'profile_email_href': f"mailto:{email}" if email else '#',
        'profile_github_url': github_url,
        'profile_github_base': github_base,
        'profile_linkedin_url': profile.get('linkedin_url', '#'),
    }
