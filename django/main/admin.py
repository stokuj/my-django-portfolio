from django.contrib import admin
from .models import Project, Tag, PageView
from ckeditor.widgets import CKEditorWidget
from ckeditor.fields import RichTextField

class ProjectAdmin(admin.ModelAdmin):
    formfield_overrides = {
        RichTextField: {'widget': CKEditorWidget},
    }

admin.site.register(Project, ProjectAdmin)
#admin.site.register(Project)
admin.site.register(Tag)
admin.site.register(PageView)