from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class GitHubAdminOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    def _deny(self, request, message):
        messages.error(request, message)
        raise ImmediateHttpResponse(redirect("home"))

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != "github":
            return

        allowed_login = (
            (getattr(settings, "GITHUB_ALLOWED_LOGIN", "") or "").strip().lower()
        )
        allowed_email = (
            (getattr(settings, "GITHUB_ALLOWED_EMAIL", "") or "").strip().lower()
        )

        if not allowed_login:
            self._deny(request, "GitHub login is not configured.")

        github_login = (
            (sociallogin.account.extra_data.get("login") or "").strip().lower()
        )
        github_email = (
            (
                sociallogin.user.email
                or sociallogin.account.extra_data.get("email")
                or ""
            )
            .strip()
            .lower()
        )

        if github_login != allowed_login:
            self._deny(request, "This GitHub account is not allowed.")

        if allowed_email and github_email and github_email != allowed_email:
            self._deny(request, "GitHub account email does not match admin account.")

        if sociallogin.is_existing:
            if not sociallogin.user.is_superuser:
                self._deny(request, "This GitHub account is not linked to admin user.")
            return

        user_model = get_user_model()
        admin_user = user_model.objects.filter(is_superuser=True).order_by("id").first()
        if not admin_user:
            self._deny(request, "No admin user found.")

        sociallogin.connect(request, admin_user)
