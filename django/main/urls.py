from django.urls import path
from main import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("about/heatmap-data/", views.about_heatmap_data, name="about_heatmap_data"),
    path(
        "about/heatmap-disconnect/",
        views.about_heatmap_disconnect,
        name="about_heatmap_disconnect",
    ),
    path("projects/", views.projects, name="projects"),
    path("blog/<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
    path(
        "admin-tools/run-markdown-sync/",
        views.run_markdown_sync_task,
        name="run_markdown_sync_task",
    ),
    path(
        "admin-tools/run-heatmap-refresh/",
        views.run_heatmap_refresh_task,
        name="run_heatmap_refresh_task",
    ),
]
