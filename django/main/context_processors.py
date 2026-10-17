from .models import PageView, PortfolioProfile, Project


def project_count(request):
    """Expose the total number of projects to all templates.

    Returns:
        dict: Context with `project_count` key.
    """
    count = Project.objects.count()
    return {"project_count": count}


def visitor_counter(request):
    instance = PageView.objects.filter(id=1).first()
    return {"visitor_count": instance.count if instance else 0}


def portfolio_profile(request):
    """Expose the active portfolio profile (or an unsaved default) as `profile`."""
    return {"profile": PortfolioProfile.get_active()}
