from django.db import models
from tinymce.models import HTMLField
from django_summernote.fields import SummernoteTextField
from ckeditor.fields import RichTextField
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Zamiana na wielkie litery przed zapisem
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Project(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, default='thumbnails/default_image.png')
    short_description = models.CharField(max_length=100)
    
    blog = models.BooleanField(default=False)
    blog_url = models.CharField(max_length=100, blank=True, null=True)
    
    description = RichTextField(blank=True, null=True)
    role = RichTextField(blank=True, null=True)
    challenges = RichTextField(blank=True, null=True)
    features = JSONField(default=list, blank=True, null=True)
    technical_details = RichTextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title

class PageView(models.Model):
    count = models.IntegerField(default=0)