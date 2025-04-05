from django.db import models
from tinymce.models import HTMLField

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
    description = HTMLField()  # pole rich text
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title
