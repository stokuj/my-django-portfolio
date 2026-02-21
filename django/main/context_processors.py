# main/context_processors.py
from allauth.socialaccount.models import SocialAccount

from .models import PageView, PortfolioProfile, Project


def project_count(request):
    # Zliczamy liczbę projektów w bazie danych
    count = Project.objects.count()
    return {"project_count": count}


def visitor_counter(request):
    # Pobieramy globalny licznik odwiedzin
    count = PageView.get_instance().count
    return {"visitor_count": count}


def portfolio_profile(request):
    source = (
        PortfolioProfile.objects.filter(is_active=True).first() or PortfolioProfile()
    )
    github_url = source.github_url or "#"
    linkedin_url = source.linkedin_url or "#"
    email = source.email
    github_base = github_url.rstrip("/") if github_url != "#" else "#"

    return {
        "site_name": source.site_name,
        "profile_full_name": source.full_name,
        "profile_role_line": source.role_line,
        "profile_specialization_line": source.specialization_line,
        "profile_home_intro": source.home_intro,
        "profile_about_intro": source.about_intro,
        "profile_email": email,
        "profile_email_href": f"mailto:{email}" if email else "#",
        "profile_github_url": github_url,
        "profile_github_base": github_base,
        "profile_linkedin_url": linkedin_url,
    }


def auth_state(request):
    github_connected = False
    user = getattr(request, "user", None)

    if user and user.is_authenticated:
        github_connected = SocialAccount.objects.filter(
            user=user,
            provider="github",
        ).exists()

    return {
        "github_connected": github_connected,
    }
