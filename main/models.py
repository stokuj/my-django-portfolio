from django.db import models
import datetime
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
    date = models.DateField(default=datetime.date(2022, 5, 1))     
    blog = models.BooleanField(default=True)
    blog_url = models.CharField(max_length=100, blank=True, null=True)
    github_url = models.CharField(max_length=100, blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
    ]

    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='planned',)

    def __str__(self):
        return self.title

class PageView(models.Model):
    count = models.IntegerField(default=0)

    @classmethod
    def get_instance(cls):
        """
        Singleton pattern implementation.
        Always returns the same instance of PageView.
        """
        instance, created = cls.objects.get_or_create(id=1)
        return instance
